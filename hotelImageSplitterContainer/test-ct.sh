#!/bin/bash

in_dir="/Users/drm/projects/nrg/ccdb/ccdb/hotelImageSplitterContainer/data"
out_dir=/tmp/split

mkdir ${out_dir}
docker run \
    --name split \
    -v "${in_dir}":/input:ro \
    -v ${out_dir}:output \
    hotel_splitter:v1 \
    python splitter_of_mice.py /input/mpet3631a_ct1_v1.ct.img /output

