#!/bin/bash

export PATH=~/github/hdf5_correlator/scripts:$PATH

zenith=0
if [[ -n "$1" && "$1" != "-" ]]; then
   zenith=1
fi

inttime=0.28
n_avg=8140
freq_ch=204
station_name=EDA2
convert_options="" # "-I 2"
if [[ $zenith -gt 0 ]]; then
   convert_options="$convert_options -z"
fi

ls *.hdf5 > new_hdf5_list.txt

export PATH=~/aavs-calibration/:$PATH

# removed option -z to have Sun in the phase center :
echo "hdf5_to_uvfits_all.sh -c -l -i $inttime -n $n_avg -d "./" -N -f $freq_ch -l -L new_hdf5_list.txt -s ${station_name} $convert_options"
hdf5_to_uvfits_all.sh -c -l -i $inttime -n $n_avg -d "./" -N -f $freq_ch -l -L new_hdf5_list.txt -s ${station_name} $convert_options

# echo "~/aavs-calibration/calibrate_uvfits.sh"
# ~/aavs-calibration/calibrate_uvfits.sh