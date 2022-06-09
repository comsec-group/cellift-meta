#!/bin/bash
# This script builds the benchmarks for all current designs.

set -e

if [ "$CELLIFT_ENV_SOURCED" != "yes" ]
then
    echo "Please source cellift env.sh."
    exit 1
fi

for DESIGN in ibex pulpissimo cva6 rocket boom
do
    source build-benchmarks.sh $DESIGN
done
