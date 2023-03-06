#!/bin/bash

uv=chan_126_20220917T07201850_XX.uv
if [[ -n "$1" && "$1" != "-" ]]; then
   uv=$1
fi
b=${uv%%.uv}

n_chan=32
if [[ -n "$2" && "$2" != "-" ]]; then
   n_chan=$2
fi

ch=1
while [[ $ch -le $n_chan ]]; 
do
   ch_str=`echo $ch | awk '{printf("%02d",$1);}'`
   outbase=${uv%%.uv}
   outmap=${outbase}_ch${ch_str}.map
   outbeam=${outbase}_ch${ch_str}.beam
   outfits=${outbase}_ch${ch_str}.fits

   echo "invert vis=${uv} map=${outmap} imsize=128,128 beam=${outbeam} robust=-0.5 options=double,mfs stokes=XX select='uvrange(0.0,100000)' line=chan,1,${ch}"      
   invert vis=${uv} map=${outmap} imsize=128,128 beam=${outbeam} robust=-0.5 options=double,mfs stokes=XX select='uvrange(0.0,100000)' line=chan,1,${ch}
   
   echo "fits op=xyout in=${outmap} out=${outfits}"
   fits op=xyout in=${outmap} out=${outfits}
   
   echo "calcfits_bg ${outfits} s 20 112 -R 10"
   calcfits_bg ${outfits} s 20 112 -R 10
   
   ch=$(($ch+1))   
done

# also create image of all channels for comparison :
outbeam=${b}_ch1-${n_chan}.beam
outmap=${b}_ch1-${n_chan}.map
outfits=${b}_ch1-${n_chan}.fits
outfits1=${outfits}

echo "invert vis=${uv} map=${outmap} imsize=128,128 beam=${outbeam} robust=-0.5 options=double,mfs stokes=XX select='uvrange(0.0,100000)' line=chan,${n_chan},1"
invert vis=${uv} map=${outmap} imsize=128,128 beam=${outbeam} robust=-0.5 options=double,mfs stokes=XX select='uvrange(0.0,100000)' line=chan,${n_chan},1

echo "fits op=xyout in=${outmap} out=${outfits}"
fits op=xyout in=${outmap} out=${outfits}

echo "calcfits_bg ${outfits} s 20 112 -R 10"
calcfits_bg ${outfits} s 20 112 -R 10

# all channels "normal" way
outbeam=${b}_AllChannels.beam
outmap=${b}_AllChannels.map
outfits=${b}_AllChannels.fits

echo "invert vis=${uv} map=${outmap} imsize=128,128 beam=${outbeam} robust=-0.5 options=double,mfs stokes=XX select='uvrange(0.0,100000)'"
invert vis=${uv} map=${outmap} imsize=128,128 beam=${outbeam} robust=-0.5 options=double,mfs stokes=XX select='uvrange(0.0,100000)'

echo "fits op=xyout in=${outmap} out=${outfits}"
fits op=xyout in=${outmap} out=${outfits}

echo "calcfits_bg ${outfits} s 20 112 -R 10"
calcfits_bg ${outfits} s 20 112 -R 10

# Compare both ways of calculating image of all 32 channels :
echo "calcfits_bg ${outfits1} = ${outfits}"
calcfits_bg ${outfits1} = ${outfits}

