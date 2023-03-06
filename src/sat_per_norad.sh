#!/bin/bash


for norad in `cat sat.list`
do
   count=`grep $norad coinc_eda2_aavs2.txt | wc -l`
   
   echo "$norad $count"
done


