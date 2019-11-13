'''
Program: splitter_of_mice.py
Authors: Mikhail Milchenko (animal detection), Jack Muskopf (microPET image i/o)
Description: split microPET mice images into individual animal images

Copyright 2017-2019
Washington University, Mallinckrodt Insitute of Radiology. All rights reserved. 
This software may not be reproduced, copied, or distributed without written permission of Washington University. 
For more information contact Mikhail Milchenko, PhD
'''

import os
import sys
import numpy as np
import ntpath
import warnings
import tempfile
import struct
import copy
import gc
import shutil

#comment out the next line if running outside of Jupyter notebooks.
import ipywidgets as ipw
from PIL import Image
from io import BytesIO
import inspect
import nibabel
import skimage
from skimage import measure, filters
import argparse

class Params:
    def __init__(self,**kwargs):
        self.__dict__.update(kwargs)
       
class BaseImage:

    def __init__(self, filepath=None, img_data=None, frame_range=None):
        self.filepath = filepath
        self.img_data = img_data
        self.ax_map = {'z':0,'y':1,'x':2}
        self.inv_ax_map = {v:k for k,v in self.ax_map.items()}
        self.struct_flags = {
                                1:'B',
                                2:'h',
                                3:'i',
                                4:'f'
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
        self.bpp = None # bytes per pixel
        self.tempdir = None
        self.data_lim = 10**7  # 10 MB
        self.rotation_history = []

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
        mx,my = mat.shape
        if mx > xdim or my > ydim:
            raise ValueError('Cannot place {}x{} matrix on {}x{} matrix'.format(mx,my,xdim,ydim))
        fillmat = np.zeros((xdim,ydim))

        # find centers
        ccx,ccy = (round(mx/2),round(my/2))
        czx,czy = (round(xdim/2),round(ydim/2))

        # find indices
        sx = czx - ccx
        ex = mx + sx
        sy = czy - ccy
        ey = my + sy

        fillmat[sx:ex,sy:ey] = mat

        return fillmat


    def submemmap(self, ix, data):
        if self.tempdir is None:
            raise ValueError('self.tempdir is None in self.sub_memmap.')

        
        found_filename = False
        while not found_filename:
            fnpcs = self.filename.split('.')
            fnpcs[0] = fnpcs[0] + '_s{}'.format(ix)
            filename = '.'.join(fnpcs)
            img_temp_name = os.path.join(self.tempdir,'{}.dat'.format(filename.split('.')[0]))
            found_filename = not os.path.exists(img_temp_name)
            ix+=1

        dfile = np.memmap(img_temp_name, mode='w+', dtype='float32', shape=self.img_data.shape)

        # center cut on parent image dimensions
        dz,dy,dx,df = data.shape
        print('dz,dy,dx,df',dz,dy,dx,df)
        xdim = self.params.x_dimension
        ydim = self.params.y_dimension
        print('xdim,ydim',xdim,ydim)
        
        # find centers
        ccx,ccy = (round(dx/2),round(dy/2))
        czx,czy = (round(xdim/2),round(ydim/2))
        print('ccx,ccy,czx,czy',ccx,ccy,czx,czy)
        
        # find indices
        sx = czx - ccx
        ex = dx + sx
        sy = czy - ccy
        ey = dy + sy

        print('sx,ex,sy,ey',sx,ex,sy,ey)
        dfile[:,sy:ey,sx:ex,:] = data[:,:,:,:]

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
        params = {kw : None for kw in kwrds}

        for kw in kwrds:
            for line in hdr_lines:
                kv = params[kw]
                try:
                    if kw ==  line.strip().split(' ')[0]:
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

        ok_miss = ['animal_number','subject_weight','dose','injection_time']
        failed = [kw for kw in kwrds if params[kw] is None and kw not in ok_miss]
        if any(failed):
            raise ValueError('Failed to parse parameters: {}'.format(', '.join(failed)))
        hdr_file.close()

        for s in self.strings:
            params[s] = '' if params[s] is None else params[s]

        self.params = Params(**params)
        return


    def load_image(self,plane_range=None,frame_range=None,unscaled=False):
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
            to_read = bpp*matsize
            read_lim = self.data_lim
            # print('Will read {0} {1}MB chunks.'.format(to_read/read_lim,int(read_lim/10**6)))
            ix = 0
            while to_read > read_lim:
                # print('Reading new chunk; {}MB left'.format(int(to_read/10**6)))
                nbytes = read_lim
                npixels = int(nbytes/bpp)
                chunk = np.array(struct.unpack(sf*npixels,img_file.read(nbytes)))
                imgmat[ifr][ix:ix+npixels] = chunk
                to_read -= read_lim
                ix+=npixels

            # print('Reading new chunk; {}MB left'.format(int(to_read/10**6)))
            nbytes = to_read
            npixels = int(nbytes/bpp)
            chunk = np.array(struct.unpack(sf*npixels,img_file.read(nbytes)))
            imgmat[ifr][ix:ix+npixels] = chunk



        x,y,z,fs = self.params.x_dimension,self.params.y_dimension,self.params.z_dimension,self.params.total_frames
        print('File dimensions: ({},{},{},{})'.format(x,y,z,fs))
        ps = self.params

        if self.tempdir is None:
            self.tempdir = tempfile.mkdtemp()

        if plane_range is None:
            if ps.z_dimension > 1:
                plane_range = [0, ps.z_dimension-1]
            else:
                plane_range = [0,0]
        elif type(plane_range) is int:
            plane_range = [plane_range,plane_range]
        else:
            plane_range = list(plane_range)
            if plane_range[-1] >= self.params.z_dimension:
                plane_range[-1] = self.params.z_dimension-1
                warnings.warn('Input z-plane range exceeds number of z-planes in data file.  Usings z-planes {}.'.format(plane_range))


        if frame_range is None:
            if ps.total_frames > 1:
                frame_range = [0, ps.total_frames-1]
            else:
                frame_range = [0,0]
        elif type(frame_range) is int:
            frame_range = [frame_range,frame_range]
        else:
            frame_range = list(frame_range)
            if frame_range[-1] >= self.params.total_frames:
                frame_range[-1] = self.params.total_frames-1
                warnings.warn('Input frame range exceeds number of frames in data file.  Usings frames {}.'.format(frame_range))


        if plane_range[1]>plane_range[0]:
            multi_plane = True
        else:
            multi_plane = False
        if frame_range[1]>frame_range[0]:
            multi_frame = True
        else:
            multi_frame = False


        pl,fr = plane_range,frame_range
        self.plane_range,self.frame_range = pl,fr

        
        # some calcs with params
        if self.type == 'pet':
            axial_fov=ps.axial_blocks*ps.axial_crystals_per_block*ps.axial_crystal_pitch+ps.axial_crystal_pitch
            Iz_size=ps.z_dimension
            Iz_pixel=axial_fov/ps.z_dimension
            aspect=Iz_pixel/ps.pixel_size
            calib_scale_factor=ps.scale_factor*(ps.calibration_factor/ps.isotope_branching_fraction);
            
        
        # which planes/frames to use
        npl = len(pl)
        nfr = len(fr)

        if npl > 2:
            raise ValueError('Input plane range invalid format: {}'.format(pl))
        else:
            if not multi_plane:
                pl1 = pl[0]
                pl2 = pl[0]
                planes = [pl1,]
                nplanes = 1
            else:
                pl1 = pl[0]
                pl2 = pl[1]
                planes = range(pl1,pl2+1)
                nplanes = len(planes)

        if nfr > 2:
            raise ValueError('Input frame range invalid format: {}'.format(fr))
        else:
            if not multi_frame:
                fr1 = fr[0]
                fr2 = fr[0]
                frames = [fr1,]
                nframes = 1
            else:
                fr1 = fr[0]
                fr2 = fr[1]
                frames = range(fr1,fr2+1)
                nframes = len(frames)
        self.nframes = nframes
                
            
        # file data format parameters
        bytes_per_pixel = {
            1:1,
            2:2,
            3:4,
            4:4
        }

        bpp = bytes_per_pixel[ps.data_type]
        self.bpp = bpp
        sf = self.struct_flags[ps.data_type]

        # read data from file
        print('Reading microPET image data...')
        
        img_file = open(self.filepath,'rb')
        matsize = ps.x_dimension*ps.y_dimension*nplanes
        pl_offset = pl[0]*(ps.x_dimension*ps.y_dimension)

        # make tempfile for whole image
        img_temp_name = os.path.join(self.tempdir,'{}.dat'.format(self.filename.split('.')[0]))
        imgmat = np.memmap(img_temp_name,mode='w+',dtype='float32',shape=(nframes,matsize))
        
        for ifr in frames:  
            fr_offset = ifr*(ps.x_dimension*ps.y_dimension*ps.z_dimension)
            img_file.seek(bpp*(fr_offset+pl_offset))
            read_chunks(ifr)
        imgmat = imgmat.swapaxes(0,1)
        img_file.close()

        # scale data
        if unscaled:
            self.img_data = imgmat
            self.scaled = False
        else:
            imgmat = imgmat.reshape(nplanes,ps.x_dimension,ps.y_dimension,nframes)
            if multi_plane and (not multi_frame):
                imgmat = imgmat[0:nplanes,:,:,0]
                self.scale_factor = ps.scale_factor[fr1]
            elif (not multi_plane) and multi_frame:
                imgmat = imgmat[0,:,:,0:nframes]
                self.scale_factor = ps.scale_factor[fr1:fr2+1]
            elif (not multi_plane) and (not multi_frame):
                imgmat = imgmat[0,:,:,0]
                self.scale_factor = ps.scale_factor[fr1]
            else: 
                imgmat = imgmat[0:nplanes,:,:,0:nframes]      
                self.scale_factor = ps.scale_factor[fr1:fr2+1]
            imgmat = imgmat*self.scale_factor
            self.img_data = imgmat.reshape(nplanes,ps.y_dimension,ps.x_dimension,nframes)
            self.scaled = True

        self.rotate_on_axis('x')
        return
        
    def save_cut(self,index,path):

        def add_animal_number(hdr_lines,animal_number):
            for i,line in enumerate(hdr_lines):
                if line.strip().startswith('subject_identifier'):
                    return hdr_lines[:i+1] + [
                            '#','# animal_number (string)', '#',
                            'animal_number {}'.format(animal_number.strip())
                            ] + hdr_lines[i+1:]

        def change_line(hdr_lines,hdr_var,value):
            '''
            Update line to match value in parameters (user input)
            '''
            for j,line in enumerate(hdr_lines):
                if line.strip().startswith(hdr_var+' '):
                    hdr_lines[j] = ' '.join([hdr_var,value])
                    break
            return hdr_lines

        def write_chunks(data, dfile):
            '''
            Trying to read data in chunks to handle HiResCt images
            '''
            if self.bpp is None:
                raise ValueError('self.bpp not defined in self.save_cuts')
            bpp = self.bpp

            total_pixels = len(data)
            bytes_to_write = total_pixels*bpp
            write_lim = self.data_lim
            print('Will write {0} {1}MB chunks.'.format(bytes_to_write/write_lim,int(write_lim/10**6)))
            ix = 0
            while bytes_to_write > write_lim:
                print('Writing new chunk; {}MB left'.format(int(bytes_to_write/10**6)))
                nbytes = write_lim
                npixels = int(nbytes/bpp)
                chunk = data[ix:ix+npixels]
                dfile.write(struct.pack(npixels*sf, *chunk))
                bytes_to_write -= write_lim
                ix += npixels

            print('Writing new chunk; {}MB left'.format(int(bytes_to_write/10**6)))
            nbytes = bytes_to_write
            npixels = int(nbytes/bpp)
            chunk = data[ix:ix+npixels]
            dfile.write(struct.pack(npixels*sf, *chunk))
            return



        print('Saving files...')
        if not self.cuts:
            raise ValueError('Image has not been cut in BaseImage.save_cuts()')
        if path is None:
            raise ValueError('Path not specified')
        sf  = self.struct_flags[self.params.data_type]

        hdr_file = open(self.header_file, 'r')
        hdr_string = hdr_file.read()
        hdr_lines = hdr_string.split('\n')

        '''
        Might need to be careful of aliasing, memory, memmaps here.  will image be flipped if saving is interrupted
        by overwrite warning on a cut besides the first?
        '''

        cut_img = self.cuts[index]
            
        # did this when reading image data, flip it back now
        cut_img.rotate_on_axis('x')
        
        # update header variables
        cut_hdr_lines = hdr_lines
        vars_to_update = ['x_dimension','y_dimension','z_dimension','subject_weight']
        if self.type == 'pet':
            vars_to_update += ['dose', 'injection_time']

        for v in vars_to_update:
            cut_hdr_lines = change_line(cut_hdr_lines,v,str(getattr(cut_img.params,v)))
        
        # add animal_number to header information if it has been set
        animal_number = cut_img.params.animal_number
        if animal_number.strip():
            cut_hdr_lines = add_animal_number(cut_hdr_lines,animal_number)


        cut_filename = cut_img.out_filename
        #print('cut_filename ', cut_filename)
        cut_hdr_name = cut_filename+'.hdr'
        cut_hdr_str = '\n'.join(cut_hdr_lines)

        #print('writing header to ',os.path.join(path,cut_hdr_name))
        with open(os.path.join(path,cut_hdr_name),'w') as hf:
            hf.write(cut_hdr_str)

        out_data = cut_img.img_data
        #print('out_data.shape',out_data.shape)
        
        out_data = out_data.reshape(cut_img.xdim*cut_img.ydim*cut_img.zdim,cut_img.nframes)

        if self.scaled:
            inv = lambda x: 1/x
            v_inv = np.vectorize(inv)
            inv_scale_factor = v_inv(self.scale_factor)
            out_data = out_data*inv_scale_factor

        # prepare data to write out
        out_data = out_data.swapaxes(0,1).flatten()
        
        # make sure data is int if it is supposed to be
        if sf in ['i','B','h']:
            out_data = out_data.astype(int)
        print('writing microPET image to ',os.path.join(path,cut_filename))
        with open(os.path.join(path,cut_filename),'wb') as dfile:
            write_chunks(out_data,dfile)
        print('File saved.')

        # clean up after myself.
        cut_img.rotate_on_axis('x')
        out_data = None
        gc.collect()


    def clean_cuts(self):
        '''
        remove existing cuts
        '''
        self.colors = [x for x in self.all_colors]
        for cut in self.cuts:
            try:
                delattr(cut,'img_data')
            except AttributeError:
                pass
            fn = '{}.dat'.format(cut.filename.split('.')[0])
            
            del cut
             
            fp = os.path.join(self.tempdir,fn)
            if os.path.exists(fp):
                try_rmfile(fp)

        self.cuts = []
        gc.collect()


    def unload_image(self):
        self.clean_cuts()
        self.img_data = None
        gc.collect()
        if self.tempdir:
            shutil.rmtree(self.tempdir)
        self.tempdir = None


    def get_axis(self,axis):
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
   
    def check_collapse_method(self,method):
        if method not in ['sum','mean','max']:
            raise ValueError('Unrecognized input collapse method: {}'.format(method))


    def get_frame(self,n):
        
        self.check_data()
       
        if self.frame_range is None:
            raise ValueError('self.frame_range has not been declared in self.get_frame()')

        f1,f2 = tuple(self.frame_range)
        if n not in range(f1,f2+1):
            raise IndexError('Specified frame {0} is not in loaded range {1}'.format(n,self.frame_range))
        return self.img_data[:,:,:,f1-n]

    def collapse_frame(self,axis,frame=None,method='sum'):
        if frame is None:
            matrix = self.img_data
        else:
            matrix = self.get_frame(frame)
        ax = self.get_axis(axis)
        self.check_collapse_method(method)
        cmatrix = getattr(matrix,method)(axis=ax)
        return cmatrix

    def collapse_over_frames(self,method,matrix=None):
        if matrix is None:
            matrix = self.img_data
        self.check_collapse_method(method)
        return getattr(self.img_data,method)(axis=3)

    def rotate_on_axis(self, axis, log=False):
        self.check_data()
        axis = self.get_axis(axis)
        if log:
            self.rotation_history.append(axis)
        axes_to_flip = [0,1,2]
        axes_to_flip.remove(axis)
        self.img_data = np.flip(self.img_data,axes_to_flip[0])
        self.img_data = np.flip(self.img_data,axes_to_flip[1])

    def split_on_axis(self,matrix,axis):
        axis = self.get_axis(axis)
        mats = np.split(matrix, matrix.shape[axis], axis=axis)
        mats = [np.squeeze(m) for m in mats]
        return mats


class SubImage(BaseImage):

    def __init__(self, parent_image, img_data, filename, cut_coords, linecolor='red'):

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
        self.x_dimension,self.y_dimension,self.z_dimension = self.xdim,self.ydim,self.zdim
        self.params = copy.copy(parent_image.params)
        reset_params = ['animal_number', 'subject_weight', 'dose', 'injection_time']
        for p in reset_params:
            setattr(self.params,p,'')
        self.params.x_dimension,self.params.y_dimension,self.params.z_dimension, self.params.total_frames = self.xdim,self.ydim,self.zdim, self.nframes
        self.bounds={0 : (self.ydim, self.xdim), 
                    1 : (self.xdim, self.zdim),
                    2 : (self.zdim, self.ydim)}

        self.linecolor = linecolor



# make so can initialize with np matrix
class PETImage(BaseImage):

    def __init__(self, filepath, img_data=None):
        '''
        Needs header file and data file in same directory
        '''
        BaseImage.__init__(self, filepath=filepath, img_data=img_data)
        self.type = 'pet'

        # for header file info
        self.params = None
        self.keywords = ['axial_blocks',
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
        self.integers = ['data_type','z_dimension','total_frames','x_dimension','y_dimension']
        self.per_frame = ['scale_factor','frame_duration'] 
        self.strings = ['injection_time','animal_number','subject_weight','dose']


        self.header_file = filepath+'.hdr'

        self.load_header()  # initialize params
        self.xdim = self.params.x_dimension
        self.ydim = self.params.y_dimension
        self.zdim = self.params.z_dimension
        self.x_dimension,self.y_dimension,self.z_dimension = self.xdim,self.ydim,self.zdim

        self.frame_range = None
        self.plane_range = None
        self.nframes = None

        self.bounds={0 : (self.ydim, self.xdim), 
                    1 : (self.xdim, self.zdim),
                    2 : (self.zdim, self.ydim)}
        self.scaled = None

class CTImage(BaseImage):

    def __init__(self, filepath, img_data=None):
        BaseImage.__init__(self, filepath=filepath, img_data=img_data)
        self.type = 'ct'
        self.params = None
        self.header_file = filepath+'.hdr'

        self.keywords = [
                'data_type',
                'z_dimension',
                'x_dimension',
                'y_dimension',
                'pixel_size',
                'total_frames',
                'calibration_factor',
                'scale_factor',
                'animal_number',
                'frame_duration',
                'subject_weight']

        self.integers = ['data_type','z_dimension','total_frames','x_dimension','y_dimension']
        self.per_frame = ['scale_factor','frame_duration'] 
        self.strings = ['animal_number','subject_weight']
        self.load_header()
        self.xdim = self.params.x_dimension
        self.ydim = self.params.y_dimension
        self.zdim = self.params.z_dimension
        self.x_dimension,self.y_dimension,self.z_dimension = self.xdim,self.ydim,self.zdim

        self.frame_range = None
        self.plane_range = None
        self.nframes = None

        self.bounds={0 : (self.ydim, self.xdim), 
                    1 : (self.xdim, self.zdim),
                    2 : (self.zdim, self.ydim)}
        self.scaled = None


# functions
def try_rmfile(path):
    try:
        os.remove(path)
    except Exception as e:
        print(e)
        print('Failed to remove file: {}'.format(os.path.split(path)[1]))

"""
Rectangle manipulation
"""        
class Rect:
    def overlaps(self,other):
        a, b = self, other
        xlt = max(min(a.xlt, a.xrb), min(b.xlt, b.xrb))
        ylt = max(min(a.ylt, a.yrb), min(b.ylt, b.yrb))
        xrb = min(max(a.xlt, a.xrb), max(b.xlt, b.xrb))
        yrb = min(max(a.ylt, a.yrb), max(b.ylt, b.yrb))
        return xlt<xrb and ylt<yrb
    
    def intersection(self, other):
        a, b = self, other
        xlt = max(min(a.xlt, a.xrb), min(b.xlt, b.xrb))
        ylt = max(min(a.ylt, a.yrb), min(b.ylt, b.yrb))
        xrb = min(max(a.xlt, a.xrb), max(b.xlt, b.xrb))
        yrb = min(max(a.ylt, a.yrb), max(b.ylt, b.yrb))
        if xlt<=xrb and ylt<=yrb:
            return type(self)(xlt, ylt, xrb, yrb)   
    
    def wid(self):
        return self.xrb-self.xlt
    def ht(self):
        return self.yrb-self.ylt
    def ctr(self):
        return self.xlt+self.wid()*.5,self.ylt+self.ht()*.5
    
    def expand(self, m):
        self.xlt-=m[0]; self.xrb+=m[0];
        self.ylt-=m[1]; self.yrb+=m[1];
        
    def adjust_to_size(self,sz):
        #print ('adjust_to_size: {}'.format(sz))
        #print(self)
        sz0,x0,x1=np.array(sz),np.array([self.xlt,self.ylt]),np.array([self.xrb,self.yrb])        
        d=(sz0-(x1-x0))*.5;x0n=x0-d; x1n=x1+d
        self.xlt,self.ylt,self.xrb,self.yrb=x0n[0],x0n[1],x1n[0],x1n[1]
        #print ('adjusted:')
        #print(self)
        
    def __str__(self):
        return "Rectangle, wid={}, ht={}, ctr=({},{}), l,t,r,b=({},{},{},{})".format(
            self.wid(),self.ht(),self.ctr()[0],self.ctr()[1],self.xlt,self.ylt,self.xrb,self.yrb)
    
    @staticmethod
    def union_list(rects):
        if len(rects)<1: return None
        out=rects[0]
        for i in range(len(rects)):
            out=out.union(rects[i])
        return out
            
    def union(self, other):
        a,b=self,other
        return type(self) (verts=[min(a.xlt,b.xlt),min(a.ylt,b.ylt),max(a.xrb,b.xrb),max(a.yrb,b.yrb)])
        
    def __init__(self, bb=None, verts=None):
        if bb is not None:
            self.xlt, self.ylt, self.xrb, self.yrb = bb[1],bb[0],bb[3],bb[2]
        if verts is not None:
            self.xlt, self.ylt, self.xrb, self.yrb = verts[0],verts[1],verts[2],verts[3]        
            
    def area(self):
        return float(self.xrb-self.xlt)*(self.yrb-self.ylt)
    
    def pt_inside(self, pt):
        return pt[0]>self.xlt and pt[0]<self.xrb and pt[1]>self.ylt and pt[1]<self.yrb
    
    #for a pt inside, return its quadrant.
    def quadrant(self,pt):
        c=self.ctr()
        tl,tr=Rect(verts=[self.xlt,self.ylt,c[0],c[1]]),Rect(verts=[c[0],self.ylt,self.xrb,c[1]])
        bl,br=Rect(verts=[self.xlt,c[1],c[0],self.yrb]),Rect(verts=[c[0],c[1],self.xrb,self.yrb])
        if tl.pt_inside(pt): return 'lt'
        elif tr.pt_inside(pt): return 'rt'
        elif bl.pt_inside(pt): return 'lb'
        elif br.pt_inside(pt): return 'rb'
        else: return 'ot'    
    
    def subimage(self,img):
        xl,xr,yt,yb = int(round(max(self.xlt,0))), int(round(min(self.xrb,img.shape[0]-1))), \
            int(round(max(self.ylt,0))), int(round(min(self.yrb,img.shape[1]-1)))
        return img[yt:yb,xl:xr]
    
    def significant_intersection(self,other,ratio=0.5):
        a,b=self,other
        c=a.intersection(b)
        if c is None: 
            return False
        s1,s2,s3=a.area(),b.area(),c.area()
        if s3!=0: 
            return (min(s1,s2)/s3 >= ratio)
        else:
            return False
#end class Rect            

#splitter of mice.
class SoM:
    ipw_on=False
    
    def __init__(self,file):
        self.filename=file
        self.pi=SoM.load_image(file)            
    
    @staticmethod
    def add_cuts_to_image(im,boxes, save_analyze_dir=None):
        
        ims=[]
        for b in boxes:
            r,desc=b['rect'],b['desc']
            ix=len(im.cuts)+1
            xmax,xmin=int(round(r.xrb)),int(round(r.xlt))
            ymax,ymin=int(round(r.yrb)),int(round(r.ylt))
            #print('xmax={},xmin={},ymax={},ymin={}'.format(xmax,xmin,ymax,ymin))
            fname=im.filename[:-4]+'_'+desc
            data=im.img_data[:,ymin:ymax,xmin:xmax,:]
            d,h,w=data.shape[0],data.shape[1],data.shape[2]
            
            
            if data.shape[3]==1:
                ims+=[SoM.a2im(np.squeeze(data[:,:,int(round(w*.5)),0]),2)]
            else:
                t2=int(data.shape[3]/2)
                ims+=[SoM.a2im(np.squeeze(data[:,:,int(round(w*.5)),t2]),2)]

            #_,data=im.submemmap(ix=ix,data=im.img_data[:,ymin:ymax,xmin:xmax,:])
            #print(data.shape)

            new_img=SubImage(parent_image=im,img_data=data,filename=fname+'.img', 
                             cut_coords=[(xmin,xmax),(ymin,ymax)])
            #print('adding '+fname+'.img')
            #print('saving '+fname)
            if save_analyze_dir is not None:
                SoM.write_analyze(new_img,save_analyze_dir+'/'+fname+'_analyze.img')
            im.cuts.append(new_img)        
        if SoM.ipw_on:
            print('split images(midsagittal slice)')
            box=ipw.HBox(ims)
            display(box)
    
    @staticmethod
    def write_analyze(im,filepath):
        id1=np.swapaxes(im.img_data,0,2)
        ps=im.params.pixel_size
        hdr=nibabel.AnalyzeHeader()
        hdr.set_data_shape(id1.shape)
        hdr.set_data_dtype(id1.dtype)
        hdr.set_zooms([ps,ps,ps,im.params.frame_duration[0]])
        analyze_img=nibabel.AnalyzeImage(id1,None,hdr)
        print('writing Analyze 7.5 image: '+filepath)
        analyze_img.to_filename(filepath)
    
    @staticmethod
    def load_image(file):
        pi=PETImage(file)
        pi.load_header()
        pi.load_image()
        return pi
            
    @staticmethod
    def a2im(a,r,return_array=False):
        if not SoM.ipw_on and not return_array: return None
        f=BytesIO()
        b=0.3
        im0=(a/(np.max(a)*b))
        im0[im0>1]=1
        arr=np.uint8(im0*255)               
        if not SoM.ipw_on: return arr
        img=Image.fromarray(arr)
        img.save(f,'png')
        layout={'width':str(r*a.shape[1])+'px','height':str(r*a.shape[0])+'px'}
        return ipw.Image(value=f.getvalue(),layout=layout)
    
    @staticmethod
    def z_compress(pi): 
        n=12
        img=pi.img_data

        if len(img.shape)==3:
            imgz=np.squeeze(np.sum(img,axis=0))
        elif len(img.shape)==4:
            imgz=np.squeeze(np.sum(img,axis=(0,3)))
        im=filters.gaussian(imgz, sigma=1/(4.*n))
        return im
        
        blobs= im > self.sep_thresh * np.mean(im)
        #all_labels = measure.label(blobs)
        (blobs_labels,num) = measure.label(blobs, return_num=True,background=0)
        #plt.imshow(blobs_labels, cmap=plt.cm.gray)
        return im,blobs_labels,num            
    
    @staticmethod
    def merge_im_arrays(im0,im1,orientation='horizontal',bg=255):
        a=im0; ash=np.array(a.shape)
        b=im1; bsh=np.array(b.shape)
        msh=np.maximum(np.array(a.shape),np.array(b.shape))
        da=msh-a.shape; db=msh-b.shape
        if orientation=='horizontal':
            ap=np.pad(a,[(0,da[0]),(0,0)],constant_values=bg)
            bp=np.pad(b,[(0,db[0]),(0,0)],constant_values=bg)
            #print(ap.shape,bp.shape)
            #print(a.dtype,b.dtype)
            im=np.concatenate((ap,bp),1)
        else:
            ap=np.pad(a,[(0,da[1]),(0,0)],constant_values=bg)
            bp=np.pad(b,[(0,db[1]),(0,0)],constant_values=bg)
            #print(ap.shape,bp.shape)
            im=np.concatenate((ap,bp),0)
        return im
                     
                     
    def split_mice(self,outdir,save_analyze=False,num_anim=None,
                   sep_thresh=None,margin=None,minpix=None,output_qc=False):
        print ('Splitting '+self.pi.filename)
        SoM.num_anim=num_anim
        SoM.sep_thresh=0.9 if sep_thresh is None else sep_thresh
        SoM.margin=20 if margin is None else margin
        SoM.minpix=200 if minpix is None else minpix
        pi=self.pi        
        imz=SoM.z_compress(pi)
        blobs_labels,num=SoM.detect_animals(imz)
                
        if num_anim is not None:
            if num<num_anim:
                print('split_mice detected less regions ({}) than indicated animals({}), attempting to compensate'.
                     format(num,num_anim))
                while num < num_anim and self.sep_thresh<1:
                    self.sep_thresh += 0.01
                    blobs_labels,num=SoM.detect_animals(imz)
                if num<num_anim:
                    print('compensation failed')
                    pi.clean_cuts(); pi.unload_image(); return 1
            rects=measure.regionprops(blobs_labels)
            if num>num_anim:
                rects.sort(key=lambda p: p.area, reverse=True)
                rects=rects[:num_anim]
        else:
            rects=SoM.get_valid_regs(blobs_labels)
            if len(rects)>4:
                print('detected {}>4 regions, attempting to compensate'.format(len(rects)))
                inc=self.minpix*0.1
                while len(rects)>4:
                    self.minpix+=inc
                    rects=SoM.get_valid_regs(blobs_labels)
                    
        if SoM.ipw_on:
            b=ipw.HBox([SoM.a2im(imz,2),SoM.a2im(blobs_labels,2)])
            print('right: original image; left: detected regions')
            display(b)
        if output_qc:
            im1,im2=SoM.a2im(imz,4,True),SoM.a2im(blobs_labels,4,True)  
            qcf=outdir+'/'+pi.filename[:-4]+'_qc.png'
            print('saving '+qcf)
            print(blobs_labels.shape,imz.shape)
            label=np.uint8(255*skimage.color.label2rgb(blobs_labels,image=im1,bg_label=0,alpha=0.2))
            print(label.shape,label.dtype,np.max(label))
            Image.fromarray(label).save(qcf,'png')
            #Image.fromarray(SoM.merge_im_arrays(im1,im2)).save(qcf,'png')
        
        cuts=SoM.split_coords(imz,rects)
        save_analyze_dir=outdir if save_analyze else None
        SoM.add_cuts_to_image(pi,cuts,save_analyze_dir)
        
        for ind in range(len(pi.cuts)):
            pi.save_cut(ind,outdir+'/')
        pi.clean_cuts(); pi.unload_image()
        return 0
        
    @staticmethod
    def detect_animals(im):
        blobs= im > SoM.sep_thresh * np.mean(im)
        #all_labels = measure.label(blobs)
        (blobs_labels,num) = measure.label(blobs, return_num=True,background=0)
        return blobs_labels,num                
    
    @staticmethod    
    def get_valid_regs(label):
        min_pts=SoM.minpix
        m=[SoM.margin,SoM.margin]
        props=measure.regionprops(label)
        areas=[p.area for p in props]
        print('areas'+str(areas))
        valid_reg=[ p for p in props if p.area >= min_pts  ]        
        print('valid regions detected: '+str(len(valid_reg)))
        return valid_reg
    
    
    @staticmethod
    def harmonize_rects(rects):
        nrect=len(rects)
        if nrect==1:
            r=rects['ctr']; sz=int(round(max(r.wid(),r.ht())))
            r.adjust_to_size([sz,sz])
        elif nrect==2:
            rl,rr=rects['l'],rects['r']
            w=int(round(rr.ctr()[0]-rl.ctr()[0]))
            rl.adjust_to_size([w,w]); rr.adjust_to_size([w,w])
        elif nrect==3 or nrect==4:
            rs=[ l['rect'] for l in rects ]
            rs.sort(key=lambda r:r.xlt)
            w=rs[-1].ctr()[0]-rs[0].ctr()[0]
            rs.sort(key=lambda r:r.ylt)
            h=rs[-1].ctr()[1]-rs[0].ctr()[1]
            print('harmonize_rects, nrect={}, w: {}, h: {}'.format(nrect,w,h))
            sz=int(round(max(w,h))); s=[sz,sz]
            for r in rs: r.adjust_to_size(s)

    @staticmethod
    def split_coords(img,valid_reg):
        ims=[]
        out_boxes=[]
        m=[SoM.margin,SoM.margin]
        print('split images (axial projection):')
        if len(valid_reg)==1:
            bb=valid_reg[0].bbox
            r=Rect(bb=bb); r.expand(m); SoM.harmonize_rects({'ctr':r})
            out_boxes+=[{'desc':'ctr','rect':r}]
            #print subimage        
            ims=[SoM.a2im(r.subimage(img),4)]

        elif len(valid_reg)==2:        
            bb1,bb2=valid_reg[0].bbox,valid_reg[1].bbox
            
            if bb1[1]<bb2[1]: rl=Rect(bb=bb1); rr=Rect(bb=bb2)
            else: rl=Rect(bb=bb2); rr=Rect(bb=bb1)
            rl.expand(m); rr.expand(m); 
            SoM.harmonize_rects({'l':rl,'r':rr})
            out_boxes+=[{'desc':'l','rect':rl},{'desc':'r','rect':rr}]
            ims=[SoM.a2im(rl.subimage(img),4),SoM.a2im(rr.subimage(img),4)]
        
        elif len(valid_reg)==3 or len(valid_reg)==4:
            rs=[Rect(bb=valid_reg[i].bbox) for i in range(len(valid_reg))]
            big_box=Rect.union_list(rs)
            lr=[ {'desc':big_box.quadrant(r.ctr()),'rect':r} for r in rs ]
            SoM.harmonize_rects(lr)
            out_boxes=lr
            ims=[ SoM.a2im(r.subimage(img),4) for r in rs ]
        if SoM.ipw_on:
            box=ipw.HBox(ims)
            display(box)
        return out_boxes

class DefParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)
        
if __name__=="__main__":
    p=DefParser(description='Split a microPET image into individual animal images')
    p.add_argument('file_path',type=str,help='full path to microPET .img file')
    p.add_argument('out_dir',type=str,help='output directory')
    p.add_argument('-n',metavar='<int>', type=int,help='expected number of animals [auto-detect]')
    p.add_argument('-t',metavar='<float>', type=float,help='separation threshold between 0..1 [0.9]')
    p.add_argument('-a',action='store_true',help='save a copy in Analyze 7.5 format to output directory')
    p.add_argument('-q',action='store_true',help='output a QC .png image')
    p.add_argument('-m',metavar='<int>', type=int, help='maximum margin on axial slice in pixels [20]')
    p.add_argument('-p',metavar='<int>', type=int, help='minimum number of pixels in detectable region [200]')
    a=p.parse_args()
    print ('split_mice({},{},save_analyze={},num_anim={}, sep_thresh={},margin={},minpix={})'.
           format(a.file_path,a.out_dir,a.a,a.n,a.t,a.m,a.p))
    sys.exit(SoM(a.file_path).split_mice(a.out_dir,save_analyze=a.a,
                   num_anim=a.n,sep_thresh=a.t,margin=a.m,minpix=a.p,output_qc=a.q))
    