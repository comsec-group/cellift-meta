# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Remove modules from given SystemVerilog file.

import multiprocessing as mp
import re
import sys

num_workers = mp.cpu_count()

# sys.argv[1]: source file path.
# sys.argv[2]: target file path (will be a copy of the source file, but without the unused modules).
# sys.argv[3...]: Module names to not remove.

# MODULE_DEF_REGEX = r'^module\s+([a-zA-Z0-9_]+)\s*(?:#|\(|import)'
MODULE_DEF_REGEX = r'^module(?:\s|\n)+([\$\\a-zA-Z0-9_]+)(?:\s|\n)*(?:#|\(|import)'
# Return True iff the module is never referenced except in its own definition and in comments.
def is_single_ref(modulename):
    print(f"Finding references to module `{modulename}`")
    references_to_m = re.findall(r'^.*\b'+modulename.replace('\\', '\\\\')+r'\b', verilog_content, re.MULTILINE)
    references_to_m = list(filter(lambda s: '//' not in s, references_to_m))
    # print(f"References to {modulename}: {references_to_m}")
    return len(references_to_m) == 1

if __name__ == "__main__":
    global verilog_content
    if len(sys.argv) < 3:
        print("Takes at least 2 arguments: the Verilog source file path, the Verilog target file path. The rest of the arguments are modules that must not be removed")

    with open(sys.argv[1], "r") as f:
        verilog_content = f.read()

    if len(sys.argv) >= 3:
        modules_to_keep = sys.argv[3:]
    else:
        modules_to_keep = []

    num_removed_modules = 0
    MODULE_DEF_REGEX = re.compile(MODULE_DEF_REGEX, re.MULTILINE)
    all_modulenames = re.findall(MODULE_DEF_REGEX, verilog_content)
    num_tot_modules = len(all_modulenames)

    # Check that the modules to keep are present initially
    for module_to_keep in modules_to_keep:
        if module_to_keep not in all_modulenames:
            print(f"Failed to find definition of module to keep: `{module_to_keep}`")

    all_modulenames = list(filter(lambda s: s not in modules_to_keep, all_modulenames))
    # Do it iteratively until none of them is unused anymore
    do_continue = True

    while do_continue:
        do_continue = False

        # Find references in parallel
        print('Finding references to modules...')
        with mp.Pool(num_workers) as p:
            remove_modules = p.map(is_single_ref, all_modulenames)
        print('  Done finding references to modules.')

        newly_removed_modulenames = []
        for moduleid, modulename in enumerate(all_modulenames):
            if not remove_modules[moduleid]:
                continue
            do_continue = True
            num_removed_modules += 1
            newly_removed_modulenames.append(modulename)
            # references_to_m = re.findall(r'^.*\b'+modulename+r'\b', verilog_content, re.MULTILINE)
            # references_to_m = list(filter(lambda s: '//' not in s, references_to_m))
            module_def_regex = r'^module\s+'+modulename+r'\s*(?:#|\()(?:.|\n)+?\n\s*endmodule(\s*:\s*[a-zA-Z0-9_]*)?'
            # # # Check that we find the def
            # # # assert re.search(module_def_regex, verilog_content, re.DOTALL | re.MULTILINE)
            verilog_content, count = re.subn(module_def_regex, '\n\n', verilog_content, flags = re.DOTALL | re.MULTILINE)
            print(f"  Removed module {modulename} ({count} occurrence(s)).")
        for modulename in newly_removed_modulenames:
            all_modulenames.remove(modulename)
    
    print(f"Removed {num_removed_modules}/{num_tot_modules} module(s).")

    with open(sys.argv[2], "w") as f:
        f.write(verilog_content)
