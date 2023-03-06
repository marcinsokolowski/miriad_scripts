#!/bin/bash

list=fits_list_I
if [[ -n "$1" && "$1" != "-" ]]; then
   list=$1
fi

path=`which fixCoordHdr.py`

for fits in `cat $list`
do
   echo "python $path $fits"
   python $path $fits
done
