LICENSE<br>
Program: splitter_of_mice.py
Authors: Mikhail Milchenko (animal detection), Jack Muskopf (microPET image i/o)
Description: split microPET mice images into individual animal images

Copyright 2017-2019
Washington University, Mallinckrodt Insitute of Radiology. All rights reserved. 
This software may not be reproduced, copied, or distributed without written permission of Washington University. 
For more information contact Mikhail Milchenko, PhD

ENVIRONMENT REQUREMENTS<br>
Python 3.6.5 with ipywidgets, numpy, pillow, nibabel, and skimage packages

DESCRIPTION<br>
Mouse image splitting technique. Implemented in Python, reusing the ‘ccdb’ code to read/write images. 
The algorithm only requires microPET image (img/img.hdr pair) as input. The output is the same format. It detects the number of mice and outputs split images with suffix appended to the original filename according to the following conventions:
1 mouse: _ctr: single image 
2 mice: _l, _r: left and right mice.
3-4 mice: _lt, _lb, _rt, _rb: left top, left bottom, right top, right bottom mouse, as they are seen in the GUI viewer.

USAGE<br>
splitter_of_mice.py [options] file_path out_dir

positional arguments:
  file_path   full path to microPET .img file
  out_dir     output directory

optional arguments:
  -h, --help  show this help message and exit
  -n <int>    expected number of animals [auto-detect]
  -t <float>  separation threshold between 0..1 [0.9]
  -a          save a copy in Analyze 7.5 format to output directory
  -m <int>    maximum margin on axial slice in pixels [20]
  -p <int>    minimum number of pixels in detectable region [200]
  
NOTE specify the number of animals for additional verification of detected regions. 
