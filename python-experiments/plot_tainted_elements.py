# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script is used to count chronologically how many taint bits are in the design.
# It has been used, for example, to generate the Meltdown and Spectre plots.

# For nice plots, you should adjust the window in `listtaintedelems/luigi/plotcountelems.py`

import luigi
import multiprocessing
import os

from listtaintedelems.luigi.plotcountelems import PlotCountElems

from common.enums import Simulator, InstrumentationMethod
from common.designcfgs import get_design_cellift_path
from common.taintfile import parse_taintfile

# To avoid using all the cores.
process_division_factor = 4

if __name__ == '__main__':
    num_workers = (multiprocessing.cpu_count()+process_division_factor)//process_division_factor

    if "CELLIFT_ENV_SOURCED" not in os.environ:
        raise Exception("The CellIFT environment must be sourced prior to running the Python recipes.")

    SIMULATOR = Simulator.VERILATOR

    simtime = 2000 # 2000 is useful for MDS analysis, and 5000 for Meltdown analysis. This number must be larger than the upper bound of the window given in `listtaintedelems/luigi/plotcountelems.py`.

    design_name = "boom"

    # For Meltdown
    scenario_name = "scenario_1_load_tainted_data_forbidden" # Make sure to have compiled the executable first (in the `sw` subfolder of the design).

    # For Spectre
    # scenario_name = "boom_attacks_v1"
    # scenario_name = "boom_attacks_v1_nofdiv"

    binary_scenario_path = os.path.join(get_design_cellift_path(design_name), "sw", scenario_name, "build", "app.elf")
    taintfile_scenario_path = os.path.join(get_design_cellift_path(design_name), "taint_data", scenario_name, "taint_data.txt")

    run_params = {
        "simulator"       : Simulator.VERILATOR,
        "taintbits"       : parse_taintfile(taintfile_scenario_path),
        "binary"          : binary_scenario_path,
        "design_name"     : design_name,
        "simtime"         : simtime,
        "instrumentation" : InstrumentationMethod.CELLIFT,
    }

    luigi.build([PlotCountElems(**run_params)], workers=num_workers, local_scheduler=True, log_level='INFO')

else:
    raise Exception("This module must be at the toplevel.")
