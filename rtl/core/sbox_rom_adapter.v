// One synchronous AES S-box ROM shared by the state and key datapaths.
module sbox_rom_adapter (
    input  wire       clk,
    input  wire       enable,
    input  wire [7:0] address,
    output reg  [7:0] data
);
`ifdef SYNTHESIS
    ics55_ecos_rom_256x8_m8_b1 u_rom (
        .A(address),
        .CEB(~enable),
        .CLK(clk),
        .MARE(1'b0),
        .MAR(4'b0000),
        .Q(data)
    );
`else
    reg [7:0] rom[0:255];
    initial
        $readmemb("ip/ics55_ecos_rom_256x8_m8_b1/verilog/ics55_ecos_rom_256x8_m8_b1.romcode", rom);
    always @(posedge clk) begin
        if (enable) data <= rom[address];
    end
`endif
endmodule
