#!/bin/bash

do_xx_yy=0 # WARNING : do not use =1 as this when applied to other observation (calibration transfer) produces wrong flux scale !!!
           # 2023-01-28 : I think the above comment is no longer valid, at least for visibilities phase centred on the Sun 
if [[ -n "$1" && "$1" != "-" ]]; then
   do_xx_yy=$1
fi

freq_ch=204
if [[ -n "$2" && "$2" != "-" ]]; then
   freq_ch=$2
fi

hdf5_file=""
if [[ -n "$3" && "$3" != "-" ]]; then
   hdf5_file=$3
   echo $hdf5_file > miriad_calibrate_corr_hdf5_list.txt
else
   ls *.hdf5 > miriad_calibrate_corr_hdf5_list.txt
fi

processing_subdir="./"
subdir=0
if [[ -n "$4" && "$4" != "-" ]]; then
   processing_subdir=$4
   subdir=1
fi

final_caldir="calibration/"
if [[ -n "$5" && "$5" != "-" ]]; then
   final_caldir=$5
fi

n_uvfits=-1 # <0 -> ALL
if [[ -n "$6" && "$6" != "-" ]]; then
   n_uvfits=$6 
fi


echo "#############################################"
echo "PARAMETERS:"
echo "#############################################"
echo "hdf5_file = $hdf5_file"
echo "do_xx_yy = $do_xx_yy"
echo "freq_ch  = $freq_ch"
echo "processing_subdir = $processing_subdir (subdir = $subdir)"
echo "final cal dir  = $final_caldir"
echo "n_uvfits = $n_uvfits"
echo "#############################################"


inttime=1.9818086
n_avg=1
station_name=EDA2
convert_options="" # "-I 2"

export PATH=~/aavs-calibration/:$PATH

if [[ $subdir -gt 0 ]]; then
   path=`pwd`
   mkdir -p ${processing_subdir}
   cd ${processing_subdir}
   
   # CLEAN :
   echo "rm -fr *.L*C *.uvfits *.uv *.fits *.beam *.map"
   rm -fr *.L*C *.uvfits *.uv *.fits *.beam *.map
   
   echo "cp ${path}/miriad_calibrate_corr_hdf5_list.txt ."
   cp ${path}/miriad_calibrate_corr_hdf5_list.txt .
   
   for hdf5_file in `cat miriad_calibrate_corr_hdf5_list.txt`
   do
      echo "ln -sf ${path}/${hdf5_file}"
      ln -sf ${path}/${hdf5_file}
   done
   
   echo "List of hdf5 files to be converted to Sun phase centred uvfits:"
   echo "cat miriad_calibrate_corr_hdf5_list.txt"
   cat miriad_calibrate_corr_hdf5_list.txt
fi

# WARNING : this conversion is strictly required. It seems that we cannot use .uvfits files with were originally converted to zenith phase centre and then uvedit them
#           we do need to convert again (at least until we know why change of phase centre does not work).
#           It seems that when calibration after uvedit (ra,dec=Sun) is applied to another phase centred .uv data the flux scale can go crazy or image is offset
# removed option -z to have Sun in the phase center :
pwd
echo "hdf5_to_uvfits_all.sh -c -l -i $inttime -n $n_avg -d "./" -N -a 1 -f $freq_ch -L miriad_calibrate_corr_hdf5_list.txt -S 0 -s ${station_name} $convert_options"
hdf5_to_uvfits_all.sh -c -l -i $inttime -n $n_avg -d "./" -N -a 1 -f $freq_ch -L miriad_calibrate_corr_hdf5_list.txt -S 0 -s ${station_name} $convert_options

if [[ $n_uvfits -gt 0 ]]; then
   ls *.uvfits | head --lines=${n_uvfits} | tail -1 > miriad_calibrate_corr.uvlist
else
   ls *.uvfits > miriad_calibrate_corr.uvlist
fi

echo "DEBUG (miriad_calibrate_corr.sh) calibrating using the following UVFITS files converted with Sun in the phase centre:"
echo
cat miriad_calibrate_corr.uvlist
echo

# LAST 0 indicates that changing of phase centre to Sun is not required because the above command hdf5_to_uvfits_all.sh 
# already converts HDF5 files to UVFITS files with phase centre on the Sun :
echo "~/aavs-calibration/calibrate_uvfits.sh ${do_xx_yy} ${freq_ch} miriad_calibrate_corr.uvlist - ${final_caldir} - 1 0"
~/aavs-calibration/calibrate_uvfits.sh ${do_xx_yy} ${freq_ch} miriad_calibrate_corr.uvlist - ${final_caldir} - 1 0
