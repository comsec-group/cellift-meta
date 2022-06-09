# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Corrects Yosys mistakes such as: assign { 48'hffffffffffff, \gen_special_results[0].active_format.special_results.special_res [31:16] } = info_q[5]

import sys
import re

# sys.argv[1] the path to the input file.
# sys.argv[2] the path to the output file.

if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        verilog_content = f.read()
    verilog_content, num_subs = re.subn("assign\s+\{\s*\d+'[a-zA-Z\d]+\s*,", "assign {", verilog_content, count=0, flags=re.MULTILINE)
    print("  Num too wide lvalues corrected: {}".format(num_subs))
    with open(sys.argv[2], "w") as f:
        f.write(verilog_content)
