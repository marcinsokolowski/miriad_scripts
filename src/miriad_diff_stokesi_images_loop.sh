#!/bin/bash

export PATH=~/Software/eda2tv/:$PATH

function plot_rms
{
   www_dir=$1
   do_scp=$2

   mkdir -p images/

   cnt=`ls rms_vs_time_center* |wc -l`
   if [[ $cnt -gt 0 ]]; then   
      echo "python ~/aavs-calibration/monitoring/plot_rms_vs_time.py rms_vs_time_center --y_axis_title=\"RMS_center [Jy]\""
      python ~/aavs-calibration/monitoring/plot_rms_vs_time.py rms_vs_time_center --y_axis_title="RMS_center [Jy]" 
   
      echo "python ~/aavs-calibration/monitoring/plot_rms_vs_time.py rms_vs_time_center --y_axis_title=\"RMS_center [Jy]\" --y_min=0 --y_max=100.00 --outfile=rms_vs_time_center_zoom"
      python ~/aavs-calibration/monitoring/plot_rms_vs_time.py rms_vs_time_center --y_axis_title="RMS_center [Jy]" --y_min=0 --y_max=100.00 --outfile=rms_vs_time_center_zoom      
   else
      echo "WARNING : no files to be plotted found -> skipped"
      do_scp=0
   fi

   cnt=`ls rms_vs_time_full_image* |wc -l`
   if [[ $cnt -gt 0 ]]; then
      echo "python ~/aavs-calibration/monitoring/plot_rms_vs_time.py rms_vs_time_full_image --y_axis_title=\"RMS_Stokes [Jy]\""
      python ~/aavs-calibration/monitoring/plot_rms_vs_time.py rms_vs_time_full_image --y_axis_title="RMS_Stokes [Jy]" 
   
      echo "python ~/aavs-calibration/monitoring/plot_rms_vs_time.py rms_vs_time_full_image --y_axis_title=\"RMS_Stokes [Jy]\" --y_min=0 --y_max=100.00 --outfile=rms_vs_time_full_image_zoom"
      python ~/aavs-calibration/monitoring/plot_rms_vs_time.py rms_vs_time_full_image --y_axis_title="RMS_Stokes [Jy]" --y_min=0 --y_max=100.00 --outfile=rms_vs_time_full_image_zoom
      
      do_scp=1
   else
      echo "WARNING : no files to be plotted found -> skipped"
   fi
            
   if [[ $do_scp -gt 0 ]]; then            
      if [[ -n ${www_dir} && ${www_dir} != "-" ]]; then
         echo "INFO : Copying image to ${www_dir}/"

         echo "rsync -avP images/rms*.png ${www_dir}/"
         rsync -avP images/rms*.png ${www_dir}/
      fi      
   else
      echo "WARNING : no files coped to ${www_dir}"
   fi
}

station_name=eda2
if [[ -n "$1" && "$1" != "-" ]]; then
   station_name=$1
fi
station_name_lower=`echo $station_name | awk '{print tolower($1);}'`

www_dir=aavs1-server:/exports/eda/${station_name_lower}/sensitivity/
if [[ -n "$2" && "$2" != "-" ]]; then
    www_dir=$2
fi

do_scp=1
if [[ -n "$3" && "$3" != "-" ]]; then
   do_scp=$3
fi

freq_ch=204
if [[ -n "$4" && "$4" != "-" ]]; then
   freq_ch=$4
fi

restart=0
if [[ -n "$5" && "$5" != "-" ]]; then
   restart=$5
fi

echo "Started at:"
date

iter=0

if [[ $restart -gt 0 ]]; then
   echo "DEGUG : restart from scratch is REQUIRED - removing stamp files"
   echo "rm -f fits_list_i_diff_processing_PREV"
   rm -f fits_list_i_diff_processing_PREV
else
   echo "DEBUG : restart from scratch is NOT REQUIRED"
fi
touch fits_list_i_diff_processing_PREV

start_ux=-1
nothing_new_counter=0
rm -f endFile.txt

while [ 1 ];
do
   echo
   echo "---------------------------- Iteration $iter ----------------------------"
   date
#   ls *_I.fits > fits_list_i_diff_processing
   echo "find . -maxdepth 1 -name \"*_I.fits\"  | awk '{gsub("./","");print \$0;}' | sort > fits_list_i_diff_processing"
   find . -maxdepth 1 -name "*_I.fits"  | awk '{gsub("./","");print $0;}' | sort > fits_list_i_diff_processing

   # identify new files to process :
   touch fits_list_i_diff_processing_PREV
   diff --normal fits_list_i_diff_processing_PREV fits_list_i_diff_processing | awk '{if(NF>=2){print $2;}}' > new_fits_i_diff_to_process
   new_count=`cat new_fits_i_diff_to_process | wc -l`

   if [[ $new_count -gt 0 ]]; then
      start_ux=`date +%s`
      echo "INFO : $new_count new diff files identified -> processing them ..."
      
      # start processing :   
      # it is ensured inside miriad_diff_images.sh that the same files are not re-processed :
      echo "time miriad_diff_images.sh fits_list_i_diff_processing I 1 $freq_ch $station_name"
      time miriad_diff_images.sh fits_list_i_diff_processing I 1 $freq_ch $station_name

      # do plots and copy to server :
      plot_rms $www_dir
   
      echo "mv fits_list_i_diff_processing fits_list_i_diff_processing_PREV"
      mv fits_list_i_diff_processing fits_list_i_diff_processing_PREV
   else
      echo "INFO : no new files collected -> nothing to be processed"      
      nothing_new_counter=$(($nothing_new_counter+1))
      
      # if nothing new more than 20 times and already N=2 hours since the start -> probably finished 
      ux=`date +%s`
      diff_seconds=$(($ux-$start_ux))
      if [[ $nothing_new_counter -gt 20 && $diff_seconds -gt 7200 ]]; then
         echo "WARNING : nothing new $nothing_new_counter and already $diff_seconds passed (vs. 7200 seconds) since start ($ux vs. $start_ux) -> setting end file"
         echo $ux > endFile.txt
      else
         echo "PROGRESS : still new data processed or $diff_seconds  ($ux vs. $start_ux) less than 7200 seconds limit -> setting end file -> continue processing"
      fi
   fi
   
   echo "sleep 300"
   sleep 300
   
   iter=$(($iter+1))
done
