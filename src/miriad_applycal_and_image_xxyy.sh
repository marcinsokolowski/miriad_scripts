#!/bin/bash

src=chan_204_20191228T052443
if [[ -n "$1" && "$1" != "-" ]]; then
  src=$1
fi

cal=chan_204_20191228T052443
if [[ -n "$2" ]]; then
   cal=$2
fi

is_cal_xxyy=0
if [[ ${cal} != "-" ]]; then
   is_cal_xxyy=`echo $cal | awk '{u=toupper($1);is_cal_xxyy=index(u,"_X");if(is_cal_xxyy<=0){is_cal_xxyy=index(u,"_Y");}print is_cal_xxyy;}'`
else 
   echo "WARNING : calibration file not provided ( cal = $cal )"
fi

echo "is_cal_xxyy = $is_cal_xxyy"

imsize=180 # 128 or 256 
if [[ -n "$3" && "$3" != "-" ]]; then
   imsize=$3
fi

robust=-0.5
if [[ -n "$4" && "$4" != "-" ]]; then
   robust=$4
fi

do_png=1
if [[ -n "$5" && "$5" != "-" ]]; then
   do_png=$5
fi

do_corrections=1
if [[ -n "$6" && "$6" != "-" ]]; then
   do_corrections=$6
fi

all_channels=0 # if >1 -> image all fine channels 
if [[ -n "$7" && "$7" != "-" ]]; then
   all_channels=$7
fi

update_calibration=1
if [[ -n "$8" && "$8" != "-" ]]; then
   update_calibration=$8
fi

max_calibration_age_in_seconds=43200
if [[ -n "$9" && "$9" != "-" ]]; then
   max_calibration_age_in_seconds=$9
fi


echo "##########################################"
echo "PARAMETERS:"
echo "##########################################"
echo "src = $src"
echo "update_calibration = $update_calibration"
echo "max_calibration_age_in_seconds = $max_calibration_age_in_seconds"
echo "##########################################"


png_stokes=XX

if [[ -d ${src}.uv ]]; then
   echo "UV files ${src}.uv exist -> no need to execute conversion task (.uvfits -> .uv) : fits op=uvin in=${src}.uvfits out=${src}.uv options=compress"
else
   echo "fits op=uvin in=${src}.uvfits out=${src}.uv options=compress"
   fits op=uvin in=${src}.uvfits out=${src}.uv options=compress
fi

# FLAGGING for 2019-12-28 data (EDA2) :
# uvflag flagval=flag vis=${src}.uv select='ant(1,2,3,4,5,6,7,8,9,17,18,19,20,21,22,23,24,31,60,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,125,129,130,131,132,133,134,135,136,137,138,139,140)'
# uvflag flagval=flag vis=${src}.uv select='ant(141,142,143,144,153,154,155,156,157,158,159,160,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,201,202,203,204,205,206,207,208,217,218,219,220,221,222,223,224,230,241,245,249,250,251,252,253,254,255,256)'

# 2019-12-28 AAVS2 :
# uvflag flagval=flag vis=${src}.uv select='ant(1,2,3,4,5,6,7,8,33,34,35,36,37,38,39,40,57,58,59,60,61,62,63,64,117,118,119,120,125,126,127,128,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,201,202,203,204,205,206,207)'
# uvflag flagval=flag vis=${src}.uv select='ant(208,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,241,242,243,244,245,246,247,248)'

echo "puthd in=${src}.uv/jyperk value=2000.0"
puthd in=${src}.uv/jyperk value=2000.0

echo "puthd in=${src}.uv/systemp value=200.0"
puthd in=${src}.uv/systemp value=200.0

# make calibration solutions valid for infinite time (365 days is good enough as infinity in this case) :
if [[ -d ${cal}_XX.uv ]]; then
   echo "puthd in=${cal}_XX.uv/interval value=365"
   puthd in=${cal}_XX.uv/interval value=365
else
   echo "WARNING : calibration file ${cal}_XX.uv does not exist -> puthd skipped"
fi

if [[ -d ${cal}_YY.uv ]]; then
   echo "puthd in=${cal}_YY.uv/interval value=365"
   puthd in=${cal}_YY.uv/interval value=365
