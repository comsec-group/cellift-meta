# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Runs the experiments for all designs and all benchmarks.
# simulator:         common.enums.Simulator (VERILATOR for instance).
# simtime:           Max num cycles to run, including lead cycles (for CVA6, for instance). This allows to shorten experiments in comparison with the standard duration given in `perfbenchmark/common`.

import luigi
import os
import pickle

from collections import defaultdict

from perfbenchmark.luigi.singledesign import SingleDesignPerformanceExperiment
from perfbenchmark.common import get_design_names, get_design_numcycles

from common.enums import Simulator, InstrumentationMethod
from common.benchmarks import get_benchmark_names, get_benchmark_path, get_benchmark_taint_path
from common.taintfile import parse_taintfile
from common.designcfgs import get_instrumentation_methods_per_design_verilator

class AllDesignsPerformanceExperiment(luigi.Task):
    simulator = luigi.IntParameter()
    simtime   = luigi.IntParameter()

    def __init__(self, *args, **kwargs):
        super(AllDesignsPerformanceExperiment, self).__init__(*args, **kwargs)
        self.experiment_name = "perfbenchmark-all-{}-{}".format(self.simulator, self.simtime)
        self.design_names = get_design_names()
        self.benchmarks = get_benchmark_names()

    def output(self):
        return luigi.LocalTarget('{}/experiments/{}.pickle'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name), format=luigi.format.Nop)

    def requires(self):
        ret = []

        for design_name in self.design_names:
            for benchmark_name in self.benchmarks:
                taintfile_path = get_benchmark_taint_path(design_name, benchmark_name)
                binary_path    = get_benchmark_path(design_name, benchmark_name)

                # Extract the taint bits from the taint data file.
                taintbits = parse_taintfile(taintfile_path)

                simtime = self.simtime

                instrumentation_methods = get_instrumentation_methods_per_design_verilator(design_name)
                for instrumentation_method in instrumentation_methods:
                    run_params = {
                        "simulator"        : Simulator.VERILATOR,
                        "taintbits"        : taintbits,
                        "binary"           : binary_path,
                        "design_name"      : design_name,
                        "simtime"          : min(get_design_numcycles(design_name), self.simtime),
                        "instrumentation"  : instrumentation_method,
                    }

                    if run_params["design_name"] not in run_params["binary"]:
                        raise ("Design name does not appear in the binary path. Did you select the right binary path (for the design {}) : {} ?".format(run_params["design_name"], run_params["binary"]))

                    ret.append(SingleDesignPerformanceExperiment(**run_params))
        return ret

    # @return a dict[design_name][instrumentation][binary] = simtime
    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        # Get the required file pointers.
        pickle_flist = [pickle.load(x.open()) for x in self.input()]

        results_dict = {design_name: defaultdict(dict) for design_name in self.design_names}
        for elem in pickle_flist:
            results_dict[elem['design_name']][elem['instrumentation']][elem['binary']] = elem['simtime']

        with self.output().temporary_path() as outfile_fn:
            pickle.dump(results_dict, open(outfile_fn, 'wb'))
