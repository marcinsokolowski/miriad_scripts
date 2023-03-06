#!/bin/bash

list=fits_list_I
if [[ -n "$1" && "$1" != "-" ]]; then
   list=$1
fi

stokes=I
if [[ -n "$2" && "$2" != "-" ]]; then
   stokes=$2
fi

miriad_diff_images=1 # use miriad to subtract images of calcfits_bg program
if [[ -n "$3" && "$3" != "-" ]]; then
  miriad_diff_images=$3
fi

freq_ch=204
if [[ -s channel.txt ]]; then
   freq_ch=`cat channel.txt`
   echo "freq_ch = $freq_ch (from file channel.txt)"
fi

if [[ -n "$4" && "$4" != "-" ]]; then
   freq_ch=$4
fi

station_name=eda2
if [[ -n "$5" && "$5" != "-" ]]; then
   station_name=$5
fi

do_source_finder=0
if [[ -n "$6" && "$6" != "-" ]]; then
   do_source_finder=$6
fi

do_processing=1
if [[ -n "$7" && "$7" != "-" ]]; then
   do_processing=$7
fi


force=0
force_source_finder=1
source_finder_on_all=0
center_radius=5
new_diff_fits_files=new_diff_fits_files_${stokes}.txt

rms_script_path=`which miriad_rms.py`
source_finder_path=`which source_finder_simple.py`

echo "##########################################################################################"
echo "PARAMETERS:"
echo "##########################################################################################"
echo "list          = $list"
echo "stokes        = $stokes -> ${new_diff_fits_files}"
echo "miriad_diff_images = $miriad_diff_images"
echo "freq_ch       = $freq_ch"
echo "do_processing = $do_processing"
echo "##########################################################################################"


index=0
prev_fits=""
rm -f ${new_diff_fits_files}

while read fits_file # example 
do
   diff_file=${fits_file%%.fits}_diff.fits
   diff_file_base=${fits_file%%.fits}_diff
   src_finder_out=${fits_file%%.fits}_diff.srcfinder_out
   
   do_source_finder=$force_source_finder   
   
   size=0
   if [[ -s ${diff_file} ]]; then
      size=`stat ${diff_file} --format=%s`
      echo "File $diff_file size = $size"
   fi
   
   if [[ ! -s ${diff_file} || $size -le 0 || $force -gt 0 ]]; then
      if [[ $index -ge 1 ]]; then
         if [[ $miriad_diff_images -gt 0 ]]; then
            echo "time miriad_diff.sh $fits_file $prev_fits $diff_file"
            time miriad_diff.sh $fits_file $prev_fits $diff_file
         else
            echo "time calcfits_bg $fits_file - $prev_fits $diff_file"
            time calcfits_bg $fits_file - $prev_fits $diff_file
         fi                 
         
         echo $diff_file >> ${new_diff_fits_files}
                  
#         echo "time python $rms_script_path $diff_file --outfile=rms_vs_time_full_image_${stokes}.txt >> rms_${stokes}.out"         
#         time python $rms_script_path $diff_file --outfile=rms_vs_time_full_image_${stokes}.txt >> rms_${stokes}.out 
                  
         # also calculate RMS in the very center of the image :
#         echo "time python $rms_script_path $diff_file --center --radius=${center_radius} --outfile=rms_vs_time_center_${stokes}.txt >> rms_${stokes}_radius${center_radius}.out"
#         time python $rms_script_path $diff_file --center --radius=${center_radius} --outfile=rms_vs_time_center_${stokes}.txt >> rms_${stokes}_radius${center_radius}.out

#         if [[ $do_source_finder -gt 0 ]]; then         
#            if [[ $source_finder_on_all -le 0 ]]; then
#               echo "DEBUG : running source finder on new diff images only :"
#               echo "python $source_finder_path $diff_file --thresh_in_sigma=5 > $src_finder_out 2>&1"
#               python $source_finder_path $diff_file --thresh_in_sigma=5 > $src_finder_out 2>&1
#            fi
#         else 
#            echo "WARNING : source finder is not required"
#         fi
      else 
         echo "First file $fits_file skipped"
      fi   
   else
      echo "Difference file $diff_file already exists -> skipped"      
   fi

