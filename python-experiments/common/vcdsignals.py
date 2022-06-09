# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import collections
import itertools
import multiprocessing as mp
import numpy as np
import os
import re
import sys

from bisect import bisect_left
from tqdm import tqdm

import common.designcfgs as designcfgs

NUM_PROCESSES = int(os.getenv("CELLIFT_JOBS"))
vcd_timestep = 5 # Changes in signal values can only occur every vcd_timestep step.

FILTERSTATEELEMENTS  = True  # Whether to only account for state-holding elements.
TAINTMARKER          = '_t0' # Taint suffix.
STATE_ELEMENT_MARKER = '@LIST_STATE_ELEMENT'

INT_TYPE = np.int32

def is_taintsignal(signame):
    return len(signame) >= len(TAINTMARKER) and signame[-len(TAINTMARKER):] == TAINTMARKER

# @param data an iterable of vcd objects (with the attribute `endtime`).
# @return the max time value of a vcd in the iterable.
def get_maxtimes(data):
    return max(map(lambda v: v.endtime, data))

# From a signal name, each potentially finishing with a slice \[\d+:0\], creates a list
# of the same size that stores the width of each signal.
# @param data a string representations of a signal.
def get_signal_widths(signal):
    curr_search = re.search(r".+\[(-?\d+)\s*:\s*(\d+)\]\s*\n", signal)
    if curr_search:
        high_bound = int(curr_search.group(1))
        low_bound  = int(curr_search.group(2))
        assert high_bound >= low_bound
        return high_bound-low_bound+1
    else:
        return 1

# From a signal name, each potentially finishing with a slice \[\d+:0\], removes this slice if it exists.
# Does NOT modify the param signal in place.
# @param data a string representations of signals.
def remove_signal_trailing_slice(signal):
    curr_search = re.search(r"(.+)\[-?\d+\s*:\s*\d+\]\s*\n*", signal)
    if curr_search:
        return curr_search.group(1)
    else:
        return signal

# Auxiliary function used by get_signals_list.
# Find the set of present signals corresponding to the allowed signals.
def find_corresponding_signal_worker(allowed_signal, present_signals_sorted_noslice):
    ret_signal_id = bisect_left(present_signals_sorted_noslice, allowed_signal)

    if ret_signal_id >= 0 and present_signals_sorted_noslice[ret_signal_id] == allowed_signal:
        return ret_signal_id
    return -1

# @param data an iterable of vcd objects (with the attribute `endtime`).
# @param allowed_list an iterable of allowed signal names (the signals in which we are interested in). Typically, the list of stateful signals.
# @param wanttaint a boolean which causes the taint signals to be filtered out if this boolean is true.
# @param wantregular a boolean which causes the regular (non-taint) signals to be filtered out if this boolean is true.
# @param design_name the design name (lowercase, as given in the JSON keys in the CELLIFT_DESIGN_PROCESSING_ROOT directory).
# @return A list of signal names corresponding to those found in the VCD file.
def get_signals_list(data, allowed_list, wanttaint, wantregular, design_name):
    # Ensure that all vcd have exactly the same set of signal names.
    signals_list           = [tuple(sorted(x.references_to_ids.keys())) for x in data]
    # signals_list           = list(map(lambda t: tuple(sorted(map(remove_signal_trailing_slice, t))), signals_list))
    signals_list_set       = set(signals_list)
    signals_list_set_len   = len(signals_list_set)
    if signals_list_set_len != 1:
        raise ValueError('Unexpected signal list discrepancy: the `data` parameter is expected to be a list of a single element.')
    signals_set = set(signals_list_set.pop())
    signals_sorted = sorted(list(signals_set))

    assert len(signals_sorted)
    assert len(allowed_list)

    # Filter out unwanted signals.
    if wanttaint: # Filter out the taint signals if necessary.
        allowed_list = list(filter(lambda sig: is_taintsignal(sig), allowed_list))
    if wantregular: # Filter out the refular (non-taint) signals if necessary.
        allowed_list = list(filter(lambda sig: not is_taintsignal(sig), allowed_list))
    # Check that there are still some allowed signals.
    if not allowed_list:
        raise ValueError("When filtering out taint or regular signals, all signals in allowed lists were removed.")

    # Prepend the right signal prefixes.
    allowed_set = set(map(lambda x: x.replace('TOP.', 'TOP.{}.'.format(designcfgs.get_design_cfg(design_name)["trace_top"])), allowed_list))

    signals_sorted_noslice = list(map(remove_signal_trailing_slice, signals_sorted))

    # Use sequenial instead of multiprocessing
    indices_list = []
    for allowed_signal_id, allowed_signal in enumerate(allowed_set):
        # print(allowed_signal)
        new_ret = find_corresponding_signal_worker(allowed_signal, signals_sorted_noslice)
        if new_ret >= 0:
            indices_list.append(new_ret)
    # End of: Use sequenial instead of multiprocessing

    ret_list = list(map(lambda x: signals_sorted[x], indices_list))

    print("Found {}/{} allowed signals.".format(len(ret_list), len(list(allowed_set))))
    return ret_list

# Lists all the times where a signal appears in one of the VCD files.
# @param signame the signal name as produced by get_signals_list.
# @param data an iterable of vcd objects.
# @return A list of signal names corresponding to those found in the VCD file.
def get_times(signame, data, maxtime):
    times=[]
    # Iterate through the time indications for this signal in all the vcd objects.
    for vcd in data:
        new_times = map(lambda t: t[0], vcd[signame].tv)
        times = itertools.chain(times, new_times)
    # Also add the extreme times.
    times = itertools.chain(times, range(maxtime+1))
    times = sorted(set(times))
    return times

