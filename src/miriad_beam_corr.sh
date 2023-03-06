#!/bin/bash

fits=chan_204_20200411T040000_XX.fits # or date/time in UTC format 20200723_030700
if [[ -n "$1" && "$1" != "-" ]]; then
   fits=$1
fi

freq_mhz=160.00
if [[ -n "$2" && "$2" != "-" ]]; then
   freq_mhz=$2
fi

station_name="EDA"
if [[ -n "$3" && "$3" != "-" ]]; then
   station_name=$3
fi

nf=`echo $fits  | awk -F "_" '{print NF;}'`

echo "DEBUG : nf=$nf"

if [[ $nf -gt 2 ]]; then
   utc=`echo $fits | awk -F "_" '{gsub("T","_",$3);print $3;}'`
else
   utc=$fits
fi   

echo "date2date -ut2ux=${utc}"
ux=`date2date -ut2ux=${utc} | awk '{print $3;}'`

echo "print_sun $ux -c -A"
print_sun $ux -c -A 

line=`print_sun $ux -c -A | grep AZIM`

azim_deg=`echo $line | awk '{print $4;}'`
elev_deg=`echo $line | awk '{print $6;}'`

echo "python ~/github/station_beam/python/fits_beam.py --az_deg=${azim_deg} --el_deg=${elev_deg} --freq_mhz=${freq_mhz} --station_name=${station_name}"
python ~/github/station_beam/python/fits_beam.py --az_deg=${azim_deg} --el_deg=${elev_deg} --freq_mhz=${freq_mhz} --station_name=${station_name}

