#!/bin/bash

HOST=https://ccdb-dev-maffitt1.nrg.wustl.edu
PROJ=DRM-test
INFO=./.info
creds=`head -1 $INFO`

JSESSION=`curl -k -u ${creds} "${HOST}/REST/JSESSION"`
echo "JSESSION=${JSESSION}"

curl -v -k -b JSESSIONID=$JSESSION -X POST\
    --header 'Content-Type: application/zip' \
    --header 'Accept: text/html' \
    --data-binary '@bed1.zip' \
    "https://ccdb-dev-maffitt1.nrg.wustl.edu/xapi/ccdb/projects/${PROJ}/hotelSessions"
   
#curl -v -k -b JSESSIONID=$JSESSION \
#    --trace trace.txt \
#    -F 'file=@small.zip' \
#    "https://ccdb-dev-maffitt1.nrg.wustl.edu/xapi/ccdb/projects/${PROJ}/hotelSessions"
   

