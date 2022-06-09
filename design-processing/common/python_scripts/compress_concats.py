# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import re
import sys

# sys.argv[1]: source Verilog file
# sys.argv[2]: target Verilog file

BRACKET_FIND_REGEX = r"\{([^\}\n]+)\}"
ARRAY_DEREF_REGEX = r"(\w+)\[(\d+)\]"

# @param elems the elements of a concatenation array
# @return the same array, but with identical contiguous elements compressed
def replace_reps(elems):
    curr_length = 0
    ret_groups = []
    for elem in elems:
        if not curr_length:
            last_elem = elem
            curr_length = 1
            continue
        else:
            if last_elem != elem:
                if curr_length == 1:
                    ret_groups.append(last_elem)
                else:
                    ret_groups.append("{ "+str(curr_length)+"{ "+last_elem+" }"+" }")
                curr_length = 0

        last_elem = elem
        curr_length += 1

    if curr_length == 1:
        ret_groups.append(last_elem)
    elif curr_length:
        ret_groups.append("{ "+str(curr_length)+"{ "+last_elem+" }"+" }")

    return ret_groups

# @param elems the elements of a concatenation array
# @return the same array, but with increasing sequences written as slices
def replace_incr(elems):
    def commit_prev_elem(curr_arr_name, curr_arr_start_id, curr_length):
        assert curr_length
        if curr_length == 1:
            return "{}[{}]".format(curr_arr_name, curr_arr_start_id)
        return "{}[{}:{}]".format(curr_arr_name, curr_arr_start_id, curr_arr_start_id+curr_length-1)

    curr_arr_name = ""
    curr_arr_start_id = 0
    curr_length = 0

    ret_groups = []

    for elem in elems:
        curr_search = re.search(ARRAY_DEREF_REGEX, elem)
        if not curr_search or curr_search.group(0) != elem: # If this is not an array dereference
            if curr_length: # Commit the previous slice
                ret_groups.append(commit_prev_elem(curr_arr_name, curr_arr_start_id, curr_length))
            ret_groups.append(elem) # Transmit the current element
            curr_length = 0
            continue
        search_arr_name = curr_search.group(1)
        search_arr_id = int(curr_search.group(2))
        if not curr_length: # If no array is yet initiated
            curr_length = 1
            curr_arr_start_id = search_arr_id
            curr_arr_name = search_arr_name
        elif search_arr_name != curr_arr_name or search_arr_id != curr_arr_start_id+curr_length: # If an array with another name was initiated
            ret_groups.append(commit_prev_elem(curr_arr_name, curr_arr_start_id, curr_length))
            curr_length = 1
            curr_arr_start_id = search_arr_id
            curr_arr_name = search_arr_name
        else: # If this is the continuation of the current slice
            curr_length += 1

    if curr_length:
        ret_groups.append(commit_prev_elem(curr_arr_name, curr_arr_start_id, curr_length))

    return ret_groups

# @param elems the elements of a concatenation array
# @return the same array, but with decreasing sequences written as slices
def replace_decr(elems):
    def commit_prev_elem(curr_arr_name, curr_arr_start_id, curr_length):
        assert curr_length
        if curr_length == 1:
            return "{}[{}]".format(curr_arr_name, curr_arr_start_id)
        return "{}[{}:{}]".format(curr_arr_name, curr_arr_start_id+curr_length-1, curr_arr_start_id)

    curr_arr_name = ""
    curr_arr_start_id = 0
    curr_length = 0

    ret_groups = []

    for elem in elems:
        curr_search = re.search(ARRAY_DEREF_REGEX, elem)
        if not curr_search or curr_search.group(0) != elem: # If this is not an array dereference
            if curr_length: # Commit the previous slice
                ret_groups.append(commit_prev_elem(curr_arr_name, curr_arr_start_id, curr_length))
            ret_groups.append(elem) # Transmit the current element
            curr_length = 0
            continue
        search_arr_name = curr_search.group(1)
        search_arr_id = int(curr_search.group(2))
        if not curr_length: # If no array is yet initiated
            curr_length = 1
            curr_arr_start_id = search_arr_id
            curr_arr_name = search_arr_name
        elif search_arr_name != curr_arr_name or search_arr_id != curr_arr_start_id-curr_length: # If an array with another name was initiated
            ret_groups.append(commit_prev_elem(curr_arr_name, curr_arr_start_id, curr_length))
            curr_length = 1
            curr_arr_start_id = search_arr_id
            curr_arr_name = search_arr_name
        else: # If this is the continuation of the current slice
            curr_length += 1

    if curr_length:
        ret_groups.append(commit_prev_elem(curr_arr_name, curr_arr_start_id, curr_length))

    return ret_groups


def reduce_bracket(match):
    bracket_content = match.group(1)
    splitted = list(map(lambda x: x.strip(), bracket_content.split(',')))

    # Find repetitions of identical elements
    ret_groups = replace_reps(splitted)

    # Unsupported by some commercial tool
    # # Find expanded slices
    # ret_groups = replace_incr(ret_groups)

    # Find expanded slices
    ret_groups = replace_decr(ret_groups)


    return "{ "+' , '.join(ret_groups)+" }"

if __name__ == "__main__":
    src_filename = sys.argv[1]
    tgt_filename = sys.argv[2]

    with open(src_filename, "r") as f:
        content = f.read()

    content = re.sub(BRACKET_FIND_REGEX, reduce_bracket, content)

    with open(tgt_filename, "w") as f:
        f.write(content)
