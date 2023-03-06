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

fits op=uvin in=${src}.uvfits out=${src}.uv options=compress
puthd in=${src}.uv/jyperk value=2000.0
puthd in=${src}.uv/systemp value=200.0

uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv

# mfcal :
mfcal vis=${src}_XX.uv flux=50000 select='uvrange(0.00,10000)'
mfcal vis=${src}_YY.uv flux=50000 select='uvrange(0.00,10000)'

# selfcal :
reference_antenna=3
selfcal vis=${src}_XX.uv select='uvrange(0.005,10)' options=amplitude,noscale refant=${reference_antenna} flux=100000
selfcal vis=${src}_YY.uv select='uvrange(0.005,10)' options=amplitude,noscale refant=${reference_antenna} flux=100000

# save solutions :
stokes=XX
for stokes in `echo "XX YY"`
do
   gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_amp.txt
   gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_pha.txt yaxis=phase
   gain_extract_selfcal.sh aavs_gain_${stokes}_amp.txt >> "amp_${stokes}.txt"
   gain_extract_selfcal.sh aavs_gain_${stokes}_pha.txt >> "phase_${stokes}.txt"   
done

rm -f ${src}_XX.map ${src}_XX.beam
invert vis=${src}.uv map=${src}_XX.map imsize=${imsize},${imsize} beam=${src}_XX.beam robust=$robust options=double,mfs stokes=XX select='uvrange(0.0,100000)'
fits op=xyout in=${src}_XX.map out=${src}_XX.fits

rm -f ${src}_YY.map ${src}_YY.beam
invert vis=${src}.uv map=${src}_YY.map imsize=${imsize},${imsize} beam=${src}_YY.beam robust=$robust options=double,mfs stokes=YY select='uvrange(0.0,100000)'
fits op=xyout in=${src}_YY.map out=${src}_YY.fits

utc=`fitshdr ${src}_XX.fits  | grep DATE-OBS | awk '{gsub("''","",$0);dtm=substr($2,2,19);gsub("T","_",dtm);gsub("-","",dtm);gsub(":","",dtm);print dtm;}'`
echo "utc = $utc"

ux=`date2date -ut2ux=${utc} | awk '{print $3;}'`
lst=`ux2sid $ux | awk '{print $8}'`
echo "ux = $ux -> lst = $lst"

date
echo "fixCoordHdr.py ${src}_XX.fits ${lst}"
time fixCoordHdr.py ${src}_XX.fits ${lst}

echo "fixCoordHdr.py ${src}_YY.fits ${lst}"
time fixCoordHdr.py ${src}_YY.fits ${lst}
date

