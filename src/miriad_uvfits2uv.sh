#!/bin/bash

do_plots=1

for uvfits in `ls *.uvfits`
do
   src=${uvfits%%.uvfits}
   
   # convert uvfits to uv
   fits op=uvin in=${src}.uvfits out=${src}.uv options=compress

   # uvspec device='/xs' vis=${src}.uv axis=freq,amp select=auto nxy=1,1
   puthd in=${src}.uv/jyperk value=2000.0
   puthd in=${src}.uv/systemp value=200.0
   uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
   uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv
#   uvspec device='/xs' vis=${src}.uv axis=freq,amp select=auto select='ant(0)' nxy=1,1
   uvdump vis=${src}.uv vars=freq,amp select=auto stokes=’XX’    
   
   # uvspec device='/xs' vis=${src}.uv axis=freq,amp select=auto nxy=8,4
done




