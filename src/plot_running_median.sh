#!/bin/bash

file=B0950+08.txt
if [[ -n "$1" && "$1" != "-" ]]; then
   file=$1
fi

root_options=""

b=${file%%.txt}

echo "running_median ${b}.txt ${b}_running_median30 -n 30"
running_median ${b}.txt ${b}_running_median30 -n 30

if [[ -d eda2 ]]; then
   cd eda2/
   echo "running_median ${b}.txt ${b}_running_median30 -n 30"
   running_median ${b}.txt ${b}_running_median30 -n 30
   cd ..
fi

echo "ls aavs2/${b}_running_median30_median_subtr.txt eda2/${b}_running_median30_median_subtr.txt > running_median.list"
ls aavs2/${b}_running_median30_median_subtr.txt eda2/${b}_running_median30_median_subtr.txt > running_median.list

root ${root_options} "plotNfilesFlux_vs_time_scaling.C(\"running_median.list\")"
