#!/bin/bash
sm=/home/wustl/mmilchenko/src/ccdb/splitter_of_mice/splitter_of_mice.py


dir1=/home/wustl/mmilchenko/src/ccdb/Pre-Clinical_Data_Samples/Concorde_Microsystems_F220_Scanner/
dir2=/home/wustl/mmilchenko/src/ccdb/Pre-Clinical_Data_Samples/Siemens_Inveon_Scanner/

impet=( $dir1'1_Bed/Static/mpet3681a_em1_v1.img' \
        $dir1'4_Bed/Static/mpet3719b_em1_v1.img' \
        $dir1'2_Bed/Static/mpet3723b_em1_v1.img' \
        $dir2'1_Bed/Static/PET/mpet3631a_em1_v1.pet.img' \
        $dir2'1_Rat/Static/PET/mpet3617a_em1_v1.pet.img' \
        $dir2'2_Bed/Static/PET/mpet3742a_em1_v1.pet.img' \
        $dir2'4_Bed/Static/PET/mpet3745a_em1_v1.pet.img' \
	$dir1'1_Rat/Dynamic/mpet3659b_em1_v1.img' \
        $dir1'2_Bed/Dynamic/mpet3688a_em1_v1.img' \
        $dir1'4_Bed/Dynamic/mpet3691b_em1_v1.img' \
        $dir2'1_Bed/Dynamic/PET/mpet3715b_em1_v1.pet.img' \
        $dir2'1_Rat/Dynamic/PET/mpet3739a_em1_v1.pet.img' \
        $dir2'2_Bed/Dynamic/PET/mpet3741a_em1_v1.pet.img' \
        $dir2'4_Bed/Dynamic/PET/mpet3721a_em1_v1.pet.img' \
)


for im in ${impet[*]}; do
	echo python $sm $im . -a -q
	python $sm $im . -a -q
done
