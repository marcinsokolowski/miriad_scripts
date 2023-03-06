#!/bin/bash

coinc_file=coinc_eda2_aavs2.txt


sat_dir=SAT_halfsecond
if [[ -n "$1" && "$1" != "-" ]]; then
   sat_dir=$1
fi

out_file=tle_radec.txt
if [[ -n "$2" && "$2" != "-" ]]; then
   out_file=$2
fi


rm -f ${out_file}

for uxtime in `cat ${coinc_file} | awk '{if($1!="#"){printf("%d\n",$13);}}'`
do
   if [[ -s ${sat_dir}/${uxtime}.0000.txt ]]; then
       echo "cat ${sat_dir}/${uxtime}.0000.txt >> tle_radec.txt"
       cat ${sat_dir}/${uxtime}.0000.txt | awk '{if($1!="#" && $5>0 ){print $2" "$3;}}'  >> ${out_file}
   fi
done
