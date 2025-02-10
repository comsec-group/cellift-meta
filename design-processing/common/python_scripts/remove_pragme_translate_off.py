# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Remove //pragma translate_off/on sections.

import re
import sys

# sys.argv[1]: source file path.
# sys.argv[2]: target file path (will be a copy of the source file, but without the specified modules).

REGEX = r'//\s*pragma\s+translate_off(?:.|\n)+?//\s*pragma\s+translate_on'

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Takes 2 arguments: the Verilog source file path, the Verilog target file path.")

    with open(sys.argv[1], "r") as f:
        verilog_content = f.read()

    verilog_content, num_subs = re.subn(REGEX, "\n", verilog_content, flags=re.MULTILINE|re.DOTALL)
    print("  Removed {} occurrences of pragma translate on/off.".format(num_subs))

    with open(sys.argv[2], "w") as f:
        f.write(verilog_content)

