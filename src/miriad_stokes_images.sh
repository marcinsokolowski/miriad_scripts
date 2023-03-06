#!/bin/bash

src=chan_204_20200410T221756
if [[ -n "$1" && "$1" != "-" ]]; then
   src="$1"
fi

h5file=EDA2_110_160MHz.h5
if [[ -n "$2" && "$2" != "-" ]]; then
   h5file="$2"
fi

station=aavs2
if [[ -n "$3" && "$3" != "-" ]]; then
   station=$3
fi

show=0
if [[ -n "$4" && "$4" != "-" ]]; then
   show=$4
fi

do_convert=1
if [[ -n "$5" && "$5" != "-" ]]; then
   do_convert=$5
fi

cal_uv=""
if [[ -n "$6" && "$6" != "-" ]]; then
   cal_uv=$6
fi

if [[ $do_convert -gt 0 ]]; then
   echo "fits op=uvin in=${src}.uvfits out=${src}.uv options=compress"
   fits op=uvin in=${src}.uvfits out=${src}.uv options=compress
else
   echo "WARNING : conversion is not required"
fi

if [[ -n "$cal_uv" ]]; then
   echo "gpcopy vis=${cal_uv} out=${src}.uv"
   gpcopy vis=${cal_uv} out=${src}.uv
else
   echo "WARNING : calibration will not be applied, no calibration solutions .uv file specified"
fi

# Form Instrumental XX,XY,YX,YY images in Real and Imaginary versions :
echo "uvcat vis=${src}.uv stokes=xx out=${src}_xx.uv"
uvcat vis=${src}.uv stokes=xx out=${src}_xx.uv

echo "uvcat vis=${src}.uv stokes=xy out=${src}_xy.uv"
uvcat vis=${src}.uv stokes=xy out=${src}_xy.uv

echo "uvcat vis=${src}.uv stokes=yx out=${src}_yx.uv"
uvcat vis=${src}.uv stokes=yx out=${src}_yx.uv

echo "uvcat vis=${src}.uv stokes=yy out=${src}_yy.uv"
uvcat vis=${src}.uv stokes=yy out=${src}_yy.uv

echo "invert vis=${src}_xx.uv map=${src}_xx.map imsize=180,180 beam=${src}_xx.beam robust=-0.5 options=double,mfs stokes=xx select='uvrange(0.0,100000)'"
invert vis=${src}_xx.uv map=${src}_xx.map imsize=180,180 beam=${src}_xx.beam robust=-0.5 options=double,mfs stokes=xx select='uvrange(0.0,100000)'

echo "invert vis=${src}_yy.uv map=${src}_yy.map imsize=180,180 beam=${src}_yy.beam robust=-0.5 options=double,mfs stokes=yy select='uvrange(0.0,100000)'"
invert vis=${src}_yy.uv map=${src}_yy.map imsize=180,180 beam=${src}_yy.beam robust=-0.5 options=double,mfs stokes=yy select='uvrange(0.0,100000)'

echo "invert vis=${src}_xy.uv map=${src}_xy.map imsize=180,180 beam=${src}_xy.beam robust=-0.5 options=double,mfs stokes=xy select='uvrange(0.0,100000)'"
invert vis=${src}_xy.uv map=${src}_xy.map imsize=180,180 beam=${src}_xy.beam robust=-0.5 options=double,mfs stokes=xy select='uvrange(0.0,100000)'

echo "invert vis=${src}_xy.uv map=${src}_ixy.map imsize=180,180 beam=${src}_ixy.beam robust=-0.5 options=double,mfs,imaginary stokes=xy select='uvrange(0.0,100000)'"
invert vis=${src}_xy.uv map=${src}_ixy.map imsize=180,180 beam=${src}_ixy.beam robust=-0.5 options=double,mfs,imaginary stokes=xy select='uvrange(0.0,100000)'

echo "invert vis=${src}_yx.uv map=${src}_yx.map imsize=180,180 beam=${src}_yx.beam robust=-0.5 options=double,mfs stokes=yx select='uvrange(0.0,100000)'"
invert vis=${src}_yx.uv map=${src}_yx.map imsize=180,180 beam=${src}_yx.beam robust=-0.5 options=double,mfs stokes=yx select='uvrange(0.0,100000)'

