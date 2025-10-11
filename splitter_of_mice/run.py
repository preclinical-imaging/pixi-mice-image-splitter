import argparse
from datetime import datetime
import glob
import json
import logging
import os
import requests
import sys
import uuid
import time
from pathlib import Path
import zipfile
import math
import numpy as np

from collections import defaultdict
from requests import Session
from splitter_of_mice.splitter import SoM
from splitter_of_mice.rectangle import Rect

# Setup splitter of mice descriptor map
SoM.desc_map = {'l': 'l', 'r': 'r', 'ctr': 'ctr', 'lb': 'lb', 'rb': 'rb', 'lt': 'lt', 'rt': 'rt'}


def run(username: str, password: str, server: str,
        project: str, experiment: str,
        input_dir: str, output_dir: str, **kwargs):

    # Create a session
    session = requests.Session()
    session.auth = (username, password)

    try:
        logging.debug(f'''run(username={username}, password=*****, server={server}, 
                       project={project}, experiment={experiment}, 
                       input_dir={input_dir}, output_dir={output_dir})''')

        update_scan_record_status(session, server, project, experiment, status="Splitting In Progress")

        logging.debug(f"Find subdirectories with DICOM files in {input_dir}")

        files = defaultdict(list)

        # First look for DICOM files
        isDicomSession = True
        for dicom_file in glob.glob(f'{input_dir}/**/*.dcm', recursive=True):
            files[os.path.dirname(dicom_file)].append(os.path.basename(dicom_file))

        logging.info(f'Found {len(files)} subdirectories containing DICOM files: {files.keys()}')

        if len(files) == 0:
            isDicomSession = False
            logging.info(f'No DICOM files found in {input_dir}. Searching for Inveon .img files instead.')

            for img_file in glob.glob(f'{input_dir}/**/*.img', recursive=True):
                files[img_file].append(os.path.basename(img_file))

            logging.info(f'Found {len(files)} Inveon .img files: {files.keys()}')

        if len(files) == 0:
            logging.error(f'No DICOM or Inveon .img files found in {input_dir}. Exiting.')
            update_scan_record_status(session, server, project, experiment, "Error: No DICOM or Inveon images files found")
            sys.exit(f'No DICOM or Inveon images files found in {input_dir}')

        #if we have more than two scans, we need to pair them up for coregistration. 
        #we've decided to use scan time for this so we need to get the scan time for each scan
        start_times_for_scans = {}
        if len(files) > 2:
            start_times_for_scans = get_start_times_for_scans(session, server, project, experiment, files)
            logging.info(f"{start_times_for_scans}\n\n")

        #Create splitter and output directory for each subdirectory and prep them for coregistration if applicable
        splitters_pet = []
        splitters_ct = []
        for dicom_dir in files.keys():
            spltr = SoM(dicom_dir, dicom=isDicomSession)
            output_directory = os.path.join(output_dir, os.path.relpath(dicom_dir, input_dir))
            os.makedirs(output_directory, exist_ok=True)
            spltr.outdir = os.path.join(output_dir, os.path.relpath(dicom_dir, input_dir))
            if dicom_dir in start_times_for_scans:
                spltr.scan_time = start_times_for_scans[dicom_dir]

            #connect corresponding pet and ct scans for coregistration
            if spltr.modality == 'CT':
                splitters_ct.append(spltr)
            else:
                splitters_pet.append(spltr)
        coregister_cuts = False
        if (len(splitters_pet) == len(splitters_ct)):
            coregister_cuts = True
            splitters_pet = sorted(splitters_pet, key=lambda x: x.scan_time)
            splitters_ct = sorted(splitters_ct, key=lambda x: x.scan_time)
            splitters = list(zip(splitters_pet, splitters_ct))
        else:
            splitters = splitters_pet + splitters_ct

        # Get hotel scan record
        hotel_scan_record = get_hotel_scan_record(session, server, project, experiment)
        num_anim = sum(1 for subj in hotel_scan_record['hotelSubjects'] if subj.get('subjectId'))

        # Convert hotel scan record to metadata dictionary format expected by splitter of mice
        metadata = convert_hotel_scan_record(hotel_scan_record, dicom=isDicomSession, mpet=not isDicomSession)

        # Get Technicians Perspective and rotate image if needed
        technicians_perspective = hotel_scan_record.get('technicianPerspective', 'Front')
        technicians_perspective = technicians_perspective.lower()

        pet_cuts_for_coregister = None
        pet_img_shape_for_coregister = None

        for splitter in splitters:
            # custom code to handle wustl scanners
            pet_img_size = None
            ct_img_size = None
            if 'nscan' in experiment:
                # if experiment contains the word 'nscan'
                pet_img_size = (65, 65)
                ct_img_size = (260, 260)
            elif 'mpet' in experiment:
                # if experiment contains the word 'mpet'
                pet_img_size = (43, 43)
                ct_img_size = (172, 172)

            if coregister_cuts:
                splitter_pet = splitter[0]
                splitter_ct = splitter[1]
                if technicians_perspective == 'back':
                    splitter_pet.pi.rotate_on_axis('y')
                    splitter_ct.pi.rotate_on_axis('y')
                run_splitter(splitter_pet, num_anim, metadata, pet_img_size, ct_img_size, coregister_cuts=True)
                run_splitter(splitter_ct, num_anim, metadata, pet_img_size, ct_img_size, coregister_cuts=True)
            else:
                if technicians_perspective == 'back':
                    splitter.pi.rotate_on_axis('y')
                run_splitter(splitter, num_anim, metadata, pet_img_size, ct_img_size)

        if coregister_cuts:
            for splitter in splitters:
                harmonize_pet_and_ct_cuts(splitter[0], splitter[1], metadata, num_anim)
            #flatten out lists now that we're done with coregistration
            splitters_flattened = [item for sublist in splitters for item in sublist]
            splitters = splitters_flattened

        # Upload each cut to XNAT
        # Send all scans for a subject together so the prearchive doesn't accidentally archive one scan before the other.
        subject_zip_files = defaultdict(list)
        for splitter in splitters:
            for zip_outputs in splitter.pi.zip_outputs:
                subject, zip_file_path = zip_outputs
                zip_file_path = Path(zip_file_path)
                subject_zip_files[subject].append(zip_file_path)

        if not isDicomSession:
            # Merge the zip files for each subject into a single zip file
            # The DICOM zip importer can handle multiple zip files for a single session but not the Inveon importer
            for subject, zip_files in subject_zip_files.items():
                if len(zip_files) > 1:
                    # Create a new zip file for the subject
                    merged_zip_file_path = os.path.join(output_dir, f'{subject}_merged.zip')
                    with zipfile.ZipFile(merged_zip_file_path, 'w') as merged_zip_file:
                        for zip_file_path in zip_files:
                            # Open each zip file and extract all files into the new zip file
                            with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
                                for file in zip_file.namelist():
                                    merged_zip_file.writestr(file, zip_file.read(file))

                    # Delete the old zip files
                    for zip_file_path in zip_files:
                        os.remove(zip_file_path)

                    # Replace the list of zip files for the subject with the new merged zip file
                    subject_zip_files[subject] = [Path(merged_zip_file_path)]

        for subject, zip_files in subject_zip_files.items():
            for zip_file_path in zip_files:
                if subject:  # skip empty subjects
                    send_split_images(session, server, project, subject, experiment, zip_file_path, isDicomSession)

        for splitter in splitters:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            modality = splitter.modality if splitter.modality else ""
            send_qc_image(session, server, project, experiment,
                          splitter.pi.qc_outputs, resource_name=f"QC_SNAPSHOTS_{timestamp}_{splitter.modality}")

        # update hotel scan record
        update_scan_record(session, server, experiment, hotel_scan_record)

        # update hotel scan record status
        update_scan_record_status(session, server, project, experiment, status="Split Complete")

    except Exception as e:
        logging.exception("Fatal error while splitting hotel scan: " + str(e))
        update_scan_record_status(session, server, project, experiment, "Error: Not Split")
        sys.exit("Fatal error while splitting hotel scan " + str(e))

    return


