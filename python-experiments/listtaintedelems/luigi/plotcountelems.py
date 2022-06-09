# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# For a given design, runs a experiment to get the number of bits tainted at each cycle.
# simulator:         common.enums.Simulator (VERILATOR for instance).
# taintbits:         list of pairs (addr, taint assignment).
# binary:            path to the simulation binary.
# design_name:       see JSON keys in CELLIFT_DESIGN_PROCESSING_ROOT.
# simtime:           num cycles to run, including lead cycles (for CVA6, for instance).
# instrumentation:   list of common.enums.InstrumentationMethod.

import json
import luigi
import os

from listtaintedelems.luigi.countelems import CountElems
from common.enums import Simulator, InstrumentationMethod
from common.params_to_str import taintstr, binarycrc
from common.vcdsignals import get_taintmatrix, vcd_timestep

import matplotlib.pyplot as plt

#####
# Luigi task
#####

class PlotCountElems(luigi.Task):
    simulator        = luigi.IntParameter()
    taintbits        = luigi.ListParameter()
    binary           = luigi.Parameter()
    simtime          = luigi.IntParameter()
    design_name      = luigi.Parameter()
    instrumentation  = luigi.ListParameter()

    def __init__(self, *args, **kwargs):
        super(PlotCountElems, self).__init__(*args, **kwargs)
        self.experiment_name = "plotcountelems-{}-{}-{}-{}-{}-{}".format(self.simulator, taintstr(self.taintbits), binarycrc(self.binary), self.simtime, self.design_name, self.instrumentation)

    def output(self):
        return luigi.LocalTarget('{}/experiments/{}.png'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name), format=luigi.format.Nop)

    def requires(self):
        return [CountElems(
            simulator       = self.simulator,
            taintbits       = self.taintbits,
            binary          = self.binary,
            simtime         = self.simtime,
            design_name     = self.design_name,
            instrumentation = self.instrumentation
        )]

    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        # Get the required file pointers.
        json_data = [json.load(x.open()) for x in self.input()][0]

        # For Meltdown
        minx, maxx = 1000, 1700
        # For Spectre
        # minx, maxx = 400, 750

        X = list(range(minx, maxx+1))
        Y = json_data[minx:maxx+1]

        fig = plt.figure(figsize=(10, 2))

        plt.grid()
        plt.plot(X, Y)
        plt.xlabel("Clock cycle")
        plt.ylabel("Num. tainted bits")

        plt.tight_layout()
        plt.savefig("meltdown_{}.png".format(self.design_name), dpi=300)
        plt.savefig("meltdown_{}.pdf".format(self.design_name), dpi=300)
    