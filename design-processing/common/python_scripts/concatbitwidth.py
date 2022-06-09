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
SIGNAL_DECLARATION_PREFIX = r"(?:wire|reg|logic|input|output)\s*(?:\[\s*(\d+)\s*:\s*(\d+)\s*\])?\s*"
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
            raise ValueError("Unexpected character in concatenation bracket content: {}".format(forbidden_character))

    bracket_width = 0
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
            if ":" not in bracket_element:
                bracket_width += 1
                continue
            # Else, it is a range.
            search_result = re.search(SIGNAL_SLICE_REGEXP, bracket_element)
            if search_result is None:
                raise ValueError("Error when processing curly bracket token when assessing the concatenation bit width: {}".format(bracket_element))
            range_high = search_result.group(1)
            range_low = search_result.group(2)
            assert range_high is not None and range_low is not None
            bracket_width += int(range_high) - int(range_low) + 1
            continue

        # (c) If this element is a pre-declared signal.
        else:
            # First, check in the cache to accelerate lookups.
            if bracket_element in bracket_signal_cache:
                bracket_width += bracket_signal_cache[bracket_element]
                continue

            signal_decl_regexp = SIGNAL_DECLARATION_PREFIX + bracket_element + r"\s*;"
            regexp = re.compile(signal_decl_regexp)

            # Find the signal declaration in the preceding lines.
            for search_line_id in range(curr_line_number-1, -1, -1):
                search_result = regexp.search(all_lines[search_line_id])
                # If this line corresponds to the right declaration.
                if search_result:
                    range_high = search_result.group(1)
                    # If this is a single-bit declaration without square brackets.
                    if range_high is None:
                        curr_elem_width = 1
                    else:
                        range_low = search_result.group(2)
                        curr_elem_width = int(range_high) - int(range_low) + 1
                    bracket_signal_cache[bracket_element] = curr_elem_width
                    bracket_width += curr_elem_width
                    break

    return bracket_width
