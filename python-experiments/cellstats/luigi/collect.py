# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Collects the cell stats for all designs.
# simulator: common.enums.Simulator (VERILATOR for instance).

import json
import luigi
import os
import re

from collections import defaultdict

from cellstats.common import get_design_names, get_cell_type_by_str, cell_types, get_instrumentation_methods_nopassthrough

from common.enums import Simulator, InstrumentationMethod, instrumentation_method_to_string, instrumentation_method_to_pretty_string
from common.designcfgs import get_design_cellift_path

class CollectCellStats(luigi.Task):
    simulator = luigi.IntParameter()

    def __init__(self, *args, **kwargs):
        super(CollectCellStats, self).__init__(*args, **kwargs)
        self.experiment_name = "collect-cellstats-all-{}".format(self.simulator)
        self.design_names = get_design_names()

    def output(self):
        return luigi.LocalTarget('{}/experiments/{}.json'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name), format=luigi.format.Nop)

    # Leaf
    def requires(self):
        return None

    # @return a dict[design_name][instrumentation] = (yosys_duration_ms, synthesis_duration_ms)
    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        ######
        # Get the paths to the stats of all designs.
        ######

        # stat_logfile_paths = dict[design_name][instrumentation]=stat_logfile_path
        stat_logfile_paths = defaultdict(lambda : defaultdict(dict))

        for design_name in self.design_names:
            design_cellift_path = get_design_cellift_path(design_name)
            for instrumentation_method in get_instrumentation_methods_nopassthrough():
                stat_logfile_paths[design_name][instrumentation_method] = os.path.join(design_cellift_path, "statistics", "{}.log".format(instrumentation_method_to_string(instrumentation_method)))

        ######
        # For each stat file, extract the cell statistics.
        ######

        # stat_dict = dict[design_name][instrumentation][cell_type]=cell_count
        stat_dict = defaultdict(lambda : defaultdict(lambda : defaultdict(int)))

        # Regex start and stop markers.
        end_marker = r"tstpstart_stat_tstpend"
        interest_region_regex = r"^\s*Number of cells:\s*\d*\s*$.+?(?="+end_marker+r")"
        cell_regex = r"^\s*\$(\w+)\s*(\d+)\s*$"

        # Read all the present cell types
        for design_name in self.design_names:
            for instrumentation_method in get_instrumentation_methods_nopassthrough():
                print(f"Current instr: {instrumentation_method}.")
                # Read the statistics logfile.
                with open(stat_logfile_paths[design_name][instrumentation_method], "r") as f:
                    logfile_content = f.read()
                matches = re.findall(interest_region_regex, logfile_content, flags=re.MULTILINE|re.DOTALL)
                assert matches, "Could not find the cell statistics summary for {} {}".format(design_name, instrumentation_method_to_pretty_string(instrumentation_method))
                assert len(matches) == 1, "Multiple cell statistics summaries for {} {}".format(design_name, instrumentation_method_to_pretty_string(instrumentation_method))
                matchlines = matches[0].split('\n')

                # Start by finding the last occurrence of `Number of cells`.
                for i in range(len(matchlines)-1, -1, -1):
                    if "Number of cells:" in matchlines[i]:
                        matchlines = matchlines[i+1:-1]
                        break
                for matchline in matchlines:
                    cellmatches = re.findall(cell_regex, matchline)
                    # There should only be exactly one match per line, or zero if this line does not indicate a cell.
                    if len(cellmatches) == 1:
                        curr_match = cellmatches[0]
                        cell_str, cell_count = curr_match
                        cell_type = get_cell_type_by_str(cell_str)
                        stat_dict[design_name][instrumentation_method][cell_type] += int(cell_count)

        with self.output().temporary_path() as outfile_fn:
            json.dump(stat_dict, open(outfile_fn, 'w'))
