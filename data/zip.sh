#!/bin/bash

ROOT="/Users/drm/Box/CCDB_KooreshShoghi/Pre-Clinical_Data_Samples/Seimens Inveon Scanner"

zip -r 1bed.zip  \
    1bed.csv \
    "${ROOT}/1 Bed/Static/CT" \
    "${ROOT}/1 Bed/Static/PET"
