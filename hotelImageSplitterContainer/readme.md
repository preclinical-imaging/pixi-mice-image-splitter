Description: Code to create Docker image to run 'splitter_of_mice.py'.<br>
Authors: David Maffitt

Copyright 2019<br>
Washington University, Mallinckrodt Insitute of Radiology. All rights reserved. <br>
This software may not be reproduced, copied, or distributed without written permission of Washington University. <br>
For more information contact David Maffitt<br>

ENVIRONMENT REQUREMENTS<br>
Docker

BUILD<br>
1. Run 'source build-base2.sh' to generate Docker the image containing the required Python environment. The image tag is currently hardcoded as 'python-base:v1'.
1. The version of 'splitter_of_mice.py' installed in the container is in the 'context-splitter' directory. Note the version in this repo is not the same as in the 'splitter_of_mice' directory.  This version has been modified to remove dependencies only needed if running in the Jupyter context and, for some reason, comments in Russian.
1. Run 'source build-splitter2.sh'. This will build the Docker image 'hotel_splitter:v2' from the python-base image created in step 1. 

CONFIGURE<br>
1. Install the hotel-splitter:v2 image. The preferred way to do this is to upload the image to a Docker hub from which it will be discovered by XNAT. An alternative is the series of manual steps outlined in deploy-image.sh.
1. Administer -> Plugin Settings -> Images and Commands: "Show Hidden Images" will reveal hotel_splitter:v2.
1. Click "Add New Command", replace the contents of the pop-up with the contents of command.json, then click "Save".
1. Browse to the Project page.
1. Select "Project Settings" from Action Menu.
1. Under "Configure Commands", enable command named "Run hotel splitter on a session qc".
1. Now, when you browse to a session in the project, you will see "Run containers" in the Action Menu.
1. Select "hotelimagesplitterqc" to run the container.

