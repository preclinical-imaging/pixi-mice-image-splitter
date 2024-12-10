"""
This module contains the classes used to define the image to be cut.
"""

import copy
import gc
import glob
import logging
import ntpath
import os
import shutil
import struct
import tempfile
import uuid
import warnings
import zipfile

import numpy as np
import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from datetime import datetime

# logging
logger = logging.getLogger(__name__)


# functions
def try_rm_file(path):
    try:
        os.remove(path)
    except Exception as e:
        logger.error(e)
        logger.error('Failed to remove file: {}'.format(os.path.split(path)[1]))


# classes
class Params:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class BaseImage:

    def __init__(self, filepath=None, img_data=None, frame_range=None):
        self.filepath = filepath
        self.img_data = img_data
        self.ax_map = {'z': 0, 'y': 1, 'x': 2}
        self.inv_ax_map = {v: k for k, v in self.ax_map.items()}
        self.struct_flags = {
            1: 'B',
            2: 'h',
            3: 'i',
            4: 'f'
        }
        self.frame_range = frame_range
        if filepath is not None:
            self.filename = ntpath.basename(filepath)
            fpcs = self.filename.split('_')
            if len(fpcs) >= 4:
                self.subject_id = fpcs[0] + fpcs[3].split('.')[0]
            else:
                self.subject_id = fpcs[0]
        self.cuts = []
        self.scale_factor = None
        self.scaled = None
        self.bpp = None  # bytes per pixel
        self.tempdir = None
        self.data_lim = 10 ** 7  # 10 MB
        self.rotation_history = []
        self.image_format = '.img'
        self.zip_outputs = []

        # color map for distinguishing cuts
        self.all_colors = [
            'red',
            'green',
            'blue',
            'orange',
            'magenta',
            'cyan'
        ]
        self.colors = [x for x in self.all_colors]

    def center_on_zeros(self, mat, xdim, ydim):
        if len(mat.shape) != 2:
            raise ValueError('Wrong shape matrix in center_on_zeros')
        mx, my = mat.shape
        if mx > xdim or my > ydim:
            raise ValueError('Cannot place {}x{} matrix on {}x{} matrix'.format(mx, my, xdim, ydim))
        fillmat = np.zeros((xdim, ydim))

        # find centers
        ccx, ccy = (round(mx / 2), round(my / 2))
        czx, czy = (round(xdim / 2), round(ydim / 2))

        # find indices
        sx = czx - ccx
        ex = mx + sx
        sy = czy - ccy
        ey = my + sy

        fillmat[sx:ex, sy:ey] = mat

        return fillmat

    def submemmap(self, ix, data):
        if self.tempdir is None:
            raise ValueError('self.tempdir is None in self.sub_memmap.')

        found_filename = False
        while not found_filename:
            fnpcs = self.filename.split('.')
            fnpcs[0] = fnpcs[0] + '_s{}'.format(ix)
            filename = '.'.join(fnpcs)
            img_temp_name = os.path.join(self.tempdir, '{}.dat'.format(filename.split('.')[0]))
            found_filename = not os.path.exists(img_temp_name)
            ix += 1

        dfile = np.memmap(img_temp_name, mode='w+', dtype='float32', shape=self.img_data.shape)

        # center cut on parent image dimensions
        dz, dy, dx, df = data.shape
        print('dz,dy,dx,df', dz, dy, dx, df)
        xdim = self.params.x_dimension
        ydim = self.params.y_dimension
        print('xdim,ydim', xdim, ydim)

        # find centers
        ccx, ccy = (round(dx / 2), round(dy / 2))
        czx, czy = (round(xdim / 2), round(ydim / 2))
        print('ccx,ccy,czx,czy', ccx, ccy, czx, czy)

        # find indices
        sx = czx - ccx
        ex = dx + sx
        sy = czy - ccy
        ey = dy + sy

        print('sx,ex,sy,ey', sx, ex, sy, ey)
        dfile[:, sy:ey, sx:ex, :] = data[:, :, :, :]

        return filename, dfile

    def load_header(self):
        '''
        parses parameters from header file; checks line by line if line starts with keyword;
        uses first instance of keyword unless keyword in per_frame (in which case uses np.array)
        '''

        hdr_file = open(self.header_file, 'r')
        hdr_string = hdr_file.read()
        hdr_lines = hdr_string.split('\n')

        kwrds = self.keywords
        integers = self.integers
        strings = self.strings
        per_frame = self.per_frame
        params = {kw: None for kw in kwrds}

        for kw in kwrds:
            for line in hdr_lines:
                kv = params[kw]
                try:
                    if kw == line.strip().split(' ')[0]:
                        if kw in per_frame:
                            if kv is None:
                                params[kw] = np.array([])
                            params[kw] = np.append(params[kw], float(line.strip().split(' ')[1]))
                        elif kv is None:
                            ks = line.strip().split(' ')[1]
                            if kw in integers:
                                params[kw] = int(ks)
                            elif kw in strings:
                                params[kw] = ' '.join(line.strip().split(' ')[1:])
                            else:
                                params[kw] = float(ks)
                except IndexError:
                    pass

        ok_miss = ['animal_number', 'subject_weight', 'dose', 'injection_time']
        failed = [kw for kw in kwrds if params[kw] is None and kw not in ok_miss]
        if any(failed):
            raise ValueError('Failed to parse parameters: {}'.format(', '.join(failed)))
        hdr_file.close()

        for s in self.strings:
            params[s] = '' if params[s] is None else params[s]

        self.params = Params(**params)
        return

    def load_image(self, plane_range=None, frame_range=None, unscaled=False):
        '''
        - loads specified frames into np.ndarray
        - can do range of frames now; maybe implement list of frames
        - same for z-dimension
        - does not support selection over x,y dimensions
        - returns scaled image data;
        - planes and frames should both be tuples corresponding to the range of planes and frames to be
        returned from the image data;
        - defaults to all data;
        - for single plane or single frame, just give n where n is the index
        of the plane or frame to include;
        - index from 0, e.g. for the first 40 planes, use [0,39]
        '''

        def read_chunks(ifr):
            '''
            Trying to read data in chunks to handle HiResCt images
            '''
            to_read = bpp * matsize
            read_lim = self.data_lim
            # print('Will read {0} {1}MB chunks.'.format(to_read/read_lim,int(read_lim/10**6)))
            ix = 0
            while to_read > read_lim:
                # print('Reading new chunk; {}MB left'.format(int(to_read/10**6)))
                nbytes = read_lim
                npixels = int(nbytes / bpp)
                chunk = np.array(struct.unpack(sf * npixels, img_file.read(nbytes)))
                imgmat[ifr][ix:ix + npixels] = chunk
                to_read -= read_lim
                ix += npixels

            # print('Reading new chunk; {}MB left'.format(int(to_read/10**6)))
            nbytes = to_read
            npixels = int(nbytes / bpp)
            chunk = np.array(struct.unpack(sf * npixels, img_file.read(nbytes)))
            imgmat[ifr][ix:ix + npixels] = chunk

        x, y, z, fs = self.params.x_dimension, self.params.y_dimension, self.params.z_dimension, self.params.total_frames
        print('File dimensions: ({},{},{},{})'.format(x, y, z, fs))
        ps = self.params

        if self.tempdir is None:
            self.tempdir = tempfile.mkdtemp()

        if plane_range is None:
            if ps.z_dimension > 1:
                plane_range = [0, ps.z_dimension - 1]
            else:
                plane_range = [0, 0]
        elif type(plane_range) is int:
            plane_range = [plane_range, plane_range]
        else:
            plane_range = list(plane_range)
            if plane_range[-1] >= self.params.z_dimension:
                plane_range[-1] = self.params.z_dimension - 1
                warnings.warn(
                    'Input z-plane range exceeds number of z-planes in data file.  Usings z-planes {}.'.format(
                        plane_range))

        if frame_range is None:
            if ps.total_frames > 1:
                frame_range = [0, ps.total_frames - 1]
            else:
                frame_range = [0, 0]
        elif type(frame_range) is int:
            frame_range = [frame_range, frame_range]
        else:
            frame_range = list(frame_range)
            if frame_range[-1] >= self.params.total_frames:
                frame_range[-1] = self.params.total_frames - 1
                warnings.warn(
                    'Input frame range exceeds number of frames in data file.  Usings frames {}.'.format(frame_range))

        if plane_range[1] > plane_range[0]:
            multi_plane = True
        else:
            multi_plane = False
        if frame_range[1] > frame_range[0]:
            multi_frame = True
        else:
            multi_frame = False

        pl, fr = plane_range, frame_range
        self.plane_range, self.frame_range = pl, fr

        # some calcs with params
        if self.type == 'pet':
            axial_fov = ps.axial_blocks * ps.axial_crystals_per_block * ps.axial_crystal_pitch + ps.axial_crystal_pitch
            Iz_size = ps.z_dimension
            Iz_pixel = axial_fov / ps.z_dimension
            aspect = Iz_pixel / ps.pixel_size
            calib_scale_factor = ps.scale_factor * (ps.calibration_factor / ps.isotope_branching_fraction);

        # which planes/frames to use
        npl = len(pl)
        nfr = len(fr)

        if npl > 2:
            raise ValueError('Input plane range invalid format: {}'.format(pl))
        else:
            if not multi_plane:
                pl1 = pl[0]
                pl2 = pl[0]
                planes = [pl1, ]
                nplanes = 1
            else:
                pl1 = pl[0]
                pl2 = pl[1]
                planes = range(pl1, pl2 + 1)
                nplanes = len(planes)

        if nfr > 2:
            raise ValueError('Input frame range invalid format: {}'.format(fr))
        else:
            if not multi_frame:
                fr1 = fr[0]
                fr2 = fr[0]
                frames = [fr1, ]
                nframes = 1
            else:
                fr1 = fr[0]
                fr2 = fr[1]
                frames = range(fr1, fr2 + 1)
                nframes = len(frames)
        self.nframes = nframes

        # file data format parameters
        bytes_per_pixel = {
            1: 1,
            2: 2,
            3: 4,
            4: 4
        }

        bpp = bytes_per_pixel[ps.data_type]
        self.bpp = bpp
        sf = self.struct_flags[ps.data_type]

        # read data from file
        print('Reading microPET image data...')

        img_file = open(self.filepath, 'rb')
        matsize = ps.x_dimension * ps.y_dimension * nplanes
        pl_offset = pl[0] * (ps.x_dimension * ps.y_dimension)

        # make tempfile for whole image
        img_temp_name = os.path.join(self.tempdir, '{}.dat'.format(self.filename.split('.')[0]))
        imgmat = np.memmap(img_temp_name, mode='w+', dtype='float32', shape=(nframes, matsize))

        for ifr in frames:
            fr_offset = ifr * (ps.x_dimension * ps.y_dimension * ps.z_dimension)
            img_file.seek(bpp * (fr_offset + pl_offset))
            read_chunks(ifr)
        imgmat = imgmat.swapaxes(0, 1)
        img_file.close()

        # scale data
        if unscaled:
            self.img_data = imgmat
            self.scaled = False
        else:
            imgmat = imgmat.reshape(nplanes, ps.x_dimension, ps.y_dimension, nframes)
            if multi_plane and (not multi_frame):
                imgmat = imgmat[0:nplanes, :, :, 0]
                self.scale_factor = ps.scale_factor[fr1]
            elif (not multi_plane) and multi_frame:
                imgmat = imgmat[0, :, :, 0:nframes]
                self.scale_factor = ps.scale_factor[fr1:fr2 + 1]
            elif (not multi_plane) and (not multi_frame):
                imgmat = imgmat[0, :, :, 0]
                self.scale_factor = ps.scale_factor[fr1]
            else:
                imgmat = imgmat[0:nplanes, :, :, 0:nframes]
                self.scale_factor = ps.scale_factor[fr1:fr2 + 1]
            imgmat = imgmat * self.scale_factor
            self.img_data = imgmat.reshape(nplanes, ps.y_dimension, ps.x_dimension, nframes)
            self.scaled = True

        return

    def save_cut(self, index, path, zip=False):
        def zip_cut(img_file, hdr_file, zip_file):
            with zipfile.ZipFile(zip_file, 'w') as zfile:
                zfile.write(img_file, os.path.basename(img_file))
                zfile.write(hdr_file, os.path.basename(hdr_file))

            return

        def add_animal_number(hdr_lines, animal_number):
            for i, line in enumerate(hdr_lines):
                if line.strip().startswith('subject_identifier'):
                    return hdr_lines[:i + 1] + [
                        '#', '# animal_number (string)', '#',
                        'animal_number {}'.format(animal_number.strip())
                    ] + hdr_lines[i + 1:]

        def change_line(hdr_lines, hdr_var, value):
            '''
            Update line to match value in parameters (user input)
            '''
            for j, line in enumerate(hdr_lines):
                if line.strip().startswith(hdr_var + ' ') or line.strip() == hdr_var:
                    hdr_lines[j] = ' '.join([hdr_var, value])
                    break
            return hdr_lines

        def get_line_value(hdr_lines, hdr_var):
            '''
            Get value from line in header file
            '''
            for line in hdr_lines:
                if line.strip().startswith(hdr_var + ' ') or line.strip() == hdr_var:
                    return line.strip(hdr_var).strip()
            return None

        def write_chunks(data, dfile):
            '''
            Trying to read data in chunks to handle HiResCt images
            '''
            if self.bpp is None:
                raise ValueError('self.bpp not defined in self.save_cuts')
            bpp = self.bpp

            total_pixels = len(data)
            bytes_to_write = total_pixels * bpp
            write_lim = self.data_lim
            print('Will write {0} {1}MB chunks.'.format(bytes_to_write / write_lim, int(write_lim / 10 ** 6)))
            ix = 0
            while bytes_to_write > write_lim:
                print('Writing new chunk; {}MB left'.format(int(bytes_to_write / 10 ** 6)))
                nbytes = write_lim
                npixels = int(nbytes / bpp)
                chunk = data[ix:ix + npixels]
                dfile.write(struct.pack(npixels * sf, *chunk))
                bytes_to_write -= write_lim
                ix += npixels

            print('Writing new chunk; {}MB left'.format(int(bytes_to_write / 10 ** 6)))
            nbytes = bytes_to_write
            npixels = int(nbytes / bpp)
            chunk = data[ix:ix + npixels]
            dfile.write(struct.pack(npixels * sf, *chunk))
            return

        print('Saving files...')
        if not self.cuts:
            raise ValueError('Image has not been cut in BaseImage.save_cuts()')
        if path is None:
            raise ValueError('Path not specified')
        sf = self.struct_flags[self.params.data_type]

        hdr_file = open(self.header_file, 'r')
        hdr_string = hdr_file.read()
        hdr_lines = hdr_string.split('\n')

        '''
        Might need to be careful of aliasing, memory, memmaps here.  will image be flipped if saving is interrupted
        by overwrite warning on a cut besides the first?
        '''

        cut_img = self.cuts[index]
        metadata = cut_img.metadata

        # update header variables
        cut_hdr_lines = hdr_lines
        vars_to_update = ['x_dimension', 'y_dimension', 'z_dimension', 'subject_weight']
        if self.type == 'pet':
            vars_to_update += ['dose', 'injection_time']

        if metadata:  # Metadata from hotel scan record
            if 'PatientID' in metadata:
                setattr(cut_img.params, 'subject_identifier', metadata['PatientID'])
                vars_to_update += ['subject_identifier']
            if 'PatientWeight' in metadata:
                setattr(cut_img.params, 'subject_weight', metadata['PatientWeight'])
                # already in vars_to_update
            if 'PatientOrientation' in metadata:
                orientations = {  # 0 is unknown
                    'FFP': 1,
                    'HFP': 2,
                    'FFS': 3,
                    'HFS': 4,
                    'FFDR': 5,
                    'HFDR': 6,
                    'FFDL': 7,
                    'HFDL': 8,
                }

                if metadata['PatientOrientation'] in orientations:
                    setattr(cut_img.params, 'subject_orientation', orientations[metadata['PatientOrientation']])
                else:
                    setattr(cut_img.params, 'subject_orientation', 0)

                vars_to_update += ['subject_orientation']
            if 'PatientComments' in metadata:
                setattr(cut_img.params, 'acquisition_notes', metadata['PatientComments'])
                vars_to_update += ['acquisition_notes']
            if 'RadiopharmaceuticalStartTime' in metadata:
                injection_date_time = get_line_value(cut_hdr_lines, 'scan_time')
                injection_date_time_split = injection_date_time.split(' ')
                injection_date_time_split[3] = f"{metadata['RadiopharmaceuticalStartTime'][:2]}:{metadata['RadiopharmaceuticalStartTime'][2:4]}:{metadata['RadiopharmaceuticalStartTime'][4:]}"  # HH:MM:SS
                injection_date_time = ' '.join(injection_date_time_split)
                setattr(cut_img.params, 'injection_time', injection_date_time)
                # already in vars_to_update if PET
            if 'RadiopharmaceuticalStartDate' in metadata and 'RadiopharmaceuticalStartTime' in metadata:
                # This will overwrite the injection time if it is already set above
                # Convert date and time from YYYYMMDD and HH:MM:SS to %a %b %-d %H:%M:%S %Y
                year = metadata['RadiopharmaceuticalStartDate'][:4]
                month = metadata['RadiopharmaceuticalStartDate'][4:6]
                day = metadata['RadiopharmaceuticalStartDate'][6:]
                hour = metadata['RadiopharmaceuticalStartTime'][:2]
                minute = metadata['RadiopharmaceuticalStartTime'][2:4]
                second = metadata['RadiopharmaceuticalStartTime'][4:]
                injection_date_time = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second)).strftime('%a %b %-d %H:%M:%S %Y')
                setattr(cut_img.params, 'injection_time', injection_date_time)
                # already in vars_to_update if PET
            if 'RadionuclideTotalDose' in metadata:
                setattr(cut_img.params, 'dose', metadata['RadionuclideTotalDose'])
                # already in vars_to_update if PET

        for v in vars_to_update:
            cut_hdr_lines = change_line(cut_hdr_lines, v, str(getattr(cut_img.params, v)))

        cut_filename = cut_img.out_filename
        # print('cut_filename ', cut_filename)
        cut_hdr_name = cut_filename + '.hdr'
        cut_hdr_str = '\n'.join(cut_hdr_lines)

        # print('writing header to ',os.path.join(path,cut_hdr_name))
        with open(os.path.join(path, cut_hdr_name), 'w') as hf:
            hf.write(cut_hdr_str)

        out_data = cut_img.img_data
        # print('out_data.shape',out_data.shape)

        out_data = out_data.reshape(cut_img.xdim * cut_img.ydim * cut_img.zdim, cut_img.nframes)

        if self.scaled:
            inv = lambda x: 1 / x
            v_inv = np.vectorize(inv)
            inv_scale_factor = v_inv(self.scale_factor)
            out_data = out_data * inv_scale_factor

        # prepare data to write out
        out_data = out_data.swapaxes(0, 1).flatten()

        # make sure data is int if it is supposed to be
        if sf in ['i', 'B', 'h']:
            out_data = out_data.astype(int)
        print('writing microPET image to ', os.path.join(path, cut_filename))
        with open(os.path.join(path, cut_filename), 'wb') as dfile:
            write_chunks(out_data, dfile)
        print('File saved.')

        # Zip the cut if requested
        if zip:
            logger.debug(f'Zipping cut {index} to {path}...')
            zip_cut(os.path.join(path, cut_filename),
                    os.path.join(path, cut_hdr_name),
                    os.path.join(path, cut_filename + '.zip'))

            try:
                patient_id = self.cuts[index].metadata['PatientID']
                self.zip_outputs.append((patient_id, os.path.join(path, cut_filename + '.zip')))
            except AttributeError:
                logger.error('PatientID not found in metadata. Unable to add to zip_outputs.')
                raise Exception('PatientID not found in metadata. Unable to add to zip_outputs.')

        out_data = None
        gc.collect()

    def clean_cuts(self):
        '''
        remove existing cuts
        '''
        self.colors = [x for x in self.all_colors]
        for cut in self.cuts:
            try:
                delattr(cut, 'img_data')
            except AttributeError:
                pass
            fn = '{}.dat'.format(cut.filename.split('.')[0])

            del cut

            if self.tempdir is None:
                self.tempdir = tempfile.mkdtemp()

            fp = os.path.join(self.tempdir, fn)
            if os.path.exists(fp):
                try_rm_file(fp)

        self.cuts = []
        gc.collect()

    def unload_image(self):
        self.clean_cuts()
        self.img_data = None
        gc.collect()
        if self.tempdir:
            shutil.rmtree(self.tempdir)
        self.tempdir = None

    def get_axis(self, axis):
        '''
        converts axis x,y,z to 2,1,0 for use with numpy
        '''
        if axis not in ['x', 'y', 'z'] + list(range(3)):
            raise ValueError('Invalid axis input: {}\nUse axis in ["x","y",z",1,2,3].'.format(axis))
        try:
            axis = self.ax_map[axis]
        except KeyError:
            pass
        return axis

    def check_data(self):
        if self.img_data is None:
            raise ValueError('self.img_data has not been intialized. Use image.load_image()')

    def check_collapse_method(self, method):
        if method not in ['sum', 'mean', 'max']:
            raise ValueError('Unrecognized input collapse method: {}'.format(method))

    def get_frame(self, n):

        self.check_data()

        if self.frame_range is None:
            raise ValueError('self.frame_range has not been declared in self.get_frame()')

        f1, f2 = tuple(self.frame_range)
        if n not in range(f1, f2 + 1):
            raise IndexError('Specified frame {0} is not in loaded range {1}'.format(n, self.frame_range))
        return self.img_data[:, :, :, f1 - n]

    def collapse_frame(self, axis, frame=None, method='sum'):
        if frame is None:
            matrix = self.img_data
        else:
            matrix = self.get_frame(frame)
        ax = self.get_axis(axis)
        self.check_collapse_method(method)
        cmatrix = getattr(matrix, method)(axis=ax)
        return cmatrix

    def collapse_over_frames(self, method, matrix=None):
        if matrix is None:
            matrix = self.img_data
        self.check_collapse_method(method)
        return getattr(self.img_data, method)(axis=3)

    def rotate_on_axis(self, axis, log=False):
        self.check_data()
        axis = self.get_axis(axis)
        if log:
            self.rotation_history.append(axis)
        axes_to_flip = [0, 1, 2]
        axes_to_flip.remove(axis)
        self.img_data = np.flip(self.img_data, axes_to_flip[0])
        self.img_data = np.flip(self.img_data, axes_to_flip[1])

    def split_on_axis(self, matrix, axis):
        axis = self.get_axis(axis)
        mats = np.split(matrix, matrix.shape[axis], axis=axis)
        mats = [np.squeeze(m) for m in mats]
        return mats

    def get_shape(self, axis=None):
        self.check_data()
        if axis is None:
            return self.img_data.shape
        else:
            return self.img_data.shape[self.get_axis(axis)]