else
   echo "WARNING : calibration file ${cal}_YY.uv does not exist -> puthd skipped"
fi
   

cnt_xxyy=`ls -d ${src}_XX.uv ${src}_YY.uv | wc -l`

if [[ $cnt_xxyy -le 0 ]]; then
   echo "uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv"
   uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
   
   echo "uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv"
   uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv
fi

# apply calibration in both XX and YY :
if [[ -d ${cal}_XX.uv ]]; then
   echo "gpcopy vis=${cal}_XX.uv out=${src}_XX.uv options=relax"
   gpcopy vis=${cal}_XX.uv out=${src}_XX.uv options=relax
else
   echo "WARNING : calibration file ${cal}_XX.uv does not exist -> gpcopy skipped"
fi

if [[ -d ${cal}_YY.uv ]]; then   
   echo "gpcopy vis=${cal}_YY.uv out=${src}_YY.uv options=relax"
   gpcopy vis=${cal}_YY.uv out=${src}_YY.uv options=relax
else
   echo "WARNING : calibration file ${cal}_YY.uv does not exist -> gpcopy skipped"
fi
   
invert_options="double,mfs"
if [[ $all_channels -gt 0 ]]; then
   invert_options="double"
fi

# images :
rm -fr ${src}_XX.map ${src}_XX.beam
echo "invert vis=${src}_XX.uv map=${src}_XX.map imsize=${imsize},${imsize} beam=${src}_XX.beam robust=$robust options=$invert_options stokes=XX select='uvrange(0.0,100000)'"
invert vis=${src}_XX.uv map=${src}_XX.map imsize=${imsize},${imsize} beam=${src}_XX.beam robust=$robust options=$invert_options stokes=XX select='uvrange(0.0,100000)'
echo "fits op=xyout in=${src}_XX.map out=${src}_XX.fits"
fits op=xyout in=${src}_XX.map out=${src}_XX.fits

rm -fr ${src}_YY.map ${src}_YY.beam
echo "invert vis=${src}_YY.uv map=${src}_YY.map imsize=${imsize},${imsize} beam=${src}_YY.beam robust=$robust options=$invert_options stokes=YY select='uvrange(0.0,100000)'"
invert vis=${src}_YY.uv map=${src}_YY.map imsize=${imsize},${imsize} beam=${src}_YY.beam robust=$robust options=$invert_options stokes=YY select='uvrange(0.0,100000)'
echo "fits op=xyout in=${src}_YY.map out=${src}_YY.fits"
fits op=xyout in=${src}_YY.map out=${src}_YY.fits

utc=`fitshdr ${src}_XX.fits  | grep DATE-OBS | awk '{gsub("''","",$0);dtm=substr($2,2,19);gsub("T","_",dtm);gsub("-","",dtm);gsub(":","",dtm);print dtm;}'`
dtm_utc=`echo ${utc} | awk '{print substr($1,1,4)"-"substr($1,5,2)"-"substr($1,7,2)" "substr($1,10,2)":"substr($1,12,2)":"substr($1,14,2);}'`
dtm_utc_hour=`echo ${utc} | awk '{print substr($1,10,2);}'`
ux=`date -u -d "${dtm_utc}" +%s`

echo "utc = $utc -> unix time = $ux , dtm_utc_hour = $dtm_utc_hour"


# ux=`date2date -ut2ux=${utc} | awk '{print $3;}'`
# lst=`ux2sid $ux | awk '{print $8}'`
# echo "ux = $ux -> lst = $lst"
if [[ $do_corrections -gt 0 ]]; then
   # optimisations : both XX and YY files in one go:
   if [[ $all_channels -le 0 ]]; then
      path=`which fixCoordHdr.py`
      echo "time python $path ${src}_XX.fits,${src}_YY.fits"
      time python $path ${src}_XX.fits,${src}_YY.fits
   else
      echo "WARNING : generating data cube for all channels and script fixCoordHdr.py is not ready for this -> skipped -> coordinates might be wrong !"
   fi

   # echo "time python $path ${src}_YY.fits"
   # time python $path ${src}_YY.fits

   # (XX+YY) -> I       
   # TODO : in the future proper calculation of Stokes I from XX and YY !!!
   #        using Adrian's formalism 
   echo "time miriad_avg_xxyy.sh ${src}_XX.fits"
   time miriad_avg_xxyy.sh ${src}_XX.fits

   show_path=`which show_known_sources.py`
   echo "python $show_path ${src}_${png_stokes}.fits"
   time python $show_path ${src}_${png_stokes}.fits

   if [[ $do_png -gt 0 ]]; then   
      echo "time miriad_image2jpg.sh ${src} ${png_stokes}"
      time miriad_image2jpg.sh ${src} ${png_stokes}
   else 
      echo "WARNING : png file is not required"
   fi
