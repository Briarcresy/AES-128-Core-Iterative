// Asynchronous 256 x 8 forward AES S-box ROM.
module sbox_byte (
    input  wire [7:0] in_byte,
    output wire [7:0] out_byte
);
    reg [7:0] sbox_rom[0:255];

    // Run simulation/synthesis from the repository root.
    initial $readmemh("mem/sbox.mem", sbox_rom);

    assign out_byte = sbox_rom[in_byte];
endmodule
