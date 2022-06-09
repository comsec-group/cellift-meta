# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import os

# Returns the list of names in the considered risc-v benchmark suite.
# This is intended to be an auxiliary function of get_benchmark_paths.
def get_benchmark_names():
    return [
        "dhrystone",
        "median",
        "mm",
        "multiply",
        "qsort",
        "rsort",
        "spmv",
        "towers",
        "vvadd"
    ]

# Returns the list of paths to each benchmark.
def get_benchmark_path(design_name, benchmark_name):
    meta_root = os.getenv("CELLIFT_META_ROOT")
    if not meta_root:
        raise Exception("Please re-source env.sh first. See README.md in the meta repo")
    ret_dir = os.path.join(meta_root, "benchmarks", "out", design_name, "bin")
    return os.path.join(ret_dir, "{}.riscv".format(benchmark_name))

# Returns the list of paths to each benchmark taint file.
def get_benchmark_taint_path(design_name, benchmark_name):
    meta_root = os.getenv("CELLIFT_META_ROOT")
    if not meta_root:
        raise Exception("Please re-source env.sh first. See README.md in the meta repo")
    ret_dir = os.path.join(meta_root, "benchmarks", "out", design_name, "taint_data")
    return os.path.join(ret_dir, "{}.txt".format(benchmark_name))
