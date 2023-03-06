#!/bin/bash

dump_cal_solutions()
{
   src=$1   
   stokes=$2   
   channel=$3
   reference_antenna=$4

   if [[ -n "$stokes" ]]; then
      echo "gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_amp.txt"
      gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_amp.txt

      echo "gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_pha.txt yaxis=phase"
      gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_pha.txt yaxis=phase

      # Extract calibration solutions
      outfile_amp="chan_${channel}_selfcal_amp"
      outfile_pha="chan_${channel}_selfcal_pha"

      gain_extract_selfcal.sh aavs_gain_${stokes}_amp.txt >> "${outfile_amp}_${stokes}.txt"
      gain_extract_selfcal.sh aavs_gain_${stokes}_pha.txt >> "${outfile_pha}_${stokes}.txt"      
   else
      echo "gpplt vis=${src}.uv log=aavs_gain_amp.txt"
      gpplt vis=${src}.uv log=aavs_gain_amp.txt

      echo "gpplt vis=${src}.uv log=aavs_gain_pha.txt yaxis=phase"
      gpplt vis=${src}.uv log=aavs_gain_pha.txt yaxis=phase

      # Extract calibration solutions
      outfile_amp="chan_${channel}_selfcal_amp"
      outfile_pha="chan_${channel}_selfcal_pha"

      gain_extract_selfcal.sh aavs_gain_amp.txt >> "${outfile_amp}.txt"
      gain_extract_selfcal.sh aavs_gain_pha.txt >> "${outfile_pha}.txt"
      
      # TEST : extract XX and YY to separate files -> did not do what I wanted :
#      echo "gpplt vis=${src}.uv log=aavs_gain_pha_XX.txt yaxis=phase select=\"polarization(XX)\""
#      gpplt vis=${src}.uv log=aavs_gain_pha_XX.txt yaxis=phase select="polarization(XX)"

#      echo "gpplt vis=${src}.uv log=aavs_gain_pha_YY.txt yaxis=phase select=\"polarization(YY)\""
#      gpplt vis=${src}.uv log=aavs_gain_pha_YY.txt yaxis=phase select="polarization(YY)"

   fi
}


calibrate_mfcal()
{
   src=$1   
   stokes=$2   
   channel=$3
   reference_antenna=$4

   # below 150 MHz the uvrange has to be different as otherwise we can end up with 0 baselines 
   # I set limit to B>10m and calculate 
   min_klambda=`echo $channel | awk '{print ($1*(400.00/512.00))/30000.00;}'`

   if [[ -n "$stokes" ]]; then
      # Perhaps not required, but could not make it working otherwise !
      # mfcal vis=${src}.uv flux=51000,0.15,1.6 select='uvrange(0.005,1)'   
      if [[ $channel -le 192 ]]; then # 192*(400/512) = 150 MHz 
         echo "mfcal vis=${src}_${stokes}.uv flux=51000,0.15,1.6 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna}"
         mfcal vis=${src}_${stokes}.uv flux=51000,0.15,1.6 select="uvrange($min_klambda,1)" refant=${reference_antenna}# f > 150 MHz
      else
         echo "mfcal vis=${src}_${stokes}.uv flux=51000,0.15,1.9 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna}"
         mfcal vis=${src}_${stokes}.uv flux=51000,0.15,1.9 select="uvrange($min_klambda,1)" refant=${reference_antenna} # f < 150 MHz
      fi   
 
      echo "dump_cal_solutions $src $stokes $channel $reference_antenna"
      dump_cal_solutions $src $stokes $channel $reference_antenna     
   else
      # mfcal vis=${src}.uv flux=51000,0.15,1.6 select='uvrange(0.005,1)'
      if [[ $channel -le 192 ]]; then # 192*(400/512) = 150 MHz 
         echo "mfcal vis=${src}.uv flux=51000,0.15,1.6 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna} "
         mfcal vis=${src}.uv flux=51000,0.15,1.6 select="uvrange($min_klambda,1)" refant=${reference_antenna} # f > 150 MHz
      else
         echo "mfcal vis=${src}.uv flux=51000,0.15,1.9 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna} "
         mfcal vis=${src}.uv flux=51000,0.15,1.9 select="uvrange($min_klambda,1)" refant=${reference_antenna}  # f < 150 MHz
      fi         
      
      echo "gpplt vis=${src}.uv log=aavs_gain_amp.txt"
      gpplt vis=${src}.uv log=aavs_gain_amp.txt

      echo "gpplt vis=${src}.uv log=aavs_gain_pha.txt yaxis=phase"
      gpplt vis=${src}.uv log=aavs_gain_pha.txt yaxis=phase

      echo "dump_cal_solutions $src \"\" $channel $reference_antenna"
      dump_cal_solutions $src "" $channel $reference_antenna      
   fi
}

