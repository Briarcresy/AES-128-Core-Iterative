// Forward MixColumns transform for one 32-bit AES column.
module mix_column (
    input  wire [31:0] column_in,
    output wire [31:0] column_out
);
    `include "rtl/core/includes/xtime.vh"
    wire [7:0] a = column_in[31:24];
    wire [7:0] b = column_in[23:16];
    wire [7:0] c = column_in[15:8];
    wire [7:0] d = column_in[7:0];
    assign column_out[31:24] = xtime(a) ^ (xtime(b) ^ b) ^ c ^ d;
    assign column_out[23:16] = a ^ xtime(b) ^ (xtime(c) ^ c) ^ d;
    assign column_out[15:8]  = a ^ b ^ xtime(c) ^ (xtime(d) ^ d);
    assign column_out[7:0]   = (xtime(a) ^ a) ^ b ^ c ^ xtime(d);
endmodule
