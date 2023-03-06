#!/bin/bash

# showing coincindence event in ds9 (from both stations)

evtidx=0
if [[ -n "$1" && "$1" != "-" ]]; then
   evtidx=$1
fi

logfile=coinc_eda2_aavs2.txt
if [[ -n "$2" && "$2" != "-" ]]; then
   logfile=$2
fi

auto_copy=1
if [[ -n "$3" && "$3" != "-" ]]; then
   auto_copy=43
fi

# line=`awk -v idx=0 -v evtidx=$evtidx '{if($1!="#"){if(idx==evtidx){print $0;}idx+=1;}}' ${logfile}`
line=`awk -v idx=0 -v evtidx=$evtidx '{if($1!="#"){if(substr(evtidx,1,3)=="EVT"){if($1==evtidx){print $0;}}else{if(idx==evtidx){print $0;}}idx+=1;}}' ${logfile}`

# ANG_DIST[deg] DELAY[sec] FITSFILE_highfreq RA_high[deg] DEC_high[deg] X_high Y_high UXTIME_high FITSFILE_lowfreq RA_low[deg] DEC_low[deg] X_low Y_low UXTIME_low DIST_sun[deg]
# 0.8772 0.000 chan_294_20200530T135006_I_diff.fits 215.669640 5.852438 126.0 193.0 1590846606.0000 chan_204_20200530T135006_I_diff.fits 216.547358 5.937475 87.0 131.0 1590846606.0000 138.2
fits_high=`echo $line | awk '{print $6;}'`
fits_low=`echo $line | awk '{print $14;}'`

reg_high=../${fits_high%%.fits}_cand.reg
reg_low=../${fits_low%%.fits}_cand.reg

if [[ ! -s ${reg_high} ]]; then
   reg_high=${fits_high%%.fits}_high.reg
fi

if [[ ! -s ${reg_low} ]]; then
   reg_low=${fits_low%%.fits}_low.reg
fi

fits_high=${fits_high%%_diff.fits}.fits
fits_low=${fits_low%%_diff.fits}.fits

if [[ ! -s ../${fits_high} && $auto_copy -gt 0 ]]; then
   echo "get_remote_file.sh ${fits_high} - aavs2"
   get_remote_file.sh ${fits_high} - aavs2
fi

echo "ds9 -geometry 2000x1200 -scale zscale ../${fits_high} -regions load ${reg_high} -zoom to fit  -grid yes -grid type publication -grid skyformat degrees -grid labels def1 no  &"
ds9 -geometry 2000x1200 -scale zscale ../${fits_high} -regions load ${reg_high} -zoom to fit  -grid yes -grid type publication -grid skyformat degrees -grid labels def1 no  &

if [[ ! -s ../low/${fits_low} && $auto_copy -gt 0 ]]; then
   echo "get_remote_file.sh ${fits_low} - eda2"
   get_remote_file.sh ${fits_low} - eda2
fi

echo "ds9 -geometry 2000x1200  -scale zscale ../low/${fits_low} -regions load ${reg_low} -zoom to fit  -grid yes -grid type publication -grid skyformat degrees -grid labels def1 no  &"
ds9 -geometry 2000x1200 -scale zscale ../low/${fits_low} -regions load ${reg_low} -zoom to fit  -grid yes -grid type publication -grid skyformat degrees -grid labels def1 no  &




