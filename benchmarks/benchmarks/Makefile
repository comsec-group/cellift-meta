#=======================================================================
# UCB VLSI FLOW: Makefile for riscv-bmarks
#-----------------------------------------------------------------------
# Yunsup Lee   (yunsup@cs.berkeley.edu)
# Flavien Solt (flsolt@ethz.ch)
#

XLEN ?= 64

ifndef CELLIFT_DESIGN
$(error No design is selected: the CELLIFT_DESIGN environment variable is unset. Please use the scripts selecting a design before compiling the benchmarks.)
endif

default: all

src_dir = .

instname = riscv-bmarks
instbasedir = $(UCB_VLSI_HOME)/install

LINKER_SCRIPT = $(src_dir)/linker_scripts/$(CELLIFT_DESIGN)_link.ld
START_ADDR = `cat $(CELLIFT_DESIGN_CELLIFTDIR)/meta/start_addr.txt`
STOP_SIGNAL_ADDR = `cat $(CELLIFT_DESIGN_CELLIFTDIR)/meta/stop_signal_addr.txt`
RV_ARCH_FLAGS = `cat $(CELLIFT_DESIGN_CELLIFTDIR)/meta/riscv_arch_flags.txt`

#--------------------------------------------------------------------
# Sources
#--------------------------------------------------------------------

bmarks = \
	median \
	qsort \
	rsort \
	towers \
	vvadd \
	multiply \
	mm \
	dhrystone \
	spmv \

#--------------------------------------------------------------------
# Build rules
#--------------------------------------------------------------------

RISCV_PREFIX ?= riscv32-unknown-elf-
RISCV_GCC ?= $(RISCV_PREFIX)gcc
RISCV_GCC_OPTS ?= -DPREALLOCATE=1 -mcmodel=medany -static -std=gnu99 -O2 -ffast-math -fno-common -fno-builtin-printf -fno-tree-loop-distribute-patterns $(RV_ARCH_FLAGS) -DSTOP_SIGNAL_ADDR="$(STOP_SIGNAL_ADDR)"
RISCV_LINK ?= $(RISCV_GCC) -T $(src_dir)/common/test.ld $(incs)
RISCV_LINK_OPTS ?= -static -nostdlib -nostartfiles -lm -lgcc -T $(LINKER_SCRIPT)
RISCV_OBJDUMP ?= $(RISCV_PREFIX)objdump --disassemble-all --disassemble-zeroes --section=.text --section=.text.startup --section=.text.init --section=.data
RISCV_SIM ?= spike --isa=rv$(XLEN)gc

incs  += -I$(src_dir)/../env -I$(src_dir)/common $(addprefix -I$(src_dir)/, $(bmarks))
objs  :=

define compile_template
../out/$(CELLIFT_DESIGN)/bin/$(1).riscv: $(LINKER_SCRIPT) | ../out/$(CELLIFT_DESIGN)/bin ../out/$(CELLIFT_DESIGN)/taint_data
	$$(RISCV_GCC) $$(incs) $$(RISCV_GCC_OPTS) -o $$@ $(wildcard $(src_dir)/$(1)/*.c) $(wildcard $(src_dir)/common/*.c) $(wildcard $(src_dir)/common/*.S) $$(RISCV_LINK_OPTS)
endef

$(foreach bmark,$(bmarks),$(eval $(call compile_template,$(bmark))))

#------------------------------------------------------------
# Build and run benchmarks on riscv simulator

bmarks_riscv_bin  = $(addprefix ../out/$(CELLIFT_DESIGN)/bin/, $(addsuffix .riscv,  $(bmarks)))
bmarks_riscv_dump = $(addprefix ../out/$(CELLIFT_DESIGN)/bin/, $(addsuffix .riscv.dump, $(bmarks)))
bmarks_riscv_out  = $(addprefix ../out/$(CELLIFT_DESIGN)/bin/, $(addsuffix .riscv.out,  $(bmarks)))

$(bmarks_riscv_dump): %.riscv.dump: %.riscv
	$(RISCV_OBJDUMP) $< > $@

$(bmarks_riscv_out): %.riscv.out: %.riscv
	$(RISCV_SIM) $< > $@

riscv: $(bmarks_riscv_dump)
run: $(bmarks_riscv_out)

junk += $(bmarks_riscv_bin) $(bmarks_riscv_dump) $(bmarks_riscv_hex) $(bmarks_riscv_out)

#--------------------------------------------------------------------
# Linker script

$(LINKER_SCRIPT): $(src_dir)/common/template_link.ld | $(src_dir)/build
	sed s/TEMPLATE_START_ADDR/$(START_ADDR)/ $< > $@

#------------------------------------------------------------
# Default

all: riscv

#------------------------------------------------------------
# Install

date_suffix = $(shell date +%Y-%m-%d_%H-%M)
install_dir = $(instbasedir)/$(instname)-$(date_suffix)
latest_install = $(shell ls -1 -d $(instbasedir)/$(instname)* | tail -n 1)

install:
	mkdir $(install_dir)
	cp -r $(bmarks_riscv_bin) $(bmarks_riscv_dump) $(install_dir)

install-link:
	rm -rf $(instbasedir)/$(instname)
	ln -s $(latest_install) $(instbasedir)/$(instname)

#------------------------------------------------------------
# Directories

$(src_dir)/build ../out ../out/$(CELLIFT_DESIGN) ../out/$(CELLIFT_DESIGN)/bin ../out/$(CELLIFT_DESIGN)/taint_data:
	mkdir -p $@

#------------------------------------------------------------
# Clean up

clean:
	rm -rf $(objs) $(junk)