def run_splitter(splitter, num_anim, metadata, pet_img_size, ct_img_size, coregister_cuts=False):
    exit_code = splitter.split_mice(num_anim=num_anim, remove_bed=True,
        zip=True, dicom_metadata=metadata, output_qc=True,
        pet_img_size=pet_img_size, ct_img_size=ct_img_size, 
        coregister_cuts=coregister_cuts)
    if exit_code != 0:
        raise Exception(f'Error splitting subdirectory {os.path.dirname(splitter.filename)}')


def harmonize_pet_and_ct_cuts(splitter_pet, splitter_ct, metadata, num_anim):
    pet_cuts, ct_cuts = splitter_pet.cuts, splitter_ct.cuts
    logging.info(f"PET CUT LENGTH: {len(pet_cuts)}\n CT CUT LENGTH: {len(ct_cuts)}")
    pet_shape, ct_shape = splitter_pet.pi.img_data.shape, splitter_ct.pi.img_data.shape
    x_scale, y_scale = (ct_shape[1]/pet_shape[1]), (ct_shape[2]/pet_shape[2])

    coregistered_cuts_ct = []
    coregistered_cuts_pet = []

    if splitter_pet.original_number_cuts > 2*num_anim:
        #in this case, we can be reasonably confident that the splitter was not finding it easy to segment the PET image
        #as such, we're going to default to the CT scan which does splitting in a less naive way
        replacement_pet_cuts = []
        for cut in ct_cuts:
            cut_rect = cut['rect']
            new_bb = [(cut_rect.xlt/x_scale).astype(int), (cut_rect.ylt/y_scale).astype(int), (cut_rect.xrb/x_scale).astype(int), (cut_rect.yrb/y_scale).astype(int)]
            new_rect_one = Rect(bb=new_bb, label=cut_rect.label)
            replacement_pet_cuts += [{'desc': cut['desc'], 'rect': new_rect_one}]
        #because we don't trust the pet cuts, we will not be changing the ct data in any way.
        #simply replace the pet cuts with their new versions which are already coregistered with the ct cuts.
        splitter_pet.cuts = replacement_pet_cuts
    else:
        for cut in pet_cuts:
            cut_rect = cut['rect']
            bb = [cut_rect.xlt*x_scale, cut_rect.ylt*y_scale, cut_rect.xrb*x_scale, cut_rect.yrb*y_scale]
            scaled_pet_rect = Rect(bb=bb, label=cut_rect.label)

            filtered_cuts = list(filter(lambda x: x['desc'] == cut['desc'], ct_cuts))
            connected_ct_cut = filtered_cuts[0]

            if len(filtered_cuts) == 1:
                #one to one relationship between pet and ct cuts. we can simply combine them without other processing.
                ct_cuts.remove(connected_ct_cut)
            elif len(filtered_cuts) == 2:
                #two cuts were both mapped to within the same portion of the image. 
                #combine them into one to try to get all relavent data into the same cut
                combined_ct_rect, __ = combine_two_rects(filtered_cuts[0]['rect'], filtered_cuts[1]['rect'], [1.0, 1.0], [1.0, 1.0])
                connected_ct_cut = {'desc': filtered_cuts[0]['desc'], 'rect': combined_ct_rect}
                ct_cuts.remove(filtered_cuts[0])
                ct_cuts.remove(filtered_cuts[1])
            else:
                #if we have more than 2 cuts in a given region we have a real problem so the splitter should throw an error
                logging.error(f"Too many sessions within the region {cut['desc']}. Could not combine them.")
                raise Exception(f"Too many sessions within the region {cut['desc']}")
            
            connected_ct_cut_rect = connected_ct_cut['rect']

            new_ct_cut, new_pet_cut = combine_two_rects(connected_ct_cut_rect, scaled_pet_rect, [1.0,1.0], [x_scale, y_scale])

            coregistered_cuts_ct += [{'desc': connected_ct_cut['desc'], 'rect': new_ct_cut}]
            coregistered_cuts_pet += [{'desc': cut['desc'], 'rect': new_pet_cut}]
        splitter_ct.cuts = coregistered_cuts_ct
        splitter_pet.cuts = coregistered_cuts_pet

    splitter_ct.complete_cut_process(metadata, True)
    splitter_pet.complete_cut_process(metadata, True)

    logging.info(f"\n\n\n")


