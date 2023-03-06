#!/bin/bash

obsid=1194350120
if [[ -n "$1" && "$1" != "-" ]]; then
   obsid=$1
else
   echo "ERROR : OBSID must be provided in 1st parameter !!!"
   exit;
fi

calid=1194345816
if [[ -n "$2" && "$2" != "-" ]]; then
   calid=$2
else
   echo "ERROR : CALIBRATION OBSID must be provided in 2nd parameter !!!"
   exit;
fi

object="00h36m08.95s -10d34m00.3s"
# test : J2330 object="23h30m26.9s -20d05m29.63s"
if [[ -n "$3" && "$3" != "-" ]]; then
   object="$3"
else
   echo "ERROR : OBJECT must be provided in 3rd parameter !!!"
   exit;
fi

sleep_time=2
if [[ -n "$4" && "$4" != "-" ]]; then
   sleep_time=$4
fi

file_template="timestamps_?????.txt"
if [[ -n "$5" && "$5" != "-" ]]; then
   file_template=$5
fi

imagesize=2048
if [[ -n "$6" && "$6" != "-" ]]; then
   imagesize=$6
fi


if [[ -d data || -L data ]]; then
   echo "INFO : data subdirectory / link already exists -> nothing to be done"
else
   echo "WARNING : data subdirectory does not exist -> creating a link for user = $USER :"
   if [[ $USER == "msok" ]]; then
      if [[ $cluster != "mwa" && $cluster != "garrawarla" ]]; then # mwa = garrawarla
         echo "ln -s /group/mwasci/msok/test/202002/1194350120/J2330/data"
         ln -s /group/mwasci/msok/test/202002/1194350120/J2330/data
      else
         echo "ln -s /astro/mwaops/msok/mwa/smart/data"
         ln -s /astro/mwaops/msok/mwa/smart/data 
      fi
   else
      echo "$USER : ln -s ~/github/mwa_pb/data"
      ln -s ~/github/mwa_pb/data
   fi
fi

mkdir -p TIMESTAMPS_BACKUP/
echo "cp  ${file_template} TIMESTAMPS_BACKUP/"
cp  ${file_template} TIMESTAMPS_BACKUP/

last_file=`ls ${file_template} | tail -1`

for timestep_file in `ls ${file_template}`
do
   # last 1 is to create subdirectories for each timestamp
#   echo "sbatch -p workq -M magnus $SMART_DIR/bin/pawsey/pawsey_smart_cotter_timestep.sh - - - - - \"00h34m21.83s -05d34m36.72s\" - - $timestep_file 1"
#   sbatch -p workq -M magnus $SMART_DIR/bin/pawsey/pawsey_smart_cotter_timestep.sh - - - - - "00h34m21.83s -05d34m36.72s" - - $timestep_file 1

   is_last=0
   if [[ $timestep_file == $last_file ]]; then
      echo "Last file $timestep_file == $last_file -> is_last := 1"
      is_last=1
   fi
   
   # /astro/mwaops/vcs/ -> /astro/mwavcs/vcs/1275085816/vis/
   echo "sbatch -p workq -M $sbatch_cluster $SMART_DIR/bin/pawsey/pawsey_smart_cotter_timestep_magnus.sh - - /astro/mwavcs/vcs/${obsid}/vis ${obsid} ${calid} \"${object}\" - $imagesize $timestep_file 1 $is_last"
   sbatch -p workq -M $sbatch_cluster $SMART_DIR/bin/pawsey/pawsey_smart_cotter_timestep_magnus.sh - - /astro/mwavcs/vcs/${obsid}/vis ${obsid} ${calid} "${object}" - $imagesize $timestep_file 1 $is_last


#   echo "mv ${timestep_file} ${timestep_file}.SUBMITTED"
#   mv ${timestep_file} ${timestep_file}.SUBMITTED
   
   echo "sleep $sleep_time"
   sleep $sleep_time
done

# 
# NOT ANYMORE !!! Replaced by automatic submit at last file 
#
# submitting a job to wait until all images are created and average them:
# echo "nohup $SMART_DIR/bin/pawsey//submit_avg_magnus.sh \"${file_template}\" > avg_wait.out 2>&1 "
# nohup $SMART_DIR/bin/pawsey//submit_avg_magnus.sh "${file_template}" > avg_wait.out 2>&1 &
