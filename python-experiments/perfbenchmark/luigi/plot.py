# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Plots the performance of all designs.
# simulator:         common.enums.Simulator (VERILATOR for instance).
# simtime:           num cycles to run, including lead cycles (for CVA6, for instance).

import luigi
import numpy as np
import os
import pickle
import statistics
import sys

import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path

from perfbenchmark.luigi.alldesigns import AllDesignsPerformanceExperiment
from perfbenchmark.common import get_design_names

from common.designcfgs import get_design_prettyname
from common.enums import Simulator, InstrumentationMethod, instrumentation_method_to_short_string
from common.taintfile import parse_taintfile

PLOT_PASSTHROUGH = False

rectangle_colors = {
    InstrumentationMethod.VANILLA:     'darkgreen',
    InstrumentationMethod.PASSTHROUGH: 'gray',
    InstrumentationMethod.CELLIFT:     '#1f77b4', # default blue
    InstrumentationMethod.GLIFT:       'orange', # default orange
}

class PerformancePlot(luigi.Task):
    simulator = luigi.IntParameter()
    simtime   = luigi.IntParameter()

    def __init__(self, *args, **kwargs):
        super(PerformancePlot, self).__init__(*args, **kwargs)
        self.experiment_name = "perfbenchmark-plot-{}-{}".format(self.simulator, self.simtime)

    def output(self):
        return luigi.LocalTarget('{}/results/{}.png'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name), format=luigi.format.Nop)

    def requires(self):
        run_params = {
            'simulator': self.simulator,
            'simtime': self.simtime
        }
        return [AllDesignsPerformanceExperiment(**run_params)]

    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        # Get the required file pointers.
        pickle_input = [pickle.load(x.open()) for x in self.input()][0] # pickle_input is a dict[design_name][instrumentation][binary] = simtime

        design_names = get_design_names()

        #####
        # Generate plot_data: a dict[design_name][instrumentation] = (avg, standard_deviation) <for the ratio with the vanilla target>
        #####

        plot_data = {}
        for design_name in pickle_input:
            plot_data[design_name] = {}
            for instrumentation, binary_timings in pickle_input[design_name].items():
                if instrumentation == InstrumentationMethod.VANILLA:
                    continue
                if instrumentation == InstrumentationMethod.PASSTHROUGH and not PLOT_PASSTHROUGH:
                    continue
                # Here, binary_timings is pickle_input[design_name][instrumentation], i.e. a dict[binary] = simtime
                duration_ratios = []
                for binary in binary_timings:
                    duration_ratios.append(binary_timings[binary]/pickle_input[design_name][int(InstrumentationMethod.VANILLA)][binary])

                # Compute the average ratio
                avg_ratio = statistics.harmonic_mean(duration_ratios)
                stdev_ratio = statistics.stdev(duration_ratios)
                # Store the statistical results into plot_data
                plot_data[design_name][instrumentation] = avg_ratio, stdev_ratio

        #####
        # Ticks and data
        #####

        # Generate tick labels
        xlabels = []
        for design_name in design_names:
            tickstr = "{}".format(get_design_prettyname(design_name))
            xlabels.append(tickstr)

        #######
        # Plot the data
        #######

        width = 0.1
        spacing = 2*width
        left_offset = spacing
        xticks = []

        if PLOT_PASSTHROUGH:
            assert False, "Perfbenchmark xticks to calculate!"
        else:
            xticks.append( left_offset + 1.0*width               )
            xticks.append( left_offset + 3.0*width   + spacing   )
            xticks.append( left_offset + 5.0*width   + 2*spacing )
            xticks.append( left_offset + 6.5*width   + 3*spacing )
            xticks.append( left_offset + 7.5*width   + 4*spacing )

        assert len(xticks) == len(xlabels)

        fig, all_axes = plt.subplots(2, 1, figsize=(8, 4), gridspec_kw={'height_ratios': [10, 20]})

        # Ticks & grid
        yticks_minor = [
            np.arange(300, 400, 2.5),
            np.arange(0, 300, 2.5)
        ]
        yticks_major = [
            np.arange(0, 1000, 10),
            np.arange(0, 1000, 10)
        ]
        for each_ax_id, each_ax in enumerate(all_axes):
            each_ax.set_yticks(yticks_major[each_ax_id], minor=False)
            each_ax.set_yticks(yticks_minor[each_ax_id], minor=True)
            each_ax.yaxis.grid(True, which='minor', color='k', linewidth=0.4, linestyle='--', zorder=0)
            each_ax.yaxis.grid(True, which='minor', color='k', linewidth=0.4, linestyle='--', zorder=0)
            each_ax.yaxis.grid(True, which='major', color='k', linewidth=0.8, zorder=0)
            each_ax.yaxis.grid(True, which='major', color='k', linewidth=0.8, zorder=0)

        # Each subplot has its own data range.
        all_axes[0].set_ylim([300, 360])
        all_axes[-1].set_ylim([0, 120])

        # Remove axes between the two subplots.
        all_axes[0].spines['bottom'].set_visible(False)
        if len(all_axes) > 2:
            for each_ax in all_axes[1:-1]:
                each_ax.spines['bottom'].set_visible(False)
                each_ax.spines['top'].set_visible(False)
        all_axes[-1].spines['top'].set_visible(False)

        # Data x coordinates
        if PLOT_PASSTHROUGH:
            rects_passthrough_x = [xticks[0]-1.0*width] + [xticks[1]-1.0*width] + [xticks[2]-1.0*width] + [xticks[3]-0.5*width] + [xticks[4]-0.5*width]
            rects_cellift_x     = [xticks[0]+0.0*width] + [xticks[1]+0.0*width] + [xticks[2]+0.0*width] + [xticks[3]+0.5*width] + [xticks[4]+0.5*width]
            rects_glift_x       = [xticks[0]+1.0*width] + [xticks[1]+1.0*width] + [xticks[2]+1.0*width]
        else:
            rects_cellift_x     = [xticks[0]-0.5*width] + [xticks[1]-0.5*width] + [xticks[2]-0.5*width] + [xticks[3]+0.0*width] + [xticks[4]+0.0*width]
            rects_glift_x       = [xticks[0]+0.5*width] + [xticks[1]+0.5*width] + [xticks[2]+0.5*width]

        # Data heights
        if PLOT_PASSTHROUGH:
            rects_passthrough_y = [plot_data[d][InstrumentationMethod.PASSTHROUGH][0] for d in design_names]
        rects_cellift_y     = [plot_data[d][InstrumentationMethod.CELLIFT][0]     for d in design_names]
        rects_glift_y       = [plot_data["ibex"][InstrumentationMethod.GLIFT][0], plot_data["rocket"][InstrumentationMethod.GLIFT][0], plot_data["pulpissimo"][InstrumentationMethod.GLIFT][0]]

        # Data stdev
        if PLOT_PASSTHROUGH:
            rects_passthrough_err = [plot_data[d][InstrumentationMethod.PASSTHROUGH][1] for d in design_names]
        rects_cellift_err     = [plot_data[d][InstrumentationMethod.CELLIFT][1]     for d in design_names]
        rects_glift_err       = [plot_data["ibex"][InstrumentationMethod.GLIFT][1], plot_data["rocket"][InstrumentationMethod.GLIFT][1], plot_data["pulpissimo"][InstrumentationMethod.GLIFT][1]]

        # Rectangles (yosys).
        for ax_id, each_ax in enumerate(all_axes):
            if ax_id == 0:
                if PLOT_PASSTHROUGH:
                    each_ax.bar(rects_passthrough_x, rects_passthrough_y, width, alpha=1, zorder=3, yerr=rects_passthrough_err, color=rectangle_colors[InstrumentationMethod.PASSTHROUGH], ec='black', label="Passthrough")
                each_ax.bar(rects_cellift_x    , rects_cellift_y    , width, alpha=1, zorder=3, yerr=rects_cellift_err    , color=rectangle_colors[InstrumentationMethod.CELLIFT]    , ec='black', label="CellIFT")
                each_ax.bar(rects_glift_x      , rects_glift_y      , width, alpha=1, zorder=3, yerr=rects_glift_err      , color=rectangle_colors[InstrumentationMethod.GLIFT]      , ec='black', label="GLIFT")
            else:
                if PLOT_PASSTHROUGH:
                    each_ax.bar(rects_passthrough_x, rects_passthrough_y, width, alpha=1, zorder=3, yerr=rects_passthrough_err, color=rectangle_colors[InstrumentationMethod.PASSTHROUGH], ec='black')
                each_ax.bar(rects_cellift_x    , rects_cellift_y    , width, alpha=1, zorder=3, yerr=rects_cellift_err    , color=rectangle_colors[InstrumentationMethod.CELLIFT]    , ec='black')
                each_ax.bar(rects_glift_x      , rects_glift_y      , width, alpha=1, zorder=3, yerr=rects_glift_err      , color=rectangle_colors[InstrumentationMethod.GLIFT]      , ec='black')

        if PLOT_PASSTHROUGH:
            fig.legend(ncol=3, framealpha=1)
        else:
            fig.legend(ncol=2, framealpha=1)

        # Remove ticks of the top subplot.
        for ax_id, each_ax in enumerate(all_axes):
            if ax_id == len(all_axes)-1:
                each_ax.set_xticks(xticks, xlabels)
            else:
                each_ax.set_xticks([])

        # Y label
        all_axes[0].set_ylabel(" ")
        fig.text(0.015, 0.50, 'Slowdown relative to original (non-instrumented) design', va='center', rotation='vertical')

        plt.subplots_adjust(wspace=0, hspace=0)
        fig.tight_layout()

        print("rects_glift_y", rects_glift_y)

        plt.savefig("slowdowns.png", dpi=300)
        plt.savefig("slowdowns.pdf", dpi=300)
