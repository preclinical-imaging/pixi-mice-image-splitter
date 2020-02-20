#!/bin/bash

xsiType=$1
options_flag=$2

if [[ $xsiType = "ccdb:hotelCT" ]]
then
    modality_flag="--mod ct"
elif [[ $xsiType = "ccdb:hotelPET" ]]
then
    modality_flag="--mod pet"
else
    modality_flag=""
fi

# allow optional params to be passed in.
CMD="python splitter_of_mice.py ${options_flag} -q $modality_flag  /input/*.img /output"

echo $CMD

eval "$CMD"

# copy the qc image to qc dir.
mv /output/*png /output-qc

