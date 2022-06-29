# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# For a given design, runs a experiment to get the number of bits tainted at each cycle,
# and data values. Save resulting matrix and metadata in a pickle.
# simulator:         common.enums.Simulator (VERILATOR for instance).
# taintbits:         list of pairs (addr, taint assignment).
# binary:            path to the simulation binary.
# design_name:       see JSON keys in CELLIFT_DESIGN_PROCESSING_ROOT.
# simtime:           num cycles to run, including lead cycles (for CVA6, for instance).
# instrumentation:   list of common.enums.InstrumentationMethod.

import json
import pickle
import luigi
import os
import numpy

from luigi.util import inherits

from listtaintedelems.luigi.countelems import CountElems
from common.enums import Simulator, InstrumentationMethod
from common.params_to_str import taintstr, binarycrc
from common.vcdsignals import get_taintmatrix, matrix_uniq_cols
from common.luigi.simulationrun import SimulationRun

import matplotlib.pyplot as plt

#####
# Luigi task
#####

class SignalsMatrixList(luigi.Task):
    simulator        = luigi.IntParameter()
    taintbits        = luigi.ListParameter()
    binary           = luigi.Parameter()
    simtime          = luigi.IntParameter()
    design_name      = luigi.Parameter()
    instrumentation  = luigi.ListParameter()
    expname          = luigi.Parameter()
    picktaint        = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super(SignalsMatrixList, self).__init__(*args, **kwargs)
        self.experiment_name = "signalsmatrixlistpickle-{}-{}-{}-{}-{}-{}".format(self.simulator, taintstr(self.taintbits), binarycrc(self.binary), self.simtime, self.design_name, self.instrumentation)

    def output(self):
        return luigi.LocalTarget('{}/experiments/{}-{}-{}.pickle'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name, self.expname, self.picktaint), format=luigi.format.Nop)

    def requires(self):
        return [SimulationRun(simulator=self.simulator, taintbits=self.taintbits, instrumentation=self.instrumentation, binary=self.binary, simtime=self.simtime, design_name=self.design_name, dotrace=True, include_synth_log=True)]

    def run(self):
        if self.simulator == Simulator.VERILATOR:
            simulator_name = 'Verilator'
        else:
            raise Exception('Did not recognize simulator')

        ins = self.input()
        assert len(ins) == 1
        infile = pickle.load(ins[0].open())

        print('have: %s' % list(infile))

        matrix, signals_list = get_taintmatrix(infile, infile['synthlog'], self.design_name, self.picktaint)
        print('%s matrix size: %s siglist taint: %d' % (self.binary, matrix.shape,len(signals_list)))

        if False:
            assert len(signals_list_taint) == taintmatrix.shape[0]
            assert len(signals_list_data) == datamatrix.shape[0]
            signals_list=signals_list_taint+signals_list_data
            timelen = min(taintmatrix.shape[1], datamatrix.shape[1])
            taintmatrix = taintmatrix[:,-timelen:]
            datamatrix = datamatrix[:,-timelen:]
            assert taintmatrix.shape[1] == timelen
            assert datamatrix.shape[1] == timelen
            matrix=numpy.vstack([taintmatrix,datamatrix])
            assert matrix.shape[0] == len(signals_list)
            assert matrix.shape[1] == timelen
            matrix = matrix.astype('int8')

            print('matrix uncompressed: %s' % (matrix.shape,))
            matrix=matrix_uniq_cols(matrix)
            print('matrix compressed: %s' % (matrix.shape,))

        with self.output().temporary_path() as outfile_fn:
            matrix_fn = outfile_fn + '-matrix'
            numpy.save(matrix_fn, matrix)
            print('saving matrix to %s' % matrix_fn)
            pickle.dump({'meta': infile, 'siglist': signals_list, 'matrix': matrix_fn}, open(outfile_fn, 'wb'))

@inherits(SignalsMatrixList)
class SignalsMatrixListJSON(luigi.Task):

    def __init__(self, *args, **kwargs):
        super(SignalsMatrixListJSON, self).__init__(*args, **kwargs)
        self.experiment_name = "signalsmatrixlistjson-{}-{}-{}-{}-{}-{}-{}".format(self.simulator, taintstr(self.taintbits), binarycrc(self.binary), self.simtime, self.design_name, self.instrumentation, self.picktaint)

    def requires(self):
        t = self.clone(SignalsMatrixList)
        return t

    def output(self):
        return luigi.LocalTarget('{}/experiments/{}-{}-jsondata.json'.format(os.environ["CELLIFT_DATADIR"], self.experiment_name, self.expname), format=luigi.format.Nop)

    def run(self):
        with self.input().open() as inf:
            d=pickle.load(inf)
            nodes=dict()
            fullname2id=dict()
            links=set()
            nid=0
            for signame in d['siglist']:
                parts=signame.split('.')
                for p in range(len(parts)):
                    name='.'.join(parts[0:p+1])
                    if name not in fullname2id:
                        nodes[nid]=parts[p]
                        fullname2id[name]=nid
                        nid+=1
                    if p > 0:
                        prev_name='.'.join(parts[0:p])
                        links.add((fullname2id[prev_name], fullname2id[name]))
#                print('links: %s' % (links,))
#                print('nodes: %s' % (nodes,))
            matrix=numpy.load(d['matrix'] + '.npy')
            print('matrix uncompressed: %s' % (matrix.shape,))
            matrix=matrix_uniq_cols(matrix)
            print('matrix compressed: %s' % (matrix.shape,))
            json_timematrix = numpy.transpose(matrix).tolist()
            json_nodes = [{'text': nodes[nid], 'id': nid} for nid in list(nodes)]
            json_links = [{'source': l[0], 'target': l[1]} for l in links]
            with self.output().temporary_path() as outfile_fn:
                json.dump({'matrix': json_timematrix, 'nodes': json_nodes, 'links': json_links}, open(outfile_fn, 'w'), separators=(',', ':'))


