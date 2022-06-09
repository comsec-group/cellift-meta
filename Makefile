# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This Makefile manages the repository and the submodule hierarchy.

SHELL := /bin/bash # Need this for associative arrays

ifndef CELLIFT_ENV_SOURCED
$(error Please re-source env.sh first, see README.md)
endif

ifneq "$(CELLIFT_ENV_VERSION)" "1"
$(error Current env.sh out of date, please source env.sh again, see README.md)
endif

default-target:
	@echo "Usage:"
	@echo "    make installtools    - build riscv toolchain, morty, bender,"
	@echo "                           verilator, sv2v and other tools and install"
	@echo "                           in $(PREFIX_CELLIFT)"
	@echo "    make cleantools      - clean build tree of tools and delete"
	@echo "                           $(PREFIX_CELLIFT)"
	@echo "    make pull            - do git pull for current repo and update submodules"

pull:
	git pull
	git submodule update --jobs $(CELLIFT_JOBS) --init --recursive

clean-designs:
	for design in $(DESIGNS); \
	do	 \
     	make -C designs/$$design/cellift clean; \
	done

update-designs:
	for design in $(DESIGNS); \
	do	 \
     	( cd designs/$$design && git checkout master && echo $$design && git pull --rebase ) \
	done
	( cd cellift-paper && git checkout master && git pull --rebase && git push )

installtools:
	make -C tools installtools

cleantools:
	make -C tools cleantools
