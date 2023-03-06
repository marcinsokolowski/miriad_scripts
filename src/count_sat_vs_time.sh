#!/bin/bash

inttime=0 # or 2 
if [[ -n "$1" && "$1" != "-" ]]; then
   inttime=$1
fi

postfix=".0000.txt"
if [[ -n "$2" && "$2" != "-" ]]; then
   postfix=$2
fi

min_elev=25
if [[ -n "$3" && "$3" != "-" ]]; then
   min_elev=$3
fi


echo "find . -name \"1?????????${postfix}\" | awk '{print substr($1,3);}' | sort > uxfile.list"
find . -name "1?????????${postfix}" | awk '{print substr($1,3);}' | sort > uxfile.list

outfile="satcount_vs_time_inttime${inttime}sec.txt"

echo "rm -f ${outfile}"
rm -f ${outfile}


for uxfile in `cat uxfile.list`
do
    uxtime=`echo $uxfile | cut -b 1-10`
    cnt=`cat $uxfile | wc -l`
    echo "TEST : $uxfile $cnt"
    
    ux=${uxtime}
    ux_min=`echo $uxtime | awk -v inttime=${inttime} '{printf("%.2f\n",($1-inttime/2+0.0001));}'`
    ux_max=`echo $uxtime | awk -v inttime=${inttime} '{printf("%.2f\n",($1+inttime/2+0.0001));}'`       
    
    echo "SELECTING : $uxfile -> $uxtime -> $ux_min <= $ux <= $ux_max"
    echo "Using files :"
    echo "----"
    rm -f uxtmp.txt
    cont=1
    while [[ $cont -gt 0 ]]; 
    do
       ls -al ${ux}${postfix}
       echo "cat ${ux}${postfix} | awk '{if($1!=\"#\"){print $0;}}' >> uxtmp.txt"
       cat ${ux}${postfix} | awk '{if($1!="#"){print $0;}}' >> uxtmp.txt
       
       ux=$(($ux+1))
       
       cont=`echo "$ux_min $ux $ux_max" | awk '{if($1<=$2 && $2<=$3){print 1;}else{print 0;}}'`
    done      
    echo "----"
    
    # sort -u is unique sort required to make it counting only once each satellite !
    satcount=`cat uxtmp.txt | awk -v min_elev=${min_elev} -v count=0 '{if($1!="#" && $5>min_elev){print $8;}}' | sort -u | wc -l`
    
    echo "$uxtime $satcount" >> $outfile
    
    echo "$uxtime $satcount"
#    exit
done
