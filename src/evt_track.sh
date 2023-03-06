#!/bin/bash

# ds9 -geometry 2250x1500 -scale zscale -zoom ${zoom} $fits -regions load $reg -saveimage images/$png -quit

fits=chan_294_20200412T234048_I_diff.fits

mkdir -p images
for reg in `ls *.reg`
do
   png=${reg%%reg}png

   if [[ -s images/$png ]]; then
      echo "$reg already processed"
   else 
      echo "ds9 -geometry 2250x1500 -scale zscale -zoom 2.5 $fits -regions load $reg -saveimage images/$png -quit"
      ds9 -geometry 2250x1500 -scale zscale -zoom 2.5 $fits -regions load $reg -saveimage images/$png -quit
   fi
done

