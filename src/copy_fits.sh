#!/bin/bash

remote_dir=eda2:/data/2020_04_10_ch204_corr/merged/
if [[ -n "$1" && "$1" != "-" ]]; then
   remote_dir=$1
fi

for i in `echo "0 1 2 3 4 5 6 7 8 9"`
do
   echo "rsync -avP ${remote_dir}/chan_*_????????T?????${i}_??.fits ."
   rsync -avP ${remote_dir}/chan_*_????????T?????${i}_??.fits .
   
   sleep 1
done
