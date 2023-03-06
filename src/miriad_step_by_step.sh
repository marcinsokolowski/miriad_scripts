#!/bin/bash

# src=chan_294_20220716T040000
# src=chan_294_20220716T040920
src=chan_294_20220716T120001
cal=chan_294_20220716T041000

cal_dt=`echo $cal | cut -b 10-17`
cal_tm=`echo $cal | cut -b 19-26`
cal_ux=`date2date -ut2ux=$cal | awk '{print $3;}'`
print_sun $cal_ux -c 

# (RA,DEC)   = ( 285.6552 , -22.6606 ) [deg]
# deg2radec.sh 285.6552 -22.6606
# 19:02:37 -22:39:38

rm -fr *.uv *.beam *.map *.fits *.txt

fits op=uvin in=${cal}.uvfits out=${cal}.uv options=compress
uvedit vis=${cal} ra=19,02,37 dec=-22,39,38
# puthd in=${cal}.uv/jyperk value=1310.0
# puthd in=${cal}.uv/systemp value=200.0
# uvcat vis=${cal}.uv stokes=xx out=${cal}_XX.uv
# uvcat vis=${cal}.uv stokes=yy out=${cal}_YY.uv


apparent_solar_flux=51000
apparent_solar_flux_x=51000
apparent_solar_flux_y=51000
reference_antenna=3
imsize=256
robust=-0.5

mfcal vis=${cal}.uv flux=${apparent_solar_flux},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna} 
# mfcal vis=${cal}_XX.uv flux=${apparent_solar_flux_x},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna} # f > 150 MHz
# mfcal vis=${cal}_YY.uv flux=${apparent_solar_flux_y},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna} # f > 150 MHz
uvcat vis=${cal}.uv stokes=xx out=${cal}_XX.uv
uvcat vis=${cal}.uv stokes=yy out=${cal}_YY.uv


# dump cal. solutions :
gpplt vis=${cal}_XX.uv log=pha_XX.txt yaxis=phase
gpplt vis=${cal}_YY.uv log=pha_YY.txt yaxis=phase
gpplt vis=${cal}_XX.uv log=amp_XX.txt yaxis=phase
gpplt vis=${cal}_YY.uv log=amp_YY.txt yaxis=phase

# 
puthd in=${cal}.uv/interval value=365
puthd in=${cal}_XX.uv/interval value=365
puthd in=${cal}_YY.uv/interval value=365

invert vis=${cal}_XX.uv map=${cal}_XX.map imsize=${imsize},${imsize} beam=${cal}_XX.beam robust=$robust options=double,mfs stokes=XX select='uvrange(0.0,100000)'
fits op=xyout in=${cal}_XX.map out=${cal}_XX.fits



# apply and image :
fits op=uvin in=${src}.uvfits out=${src}.uv options=compress
# puthd in=${src}.uv/jyperk value=1310.0
# puthd in=${src}.uv/systemp value=200.0

# vs other place:
gpcopy vis=${cal}.uv out=${src}.uv options=relax mode=copy

uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv

# gpcopy vis=${cal}_XX.uv out=${src}_XX.uv options=relax
# gpcopy vis=${cal}_YY.uv out=${src}_YY.uv options=relax

invert vis=${src}_XX.uv map=${src}_XX.map imsize=${imsize},${imsize} beam=${src}_XX.beam robust=$robust options=double,mfs stokes=XX select='uvrange(0.0,100000)'
fits op=xyout in=${src}_XX.map out=${src}_XX.fits



