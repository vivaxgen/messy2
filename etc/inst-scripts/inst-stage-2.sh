#!/usr/bin/env bash

echo "Performing 2nd stage installation for MESSy2"

echo ">>> Link resource files"
${VVGBIN}/link-resource-files.sh ${ENVS_DIR}/messy2/etc/bashrc.d


(
cd ${VVG_BASEDIR}

uv add --editable envs/messy2
)