else
   echo "WARNING : fixCoordHdr.py, miriad_avg_xxyy.sh, show_known_sources.py and miriad_image2jpg.sh is not required - maybe it's done by the calling script"
fi   


# new part - checking if calibration is fresh and updates if not:
if [[ $update_calibration -gt 0 && 0 -gt 1 ]]; then # Changed to ALWAYS false because it is done in eda2tv_convert.sh as currently hdf5 file is required to convert with Sun in the phase centre !
   echo "INFO : updating calibration is required"
      
   last_calibration_ux=-1
   diff_ux=1000000000
   if [[ -s calibration/last_calibration.txt ]]; then
      last_calibration_ux=`cat calibration/last_calibration.txt`
      echo "INFO : last calibration ux = $last_calibration_ux"      
      diff_ux=$(($ux-$last_calibration_ux))
   else
      echo "INFO : last calibration file not found -> diff_ux = $diff_ux"
   fi

   if [[ $diff_ux -gt $max_calibration_age_in_seconds ]]; then
      # TODO : check if time is around sun transit - for now checking if UTC = 4 hours , but later do it in more proper way to more general not just for the MRO:
      if [[ $dtm_utc_hour == "04" ]]; then # do it exactly for the MIDDAY file:         
         echo "INFO : last calibration performed on $last_calibration_ux , current file ux = $ux -> difference = $diff_ux > max cal. age = $max_calibration_age_in_seconds -> RE-CALIBRATING"
         echo "INFO : utc_hour = $dtm_utc_hour -> can do re-calibration"
         
         channel=`echo $src | awk '{i1=index($1,"_");s=substr($1,i1+1);i2=index(s,"_");print substr(s,1,i2-1);}'`

         tmp_uvlist_file=`date +%s_uvlist`
         echo $src > $tmp_uvlist_file         
         
         # 7th parameter = 0 is set to not use HDF5 files but just unixtime of specified .uvfits file:
         echo "calibrate_uvfits.sh 1 $channel $tmp_uvlist_file 1 calibration/ 1 0"
         calibrate_uvfits.sh 1 $channel $tmp_uvlist_file 1 calibration/ 1 0 
         
         # move current calibration solutions to OLD directory (calibration_old)
         # and update calibration solutions used by the pipeline :
         mkdir -p calibration_old
         echo "rm -f calibration_old/chan_${channel}*.uv"
         rm -f calibration_old/chan_${channel}*.uv
         
         echo "mv chan_${channel}_??.uv calibration_old/"
         mv chan_${channel}_??.uv calibration_old/
      
         echo "mv chan_${channel}.uv calibration_old/"
         mv chan_${channel}.uv calibration_old/
         
         echo "cp -a calibration/cal.uv chan_${channel}.uv"
         cp -a calibration/cal.uv chan_${channel}.uv

         echo "cp -a calibration/cal_XX.uv chan_${channel}_XX.uv"
         cp -a calibration/cal_XX.uv chan_${channel}_XX.uv

         echo "cp -a calibration/cal_YY.uv chan_${channel}_YY.uv"
         cp -a calibration/cal_YY.uv chan_${channel}_YY.uv
      else
         echo "INFO : time [hour] of the UV fits file is $dtm_utc_hour UTC -> not near solar transit at the MRO -> skipped"
      fi
   else
      echo "INFO : last calibration performed on $last_calibration_ux , current file ux = $ux -> difference = $diff_ux < max cal. age = $max_calibration_age_in_seconds"
   fi
else
   echo "WARNING : automatic update of calibration is not required"
fi
