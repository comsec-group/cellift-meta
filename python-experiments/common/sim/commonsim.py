# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import os
import common.taintfile as taintfile_module

def write_taintfile(resultsdir_final, taintbits_list):
    sram_taintfile = os.path.join(resultsdir_final, 'sram_taint_data.txt')
    assert isinstance(taintbits_list, tuple)
    taintfile_module.write_taintfile(sram_taintfile, taintbits_list)
    return sram_taintfile

# Replace the environment with new values.
# sram_taintfile: path relative to celliftdir
# bootrom_elf: path relative to celliftdir
def setup_sim_env(sram_elf, bootrom_elf, tracefile, simtime, sram_taintfile, celliftdir):
    assert isinstance(sram_elf, str)
    assert isinstance(bootrom_elf, str) or bootrom_elf is None
    assert isinstance(tracefile, str) or tracefile is None
    assert isinstance(simtime, int)
    assert isinstance(sram_taintfile, str)

    # Make all paths absolute.
    if bootrom_elf:
        bootrom_elf = os.path.join(celliftdir, bootrom_elf)
    sram_taintfile = os.path.join(celliftdir, sram_taintfile)

    # Copy the OS environment.
    my_env = os.environ.copy()

    # Replace the environment simlen and xproptaint.
    my_env["SIMLEN"] = str(simtime)

    if tracefile:
        my_env["TRACEFILE"] = tracefile
    else:
        assert "TRACEFILE" not in my_env

    # Replace the environment ELF paths.
    my_env["SIMSRAMELF"] = sram_elf
    if bootrom_elf:
        my_env["SIMROMELF"] = bootrom_elf
    else:
        my_env["SIMROMELF"] = sram_elf

    print('setting SIMSRAMELF to {}'.format(my_env["SIMSRAMELF"]))
    print('setting SIMROMELF to {}'.format(my_env["SIMROMELF"]))

    # Replace the environment taint paths.
    my_env["SIMROMTAINT"] = sram_taintfile
    my_env["SIMSRAMTAINT"] = sram_taintfile
    return my_env
