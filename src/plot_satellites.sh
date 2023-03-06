#!/bin/bash


listfile=sat.list

mkdir -p sat/images/

for sattmp in `cat $listfile`
do
   # this is line to change "/" to "s" as "/" in the file name will not work well with linux paths etc ...
   # sat=`echo $sattmp | awk '{gsub("/","s");gsub("[","N");gsub("]","N");print $0;}'`
   # sat=${sattmp}
   sat=`echo $sattmp | sed 's/\//s/g' | sed 's/\[/S/g' | sed 's/\]/S/g'`
   
#   grep ${sattmp} coinc_eda2_aavs2_SATELLITES.txt | awk '{if($1!="#"){print $2" "$3;}}' > sat/${sat}.txt
   awk -v sat=${sat} '{if($25==sat){print $0;}}' coinc_eda2_aavs2_SATELLITES.txt | awk '{if($1!="#"){print $2" "$3" "$25;}}' > sat/${sat}.txt
   
   if [[ -s  sat/${sat}.txt ]]; then
      cd sat/   
      root -b -q "trackplot_radec.C(\"${sat}.txt\")"
      cd ../
   else
      echo "ERROR : file sat/${sat}.txt not created !?"
   fi
done

awk '{if($1!="#"){print $2" "$3;}}' coinc_eda2_aavs2_SATELLITES.txt > sat/all.txt

cd sat/
root -b -q "trackplot_radec.C(\"all.txt\")"
wc *.txt | sort -n | awk '{if($1>=10){print $0;}}' > satellite_stat.txt
cd ../

cd sat/images/
gthumb -n *.png &
