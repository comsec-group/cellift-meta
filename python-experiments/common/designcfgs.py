# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import json
import os
from collections import defaultdict
from common.enums import InstrumentationMethod, instrumentation_method_to_string

DESIGN_REPOS_JSON_NAME = "design_repos.json"

cached_configs = defaultdict(dict)

def get_design_cellift_path(design_name):
    # 1. Find the designs folder.
    designs_folder = os.getenv("CELLIFT_DESIGN_PROCESSING_ROOT")
    if not designs_folder:
        raise Exception("Please re-source env.sh first, in the meta repo, and run from there, not this repo. See README.md in the meta repo")
    # 2. Find the repo name.
    with open(os.path.join(designs_folder, DESIGN_REPOS_JSON_NAME), "r") as f:
        read_dict = json.load(f)
    try:
        repo_name = read_dict[design_name]
    except:
        candidate_names = read_dict.keys()
        raise ValueError("Design name not in design_repos.json: {}. Candidates are: {}.".format(design_name, ', '.join(candidate_names)))
    return os.path.join(designs_folder, repo_name)

# @param design_name: must be one of the keys of the design_repos.json dict.
# @return the design config of the relevant repo.
def get_design_cfg(design_name):
    if not cached_configs[design_name]:
        with open(os.path.join(get_design_cellift_path(design_name), "meta", "cfg.json"), "r") as f:
            cached_configs[design_name] = json.load(f)
    return cached_configs[design_name]

# @param design_name: must be one of the keys of the design_repos.json dict.
# @param instrumentation: common.enums.InstrumentationMethod.
# @param dotrace: boolean.
# @return pair(the base path to the 'cellift' folder of the design repository, the RELATIVE path to the hardware simulation binary of the given design with the given parameters).
def get_design_hsb_path(design_name, instrumentation, dotrace):
    design_cellift_path = get_design_cellift_path(design_name)
    instrumentation_name = instrumentation_method_to_string(instrumentation)
    dotrace_str = "trace" if dotrace else "notrace"
    toplevel_name = get_design_cfg(design_name)["toplevel"]
    return design_cellift_path, "build/run_{}_{}_0.1/default-verilator/V{}".format(instrumentation_name, dotrace_str, toplevel_name)

# Prettifies known design names.
def get_design_prettyname(design_name):
    if design_name == "ibex":
        return "Ibex"
    elif design_name == "cva6":
        return "Ariane"
    elif design_name == "pulpissimo":
        return "PULPissimo"
    elif design_name == "rocket":
        return "Rocket"
    elif design_name == "boom":
        return "BOOM"
    else:
        return design_name

# Returns the list of supported instrumentation methods supported by the given design for synthesis.
def get_instrumentation_methods_per_design_yosys(design_name):
    assert design_name in ["ibex", "cva6", "pulpissimo", "rocket", "boom"]
    instrumentation_methods = [
        InstrumentationMethod.VANILLA,
        InstrumentationMethod.PASSTHROUGH,
        InstrumentationMethod.CELLIFT,
        InstrumentationMethod.GLIFT
    ]
    return instrumentation_methods

# Returns the list of supported instrumentation methods supported by the given design for synthesis.
def get_instrumentation_methods_per_design_verilator(design_name):
    assert design_name in ["ibex", "cva6", "pulpissimo", "rocket", "boom"]
    instrumentation_methods = [
        InstrumentationMethod.VANILLA,
        InstrumentationMethod.PASSTHROUGH,
        InstrumentationMethod.CELLIFT,
    ]
    # Only some designs  GLIFT target.
    if design_name in ["ibex", "pulpissimo", "rocket"]:
        instrumentation_methods.append(InstrumentationMethod.GLIFT)
    return instrumentation_methods

# Get the path to V<toplevel_name>__024root.h'
def get_root_c_header_path(design_name, instrumentation, do_trace):
    cellift_path = get_design_cellift_path(design_name)
    run_target_str = "run_{}_{}_0.1".format(instrumentation_method_to_string(instrumentation), "trace" if dotrace else "notrace")
    return os.path.join(cellift_path, "build", run_target_str, "default-verilator")
