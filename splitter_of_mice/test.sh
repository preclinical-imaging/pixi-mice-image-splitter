#!/bin/bash

if [ -z "$1" ]; then 
	echo "usage: test.sh <image list file.lst>
	exit -1
fi

input=$1

while IFS= read -r line
do
  echo "$line"
  python splitter_of_mice.py -a $line ~/temp
done < "$input"