def combine_two_rects(rect_one, rect_two, scale_for_rect_one, scale_for_rect_two):
    new_rect_params = [(rect_one.xlt+rect_two.xlt)/2, (rect_one.ylt+rect_two.ylt)/2, (rect_one.xrb+rect_two.xrb)/2, (rect_one.yrb+rect_two.yrb)/2]
    new_rect_one_bb = [(new_rect_params[0]/scale_for_rect_one[0]).astype(int), (new_rect_params[1]/scale_for_rect_one[1]).astype(int), (new_rect_params[2]/scale_for_rect_one[0]).astype(int), (new_rect_params[3]/scale_for_rect_one[1]).astype(int)]
    new_rect_one = Rect(bb=new_rect_one_bb, label=rect_one.label)
    new_rect_two_bb = [(new_rect_params[0]/scale_for_rect_two[0]).astype(int), (new_rect_params[1]/scale_for_rect_two[1]).astype(int), (new_rect_params[2]/scale_for_rect_two[0]).astype(int), (new_rect_params[3]/scale_for_rect_two[1]).astype(int)]
    new_rect_two = Rect(bb=new_rect_two_bb, label=rect_two.label)
    return new_rect_one, new_rect_two


def convert_hotel_scan_record(hotel_scan_record: dict, dicom: bool = False, mpet: bool = False):
    """
    Convert hotel scan record to metadata dictionary format expected by splitter of mice
    """

    logging.debug(f'convert_hotel_scan_record(hotel_scan_record={hotel_scan_record})')

    metadata = {'l': None, 'r': None, 'ctr': None, 'lb': None, 'rb': None, 'lt': None, 'rt': None}

    num_subjects = len(hotel_scan_record['hotelSubjects'])
    num_rows = max([subj['position']['y'] for subj in hotel_scan_record['hotelSubjects']])

    logging.debug(f'num_subjects={num_subjects}, num_rows={num_rows}')

    if num_rows == 1:
        hotel_subjects = sorted(hotel_scan_record['hotelSubjects'], key=lambda x: x['position']['x'])

        if num_subjects == 1:
            metadata['ctr'] = hotel_subjects[0]

        elif num_subjects == 2:
            metadata['l'] = hotel_subjects[0]
            metadata['r'] = hotel_subjects[1]

        elif num_subjects == 3:
            metadata['l'] = hotel_subjects[0]
            metadata['ctr'] = hotel_subjects[1]
            metadata['r'] = hotel_subjects[2]

        else:
            raise Exception(f'Cannot split {num_subjects} animals in one row.')

    elif num_rows == 2:
        top_row_subjects = list(filter(lambda subj: subj['position']['y'] == 1, hotel_scan_record['hotelSubjects']))
        bottom_row_subjects = list(filter(lambda subj: subj['position']['y'] == 2, hotel_scan_record['hotelSubjects']))

        n_t = len(top_row_subjects)
        n_b = len(bottom_row_subjects)

        if n_t != 2 or n_b != 2:
            raise Exception(f'Expecting 2 animals in each row. Found {n_t} in top row and {n_b} in bottom row.')

        top_row_subjects = sorted(top_row_subjects, key=lambda x: x['position']['x'])
        bottom_row_subjects = sorted(bottom_row_subjects, key=lambda x: x['position']['x'])

        metadata['lt'] = top_row_subjects[0]
        metadata['rt'] = top_row_subjects[1]
        metadata['lb'] = bottom_row_subjects[0]
        metadata['rb'] = bottom_row_subjects[1]

    else:
        raise Exception(f'Cannot split more than 2 rows of animals. Found {num_rows} rows.')

    # Update metadata keys to match dicom format
    for position in metadata.keys():
        if metadata[position]:
            hotel_subject = metadata[position]
            hotel_subject['StudyInstanceUID'] = x667_uuid()  # New UID for each animal but same across scans
            hotel_subject['PatientID'] = hotel_subject['subjectLabel'] if 'subjectLabel' in hotel_subject else 'blank'
            hotel_subject['PatientName'] = hotel_subject['subjectLabel'] if 'subjectLabel' in hotel_subject else 'blank'
            hotel_subject['PatientOrientation'] = hotel_subject['orientation'] if 'orientation' in hotel_subject else ''
            if dicom:  # Convert weight from g to kg
                hotel_subject['PatientWeight'] = hotel_subject['weight'] * pow(10, -3) if 'weight' in hotel_subject else 0
            elif mpet:
                hotel_subject['PatientWeight'] = hotel_subject['weight'] if 'weight' in hotel_subject else 0
            hotel_subject['PatientComments'] = hotel_subject['notes'] if 'notes' in hotel_subject else ''
            hotel_subject['RadiopharmaceuticalStartDate'] = hotel_subject['injectionDate'] if 'injectionDate' in hotel_subject else ''
            hotel_subject['RadiopharmaceuticalStartTime'] = hotel_subject['injectionTime'] if 'injectionTime' in hotel_subject else ''
            if dicom:  # Convert activity from mCi to MBq
                hotel_subject['RadionuclideTotalDose'] = hotel_subject['activity'] * 37 * pow(10, 6) if 'activity' in hotel_subject else 0
            elif mpet:
                hotel_subject['RadionuclideTotalDose'] = hotel_subject['activity'] if 'activity' in hotel_subject else 0

            metadata[position] = hotel_subject

    logging.debug(f'metadata={metadata}')

    return metadata


