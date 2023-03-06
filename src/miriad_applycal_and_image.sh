#!/bin/bash

src=chan_204_20191228T052443
if [[ -n "$1" && "$1" != "-" ]]; then
  src=$1
fi

cal=cal
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

do_png=1
if [[ -n "$5" && "$5" != "-" ]]; then
   do_png=$5
fi

do_corrections=1
if [[ -n "$6" && "$6" != "-" ]]; then
   do_corrections=$6
fi

is_cal_xxyy=`echo $cal | awk '{u=toupper($1);is_cal_xxyy=index(u,"_X");if(is_cal_xxyy<=0){is_cal_xxyy=index(u,"_Y");}print is_cal_xxyy;}'`
echo "is_cal_xxyy = $is_cal_xxyy"
if [[ -n "$7" && "$7" != "-" ]]; then
   is_cal_xxyy=$7
fi

echo "###########################################"
echo "PARAMETERS:"
echo "###########################################"
echo "is_cal_xxyy = $is_cal_xxyy"
echo "###########################################"


png_stokes=XX

if [[ -d ${src}.uv ]]; then
   echo "UV files ${src}.uv exist -> no need to execute conversion task (.uvfits -> .uv) : fits op=uvin in=${src}.uvfits out=${src}.uv options=compress"
else
   echo "fits op=uvin in=${src}.uvfits out=${src}.uv options=compress"
   fits op=uvin in=${src}.uvfits out=${src}.uv options=compress
fi

# FLAGGING for 2019-12-28 data (EDA2) :
# uvflag flagval=flag vis=${src}.uv select='ant(1,2,3,4,5,6,7,8,9,17,18,19,20,21,22,23,24,31,60,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,125,129,130,131,132,133,134,135,136,137,138,139,140)'
# uvflag flagval=flag vis=${src}.uv select='ant(141,142,143,144,153,154,155,156,157,158,159,160,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,201,202,203,204,205,206,207,208,217,218,219,220,221,222,223,224,230,241,245,249,250,251,252,253,254,255,256)'

# 2019-12-28 AAVS2 :
# uvflag flagval=flag vis=${src}.uv select='ant(1,2,3,4,5,6,7,8,33,34,35,36,37,38,39,40,57,58,59,60,61,62,63,64,117,118,119,120,125,126,127,128,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,201,202,203,204,205,206,207)'
# uvflag flagval=flag vis=${src}.uv select='ant(208,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,241,242,243,244,245,246,247,248)'

echo "puthd in=${src}.uv/jyperk value=2000.0"
puthd in=${src}.uv/jyperk value=2000.0

echo "puthd in=${src}.uv/systemp value=200.0"
puthd in=${src}.uv/systemp value=200.0

# make calibration solutions valid for infinite time (365 days is good enough as infinity in this case) :
echo "puthd in=${cal}.uv/interval value=365"
puthd in=${cal}.uv/interval value=365

rm -fr ${src}_XX.map ${src}_XX.beam
rm -fr ${src}_YY.map ${src}_YY.beam

if [[ $is_cal_xxyy -gt 0 ]]; then
   # WARNING : this does not apply correct flux scale !
   echo "Apply calibration to _XX.uv and _YY.uv files"

   if [[ -d ${src}_XX.uv ]]; then
      echo "INFO : ${src}_XX.uv already exists -> no need to call uvcat"
      
      echo "puthd in=${src}_XX.uv/jyperk value=2000.0"
      puthd in=${src}_XX.uv/jyperk value=2000.0
      
      echo "puthd in=${src}_XX.uv/systemp value=200.0"
      puthd in=${src}_XX.uv/systemp value=200.0

      # make calibration solutions valid for infinite time (365 days is good enough as infinity in this case) :
      echo "puthd in=${cal}_XX.uv/interval value=365"
      puthd in=${cal}_XX.uv/interval value=365
   else   
      echo "uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv"
      uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
   fi
   
   if [[ -d ${src}_YY.uv ]]; then
      echo "INFO : ${src}_YY.uv already exists -> no need to call uvcat"
      
      echo "puthd in=${src}_YY.uv/jyperk value=2000.0"
      puthd in=${src}_YY.uv/jyperk value=2000.0

      echo "puthd in=${src}_YY.uv/systemp value=200.0"
      puthd in=${src}_YY.uv/systemp value=200.0

      # make calibration solutions valid for infinite time (365 days is good enough as infinity in this case) :
      echo "puthd in=${cal}_YY.uv/interval value=365"
      puthd in=${cal}_YY.uv/interval value=365
   else
      echo "uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv"
      uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv
   fi

   # apply calibration :
   echo "gpcopy vis=${cal}_XX.uv out=${src}_XX.uv options=relax mode=copy"
   gpcopy vis=${cal}_XX.uv out=${src}_XX.uv options=relax mode=copy
   
   echo "gpcopy vis=${cal}_YY.uv out=${src}_YY.uv options=relax mode=copy"
   gpcopy vis=${cal}_YY.uv out=${src}_YY.uv options=relax mode=copy

   echo "invert vis=${src}_XX.uv map=${src}_XX.map imsize=${imsize},${imsize} beam=${src}_XX.beam robust=$robust options=double,mfs stokes=XX select='uvrange(0.0,100000)'"
   invert vis=${src}_XX.uv map=${src}_XX.map imsize=${imsize},${imsize} beam=${src}_XX.beam robust=$robust options=double,mfs stokes=XX select='uvrange(0.0,100000)'
   echo "fits op=xyout in=${src}_XX.map out=${src}_XX.fits"
   fits op=xyout in=${src}_XX.map out=${src}_XX.fits

   echo "invert vis=${src}_YY.uv map=${src}_YY.map imsize=${imsize},${imsize} beam=${src}_YY.beam robust=$robust options=double,mfs stokes=YY select='uvrange(0.0,100000)'"
   invert vis=${src}_YY.uv map=${src}_YY.map imsize=${imsize},${imsize} beam=${src}_YY.beam robust=$robust options=double,mfs stokes=YY select='uvrange(0.0,100000)'
   echo "fits op=xyout in=${src}_YY.map out=${src}_YY.fits"
   fits op=xyout in=${src}_YY.map out=${src}_YY.fits
