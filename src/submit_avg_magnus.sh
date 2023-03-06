#!/bin/bash

file_template="timestamps_?????.txt"
if [[ -n "$1" && "$1" != "-" ]]; then
   file_template=$1
fi

count_expected=`cat ${file_template} | wc -l`

wait=1
while [[ $wait -gt 0 ]]; 
do
   echo
   date
   n_running_jobs=`squeue  -o "%.10i %.9P %.20j %.8u %.7a %.2t %.9e %.9L %.6D %.8Q %R" -u $USER -M magnus | wc -l`
   
   cnt=0
   for timestamp in `cat $file_template`
   do
      if [[ -d $timestamp ]]; then
         cnt=$(($cnt+1))
      fi
   done
   
   if [[ $cnt == $count_expected ]]; then
      echo "sbatch -p workq -M magnus $SMART_DIR/bin/pawsey/pawsey_avg_images.sh"
      sbatch -p workq -M magnus $SMART_DIR/bin/pawsey/pawsey_avg_images.sh
      exit;
   else
      echo "Number of processed timestamps = $cnt vs. expected = $count_expected -> sleep 600"
      sleep 600
   fi
   
#   if [[ $n_running_jobs -gt 2 ]]; then
#      echo "Number of running jobs = $n_running_jobs -> sleep 600"
#      sleep 600
#   else   
#      echo "Number of running jobs = $n_running_jobs -> submtting avraging job now"
#   
#      echo "sbatch -p workq -M magnus $SMART_DIR/bin/pawsey/pawsey_avg_images.sh"
#      sbatch -p workq -M magnus $SMART_DIR/bin/pawsey/pawsey_avg_images.sh
#
##      echo "sbatch -p workq -M magnus $SMART_DIR/bin/pawsey/pawsey_avg_images_pbcorr.sh"
##      sbatch -p workq -M magnus $SMART_DIR/bin/pawsey/pawsey_avg_images_pbcorr.sh
#      
#      wait=0
#   fi   
done
   
echo "Scripts pawsey_avg_images_pbcorr.sh and pawsey_avg_images.sh submitted at -> exiting waiting script now"
date