def x667_uuid():
    return '2.25.%d' % uuid.uuid4()


def delete_existing_session(session: Session, server: str, project: str, experiment: str):
    # First check if the session exists
    url = f'{server}/data/projects/{project}/experiments/{experiment}'
    parameters = {'removeFiles': 'TRUE'}

    logging.info(f'Checking if session {experiment} exists in project {project}')
    logging.debug(f'URL: {url}')
    logging.debug(f'Parameters: {parameters}')

    r = session.get(url)

    if r.ok:
        logging.info(f'Session {experiment} exists in project {project}')
    else:
        logging.info(f'Session {experiment} does not exist in project {project}')
        return

    # Then delete the session
    logging.info(f'Deleting session {experiment} from project {project}')

    r = session.delete(url, params=parameters)

    if r.ok:
        logging.info(f'Session {experiment} deleted from project {project}')
    else:
        logging.error(f'Failed to delete session {experiment} from project {project}. '
                      f'Status code: {r.status_code}, text: {r.text}, reason: {r.reason}')
        raise Exception(f'Failed to delete session {experiment} from project {project}')


def send_split_images(session: Session, server: str, project: str, subject: str, experiment: str,
                      zip_file: Path, dicom: bool):

    # Delete existing session
    experiment = experiment + "_split_" + subject
    delete_existing_session(session, server, project, experiment)

    time.sleep(5)

    dest_url = f'{server}/data/services/import'
    parameters = {
        'import-handler': 'DICOM-zip' if dicom else 'INVEON',
        'Direct-Archive': 'true',
        'overwrite': 'append',
        'PROJECT_ID': project,
        'SUBJECT_ID': subject,
        'EXPT_LABEL': experiment
    }

    logging.info(f'Uploading {zip_file} to XNAT')
    logging.debug(f'URL: {dest_url}')
    logging.debug(f'Parameters: {parameters}')

    max_attempts = 3
    attempts = 0

    while attempts < max_attempts:
        try:
            r = session.post(dest_url, params=parameters, files={'file': open(zip_file, 'rb')})

            if r.ok:
                logging.info(f'Upload successful for {zip_file}')
                break
            elif r.status_code == 504:
                logging.warning(f'Gateway timeout for {zip_file}. Typically due to large file size but the upload is '
                                f'usually successful. Will not retry. Status code: {r.status_code} - {r.text}')
                time.sleep(3)
                break
            else:
                logging.error(f'Upload failed for {zip_file}: '
                              f'status code {r.status_code}, text: {r.text}, reason: {r.reason}')
        except Exception as err:
            logging.error(f'Upload failed for {zip_file}: {err}')

        attempts += 1
        logging.warning(f'Retrying upload for {zip_file}')

        if attempts == max_attempts:
            raise Exception(f'Upload failed for {zip_file}')

    return


