# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Collects the instrumentation performance for all designs.
# simulator: common.enums.Simulator (VERILATOR for instance).

import json
import luigi
import os
import re

from collections import defaultdict
from pathlib import Path

from common.luigi.checkdesignhsb import CheckDesignHSB
from perfinstrum.common import get_design_names, get_verilator_synthesis_duration

from common.enums import Simulator, InstrumentationMethod, instrumentation_method_to_string, instrumentation_method_to_pretty_string
from common.designcfgs import get_design_cellift_path, get_instrumentation_methods_per_design_yosys, get_instrumentation_methods_per_design_verilator

class InstrumentationPerformanceCollect(luigi.Task):
    simulator = luigi.IntParameter()

    def __init__(self, *args, **kwargs):
        super(InstrumentationPerformanceCollect, self).__init__(*args, **kwargs)
        self.experiment_name = "perfinstrum-all-{}".format(self.simulator)
        self.design_names = get_design_names()

    def output(self):
        return luigi.LocalTarget('{}/experiments/{}.json'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name), format=luigi.format.Nop)

    def requires(self):
        ret = []
        for design_name in self.design_names:
            instrumentation_methods = get_instrumentation_methods_per_design_verilator(design_name)

            for instrumentation_method in instrumentation_methods:
                run_params = {
                    "instrumentation" : instrumentation_method,
                    "design_name"     : design_name,
                    "dotrace"         : False,
                }
                ret.append(CheckDesignHSB(**run_params))
        return ret

    # @return a dict[design_name][instrumentation]['yosys' or 'verilator'] = yosys_duration_ms or synthesis_duration_ms
    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        ######
        # Get the Yosys instrumentation duration and the Verilator synthesis duration.
        ######

        collected_durations = defaultdict(lambda : defaultdict(lambda : defaultdict(dict)))

        for design_name in self.design_names:
            instrumentation_methods_yosys = get_instrumentation_methods_per_design_yosys(design_name)

            design_cellift_path = get_design_cellift_path(design_name)
            for instrumentation_method in instrumentation_methods_yosys:
                # 1. Get the Yosys instrumentation duration.
                if instrumentation_method == InstrumentationMethod.VANILLA:
                    first_timestamp = 0
                    last_timestamp = 0
                else:
                    logfile_path = os.path.join(design_cellift_path, 'generated', 'out', '{}.sv.log'.format(instrumentation_method_to_string(instrumentation_method)))
                    with open(logfile_path, "r") as logfile:
                        all_loglines = logfile.readlines()
                        # Find the first and the last timestamp
                        first_timestamp = -1
                        last_timestamp = -1
                        for line in all_loglines:
                            curr_search_first = re.search(r"^tstpstart_hierarchy_tstpend\s*:\s*(\d+)\.", line)
                            curr_search_last = re.search(r"^tstpstart_end_tstpend\s*:\s*(\d+)\.", line)
                            if curr_search_first:
                                first_timestamp = int(curr_search_first.group(1))
                            if curr_search_last:
                                last_timestamp = int(curr_search_last.group(1))

                        assert first_timestamp != -1
                        assert last_timestamp != -1
                yosys_duration_ms = last_timestamp-first_timestamp
                print("Duration (yosys) {} {}:".format(design_name, instrumentation_method_to_pretty_string(instrumentation_method)), yosys_duration_ms)
                collected_durations[design_name][instrumentation_method]['yosys'] = yosys_duration_ms

            # 2. Get the Verilator synthesis duration.
            instrumentation_methods_verilator = get_instrumentation_methods_per_design_verilator(design_name)
            for instrumentation_method in instrumentation_methods_verilator:
                verilator_duration_s = get_verilator_synthesis_duration(design_name, instrumentation_method, False, 'synth')
                verilator_duration_ms = 1000*verilator_duration_s
                print("Duration (verilator) {} {}:".format(design_name, instrumentation_method_to_pretty_string(instrumentation_method)), yosys_duration_ms)
                collected_durations[design_name][instrumentation_method]['verilator'] = verilator_duration_ms

        with self.output().temporary_path() as outfile_fn:
            json.dump(collected_durations, open(outfile_fn, 'w'))
