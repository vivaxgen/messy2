#!.usr/bin/env bash

echo "Performing 2nd stage installation for MESSy2"

(
cd ${VVG_BASEDIR}

uv add --editable envs/messy2
)