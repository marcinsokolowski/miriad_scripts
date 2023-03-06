#!/bin/bash

channel=294
if [[ -n "$1" && "$1" != "-" ]]; then
   channel=$1
fi

center=130
if [[ -n "$2" && "$2" != "-" ]]; then
   center=$2
fi

ls *rmsiqr.fits > fits_list_rmsiqr_I

# root_options="-b -q -l"
root_options="-l"

echo "python ~/github/eda2tv/source_finder/dump_pixel_simple_rms.py fits_list_rmsiqr_I $center $center rmsiqr_noisemaps/ --channel=${channel}"
python ~/github/eda2tv/source_finder/dump_pixel_simple_rms.py fits_list_rmsiqr_I $center $center rmsiqr_noisemaps/ --channel=${channel}

cd rmsiqr_noisemaps
awk '{mean=0;cnt=0;for(f=2;f<=NF;f++){mean+=$f;cnt+=1};print $1" "mean/cnt" "cnt;}' pixel_${center}_${center}.txt > mean_rms_vs_uxtime.txt


cp pixel_${center}_${center}.txt rms_vs_uxtime_ZA0deg.txt
awk '{mean=($3+$7+$11+$15)/4.00;print $1" "mean;}'  pixel_${center}_${center}.txt >  rms_vs_uxtime_ZA20deg.txt
awk '{mean=($4+$8+$12+$16)/4.00;print $1" "mean;}'  pixel_${center}_${center}.txt >  rms_vs_uxtime_ZA30deg.txt
awk '{mean=($5+$9+$13+$17)/4.00;print $1" "mean;}'  pixel_${center}_${center}.txt >  rms_vs_uxtime_ZA45deg.txt
awk '{mean=($6+$10+$14+$18)/4.00;print $1" "mean;}' pixel_${center}_${center}.txt >  rms_vs_uxtime_ZA75deg.txt

ls mean_rms_vs_uxtime.txt rms_vs_uxtime_ZA0deg.txt rms_vs_uxtime_ZA20deg.txt rms_vs_uxtime_ZA30deg.txt rms_vs_uxtime_ZA45deg.txt rms_vs_uxtime_ZA75deg.txt > rms_vs_uxtime.list
root ${root_options} "plotNfilesFlux_vs_time_scaling.C(\"rms_vs_uxtime.list\")"





