#!/bin/bash

in_dir="/Users/drm/projects/nrg/ccdb/ccdb/hotelImageSplitterContainer/data2/mpet2785a/pt"
out_dir=/tmp/split

mkdir ${out_dir}
docker run \
    --name split \
    -v "${in_dir}":/input:ro \
    -v "${out_dir}":/output \
    hotel_splitter:v1 \
    python /splitter_of_mice.py /input/mpet2785a_em1_v1.pet.img /output

