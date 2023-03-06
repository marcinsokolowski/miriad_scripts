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


echo "Started at:"
date

iter=0

while [ 1 ];
do
   echo
   echo "---------------------------- Iteration $iter ----------------------------"
   date
   
   find . -name "*_XX.fits" -maxdepth 1 | awk '{gsub("./","");print $0;}' | sort > fits_list_xx
   find . -name "*_YY.fits" -maxdepth 1 | awk '{gsub("./","");print $0;}' | sort > fits_list_yy
#   ls *_XX.fits > fits_list_xx
#   ls *_YY.fits > fits_list_yy
   
   echo "miriad_diff_images.sh fits_list_xx XX 1"
   miriad_diff_images.sh fits_list_xx XX 1

   echo "miriad_diff_images.sh fits_list_yy YY 1 "
   miriad_diff_images.sh fits_list_yy YY 1   

   # do plots and copy to server :
   plot_rms $www_dir
   
   echo "sleep 300"
   sleep 300
   
   iter=$(($iter+1))
done
