import argparse
import datetime
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

from collections import defaultdict
from requests.auth import HTTPBasicAuth
from splitter_of_mice.splitter import SoM

# Setup splitter of mice descriptor map
SoM.desc_map = {'l': 'l', 'r': 'r', 'ctr': 'ctr', 'lb': 'lb', 'rb': 'rb', 'lt': 'lt', 'rt': 'rt'}


def run(username: str, password: str, server: str,
        project: str, experiment: str,
        input_dir: str, output_dir: str, **kwargs):
    try:
        logging.debug(f'''run(username={username}, password=*****, server={server}, 
                       project={project}, experiment={experiment}, 
                       input_dir={input_dir}, output_dir={output_dir})''')

        update_scan_record_status(username, password, server, project, experiment, status="Splitting In Progress")

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
            update_scan_record_status(username, password, server, project, experiment, "Error: No DICOM or Inveon images files found")
            sys.exit(f'No DICOM or Inveon images files found in {input_dir}')

        logging.debug(f"Create splitter and output directory for each subdirectory")

        splitters = [SoM(dicom_dir, dicom=isDicomSession) for dicom_dir in files.keys()]

        # Create output directory for each subdirectory
        output_dirs = [os.path.join(output_dir, os.path.relpath(dicom_dir, input_dir)) for dicom_dir in files.keys()]

        for output_dir in output_dirs:
            os.makedirs(output_dir, exist_ok=True)

        logging.info(f"Created {len(output_dirs)} output directories: {output_dirs}")

        logging.debug(f"Split each subdirectory")

        # Get hotel scan record
        hotel_scan_record = get_hotel_scan_record(username, password, server, project, experiment)
        num_anim = sum(1 for subj in hotel_scan_record['hotelSubjects'] if subj.get('subjectId'))

        # Convert hotel scan record to metadata dictionary format expected by splitter of mice
        metadata = convert_hotel_scan_record(hotel_scan_record, dicom=isDicomSession, mpet=not isDicomSession)

        # Get Technicians Perspective and rotate image if needed
        technicians_perspective = hotel_scan_record.get('technicianPerspective', 'Front')
        technicians_perspective = technicians_perspective.lower()

        for i, (splitter, output_dir) in enumerate(zip(splitters, output_dirs)):
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

            if technicians_perspective == 'back':
                splitter.pi.rotate_on_axis('y')

            exit_code = splitter.split_mice(output_dir, num_anim=num_anim, remove_bed=True,
                                          zip=True, dicom_metadata=metadata, output_qc=True,
                                          pet_img_size=pet_img_size, ct_img_size=ct_img_size)

            if exit_code != 0:
                raise Exception(f'Error splitting subdirectory {os.path.dirname(splitter.filename)}')

        # Upload each cut to XNAT
        # Send all scans for a subject together so the prearchive doesn't accidentally
        # archive one scan before the other.
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
                    send_split_images(username, password, server, project, subject, experiment, zip_file_path, isDicomSession)

        for splitter in splitters:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            send_qc_image(username, password, server, project, experiment,
                          splitter.pi.qc_outputs, resource_name=f"QC_SNAPSHOTS_{timestamp}")

        # update hotel scan record
        update_scan_record(username, password, server, experiment, hotel_scan_record)

        # update hotel scan record status
        update_scan_record_status(username, password, server, project, experiment, status="Split Complete")

    except Exception as e:
        logging.exception("Fatal error while splitting hotel scan: " + str(e))
        update_scan_record_status(username, password, server, project, experiment, "Error: Not Split")
        sys.exit("Fatal error while splitting hotel scan " + str(e))

    return


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


def delete_existing_session(username: str, password: str, server: str, project: str, experiment: str):
    # First check if the session exists
    url = f'{server}/data/projects/{project}/experiments/{experiment}'
    parameters = {'removeFiles': 'TRUE'}

    logging.info(f'Checking if session {experiment} exists in project {project}')
    logging.debug(f'URL: {url}')
    logging.debug(f'Parameters: {parameters}')

    r = requests.get(url, auth=HTTPBasicAuth(username, password))

    if r.ok:
        logging.info(f'Session {experiment} exists in project {project}')
    else:
        logging.info(f'Session {experiment} does not exist in project {project}')
        return

    # Then delete the session
    logging.info(f'Deleting session {experiment} from project {project}')

    r = requests.delete(url,
                        auth=HTTPBasicAuth(username, password),
                        params=parameters)

    if r.ok:
        logging.info(f'Session {experiment} deleted from project {project}')
    else:
        logging.error(f'Failed to delete session {experiment} from project {project}. '
                      f'Status code: {r.status_code}, text: {r.text}, reason: {r.reason}')
        raise Exception(f'Failed to delete session {experiment} from project {project}')


