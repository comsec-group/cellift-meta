# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# absolute path we are executing from

if [ "$0" != "$BASH_SOURCE" -a "$BASH_SOURCE" ]
then  # sourced in bash
	myroot=$(dirname $(realpath -- $BASH_SOURCE))
else
	myroot=$(cd $(dirname $0) && pwd -P)
fi

# Sanity check: our root must contain the benchmarks dir
if [ ! -d $myroot/benchmarks ]
then    echo "path detection of env.sh failed; known to fail in dash (/bin/sh). try bash or zsh."
        exit 1
fi

echo "metarepo root: $myroot"

# Set meta repo root
export CELLIFT_META_ROOT=$myroot

# Where are the design submodules located
export CELLIFT_DESIGN_PROCESSING_ROOT=$CELLIFT_META_ROOT/design-processing

# Do not select any design by default
unset CELLIFT_DESIGN

# Defaults

# Where to install the binaries and other files of all the tools
# (compiler toolchain, verilator, sv2v, etc.)
export PREFIX_CELLIFT=$HOME/prefix-cellift

# How many parallel jobs would you like to have issued?
export CELLIFT_JOBS=250 # Feel free to change this
ulimit -n 10000 # many FD's

# Where to store a lot of data?
export CELLIFT_DATADIR=$CELLIFT_META_ROOT/experimental-data # Feel free to change this

# Where the common HDL processing Python scripts are located.
export CELLIFT_PYTHON_COMMON=$CELLIFT_DESIGN_PROCESSING_ROOT/common/python_scripts

# If you would like to customize some of the settings, add another
# $USER test clause like the one below.

if [ "$USER" = flsolt ] # ETHZ Flavien
then
    # Example customization
    export CELLIFT_JOBS=250

    ulimit -n 10000 # many FD's
    export CELLIFT_DATADIR=/data/flsolt/data
fi

# Where should our python venv be?
export CELLIFT_PYTHON_VENV=$PREFIX_CELLIFT/python-venv

# RISCV toolchain location
export RISCV=$PREFIX_CELLIFT/riscv

# Have we been sourced?
export CELLIFT_ENV_SOURCED=yes

# Rust settings
export CARGO_HOME=$PREFIX_CELLIFT/.cargo
export RUSTUP_HOME=$PREFIX_CELLIFT/.rustup

# If we add more variables, let consumers
# of these variables detect it
export CELLIFT_ENV_VERSION=1

# Set opentitan path (for Ibex)
export OPENTITAN_ROOT=$myroot/external-dependencies/cellift-opentitan

# Set yosys scripts location
export CELLIFT_YS=$CELLIFT_DESIGN_PROCESSING_ROOT/common/yosys

# use which compiler?
export CELLIFT_GCC=riscv32-unknown-elf-gcc
export CELLIFT_OBJDUMP=riscv32-unknown-elf-objdump

# use libstdc++ in this prefix
export LD_LIBRARY_PATH=$PREFIX_CELLIFT/lib64:$LD_LIBRARY_PATH

export MPLCONFIGDIR=$PREFIX_CELLIFT/matplotlib
mkdir -p $MPLCONFIGDIR

# Make configuration usable; prioritize our tools
PATH=$PREFIX_CELLIFT/bin:$CARGO_HOME/bin:$PREFIX_CELLIFT/python-venv/bin/:$PATH
PATH=$PREFIX_CELLIFT/riscv/bin:$PATH
