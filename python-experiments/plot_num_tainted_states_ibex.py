# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import luigi
import multiprocessing
import os

from numtaintedstates.luigi.plot import PlotMaxTaintedStates

from common.enums import Simulator, InstrumentationMethod
from common.taintfile import parse_taintfile

# To avoid using all the cores.
process_division_factor = 4

if __name__ == '__main__':
    num_workers = (multiprocessing.cpu_count()+process_division_factor)//process_division_factor

    if "CELLIFT_ENV_SOURCED" not in os.environ:
        raise Exception("The CellIFT environment must be sourced prior to running the Python recipes.")

    design_name = "ibex"

    # Get the taint bits
    run_params = {
        "simulator"        : Simulator.VERILATOR,
        "design_name"      : design_name,
        "simtime"          : 100000
    }

    luigi.build([PlotMaxTaintedStates(**run_params)], workers=30, local_scheduler=True, detailed_summary=True, log_level='INFO')

else:
    raise Exception("This module must be at the toplevel.")
