#!/bin/bash

file=coinc_eda2_aavs2_TRANSIENT_CANDIDATEs.txt
if [[ -n "$1" && "$1" != "-" ]]; then
   file=$1
fi

name=2020_04_11_ch294_corr
if [[ -n "$2" && "$2" != "-" ]]; then
   name=$2
fi

local_dir="../"
if [[ -n "$3" && "$3" != "-" ]]; then
   local_dir=$3
fi

station=aavs2
if [[ -n "$4" && "$4" != "-" ]]; then
   station=$4
fi


for fits in `cat ${file} | awk '{if($1!="#"){print $6;}}' | sort -u`
do
   if [[ -s ${local_dir}/${fits} ]]; then
      echo "INFO : already copied ${local_dir}/${fits}"
   else
      echo "rsync -avP ${station}:/data/${name}/merged/$fits ${local_dir}"
      rsync -avP ${station}:/data/${name}/merged/$fits ${local_dir}
   fi
done

