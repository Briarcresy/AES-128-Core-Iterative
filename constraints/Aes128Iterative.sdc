# FPGA and ASIC use the same test clock.
set clock_frequency_mhz $::env(CLK_FREQ_MHZ)
set clock_period_ns [expr 1000.0 / $clock_frequency_mhz]
set clock_half_period_ns [expr $clock_period_ns / 2.0]
create_clock -name test_clock -period $clock_period_ns \
    -waveform [list 0.0 $clock_half_period_ns] [get_ports clock]

# Yosys flattens io_in[0] to io_in_0_ in the gate-level netlist.
set input_ports [list reset]
for {set i 0} {$i < 66} {incr i} {
    lappend input_ports "io_in_${i}_"
}

# FPGA changes these inputs on a falling edge.
set_input_delay -clock test_clock -clock_fall -max 10.000 [get_ports $input_ports]
set_input_delay -clock test_clock -clock_fall -min 0.000  [get_ports $input_ports]

# Build the exact flattened names for both 66-bit output buses.
set output_ports [list]
for {set i 0} {$i < 66} {incr i} {
    lappend output_ports "io_out_${i}_" "io_oe_${i}_"
}

# FPGA samples ASIC outputs using the same clock.
set_output_delay -clock test_clock -max 10.000 [get_ports $output_ports]
set_output_delay -clock test_clock -min 0.000  [get_ports $output_ports]

# A simple allowance for clock jitter and clock-distribution uncertainty.
set_clock_uncertainty 0.000 [get_clocks test_clock]
