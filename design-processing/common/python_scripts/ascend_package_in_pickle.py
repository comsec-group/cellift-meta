# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Move the specified package up in the pickle file, works in place.

import re
import sys

# sys.argv[1]: Package name
# sys.argv[2]: source and target pickle Verilog file

if __name__ == "__main__":
    pkgname = sys.argv[1]
    src_filename = sys.argv[2]

    with open(src_filename, "r") as f:
        content = f.read()

    regex_pattern = r"package\s*"+pkgname+r"(?:.|\n)+?endpackage"

    # Get the package texts
    packagetexts = re.findall(regex_pattern, content, re.DOTALL)
    # Remove them from the pickle
    content = re.sub(regex_pattern, '\n\n', content, re.DOTALL)

    # Write them to the top of the pickle file
    content = '\n\n'.join(packagetexts) + content

    with open(src_filename, "w") as f:
        f.write(content)
