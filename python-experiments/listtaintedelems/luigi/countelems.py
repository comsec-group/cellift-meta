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

import ctypes
import itertools
import json
import luigi
import multiprocessing as mp
import numpy as np
import os
import pickle

from common.enums import Simulator, InstrumentationMethod
from common.params_to_str import taintstr, binarycrc
from common.luigi.simulationrun import SimulationRun
from common.vcdsignals import get_taintmatrix, vcd_timestep

NUM_PROCESSES = int(os.getenv("CELLIFT_JOBS"))

#####
# multiprocessing workers
#####

def init_worker(shared_taintmatrix):
    global shared_taintmatrix_glob
    shared_taintmatrix_glob = shared_taintmatrix

# Parallel worker used in the run function
# @param row_size the row size of the transposed matrix, i.e., the number of observed signals at a given point in time.
# @implicit the param shared_taintmatrix is passed implicitly by mp. It is the flattened transposed taint matrix.
# @return a list of row ids.
def count_affected_components_worker(row_size, timestep):
    ret = 0
    for row_id in range(row_size):
        ret += shared_taintmatrix_glob[row_size*timestep + row_id]
    return ret

#####
# Luigi task (calls the multiprocessing workers)
#####

class CountElems(luigi.Task):
    simulator        = luigi.IntParameter()
    taintbits        = luigi.ListParameter()
    binary           = luigi.Parameter()
    simtime          = luigi.IntParameter()
    design_name      = luigi.Parameter()
    instrumentation  = luigi.ListParameter()

    def __init__(self, *args, **kwargs):
        super(CountElems, self).__init__(*args, **kwargs)
        self.experiment_name = "countelems-{}-{}-{}-{}-{}-{}".format(self.simulator, taintstr(self.taintbits), binarycrc(self.binary), self.simtime, self.design_name, self.instrumentation)
        # This pass is typically used with CellIFT (although compatible with GLIFT as well)
        assert self.instrumentation not in {InstrumentationMethod.VANILLA, InstrumentationMethod.PASSTHROUGH}

    def output(self):
        return luigi.LocalTarget('{}/experiments/{}.json'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name), format=luigi.format.Nop)

    def requires(self):
        return [SimulationRun(simulator=self.simulator, taintbits=self.taintbits, instrumentation=self.instrumentation, binary=self.binary, simtime=self.simtime, design_name=self.design_name, dotrace=True, include_synth_log=True)]

    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        # Get the required file pointers.
        pickle_data = [pickle.load(x.open()) for x in self.input()][0]

        taintmatrix, signals_list = get_taintmatrix(pickle_data, pickle_data['synthlog'], self.design_name)

        # Parallelize finding the affected microelements
        print("Creating shared matrix...")
        taintmatrix_transposed = taintmatrix.transpose()
        shared_taintmatrix = mp.RawArray(ctypes.c_int16, taintmatrix_transposed.size)
        # Copy the matrix into the shared area
        shared_taintmatrix_np = np.frombuffer(shared_taintmatrix, np.int16).reshape(taintmatrix_transposed.shape)
        np.copyto(shared_taintmatrix_np, taintmatrix_transposed)

        print("Done: Creating shared matrix.")

        worker_params = list(zip(itertools.repeat(taintmatrix.shape[0]), range(0, len(taintmatrix[0]), vcd_timestep)))
        print("Counting tainted signals...")
        with mp.Pool(processes=NUM_PROCESSES, initializer=init_worker, initargs=(shared_taintmatrix, )) as pool:
            tainted_signal_counts = pool.starmap(count_affected_components_worker, worker_params)
            pool.close()
            pool.join()
        print("Done: Counting tainted signals.")

        with self.output().temporary_path() as outfile_path:
            with open(outfile_path, "w") as outfile:
                json.dump(tainted_signal_counts, outfile)