def send_qc_image(session: Session, server: str, project: str, experiment: str, qc_image_path: str, **kwargs):
    # create a resource on the scan record with the name QC_SNAPSHOTS_DATETIME or get from kwargs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    resource_name = f"QC_SNAPSHOTS_{timestamp}" if 'resource_name' not in kwargs else kwargs['resource_name']
    url = f"{server}/data/projects/{project}/experiments/{experiment}_scan_record/resources/{resource_name}?format=IMG&content=RAW"

    r = session.put(url)

    if r.ok:
        logging.info(f'QC image resource created for project: {project} , session: {experiment}')
    elif r.status_code == 409:
        logging.info(f'QC image resource already exists for project: {project} , session: {experiment}')
    else:
        logging.warning(
            f'Failed to create QC image resource for project: {project} , session: {experiment}, status code: {r.status_code}')
        return False

    # put image files into scan record resource
    # glob png files from qc image path and all subdirectories
    qc_images = glob.glob(f'{qc_image_path}/**/*.png', recursive=True)

    for qc_image in qc_images:
        qc_image_name = os.path.relpath(qc_image, qc_image_path)

        url = (f"{server}/data/projects/{project}/experiments/{experiment}_scan_record"
               f"/resources/{resource_name}/files/{qc_image_name}?inbody=true")

        with open(qc_image, 'rb') as f:
            r = session.put(url, data=f)

            if r.ok:
                logging.info(f'QC image {qc_image_name} uploaded to project: {project} , session: {experiment}')
            else:
                logging.warning(
                    f'Failed to upload QC image {qc_image_name} to project: {project} , session: {experiment}, status code: {r.status_code}')
                return False


