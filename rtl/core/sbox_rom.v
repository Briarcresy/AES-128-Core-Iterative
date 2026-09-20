// One synchronous AES S-box ROM shared by the state and key datapaths.
module sbox_rom (
    input  wire       clk,
    input  wire       enable,
    input  wire [7:0] address,
    output wire [7:0] data
);
    ics55_ecos_rom_256x8_m8_b1
`ifndef SYNTHESIS
    #(
        .codefile("pdk/IP/ROM/ics55_ecos_rom_256x8_m8_b1/verilog/ics55_ecos_rom_256x8_m8_b1.romcode")
    )
`endif
    u_rom (
        .A(address),
        .CEB(~enable),
        .CLK(clk),
        .MARE(1'b0),
        .MAR(4'b0000),
        .Q(data)
    );
endmodule
