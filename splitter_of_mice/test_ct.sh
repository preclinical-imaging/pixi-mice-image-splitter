#!/bin/bash
sm=/home/wustl/mmilchenko/src/ccdb/splitter_of_mice/splitter_of_mice.py
dir=/home/wustl/mmilchenko/src/ccdb/Pre-Clinical_Data_Samples/Siemens_Inveon_Scanner/
imCT=(1_Bed/Static/CT/mpet3631a_ct1_v1.ct.img 1_Rat/Static/CT/mpet3617a_ct1_v1.ct.img 2_Bed/Static/CT/mpet3742a_ct1_v1.ct.img 4_Bed/Static/CT/mpet3745a_ct1_v1.ct.img 1_Bed/Dynamic/CT/mpet3715b_ct1_v1.ct.img 1_Rat/Dynamic/CT/mpet3739a_ct1_v1.ct.img 2_Bed/Dynamic/CT/mpet3741a_ct1_v1.ct.img 4_Bed/Dynamic/CT/mpet3721a_ct1_v1.ct.img)
for im in ${imCT[*]}; do
	echo python $sm ${dir}$im . -a -q
	python $sm ${dir}$im . -a -q
done
