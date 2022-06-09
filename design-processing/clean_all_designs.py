# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script cleans all designs listed in the design_repos json file.

import json
import multiprocessing
import subprocess
import os

if "CELLIFT_ENV_SOURCED" not in os.environ:
    raise Exception("The CellIFT environment must be sourced prior to running the Python recipes.")

DESIGN_CFGS_BASENAME = "design_repos.json"
PATH_TO_DESIGN_CFGS = os.path.join(os.getenv("CELLIFT_DESIGN_PROCESSING_ROOT"), DESIGN_CFGS_BASENAME)

# Ask confirmation before cleaning all designs.
confirmation_str = input("This will clean all the design repositories listed in {}. Continue (yes|NO)?".format(DESIGN_CFGS_BASENAME))
if confirmation_str.lower() not in ["y","yes"]:
    print("Aborted.")

# Read the list of paths to the design cellift directories.
with open(PATH_TO_DESIGN_CFGS, "r") as f:
    design_json_content = json.load(f)
design_cellift_paths = list(design_json_content.values())

# Run cleaning in parallel.
num_processes = int(os.getenv("CELLIFT_JOBS"))
def worker(design_cellift_path):
    cmdline = ["make", "-C", design_cellift_path, "clean"]
    subprocess.check_call(cmdline)
my_pool = multiprocessing.Pool(num_processes)
my_pool.map(worker, design_cellift_paths)
