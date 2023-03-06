#!/bin/bash

aavs2_dir="./"

eda2_dir=/media/msok/0754e982-0adb-4e33-80cc-f81dda1580c8/eda2/data/2020_05_30_ch204_corr/merged
if [[ -n "$1" && "$1" != "-" ]]; then
   eda2_dir="$1"
fi

min_elev=25
if [[ -n "$2" && "$2" != "-" ]]; then
   min_elev=$2
fi

outdir="coinc/"
if [[ -n "$3" && "$3" != "-" ]]; then
   outdir="$3"
fi

coinc_options="" # --max_delay_sec as per : python /home/msok/bighorns/software/analysis/scripts/python/dispersion2.py 1000 230 160
if [[ -n "$4" && "$4" != "-" ]]; then
   coinc_options="$4"
fi


plot_satellites=1
if [[ -n "$5" && "$5" != "-" ]]; then
   plot_satellites=$5
fi

inttime=2

cd ${aavs2_dir}
# ls *_I_diff_cand.txt > cand_list_aavs2
echo "find . -maxdepth 1 -name \"chan*_I_diff_cand.txt\" | awk '{gsub(\"./\",\"\");print \$0;}' | sort > cand_list_aavs2"
find . -maxdepth 1 -name "chan*_I_diff_cand.txt" | awk '{gsub("./","");print $0;}' | sort > cand_list_aavs2

# ls ${eda2_dir}/*_I_diff_cand.txt > cand_list_eda2
echo "find ${eda2_dir}/ -maxdepth 1 -name \"chan*_I_diff_cand.txt\" | sort > cand_list_eda2"
find ${eda2_dir}/ -maxdepth 1 -name "chan*_I_diff_cand.txt" | sort > cand_list_eda2

cd ${aavs2_dir}
path=`which eda2_aavs2_concidence.py`

mkdir -p images/

# run coincidence :
# Coinc + TLE :
pwd
date
if [[ ! -s mro.qth ]]; then
   echo ".qth config file does not exist -> copying"
      
   echo "cp $EDA2TV_PATH/source_finder/config/mro.qth ."
   cp $EDA2TV_PATH/source_finder/config/mro.qth .
else
   echo "INFO : mro.qth file already exists"
fi
   
if [[ ! -d TLE/ ]]; then
   echo "TLE directory does not exist -> preparing one now ..."
      
   mkdir -p TLE
   for dt in `ls *_I_diff_cand.txt | awk -F "_" '{print substr($3,1,8);}' | sort -u`
   do
      mkdir TLE/${dt}
         
      echo "cp /home/msok/bighorns/data/TLE/${dt}/satelitesdb.tle TLE/${dt}/"
      cp /home/msok/bighorns/data/TLE/${dt}/satelitesdb.tle TLE/${dt}/
   done
else
   echo "INFO : TLE/ directory already exists"
fi

echo "python $path --list_high_freq=cand_list_aavs2 --list_low_freq=cand_list_eda2 --min_elevation=${min_elev} --outdir=${outdir} ${coinc_options}"
python $path --list_high_freq=cand_list_aavs2 --list_low_freq=cand_list_eda2 --min_elevation=${min_elev} --outdir=${outdir} ${coinc_options}

cd ${outdir}
mkdir -p images/

echo "sort -k 3.1 -n coinc_eda2_aavs2.txt > coinc_eda2_aavs2_DEC-SORTED.txt"
sort -k 3.1 -n coinc_eda2_aavs2.txt > coinc_eda2_aavs2_DEC-SORTED.txt

echo "grep TRANSIENT_CANDIDATE coinc_eda2_aavs2.txt > coinc_eda2_aavs2_TRANSIENT_CANDIDATEs.txt"
grep TRANSIENT_CANDIDATE coinc_eda2_aavs2.txt > coinc_eda2_aavs2_TRANSIENT_CANDIDATEs.txt

echo "sort -k 3.1 coinc_eda2_aavs2_TRANSIENT_CANDIDATEs.txt > coinc_eda2_aavs2_TRANSIENT_CANDIDATEs_DEC-SORTED.txt"
sort -k 3.1 coinc_eda2_aavs2_TRANSIENT_CANDIDATEs.txt > coinc_eda2_aavs2_TRANSIENT_CANDIDATEs_DEC-SORTED.txt

echo "grep SATELLITE coinc_eda2_aavs2.txt > coinc_eda2_aavs2_SATELLITES.txt"
grep SATELLITE coinc_eda2_aavs2.txt > coinc_eda2_aavs2_SATELLITES.txt

awk '{if($1!="#"){print $2" "$3;}}' coinc_eda2_aavs2_SATELLITES.txt > coinc_eda2_aavs2_SATELLITES_RADEC.txt
root -b -q "transientplot_radec.C(\"coinc_eda2_aavs2_SATELLITES_RADEC.txt\")"

echo "grep SOURCE coinc_eda2_aavs2.txt > coinc_eda2_aavs2_SOURCES.txt"
grep SOURCE coinc_eda2_aavs2.txt > coinc_eda2_aavs2_SOURCES.txt

awk '{if($1!="#"){print $2" "$3;}}' coinc_eda2_aavs2_SOURCES.txt > coinc_eda2_aavs2_SOURCES_RADEC.txt
root -b -q "transientplot_radec.C(\"coinc_eda2_aavs2_SOURCES_RADEC.txt\")"

echo "grep RFI coinc_eda2_aavs2.txt > coinc_eda2_aavs2_RFI.txt"
grep RFI coinc_eda2_aavs2.txt > coinc_eda2_aavs2_RFI.txt

