# Python design experiments

The following conditions must be verified to ensure that the experiments will run:

- The designs must be placed in a folder next to `cellift-meta`, called `cellift-designs`, which contains itself the directories that we provide separately: `ibex`, `cva6`, `pulpissimo-hdac-2018` and `chipyard`.
- The concerned simulation binaries must be compiled before running the experiments, for example by running `make run_vanilla_trace` in `ibex/cellift` to generate an Ibex simulation binary with VCD traces and without IFT instrumentation.

## Cell statistics

For getting the cell statistics, you must run, in all designs and for all instrumentation methods: `make statistics/<instrumentation_method>.log`.