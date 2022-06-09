# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script provides the following functions to run Verilator simulations:
#   run_sim_verilator
#

import os
import re
import pickle
import subprocess
import sys
import time
from pathlib import Path

from .commonsim import write_taintfile, setup_sim_env
import common.designcfgs as designcfgs
from vcdvcd import VCDVCD

# Runs an already-built Verilator simulation binary.
#
# @param taintbits: tuple (addr, byte, taint_mask).
# @param vcdpickle_final: path of the output vcd file.
# @param simbuild: build directory.
# @param design: design name (string).
# @param binary: the path to the ELF.
# @param run_simtime: number of simulation cycles.
# @param include_synth_log: boolean indicating whether to insert the synth log data into the output log.
# @return {'vcd': vcd, 'elapsed': elapsed, 'stdout': open(outputfile).read(), 'synthlog': synthlog, 'env': my_env}.
def run_sim_verilator(taintbits, vcdpickle_final, simbuild, design, binary, run_simtime, dotrace, include_synth_log):
    # Verilator-specific config.
    design_cfg       = designcfgs.get_design_cfg(design)
    celliftdir       = designcfgs.get_design_cellift_path(design)
    builddir         = os.path.join(celliftdir,'build')
    resultsdir_final = os.path.abspath(os.path.dirname(vcdpickle_final))
    # Check that paths are absolute.
    assert vcdpickle_final[0] == '/'
    assert resultsdir_final[0] == '/'
    # Trace vs. notrace configuration.
    if dotrace:
        tracestr='trace'
        tracearg=['--trace']
        vcdfile='%s/trace.vcd' % resultsdir_final
    else:
        tracestr='notrace'
        tracearg=[]
        vcdfile = None
    # Build paths.
    simdir               = 'run_%s_%s_0.1' % (simbuild, tracestr)
    verilatordir         = 'default-verilator'
    verilator_executable = 'V%s' % design_cfg['toplevel']
    sim_executable_path  = os.path.abspath(os.path.join(builddir, simdir, verilatordir, verilator_executable))
    # Result paths.
    sim_cwd              = '%s/simulation-cwd' % resultsdir_final
    outputfile           = '%s/stdout.txt'     % resultsdir_final

    # Check whether executable path exists.
    if not os.path.exists(sim_executable_path):
        print("Error: Need {} to run this experiment. Design is {}.\n"
              "Please run 'make run_{}_{}' to build the binary in {}.\n"
              "Also be in the cellift dir so the path is right.\n".format(sim_executable_path, design, simbuild, tracestr, celliftdir))
        sys.exit(1)
    # Create the results directory if necessary.
    if not os.path.exists(sim_cwd):
        Path(sim_cwd).mkdir(parents=True, exist_ok=True)

    # Generate the ELF with potentially special values at tainted spots, and generate the taint file.
    sram_taintfile = write_taintfile(resultsdir_final, taintbits)
    my_env         = setup_sim_env(binary, design_cfg['bootrom_elf'], vcdfile, run_simtime, sram_taintfile, celliftdir)

    # Run and time the simulation.
    t0 = time.time()
    cmdline=[sim_executable_path]+tracearg
    subprocess.check_call(cmdline, cwd=sim_cwd, stdout=open(outputfile, 'w'), env=my_env)
    elapsed = time.time()-t0
    if dotrace:
        assert os.path.exists(vcdfile)
        with open(vcdfile, 'r') as vcdfd:
            vcdstr = vcdfd.read()
        vcd = VCDVCD(vcd_string=vcdstr)
    else:
        vcd=None

    # Read the synthesis data if requested
    if include_synth_log:
        synthlogfile = '%s.log' % sim_executable_path
        if not os.path.exists(synthlogfile):
            raise Exception('Unable to find the logfile saved from synthesis here: {}. If you are running with out instrumentation (Vanilla), did you forget to generate the synthesis log file?'.format(synthlogfile))
        with open(synthlogfile) as f:
            synthlog = f.read()
    else:
        synthlog = None

    # Save space by throwing out the original fst file
    if dotrace:
        assert os.path.exists(vcdfile)
        os.remove(vcdfile)

    print('Simulation & pickling done.')
    return {'vcd': vcd, 'elapsed': elapsed, 'stdout': open(outputfile).read(), 'synthlog': synthlog, 'env': my_env}