awk '{if($1!="#"){print $2" "$3;}}' coinc_eda2_aavs2_RFI.txt > coinc_eda2_aavs2_RFI_RADEC.txt
root -b -q "transientplot_radec.C(\"coinc_eda2_aavs2_RFI_RADEC.txt\")"


# AZIM,ELEV :
# 23,24 

awk '{if($1!="#"){print $23" "$24;}}' coinc_eda2_aavs2.txt > coinc_eda2_aavs2_AZALT.txt
root -b -q "transientplot_azelev.C(\"coinc_eda2_aavs2_AZALT.txt\")"

grep SATELLITE coinc_eda2_aavs2.txt | awk '{if($1!="#"){print $23" "$24;}}' > coinc_eda2_aavs2_SATELLITES_AZALT.txt
root -b -q "transientplot_azelev.C(\"coinc_eda2_aavs2_SATELLITES_AZALT.txt\")"

grep PLANE coinc_eda2_aavs2.txt | awk '{if($1!="#"){print $23" "$24;}}' > coinc_eda2_aavs2_PLANES_AZALT.txt
root -b -q "transientplot_azelev.C(\"coinc_eda2_aavs2_PLANES_AZALT.txt\")"

grep SOURCE coinc_eda2_aavs2.txt | awk '{if($1!="#"){print $23" "$24;}}' > coinc_eda2_aavs2_SOURCES_AZALT.txt
root -b -q "transientplot_azelev.C(\"coinc_eda2_aavs2_SOURCES_AZALT.txt\")"

grep RFI coinc_eda2_aavs2.txt | awk '{if($1!="#"){print $23" "$24;}}' > coinc_eda2_aavs2_RFI_AZALT.txt
root -b -q "transientplot_azelev.C(\"coinc_eda2_aavs2_RFI_AZALT.txt\")"

grep TRANSIENT_CANDIDATE coinc_eda2_aavs2.txt | awk '{if($1!="#"){print $23" "$24;}}' > coinc_eda2_aavs2_CANDIDATES_AZALT.txt
root -b -q "transientplot_azelev.C(\"coinc_eda2_aavs2_CANDIDATES_AZALT.txt\")"

# sorted by elevation
sort -k 24.1 -n coinc_eda2_aavs2.txt > coinc_eda2_aavs2_SORTED_BY_ELEV.txt

# 25,26 :
echo "# NAME RA   DEC  FITS_high FITS_low" > coinc_eda2_aavs2_RADEC_FITS.txt
awk '{print $1" "$2" "$3" "$6" "$14}' coinc_eda2_aavs2.txt >> coinc_eda2_aavs2_RADEC_FITS.txt

awk '{if($1!="#"){print $2" "$3;}}' coinc_eda2_aavs2.txt > coinc_eda2_aavs2_RADEC_PLOT.txt
root -b -q "transientplot_radec.C(\"coinc_eda2_aavs2_RADEC_PLOT.txt\")"

awk '{if($1!="#"){print $2" "$3;}}' coinc_eda2_aavs2_TRANSIENT_CANDIDATEs_DEC-SORTED.txt > coinc_eda2_aavs2_TRANSIENT_CANDIDATEs_DEC-SORTED_XY.txt
root -b -q "transientplot_radec.C(\"coinc_eda2_aavs2_TRANSIENT_CANDIDATEs_DEC-SORTED_XY.txt\")"

awk '{if($1!="#"){print $2" "$3;}}' coinc_eda2_aavs2_TRANSIENT_CANDIDATEs.txt > coinc_eda2_aavs2_TRANSIENT_CANDIDATEs_RADEC.txt
root -b -q "transientplot_radec.C(\"coinc_eda2_aavs2_TRANSIENT_CANDIDATEs_RADEC.txt\")"

awk '{if($1!="#"){print $2" "$3;}}' coinc_eda2_aavs2_all_coinc.txt > coinc_eda2_aavs2_all_coinc_RADEC.txt
root -b -q "transientplot_radec.C(\"coinc_eda2_aavs2_all_coinc_RADEC.txt\")"

awk '{if($1!="#"){print $23" "$24;}}' coinc_eda2_aavs2_all_coinc.txt > coinc_eda2_aavs2_all_coinc_AZALT.txt
root -b -q "transientplot_azelev.C(\"coinc_eda2_aavs2_all_coinc_AZALT.txt\")"

# list unique satellites :
awk '{print $25}' coinc_eda2_aavs2_SATELLITES.txt | sort -u > sat.list
if [[ $plot_satellites -gt 0 ]]; then
   echo "plot_satellites.sh"
   sleep 5
   plot_satellites.sh 
fi

# Final statistics :
sat_count=`grep SATELLITE coinc_eda2_aavs2.txt | wc -l`
plane_count=`grep PLANE coinc_eda2_aavs2.txt | wc -l`
source_count=`grep SOURCE coinc_eda2_aavs2.txt | wc -l`
transient_count=`grep TRANSIENT_CANDIDATE coinc_eda2_aavs2.txt | wc -l`
skipped_images=`cat flagged_images.txt | sort -u | wc -l`
skipped_hours=`echo $skipped_images | awk -v inttime=${inttime} '{printf("%.4f\n",($1*inttime/3600));}'`

echo
echo "-----------------------------------------------------"
echo "FINAL STATISTICS :"
echo "-----------------------------------------------------"
echo "Transient candidates = $transient_count"
echo "Astro sources        = $source_count"
echo "Planes               = $plane_count"
echo "Satellites           = $sat_count"
echo 
echo "Skipped images = $skipped_images -> Skipped time = $skipped_hours [hours]"
echo "-----------------------------------------------------"