class SubImage(BaseImage):

    def __init__(self, parent_image, img_data, filename, cut_coords, linecolor='red',
                 desc=None, metadata=None, **kwargs):

        self.filename = filename

        self.out_filename = filename

        BaseImage.__init__(self, filepath='./{}'.format(self.filename), img_data=img_data)
        self.type = parent_image.type
        self.parent_image = parent_image
        self.frame_range = parent_image.frame_range
        self.plane_range = parent_image.plane_range
        self.scaled = parent_image.scaled
        self.cut_coords = cut_coords
        shape = self.img_data.shape
        self.zdim, self.ydim, self.xdim, self.nframes = shape
        self.x_dimension, self.y_dimension, self.z_dimension = self.xdim, self.ydim, self.zdim
        self.params = copy.copy(parent_image.params)
        reset_params = ['animal_number', 'subject_weight', 'dose', 'injection_time']
        for p in reset_params:
            if hasattr(self.params, p):
                setattr(self.params, p, '')

        if hasattr(self.params, 'x_dimension'):
            setattr(self.params, 'x_dimension', self.xdim)

        if hasattr(self.params, 'y_dimension'):
            setattr(self.params, 'y_dimension', self.ydim)

        if hasattr(self.params, 'z_dimension'):
            setattr(self.params, 'z_dimension', self.zdim)

        if hasattr(self.params, 'total_frames'):
            setattr(self.params, 'total_frames', self.nframes)

        self.bounds = {0: (self.ydim, self.xdim),
                       1: (self.xdim, self.zdim),
                       2: (self.zdim, self.ydim)}

        self.linecolor = linecolor

        self.metadata = metadata