#   if [[ $do_source_finder -gt 0 ]]; then   
#      if [[ $source_finder_on_all -gt 0 ]]; then
#          echo "DEBUG : running source finder on all :"
#          echo "python $source_finder_path $diff_file --thresh_in_sigma=5 > $src_finder_out 2>&1"
#          python $source_finder_path $diff_file --thresh_in_sigma=5 > $src_finder_out 2>&1
#      fi
#   else 
#      echo "WARNING : source finder is not required"
#   fi
   
#   echo "miriad_image2jpg.sh $diff_file_base I - ${diff_file_base}_cand.reg images_diff/ ${diff_file_base}.fits"
#   miriad_image2jpg.sh $diff_file_base I - ${diff_file_base}_cand.reg images_diff/ ${diff_file_base}.fits

   prev_fits=$fits_file
   index=$(($index+1))
done < $list

if [[ $do_processing -gt 0 ]]; then
   echo "INFO : processing difference images is required"

   if [[ ! -d images_diff ]]; then
      echo "DEBUG : directory images_diff does not exist -> re-processing all *_${stokes}_diff.fits files"
#       ls *_${stokes}_diff.fits > ${new_diff_fits_files}
      find . -name "*_${stokes}_diff.fits" -maxdepth 1 | awk '{gsub("./","");print $0;}' | sort > ${new_diff_fits_files}
   fi

   if [[ -s ${new_diff_fits_files} ]]; then
      echo "DEBUG : starting processing new diff files at :"
      date

      echo "time python $rms_script_path ${new_diff_fits_files} --outfile=rms_vs_time_full_image_${stokes}.txt >> rms_${stokes}.out"         
      time python $rms_script_path ${new_diff_fits_files} --outfile=rms_vs_time_full_image_${stokes}.txt >> rms_${stokes}.out 
                  
      # also calculate RMS in the very center of the image :
      echo "time python $rms_script_path ${new_diff_fits_files} --center --radius=${center_radius} --outfile=rms_vs_time_center_${stokes}.txt >> rms_${stokes}_radius${center_radius}.out"
      time python $rms_script_path ${new_diff_fits_files} --center --radius=${center_radius} --outfile=rms_vs_time_center_${stokes}.txt >> rms_${stokes}_radius${center_radius}.out

      echo "time python $source_finder_path ${new_diff_fits_files} --thresh_in_sigma=5 --dont_check_ateam_sources --transient_mode >> source_finder_on_diff_${stokes}.out 2>&1"
      time python $source_finder_path ${new_diff_fits_files} --thresh_in_sigma=5 --dont_check_ateam_sources --transient_mode >> source_finder_on_diff_${stokes}.out 2>&1

      image_path=`which imagefits.py`
      echo "time python $image_path ${new_diff_fits_files} --outdir=images_diff/ --ext=png --reg_postfix=\"_cand.reg\" --fits_list=${new_diff_fits_files} --out_image_type=\"png\" --every_n_fits=1 >> imagefits_${stokes}.out 2>&1"
      time python $image_path ${new_diff_fits_files} --outdir=images_diff/ --ext=png --reg_postfix="_cand.reg" --fits_list=${new_diff_fits_files} --out_image_type="png" --every_n_fits=1 >> imagefits_${stokes}.out 2>&1
      # python $image_path tmp_new_list_to_process  --outdir images/ --ext=png  --reg_postfix="_known_sources.reg" --fits_list=tmp_new_list_to_process --out_image_type="png" --every_n_fits=$n_modulo_convert_to_jpg

      echo "eda2tv_make_movie.sh ${freq_ch} ${station_name} 1 images_diff/movie/ 0 ${stokes}"
      eda2tv_make_movie.sh ${freq_ch} ${station_name} 1 images_diff/movie/ 0 ${stokes}
   else
      echo "DEBUG : file ${new_diff_fits_files} not found -> no new diff files to process"
   fi


   find . -name "*_I_diff.fits" -maxdepth 1 | awk '{gsub("./","");print $0;}' | sort > diff_fits_list_${stokes}
   # ls *_${stokes}_diff.fits > diff_fits_list_${stokes}
   # sd9all! 1 - - "chan_204*_${stokes}_diff.fits" - - "images_${stokes}_diff/"
else
   echo "WARNING : processing of difference images is not required -> skipped"
fi   
