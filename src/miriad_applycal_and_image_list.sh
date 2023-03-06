#!/bin/bash

listfile="uvfits_list"
if [[ -n "$1" && "$1" != "-" ]]; then
  listfile=$1
fi

cal=chan_204_20191228T052443
if [[ -n "$2" && "$2" != "-" ]]; then
   cal=$2
fi

imsize=180 # 128 or 256 
if [[ -n "$3" && "$3" != "-" ]]; then
   imsize=$3
fi

robust=-0.5
if [[ -n "$4" && "$4" != "-" ]]; then
   robust=$4
fi

diff_images=1
if [[ -n "$5" && "$5" != "-" ]]; then
   diff_images=$5
fi

n_modulo_convert_to_jpg=1
if [[ -n "$6" && "$6" != "-" ]]; then
   n_modulo_convert_to_jpg=$6
fi

fixhdr=1
if [[ -n "$7" && "$7" != "-" ]]; then
   fixhdr=$7
fi

do_images=1
if [[ -n "$8" && "$8" != "-" ]]; then
   do_images=$8
fi

allow_missing_cal=1
if [[ -n "$9" && "$9" != "-" ]]; then
   allow_missing_cal=$9
fi

all_channels=0 # if >1 -> image all fine channels
if [[ -n "${10}" && "${10}" != "-" ]]; then
   all_channels=${10}
fi


if [[ ! -d ${cal}_XX.uv || ! -d ${cal}_YY.uv ]]; then
   if [[ $allow_missing_cal -gt 0 ]]; then
      echo "WARNING : at least one of calibration files ${cal}_XX.uv or ${cal}_YY.uv does not exist !!! -> however allow_missing_cal=1 -> continuning processing"
   else
      echo "ERROR : at least one of calibration files ${cal}_XX.uv or ${cal}_YY.uv does not exist !!! -> cannot continue and exiting now !!!" 
      exit -1
   fi
else
   echo "OK : calibration solution files ${cal}_XX.uv and ${cal}_YY.uv exist"
fi



# frb_x=99
# frb_y=86

echo "##################################################"
echo "PARAMETERS :"
echo "##################################################"
echo "listfile    = $listfile"
echo "cal         = $cal"
echo "imsize      = $imsize"
echo "robust      = $robust"
echo "diff_images = $diff_images"
echo "n_modulo_convert_to_jpg = $n_modulo_convert_to_jpg"
echo "fixhdr      = $fixhdr"
echo "do_images   = $do_images"
echo "##################################################"
echo "Version with XX and YY images separately calibrated"
echo "##################################################"




average_images_path=`which average_images.py`
print_path=`which print_image_flux_single.py`
show_path=`which show_known_sources.py`


rm -f values.txt values_XX.txt values_YY.txt

rm -f tmp_new_list_to_process
idx=0
for uvfits in `cat $listfile`
do
   uvfits_base=${uvfits%%.uvfits}

   if [[ ! -s ${uvfits_base}_XX.fits ]]; then
      rest=$(($idx % $n_modulo_convert_to_jpg))
      do_png=0      
      if [[ $rest == 0 ]]; then
         do_png=1
      fi
      echo "DEBUG : rest = $rest -> do_png = $do_png"
     
      # These are done later in bulk (to optimise calls to python) :
      # fixCoordHdr.py, miriad_avg_xxyy.sh, show_known_sources.py and miriad_image2jpg.sh 

# OLD version does not allow for application of proper cal. solutions with correction for Sun beam in X and Y polarisations :
#      echo "miriad_applycal_and_image.sh ${uvfits_base} ${cal} ${imsize} ${robust} 0 0"
#      miriad_applycal_and_image.sh ${uvfits_base} ${cal} ${imsize} ${robust} 0 0 
      
      
      echo "miriad_applycal_and_image_xxyy.sh ${uvfits_base} ${cal} ${imsize} ${robust} 0 0 $all_channels"
      miriad_applycal_and_image_xxyy.sh ${uvfits_base} ${cal} ${imsize} ${robust} 0 0 $all_channels
      
      echo $uvfits_base >> tmp_new_list_to_process
      
      ls ${uvfits_base}_XX.fits ${uvfits_base}_YY.fits > ${uvfits_base}.list 
      
      # (XX+YY) -> I       
      # TODO : in the future proper calculation of Stokes I from XX and YY !!!
      #        using Adrian's formalism 
#      echo "miriad_avg_xxyy.sh ${uvfits_base}_XX.fits"
#      miriad_avg_xxyy.sh ${uvfits_base}_XX.fits
      
