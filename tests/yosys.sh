set -e
. ../env.sh
export VERILOG_INPUT
export INSTRUMENTATION
for SV_INPUT in verilog/t_param_local.v
do
    export VERILOG_INPUT=$SV_INPUT.v
    sv2v $SV_INPUT >$VERILOG_INPUT
    echo sv2v $?
    for INSTRUMENTATION in vanilla glift cellift
    do
        export VERILOG_OUTPUT=$VERILOG_INPUT.$INSTRUMENTATION.out
        export TOP_MODULE=t
        yosys -c ../design-processing/common/yosys/instrument.ys.tcl 
    done
done
