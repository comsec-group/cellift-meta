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
# @param is_synth true for synthesis, false for instrumentation.
# @return float.
def get_rss(design_name, instrumentation_method, dotrace, is_synth):
    if is_synth and not dotrace:
        trace_text = "_notrace"
    else:
        trace_text = ""
    label = "synth" if is_synth else "instr"
    json_basename = "resource-usage-log-entry_{}__{}{}__{}.json".format(design_name, instrumentation_method_to_string(instrumentation_method), trace_text, label)
    json_path = os.path.join(get_verilator_resources_root(), json_basename)
    with open(json_path, "r") as f:
        json_content = json.load(f)
    if not 'maxrss' in json_content:
        raise ValueError("Expected 'maxrss' field in {} when treating {design_name: {}, instrumentation_method: {}, dotrace: {}, label: {}".format(json_basename, design_name, instrumentation_method, dotrace, label))
    return float(json_content['maxrss'])
