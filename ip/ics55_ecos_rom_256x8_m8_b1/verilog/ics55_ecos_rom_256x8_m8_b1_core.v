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

  parameter codefile = "verilog/ics55_ecos_rom_256x8_m8_b1.romcode";
  reg [7:0] rom_core [255:0];
  initial
  begin
    $readmemb( codefile, rom_core, 0, 255 );
  end

  reg [7:0] Q_buf;

  always@ (posedge CLK)
  begin
    if( CEB == 1'b0 )
    Q_buf <= rom_core[A];
  end

  assign Q = Q_buf;



endmodule