# Finds the stateful signals thanks to the synthesis log.
# @param synthlog_list the list of synthesis logs. If the list contains more than one element, then this function will make sure that the data matches in all the provided logs.
# @return The list of stateful signals.
def get_stateful_elems(synthlog_list):
    sigset=None
    assert isinstance(synthlog_list, list)

    if not synthlog_list or (len(synthlog_list) == 1 and not synthlog_list[0]):
        raise ValueError("Trivial synthlog list. There is no stateful element to extract.")

    # All the synthesis logs should give the same result.
    for synthlog in synthlog_list:
        signames_set = set(map(lambda l: l.split()[1], filter(lambda l: STATE_ELEMENT_MARKER in l, synthlog.split('\n'))))
        if sigset == None:
            sigset = signames_set
        elif sigset != signames_set:
            raise Exception('different stateful signals list!')

    return sigset

# Auxiliary function for get_taintmatrix.
def get_taintmatrix_worker(signame, maxtime, signame_data):
    signame_noslice = remove_signal_trailing_slice(signame)
    # I commented out this assertion because we may want to process regular stateful signals as well.
    # assert signame_noslice[-len(TAINTMARKER):] == TAINTMARKER, signame_noslice # make sure all signals we get end in '_t0' as expected

    result_list = np.zeros((maxtime+1,), dtype=INT_TYPE)

    for ti in range(0, maxtime, vcd_timestep):
        t1,t2 = ti, ti+vcd_timestep
        v     = signame_data[t1] # v is the change of signame at time ti in the vcd file.
        # First step values can only happen at the first step.
        if v is None:
            # assert not t1, "t1: {}, t2: {}, signame: {}".format(t1, t2, signame)
            continue
        c1 = v.count('1')
        c0 = v.count('0')
        assert len(v) == c0 + c1 # v must be composed only of zeroes and ones.
        result_list[t1:t2] += c1 # add the count of ones in all the cells until the next simt step.

    # This version works only when `times` is complete, i.e., missing no step.
    return result_list

# @param datalump the output of a simulation run.
# @param synthlog the synthesis log (that allows extracting which were the stateful signals).
# @param design_name the design name.
# @return taintmatrix (matrix[signal][time]), signallist (iterable of signals without the taint marker)
def get_taintmatrix(datalump, synthlog, design_name, wanttaint=True):
    assert isinstance(datalump, dict)

    # Get vcd data and maxtime.
    data            = tuple(map(lambda d: d['vcd'], [datalump])) # Transform to tuple to be able to use it multiple times.
    maxtime         = get_maxtimes(data)

    print("Generating signals list...")
    # Get signal list.
    siglist_stateful = get_stateful_elems([synthlog])
    # Filter out the signals containing `$rdreg[`
    siglist_stateful = list(filter(lambda sig: r'$rdreg[' not in sig, siglist_stateful))
    # signals_list includes the slices.
    signals_list     = get_signals_list(data, siglist_stateful, wanttaint=wanttaint, wantregular=not wanttaint, design_name=design_name)
    print("Done: Generating signals list.")

    assert isinstance(signals_list,list)

    # Generate `times`: an iterable of all times with events concerning this signal in the VCD file.
    # Commented out because Verilator outputs VCD's with one time per time.
    # times = list(map(lambda signame: get_times(signame, data, maxtime), signals_list))

    #######
    # Using parallel workers, match allowed signals with present signals.
    #######
    # One worker per signal, i.e., per matrix row.

    # We do not use mp pipes anymore.
    # # 1. Prepare the mp pipes: one for each matrix row.
    # parent_conns = [None for _ in signals_list]
    # child_conns = [None for _ in signals_list]
    # for row_id in range(len(signals_list)):
    #     parent_conns[row_id], child_conns[row_id] = mp.Pipe()

    # 2. Generate the parameters for the workers.
    signame_data = [datalump['vcd'][signame] for signame in signals_list]
    worker_params = zip(signals_list, itertools.repeat(maxtime), signame_data)

    # 3. Create and run the pool.
    my_pool = mp.Pool(NUM_PROCESSES)
    print("Generating taint matrix using parallel workers...")
    taintmatrix_prenp = my_pool.starmap(get_taintmatrix_worker, worker_params)
    my_pool.close()
    my_pool.join()
    print("Done: Generating taint matrix using parallel workers.")

    # # 4. Build the taintmatrix with the generated data.
    # # First, get all the messages from the workers.
    # print("Reshaping the matrix...")
    # flattened = itertools.chain.from_iterable(map(lambda p: p.recv(), parent_conns))
    # # Then, create a flat list of these.
    # taintmatrix_1d = np.fromiter(flattened, dtype=INT_TYPE)
    # # Finally, reshape to get the right matrix.
    # taintmatrix = np.reshape(taintmatrix_1d, (len(signals_list), -1))
    # print("Done: Reshaping the matrix.")
    taintmatrix = np.array(taintmatrix_prenp, dtype=INT_TYPE)

    #signals_list = map(lambda s: s.replace(TAINTMARKER, ''), signals_list) # Remove the taint marker
    return taintmatrix, signals_list