echo "invert vis=${src}_yx.uv map=${src}_iyx.map imsize=180,180 beam=${src}_iyx.beam robust=-0.5 options=double,mfs,imaginary stokes=yx select='uvrange(0.0,100000)'"
invert vis=${src}_yx.uv map=${src}_iyx.map imsize=180,180 beam=${src}_iyx.beam robust=-0.5 options=double,mfs,imaginary stokes=yx select='uvrange(0.0,100000)'

echo "fits op=xyout in=${src}_xx.map out=${src}_xx.fits"
fits op=xyout in=${src}_xx.map out=${src}_xx.fits

echo "fits op=xyout in=${src}_yy.map out=${src}_yy.fits"
fits op=xyout in=${src}_yy.map out=${src}_yy.fits

echo "fits op=xyout in=${src}_xy.map out=${src}_xy.fits"
fits op=xyout in=${src}_xy.map out=${src}_xy.fits

echo "fits op=xyout in=${src}_ixy.map out=${src}_ixy.fits"
fits op=xyout in=${src}_ixy.map out=${src}_ixy.fits

echo "fits op=xyout in=${src}_yx.map out=${src}_yx.fits"
fits op=xyout in=${src}_yx.map out=${src}_yx.fits

echo "fits op=xyout in=${src}_iyx.map out=${src}_iyx.fits"
fits op=xyout in=${src}_iyx.map out=${src}_iyx.fits

dt_ut=`echo $src | awk '{i1=index($1,"_");s=substr($1,i1+1);i2=index(s,"_");s2=substr(s,i2+1);gsub("T","_",s2);print s2;}'`
ux=`date2date -ut2ux=$dt_ut | awk '{print $3;}'`
gps=`ux2gps! $ux`

channel=`echo $src | awk '{i1=index($1,"_");s=substr($1,i1+1);i2=index(s,"_");s2=substr(s,1,i2-1);;print s2;}'`
freq_mhz=`echo $channel | awk '{printf("%.8f\n",$1*(400.00/512.00));}'`

echo "python ~/github/ska_pb/scripts/beam_correct_image_NEW.py --xx_file=${src}_xx.fits --yy_file=${src}_yy.fits --xy_file=${src}_xy.fits --xyi_file=${src}_ixy.fits --yx_file=${src}_yx.fits --yxi_file=${src}_iyx.fits --obsid=${gps} --freq_mhz=${freq_mhz} -b 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 --model=2016 --h5file=${h5file} --zenith_norm"
python ~/github/ska_pb/scripts/beam_correct_image_NEW.py --xx_file=${src}_xx.fits --yy_file=${src}_yy.fits --xy_file=${src}_xy.fits --xyi_file=${src}_ixy.fits --yx_file=${src}_yx.fits --yxi_file=${src}_iyx.fits --obsid=${gps} --freq_mhz=${freq_mhz} -b 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 --model=2016 --h5file=${h5file} --zenith_norm

# Stokes QUV normalised by Stokes I image :
echo "calcfits_bg V.fits / I.fits V_div_I.fits"
calcfits_bg V.fits / I.fits V_div_I.fits

echo "calcfits_bg Q.fits / I.fits Q_div_I.fits"
calcfits_bg Q.fits / I.fits Q_div_I.fits

echo "calcfits_bg U.fits / I.fits U_div_I.fits"
calcfits_bg U.fits / I.fits U_div_I.fits

echo "mv I.fits I_${station}.fits"
mv I.fits I_${station}.fits

echo "mv Q.fits Q_${station}.fits"
mv Q.fits Q_${station}.fits

echo "mv U.fits U_${station}.fits"
mv U.fits U_${station}.fits

echo "mv V.fits V_${station}.fits"
mv V.fits V_${station}.fits


if [[ $show -gt 0 ]]; then
   ds9_stokes! I_${station}.fits
   sleep 2   

   ds9_stokes! Q_${station}.fits
   sleep 2   

   ds9_stokes! U_${station}.fits
   sleep 2   

   ds9_stokes! V_${station}.fits
   sleep 2   

   ds9_stokes_ratio! Q_div_I.fits
   sleep 2

   ds9_stokes_ratio! U_div_I.fits
   sleep 2

   ds9_stokes_ratio! V_div_I.fits
   sleep 2
fi

