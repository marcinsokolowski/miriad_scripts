#!/bin/bash

list=fits_list_I
if [[ -n "$1" && "$1" != "-" ]]; then
   list=$1
fi

stokes=I
if [[ -n "$2" && "$2" != "-" ]]; then
   stokes=$2
fi

miriad_diff_images=1
if [[ -n "$3" && "$3" != "-" ]]; then
  miriad_diff_images=$3
fi

force=0

center_radius=5

rms_script_path=`which miriad_rms.py`
source_finder_path=`which source_finder_simple.py`

index=0
prev_fits=""

while read fits_file # example 
do
   diff_file=${fits_file%%.fits}_diff.fits
   src_finder_out=${fits_file%%.fits}_diff.srcfinder_out
   
   if [[ $stokes == "XX" ]]; then   
      prev_fits=${fits_file%%14_XX.fits}00_XX.fits
   else
      if [[ $stokes == "YY" ]]; then   
         prev_fits=${fits_file%%14_YY.fits}00_YY.fits
      else
         prev_fits=${fits_file%%14_${stokes}.fits}00_${stokes}.fits
      fi
   fi
   
   if [[ ! -s ${diff_file} || $force -gt 0 ]]; then
      if [[ $index -ge 1 ]]; then
         if [[ $miriad_diff_images -gt 0 ]]; then
            echo "miriad_diff.sh $fits_file $prev_fits $diff_file"
            miriad_diff.sh $fits_file $prev_fits $diff_file
         else
            echo "calcfits_bg $fits_file - $prev_fits $diff_file"
            calcfits_bg $fits_file - $prev_fits $diff_file
         fi                 
                  
         echo "python $rms_script_path $diff_file --outfile=rms_vs_time_full_image_${stokes}.txt >> rms_${stokes}.out"         
         python $rms_script_path $diff_file --outfile=rms_vs_time_full_image_${stokes}.txt >> rms_${stokes}.out 
                  
         # also calculate RMS in the very center of the image :
         echo "python $rms_script_path $diff_file --center --radius=${center_radius} --outfile=rms_vs_time_center_${stokes}.txt >> rms_${stokes}_radius${center_radius}.out"
         python $rms_script_path $diff_file --center --radius=${center_radius} --outfile=rms_vs_time_center_${stokes}.txt >> rms_${stokes}_radius${center_radius}.out
                  
         echo "python $source_finder_path $diff_file > $src_finder_out 2>&1"
         python $source_finder_path $diff_file > $src_finder_out 2>&1
      else 
         echo "First file $fits_file skipped"
      fi   
   else
      echo "Difference file $diff_file already exists -> skipped"
   fi

   prev_fits=$fits_file
   index=$(($index+1))
done < $list


ls *_${stokes}_diff.fits > diff_fits_list_${stokes}
# sd9all! 1 - - "chan_204*_${stokes}_diff.fits" - - "images_${stokes}_diff/"
