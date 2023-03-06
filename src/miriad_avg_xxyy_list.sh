#!/bin/bash

force=0
if [[ -n "$1" && "$1" != "-" ]]; then
   force=$1
fi


for fits_xx in `find . -name "*_XX.fits" -maxdepth 1 | awk '{gsub("./","");print $0;}' | sort`
do
   echo "miriad_avg_xxyy.sh ${fits_xx} - - - ${force}"
   miriad_avg_xxyy.sh ${fits_xx} - - - ${force}
done

find . -name "chan*_I.fits" -maxdepth 1 | awk '{gsub("./","");print $0;}' | sort  > fits_list_I

