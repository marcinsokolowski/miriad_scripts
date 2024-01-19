#!/bin/bash

image_path=`which imagefits.py`

echo "image_path = $image_path"
mkdir -p images_i/

for xx_file in `ls *_XX.fits`
do
   b=${xx_file%%_XX.fits}
   yy_file=${b}_YY.fits
   i_file=${b}_I.fits
   
   if [[ -s ${i_file} ]]; then
      echo "File ${i_file} already exists -> skipped"
   else   
      echo "calcfits_bg ${xx_file} B ${yy_file} ${i_file}"
      calcfits_bg ${xx_file} B ${yy_file} ${i_file}

      ls ${i_file} > tmp_new_list_to_process
      echo "python $image_path tmp_new_list_to_process  --outdir images_i/ --ext=png  --fits_list=tmp_new_list_to_process --out_image_type=\"png\""
      python $image_path tmp_new_list_to_process  --outdir images_i/ --ext=png  --fits_list=tmp_new_list_to_process --out_image_type="png" 
   fi
done
