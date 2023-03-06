#!/bin/bash

n_iter=10000000
if [[ -n "$1" && "$1" != "-" ]]; then
   n_iter=$1
fi

dt_eda2=2020_04_10_ch204_corr
if [[ -n "$2" && "$2" != "-" ]]; then
   dt_eda2=$2
fi

dt_aavs2=2020_04_10_ch204_corr
if [[ -n "$3" && "$3" != "-" ]]; then
   dt_aavs2=$3
fi
aavs2_name=`echo $dt_aavs2 | cut -b 12-`

use_nimbus=0
if [[ -n "$4" && "$4" != "-" ]]; then
   use_nimbus=$4
fi

base_data_dir=/media/msok/0754e982-0adb-4e33-80cc-f81dda1580c8/
if [[ -n "$5" && "$5" != "-" ]]; then
   base_data_dir=$5
fi


echo "#############################################################################"
echo "PARAMETERS :"
echo "#############################################################################"
echo "n_iter   = $n_iter"
echo "dt_eda2  = $dt_eda2"
echo "dt_aavs2 = $dt_aavs2"
echo "use_nimbus = $use_nimbus"
echo "base_data_dir = $base_data_dir"
echo "#############################################################################"


# dt_eda2=2020_07_07_ch204_corr
# dt_eda2=${date_name}

# dt_aavs2=2020_07_07_ch294_corr
# dt_aavs2=${date_name}

# name=20200410_eda2-ch204_aavs2-ch204
name=${dt_eda2}_aavs2${aavs2_name}_eda2_aavs2

data_dir=${base_data_dir}/analysis/
# eda2_dir=${data_dir}/${name}/eda2/${dt_eda2}/merged
# aavs2_dir=${data_dir}/${name}/aavs2/${dt_aavs2}/merged
eda2_dir=${base_data_dir}/eda2/data/${dt_eda2}/merged
aavs2_dir=${base_data_dir}/aavs2/data/${dt_aavs2}/merged

mkdir -p ${eda2_dir}
mkdir -p ${aavs2_dir}

mkdir -p ${data_dir}/${name}/eda2/${dt_eda2}/
mkdir -p ${data_dir}/${name}/aavs2/${dt_aavs2}/

if [[ -d ${base_data_dir}/eda2/data/${dt_eda2}/merged ]]; then
   echo "DEBUG : directory with EDA2 data exists ${base_data_dir}/eda2/data/${dt_eda2}/merged -> creating symbolic link"
   echo "ln -sf ${base_data_dir}/eda2/data/${dt_eda2}/merged ${data_dir}/${name}/eda2/${dt_eda2}/"
   ln -sf ${base_data_dir}/eda2/data/${dt_eda2}/merged ${data_dir}/${name}/eda2/${dt_eda2}/
fi

if [[ -d ${base_data_dir}/aavs2/data/${dt_aavs2}/merged ]]; then
   echo "DEBUG : directory with AAVS2 data exists ${base_data_dir}/aavs2/data/${dt_aavs2}/merged -> creating symbolic link"
   echo "ln -sf ${base_data_dir}/aavs2/data/${dt_aavs2}/merged  ${data_dir}/${name}/aavs2/${dt_aavs2}/"   
   ln -sf ${base_data_dir}/aavs2/data/${dt_aavs2}/merged  ${data_dir}/${name}/aavs2/${dt_aavs2}/
fi   

stations="eda2 aavs2"

do_analysis=1
copy_fits=0

root_options="-l" # or -b -q -l 

# create symbolic links :
# cd ${data_dir}/eda2/data/${dt_eda2}/merged/
# ln -sf ${data_dir}/eda2/data/${dt_eda2}/merged eda2
# ln -sf ${data_dir}/aavs2/data/${dt_aavs2}/merged aavs2
cd ${eda2_dir}
pwd
echo "rm -f eda2"
rm -f eda2
echo "ln -sf ${eda2_dir} eda2"
ln -sf ${eda2_dir} eda2

echo "rm -f aavs2"
rm -f aavs2
ls -al aavs2
echo "ln -sf ${aavs2_dir} aavs2"
ln -sf ${aavs2_dir} aavs2
ls -al aavs2

# sleep 5

# cd ${data_dir}/aavs2/data/${dt_aavs2}/merged/
# ln -sf ${data_dir}/eda2/data/${dt_eda2}/merged eda2
# ln -sf ${data_dir}/aavs2/data/${dt_aavs2}/merged aavs2
echo
cd ${aavs2_dir}
pwd
ls -al aavs2 eda2