class PETImage(BaseImage):

    def __init__(self, filepath, img_data=None):
        """
        Needs header file and data file in same directory
        """
        BaseImage.__init__(self, filepath=filepath, img_data=img_data)
        self.type = 'pet'

        # for header file info
        self.params = None
        self.keywords = [
            'axial_blocks',
            'axial_crystals_per_block',
            'axial_crystal_pitch',
            'data_type',
            'z_dimension',
            'x_dimension',
            'y_dimension',
            'pixel_size',
            'total_frames',
            'calibration_factor',
            'scale_factor',
            'isotope_branching_fraction',
            'frame_duration',
            'animal_number',
            'subject_weight',
            'dose',
            'injection_time']
        self.integers = ['data_type', 'z_dimension', 'total_frames', 'x_dimension', 'y_dimension']
        self.per_frame = ['scale_factor', 'frame_duration']
        self.strings = ['injection_time', 'animal_number', 'subject_weight', 'dose']

        self.header_file = filepath + '.hdr'

        self.load_header()  # initialize params
        self.xdim = self.params.x_dimension
        self.ydim = self.params.y_dimension
        self.zdim = self.params.z_dimension
        self.x_dimension, self.y_dimension, self.z_dimension = self.xdim, self.ydim, self.zdim

        self.frame_range = None
        self.plane_range = None
        self.nframes = None

        self.bounds = {0: (self.ydim, self.xdim),
                       1: (self.xdim, self.zdim),
                       2: (self.zdim, self.ydim)}
        self.scaled = None


