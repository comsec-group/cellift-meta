# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Remove modules from given SystemVerilog file.

import re
import sys

# sys.argv[1]: source file path.
# sys.argv[2]: target file path (will be a copy of the source file, but without the specified modules).
# sys.argv[3]: name of the top module to remove.

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Takes 3 arguments: the Verilog source file path, the Verilog target file path and a space-separated list of entities to remove.")

    with open(sys.argv[1], "r") as f:
        verilog_content = f.read()

    for module_name in sys.argv[3:]:
        verilog_content, num_subs = re.subn("module(\s|n)+{}(\s|\n)*(\(|#|import)(.|\n)+?endmodule[^\n]*\n".format(module_name), "\n", verilog_content, flags=re.MULTILINE|re.DOTALL) # Weakness: does not ignore comments.
        print("  Removed {} occurrences of module {}.".format(num_subs, module_name))

    with open(sys.argv[2], "w") as f:
        f.write(verilog_content)
