# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Expands an expression `assign A = [&|] <long_concatenation> ` by expanding <long_concatenation> into a new signal.
# This script should be followed by compress_right_side_concat.

import re
import sys
import tqdm

# sys.argv[1]: source Verilog file
# sys.argv[2]: target Verilog file

FIND_REGEX = r"\b(assign\s+(\w+)\s*=\s*([&|])\s*\{([^\n]+)\});"
MAX_TERMS_IN_BRACKET = 1000
TYPE = "logic"
SUFFIX = "inst"
VAR_BASE_NAME = "expand_reduction_operand"

def reduce_bracket(match):
    global num_brackets_treated

    assignment_destination = match.group(2)
    reduction_operator = match.group(3)
    bracket_content = match.group(4)

    splitted = list(map(lambda x: x.strip(), bracket_content.split(',')))
    tot_num_elems = len(splitted)

    if tot_num_elems < MAX_TERMS_IN_BRACKET:
        return match.group(0)

    var_name = "{}_{}".format(VAR_BASE_NAME, num_brackets_treated)
    var_name_with_suffix = "{}_{}".format(var_name, SUFFIX)
    num_brackets_treated += 1

    ret_lines = []

    # First, declare the new wire.
    ret_lines.append("  {} [{}-1:0] {};".format(TYPE, tot_num_elems, var_name_with_suffix))

    # Second, assign the bracket value to the newly created wire.
    ret_lines.append("  assign {} = {{{}}};".format(var_name_with_suffix, bracket_content))

    # Third, modify the original wire.
    ret_lines.append("  assign {} = {} {};".format(assignment_destination, reduction_operator, var_name_with_suffix))

    return '\n'.join(ret_lines)


if __name__ == "__main__":
    global num_brackets_treated
    num_brackets_treated = 0
    src_filename = sys.argv[1]
    tgt_filename = sys.argv[2]

    with open(src_filename, "r") as f:
        content = f.read()
    content_lines = content.split('\n')
    new_lines=[]
    print('%d lines' % len(content_lines))

    n=0
    for oldline in tqdm.tqdm(content_lines):
        newline = re.sub(FIND_REGEX, reduce_bracket, oldline)
        new_lines.append(newline)
        n+=1

    with open(tgt_filename, "w") as f:
        f.write('\n'.join(new_lines))
    print('invocations: %d' % num_brackets_treated)
