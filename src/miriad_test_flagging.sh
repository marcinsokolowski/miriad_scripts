#!/bin/bash

src=chan_204_20210220T160001
if [[ -n "$1" && "$1" != "-" ]]; then
   src="$1"
fi

flag_ant_list=""
do_flag=0
if [[ -n "$2" && "$2" != "-" ]]; then
   flag_ant_list="$2"
   do_flag=1
fi


backup_dir=backup/


if [[ ! -d ${backup_dir}/${src}.uv ]]; then
   echo "WARNING : uv files ${backup_dir}/${src}.uv not found -> please put unflagged (use miriad_unflag_ants.sh) .uv file in backup/ directory"
   exit -1
fi


echo "Removing old files:"
echo "rm -fr *.fits *.uv *.beam *.map"
rm -fr *.fits *.uv *.beam *.map

echo "cp -a backup/${src}.uv ."
cp -a backup/${src}.uv .


# add flagging section here:

if [[ $do_flag -gt 0 ]]; then
   echo "INFO : flagging antennas |$flag_ant_list| is required"
   echo "uvflag flagval=flag vis=${src}.uv select='ant($flag_ant_list)'" > doflag!
   # echo "uvflag flagval=flag vis=${src}_XX.uv select='ant($flags)'" >> doflag!
   # echo "uvflag flagval=flag vis=${src}_YY.uv select='ant($flags)'" >> doflag!
   chmod +x doflag!
   ./doflag!
else
   echo "WARNING : no antennas are requested to be flagged"
fi   

miriad_applycal_and_image_xxyy.sh ${src} cal

echo "ds9 -scale zscale -geometry 2000x1200 $1 -zoom to fit -grid yes -grid type publication -grid skyformat degrees ${src}_XX.fits ${src}_YY.fits &"
ds9 -scale zscale -geometry 2000x1200 $1 -zoom to fit -grid yes -grid type publication -grid skyformat degrees ${src}_XX.fits ${src}_YY.fits &

