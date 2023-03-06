#!/bin/bash

radius=10
if [[ -n "$1" && "$1" != "-" ]]; then
   radius=$1
fi

outdir=noise_maps_radius${radius}
mkdir -p ${outdir}

force=0

for fits in `cat fits_list_I_diff`
do
   noisemap=${fits%%.fits}_noisemap
      
   if [[ ! -s noise_maps/${noisemap} ]]; then
      echo "noise_mapper $fits -r $radius -i -o ${outdir}/${noisemap}"
      noise_mapper $fits -r $radius -i -o ${outdir}/${noisemap}
   else
      echo "INFO : $fits already processed"
   fi
done
   