# Design processing

This directory provides some resources to help instrumenting designs with CellIFT.

The following scripts assume that all the designs are ready to be made, which means simply cloned for Ibex, PULPissimo and CVA6 (recursively), and for Chipyard this implies setting up the repository and generating the Verilog source of Rocket or BOOM.

- `make_all_designs` makes all the instrumentation flavors of all designs.
- `make_all_designs_cellstats` makes all the instrumentation flavors of all designs to extract statistics for all instrumentations.
- `clean_all_designs` cleans all the design instrumentations and syntheses. Use with care.
