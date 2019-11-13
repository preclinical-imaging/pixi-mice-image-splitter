#!/bin/bash

if [ -z "$2" ]; then 
	echo "usage: test.sh <image list file.lst> <out dir>"
	exit -1
fi

input=$1
out=$2

while IFS= read -r line
do
  echo "$line"
  python splitter_of_mice.py -q -a $line $out
done < "$input"
