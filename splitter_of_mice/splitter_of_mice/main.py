"""
Notebook: splitter_of_mice.py
Authors: Mikhail Milchenko (animal detection), Jack Muskopf (microPET image i/o), Andy Lassiter (DICOM image i/o)
Description: split microPET mice images into individual animal images (separate algorithms for PET and CT)

Copyright 2017-2023
Washington University, Mallinckrodt Insitute of Radiology. All rights reserved.
This software may not be reproduced, copied, or distributed without written permission of Washington University.
"""

import argparse
import logging
import sys

from splitter import SoM


class DefParser(argparse.ArgumentParser):
    def error(self, message):
        logging.error(message)
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


if __name__ == "__main__":
    # parse arguments
    p = DefParser(description='Split a microPET or DICOM image into individual animal images')

    p.add_argument('file_path', type=str, help='full path to microPET .img file or DICOM folder')
    p.add_argument('out_dir', type=str, help='output directory')
    p.add_argument('-n', metavar='<int>', type=int, help='(PET only) expected number of animals [auto-detect]')
    p.add_argument('-t', metavar='<float>', type=float, help='separation threshold between 0..1 [0.9 PET/0.99 CT]')
    p.add_argument('-a', action='store_true', help='save a copy in Analyze 7.5 format to output directory')
    p.add_argument('-q', action='store_true', help='output a QC .png image')
    p.add_argument('-m', metavar='<int>', type=int, help='maximum margin on axial slice in pixels [20]')
    p.add_argument('-sm', metavar='<str>', type=str,
                   help='ouput file suffix map [ctr:ctr,l:l,r:r,lt:lt,rt:rt,rb:rb,lb:lb]')
    p.add_argument('--mod', metavar='<str>', type=str, help='force input image modality (ct|pet) [autodetect]')
    p.add_argument('-p', metavar='<int>', type=int,
                   help='minimum number of pixels in detectable region [200 PET/3300 CT]')
    p.add_argument('--dicom', action='store_true', help='input file/folder is DICOM')
    p.add_argument('--log-level', metavar='<str>', type=str, help='log level [INFO | DEBUG]', default='INFO')
    p.add_argument('-z', action='store_true', help='Zip each split image')
    p.add_argument('--remove-bed', action='store_true',
                   help='Attempt to remove the bed from CT images to improve animal detection')
    p.add_argument('--pet-img-size', metavar='<int>', type=int, nargs=2,
                   help='Desired size of the split PET images as a (height, width) tuple. Helpful for keeping the same '
                        'image size across multiple scans.')
    p.add_argument('--ct-img-size', metavar='<int>', type=int, nargs=2,
                   help='Desired size of split CT images as a (height, width) tuple. Helpful for keeping the same '
                        'image size across multiple scans.')

    a = p.parse_args()

    # setup logging
    logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout)],
                        level=logging.getLevelName(a.log_level),
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    logging.debug(
        'modality: {}, split_mice({},{},save_analyze={},num_anim={}, sep_thresh={},margin={},minpix={},out_qc={})'.
          format(a.mod, a.file_path, a.out_dir, a.a, a.n, a.t, a.m, a.p, a.q)
    )

    sys.exit(SoM(a.file_path, modality=a.mod, dicom=a.dicom).split_mice(a.out_dir, save_analyze=a.a,
                                                                        num_anim=a.n, sep_thresh=a.t, margin=a.m,
                                                                        minpix=a.p, output_qc=a.q, suffix_map=a.sm,
                                                                        zip=a.z, remove_bed=a.remove_bed,
                                                                        pet_img_size=a.pet_img_size,
                                                                        ct_img_size=a.ct_img_size))
