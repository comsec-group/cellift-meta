riscv-tests
================

About
-----------

This repository hosts unit tests for RISC-V processors.

Building from repository
-----------------------------

We assume that the RISCV environment variable is set to the RISC-V tools
install path, and that the riscv-gnu-toolchain package is installed.

    $ git submodule update --init --recursive
    $ autoconf
    $ ./configure --prefix=$RISCV/target
    $ source build-benchmark.sh ibex <num_jobs default=$CELLIFT_JOBS>
    $ source build-benchmark.sh pulpissimo <num_jobs default=$CELLIFT_JOBS>
    $ source build-benchmark.sh cva6 <num_jobs default=$CELLIFT_JOBS>
    $ source build-benchmark.sh rocket <num_jobs default=$CELLIFT_JOBS>
    $ source build-benchmark.sh boom <num_jobs default=$CELLIFT_JOBS>
    $ source build-benchmark.sh boom-v2.2.3 <num_jobs default=$CELLIFT_JOBS>

Generating the taint data
------------------------------

    $ python3 extract_symbols.py out/$CELLIFT_DESIGN $CELLIFT_DESIGN_START_ADDR

For instance for Ibex:

    $ python3 extract_symbols.py out/ibex 80

The generated taint data txt files are then located in `out/$CELLIFT_DESIGN/taint_data/`.
