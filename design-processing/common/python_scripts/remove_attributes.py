# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Remove modules from given SystemVerilog file.

import re
import sys

# sys.argv[1]: source file path.
# sys.argv[2]: target file path (will be a copy of the source file, but without the attributes).

ATTRIBUTE_REGEX = r"^\(\*[^\n]+\*\)$"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Takes 2 arguments: the Verilog source file path, the Verilog target file path.")

    with open(sys.argv[1], "r") as f:
        verilog_content = f.read()

    verilog_content, num_subs = re.subn("module(\s|n)+{}(\s|\n)*(\(|#|import)(.|\n)+?endmodule[^\n]*\n".format(module_name), "\n", verilog_content)
    print("  Removed {} attributes.".format(num_subs))

    with open(sys.argv[2], "w") as f:
        f.write(verilog_content)
