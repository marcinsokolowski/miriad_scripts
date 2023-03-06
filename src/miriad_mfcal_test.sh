#!/bin/bash

reference_antenna=3
channel=204

~/github/hdf5_correlator//scripts/hdf5_to_uvfits_all.sh -c -l -i 2.00 -n 1 -d "./" -N -a 1 -f 204 -L new_hdf5_list.txt -S 0 -s EDA2 -I 1 > out 2>&1 

for uvfitsfile in `ls -tr chan_${channel}_*.uvfits` ; 
do     
   src=`basename $uvfitsfile .uvfits`;     
   echo "Processing $uvfitsfile to ${src}.uv";
   rm -rf ${src}.uv ${src}_XX.uv ${src}_YY.uv;
   fits op=uvin in="$uvfitsfile" out="${src}.uv" options=compress;
   puthd in=${src}.uv/jyperk value=1310.0;     
   puthd in=${src}.uv/systemp value=200.0;       
   uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv;     
   uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv; 

   for stokes in `echo "XX YY"`
   do
      mfcal vis=${src}_${stokes}.uv flux=51000,0.15,1.6 select="uvrange(0.005,10)" refant=${reference_antenna}
      gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_pha.txt yaxis=phase
   done
done

echo "###########################################################"

head aavs_gain_XX_pha.txt
# vs.
head ../Norm*/chan_204_selfcal_pha_XX.txt 

echo "###########################################################"

head aavs_gain_YY_pha.txt
# vs.
head ../Norm*/chan_204_selfcal_pha_YY.txt 

echo "###########################################################"