else
   echo "Apply calibration to .uv file"
 
   # calibration for both pols :
   # apply to .uv file and split into polarisation later:
   echo "gpcopy vis=${cal}.uv out=${src}.uv options=relax mode=copy"
   gpcopy vis=${cal}.uv out=${src}.uv options=relax mode=copy
   
#   uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
#   uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv

   echo "invert vis=${src}.uv map=${src}_XX.map imsize=${imsize},${imsize} beam=${src}_XX.beam robust=$robust options=double,mfs stokes=XX select='uvrange(0.0,100000)'"
   invert vis=${src}.uv map=${src}_XX.map imsize=${imsize},${imsize} beam=${src}_XX.beam robust=$robust options=double,mfs stokes=XX select='uvrange(0.0,100000)'
   echo "fits op=xyout in=${src}_XX.map out=${src}_XX.fits"
   fits op=xyout in=${src}_XX.map out=${src}_XX.fits

   echo "invert vis=${src}.uv map=${src}_YY.map imsize=${imsize},${imsize} beam=${src}_YY.beam robust=$robust options=double,mfs stokes=YY select='uvrange(0.0,100000)'"
   invert vis=${src}.uv map=${src}_YY.map imsize=${imsize},${imsize} beam=${src}_YY.beam robust=$robust options=double,mfs stokes=YY select='uvrange(0.0,100000)'
   echo "fits op=xyout in=${src}_YY.map out=${src}_YY.fits"
   fits op=xyout in=${src}_YY.map out=${src}_YY.fits
fi

utc=`fitshdr ${src}_XX.fits  | grep DATE-OBS | awk '{gsub("''","",$0);dtm=substr($2,2,19);gsub("T","_",dtm);gsub("-","",dtm);gsub(":","",dtm);print dtm;}'`
echo "utc = $utc"

# ux=`date2date -ut2ux=${utc} | awk '{print $3;}'`
# lst=`ux2sid $ux | awk '{print $8}'`
# echo "ux = $ux -> lst = $lst"

if [[ $do_corrections -gt 0 ]]; then
   # optimisations : both XX and YY files in one go:
   path=`which fixCoordHdr.py`
   echo "time python $path ${src}_XX.fits,${src}_YY.fits"
   time python $path ${src}_XX.fits,${src}_YY.fits

   # echo "time python $path ${src}_YY.fits"
   # time python $path ${src}_YY.fits

   # (XX+YY) -> I       
   # TODO : in the future proper calculation of Stokes I from XX and YY !!!
   #        using Adrian's formalism 
   echo "time miriad_avg_xxyy.sh ${src}_XX.fits"
   time miriad_avg_xxyy.sh ${src}_XX.fits

   show_path=`which show_known_sources.py`
   echo "python $show_path ${src}_${png_stokes}.fits"
   time python $show_path ${src}_${png_stokes}.fits

   if [[ $do_png -gt 0 ]]; then   
      echo "time miriad_image2jpg.sh ${src} ${png_stokes}"
      time miriad_image2jpg.sh ${src} ${png_stokes}
   else 
      echo "WARNING : png file is not required"
   fi
else
   echo "WARNING : fixCoordHdr.py, miriad_avg_xxyy.sh, show_known_sources.py and miriad_image2jpg.sh is not required - maybe it's done by the calling script"
fi   