echo "rm -f eda2 aavs2"
rm -f eda2 aavs2

echo "ln -sf ${eda2_dir} eda2"
ln -sf ${eda2_dir} eda2

echo "ln -sf ${aavs2_dir} aavs2"
ln -sf ${aavs2_dir} aavs2

# DEBUG - when link was not working !
# exit

# ln -sf eda2 low
# ln -sf aavs2 high


i=0
while [[ $i -lt $n_iter ]];
do
   for station in `echo $stations`
   do
      station_comp=${station}
      if [[ $use_nimbus -gt 0 ]]; then
         if [[ $station == "eda2" ]]; then
            station_comp="aavs@nimbus4"
         fi
         if [[ $station == "aavs2" ]]; then
            station_comp="aavs@nimbus5"
         fi
      fi
      
      full_dir=${data_dir}/${station}
      if [[ $station == "eda2" ]]; then
         full_dir=${eda2_dir}
#         mkdir -p ${full_dir}
# where to copy data from :
         dt_name=${dt_eda2}
      else
         full_dir=${aavs2_dir}
#         mkdir -p ${full_dir}
# where to copy data from :
         dt_name=${dt_aavs2}
      fi
      
      cd ${full_dir}
      pwd
      sleep 2
      
      dir_count=`ssh ${station} "ls -d /data/${dt_name}/merged/" 2>&1 | grep -v "cannot" | wc -l`
      
      if [[ $dir_count -gt 0 ]]; then      
         echo "rsync -avP --exclude '_cand.txt' ${station_comp}:/data/${dt_name}/merged/{s,B,2C,O}*.txt ."
         rsync -avP --exclude '_cand.txt' ${station_comp}:/data/${dt_name}/merged/{s,B,2C,O}*.txt .
      
         for i in `echo "0 1 2 3 4 5 6 7 8 9"`
         do
            echo "rsync -avP ${station_comp}:/data/${dt_name}/merged/*${i}_I_*_cand.* ."
            rsync -avP ${station_comp}:/data/${dt_name}/merged/*${i}_I_*_cand.* .
            sleep 1

            echo "rsync -avP ${station_comp}:/data/${dt_name}/merged/*${i}_XX_*_cand.* ."
            rsync -avP ${station_comp}:/data/${dt_name}/merged/*${i}_XX_*_cand.* .
            sleep 1
   
            echo "rsync -avP ${station_comp}:/data/${dt_name}/merged/*${i}_YY_*_cand.* ."
            rsync -avP ${station_comp}:/data/${dt_name}/merged/*${i}_YY_*_cand.* .
            sleep 1
      
#         echo "rsync -avP ${station_comp}:/data/${dt_name}/merged/*${i}_I_*_cand.reg ."
#         rsync -avP ${station_comp}:/data/${dt_name}/merged/*${i}_I_*_cand.reg .
#         sleep 1
      
            echo "rsync -avP --exclude '_cand.txt' ${station_comp}:/data/${dt_name}/merged/*${i}_I_*diff*.txt ."
            rsync -avP --exclude '_cand.txt' ${station_comp}:/data/${dt_name}/merged/*${i}_I_*diff*.txt .
            sleep 1

            echo "rsync -avP --exclude '_cand.txt' ${station_comp}:/data/${dt_name}/merged/*${i}_XX_*diff*.txt ."
            rsync -avP --exclude '_cand.txt' ${station_comp}:/data/${dt_name}/merged/*${i}_XX_*diff*.txt .
            sleep 1

            echo "rsync -avP --exclude '_cand.txt' ${station_comp}:/data/${dt_name}/merged/*${i}_YY_*diff*.txt ."
            rsync -avP --exclude '_cand.txt' ${station_comp}:/data/${dt_name}/merged/*${i}_YY_*diff*.txt .
            sleep 1
         done
      
         if [[ $copy_fits -gt 0 ]]; then
            echo "copy_fits.sh ${station}:/data/${dt_name}/merged/"
            copy_fits.sh ${station}:/data/${dt_name}/merged/
         fi
      else
         echo "WARNING : no data in ${station}:/data/${dt_name}/merged/"
      fi
      
      cd -      
   done
      
   i=$(($i+1))
done

if [[ $do_analysis -gt 0 ]]; then
   if [[ -n "$EDA2TV_PATH" ]]; then
      echo "INFO : env. variable EDA2TV_PATH=$EDA2TV_PATH"
   else
      echo "ERROR : env. variable EDA2TV_PATH must be defined (add : export EDA2TV_PATH=~/Software/eda2tv/ to ~/.bashrc file)"
   fi

   cd ${aavs2_dir}
   pwd
   
   mkdir -p images/   

   # difference lightcurves of monitored objects :
   ls eda2/sgr1935+2154_diff.txt aavs2/sgr1935+2154_diff.txt > sgr1935+2154_diff.list
   root ${root_options} "plotNfilesFlux_vs_time_scaling.C(\"sgr1935+2154_diff.list\",\"SGR1935+2154\")"
   
   ls eda2/sgr1935+2154_diff.txt eda2/OFF_sgr1935+2154_diff.txt > eda2_ON_vs_OFF_sgr1935+2154_diff.list
   root ${root_options} "plotNfilesFlux_vs_time_scaling.C(\"eda2_ON_vs_OFF_sgr1935+2154_diff.list\",\"ON_OFF_SGR1935+2154\")"

   
   ls eda2/B0950+08_diff.txt aavs2/B0950+08_diff.txt > B0950+08_diff.list
   root ${root_options} "plotNfilesFlux_vs_time_scaling.C(\"B0950+08_diff.list\")"
   
   ls eda2/2C806_diff.txt aavs2/2C806_diff.txt > 2C806_diff.list
   root ${root_options} "plotNfilesFlux_vs_time_scaling.C(\"2C806_diff.list\")"

   ls eda2/OFF_B0950+08_diff.txt aavs2/OFF_B0950+08_diff.txt > OFF_B0950+08_diff.list
   root ${root_options} "plotNfilesFlux_vs_time_scaling.C(\"OFF_B0950+08_diff.list\")"
   
   ls eda2/B0950+08_diff.txt eda2/OFF_B0950+08_diff.txt > eda2_ON_vs_OFF_B0950+08_diff.list
   root ${root_options} "plotNfilesFlux_vs_time_scaling.C(\"eda2_ON_vs_OFF_B0950+08_diff.list\")"

   # normal lightcurves of monitored objects :
   ls eda2/sgr1935+2154.txt aavs2/sgr1935+2154.txt > sgr1935+2154.list
   root ${root_options} "plotNfilesFlux_vs_time_scaling.C(\"sgr1935+2154.list\",\"SGR1935+2154\")"
   
   ls eda2/B0950+08.txt aavs2/B0950+08.txt > B0950+08.list
   root ${root_options} "plotNfilesFlux_vs_time_scaling.C(\"B0950+08.list\")"
   
   ls eda2/2C806.txt aavs2/2C806.txt > 2C806.list
   root ${root_options} "plotNfilesFlux_vs_time_scaling.C(\"2C806.list\",\"2C806\")"

   ls eda2/OFF_B0950+08.txt aavs2/OFF_B0950+08.txt > OFF_B0950+08.list
   root ${root_options} "plotNfilesFlux_vs_time_scaling.C(\"OFF_B0950+08.list\")"
   
   # count B0950 bursts, but ignore those seen off the pulsar
   date
   echo "count_spikes.sh > B0950_spikes.out 2>&1"
   count_spikes.sh > B0950_spikes.out 2>&1
      
   echo "count_spikes.sh sgr1935+2154_diff.txt OFF_sgr1935+2154_diff.txt > sgr1935_spikes.out 2>&1"
   count_spikes.sh sgr1935+2154_diff.txt OFF_sgr1935+2154_diff.txt > sgr1935_spikes.out 2>&1
   
   cd eda2/
   echo "count_spikes.sh > B0950_spikes.out 2>&1"
   count_spikes.sh > B0950_spikes.out 2>&1
   
   echo "count_spikes.sh sgr1935+2154_diff.txt OFF_sgr1935+2154_diff.txt > sgr1935_spikes.out 2>&1"
   count_spikes.sh sgr1935+2154_diff.txt OFF_sgr1935+2154_diff.txt > sgr1935_spikes.out 2>&1
   cd -
   
   # Plot running median subtracted for B0950+08 position:
   echo "plot_running_median.sh"
   plot_running_median.sh

   # run coincidence :
   # Coinc + TLE :
#   echo "eda2_aavs2_concidence.sh eda2/ 25 > coinc_elev15deg.out 2>&1"
#   eda2_aavs2_concidence.sh eda2/ 25 > coinc_elev15deg.out 2>&1
   echo "eda2_aavs2_concidence.sh eda2/ 25 - \"--max_sun_elevation=20\" > coinc_minelev25deg.out 2>&1"
   eda2_aavs2_concidence.sh eda2/ 25 - "--max_sun_elevation=20" > coinc_minelev25deg.out 2>&1
else
   echo "WARNING : analysis is not required"
fi
