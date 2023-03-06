#!/bin/bash

echo "Started at:"
date

iter=0

while [ 1 ];
do
   echo
   echo "---------------------------- Iteration $iter ----------------------------"
   date
   ls *14_XX.fits > fits_list_xx
   ls *14_YY.fits > fits_list_yy
   
   echo "miriad_diff_images_volt.sh fits_list_xx XX 1"
   miriad_diff_images_volt.sh fits_list_xx XX 1

   echo "miriad_diff_images_volt.sh fits_list_yy YY 1"
   miriad_diff_images_volt.sh fits_list_yy YY 1   
   
   echo "sleep 300"
   sleep 300
   
   iter=$(($iter+1))
done
