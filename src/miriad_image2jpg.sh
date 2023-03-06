#!/bin/bash

do_png=1

src="test"
if [[ -n "$1" && "$1" != "-" ]]; then
   src="$1"
fi

stokes=XX
if [[ -n "$2" && "$2" != "-" ]]; then
   stokes="$2"
fi

force=0
if [[ -n "$3" && "$3" != "-" ]]; then
   force="$3"
fi

regfile=${src}_${stokes}_known_sources.reg
if [[ -n "$4" && "$4" != "-" ]]; then
   regfile=$4
fi

outdir="images/"
if [[ -n "$5" && "$5" != "-" ]]; then
   outdir=$5
fi

fits=${src}_${stokes}.fits
if [[ -n "$6" && "$6" != "-" ]]; then
   fits=$6
fi

png=${fits%%fits}png
if [[ ! -s ${outdir}/${png} || $force -gt 0 ]]; then

   # TODO fix so that it's not needed :
   # remove this call - just verify imagefits.py if works ok ...
   date
   path=`which remove_2axis_keywords.py`
   echo "python $path $fits"
   python $path $fits
   date
   
   which python
   path=`which imagefits.py`
   echo "time python $path $fits --outfile $png --outdir ${outdir} --ext=png $options --regfile=${regfile}"
   time python $path $fits --outfile $png --outdir ${outdir} --ext=png $options --regfile=${regfile}
   date
else
   echo "Image $png already exists"
fi
