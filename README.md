# CellIFT-Meta

This repository regroups tools needed to reproduce the experiments performed in the [CellIFT paper](https://comsec.ethz.ch/cellift).

The supported designs are frozen versions of [Ibex](https://github.com/comsec-group/cellift-ibex/) , [PULPissimo (modified for the HACK@DAC'18 competition)](https://github.com/comsec-group/cellift-pulpissimo-hdac-2018/), [CVA6](https://github.com/comsec-group/cellift-cva6/), [Rocket and BOOM](https://github.com/comsec-group/cellift-chipyard/).

## What is it about?

Visit [our dedicated web page](https://comsec.ethz.ch/research/microarch/cellift/) to know more about the nature and use cases of CellIFT.

In a few words, CellIFT is a mechanism that supports dynamic information flow tracking for RTL designs.
_Dynamic information flow tracking is a mechanism that, for a given set of input signals (taint sources), reveals which internal and output signals (taint sinks) can be affected by changing values at these inputs, as illustrated in the figure below_.
Use cases of CellIFT encompass scenari from checking data integrity and confidentiality to detecting complex information leakage such as Spectre or Meltdown.

As opposed to the pre-existing information flow tracking mechanisms, CellIFT is open source.
CellIFT also outperforms pre-existing mechanisms in terms of precision and in terms of speed by one to two orders of magnitude.

Along with this repository, we provide instrumented versions of 5 CPU designs.
CellIFT can instrument any digital design, and this repository is a great starting point to instrument your own design.

## Getting started

There are two alternatives: using a Docker image, or installing the tools locally.

### With Docker

For an explanation of Docker and how CellIFT uses it, see README-Docker.txt.

There are a number of images that are available on the ETH container registry.

1. Tools (all CellIFT itself and its version-controlled dependencies):
   `tag: registry.ethz.ch/comsec/hardware-information-flow-tracking/cellift-meta:cellift-tools-main`
   To use:
```
   $ docker pull registry.ethz.ch/comsec/hardware-information-flow-tracking/cellift-meta:cellift-tools-main
   $ docker run -it registry.ethz.ch/comsec/hardware-information-flow-tracking/cellift-meta:cellift-tools-main bash
```
   CellIFT tools sources will be in /cellift-meta., and the binaries in /root/prefix-cellift/.
2. Ibex design (Tools + source code with CellIFT instrumentation infrastructure):
   `tag: registry.ethz.ch/comsec/hardware-information-flow-tracking/designs/ibex:cellift-ibex-master`
   To use:
```
   $ docker pull registry.ethz.ch/comsec/hardware-information-flow-tracking/designs/ibex:cellift-ibex-master
   $ docker run -it registry.ethz.ch/comsec/hardware-information-flow-tracking/designs/ibex:cellift-ibex-master bash
```
   CellIFT tools sources are again in `/cellift-meta`, binaries in `/root/prefix-cellift`, and the Ibex design sources
   in `/cellift-designs/ibex/`, cellift-specific dir is `/cellift-designs/ibex/cellift`.
   To see CellIFT in action, execute from the container the Ibex  tests:
```
     root@afb86238a65a:/cellift-designs/ibex/cellift# bash tests.sh
     metarepo root: /cellift-meta
     Selected design: ibex
     make: Entering directory '/cellift-meta/benchmarks/benchmarks'
```
   This will build vanilla and cellift modes, each in trace and notrace modes, and execute them, loading a certain benchmark binary (see tests.sh for details), i.e. all 4 combinations.

See `docker/README-Docker.txt`.

### With a local installation of tools

First, get the repository and its submodules.
This may take a while.

```bash
git clone --recurse-submodules -j8 git@gitlab.ethz.ch:comsec/hardware-information-flow-tracking/cellift-meta.git
cd cellift-meta
```

The -j8 indicates fetching up to 8 repo's in parallel.  This is a fairly
heavyweight operation because it includes the toolchain repo's.
If you cloned without `--recurse-submodules`, do this to get the contents:
`make pull`

Second, install the prerequisites with `apt` following the `apt` lines of `docker/Dockerfile-base`.

Third, adapt the environment file `env.sh` to your needs/capabilities and then source it.

```bash
source env.sh
```

Fourth, install the necessary tools.
This may take a while.

```bash
make -j$CELLIFT_JOBS installtools
```

Fifth, to get all the design repositories next to the cellift-meta to obtain such a hierarchy...

```
├── cellift-designs
│   ├── cellift-chipyard
│   ├── cellift-cva6
│   ├── cellift-ibex
│   └── cellift-pulpissimo-hdac-2018
└── cellift-meta
```

... type the following commands:

```bash
cd ..
mkdir cellift-designs
cd cellift-designs
git clone cellift-ibex
git clone cellift-pulpissimo-hdac-2018
git clone cellift-chipyard
git clone cellift-cva6 --recursive
```

## Repository hierarchy

- `benchmarks`: contains the riscv-tests benchmarks that can run on the 5 designs.
- `design-processing`: contains utilities to process data, that are typically shared between multiple designs.
- `docker`: to run CellIFT in a container, see `docker/README-Docker.txt`
- `external-dependencies`: contains a frozen fork of the Opentitan repository, useful for the Ibex design.
- `python-experiments`: contains a number of Python scripts that reproduce the experiments described in the paper.
- `tests`: contains basic tests to check whether the tool installation was successful.
- `tools`: contains tools, many of them as submodules.


## How to use the designs

Make sure to always have `cellift-meta/env.sh` sourced.

Designs should be cloned in a new directory `cellift-designs` next to `cellift-meta`, for example making the following path valid: `cd ../cellift-designs/celift-ibex`.
You can build all the design executables with `cd design-processing && python3 make_all_designs.py && cd..` once all the designs are cloned, and Rocket and BOOM are prepared (see below).
Designs can be instrumented and/or executed with diverse `make` targets, which must be run in the respective `cellift`.
Among these targets are:
- `run_INSTRUMENTATION_TRACING`, where `INSTRUMENTATION` is `vanilla`, `passthrough` (just goes through Yosys, but without instrumentation), `cellift` or `glift`; `TRACING` is `notrace`, `trace` (generates vcd for the tools) or `trace_fst` (fst wave format, more convenient, and that can be visualized using `make wave` or `make wave_fst`). This synthesizes (and potentially instruments) the design, compiles the testbench and runs it.
- `recompile_INSTRUMENTATION_TRACING` to only recompile the testbench.
- `rerun_INSTRUMENTATION_TRACING` to only rerun the testbench without any recompilation.
- `make wave` to visualize traces after running a target whose name ended with `_trace`, and `make wave_fst` for `_trace_fst` targets.

Designs usually require some environment variables (typically present in `env.sh` files, for example `cellift-ibex/cellift/env.sh`) to run such as:
- `TRACEFILE`: the path to the waveform file to generate (`*.fst` or `*.vcd`) if tracing is activated.
- `SIMLEN`: the number of cycles to simulate.

The taint file format is, for each line:
`<taint_color> <address> <num bytes to taint> <taint mask (all F means fully tainted)>`
All numberic values are written in hexadecimal.

### Preparing the Rocket and BOOM cores

For instrumenting the Rocket and BOOM cores, located in `cellift-chipyard`, it is required to first generate the Verilog code.
The complete procedure is as follows.

```
cd ../cellift-designs/cellift-chipyard/
# See https://www.gnu.org/licenses/gpl-3.0.en.html
sudo apt-get install -y build-essential bison flex software-properties-common curl
sudo apt-get install -y libgmp-dev libmpfr-dev libmpc-dev zlib1g-dev vim default-jdk default-jre
echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | sudo tee -a /etc/apt/sources.list.d/sbt.list
curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | sudo apt-key add
sudo apt-get update
sudo apt-get install -y sbt
sudo apt-get install -y texinfo gengetopt
sudo apt-get install -y libexpat1-dev libusb-dev libncurses5-dev cmake
sudo apt-get install -y python3.8 patch diffstat texi2html texinfo subversion chrpath wget
sudo apt-get install -y libgtk-3-dev gettext
sudo apt-get install -y python3-pip python3.8-dev rsync libguestfs-tools expat ctags
sudo apt-get install -y device-tree-compiler
sudo apt-get install -y python
sudo add-apt-repository ppa:git-core/ppa -y
sudo apt-get update
sudo apt-get install git -y
./scripts/init-submodules-no-riscv-tools.sh # Press 'y' when prompted that this is not the official repository.
# End of classical Chipyard repository setup.
cd sims/verilator

# For the 2 targets below, ignore the error `[error] Picked up JAVA_TOOL_OPTIONS: -Xmx8G -Xss8M -Djava.io.tmpdir=<some path>`.
# For Rocket
make CONFIG=MySmallVMRocketConfig
# For BOOM
make CONFIG=MySmallBoomConfig
```

### How to run the RISC-V benchmarks

To build the RISC-V benchmarks, execute:

```bash
cd benchmarks
bash build-benchmarks-alldesigns.sh
cd ..
```

Then, to run the benchmarks on all designs (they must be built beforehand), execute:
```
cd python-experiments
python3 plot_benchmark_performance.py
cd ..
```

### Compiling design-specific binaries

Each design has a `sw` directory, containing itself one directory per software experiment.
To compile each of these binaries, run `make` in the corresponding subdirectory of the `sw` directory.

### Reproducing the experiments

Once all the designs, benchmarks and design-specific binaries are compiled, you can reproduce the paper's experiments.

```
cd python-experiments

# Plot the benchmark performance (slowdown compared to Vanilla) for all designs and supported instrumentations.
python3 plot_benchmark_performance.py

# Plot the cell composition statistics (make sure to have built all the statistics logs, for example using `cd design-processing && python3 make_all_design_cellstats.py`).
python3 plot_cellstats.py

# Plot the number of tainted states in Ibex for the benchmarks.
python3 plot_num_tainted_states_ibex.py

# Plot the instrumentation performance (which should first be logged during instrumentation).
python3 plot_instrumentation_performance.py

# Plot the memory that was used during instrumentation and synthesis.
python3 plot_rss.py

# Plot the number of tainted states during a scenario (Meltdown or Spectre, for example). Do not forget to compile the design-specific binary (in the corresponding design repository, typically in `cellift-chipyard/cellift-boom/sw/<scenario_name>/`)
python3 plot_tainted_elements.py # You can customize parameters in this script, such as which design or which scenario to run.
```

## Resource usage monitoring

### Python wrapper for resource usage

`sudo apt-get install python3.9 python3.9-venv`
`python3.9 -mvenv venv/resources`
`./venv/resources/bin/pip install -r python_scripts/resources/requirements.txt ./datapoints`

### How to log resource usage for instrumentation, synthesis, and running

1. set up the python environment (parent item).
Execute these phases as normal, but before you do:
`export LOGRESOURCES=yes`
then `resourcewrapper` will log data in the `tables_data` dir for each phase and each method.

e.g.:
`export LOGRESOURCES=yes`
`make clean run_vanilla_notrace run_cellift_notrace run_glift_plus_notrace`

to check if loggin will happen, look for this line in the output:
`resourcewrapper (log): Executing fusesoc run --build hdac_run_vanilla_notrace for table pulpissimo, row vanilla, column synth.`
in particular the `(log)` word. If logging is skipped, it will say `(no log)`.

This writes the raw data to `tables_data/*.txt`, and the colated data in formatted LaTeX table
format to `generated/*.tex`.

If you want to regenerate the LaTeX tables from the raw data, use:
`./venv/resources/bin/python python_scripts/resources/resourcesgenerate.py tables_data generated`
where the first and 2nd args are the raw data dir and formatted output dir respectively.

## License

All the CellIFT related contributions are licensed under the GNU General Public License version 3.
