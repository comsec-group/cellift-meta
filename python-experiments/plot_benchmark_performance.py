# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script plots the performance of all benchmarks on all designs.

import luigi
import multiprocessing
import os

from perfbenchmark.luigi.plot import PerformancePlot

from common.enums import Simulator

# To avoid using all the cores.
process_division_factor = 4

if __name__ == '__main__':
    num_workers = (multiprocessing.cpu_count()+process_division_factor)//process_division_factor

    if "CELLIFT_ENV_SOURCED" not in os.environ:
        raise Exception("The CellIFT environment must be sourced prior to running the Python recipes.")

    SIMULATOR = Simulator.VERILATOR
    MAX_SIM_CYCLES = 10 # This value allows for shorter experiments. Set to a lower value to cap the experiment duration.

    jobs = [PerformancePlot(simulator=SIMULATOR, simtime=MAX_SIM_CYCLES)]
    luigi.build(jobs, workers=num_workers, local_scheduler=True, log_level='INFO')
    for j in jobs:
        print('%s' % j.output().path)

else:
    raise Exception("This module must be at the toplevel.")
