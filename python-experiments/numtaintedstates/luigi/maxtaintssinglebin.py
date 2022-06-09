# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Collects the max number of tainted states (over time) for the parameters given below:
# simulator:         common.enums.Simulator (VERILATOR for instance).
# taintbits:         list of pairs (addr, taint assignment).
# binary:            path to the simulation binary.
# design_name:       see JSON keys in CELLIFT_DESIGN_PROCESSING_ROOT.
# simtime:           num cycles to run, including lead cycles (for CVA6, for instance).
# instrumentation:   list of common.enums.InstrumentationMethod.

import json
import luigi
import numpy as np
import os
import pickle

from common.enums import Simulator, InstrumentationMethod
from common.luigi.simulationrun import SimulationRun
from common.params_to_str import taintstr, binarycrc
from common.vcdsignals import get_taintmatrix

class MaxTaintedStatesSingleBin(luigi.Task):
    simulator        = luigi.IntParameter()
    taintbits        = luigi.ListParameter()
    binary           = luigi.Parameter()
    simtime          = luigi.IntParameter()
    design_name      = luigi.Parameter()
    instrumentation  = luigi.ListParameter()

    def __init__(self, *args, **kwargs):
        super(MaxTaintedStatesSingleBin, self).__init__(*args, **kwargs)
        self.experiment_name = "maxtaintedstatessinglebin-{}-{}-{}-{}-{}-{}".format(self.simulator, taintstr(self.taintbits), binarycrc(self.binary), self.simtime, self.design_name, self.instrumentation)

    def output(self):
        return luigi.LocalTarget('{}/experiments/{}.json'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name), format=luigi.format.Nop)

    def requires(self):
        if self.instrumentation in (InstrumentationMethod.VANILLA, InstrumentationMethod.PASSTHROUGH):
            curr_taintbits = []
        else:
            curr_taintbits = self.taintbits

        return [SimulationRun(simulator=self.simulator, taintbits=curr_taintbits, instrumentation=self.instrumentation, binary=self.binary, simtime=self.simtime, design_name=self.design_name, dotrace=True, include_synth_log=True)]

    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        # Get the simulation result.
        pickle_data = [pickle.load(x.open()) for x in self.input()][0]

        # print("pickle_data['synthlog']", pickle_data['synthlog'])
        taintmatrix, signals_list = get_taintmatrix(pickle_data, pickle_data['synthlog'], self.design_name)

        # Compute the sums of the columns (column is the set of taint signals at a given point in time).
        col_sums = np.sum(taintmatrix, axis=0)
        max_num_tainted_signals = int(max(col_sums))

        with self.output().temporary_path() as outfile_path:
            with open(outfile_path, "w") as outfile:
                json.dump(max_num_tainted_signals, outfile)
