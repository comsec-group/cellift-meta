# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

def get_design_names():
    return [
        "ibex",
        "rocket",
        "pulpissimo",
        "cva6",
        "boom"
    ]

def get_design_numcycles(design_name):
    {
        "ibex": 40000000,
        "rocket": 40000,
        "pulpissimo": 200000,
        "cva6": 40000,
        "boom": 40000
    }[design_name]
