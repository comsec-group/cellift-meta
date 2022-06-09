# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from enum import IntEnum, auto

class Simulator(IntEnum):
    VERILATOR = auto()

class InstrumentationMethod(IntEnum):
    VANILLA     = auto()
    PASSTHROUGH = auto() # Corresponds to Vanilla, but processed by sv2v and Yosys
    CELLIFT     = auto()
    GLIFT       = auto()

def instrumentation_method_to_string(instrumentation_method):
    if instrumentation_method == InstrumentationMethod.VANILLA:
        return 'vanilla'
    elif instrumentation_method == InstrumentationMethod.PASSTHROUGH:
        return 'passthrough'
    elif instrumentation_method == InstrumentationMethod.CELLIFT:
        return 'cellift'
    elif instrumentation_method == InstrumentationMethod.GLIFT:
        return 'glift'
    else:
        raise Exception('Unsupported taint method: {}'.format(instrumentation_method))

def instrumentation_method_to_pretty_string(instrumentation_method):
    if instrumentation_method == InstrumentationMethod.VANILLA:
        return 'Original'
    elif instrumentation_method == InstrumentationMethod.PASSTHROUGH:
        return 'Passthrough'
    elif instrumentation_method == InstrumentationMethod.CELLIFT:
        return 'CellIFT'
    elif instrumentation_method == InstrumentationMethod.GLIFT:
        return 'GLIFT'
    else:
        raise Exception('Unsupported taint method: {}'.format(instrumentation_method))

def instrumentation_method_to_short_string(instrumentation_method):
    if instrumentation_method == InstrumentationMethod.VANILLA:
        return 'V'
    elif instrumentation_method == InstrumentationMethod.PASSTHROUGH:
        return 'P'
    elif instrumentation_method == InstrumentationMethod.CELLIFT:
        return 'C'
    elif instrumentation_method == InstrumentationMethod.GLIFT:
        return 'G'
    else:
        raise Exception('Unsupported taint method: {}'.format(instrumentation_method))
