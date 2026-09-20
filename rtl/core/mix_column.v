// Forward MixColumns transform for one 32-bit AES column.
module mix_column (
    input  wire [31:0] column_in,
    output wire [31:0] column_out
);
    wire [7:0] a, b, c, d;
    wire [7:0] a2, b2, c2, d2;
    wire [7:0] a3, b3, c3, d3;

    function [7:0] xtime;
        input [7:0] x;
        begin
            xtime = {x[6:0], 1'b0} ^ (8'h1b & {8{x[7]}});
        end
    endfunction

    assign a = column_in[31:24];
    assign b = column_in[23:16];
    assign c = column_in[15:8];
    assign d = column_in[7:0];
    // Multiply by 2 in GF(2^8): shift, then conditionally XOR 0x1b.
    assign a2 = xtime(a);
    assign b2 = xtime(b);
    assign c2 = xtime(c);
    assign d2 = xtime(d);

    assign a3 = a2 ^ a;
    assign b3 = b2 ^ b;
    assign c3 = c2 ^ c;
    assign d3 = d2 ^ d;

    assign column_out[31:24] = a2 ^ b3 ^ c ^ d;
    assign column_out[23:16] = a ^ b2 ^ c3 ^ d;
    assign column_out[15:8] = a ^ b ^ c2 ^ d3;
    assign column_out[7:0] = a3 ^ b ^ c ^ d2;
endmodule
