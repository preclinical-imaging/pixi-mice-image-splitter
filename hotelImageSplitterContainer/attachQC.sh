#!/bin/bash

HOST=https://ccdb-dev-maffitt1.nrg.wustl.edu
PROJ=DRM-test2
INFO=.info
creds=`head -1 $INFO`

JSESSION=`curl -s -k -u ${creds} "${HOST}/REST/JSESSION"`
echo "JSESSION=${JSESSION}"

# curl -v -k -b JSESSIONID=$JSESSION -X PUT \
#     "${HOST}/data/experiments/CCDB03_E00224/scans/1/resources/SNAPSHOTS?format=PNG&content=SNAPSHOTS"
   
curl -v -k -b JSESSIONID=$JSESSION -X PUT \
    --upload-file /tmp/split/mpet2785a_em1_v1.pet_split_qc.png \
    "${HOST}/data/experiments/CCDB03_E00224/scans/1/resources/SNAPSHOTS/files/foo.png?format=PNG&content=THUMBNAIL&inbody=true"
   
curl -v -k -b JSESSIONID=$JSESSION -X PUT \
    --upload-file /tmp/split/mpet2785a_em1_v1.pet_split_qc.png \
    "${HOST}/data/experiments/CCDB03_E00224/scans/1/resources/SNAPSHOTS/files/foo2.png?format=PNG&content=ORIGINAL&inbody=true"
   
