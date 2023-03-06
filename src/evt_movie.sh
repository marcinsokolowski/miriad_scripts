#!/bin/bash

export PATH=~/github/eda2tv/:~/github/eda2tv/source_finder/:$PATH

file=coinc_eda2_aavs2_TRANSIENT_CANDIDATEs.txt
if [[ -n "$1" && "$1" != "-" ]]; then
   file=$1
fi

is_list=0
if [[ -n "$2" && "$2" != "-" ]]; then
   is_list=$2
fi

datadir="../../"
if [[ -n "$3" && "$3" != "-" ]]; then
   datadir=$3
fi


mkdir -p track/
rm -f track/fits_list_tmp

echo "mkdir -p images/" > track/doit.sh
chmod +x track/doit.sh

cat $file | awk '{if($1!="#"){print $1;}}' > fits_list_tmp1
if [[ $is_list -gt 0 ]]; then
   echo "cp ${file} fits_list_tmp1"
   cp ${file} fits_list_tmp1
fi

for evt in `cat fits_list_tmp1`
do
   echo
   echo "Evt = $evt"
   fits=$evt
   if [[ $is_list -le 0 ]]; then
      fits=`grep $evt $file | awk '{print $6;}' | head -1`
      cand_reg=${fits%%.fits}_cand.reg
   
      if [[ ! -s track/${cand_reg} ]]; then
         grep $evt $file | awk 'BEGIN{print "global color=red width=5 font=\"times 10 normal\"";}{}' > track/${cand_reg} # was track/${evt}.reg
      fi
      # BEGIN{print "global color=green width=5 font=\"times 10 normal\"";}
   
      # exclude repetitions :
      line=`grep $evt $file | awk -v evt=$evt '{if($1==evt){print "circle "$11" "$12" 2 # color=red";}}'`
      echo "DEBUG : |grep \"$line\" track/${cand_reg}|"
      count=`grep "$line" track/${cand_reg} | wc -l`
      if [[ $count -le 0 ]]; then
         grep $evt $file | awk '{print "circle "$11" "$12" 2 # color=red";}' >> track/${cand_reg} # was track/${evt}.reg
      else
         echo "WARNING : line = |$line| already found $count times in track/${cand_reg} -> ignored"
      fi
   else
      echo "DEBUG : list file -> fits = evt = $fits"
   fi
   
   cd track/   
   echo "ln -sf ${datadir}/${fits} ${fits}"
   ln -sf ${datadir}/${fits} ${fits}    
   echo ${fits} >> fits_list_tmp
   cd ../
         
   # echo "ds9 -geometry 2250x1500 -scale zscale -zoom 2.5 ${datadir}/${fits} -regions load ${evt}.reg -saveimage images/${evt}.png -quit" >> track/doit.sh   
done

image_path=`which imagefits.py`
cd track/
sort -u fits_list_tmp > fits_list

echo "time python $image_path fits_list --outdir=images/ --ext=png --reg_postfix="_cand.reg" --fits_list=fits_list --out_image_type="png" --every_n_fits=1"
time python $image_path fits_list --outdir=images/ --ext=png --reg_postfix="_cand.reg" --fits_list=fits_list --out_image_type="png" --every_n_fits=1 

echo "time python $image_path fits_list --outdir=images/ --ext=png --reg_postfix="_cand.reg" --fits_list=fits_list --out_image_type="png" --every_n_fits=1" >> doit.sh
