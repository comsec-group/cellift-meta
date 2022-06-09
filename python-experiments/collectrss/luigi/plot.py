# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Plots the RSS of all designs.
# simulator: common.enums.Simulator (VERILATOR for instance).

import json
import luigi
import numpy as np
import os
import pickle
import pprint
import statistics

import matplotlib.pyplot as plt

from collectrss.luigi.collect import CollectRSS
from collectrss.common import get_design_names

from common.designcfgs import get_design_prettyname
from common.enums import Simulator, InstrumentationMethod
from common.taintfile import parse_taintfile

PLOT_PASSTHROUGH = False

pp = pprint.PrettyPrinter(indent=4)

rectangle_colors = {
    InstrumentationMethod.VANILLA:     'darkgreen',
    InstrumentationMethod.PASSTHROUGH: 'gray',
    InstrumentationMethod.CELLIFT:     '#1f77b4', # default blue
    InstrumentationMethod.GLIFT:       'orange', # default orange
}

class RSSPlot(luigi.Task):
    simulator = luigi.IntParameter()

    def __init__(self, *args, **kwargs):
        super(RSSPlot, self).__init__(*args, **kwargs)
        self.experiment_name = "perfbenchmark-plot-{}".format(self.simulator)

    def output(self):
        return luigi.LocalTarget('{}/results/{}.png'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name), format=luigi.format.Nop)

    def requires(self):
        run_params = {
            'simulator': self.simulator
        }
        return [CollectRSS(**run_params)]

    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        # Get the required file pointers.
        json_input = [json.load(x.open()) for x in self.input()][0] # json_input is a dict['yosys' or 'verilator'][design_name][instrumentation][binary] = simtime

        design_names = get_design_names()

        #####
        # Generate plot_data: a dict[design_name][instrumentation] = duration
        #####

        plot_data = {'yosys': {}, 'verilator': {}}
        for data_src in ['yosys', 'verilator']:
            for design_name in json_input[data_src]:
                plot_data[data_src][design_name] = {}
                for instrumentation, rss_val in json_input[data_src][design_name].items():
                    instrumentation_enum = InstrumentationMethod(int(instrumentation))
                    if instrumentation_enum == InstrumentationMethod.VANILLA and data_src == 'yosys':
                        continue
                    if instrumentation_enum == InstrumentationMethod.PASSTHROUGH and not PLOT_PASSTHROUGH:
                        continue
                    # Store the statistical results into plot_data
                    plot_data[data_src][design_name][instrumentation_enum] = rss_val/int(1e9)

        #####
        # Ticks and data
        #####

        pp.pprint("Yosys then Verilator")
        pp.pprint(plot_data['yosys'])
        pp.pprint(plot_data['verilator'])

        # Generate tick labels
        xlabels = []
        for design_name in design_names:
            tickstr = "{}".format(get_design_prettyname(design_name))
            xlabels.append(tickstr)

        #######
        # Plot the data
        #######

        spacing = 0.1
        left_offset = spacing
        width = 0.1

        if PLOT_PASSTHROUGH:
            xticks_yosys = []
            xticks_yosys.append( left_offset + 1.5*width              )
            xticks_yosys.append( left_offset + 4.5*width  + spacing   )
            xticks_yosys.append( left_offset + 7.5*width  + 2*spacing )
            xticks_yosys.append( left_offset + 10.5*width + 3*spacing )
            xticks_yosys.append( left_offset + 13.5*width + 4*spacing )

            xticks_verilator = []
            xticks_verilator.append( left_offset + 2*width                )
            xticks_verilator.append( left_offset + 5.5*width  + spacing   )
            xticks_verilator.append( left_offset + 9*width    + 2*spacing )
            xticks_verilator.append( left_offset + 13*width   + 3*spacing )
            xticks_verilator.append( left_offset + 16.5*width + 4*spacing )
        else:
            xticks_yosys = []
            xticks_yosys.append( left_offset + 1*width             )
            xticks_yosys.append( left_offset + 3*width + spacing   )
            xticks_yosys.append( left_offset + 5*width + 2*spacing )
            xticks_yosys.append( left_offset + 7*width + 3*spacing )
            xticks_yosys.append( left_offset + 9*width + 4*spacing )

            xticks_verilator = []
            xticks_verilator.append( left_offset + 1.5*width             )
            xticks_verilator.append( left_offset + 4*width   + spacing   )
            xticks_verilator.append( left_offset + 6.5*width + 2*spacing )
            xticks_verilator.append( left_offset + 9.5*width + 3*spacing )
            xticks_verilator.append( left_offset + 12*width  + 4*spacing )


        assert len(xticks_yosys) == len(xlabels)
        assert len(xticks_verilator) == len(xlabels)

        fig, all_axes = plt.subplots(3, 2, figsize=(12, 4), gridspec_kw={'height_ratios': [2, 4, 14]})

        # Ticks & grid
        yticks_minor = [
            np.arange(0, 242.5, 5),
            np.arange(0, 242.5, 5),
            np.arange(0, 242.5, 2.5)
        ]
        for row_id, each_row in enumerate(all_axes):
            for each_ax in each_row:
                each_ax.set_yticks(yticks_minor[row_id], minor=True)
                each_ax.yaxis.grid(True, which='minor', color='k', linewidth=0.4, linestyle='--', zorder=0)
                each_ax.yaxis.grid(True, which='minor', color='k', linewidth=0.4, linestyle='--', zorder=0)
                each_ax.yaxis.grid(True, which='major', color='k', linewidth=0.8, zorder=0)
                each_ax.yaxis.grid(True, which='major', color='k', linewidth=0.8, zorder=0)

        # Each subplot has its own data range.
        ax_lims = [
            [220, 240],
            [110, 150],
            [0, 55],
        ]
        assert len(ax_lims) == len(all_axes)

        for row_id, each_row in enumerate(all_axes):
            for each_ax in each_row:
                each_ax.set_ylim(ax_lims[row_id])

        # Remove axes between the two subplots.
        for each_ax in all_axes[0]:
            each_ax.spines['bottom'].set_visible(False)
        if len(all_axes) > 2:
            for each_row in all_axes[1:-1]:
                for each_ax in each_row:
                    each_ax.spines['bottom'].set_visible(False)
                    each_ax.spines['top'].set_visible(False)
        for each_ax in all_axes[-1]:
            each_ax.spines['top'].set_visible(False)

        # Data x coordinates
        if PLOT_PASSTHROUGH:
            rects_passthrough_yosys_x = [xticks_yosys[0]-1.0*width] + [xticks_yosys[1]-1.0*width] + [xticks_yosys[2]-1.0*width] + [xticks_yosys[3]-1.0*width] + [xticks_yosys[4]-1.0*width]
            rects_cellift_yosys_x     = [xticks_yosys[0]+0.0*width] + [xticks_yosys[1]+0.0*width] + [xticks_yosys[2]+0.0*width] + [xticks_yosys[3]+0.0*width] + [xticks_yosys[4]+0.0*width]
            rects_glift_yosys_x       = [xticks_yosys[0]+1.0*width] + [xticks_yosys[1]+1.0*width] + [xticks_yosys[2]+1.0*width] + [xticks_yosys[3]+1.0*width] + [xticks_yosys[4]+1.0*width]
        else:
            rects_cellift_yosys_x     = [xticks_yosys[0]-0.5*width] + [xticks_yosys[1]-0.5*width] + [xticks_yosys[2]-0.5*width] + [xticks_yosys[3]-0.5*width] + [xticks_yosys[4]-0.5*width]
            rects_glift_yosys_x       = [xticks_yosys[0]+0.5*width] + [xticks_yosys[1]+0.5*width] + [xticks_yosys[2]+0.5*width] + [xticks_yosys[3]+0.5*width] + [xticks_yosys[4]+0.5*width]

        if PLOT_PASSTHROUGH:
            rects_vanilla_verilator_x     = [xticks_verilator[0]-1.5*width] + [xticks_verilator[1]-1.5*width] + [xticks_verilator[2]-1.5*width] + [xticks_verilator[3]-1.0*width] + [xticks_verilator[4]-1.0*width]
            rects_passthrough_verilator_x = [xticks_verilator[0]-0.5*width] + [xticks_verilator[1]-0.5*width] + [xticks_verilator[2]-0.5*width] + [xticks_verilator[3]-  0*width] + [xticks_verilator[4]-  0*width]
            rects_cellift_verilator_x     = [xticks_verilator[0]+0.5*width] + [xticks_verilator[1]+0.5*width] + [xticks_verilator[2]+0.5*width] + [xticks_verilator[3]+1.0*width] + [xticks_verilator[4]+1.0*width]
            rects_glift_verilator_x       = [xticks_verilator[0]+1.5*width] + [xticks_verilator[1]+1.5*width] + [xticks_verilator[2]+1.5*width]
        else:
            rects_vanilla_verilator_x     = [xticks_verilator[0]-1.0*width] + [xticks_verilator[1]-1.0*width] + [xticks_verilator[2]-1.0*width] + [xticks_verilator[3]-0.5*width] + [xticks_verilator[4]-0.5*width]
            rects_cellift_verilator_x     = [xticks_verilator[0]+0.0*width] + [xticks_verilator[1]+0.0*width] + [xticks_verilator[2]+0.0*width] + [xticks_verilator[3]+0.5*width] + [xticks_verilator[4]+0.5*width]
            rects_glift_verilator_x       = [xticks_verilator[0]+1.0*width] + [xticks_verilator[1]+1.0*width] + [xticks_verilator[2]+1.0*width]

        # Data heights
        if PLOT_PASSTHROUGH:
            rects_passthrough_yosys_y = [plot_data['yosys'][d][InstrumentationMethod.PASSTHROUGH] for d in design_names]
        rects_cellift_yosys_y     = [plot_data['yosys'][d][InstrumentationMethod.CELLIFT]     for d in design_names]
        rects_glift_yosys_y       = [plot_data['yosys'][d][InstrumentationMethod.GLIFT]       for d in design_names]

        rects_vanilla_verilator_y     = [plot_data['verilator'][d][InstrumentationMethod.VANILLA] for d in design_names]
        if PLOT_PASSTHROUGH:
            rects_passthrough_verilator_y = [plot_data['verilator'][d][InstrumentationMethod.PASSTHROUGH] for d in design_names]
        rects_cellift_verilator_y     = [plot_data['verilator'][d][InstrumentationMethod.CELLIFT]     for d in design_names]
        rects_glift_verilator_y       = [plot_data['verilator']['ibex'][InstrumentationMethod.GLIFT], plot_data['verilator']['rocket'][InstrumentationMethod.GLIFT], plot_data['verilator']['pulpissimo'][InstrumentationMethod.GLIFT]]

        # Rectangles (yosys).
        for row_id, each_row in enumerate(all_axes):
            ax_yosys, ax_verilator = each_row
            # Yosys
            if PLOT_PASSTHROUGH:
                ax_yosys.bar(rects_passthrough_yosys_x, rects_passthrough_yosys_y, width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.PASSTHROUGH], ec='black')
            ax_yosys.bar(rects_cellift_yosys_x        , rects_cellift_yosys_y    , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.CELLIFT]    , ec='black')
            ax_yosys.bar(rects_glift_yosys_x          , rects_glift_yosys_y      , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.GLIFT]      , ec='black')
            # Verilator
            if row_id == 0:
                # Add labels once
                ax_verilator.bar(rects_vanilla_verilator_x        , rects_vanilla_verilator_y    , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.VANILLA]    , ec='black', label='Original')
                if PLOT_PASSTHROUGH:
                    ax_verilator.bar(rects_passthrough_verilator_x, rects_passthrough_verilator_y, width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.PASSTHROUGH], ec='black', label='Passthrough')
                ax_verilator.bar(rects_cellift_verilator_x        , rects_cellift_verilator_y    , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.CELLIFT]    , ec='black', label='CellIFT')
                ax_verilator.bar(rects_glift_verilator_x          , rects_glift_verilator_y      , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.GLIFT]      , ec='black', label='GLIFT')
            else:
                ax_verilator.bar(rects_vanilla_verilator_x        , rects_vanilla_verilator_y    , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.VANILLA]    , ec='black')
                if PLOT_PASSTHROUGH:
                    ax_verilator.bar(rects_passthrough_verilator_x, rects_passthrough_verilator_y, width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.PASSTHROUGH], ec='black')
                ax_verilator.bar(rects_cellift_verilator_x        , rects_cellift_verilator_y    , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.CELLIFT]    , ec='black')
                ax_verilator.bar(rects_glift_verilator_x          , rects_glift_verilator_y      , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.GLIFT]      , ec='black')

        if PLOT_PASSTHROUGH:
            fig.legend(ncol=2, loc='upper left', framealpha=1, fontsize=12)
        else:
            fig.legend(ncol=3, loc='upper left', framealpha=1, fontsize=12)

        # Remove ticks of the top subplot.
        for row_id, each_row in enumerate(all_axes):
            if row_id == len(all_axes)-1:
                each_row[0].set_xticks(xticks_yosys, xlabels, fontsize=13)
                each_row[1].set_xticks(xticks_verilator, xlabels, fontsize=13)
            else:
                each_row[0].set_xticks([])
                each_row[1].set_xticks([])

        # Y label
        all_axes[-1][0].set_ylabel(" ")
        fig.text(0.01, 0.47, 'Resident storage set high watermark (GB)', va='center', rotation='vertical', fontsize=12)

        plt.subplots_adjust(wspace=0, hspace=0)
        fig.tight_layout()

        plt.savefig("rss.png", dpi=300)
        plt.savefig("rss.pdf", dpi=300)
