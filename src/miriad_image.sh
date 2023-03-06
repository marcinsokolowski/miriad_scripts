#!/bin/bash

src=chan_204_20191228T052443
if [[ -n "$1" && "$1" != "-" ]]; then
  src=$1
fi

imsize=180 # 128 or 256 
if [[ -n "$2" && "$2" != "-" ]]; then
   imsize=$2
fi

robust=-0.5
if [[ -n "$3" && "$3" != "-" ]]; then
   robust=$3
fi


rm -f ${src}_XX.map ${src}_XX.beam
echo "invert vis=${src}_XX.uv map=${src}_XX.map imsize=${imsize},${imsize} beam=${src}_XX.beam robust=$robust options=double,mfs stokes=XX select='uvrange(0.0,100000)'"
invert vis=${src}_XX.uv map=${src}_XX.map imsize=${imsize},${imsize} beam=${src}_XX.beam robust=$robust options=double,mfs stokes=XX select='uvrange(0.0,100000)'
echo "fits op=xyout in=${src}_XX.map out=${src}_XX.fits"
fits op=xyout in=${src}_XX.map out=${src}_XX.fits

rm -f ${src}_YY.map ${src}_YY.beam
echo "invert vis=${src}_YY.uv map=${src}_YY.map imsize=${imsize},${imsize} beam=${src}_YY.beam robust=$robust options=double,mfs stokes=YY select='uvrange(0.0,100000)'"
invert vis=${src}_YY.uv map=${src}_YY.map imsize=${imsize},${imsize} beam=${src}_YY.beam robust=$robust options=double,mfs stokes=YY select='uvrange(0.0,100000)'
echo "fits op=xyout in=${src}_YY.map out=${src}_YY.fits"
fits op=xyout in=${src}_YY.map out=${src}_YY.fits

utc=`fitshdr ${src}_XX.fits  | grep DATE-OBS | awk '{gsub("''","",$0);dtm=substr($2,2,19);gsub("T","_",dtm);gsub("-","",dtm);gsub(":","",dtm);print dtm;}'`
echo "utc = $utc"

ux=`date2date -ut2ux=${utc} | awk '{print $3;}'`
lst=`ux2sid $ux | awk '{print $8}'`
echo "ux = $ux -> lst = $lst"

path=`which fixCoordHdr.py`

echo "python $path ${src}_XX.fits ${lst}"
python $path ${src}_XX.fits ${lst}

echo "python $path ${src}_YY.fits ${lst}"
python $path ${src}_YY.fits ${lst}


