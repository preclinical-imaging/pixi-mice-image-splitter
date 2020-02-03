#/bin/bash

SESSION_ID=$1
SCAN_ID=$2

# allow optional params to be passed in.
CMD="python splitter_of_mice.py -q $@ /input/*.img /output"

# echo $CMD

eval "$CMD"

# copy the qc image to thumb dir.
cp /output/*png /output-qc-thumb

# mv the qc image out of the output dir and into the orig dir.
mv /output/*png /output-qc-orig

creds=${XNAT_USER}:${XNAT_PASS}

# create resource on session.
curl -v -k -u ${creds} -X PUT \
    "${XNAT_HOST}/data/experiments/${SESSION_ID}/resources/RESOURCES?format=IMG&content=RAW"

# put image files into session resource.
for f in /output/*
do
    filename=$(basename "${f}")
    curl -v -k -u ${creds} -X PUT \
        --upload-file ${f} \
        "${XNAT_HOST}/data/experiments/${SESSION_ID}/resources/RESOURCES/files/${filename}?inbody=true"

done

curl -v -k -u ${creds} -X PUT \
    "${XNAT_HOST}/data/experiments/${SESSION_ID}/scans/${SCAN_ID}/resources/SNAPSHOTS?format=PNG&content=SNAPSHOTS"

curl -v -k -u ${creds} -X PUT \
    --upload-file /output-qc-thumb/*.png \
    "${XNAT_HOST}/data/experiments/${SESSION_ID}/scans/${SCAN_ID}/resources/SNAPSHOTS/files/thumb.png?format=PNG&content=THUMBNAIL&inbody=true"

curl -v -k -u ${creds} -X PUT \
    --upload-file /output-qc-orig/*.png \
    "${XNAT_HOST}/data/experiments/${SESSION_ID}/scans/${SCAN_ID}1/resources/SNAPSHOTS/files/orig.png?format=PNG&content=ORIGINAL&inbody=true"
