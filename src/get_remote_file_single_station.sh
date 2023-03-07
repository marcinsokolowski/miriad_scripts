#!/bin/bash

file=chan_204_20200626T131542_I_diff.fits
if [[ -n "$1" && "$1" != "-" ]]; then
   file=$1
fi
file_base=${file%%.fits}

dt_name=2020_04_10_ch204_corr # 2020_07_07_ch204_corr
if [[ -n "$2" && "$2" != "-" ]]; then
   dt_name=$2
fi

station="eda2"
if [[ -n "$3" && "$3" != "-" ]]; then
   station=$3
fi

local_data_dir="/media/msok/0754e982-0adb-4e33-80cc-f81dda1580c8/analysis/20200410_eda2-ch204_aavs2-ch204/"
if [[ -n "$4" && "$4" != "-" ]]; then
   local_data_dir=$4
fi

echo "get_remote_file.sh :"
echo "PARAMETERS:"
echo "dt_name = $dt_name"
echo "station = $station"

remote_dir=${data_dir}/eda2/${dt_name}/merged

#if [[ $station == "eda2" || $station == "all" ]]; then
echo "rsync -avP ${station}:/data/${dt_name}/merged/${file_base}*{.fits,.reg} ${local_data_dir}/"
rsync -avP ${station}:/data/${dt_name}/merged/${file_base}*{.fits,.reg} ${local_data_dir}/      
sleep 3
# fi


echo "Done at:"
date
