#!/usr/bin/bash

# installation script for litestar-pulse [https://github.com/trmznt/litestar-pulse]

# optional variable:
# - VVG_BASEDIR
# - VVG_EXCLUDE
# - MESSY2_REPOURL

set -eu

# run the base.sh
# Detect the shell from which the script was called
parent=$(ps -o comm $PPID |tail -1)
parent=${parent#-}  # remove the leading dash that login shells have
case "$parent" in
  # shells supported by `micromamba shell init`
  bash|fish|xonsh|zsh)
    shell=$parent
    ;;
  *)
    # use the login shell (basename of $SHELL) as a fallback
    shell=${SHELL##*/}
    ;;
esac

# Parsing arguments
if [ -t 0 ] && [ -z "${VVG_BASEDIR:-}" ]; then
  printf "Base installation directory? [./messy2] "
  read VVG_BASEDIR
fi

# default value
VVG_BASEDIR="${VVG_BASEDIR:-./messy2}"

PIXI_ENVNAME="${PIXI_ENVNAME:-messy2}"

# install litestar-pulse
source <(curl -L https://raw.githubusercontent.com/trmznt/litestar-pulse/main/install.sh)

echo "Cloning MESSy2"
git clone --depth 1 ${MESSY2_REPOURL:-https://github.com/vivaxgen/messy2.git} ${ENVS_DIR}/messy2

# perform 2nd stage installation for MESSy2
source ${ENVS_DIR}/messy2/etc/inst-scripts/inst-stage-2.sh

# add to installed-repo.txt
echo "messy2" >> ${ETC_DIR}/installed-repo.txt

echo
echo "MESSy2 has been successfully installed. "
echo "Please read the docs for further setup."
echo "The base installation directory (VVG_BASEDIR) is:"
echo
echo "$(realpath "${VVG_BASEDIR}")"
echo
echo "To activate the basic MESSy2 environment (eg. for installing"
echo "or setting up base enviroment directory), execute the command:"
echo
echo "    $(realpath "${BINDIR}/activate")"
echo

# EOF
