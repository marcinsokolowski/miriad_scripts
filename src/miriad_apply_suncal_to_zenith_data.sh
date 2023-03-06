#!/bin/bash

src=chan_294_20220913T093730
cal=chan_294_20220914T041301
robust=-0.5
imsize=256

rm -fr *.beam *.map *.fits *.uv *.uv_c

cp -a data/*uv .
cp -a calibration/*.uv .


# 
puthd in=${cal}.uv/interval value=365
puthd in=${cal}_XX.uv/interval value=365
puthd in=${cal}_YY.uv/interval value=365

# change phase centre of calibration UV to zenith from Sun :
# 11:32:12 -26:42:11
# uvedit vis=${cal}_XX.uv ra=16,53,37 dec=-26,42,11
uvedit vis=${cal}_XX.uv ra=11:32:12 dec=-26,42,11 # options=nouv
mv ${cal}_XX.uv ${cal}_XX.uv.sun_phase_centre
mv ${cal}_XX.uv_c ${cal}_XX.uv
invert vis=${cal}_XX.uv map=${cal}_XX.map imsize=${imsize},${imsize} beam=${cal}_XX.beam robust=$robust options=double,mfs stokes=XX select='uvrange(0.0,100000)'
fits op=xyout in=${cal}_XX.map out=${cal}_XX.fits
ds9 -zoom to fit -scale zscale -geometry 2000x1200  ${cal}_XX.fits & 
gpplt vis=${cal}_XX.uv log=cal_pha_XX.txt yaxis=phase
gpplt vis=${cal}_YY.uv log=cal_pha_YY.txt yaxis=phase
gpplt vis=${cal}_XX.uv log=cal_amp_XX.txt yaxis=phase
gpplt vis=${cal}_YY.uv log=cal_amp_YY.txt yaxis=phase



# uvedit vis=${src}_XX.uv ra=16,53,37 dec=-26,42,11

# apply calibration separately to XX and YY :
gpcopy vis=${cal}_XX.uv out=${src}_XX.uv options=relax
gpcopy vis=${cal}_YY.uv out=${src}_YY.uv options=relax
 
# test application to .uv (not separately _XX.uv and _YY.uv)
# gpcopy vis=${cal}.uv out=${src}.uv options=relax
# rm -fr ${src}_XX.uv ${src}_YY.uv
# uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
# uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv


# uvedit vis=${src}_XX.uv ra=16,53,37 dec=-26,42,11

invert vis=${src}_XX.uv map=${src}_XX.map imsize=${imsize},${imsize} beam=${src}_XX.beam robust=$robust options=double,mfs stokes=XX select='uvrange(0.0,100000)'
fits op=xyout in=${src}_XX.map out=${src}_XX.fits
gpplt vis=${src}_XX.uv log=src_pha_XX.txt yaxis=phase
gpplt vis=${src}_YY.uv log=src_pha_YY.txt yaxis=phase
gpplt vis=${src}_XX.uv log=src_amp_XX.txt yaxis=phase
gpplt vis=${src}_YY.uv log=src_amp_YY.txt yaxis=phase


ds9 -zoom to fit -scale zscale -geometry 2000x1200  ${src}_XX.fits & 


echo
echo
echo
echo "CAL:"
prthd in=${cal}_XX.uv options=full
echo
echo
echo
echo "SRC:"
prthd in=${src}_XX.uv options=full



# blflag vis=${cal}_XX.uv device=/xserve axis=uvdistance options=nobase xrange=0.00001,100
# blflag vis=${src}_XX.uv device=/xserve axis=uvdistance options=nobase xrange=0.00001,100


# Print information:
echo
echo
itemize in=${cal}_XX.uv|sort
echo
echo
itemize in=${src}_XX.uv|sort