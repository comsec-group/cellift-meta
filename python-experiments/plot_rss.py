# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import luigi
import multiprocessing
import os

from collectrss.luigi.plot import RSSPlot

from common.enums import Simulator

if __name__ == '__main__':
    if "CELLIFT_ENV_SOURCED" not in os.environ:
        raise Exception("The CellIFT environment must be sourced prior to running the Python recipes.")

    SIMULATOR = Simulator.VERILATOR

    luigi.build([RSSPlot(simulator=SIMULATOR)], workers=1, local_scheduler=True, log_level='INFO')

else:
    raise Exception("This module must be at the toplevel.")