class CTImage(BaseImage):

    def __init__(self, filepath, img_data=None):
        BaseImage.__init__(self, filepath=filepath, img_data=img_data)
        self.type = 'ct'
        self.params = None
        self.header_file = filepath + '.hdr'

        self.keywords = [
            'data_type',
            'z_dimension',
            'x_dimension',
            'y_dimension',
            'pixel_size',
            'total_frames',
            'scale_factor',
            'animal_number',
            'frame_duration',
            'subject_weight']

        self.integers = ['data_type', 'z_dimension', 'total_frames', 'x_dimension', 'y_dimension']
        self.per_frame = ['scale_factor', 'frame_duration']
        self.strings = ['animal_number', 'subject_weight']
        self.load_header()
        self.xdim = self.params.x_dimension
        self.ydim = self.params.y_dimension
        self.zdim = self.params.z_dimension
        self.x_dimension, self.y_dimension, self.z_dimension = self.xdim, self.ydim, self.zdim

        self.frame_range = None
        self.plane_range = None
        self.nframes = None

        self.bounds = {0: (self.ydim, self.xdim),
                       1: (self.xdim, self.zdim),
                       2: (self.zdim, self.ydim)}
        self.scaled = None


class DicomImage(BaseImage):

    def __init__(self, filepath, img_data=None, **kwargs):
        BaseImage.__init__(self, filepath=filepath, img_data=img_data)

        self.dicom_files = None
        self.modality = None
        self.type = 'dicom'
        self.image_format = 'dicom'
        self.params = None
        self.plane_range = None
        self.frame_range = None
        self.qc_outputs = None

        if os.path.isdir(filepath):
            self.filename = f'{os.path.basename(filepath)}.dcm'

    def load_header(self):
        logger.info('Skipping header load for DicomImage.')

    def load_image(self, **kwargs):
        logger.debug('Loading dicom image(s)')
        if os.path.isdir(self.filepath):
            self.load_image_from_dir()
        else:
            self.load_image_from_file()

    def load_image_from_dir(self, **kwargs):
        logger.debug(f'Loading dicom images from directory {self.filepath}')
        # Get all the .dcm files in the filepath
        self.dicom_files = glob.glob(os.path.join(self.filepath, '*.dcm'))

        # Get all the modality types as a set
        modalities = set()
        for dicom_file in self.dicom_files:
            modalities.add(pydicom.dcmread(dicom_file).Modality)

        # Log the modalities found
        logger.info(f'Modalities found: {modalities}')

        # Join the modalities into a string, sorted alphabetically
        self.modality = '-'.join(sorted(modalities, key=str.lower))

        # Sort dicom files by InstanceNumber
        self.dicom_files.sort(key=lambda x: pydicom.dcmread(x).InstanceNumber)

        # Load each image file into a single ndarray
        img_data = np.stack([pydicom.dcmread(dicom_file).pixel_array for dicom_file in self.dicom_files])
        img_data = img_data[..., np.newaxis]
        self.img_data = img_data

    def load_image_from_file(self):
        logger.debug(f'Loading dicom image from file {self.filepath}')
        ds = pydicom.dcmread(self.filepath)
        self.modality = ds.Modality
        self.img_data = ds.pixel_array

    def save_cut(self, index, path, zip=False):
        logger.debug(f'Saving dicom cut {index} to {path}...')

        patient_id = None

        study_instance_uid = self.x667_uuid()
        series_instance_uid = self.x667_uuid()

        for idx, dicom_file in enumerate(self.dicom_files):
            original_ds = pydicom.dcmread(dicom_file)
            split_ds = copy.deepcopy(original_ds)

            # Update metadata
            metadata = self.cuts[index].metadata

            split_ds.ImageType = ['DERIVED', 'PRIMARY', 'SPLIT']
            split_ds.DerivationDescription = 'Original volume split into equal subvolumes for each patient'
            split_ds.DerivationImageSequence = self.derive_image_sequence(
                copy.deepcopy(split_ds.SOPClassUID),
                copy.deepcopy(split_ds.SOPInstanceUID)
            )
            split_ds.SourcePatientGroupIdentificationSequence = self.derive_source_patient_group(
                copy.deepcopy(split_ds.PatientID)
            )

            split_ds.StudyInstanceUID = study_instance_uid
            split_ds.SeriesInstanceUID = series_instance_uid

            split_ds.SOPInstanceUID = self.x667_uuid()
            split_ds.file_meta.MediaStorageSOPInstanceUID = split_ds.SOPInstanceUID

            split_ds.StorageMediaFileSetUID = series_instance_uid

            if metadata is not None:
                if 'StudyInstanceUID' in metadata:
                    split_ds.StudyInstanceUID = metadata['StudyInstanceUID']
                if 'PatientID' in metadata:
                    split_ds.PatientID = metadata['PatientID']
                    patient_id = metadata['PatientID']
                if 'PatientName' in metadata:
                    split_ds.PatientName = metadata['PatientName']
                if 'PatientWeight' in metadata:
                    split_ds.PatientWeight = metadata['PatientWeight']
                if 'PatientOrientation' in metadata:
                    split_ds.PatientOrientation = metadata['PatientOrientation']
                if 'PatientComments' in metadata:
                    split_ds.PatientComments = metadata['PatientComments']

                if split_ds.Modality == 'PT' and 'RadiopharmaceuticalInformationSequence' in split_ds:
                    if 'RadiopharmaceuticalStartTime' in metadata:
                        split_ds.RadiopharmaceuticalInformationSequence[0].RadiopharmaceuticalStartTime = metadata['RadiopharmaceuticalStartTime']
                    if 'RadiopharmaceuticalStartDate' in metadata and 'RadiopharmaceuticalStartTime' in metadata:
                        split_ds.RadiopharmaceuticalInformationSequence[0].RadiopharmaceuticalStartDateTime = f'{metadata["RadiopharmaceuticalStartDate"]}{metadata["RadiopharmaceuticalStartTime"]}'
                    if 'RadionuclideTotalDose' in metadata:
                        split_ds.RadiopharmaceuticalInformationSequence[0].RadionuclideTotalDose = metadata['RadionuclideTotalDose']

            if 'SeriesDescription' in split_ds and split_ds.SeriesDescription:
                split_ds.SeriesDescription += f' split {patient_id}'
            else:
                split_ds.SeriesDescription = f'split {patient_id}'

            # Update PixelData
            split_ds.PixelData = self.cuts[index].img_data[idx, :, :, 0].tobytes()
            split_ds.Rows, split_ds.Columns = self.cuts[index].img_data[idx, :, :, 0].shape

            # Check if path exists, if not create it
            if not os.path.exists(path):
                os.makedirs(path)

            if not os.path.exists(os.path.join(path, f'{index}')):
                os.makedirs(os.path.join(path, f'{index}'))

            # Save the file
            logger.debug(f'Saving dicom file {split_ds.SOPInstanceUID} to {path}')
            filename = f'{split_ds.SOPInstanceUID}.dcm'
            split_ds.save_as(os.path.join(path, f'{index}', filename))

        if zip:
            logger.debug(f'Zipping dicom cut {index} to {path}...')

            zip_filepath = os.path.join(path, f'{index}.zip')

            with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
                for dcm_file in glob.glob(os.path.join(path, f'{index}', '*.dcm')):
                    zip_file.write(dcm_file, os.path.relpath(dcm_file, path))

            self.zip_outputs.append((patient_id, zip_filepath))

            logger.debug(f'Zip file saved to {zip_filepath}')

    def reset_zip_outputs(self):
        self.zip_outputs = []

    @staticmethod
    def x667_uuid():
        return '2.25.%d' % uuid.uuid4()

    def derive_source_patient_group(self, patient_id):
        source_patient = Dataset()
        source_patient.PatientID = patient_id
        return Sequence([source_patient])

    def derive_image_sequence(self, sop_class_uid, sop_instance_uid):
        source_image = Dataset()
        source_image.ReferencedSOPClassUID = sop_class_uid
        source_image.ReferencedSOPInstanceUID = sop_instance_uid

        purpose_of_reference = Dataset()
        purpose_of_reference.CodeValue = '113130'
        purpose_of_reference.CodingSchemeDesignator = 'DCM'
        purpose_of_reference.CodeMeaning = \
            'Predecessor containing group of imaging subjects'
        source_image.PurposeOfReferenceCodeSequence = \
            Sequence([purpose_of_reference])
        derivation_image = Dataset()
        derivation_image.SourceImageSequence = Sequence([source_image])
        derivation_code = Dataset()
        derivation_code.CodeValue = '113131'
        derivation_code.CodingSchemeDesignator = 'DCM'
        derivation_code.CodeMeaning = \
            'Extraction of individual subject from group'
        derivation_image.DerivationCodeSequence = Sequence([derivation_code])
        derivation_image_sequence = Sequence([derivation_image])

        return derivation_image_sequence

