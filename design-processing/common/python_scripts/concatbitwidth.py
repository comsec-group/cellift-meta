# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script supposes that each element in a bracket is either:
# (a) A number with explicit width.
# (b) A slice in a signal, where the slice boundaries are plain decimal numbers.
# (c) A previously declared signal, with a fixed width as a plain decimal number.
#
# In particular, it supposes no nested expressions and no nested concatenations.
#

import re

SIGNAL_SLICE_REGEXP = r"\[\s*(\d+)\s*:\s*(\d+)\s*\]"
SIGNAL_DECLARATION = r"^\s*(?:wire|reg|logic|input|output)\s*(?:\[\s*(\d+)\s*:\s*(\d+)\s*\])?\s*([a-zA-Z0-9_]+)\s*;"
FORBIDDEN_CHARACTERS = r"+-*/=<>{}"

# @param The bracket content, deprived of its surrounding curly brackets.
# @param all_lines all the lines of the document, where signals could have been declared.
# @param curr_line_number the line number corresponding to this bracket.
def get_bracket_bit_width(bracket_content, all_lines, curr_line_number):
    global num_brackets_treated
    # Cache to accelerate signal lookups in case (c).
    bracket_signal_cache = dict()

    # Quickly check that there is no nested expression or concatenation.
    for forbidden_character in FORBIDDEN_CHARACTERS:
        if forbidden_character in bracket_content:
            raise ValueError("Unexpected character in concatenation bracket content: {}. Bracket content: `{}`. Line number: `{}`.".format(forbidden_character, bracket_content, curr_line_number))

    bracket_width = 0

    ###
    # Pre-find all signal declarations
    ###

    # Finding signal declarations in 2 phases: first find the last declaration lines, then find the signal width
    signal_declaration_lines = dict() # Tuples (range high, range low if range high is not None). Only intermediate, not supposed to be used except to compute signal_widths.
    signal_declaration_regexp = re.compile(SIGNAL_DECLARATION)
    for search_line_id in range(curr_line_number):
        curr_match = re.match(signal_declaration_regexp, all_lines[search_line_id])
        if curr_match:
            signal_declaration_lines[curr_match.groups()[-1]] = curr_match.groups()[:-1]
    # Find the signal width
    signal_widths = dict() # signal_widths[signal_name] = width (bits)
    for signal_name, curr_groups in signal_declaration_lines.items():
        range_high = curr_groups[0]
        # If this is a single-bit declaration without square brackets.
        if range_high is None:
            signal_widths[signal_name] = 1
        else:
            range_low = curr_groups[1]
            signal_widths[signal_name] = int(range_high) - int(range_low) + 1

    # Compute the bracket bit width elementwise.
    for bracket_element in bracket_content.split(","):
        bracket_element = bracket_element.strip()

        # (a) If this element is a number with an explicit width.
        if "'" in bracket_element:
            bracket_width += int(bracket_element.split("'")[0])
            continue

        # Make sure that this is not a number without explicit width.
        elif bracket_element[0] in "0123456789":
            raise ValueError("Numbers in concatenation brackets must have explicit width, but no apostrophe has been found.")

        # (b) If this element is slice of some signal.
        elif "[" in bracket_element:
            # If this a single bit selection.
            index_col = bracket_element.find(':')
            if index_col == -1:
                bracket_width += 1
                continue
            # Else, it is a range.
            # Regexes are too expensive
            # search_result = re.search(SIGNAL_SLICE_REGEXP, bracket_element)
            # if search_result is None:
            #     raise ValueError("Error when processing curly bracket token when assessing the concatenation bit width: {}".format(bracket_element))
            # range_high = search_result.group(1)
            # range_low = search_result.group(2)
            # assert range_high is not None and range_low is not None
            index_brackopen  = bracket_element.index('[')
            index_brackclose = bracket_element.index(']')

            # If the colon is not between the brackets, then this is not a slice.
            if index_col < index_brackopen or index_col > index_brackclose:
                bracket_width += 1
                continue

            range_high = bracket_element[index_brackopen+1:index_col]
            range_low  = bracket_element[index_col+1:index_brackclose]
            bracket_width += int(range_high) - int(range_low) + 1
            if int(range_high) - int(range_low) + 1 < 1:
                raise ValueError(f"Err: Found width {int(range_high) - int(range_low) + 1} for bracket elem {bracket_element}. Range high: {range_high}, range low: {range_low}.")
            continue

        # (c) If this element is a pre-declared signal.
        else:
            if bracket_element in signal_widths:
                bracket_width += signal_widths[bracket_element]
            else:
                # In case it was not found 
                bracket_width += 1

    return bracket_width
