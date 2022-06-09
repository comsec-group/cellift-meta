# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Plots the performance of all designs.
# simulator: common.enums.Simulator (VERILATOR for instance).

import json
import luigi
import numpy as np
import os
import pickle
import pprint

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from perfinstrum.luigi.collect import InstrumentationPerformanceCollect
from perfinstrum.common import get_design_names

from common.designcfgs import get_design_prettyname
from common.enums import Simulator, InstrumentationMethod

PLOT_PASSTHROUGH = False

pp = pprint.PrettyPrinter(indent=4)

rectangle_colors = {
    InstrumentationMethod.VANILLA:     'darkgreen',
    InstrumentationMethod.PASSTHROUGH: 'gray',
    InstrumentationMethod.CELLIFT:     '#1f77b4', # default blue
    InstrumentationMethod.GLIFT:       'orange', # default orange
}

class InstrumentationPerformancePlot(luigi.Task):
    simulator = luigi.IntParameter()

    def __init__(self, *args, **kwargs):
        super(InstrumentationPerformancePlot, self).__init__(*args, **kwargs)
        self.experiment_name = "perfinstr-plot-{}".format(self.simulator)

    def output(self):
        return luigi.LocalTarget('{}/results/{}.png'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name), format=luigi.format.Nop)

    def requires(self):
        run_params = {
            'simulator': self.simulator
        }
        return [InstrumentationPerformanceCollect(**run_params)]

    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        # Get the required file pointers.
        json_input = [json.load(x.open()) for x in self.input()][0]
        # json_input is a dict[design_name][instrumentation]['yosys' or 'verilator'] = yosys_duration_ms or synthesis_duration_ms

        #####
        # Generate plot_data: a dict[design_name][instrumentation] = (duration_yosys_ms, duration_verilator_ms)
        #####

        pp.pprint(json_input)

        design_names = get_design_names()

        plot_data = {'yosys': {}, 'verilator': {}}
        for design_name in design_names:
            plot_data['yosys'][design_name] = {}
            plot_data['verilator'][design_name] = {}
            for instrumentation, json_instr in json_input[design_name].items():
                instrumentation_enum = InstrumentationMethod(int(instrumentation))

                if 'yosys' in json_instr:
                    duration_yosys_ms = json_instr['yosys']
                    duration_yosys_minutes = duration_yosys_ms / 60000
                    plot_data['yosys'][design_name][instrumentation_enum] = duration_yosys_minutes

                if 'verilator' in json_instr:
                    duration_verilator_ms = json_instr['verilator']
                    duration_verilator_minutes = duration_verilator_ms / 60000
                    plot_data['verilator'][design_name][instrumentation_enum] = duration_verilator_minutes

        #####
        # Gen the labels
        #####

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

        xticks = []
        if PLOT_PASSTHROUGH:
            xticks.append( left_offset + 2*width              )
            xticks.append( left_offset + 6*width  + spacing   )
            xticks.append( left_offset + 10*width + 2*spacing )
            xticks.append( left_offset + 14*width + 3*spacing )
            xticks.append( left_offset + 18*width + 4*spacing )
        else:
            xticks.append( left_offset + 1.5*width              )
            xticks.append( left_offset + 4.5*width  + spacing   )
            xticks.append( left_offset + 7.5*width + 2*spacing )
            xticks.append( left_offset + 10.5*width + 3*spacing )
            xticks.append( left_offset + 13.5*width + 4*spacing )

        assert len(xticks) == len(xlabels), "xticks len: {}, xlabels len: {}.".format(len(xticks), len(xlabels))

        fig, all_axes = plt.subplots(2, 1, figsize=(8, 4), gridspec_kw={'height_ratios': [1, 13]})

        # Ticks & grid
        yticks_minor = [
            [194],
            np.arange(0, 242.5, 5)
        ]
        yticks_major = [
            [192, 196],
            np.arange(0, 242.5, 5)
        ]
        for each_ax_id, each_ax in enumerate(all_axes):
            each_ax.set_yticks(yticks_major[each_ax_id], minor=False)
            each_ax.set_yticks(yticks_minor[each_ax_id], minor=True)
            each_ax.yaxis.grid(True, which='minor', color='k', linewidth=0.4, linestyle='--', zorder=0)
            each_ax.yaxis.grid(True, which='minor', color='k', linewidth=0.4, linestyle='--', zorder=0)
            each_ax.yaxis.grid(True, which='major', color='k', linewidth=0.8, zorder=0)
            each_ax.yaxis.grid(True, which='major', color='k', linewidth=0.8, zorder=0)

        # Each subplot has its own data range.
        all_axes[0].set_ylim([192, 196])
        all_axes[-1].set_ylim([0, 90])

        # Remove axes between the two subplots.
        all_axes[0].spines['bottom'].set_visible(False)
        if len(all_axes) > 2:
            for each_ax in all_axes[1:-1]:
                each_ax.spines['bottom'].set_visible(False)
                each_ax.spines['top'].set_visible(False)
        all_axes[-1].spines['top'].set_visible(False)

        # Data x coordinates (yosys)
        if PLOT_PASSTHROUGH:
            rects_vanilla_yosys_x     = [xticks[0]-1.5*width] + [xticks[1]-1.5*width] + [xticks[2]-1.5*width] + [xticks[3]-1.5*width] + [xticks[4]-1.5*width]
            rects_passthrough_yosys_x = [xticks[0]-0.5*width] + [xticks[1]-0.5*width] + [xticks[2]-0.5*width] + [xticks[3]-0.5*width] + [xticks[4]-0.5*width]
            rects_cellift_yosys_x     = [xticks[0]+0.5*width] + [xticks[1]+0.5*width] + [xticks[2]+0.5*width] + [xticks[3]+0.5*width] + [xticks[4]+0.5*width]
            rects_glift_yosys_x       = [xticks[0]+1.5*width] + [xticks[1]+1.5*width] + [xticks[2]+1.5*width] + [xticks[3]+1.5*width] + [xticks[4]+1.5*width]
        else:
            rects_vanilla_yosys_x     = [xticks[0]-1*width] + [xticks[1]-1*width] + [xticks[2]-1*width] + [xticks[3]-1*width] + [xticks[4]-1*width]
            rects_cellift_yosys_x     = [xticks[0]+0*width] + [xticks[1]+0*width] + [xticks[2]+0*width] + [xticks[3]+0*width] + [xticks[4]+0*width]
            rects_glift_yosys_x       = [xticks[0]+1*width] + [xticks[1]+1*width] + [xticks[2]+1*width] + [xticks[3]+1*width] + [xticks[4]+1*width]

        # Data x coordinates (verilator)
        # Use the Yosys ticks (i.e., to support also showing the places that do not synth).
        # If not use the Yosys ticks, then make sure to realign the places that do not have GLIFT.
        if PLOT_PASSTHROUGH:
            rects_vanilla_verilator_x     = [xticks[0]-1.5*width] + [xticks[1]-1.5*width] + [xticks[2]-1.5*width] + [xticks[3]-1.5*width] + [xticks[4]-1.5*width]
            rects_passthrough_verilator_x = [xticks[0]-0.5*width] + [xticks[1]-0.5*width] + [xticks[2]-0.5*width] + [xticks[3]-0.5*width] + [xticks[4]-0.5*width]
            rects_cellift_verilator_x     = [xticks[0]+0.5*width] + [xticks[1]+0.5*width] + [xticks[2]+0.5*width] + [xticks[3]+0.5*width] + [xticks[4]+0.5*width]
            rects_glift_verilator_x       = [xticks[0]+1.5*width] + [xticks[1]+1.5*width] + [xticks[2]+1.5*width] + [xticks[3]+1.5*width] + [xticks[4]+1.5*width]
        else:
            rects_vanilla_verilator_x     = [xticks[0]-1*width] + [xticks[1]-1*width] + [xticks[2]-1*width] + [xticks[3]-1*width] + [xticks[4]-1*width]
            rects_cellift_verilator_x     = [xticks[0]+0*width] + [xticks[1]+0*width] + [xticks[2]+0*width] + [xticks[3]+0*width] + [xticks[4]+0*width]
            rects_glift_verilator_x       = [xticks[0]+1*width] + [xticks[1]+1*width] + [xticks[2]+1*width] + [xticks[3]+1*width] + [xticks[4]+1*width]
        # rects_glift_verilator_x     = [xticks[0]+1.5*width] +                                   [xticks[2]+1.5*width] + [xticks[3]+1.5*width]

        # Data heights (yosys)
        rects_vanilla_yosys_y     = [plot_data['yosys'][d][InstrumentationMethod.VANILLA]     for d in design_names]
        if PLOT_PASSTHROUGH:
            rects_passthrough_yosys_y = [plot_data['yosys'][d][InstrumentationMethod.PASSTHROUGH] for d in design_names]
        rects_cellift_yosys_y     = [plot_data['yosys'][d][InstrumentationMethod.CELLIFT]     for d in design_names]
        rects_glift_yosys_y       = [plot_data['yosys'][d][InstrumentationMethod.GLIFT]       for d in design_names]
        # Order is wrhong in this line. rects_glift_yosys_y_restrained_to_synthesizable = [plot_data['yosys']['ibex'][InstrumentationMethod.GLIFT], plot_data['yosys']['pulpissimo'][InstrumentationMethod.GLIFT], plot_data['yosys']['rocket'][InstrumentationMethod.GLIFT]]

        # Data heights (verilator)
        rects_vanilla_verilator_y     = [plot_data['verilator'][d][InstrumentationMethod.VANILLA]     for d in design_names]
        if PLOT_PASSTHROUGH:
            rects_passthrough_verilator_y = [plot_data['verilator'][d][InstrumentationMethod.PASSTHROUGH] for d in design_names]
        rects_cellift_verilator_y     = [plot_data['verilator'][d][InstrumentationMethod.CELLIFT]     for d in design_names]
        rects_glift_verilator_y       = [plot_data['verilator']['ibex'][InstrumentationMethod.GLIFT], plot_data['verilator']['rocket'][InstrumentationMethod.GLIFT], plot_data['verilator']['pulpissimo'][InstrumentationMethod.GLIFT], 100, 1000]

        pp.pprint(rects_glift_yosys_y)
        pp.pprint(rects_glift_verilator_y)

        # Rectangles (yosys).
        for ax_id, each_ax in enumerate(all_axes):
            each_ax.bar(rects_vanilla_yosys_x    , rects_vanilla_yosys_y    , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.VANILLA]    , ec='black')
            if PLOT_PASSTHROUGH:
                each_ax.bar(rects_passthrough_yosys_x, rects_passthrough_yosys_y, width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.PASSTHROUGH], ec='black')
            each_ax.bar(rects_cellift_yosys_x    , rects_cellift_yosys_y    , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.CELLIFT]    , ec='black')
            each_ax.bar(rects_glift_yosys_x      , rects_glift_yosys_y      , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.GLIFT]      , ec='black')

        # Rectangles (verilator).
        for each_ax_id, each_ax in enumerate(all_axes):
            each_ax.bar(rects_vanilla_verilator_x    , rects_vanilla_verilator_y    , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.VANILLA]    , ec='black', hatch="///", bottom=rects_vanilla_yosys_y)
            if PLOT_PASSTHROUGH:
                each_ax.bar(rects_passthrough_verilator_x, rects_passthrough_verilator_y, width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.PASSTHROUGH], ec='black', hatch="///", bottom=rects_passthrough_yosys_y)
            each_ax.bar(rects_cellift_verilator_x    , rects_cellift_verilator_y    , width, alpha=1, zorder=3, color=rectangle_colors[InstrumentationMethod.CELLIFT]    , ec='black', hatch="///", bottom=rects_cellift_yosys_y)

            # Do the coloring manually with glift.
            for design_id, design_name in enumerate(design_names):
                if design_name in ["cva6", "boom"]:
                    curr_color = "red"
                else:
                    curr_color=rectangle_colors[InstrumentationMethod.GLIFT]
                each_ax.bar(rects_glift_verilator_x[design_id], rects_glift_verilator_y[design_id], width, alpha=1, zorder=3, color=curr_color, ec='black', hatch="///", bottom=rects_glift_yosys_y[design_id])

        # Create the legend
        patches = []
        patches.append(mpatches.Patch(color=rectangle_colors[InstrumentationMethod.VANILLA]    , ec='black', label='Original'))
        patches.append(mpatches.Patch(color=rectangle_colors[InstrumentationMethod.CELLIFT]    , ec='black', label='CellIFT'))
        patches.append(mpatches.Patch(color="red"                                              , ec='black', label='GLIFT (failed)'))
        if PLOT_PASSTHROUGH:
            patches.append(mpatches.Patch(color=rectangle_colors[InstrumentationMethod.PASSTHROUGH], ec='black', label='Passthrough'))
        patches.append(mpatches.Patch(color=rectangle_colors[InstrumentationMethod.GLIFT]      , ec='black', label='GLIFT'))
        fig.legend(ncol=2, handles=patches, framealpha=1, loc="upper center")
        # Remove ticks of the top subplot.
        for ax_id, each_ax in enumerate(all_axes):
            if ax_id == len(all_axes)-1:
                each_ax.set_xticks(xticks, xlabels)
            else:
                each_ax.set_xticks([])

        # Y label
        all_axes[0].set_ylabel(" ")
        fig.text(0.02, 0.52, 'Instrumentation and synthesis duration (minutes)', va='center', rotation='vertical')
    
        fig.tight_layout()

        plt.savefig("perfinstrum.png", dpi=300)
        plt.savefig("perfinstrum.pdf", dpi=300)
