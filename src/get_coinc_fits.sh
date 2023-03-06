#!/bin/bash

dataset_name=2020_04_10_ch204_corr
if [[ -n "$1" && "$1" != "-" ]]; then
   dataset_name="$1"
fi

eda2_dir=/media/msok/0754e982-0adb-4e33-80cc-f81dda1580c8/eda2/data/${dataset_name}/merged
eda2_dt=${dataset_name}

aavs2_dir=/media/msok/0754e982-0adb-4e33-80cc-f81dda1580c8/aavs2/data/${dataset_name}/merged
aavs2_dt=${dataset_name}

coinc_log=coinc_eda2_aavs2.txt

while read line # example
do
   first=`echo $line | awk '{print $1}'`
   
   if [[ $first != "#" ]]; then
      fits2=`echo $line | awk '{print $3}'`
      fits1=`echo $line | awk '{print $11}'`
      
      fits2normal=${fits2%%_diff.fits}.fits
      fits1normal=${fits1%%_diff.fits}.fits

      echo "rsync -avP eda2:/data/${eda2_dt}/merged/${fits1} ${eda2_dir}/"
      rsync -avP eda2:/data/${eda2_dt}/merged/${fits1} ${eda2_dir}/      
      sleep 3

      echo "rsync -avP eda2:/data/${eda2_dt}/merged/${fits1normal} ${eda2_dir}/"
      rsync -avP eda2:/data/${eda2_dt}/merged/${fits1normal} ${eda2_dir}/
      sleep 3
   
#      echo "rsync -avP eda2:/data/${eda2_dt}/merged/${fits2} ${eda2_dir}/"
#      rsync -avP eda2:/data/${eda2_dt}/merged/${fits2} ${eda2_dir}/
   
#      echo "rsync -avP aavs2:/data/${aavs2_dt}/merged/${fits1} ${aavs2_dir}/"
#      rsync -avP aavs2:/data/${aavs2_dt}/merged/${fits1} ${aavs2_dir}/
#      sleep 3
   
      echo "rsync -avP aavs2:/data/${aavs2_dt}/merged/${fits2} ${aavs2_dir}/"
      rsync -avP aavs2:/data/${aavs2_dt}/merged/${fits2} ${aavs2_dir}/
      sleep 3

      echo "rsync -avP aavs2:/data/${aavs2_dt}/merged/${fits2normal} ${aavs2_dir}/"
      rsync -avP aavs2:/data/${aavs2_dt}/merged/${fits2normal} ${aavs2_dir}/
      
      if [[ ! -s ${eda2_dir}/${fits1} || ! -s ${eda2_dir}/${fits1normal} || ! -s ${aavs2_dir}/${fits2} || ! -s ${aavs2_dir}/${fits2normal} ]]; then
         echo "ERROR : could not copy one of the files : ${eda2_dir}/${fits1} , ${eda2_dir}/${fits1normal}, ${aavs2_dir}/${fits2}, ${aavs2_dir}/${fits2normal} -> exiting now !"
         exit;
      fi
  fi
      
done < $coinc_log

