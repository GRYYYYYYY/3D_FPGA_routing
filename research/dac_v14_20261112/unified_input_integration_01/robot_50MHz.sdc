# Integration timing instance: 50 MHz, 1 ns maximum external I/O delay.
# This is a declared benchmark target, not an externally supplied application requirement.
create_clock -period 20 clk
set_input_delay -clock clk -max 1 [get_ports {*} ]
set_input_delay -clock clk -min 0 [get_ports {*} ]
set_output_delay -clock clk -max 1 [get_ports {*} ]
set_output_delay -clock clk -min 0 [get_ports {*} ]
