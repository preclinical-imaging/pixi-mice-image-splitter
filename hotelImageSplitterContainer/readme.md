Description: Code to create Docker image to run 'splitter_of_mice.py'.<br>
Authors: David Maffitt

Copyright 2019<br>
Washington University, Mallinckrodt Insitute of Radiology. All rights reserved. <br>
This software may not be reproduced, copied, or distributed without written permission of Washington University. <br>
For more information contact David Maffitt<br>

ENVIRONMENT REQUREMENTS<br>
Docker

BUILD INSTRUCTIONS<br>
1. Run 'source build-base.sh' to generate Docker image containing the required Python environment. The image tag is currently hardcoded as 'python-base:v1'.
2. The version of 'splitter_of_mice.py' installed in the container is in the 'context-splitter' directory. Note the version in this repo is not the same as in the 'splitter_of_mice' directory.  This version has been modified to remove dependencies only needed if running in the Jupyter context.
3. Run 'source build-splitter.sh'. This will build the Docker image 'hotel_splitter:v1' from the python-base image created in step 1. 

