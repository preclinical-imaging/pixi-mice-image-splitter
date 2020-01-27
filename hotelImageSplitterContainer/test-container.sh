#!/bin/bash

in_dir="/Users/drm/projects/nrg/ccdb/ccdb/hotelImageSplitterContainer/data2/mpet2785/a/pt"
out_dir=/tmp/split

mkdir ${out_dir}
docker run \
    --name split \
    -v "${in_dir}":/input:ro \
    -v "${out_dir}":/output \
    hotel_splitter:v2 \
    sleep 10000
