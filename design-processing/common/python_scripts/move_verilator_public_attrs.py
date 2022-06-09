# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Modifies the Yosys output attributes `(* verilator_public = "1" *)` into inline /* verilator public */ attributes, understandable by Verilator.
# Assumes that all `(* verilator_public = "1" *)` attributes are followed by a signal declaration in the next line.

import re
import sys
import tqdm

# sys.argv[1]: source Verilog file
# sys.argv[2]: target Verilog file

REGEX_VERILATOR_PUBLIC_YOSYSATTR = r"^\s*\(\* verilator_public = \"1\" \*\)\s*$"
REGEX_SIGDECL = r"^([\s|\n]*(?:(?:input\s*|output\s*)?logic|(?:input\s*|output\s*)?reg|(?:input\s*|output\s*)?wire|(?:input|output)\s*)\s+[^\s]+\s*;)\s*$"

if __name__ == "__main__":
    src_filename = sys.argv[1]
    tgt_filename = sys.argv[2]

    num_invocations = 0

    with open(src_filename, "r") as f:
        content = f.read()
    content_lines = content.split('\n')
    print("{} lines".format(len(content_lines)))

    for line_id in tqdm.trange(len(content_lines)):
        match_object = re.match(REGEX_VERILATOR_PUBLIC_YOSYSATTR, content_lines[line_id])
        if match_object:
            num_invocations += 1
            # Assume that the next line is a signal declaration.
            match_sigdecl = re.match(REGEX_SIGDECL, content_lines[line_id+1])
            assert match_sigdecl is not None
            content_lines[line_id+1] = match_sigdecl.group(1)[:-1]+" /* verilator public */;"

    with open(tgt_filename, "w") as f:
        f.write('\n'.join(content_lines))
    print("invocations: {}".format(num_invocations))