def send_split_images(username: str, password: str, server: str, project: str, subject: str, experiment: str,
                      zip_file: Path, dicom: bool):

    # Delete existing session
    experiment = experiment + "_split_" + subject
    delete_existing_session(username, password, server, project, experiment)

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
            r = requests.post(dest_url,
                              auth=HTTPBasicAuth(username, password),
                              params=parameters,
                              files={'file': open(zip_file, 'rb')})

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


def send_qc_image(username: str, password: str, server: str, project: str, experiment: str, qc_image_path: str, **kwargs):
    # create a resource on the scan record with the name QC_SNAPSHOTS_DATETIME or get from kwargs
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    resource_name = f"QC_SNAPSHOTS_{timestamp}" if 'resource_name' not in kwargs else kwargs['resource_name']
    url = f"{server}/data/projects/{project}/experiments/{experiment}_scan_record/resources/{resource_name}?format=IMG&content=RAW"

    r = requests.put(url, auth=HTTPBasicAuth(username, password))

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
            r = requests.put(url, auth=HTTPBasicAuth(username, password), data=f)

            if r.ok:
                logging.info(f'QC image {qc_image_name} uploaded to project: {project} , session: {experiment}')
            else:
                logging.warning(
                    f'Failed to upload QC image {qc_image_name} to project: {project} , session: {experiment}, status code: {r.status_code}')
                return False


def get_hotel_scan_record(username: str, password: str, server: str,
                          project: str, experiment: str):
    url = f"{server}/xapi/pixi/hotelscanrecords/{experiment}_scan_record/project/{project}"

    logging.info("Retrieving hotel scan record from " + url)

    r = requests.get(url, auth=HTTPBasicAuth(username, password))

    if r.status_code == 200:
        logging.info("Hotel scan record successfully retrieved")
        return r.json()
    else:
        logging.error("Unable to fetch Hotel Scan Record from XNAT")
        raise Exception("Unable to fetch Hotel Scan Record from XNAT")


def update_scan_record(username: str, password: str, server: str,
                       experiment: str, hotel_scan_record: dict):

    logging.debug(f'update_scan_record(username={username}, password=*****, server={server}, '
                  f'hotel_scan_record={hotel_scan_record})')

    project = hotel_scan_record['projectID']

    subjects = {}

    for subject in hotel_scan_record['hotelSubjects']:
        subject_id = subject['subjectId'] if 'subjectId' in subject else ''
        subject_label = subject['subjectLabel'] if 'subjectLabel' in subject else ''

        if subject_id and subject_label:
            subjects[subject_id] = f"{experiment}_split_{subject_label}"

    url = f"{server}/xapi/pixi/hotelscanrecords/{experiment}_scan_record/project/{project}/subjects"

    r = requests.put(url,
                     auth=HTTPBasicAuth(username, password),
                     headers={'Content-type': 'application/json'},
                     data=json.dumps(subjects))
    if r.ok:
        logging.info('Hotel scan record updated')
    else:
        logging.error("Failed to update hotel scan record")

    return


def update_scan_record_status(username: str, password: str, server: str,
                              project: str, experiment: str,
                              status: str):

    logging.debug(f'update_status(username={username}, password=*****, server={server}, '
                  f'project={project}, experiment={experiment}, '
                  f'status={status})')

    url = f"{server}/xapi/pixi/hotelscanrecords/{experiment}_scan_record/project/{project}/status"

    logging.info(f'Updating hotel scan record status at {url} to {status}')

    r = requests.put(url,
                     auth=HTTPBasicAuth(username, password),
                     headers={'Content-type': 'text/plain'},
                     data=status)

    if r.ok:
        logging.debug(f'update_status to {status} successful')
    else:
        logging.error(f'update_status failed: {r.status_code} - {r.text}')

    return


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
