#!/bin/bash


list_file=fits_list_to_process.tmp
ls chan*_XX.fits > fits_list_to_process.tmp
if [[ -n "$1" && "$1" != "-" ]]; then
   list_file=$1
fi

for fits_xx in `cat ${list_file}`
do
   fits_yy=${fits_xx%%_XX.fits}_YY.fits
   fits_i=${fits_xx%%_XX.fits}_I.fits   

   ls $fits_xx $fits_yy > xxyy_list

   # -r 1e20 - to allow any value of RMS 
   echo "avg_images xxyy_list ${fits_i} out_rms.fits -r 1e20"
   avg_images xxyy_list ${fits_i} out_rms.fits -r 1e20
   
   calcfits_bg ${fits_xx} 
done
