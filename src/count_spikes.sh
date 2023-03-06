#!/bin/bash

obj_file=B0950+08_diff.txt
if [[ -n "$1" && "$1" != "-" ]]; then
   obj_file=$1
fi

off_file=OFF_B0950+08_diff.txt
if [[ -n "$2" && "$2" != "-" ]]; then
   off_file=$2
fi



root_path=`which root`
do_plots=0
if [[ -n "$root_path" ]]; then
   echo "CERN root found in $root_path - will be used"
   do_plots=1
else
   echo "WARNING : CERN root not found -> will skip plotting"   
fi

sigma_fit=5
rms=11
if [[ $do_plots -gt 0 ]]; then
   echo "Plotting histogram using root"
   root -l -q "histofile.C(\"${off_file}\",1,1,-50,50)"

   sigma_fit=`tail -1 sigma.txt | awk '{print $2;}'`
   rms=`tail -1 sigma.txt | awk '{print $6;}'`
else
   echo "WARNING : not plotting (no root found)"
fi   

max_rms=`echo $rms  | awk '{print $1*5;}'`

echo "Fitted noise : sigma = $sigma_fit , rms = $rms -> RMSx5 = --max_rmsiqr=${max_rms} "

threshold5sigma=`echo "$sigma_fit $rms" | awk '{rms=$1;if($2>rms){rms=$2;}printf("%.2f\n",(5*rms));}'`
threshold10sigma=`echo "$sigma_fit $rms" | awk '{rms=$1;if($2>rms){rms=$2;}printf("%.2f\n",(10*rms));}'`


path=`which count_spikes.py`
# Cuts :
# Allow maximum Sun elevation <= 20 degrees :
echo "Threshold 5sigma:"
echo "python $path --threshold=${threshold5sigma} --use_candidates --max_rmsiqr=${max_rms} --max_sun_elevation=20 --object_lc=${obj_file} --off_lc=${off_file}"
python $path --threshold=${threshold5sigma} --use_candidates --max_rmsiqr=${max_rms} --max_sun_elevation=20 --object_lc=${obj_file} --off_lc=${off_file}

echo "Threshold 10sigma:"
echo "python $path --threshold=${threshold10sigma} --use_candidates --max_rmsiqr=${max_rms} --max_sun_elevation=20 --object_lc=${obj_file} --off_lc=${off_file}"
python $path --threshold=${threshold10sigma} --use_candidates --max_rmsiqr=${max_rms} --max_sun_elevation=20 --object_lc=${obj_file} --off_lc=${off_file}

cd lc_filtered
threshold10sigma_int=`echo $threshold10sigma | awk '{printf("%d\n",$1);}'`
echo "ln -sf B0950+08_diff_thresh${threshold10sigma_int}Jy.txt B0950+08_diff_thresh10sigma.txt"
ln -sf B0950+08_diff_thresh${threshold10sigma_int}Jy.txt B0950+08_diff_thresh10sigma.txt
