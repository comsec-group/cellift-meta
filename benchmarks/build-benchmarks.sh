#!/bin/bash
# This script builds the benchmark for a given design, whose name is given in $1. It is used by build-benchmarks-alldesigns.sh

# Check whether meta env has been sourced.
if [ "$CELLIFT_ENV_SOURCED" != "yes" ]
then
    echo "Please source cellift env.sh."
    exit 1
fi

# Check whether jq is installed
if ! command -v jq &> /dev/null
then
    echo "jq could not be found"
    exit 1
fi


source $CELLIFT_DESIGN_PROCESSING_ROOT/select_design.sh $1

if [[ $# == 2 ]]; then
    NUM_JOBS=$2
else
    NUM_JOBS=$CELLIFT_JOBS
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
make -C $SCRIPT_DIR/benchmarks -j $NUM_JOBS
python3 $SCRIPT_DIR/extract_symbols.py out/$CELLIFT_DESIGN $CELLIFT_DESIGN_START_ADDR
