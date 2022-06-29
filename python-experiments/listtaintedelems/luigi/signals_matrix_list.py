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
import re

from luigi.util import inherits

from listtaintedelems.luigi.countelems import CountElems
from common.enums import Simulator, InstrumentationMethod
from common.params_to_str import taintstr, binarycrc
from common.vcdsignals import get_taintmatrix, matrix_uniq_cols, matrix_nonzero_rows
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

def reduce_signame(signame):
    irg=signame
    signame = re.sub('_t0(\[[0-9:]*\])?', '', signame)
#    if signame[-3:] == '_t0':
#        signame = signame[:-3]
#    print('%s -> %s' % (irg,signame))
    return signame

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

            siglist=d['siglist']
            matrix=numpy.load(d['matrix'] + '.npy')

            print('matrix uncompressed: %s' % (matrix.shape,))
            matrix=matrix_uniq_cols(matrix)
            print('matrix compressed: %s' % (matrix.shape,))

            matrix,siglist = matrix_nonzero_rows(matrix,siglist)

            print('matrix compressed with only nonzero rows: %s' % (matrix.shape,))

            shortnames=set()
            node2signo=dict()
            assert len(siglist) == len(set(siglist))
            siglist = [reduce_signame(s) for s in siglist]
            assert len(siglist) == len(set(siglist))
            for signame in siglist:
#                signame = reduce_signame(signame)
                parts=signame.split('.')
                real_signals_found = 0
                for p in range(len(parts)):
                    name='.'.join(parts[0:p+1])
                    if name not in fullname2id:
                        shortname=parts[p]
                        while shortname in shortnames:
                            shortname+= '_'
                        assert shortname not in shortnames
                        shortnames.add(shortname)
                        nodes[nid]=shortname
                        fullname2id[name]=nid
                        if name in siglist:
                            #print('%s: found %s' % (signame, name))
                            real_signals_found += 1
                            node2signo[nid] = siglist.index(name)
                            assert node2signo[nid] >= 0 and node2signo[nid] < len(siglist)
                            assert len(siglist) == matrix.shape[0]
                        else:
                            #print('%s: not found %s' % (signame, name))
                            node2signo[nid] = -1
                        nid+=1
                    if p > 0:
                        prev_name='.'.join(parts[0:p])
                        links.add((fullname2id[prev_name], fullname2id[name]))
                if real_signals_found != 1:
                    print('signal: %s found: %d' % (signame, real_signals_found))
                assert real_signals_found == 1
#                print('links: %s' % (links,))
#                print('nodes: %s' % (nodes,))

            shortnames = {nodes[nid] for nid in nodes}
            assert len(nodes) == len(set(shortnames))
            assert sorted([node2signo[nid] for nid in list(nodes) if node2signo[nid] >= 0]) == list(range(len(siglist)))

            json_timematrix = numpy.transpose(matrix).tolist()
            print('matrix size for %s: %s' % (self.experiment_name, matrix.shape))
            json_nodes = [{'text': nodes[nid], 'id': nodes[nid], 'nid': nid, 'sigid': node2signo[nid] } for nid in list(nodes)]
            json_links = [{'source': nodes[l[0]], 'target': nodes[l[1]]} for l in links]
            with self.output().temporary_path() as outfile_fn:
                json.dump({'matrix': json_timematrix, 'nodes': json_nodes, 'links': json_links}, open(outfile_fn, 'w'), separators=(',', ':'))


