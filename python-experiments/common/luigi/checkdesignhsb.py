# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This task checks whether the HSB (hardware simulation binary) has been built, given the following Luigi parameters:
# instrumentation:        common.enums.InstrumentationMethod.
# design_name:            see JSON keys in CELLIFT_DESIGN_PROCESSING_ROOT.
# dotrace:                boolean.

import binascii
import luigi
import os
import pickle
import subprocess
from pathlib import Path

from common.enums import Simulator, InstrumentationMethod, instrumentation_method_to_string
from common.sim.verilator import run_sim_verilator
from common.params_to_str import taintstr, binarycrc
from common.designcfgs import get_design_hsb_path, get_design_cellift_path

class CheckDesignHSB(luigi.Task):
    instrumentation     = luigi.IntParameter()
    design_name         = luigi.Parameter()
    dotrace             = luigi.BoolParameter(default=True)

    def __init__(self, *args, **kwargs):
        super(CheckDesignHSB, self).__init__(*args, **kwargs)
        self.hsb_path = os.path.join(*get_design_hsb_path(self.design_name, self.instrumentation, self.dotrace))

    # This Luigi task is a pipeline leaf.
    def requires(self):
        return None

    def output(self):
        assert type(self.dotrace) == bool
        return luigi.LocalTarget(self.hsb_path, format=luigi.format.Nop)

    def run(self):
        if not os.path.isfile(self.hsb_path):
            raise ValueError("Error, expected {} to exist. Please build it, for example through {}.".format(self.hsb_path, os.path.join(os.getenv("CELLIFT_DESIGN_PROCESSING_ROOT"), "make_all_designs.py")))