def get_hotel_scan_record(session: Session, server: str, project: str, experiment: str):
    url = f"{server}/xapi/pixi/hotelscanrecords/{experiment}_scan_record/project/{project}"

    logging.info("Retrieving hotel scan record from " + url)

    r = session.get(url)

    if r.status_code == 200:
        logging.info("Hotel scan record successfully retrieved")
        return r.json()
    else:
        logging.error("Unable to fetch Hotel Scan Record from XNAT")
        raise Exception("Unable to fetch Hotel Scan Record from XNAT")


def update_scan_record(session: Session, server: str, experiment: str, hotel_scan_record: dict):

    logging.debug(f'update_scan_record(server={server}, hotel_scan_record={hotel_scan_record})')

    project = hotel_scan_record['projectID']

    subjects = {}

    for subject in hotel_scan_record['hotelSubjects']:
        subject_id = subject['subjectId'] if 'subjectId' in subject else ''
        subject_label = subject['subjectLabel'] if 'subjectLabel' in subject else ''

        if subject_id and subject_label:
            subjects[subject_id] = f"{experiment}_split_{subject_label}"

    url = f"{server}/xapi/pixi/hotelscanrecords/{experiment}_scan_record/project/{project}/subjects"

    r = session.put(url, headers={'Content-type': 'application/json'}, data=json.dumps(subjects))
    if r.ok:
        logging.info('Hotel scan record updated')
    else:
        logging.error("Failed to update hotel scan record")

    return


