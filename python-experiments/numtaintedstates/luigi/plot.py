# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Plots the max number of tainted states (over time) for the parameters given below:
# simulator:         common.enums.Simulator (VERILATOR for instance).
# design_name:       see JSON keys in CELLIFT_DESIGN_PROCESSING_ROOT.
# simtime:           num cycles to run, including lead cycles (for CVA6, for instance).

import json
import luigi
import numpy as np
import os

import matplotlib.pyplot as plt

from common.enums import Simulator, InstrumentationMethod
from common.benchmarks import get_benchmark_names, get_benchmark_path, get_benchmark_taint_path
from common.taintfile import parse_taintfile

from numtaintedstates.luigi.maxtaintssinglebin import MaxTaintedStatesSingleBin

plt.rcParams.update({'font.size': 12})

rectangle_colors = {
    InstrumentationMethod.VANILLA:     'darkgreen',
    InstrumentationMethod.PASSTHROUGH: 'gray',
    InstrumentationMethod.CELLIFT:     '#1f77b4', # default blue
    InstrumentationMethod.GLIFT:       'orange', # default orange
}

class PlotMaxTaintedStates(luigi.Task):
    simulator        = luigi.IntParameter()
    simtime          = luigi.IntParameter()
    design_name      = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super(PlotMaxTaintedStates, self).__init__(*args, **kwargs)
        self.experiment_name = "plotmaxtaintedstates-{}-{}-{}".format(self.simulator, self.simtime, self.design_name)

        # Predetermine benchmark paths, taint bits and
        self.benchmark_names = get_benchmark_names()
        self.benchmark_paths = list(map(lambda b: get_benchmark_path(self.design_name, b), self.benchmark_names))
        taint_paths = list(map(lambda b: get_benchmark_taint_path(self.design_name, b), self.benchmark_names))
        self.taintbits_list = list(map(parse_taintfile, taint_paths))

    def output(self):
        return luigi.LocalTarget('{}/experiments/{}.json'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name), format=luigi.format.Nop)

    def requires(self):
        ret = []
        # With CellIFT
        ret += [MaxTaintedStatesSingleBin(simulator=self.simulator, taintbits=curr_iter[0], instrumentation=InstrumentationMethod.CELLIFT, binary=curr_iter[1], simtime=self.simtime, design_name=self.design_name) for curr_iter in zip(self.taintbits_list, self.benchmark_paths)]
        # With GLIFT
        ret += [MaxTaintedStatesSingleBin(simulator=self.simulator, taintbits=curr_iter[0], instrumentation=InstrumentationMethod.GLIFT, binary=curr_iter[1], simtime=self.simtime, design_name=self.design_name) for curr_iter in zip(self.taintbits_list, self.benchmark_paths)]
        return ret

    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        # Get the json result.
        json_data = [json.load(x.open()) for x in self.input()]

        xlabels = ["{}".format(b) for b in self.benchmark_names]

        cellift_data = [json_data[i] for i in range(len(self.benchmark_names))]
        glift_data   = [json_data[i] for i in range(len(self.benchmark_names), 2*len(self.benchmark_names))]

        #######
        # Plot the data
        #######

        X = np.arange(len(cellift_data))
        width = 0.35

        fig = plt.figure(figsize=(12, 3.2))
        ax = fig.gca()

        # Leave some space fot the legend
        ax.set_ylim([0, 2600])
        ax.yaxis.grid(True, which='major', color='k', linewidth=0.8, zorder=0)

        rects_cellift = ax.bar(X - width/2, cellift_data, width, alpha=1, color=rectangle_colors[InstrumentationMethod.CELLIFT], label='CellIFT', zorder=3, ec='black')
        rects_glift   = ax.bar(X + width/2, glift_data,   width, alpha=1, color=rectangle_colors[InstrumentationMethod.GLIFT]  , label='GLIFT'  , zorder=3, ec='black')

        ax.set_ylabel('Taint bits (high watermark)', fontsize=14)
        ax.set_xticks(X, xlabels, fontsize=14)
        ax.legend(ncol=1, framealpha=1)

        fig.tight_layout()

        plt.savefig("numtaintedstates.png", dpi=300)
        plt.savefig("numtaintedstates.pdf", dpi=300)
