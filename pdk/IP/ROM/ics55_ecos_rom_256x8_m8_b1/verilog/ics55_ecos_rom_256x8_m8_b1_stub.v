`resetall
`timescale 10ps/1ps
`celldefine

module ics55_ecos_rom_256x8_m8_b1 (
`ifdef POWER_PIN
    VSS,
    VDD,
`endif
    MAR,
    Q,
    MARE,
    A,
    CLK,
    CEB
  );

  // Match the codefile parameter of the vendor simulation model.
  parameter codefile = "verilog/ics55_ecos_rom_256x8_m8_b1.romcode";


  input [7:0] A;
  input CEB;
  input CLK;
  input [3:0] MAR;
  input MARE;
  output [7:0] Q;
`ifdef POWER_PIN
  inout VSS;
  supply0 VSS;
  inout VDD;
  supply1 VDD;
`endif



endmodule
`endcelldefine


