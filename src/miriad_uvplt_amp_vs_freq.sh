#!/bin/bash

src=$1

echo "uvplt device='/xs' vis=${src}.uv  axis=freq,amp select=auto nxy=2,2 options=nofqav"
uvplt device='/xs' vis=${src}.uv  axis=freq,amp select=auto nxy=2,2 options=nofqav
