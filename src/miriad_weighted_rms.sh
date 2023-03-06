#!/bin/bash

radius=111
if [[ -n "$1" && "$1" != "-" ]]; then
   radius=$1
fi

list_file=fits_list_rmsiqr_I

for fits in `cat $list_file`
do
#   utc=`echo $fits | awk '{file=$1;gsub("T","_");print file;}'`
   utc=`echo $fits | awk '{gsub("T","_",$1);file=$1;print substr(file,10,15);}'`
   ux=`date2date -ut2ux=$utc | awk '{print $3;}'`
      
   line=`calcfits_bg $fits s a b -R ${radius} | grep RMS_IQR`
   mean_rmsiqr=`echo $line | awk '{print $12;}'`
   rms_rmsiqr=`echo $line | awk '{print $8;}'`
      
      
   echo "$ux $mean_rmsiqr $rms_rmsiqr $utc"
done