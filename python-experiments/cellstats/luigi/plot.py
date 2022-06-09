# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Plots the performance of all designs.
# simulator: common.enums.Simulator (VERILATOR for instance).

import json
import luigi
import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from collections import defaultdict

from cellstats.luigi.collect import CollectCellStats
from cellstats.common import get_design_names, get_cell_type_by_str, cell_types, get_instrumentation_methods_nopassthrough

from common.designcfgs import get_design_prettyname
from common.enums import Simulator, InstrumentationMethod, instrumentation_method_to_pretty_string

rectangle_colors_stats = {
    "ibex" : {
        InstrumentationMethod.VANILLA: '#754C00',
        InstrumentationMethod.CELLIFT: '#D18700',
        InstrumentationMethod.GLIFT:   '#FFB52E'
    },
    "cva6" : {
        InstrumentationMethod.VANILLA: '#51087E',
        InstrumentationMethod.CELLIFT: '#880ED4',
        InstrumentationMethod.GLIFT:   '#B24BF3'
    },
    "pulpissimo" : {
        InstrumentationMethod.VANILLA: '#007500',
        InstrumentationMethod.CELLIFT: '#00D100',
        InstrumentationMethod.GLIFT:   '#2EFF2E'
    },
    "rocket" : {
        InstrumentationMethod.VANILLA: '#000075',
        InstrumentationMethod.CELLIFT: '#0000D1',
        InstrumentationMethod.GLIFT:   '#2E2EFF'
    },
    "boom" : {
        InstrumentationMethod.VANILLA: '#3B3B3B',
        InstrumentationMethod.CELLIFT: '#696969',
        InstrumentationMethod.GLIFT:   '#979797'
    }
}

class CellStatsPlot(luigi.Task):
    simulator = luigi.IntParameter()

    def __init__(self, *args, **kwargs):
        super(CellStatsPlot, self).__init__(*args, **kwargs)
        self.experiment_name = "cellstats-plot-{}".format(self.simulator)

    def output(self):
        return luigi.LocalTarget('{}/results/{}.png'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name), format=luigi.format.Nop)

    def requires(self):
        run_params = {
            'simulator': self.simulator
        }
        return [CollectCellStats(**run_params)]

    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        # Get the required file pointers.
        json_input = [json.load(x.open()) for x in self.input()][0]
        # json_input is dict[design_name][instrumentation][cell_type]=cell_count

        design_names = get_design_names()

        # Index using the InstrumentationMethod enum instead of the representing string, and complete with default value 0.
        plot_data = defaultdict(lambda : defaultdict(lambda : defaultdict(int)))
        for design_name in design_names:
            for instrumentation_method in get_instrumentation_methods_nopassthrough():
                assert design_name in json_input, f"Missing design {design_name}"
                assert str(int(instrumentation_method)) in json_input[design_name], f"Missing method {str(int(instrumentation_method))} for design {design_name}"
                for cell_type in cell_types:
                    if cell_type in json_input[design_name][str(int(instrumentation_method))]:
                        plot_data[design_name][instrumentation_method][cell_type] = json_input[design_name][str(int(instrumentation_method))][cell_type]
                    else:
                        # Even though plot_data is a defaultdict, we use the .values() method, therefore we must specify the zero values.
                        plot_data[design_name][instrumentation_method][cell_type] = 0

        #######
        # Ticks and labels
        #######

        spacing = 0.3
        left_offset = spacing
        width = 0.1

        xticks = []
        xlabels = []
        for cell_type_id, cell_type in enumerate(cell_types):
            # 15 bars per tick (5 designs, 3 instrumentations per design).
            xticks.append(left_offset + 7.5*width + cell_type_id*(15*width + spacing))
            xlabels.append(cell_type)

        #######
        # Plot the data
        #######

        fig = plt.figure(figsize=(12, 2.95))
        ax = fig.gca()

        rects_x = defaultdict(lambda : defaultdict(list))

        # Data x coordinates
        for cell_type_id, cell_type in enumerate(cell_types):
            # 7 is half of the 15 bars per tick, so we center the bars around the corresponding tick.
            curr_x = xticks[cell_type_id] - 7*width
            for design_name in design_names:
                for instrumentation_method in get_instrumentation_methods_nopassthrough():
                    # x coordinate
                    # print("{} {}: {}".format(design_name, instrumentation_method_to_pretty_string(instrumentation_method), curr_x))
                    rects_x[design_name][instrumentation_method].append(curr_x)
                    curr_x += width

        # Ticks & grid
        ax.yaxis.grid(True, which='minor', color='k', linewidth=0.4, linestyle='--', zorder=0)
        ax.yaxis.grid(True, which='major', color='k', linewidth=0.8, zorder=0)

        # Draw the bars
        for design_name in design_names:
            for instrumentation_method in get_instrumentation_methods_nopassthrough():
                ax.bar(rects_x[design_name][instrumentation_method], list(plot_data[design_name][instrumentation_method].values()), width, alpha=1, zorder=3, color=rectangle_colors_stats[design_name][instrumentation_method])

        # Legend
        patches = []
        for design_name in design_names:
            for instrumentation_method in get_instrumentation_methods_nopassthrough():
                patches.append(mpatches.Patch(color=rectangle_colors_stats[design_name][instrumentation_method], label='{} ({})'.format(get_design_prettyname(design_name), instrumentation_method_to_pretty_string(InstrumentationMethod.VANILLA if instrumentation_method==InstrumentationMethod.PASSTHROUGH else instrumentation_method))))
        fig.legend(ncol=5, handles=patches, framealpha=1, fontsize=8)

        # X ticks and labels
        ax.set_xticks(xticks, xlabels, rotation=45, ha="right", fontsize=8)

        # Y label
        ax.set_ylabel("Number of cells of each type")

        plt.yscale("log")
        fig.tight_layout()

        plt.savefig("cellstats.png", dpi=300)
        plt.savefig("cellstats.pdf", dpi=300)
