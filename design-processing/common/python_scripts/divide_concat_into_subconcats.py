# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Expands an expression `assign A = <long_concatenation> & B` by expanding <long_concatenation> into a new signal.
# This script should be followed by compress_right_side_concat.

from concatbitwidth import get_bracket_bit_width
import re
import sys
import tqdm

# sys.argv[1]: source Verilog file
# sys.argv[2]: target Verilog file

FIND_REGEX = r"\b(assign\s+\w+\s*= )\{([^\n]+)\};"
MAX_TERMS_IN_BRACKET = 1000
TYPE = "logic"
SUFFIX = "inst"
VAR_BASE_NAME = "divide_concat_into_subconcats"

def reduce_bracket(match):
    global num_brackets_treated

    assignment_start = match.group(1)
    bracket_content = match.group(2)

    splitted = list(map(lambda x: x.strip(), bracket_content.split(',')))
    tot_num_elems = len(splitted)

    if tot_num_elems < MAX_TERMS_IN_BRACKET:
        return match.group(0)

    var_name = "{}_{}".format(VAR_BASE_NAME, num_brackets_treated)
    var_name_with_suffix = "{}_{}".format(var_name, SUFFIX)
    num_brackets_treated += 1

    num_macroterms_floor = tot_num_elems // MAX_TERMS_IN_BRACKET
    is_there_remainder = bool(tot_num_elems % MAX_TERMS_IN_BRACKET)

    ret_groups = []

    # Declare the intermediate wires

    # TODO Use the correct bit width for the signal declaration.
    ret_groups.append("  {} [{}-1:0] {};".format(TYPE, tot_num_elems, var_name))

    for macroterm_id in range(num_macroterms_floor):
        # If this is the last and there is no remainder
        if macroterm_id == num_macroterms_floor-1 and not is_there_remainder:
            # TODO Use the correct bit width for the signal declaration.
            ret_groups.append("  {} [{}-1:0] {}_{};".format(TYPE, MAX_TERMS_IN_BRACKET, var_name_with_suffix, macroterm_id))
            break
        # TODO Use the correct bit width for the signal declaration.
        ret_groups.append("  {} [{}-1:0] {}_{};".format(TYPE, MAX_TERMS_IN_BRACKET+1, var_name_with_suffix, macroterm_id))

    if is_there_remainder:
        # TODO Use the correct bit width for the signal declaration.
        ret_groups.append("  {} [{}-1:0] {}_{};".format(TYPE, tot_num_elems % MAX_TERMS_IN_BRACKET, var_name_with_suffix, num_macroterms_floor))

    ret_groups.append("  assign {} = {}_0;".format(var_name, var_name_with_suffix))

    for macroterm_id in range(num_macroterms_floor):
        macrobracket_content = ' , '.join(splitted[macroterm_id*MAX_TERMS_IN_BRACKET:(macroterm_id+1)*MAX_TERMS_IN_BRACKET])
        if macroterm_id < num_macroterms_floor-1 or is_there_remainder:
            ret_groups.append("  assign {}_{} = ".format(var_name_with_suffix, macroterm_id) + "{ " + macrobracket_content + " , {}_{}".format(var_name_with_suffix, macroterm_id+1) + " };")
        else:
            ret_groups.append("  assign {}_{} = ".format(var_name_with_suffix, macroterm_id) + "{ " + macrobracket_content + " };")

    if is_there_remainder:
        remaining_terms = splitted[num_macroterms_floor*MAX_TERMS_IN_BRACKET:]
        macrobracket_content = ' , '.join(remaining_terms)
        ret_groups.append("  assign {}_{} = ".format(var_name_with_suffix, num_macroterms_floor) + "{ " + macrobracket_content + " };")

    ret_groups.append("  {}{};".format(assignment_start, var_name))

    return '\n'.join(ret_groups)

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

    for oldline in tqdm.tqdm(content_lines):
        newline = re.sub(FIND_REGEX, reduce_bracket, oldline)
        new_lines.append(newline)

    with open(tgt_filename, "w") as f:
        f.write('\n'.join(new_lines))
    print('invocations: %d' % num_brackets_treated)
