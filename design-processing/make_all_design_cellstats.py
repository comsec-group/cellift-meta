# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script cleans all designs listed in the design_repos json file.

# Each design is built in a separate process group.
# Each design is first run until the beginning of the instrumentation once (this is a critical section). Then, all the instrumentations are run in parallel.

# Command-line arguments:
#     --exclude-designs <list_of_designs>
#     --single-threaded

import argparse
import json
import multiprocessing
import subprocess
import os
import sys
from collections import defaultdict

if "CELLIFT_ENV_SOURCED" not in os.environ:
    raise Exception("The CellIFT environment must be sourced prior to running the Python recipes.")

DESIGN_CFGS_BASENAME = "design_repos.json"
PATH_TO_DESIGN_CFGS = os.path.join(os.getenv("CELLIFT_DESIGN_PROCESSING_ROOT"), DESIGN_CFGS_BASENAME)

# Run in parallel on given number of processes.
tot_num_processes = int(os.getenv("CELLIFT_JOBS"))

####
# Parse the command-line argumens
####

parser = argparse.ArgumentParser(description='Computes the stats of all designs.')
parser.add_argument('--exclude-designs', nargs='*', type=str, default=[], help='Exclude a list of designs, for example --exclude-designs ibex cva6')
parser.add_argument('--single-threaded', action='store_true', help='Runs the script in single-threaded mode. This can help in preventing spurious segmentation faults')

args = parser.parse_args()

# Exclude designs if requested.
exclude_designs = args.exclude_designs
force_single_threaded = args.single_threaded
print("Exclude designs", exclude_designs)

exclude_designs = args.exclude_designs
if exclude_designs:
    print("Exclude designs", exclude_designs)

# Run in parallel on given number of processes.
if force_single_threaded:
    tot_num_processes = 1
else:
    tot_num_processes = int(os.getenv("CELLIFT_JOBS"))

####
# Prepare configurations to build
####

with open(PATH_TO_DESIGN_CFGS, "r") as f:
    design_json_content = json.load(f)
design_names = list(design_json_content.keys())

# Check that all the designs to be excluded are present in the design names.
if set(exclude_designs)-set(design_names):
    raise ValueError("Requested to exclude design(s) {} that are not among the present designs: {}.".format(', '.join(list(set(exclude_designs)-set(design_names))), ', '.join(design_names)))

# Remove designs requested to remove.
for design_to_exclude in set(exclude_designs):
    design_names.remove(design_to_exclude)

# Generate the pairs (design_name, instrumentation method <as a string>).
# These pairs are to be used in a later stage of the multiprocessing pool.
design_instrumentation_pairs = []
for design_name in design_names:
    instrumentation_methods = ["vanilla", "passthrough", "cellift", "glift"]
    design_instrumentation_pairs += [(design_name, im) for im in instrumentation_methods]

#####
# Two auxiliary functions
#####

cached_configs = defaultdict(dict)
cached_start_addrs = defaultdict(dict)

def get_design_cellift_path(design_name):
    # 1. Find the designs folder.
    designs_folder = os.getenv("CELLIFT_DESIGN_PROCESSING_ROOT")
    if not designs_folder:
        raise Exception("Please re-source env.sh first, in the meta repo, and run from there, not this repo. See README.md in the meta repo")
    # 2. Find the repo name.
    with open(PATH_TO_DESIGN_CFGS, "r") as f:
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

#####
# Workers for the two stages
#####

# First-stage worker, called only once per design.
def pre_instrumentation_worker(design_name):
    design_cellift_path = get_design_cellift_path(design_name)
    cmdline = ["make", "-C", design_cellift_path, "before_instrumentation"]
    subprocess.check_call(cmdline)

# Second-stage worker, called once per (design, instrumentation_type) pair.
# @param instrumentation_method: "vanilla", "passthrough", "cellift", ("glift" for designs that support it).
def instrumentation_worker(design_name, instrumentation):
    design_cellift_path = get_design_cellift_path(design_name)
    cmdline = ["make", "-C", design_cellift_path, "statistics/{}.log".format(instrumentation)]
    subprocess.check_call(cmdline)

#####
# Run the workers
#####

# Run in parallel.
my_pool = multiprocessing.Pool(tot_num_processes)
# First stage: per-design critical section.
worker_params = design_names
for worker_param in worker_params:
    pre_instrumentation_worker(worker_param)
# my_pool.map(pre_instrumentation_worker, worker_params) Do not parallelize this stage.
# Second stage: run the instrumentation of all the designs with all instrumentation methods.
worker_params = design_instrumentation_pairs
my_pool.starmap(instrumentation_worker, worker_params)
my_pool.close()
my_pool.join()

print("Success! All statistics have been generated in the respective design repositories.")