#      echo "python $show_path ${uvfits_base}_XX.fits"
#      python $show_path ${uvfits_base}_XX.fits
      
#      echo "python $average_images_path ${uvfits_base}.list ${uvfits_base}_I.fits 0 0 -10000 +10000"
#      python $average_images_path ${uvfits_base}.list ${uvfits_base}_I.fits 0 0 -10000 +10000 
      
#      echo "python $print_path ${uvfits_base}_I.fits $frb_x $frb_y >> values_I.txt"
#      python $print_path ${uvfits_base}_I.fits $frb_x $frb_y >> values_I.txt
      
#      echo "python $print_path ${uvfits_base}_XX.fits $frb_x $frb_y >> values_XX.txt"
#      python $print_path ${uvfits_base}_XX.fits $frb_x $frb_y >> values_XX.txt
      
#      echo "python $print_path ${uvfits_base}_YY.fits $frb_x $frb_y >> values_YY.txt"
#      python $print_path ${uvfits_base}_YY.fits $frb_x $frb_y >> values_YY.txt
   else
      echo "$uvfits already processed -> skipped"
   fi
   
   idx=$(($idx+1))
done

if [[ $all_channels -le 0 ]]; then
   path=`which fixCoordHdr.py`
   if [[ $fixhdr -gt 0 ]]; then
      echo "time python $path tmp_new_list_to_process --list=tmp_new_list_to_process --remove_axis"
      time python $path tmp_new_list_to_process --list=tmp_new_list_to_process --remove_axis
   else
      echo "WARNING : fixCoordHdr.py skipped"
   fi  

   # for src in `cat tmp_new_list_to_process`
   # do
   #   echo "time miriad_avg_xxyy.sh ${src}_XX.fits"   
   #   time miriad_avg_xxyy.sh ${src}_XX.fits
   #done

   # this script does not work correctly for CUBE images with >1 channel 
   xxyy2i_path=`which miriad_xxyy2i.py`    
   echo "python $xxyy2i_path tmp_new_list_to_process"
   python $xxyy2i_path tmp_new_list_to_process 
else
   echo "WARNING : generating data cube for all channels and script fixCoordHdr.py is not ready for this -> skipped -> coordinates might be wrong !"
fi   

if [[ $do_images -gt 0 ]]; then
   png_stokes=XX
   show_path=`which show_known_sources.py`
   echo "python $show_path tmp_new_list_to_process --add_extension=\"_${png_stokes}.fits\""
   time python $show_path tmp_new_list_to_process --add_extension="_${png_stokes}.fits" 

   image_path=`which imagefits.py`
   echo "python $image_path tmp_new_list_to_process  --outdir images/ --ext=png  --reg_postfix=\"_known_sources.reg\" --fits_list=tmp_new_list_to_process --out_image_type=\"png\" --every_n_fits=$n_modulo_convert_to_jpg"
   python $image_path tmp_new_list_to_process  --outdir images/ --ext=png  --reg_postfix="_known_sources.reg" --fits_list=tmp_new_list_to_process --out_image_type="png" --every_n_fits=$n_modulo_convert_to_jpg
else
   echo "WARNING : show_known_sources.py and imagefits.py skipped"
fi

# (XX+YY) -> I       
# TODO : in the future proper calculation of Stokes I from XX and YY !!!
#        using Adrian's formalism 
# echo "miriad_avg_xxyy_list.sh"
# miriad_avg_xxyy_list.sh


if [[ $diff_images -gt 0 ]]; then
   export PATH="/opt/caastro/ext/anaconda/bin:$PATH"
   sd9all! 1 - - "chan_204*XX.fits" - - "images_XX/"
   sd9all! 1 - - "chan_204*YY.fits" - - "images_YY/"
   sd9all! 1 - - "chan_204*I.fits"  - - "images_I/"

   ls chan_204*_I.fits > fits_list_I
   diff_images.sh fits_list_I I

   ls chan_204*_XX.fits > fits_list_XX
   diff_images.sh fits_list_XX XX

   ls chan_204*_YY.fits > fits_list_YY
   diff_images.sh fits_list_YY YY

   path_rms=`which rms.py`
   echo "python $path_rms diff_fits_list_I -x ${frb_x} -y ${frb_y} --radius=5 > rms_x${frb_x}_y${frb_y}_radius5.txt"
   python $path_rms diff_fits_list_I -x ${frb_x} -y ${frb_y} --radius=5 > rms_x${frb_x}_y${frb_y}_radius5.txt
else
   echo "WARNING : sd9all! , diff_images and rms are not required"   
fi
