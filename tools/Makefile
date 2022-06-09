# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

PYTHON=python3.9

RUSTEXEC=$(CARGO_HOME)/bin/rustc
RUSTUPEXEC=$(CARGO_HOME)/bin/rustup
CARGOEXEC=$(CARGO_HOME)/bin/cargo

LOGFILES=log

installtools: install_gcc install_rust install_morty install_bender install_fusesoc install_toolchain install_verilator install_sv2v install_cellift_python install_yosys install_spike install_gtkwave

install_gtkwave:
	# this one is not in the installtools list
	( cd gtkwave/gtkwave3/ && ./configure --with-tk=/usr/lib/tk8.6/ --disable-xz --prefix=$(PREFIX_CELLIFT) && make -j$(CELLIFT_JOBS) && make install ) >$(LOGFILES)/gtkwave.log 2>&1

silly_test_target:
	echo Ok, silly test done.

install_gcc:
	( cd gcc && sh go.sh ) >$(LOGFILES)/gcc.log 2>&1

install_verilator:
	( cd verilator && autoconf && ./configure --prefix=$(PREFIX_CELLIFT) && make -j$(CELLIFT_JOBS) && make install ) >$(LOGFILES)/verilator.log 2>&1

install_sv2v: $(PREFIX_CELLIFT)/bin/stack
	( cd sv2v && make -j$(CELLIFT_JOBS) && mkdir -p $(PREFIX_CELLIFT)/bin/ && cp bin/sv2v $(PREFIX_CELLIFT)/bin/ ) >$(LOGFILES)/sv2v.log 2>&1

$(PREFIX_CELLIFT)/bin/stack:
	sh stack/gethaskellstack.sh -d $(PREFIX_CELLIFT)/bin

install_yosys:
	( cd cellift-yosys && make PREFIX=$(PREFIX_CELLIFT) -j$(CELLIFT_JOBS) && make PREFIX=$(PREFIX_CELLIFT) install ) >$(LOGFILES)/yosys.log 2>&1

install_rust: $(RUSTEXEC)

install_cellift_python: $(CELLIFT_PYTHON_VENV)
	(  \
		set -e; \
		$(CELLIFT_PYTHON_VENV)/bin/pip install -r ../design-processing/python-requirements.txt; \
		$(CELLIFT_PYTHON_VENV)/bin/pip install -r ../python-experiments/python-requirements.txt; \
		$(CELLIFT_PYTHON_VENV)/bin/pip install -r ibex-python-requirements.txt; \
	    $(CELLIFT_PYTHON_VENV)/bin/pip install -r ../external-dependencies/cellift-opentitan/python-requirements.txt; \
		$(CELLIFT_PYTHON_VENV)/bin/pip install ninja==1.10.2 \
	)  >$(LOGFILES)/cellift-python.log 2>&1

$(RUSTEXEC):
	( CARGO_HOME=$(CARGO_HOME) RUSTUP_HOME=$(RUSTUP_HOME) ./rustup-init -y --default-toolchain 1.55.0 ) >$(LOGFILES)/rust.log 2>&1
	$(RUSTUPEXEC) install 1.55.0 >$(LOGFILES)/rustup.log 2>&1

install_morty: $(RUSTEXEC)
	$(CARGOEXEC) install --path morty --root $(PREFIX_CELLIFT) >$(LOGFILES)/morty.log 2>&1

install_bender: $(RUSTEXEC)
	$(CARGOEXEC) install --path bender --root $(PREFIX_CELLIFT) >$(LOGFILES)/bender.log 2>&1

install_fusesoc: $(CELLIFT_PYTHON_VENV)
	$(CELLIFT_PYTHON_VENV)/bin/pip install fusesoc==1.12.0 >$(LOGFILES)/fusesoc.log 2>&1

install_toolchain: $(PREFIX_CELLIFT)/riscv
	# make also does install
	( cd riscv-gnu-toolchain/ && ./configure --prefix=$(PREFIX_CELLIFT)/riscv --with-arch=rv32imc --with-cmodel=medlow --enable-multilib && make -j $(CELLIFT_JOBS) ) >$(LOGFILES)/toolchain.log 2>&1

install_spike: $(PREFIX_CELLIFT)/riscv
	(cd riscv-isa-sim && mkdir -p build && cd build && ../configure --prefix=$(PREFIX_CELLIFT)/riscv && make -j $(CELLIFT_JOBS) && make install) >$(LOGFILES)/spike.log 2>&1

$(CELLIFT_PYTHON_VENV):
	$(PYTHON) -mvenv $(CELLIFT_PYTHON_VENV)

cleantools:
	@echo "This is a fairly destructive recipe. Really know what's going to happen?"
	@echo "If so, press enter. Otherwise, press ^C."
	@echo -n "  >  "
	@read line
	set -x; for x in riscv-isa-sim bender morty riscv-gnu-toolchain sv2v verilator yosys-ift gcc; do ( cd $$x && git clean -xfd ); done
	rm -rf $(PREFIX_CELLIFT)
	rm -f $(LOGFILES)/*.log

$(PREFIX_CELLIFT)/riscv:
	mkdir -p $@

