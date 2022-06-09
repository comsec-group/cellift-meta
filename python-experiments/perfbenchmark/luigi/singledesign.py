# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# For a given design, runs a experiment to evaluate the simulation speed under different instrumentation methods.
# simulator:         common.enums.Simulator (VERILATOR for instance).
# taintbits:         list of pairs (addr, taint assignment).
# binary:            path to the simulation binary.
# design_name:       see JSON keys in CELLIFT_DESIGN_PROCESSING_ROOT.
# simtime:           num cycles to run, including lead cycles (for CVA6, for instance).
# instrumentation:   list of common.enums.InstrumentationMethod.

import luigi
import os
import pickle
from pathlib import Path

from common.enums import Simulator, InstrumentationMethod
from common.params_to_str import taintstr, binarycrc
from common.luigi.simulationrun import SimulationRun

class SingleDesignPerformanceExperiment(luigi.Task):
    simulator        = luigi.IntParameter()
    taintbits        = luigi.ListParameter()
    binary           = luigi.Parameter()
    simtime          = luigi.IntParameter()
    design_name      = luigi.Parameter()
    instrumentation  = luigi.ListParameter()

    def __init__(self, *args, **kwargs):
        super(SingleDesignPerformanceExperiment, self).__init__(*args, **kwargs)
        self.experiment_name = "perfbenchmark-{}-{}-{}-{}-{}-{}".format(self.simulator, taintstr(self.taintbits), binarycrc(self.binary), self.simtime, self.design_name, self.instrumentation)

    def output(self):
        return luigi.LocalTarget('{}/experiments/{}.pickle'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name), format=luigi.format.Nop)

    def requires(self):
        if self.instrumentation in (InstrumentationMethod.VANILLA, InstrumentationMethod.PASSTHROUGH):
            curr_taintbits = []
        else:
            curr_taintbits = self.taintbits

        return [SimulationRun(simulator=self.simulator, taintbits=curr_taintbits, instrumentation=self.instrumentation, binary=self.binary, simtime=self.simtime, design_name=self.design_name, dotrace=False, include_synth_log=False)]

    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        # Get the required file pointers.
        pickle_flist = [pickle.load(x.open()) for x in self.input()]

        simtimes = list(map(lambda x: x['elapsed'], pickle_flist))
        assert len(simtimes) == 1
        simtime = simtimes[0]

        label = 'Performance benchmark {} {}'.format(self.design_name, simulator_name)
        results_dict = {
            'label': label,
            'design_name': self.design_name,
            'instrumentation': self.instrumentation,
            'binary': self.binary,
            'simtime': simtime
        }

        with self.output().temporary_path() as outfile_fn:
            pickle.dump(results_dict, open(outfile_fn, 'wb'))
