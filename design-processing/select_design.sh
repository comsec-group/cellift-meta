# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script sets up the following env variables properly:
# CELLIFT_DESIGN to be one of the keys in design_repos.json.
# CELLIFT_DESIGN_CELLIFTDIR: the repo corresponding to the design, as specified in design_repos.json.
# CELLIFT_DESIGN_START_ADDR: design execution's start address (after the bootrom execution).
#
# This script takes one parameter: the CellIFT design name (e.g., ibex)

export CELLIFT_DESIGN=$1
export CELLIFT_DESIGN_CELLIFTDIR=$CELLIFT_DESIGN_PROCESSING_ROOT/$(cat $CELLIFT_DESIGN_PROCESSING_ROOT/design_repos.json | jq ".$CELLIFT_DESIGN" | sed s/\"//g)

if [[ "$CELLIFT_DESIGN_CELLIFTDIR" == *"{"* ]]; then
    echo "$0 requires one argument: the name of a design"
    return 1
fi
if [[ "$CELLIFT_DESIGN_CELLIFTDIR" == "$CELLIFT_DESIGN_PROCESSING_ROOT/null" ]]; then
    echo "Design '$CELLIFT_DESIGN' not found in $CELLIFT_DESIGN_PROCESSING_ROOT/design_repos.json"
    return 1
fi

start_addr=$CELLIFT_DESIGN_CELLIFTDIR/meta/start_addr.txt

if [ ! -f $start_addr ]; then
    echo "Design '$CELLIFT_DESIGN' does not have a start_addr.txt here: $start_addr."
    return 1
fi


export CELLIFT_DESIGN_START_ADDR=$(cat $CELLIFT_DESIGN_CELLIFTDIR/meta/start_addr.txt)

echo "Selected design: $CELLIFT_DESIGN"
