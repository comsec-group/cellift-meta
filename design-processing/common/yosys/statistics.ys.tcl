# Copyright 2022 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

if { [info exists ::env(VERILOG_INPUT)] }    { set VERILOG_INPUT $::env(VERILOG_INPUT) } else { puts "Please set VERILOG_INPUT environment variable"; exit 1 }
if { [info exists ::env(TOP_MODULE)] }       { set TOP_MODULE $::env(TOP_MODULE) } else { puts "Please set TOP_MODULE environment variable"; exit 1 }
if { [info exists ::env(DECOMPOSE_MEMORY)] } { set DECOMPOSE_MEMORY $::env(DECOMPOSE_MEMORY) } else { set DECOMPOSE_MEMORY 0 }
if { [info exists ::env(INSTRUMENTATION)] }  { set INSTRUMENTATION $::env(INSTRUMENTATION) } else { puts "Please set INSTRUMENTATION environment variable"; exit 1 }

yosys read_verilog -defer -sv $VERILOG_INPUT
yosys hierarchy -top $TOP_MODULE -check
yosys timestamp hierarchy
yosys proc
yosys timestamp proc
yosys opt -purge
yosys timestamp opt

if {$DECOMPOSE_MEMORY == 1} {
    yosys memory
    yosys timestamp memory
    yosys proc
    yosys timestamp proc
    yosys opt -purge
    yosys timestamp opt
}

if {[string equal $INSTRUMENTATION "glift"]} {
    yosys techmap
    yosys timestamp techmap
    yosys breakdown_glift -exclude-mux
    yosys timestamp breakdown_glift
}

if { [string equal $INSTRUMENTATION "glift"] || [string equal $INSTRUMENTATION "cellift"] } {
    yosys pmuxtree
    yosys timestamp pmuxtree
    yosys mul_to_adds
    yosys timestamp mul_to_adds
    yosys opt -purge
    yosys timestamp opt
    yosys cellift -exclude-signals clk_i,rst_ni,clock,reset,reset_wire_reset -imprecise-shl-sshl -verbose
    if {[string equal $INSTRUMENTATION "glift"]} {
        yosys breakdown_glift -exclude-mux
    }
    yosys timestamp cellift
    yosys opt -purge
    yosys timestamp opt
} elseif { ![string equal $INSTRUMENTATION "vanilla"] && ![string equal $INSTRUMENTATION "passthrough"] && [info exists INSTRUMENTATION] } {
    puts [format "Please unset INSTRUMENTATION environment variable, or set it either to cellift or to glift or vanilla (is currently: %s)" $INSTRUMENTATION]
    exit 1
}

yosys list_state_elements
yosys timestamp list_state_elements
yosys stat
yosys timestamp stat
yosys timestamp end
