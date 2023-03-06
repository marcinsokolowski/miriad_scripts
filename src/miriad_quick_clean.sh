#!/bin/bash

src=chan_204_20200410T190854
if [[ -n "$1" && "$1" != "-" ]]; then
   src=$1
fi

stokes=XX

invert vis=${src}_XX.uv map=${src}_XX.map imsize=180,180 beam=${src}_XX.beam robust=-0.5 options=double,mfs stokes=XX select='uvrange(0.0,100000)'
clean map=${src}_${stokes}.map beam=${src}_${stokes}.beam out=${src}_${stokes}.clean niters=15000 speed=-1 cutoff=0.2
restor model=${src}_${stokes}.clean beam=${src}_${stokes}.beam map=${src}_${stokes}.map out=${src}_${stokes}.restor options=mfs
fits op=xyout in=${src}_XX.restor out=${src}_XX.fits


fitshdr ${src}_XX.fits | grep BM

