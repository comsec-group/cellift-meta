# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Runs a simple simulation, given the following Luigi parameters:
# simulator:              common.enums.Simulator (VERILATOR for instance).
# taintbits:              list of pairs (addr, taint assignment). Must be empty if instrumentation is Vanilla.
# instrumentation:        common.enums.InstrumentationMethod.
# binary:                 path to the simulation binary.
# design_name:            see JSON keys in CELLIFT_DESIGN_PROCESSING_ROOT.
# simtime:                num cycles to run, including lead cycles.
# dotrace:                boolean.
# include_synth_log:      boolean.

import binascii
import luigi
import os
import pickle

from common.luigi.checkdesignhsb import CheckDesignHSB

from common.enums import Simulator, InstrumentationMethod, instrumentation_method_to_string
from common.sim.verilator import run_sim_verilator
from common.params_to_str import taintstr, binarycrc

class SimulationRun(luigi.Task):
    simulator           = luigi.IntParameter()
    taintbits           = luigi.ListParameter(default=[])
    instrumentation     = luigi.IntParameter()
    binary              = luigi.Parameter()
    design_name         = luigi.Parameter()
    simtime             = luigi.IntParameter()
    dotrace             = luigi.BoolParameter(default=True)
    include_synth_log   = luigi.BoolParameter(default=False)

    def __init__(self, *args, **kwargs):
        super(SimulationRun, self).__init__(*args, **kwargs)

        # Ensure that the taintbits are unset when the instrumentation method is Vanilla.
        if (self.instrumentation == InstrumentationMethod.VANILLA and self.taintbits):
            raise ValueError("If SimpleExperiment is called with Vanilla instrumentation type, then the taint bits must be empty.")

        # Add the taint bits in the design to improve reproducibility.
        self.run_name = "run-sim_{}-{}-{}-d_{}-i_{}-t_{}-tr_{}-s_{}".format(self.simulator, taintstr(self.taintbits), int(self.instrumentation), self.design_name, binarycrc(self.binary), self.simtime, int(self.dotrace), int(self.include_synth_log))

    # Require the design to be built.
    # Technically, benchmarks need to be built only if the binary to run is one of these benchmarks. But it does not hurt to have them compiled.
    def requires(self):
        assert (self.simulator == Simulator.VERILATOR)
        return [CheckDesignHSB(self.instrumentation, self.design_name, self.dotrace)]

    def output(self):
        assert type(self.dotrace) == bool
        return luigi.LocalTarget('{}/simulator-runs/{}/outfile.pickle'.format(os.environ["CELLIFT_DATADIR"], self.run_name), format=luigi.format.Nop)

    # @return a dict with fields 'vcd', 'elapsed', 'stdout', 'synthlog', 'env'.
    def run(self):
        assert type(self.dotrace) == bool

        with self.output().temporary_path() as outfile_path:
            assert not os.path.exists(outfile_path)
            outfile_path = os.path.abspath(outfile_path)
            print('Running simulation using temporary path: {}'.format(outfile_path))
            simbuild = instrumentation_method_to_string(self.instrumentation)
            if self.simulator == Simulator.VERILATOR:
                print("\nOutfile path:", outfile_path)
                ret_dict = run_sim_verilator(self.taintbits, outfile_path, simbuild, self.design_name, self.binary, self.simtime, self.dotrace, self.include_synth_log)
                if self.dotrace:
                    pickle.dump(ret_dict, open(outfile_path, 'wb'))
                else: # If no trace, then do not store the vcd, stdout or synthlog.
                    pickle.dump({'vcd': None, 'elapsed': ret_dict['elapsed'], 'stdout': None, 'synthlog': None, 'env': ret_dict['env']}, open(outfile_path, 'wb'))
            else:
                raise Exception('Unknown simulator: {}'.format(self.simulator))
