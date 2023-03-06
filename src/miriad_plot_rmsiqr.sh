#!/bin/bash

lc_file=B0950+08_diff.txt
if [[ -n "$1" && "$1" != "-" ]]; then
   lc_file=$1
fi

# root_options="-b -q -l"
root_options="-l"

# plot RMS vs. uxtime :
rms_vs_time=${lc_file%%.txt}_rms_vs_uxtime.txt
awk '{print $1" "$17;}' ${lc_file} > ${rms_vs_time}
root ${root_options} "plot_rms_vs_time.C(\"${rms_vs_time}\")"

# plot RMS vs. elevation :
rms_vs_elev=${lc_file%%.txt}_rms_vs_elev.txt
awk '{print $11" "$17;}' ${lc_file} > ${rms_vs_elev}
root ${root_options} "plot_rms_vs_elev.C(\"${rms_vs_elev}\")"


# plot distribution :
rms_for_highelev=${lc_file%%.txt}_rms_vs_elevAbove25deg.txt
awk '{if($1>25){print $0;}}' ${rms_vs_elev} > ${rms_for_highelev}
root ${root_options} "histofile.C(\"${rms_for_highelev}\",1,0,0,2000)"
