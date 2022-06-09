# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import json
import os
from common.enums import instrumentation_method_to_string

def get_design_names():
    return [
        "ibex",
        "rocket",
        "pulpissimo",
        "cva6",
        "boom"
    ]

def get_verilator_resources_root():
    return os.path.join(os.getenv("CELLIFT_DATADIR"), "resources")

# @param instrumentation_method as in common.enums (i.e.m enum type as opposed to string).
# @param label typically `synth`.
# @return float.
def get_verilator_synthesis_duration(design_name, instrumentation_method, dotrace, label='synth'):
    json_basename = "resource-usage-log-entry_{}__{}{}__{}.json".format(design_name, instrumentation_method_to_string(instrumentation_method), "_notrace" if not dotrace else "", label)
    json_path = os.path.join(get_verilator_resources_root(), json_basename)
    with open(json_path, "r") as f:
        json_content = json.load(f)
    if not 'walltime' in json_content:
        raise ValueError("Expected 'walltime' field in {} when treating {design_name: {}, instrumentation_method: {}, dotrace: {}, label: {}".format(json_basename, design_name, instrumentation_method, dotrace, label))
    return float(json_content['walltime'])
