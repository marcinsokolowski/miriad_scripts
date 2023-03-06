#!/bin/bash

image_XX=fits_XX.fits
if [[ -n "$1" && "$1" != "-" ]]; then
   image_XX=$1
fi

image_YY=${image_XX%%_XX.fits}_YY.fits
if [[ -n "$2" && "$2" != "-" ]]; then
   image_YY=$2
fi

out_image=${image_XX%%_XX.fits}_I.fits
if [[ -n "$3" && "$3" != "-" ]]; then
   out_image=$3
fi

outdir=BeamCorr/
if [[ -n "$4" && "$4" != "-" ]]; then
   outdir=$4
fi
mkdir -p ${outdir}

force=0
if [[ -n "$5" && "$5" != "-" ]]; then
   force=$5
fi


beam_corr=1

if [[ -s beam_XX.fits && -s beam_YY.fits ]]; then
  echo "Beam FITS files beam_XX.fits and beam_YY.fits found -> beam correcting XX and YY images"
else
  echo "WARNING : beam FITS files beam_XX.fits and beam_YY.fits not found -> no beam correction possible"
  beam_corr=0
fi

if [[ -s ${out_image} && $force -le 0 ]]; then
   echo "INFO : file ${out_image} already exists -> skipped (use force=1 to re-process)"
   exit;
fi

calcfits_path=`which calcfits_bg`


# cp /home/msok//github/station_beam/Beams/AAVS2/chan_204_BeamX.fits beam_XX.fits
if [[ $beam_corr -gt 0 ]]; then
#   echo "INFO : applying beam correction, uncorrected files backed-up to beam_uncorr/"
#   mkdir -p beam_uncorr/
   
#   echo "cp ${image_XX} beam_uncorr/"
#   cp ${image_XX} beam_uncorr/

#   echo "cp ${image_YY} beam_uncorr/"
#   cp ${image_YY} beam_uncorr/

   if [[ -n "$calcfits_path" ]]; then
      echo "DEBUG : program calcfits_bg ( $calcfits_path ) exists -> using it to divide XX and YY images by the beam"
  
      echo "$calcfits_path $image_XX / beam_XX.fits ${outdir}/${image_XX}"
      $calcfits_path $image_XX / beam_XX.fits ${outdir}/${image_XX}
      
      echo "$calcfits_path $image_YY / beam_YY.fits ${outdir}/${image_YY}"
      $calcfits_path $image_YY / beam_YY.fits ${outdir}/${image_YY}
   else 
       echo "WARNING : program calcfits_bg not found -> using python script to divide XX and YY images by the beam" 
       div_path=`which miriad_fits_div.py`

       echo "python $div_path $image_XX / beam_XX.fits ${outdir}/${image_XX}"
       python $div_path $image_XX / beam_XX.fits ${outdir}/${image_XX}

       echo "python $div_path $image_YY / beam_YY.fits ${outdir}/${image_YY}"
       python $div_path $image_YY / beam_YY.fits ${outdir}/${image_YY}
   fi
else
   echo "WARNING : beam correction of XX and YY images is not applied"
fi

if [[ $beam_corr -gt 0 ]]; then
   echo "WARNING : performing beam correction -> going to $outdir directory"
   
   cd ${outdir}
   pwd
fi

if [[ -n "$calcfits_path" ]]; then
   echo "DEBUG : program calcfits_bg ( $calcfits_path ) exists -> using it to calculate (XX+YY)/2 = Stokes I"
   
   # 20200905 - A -> B (A was ABSOLUTE VALUE !!!)
   echo "$calcfits_path ${image_XX} B ${image_YY} ${out_image}"
   $calcfits_path ${image_XX} B ${image_YY} ${out_image}
else
   echo "WARNING : program calcfits_bg not found -> using MIRIAD to calculate (XX+YY)/2 = Stokes I"
   image_XX_uv=${image_XX%%.fits}_tmp.uv
   image_YY_uv=${image_YY%%.fits}_tmp.uv
   out_image_uv=${out_image%%.fits}_tmp.uv

   echo "rm -fr ${out_image_uv} ${image_XX_uv} ${image_YY_uv}"
   rm -fr ${out_image_uv} ${image_XX_uv} ${image_YY_uv}

   if [[ ! -d ${image_XX_uv} ]]; then
      echo "fits op=xyin in=${image_XX} out=${image_XX_uv}"
      fits op=xyin in=${image_XX} out=${image_XX_uv}
   else
      echo "INFO : ${image_XX_uv} already exists"
   fi

   if [[ ! -d ${image_YY_uv} ]]; then
      echo "fits op=xyin in=${image_YY} out=${image_YY_uv}"
      fits op=xyin in=${image_YY} out=${image_YY_uv}
   else
      echo "INFO : ${image_YY_uv} already exists"
   fi   


   echo "maths exp=\"(${image_XX_uv}+${image_YY_uv})/2\" out=${out_image_uv}"
   maths exp="(${image_XX_uv}+${image_YY_uv})/2" out=${out_image_uv}


   echo "fits op=xyout in=${out_image_uv} out=${out_image}"
   fits op=xyout in=${out_image_uv} out=${out_image}

   echo "rm -fr ${out_image_uv} ${image_XX_uv} ${image_YY_uv}"
   rm -fr ${out_image_uv} ${image_XX_uv} ${image_YY_uv}
fi

if [[ $beam_corr -gt 0 ]]; then
   cd ../
   
   # if BeamCorrecting - create symbolic link to Stokes I calculated from BeamCorrected XX and YY files :
   echo "ln -s ${outdir}/${out_image}"
   ln -s ${outdir}/${out_image}
fi