calibrate_selfcal()
{
   src=$1   
   stokes=$2   
   channel=$3
   reference_antenna=$4

   echo "selfcal vis=${src}_${stokes}.uv select=\"uvrange(0.005,10)\" options=amplitude,noscale refant=${reference_antenna} flux=100000"
   selfcal vis=${src}_${stokes}.uv select="uvrange(0.005,10)" options=amplitude,noscale refant=${reference_antenna} flux=100000
   
   echo "gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_amp.txt"
   gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_amp.txt
   
   echo "gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_pha.txt yaxis=phase"
   gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_pha.txt yaxis=phase
   

   # Extract calibration solutions
   outfile_amp="chan_${channel}_selfcal_amp"
   outfile_pha="chan_${channel}_selfcal_pha"

   echo "gain_extract_selfcal.sh aavs_gain_${stokes}_amp.txt >> ${outfile_amp}_${stokes}.txt"   
   gain_extract_selfcal.sh aavs_gain_${stokes}_amp.txt >> ${outfile_amp}_${stokes}.txt
   
   echo "gain_extract_selfcal.sh aavs_gain_${stokes}_pha.txt >> ${outfile_pha}_${stokes}.txt"
   gain_extract_selfcal.sh aavs_gain_${stokes}_pha.txt >> ${outfile_pha}_${stokes}.txt

}

image_polarisation()
{
   src=$1
   stokes=$2   
   channel=$3
   robust=-0.5
   imsize=180

   echo "invert vis=${src}_${stokes}.uv map=${src}_${stokes}.map imsize=${imsize},${imsize} beam=${src}_${stokes}.beam robust=$robust  options=double,mfs stokes=${stokes}"
   invert vis=${src}_${stokes}.uv map=${src}_${stokes}.map imsize=${imsize},${imsize} beam=${src}_${stokes}.beam robust=$robust  options=double,mfs stokes=${stokes}

   echo "fits op=xyout in=${src}_${stokes}.map out=${src}_${stokes}.fits"
   fits op=xyout in=${src}_${stokes}.map out=${src}_${stokes}.fits

   path=`which fixCoordHdr.py`
   echo "python $path ${src}_${stokes}.fits"
   python $path ${src}_${stokes}.fits     
}

src=chan_204_20191228T041322
if [[ -n "$1" && "$1" != "-" ]]; then
  src=$1
fi

channel=`echo $src | awk '{s=substr($1,6);idx=index(s,"_");print substr(s,1,idx-1);}'`
if [[ -n "$2" && "$2" != "-" ]]; then
  channel=$2
fi

reference_antenna=3

echo "#################################################"
echo "PARAMETERS :"
echo "#################################################"
echo "src = $src"
echo "channel = $channel"
echo "reference_antenna = $reference_antenna"
echo "#################################################"


echo "fits op=uvin in=${src}.uvfits out=${src}.uv options=compress"
fits op=uvin in=${src}.uvfits out=${src}.uv options=compress

# echo "calibrate_mfcal $src \"\" $channel $reference_antenna"
# calibrate_mfcal $src "" $channel $reference_antenna

# echo "gpplt device='/xs' vis=${src}.uv options=bandpass,wrap yaxis=phase yrange=-200,200 nxy=8,4"
# gpplt device='/xs' vis=${src}.uv options=bandpass,wrap yaxis=phase yrange=-200,200 nxy=8,4

echo "uvcat options=unflagged vis=${src}.uv out=${src}_XX.uv stokes=XX"
uvcat options=unflagged vis=${src}.uv out=${src}_XX.uv stokes=XX

echo "uvcat options=unflagged vis=${src}.uv out=${src}_YY.uv stokes=YY"
uvcat options=unflagged vis=${src}.uv out=${src}_YY.uv stokes=YY

# 
calibrate_selfcal $src XX $channel $reference_antenna
calibrate_selfcal $src YY $channel $reference_antenna


# image XX :
image_polarisation $src XX $channel
image_polarisation $src YY $channel
