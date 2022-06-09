# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Collects the RSS for all designs.
# simulator: common.enums.Simulator (VERILATOR for instance).

import json
import luigi
import os

from collections import defaultdict

from common.luigi.checkdesignhsb import CheckDesignHSB
from collectrss.common import get_design_names, get_rss

from common.enums import Simulator, InstrumentationMethod
from common.designcfgs import get_design_cellift_path, get_instrumentation_methods_per_design_yosys, get_instrumentation_methods_per_design_verilator

class CollectRSS(luigi.Task):
    simulator = luigi.IntParameter()

    def __init__(self, *args, **kwargs):
        super(CollectRSS, self).__init__(*args, **kwargs)
        self.experiment_name = "collect-rss-all-{}".format(self.simulator)
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

    # @return a dict[design_name][instrumentation]['yosys' or 'verilator'] = yosys_rss or synthesis_rss
    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        ######
        # Get the max RSS for all the supported instrumentation methods.
        ######

        collected_rss_yosys = defaultdict(lambda : defaultdict(dict))
        collected_rss_verilator = defaultdict(lambda : defaultdict(dict))

        for design_name in self.design_names:
            # Yosys RSS
            instrumentation_methods_yosys = get_instrumentation_methods_per_design_yosys(design_name)
            design_cellift_path = get_design_cellift_path(design_name)
            for instrumentation_method in instrumentation_methods_yosys:
                if instrumentation_method != InstrumentationMethod.VANILLA:
                    collected_rss_yosys[design_name][instrumentation_method] = get_rss(design_name, instrumentation_method, False, False)
                    print("Collected instr rss {} {}: {}".format(design_name, instrumentation_method, collected_rss_yosys[design_name][instrumentation_method]/1000000000))
            # Verilator RSS
            instrumentation_methods_verilator = get_instrumentation_methods_per_design_verilator(design_name)
            design_cellift_path = get_design_cellift_path(design_name)
            for instrumentation_method in instrumentation_methods_verilator:
                collected_rss_verilator[design_name][instrumentation_method] = get_rss(design_name, instrumentation_method, False, True)
                print("Collected synth rss {} {}: {}".format(design_name, instrumentation_method, collected_rss_verilator[design_name][instrumentation_method]/1000000000))

        with self.output().temporary_path() as outfile_fn:
            json.dump({'yosys': collected_rss_yosys, 'verilator': collected_rss_verilator}, open(outfile_fn, 'w'))
