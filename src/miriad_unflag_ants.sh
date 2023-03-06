#!/bin/bash

src=chan_204_20210220T160001
if [[ -n "$1" && "$1" != "-" ]]; then
   src="$1"
fi

echo "Unflagging all the antennas in ${src}.uv"

echo "uvflag flagval=unflag vis=${src}.uv"
uvflag flagval=unflag vis=${src}.uv