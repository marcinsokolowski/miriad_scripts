#!/bin/bash

# Script does the following
# combine uvfits
# phase centre
# find the threshold to set flagging to remove bad antennas
# mfcal
# image and show with kvis

cd /media/ramdisk/AAVS_sun_marcin/

rm -rf *.mir
rm -rf *.mir_phc
rm -rf *.imap 

for fname in $(ls *.uvfits | sed -e 's/\.uvfits$//')
do 
    fits "in=${fname}.uvfits" "op=uvin" "out=${fname}.mir" 
done
uvcat  "vis=chan_204*.mir" "out=cat_chan_204.mir" 
uvaver "vis=cat_chan_204.mir" "out=aver_cat_chan_204.mir" "interval=1000" #"stokes=xx"

filename="aver_cat_chan_204.mir"

timemir=$(uvlist "vis=${filename}" "options=variables" | grep "Header" | sed 's/.* //')
RA=$(planets "source=sun" epoch=${timemir} | grep "RA"| sed 's/.* //' | sed -e "s/:/,/g")
Dec=$(planets "source=sun" epoch=${timemir} | grep "DEC"| sed 's/.* //' | sed -e "s/:/,/g")
echo $RA
echo $Dec
uvedit "vis=${filename}" "ra=${RA}" "dec=${Dec}" "out=${filename}_phc"
uvflux "vis=${filename}" "select=-auto" "stokes=xx" "options=nocal"

mean_visi=$(uvflux "vis=aver_cat_chan_204.mir" "select=-auto" "stokes=xx" "options=nocal" | grep "eda2cal"| awk '{print $7}')
mean_visi_dec=$(printf '%.2f' $mean_visi)
rms_visi=$(uvflux "vis=aver_cat_chan_204.mir" "select=-auto" "stokes=xx" "options=nocal" | grep "eda2cal"| awk '{print $8}')
rms_visi_dec=$(printf '%.2f' $rms_visi)
flaglim=$(echo "$mean_visi_dec-$rms_visi_dec" | bc)
uvflag "vis=${filename}_phc" "select=amplitude(0, $flaglim)"  "flagval=flag" 

mfcal "vis=${filename}_phc" "select=uvrange(0.001, 1.0)" "flux=56200" "stokes=xx"

puthd  "in=${filename}_phc/pbtype" "value = gaus(162000)" 
invert "vis=${filename}_phc" "map=${filename}_phc.imap" "imsize=3,3,beam" "cell=10,10,res" "stokes=xx" #"options=nocal, nopass"

kvis *.imap

 