def update_scan_record_status(session: Session, server: str, project: str, experiment: str, status: str):
    url = f"{server}/xapi/pixi/hotelscanrecords/{experiment}_scan_record/project/{project}/status"

    r = session.put(url, headers={'Content-type': 'text/plain'}, data=status)

    if r.ok:
        logging.debug(f'Updating hotel scan record status to {status}')
    else:
        logging.error(f'update_status failed: {r.status_code} - {r.text}')

    return


def get_start_times_for_scans(session: Session, server: str, project: str, experiment: str, files):
    experiment_id = get_experiment_id_for_label(session, server, project, experiment)

    file_to_start_time= {}

    for file in files.keys():
        split_path = file.split(os.sep)
        position_of_scan_name = split_path.index("SCANS") + 1
        file_to_start_time[file] = get_scan_time_of_scan(session, server, experiment_id, split_path[position_of_scan_name])

    return file_to_start_time


def get_experiment_id_for_label(session: Session, server: str, project: str, experiment_label: str):
    url = f"{server}/data/projects/{project}/experiments"

    r = session.get(url)

    if r.status_code == 200:
        project_experiments_information = r.json()['ResultSet']["Result"]

        for experiment in project_experiments_information:
            if experiment['label'] == experiment_label:
                return experiment['ID']
        raise Exception("Could not obtain necessary experiment ID")
    else:
        logging.error("Unable to obtain experiment data for project")
        raise Exception("Unable to obtain experiment data for project")


#extract the start date/time field for the scan 
def get_scan_time_of_scan(session: Session, server: str, experiment: str, scan: str):
    payload = {'format': 'json'}
    url = f"{server}/data/experiments/{experiment}/scans/{scan}"

    r = session.get(url, params=payload)

    if r.status_code == 200:
        start_datetime = r.json()['items'][0]['meta']['start_date']
        start_datetime_in_python = datetime.strptime(start_datetime, '%a %b %d %H:%M:%S %Z %Y')
        return start_datetime_in_python
    else:
        logging.error("Unable to obtain scan time to pair CT and PET sessions")
        raise Exception("Unable to obtain scan time to pair CT and PET sessions")


if __name__ == "__main__":

    # parse arguments
    p = argparse.ArgumentParser(description='Split DICOM or Inveon PET/CT image into individual '
                                            'animal images and upload to XNAT')
    p.add_argument('input_dir', type=str, help='full path to DICOM/Inveon folder(s)')
    p.add_argument('output_dir', type=str, help='output directory')
    p.add_argument('-l', '--log-level', metavar='<str>', type=str, default='INFO', help='logging level')
    p.add_argument('-u', '--username', metavar='<str>', type=str, help='XNAT username')
    p.add_argument('-p', '--password', metavar='<str>', type=str, help='XNAT password')
    p.add_argument('-s', '--server', metavar='<str>', type=str, help='XNAT server')
    p.add_argument('-r', '--project', metavar='<str>', type=str, help='XNAT project')
    p.add_argument('-e', '--experiment', metavar='<str>', type=str, help="""
                                                                            Hotel image session experiment label in 
                                                                            XNAT to split and upload to XNAT. A hotel
                                                                            scan record must exist in XNAT for this
                                                                            experiment.
                                                                        """)

    kwargs = vars(p.parse_args())

    # setup logging
    logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout)],
                        level=logging.getLevelName(kwargs['log_level']),
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    logging.info('Starting xnat_run_splitter_of_mice program')

    # run
    try:
        run(**kwargs)
    except Exception as e:
        logging.error(f'Exception: {e}')
        sys.exit(1)

    sys.exit()
