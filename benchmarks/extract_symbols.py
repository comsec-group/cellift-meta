# This script creates the taint data file for each benchmark. It is called by build-benchmarlks-alldesigns.

import re
import sys
import os
from pathlib import Path

# sys.argv[1]: the folder in which the *.riscv and *.riscv.dump are located in bin/.
# sys.argv[2]: the start address (after bootrom execution).

if __name__ == "__main__":

    def gen_taint_data_content(addr):
        return "0 {} 4 FFFFFFFF".format(addr)

    # None: the first instruction will be tainted.
    symbol_dict = {
        "dhrystone": None, # Taint the first address.
        "median": "input_data",
        "mm": "input1_data_mm",
        "multiply": "input_data1",
        "qsort": "input_data",
        "rsort": "input_data",
        "spmv": "val",
        "towers": "num_discs",
        "vvadd": "input1_data",
    }

    # Directory paths.
    base_dir = sys.argv[1]
    bin_dir = os.path.join(base_dir, "bin")
    taint_data_dir = os.path.join(base_dir, "taint_data")
    # Create the taint_data dir if it does not yet exist.
    Path(taint_data_dir).mkdir(parents=True, exist_ok=True)

    # Start address.
    start_addr = sys.argv[2]


    addr = None
    for benchmark, symbol in symbol_dict.items():
        # Find the symbol address, for each benchmark
        if symbol is None:
            addr = start_addr
            if "".join(addr[:2]) == "0x":
                addr = addr[2:]
        else:
            dump_file_path = os.path.join(bin_dir, benchmark+".riscv.dump")
            with open(dump_file_path, "r") as f:
                dump_content = f.read()
            # Find the symbol address in the dump file.
            match_occurrence = re.search(r"# ([1-9a-fA-F][\da-fA-F]+) <"+symbol+r">\n", dump_content)
            # Check that exactly 1 match was found.
            if match_occurrence is None:
                raise ValueError("Expected at least 1 match for symbol {} in {}.".format(symbol, dump_file_path))
            # Extract the symbol address
            addr = match_occurrence.group(1)

        # Write the taint data, for each benchmark
        out_file_path = os.path.join(taint_data_dir, benchmark+'.txt')
        with open(out_file_path, "w") as f:
            f.write(gen_taint_data_content(addr))
            print("Wrote {}".format(out_file_path))