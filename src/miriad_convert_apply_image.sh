#!/bin/bash

cal=cal
voltages=0

export PATH=~/github/hdf5_correlator/scripts:$PATH

if [[ $voltages -gt 0 ]]; then
   echo "miriad_convert_voltages.sh 1"
   miriad_convert_voltages.sh 1
else
   echo "miriad_convert_corr.sh 1"
   miriad_convert_corr.sh 1
fi   

for uvfits in `ls *.uvfits`
do
   uv=${uvfits%%.uvfits}
   
   echo "miriad_applycal_and_image.sh $uv $cal"
   miriad_applycal_and_image.sh $uv $cal
done

# I = (XX+YY)/2.00
echo "miriad_xxyy2i.sh"
miriad_xxyy2i.sh
