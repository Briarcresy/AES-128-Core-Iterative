// Forward MixColumns, one independent transform per AES state column.
module mix_columns (
    input  wire [127:0] state_in,
    output wire [127:0] state_out
);
    `include "rtl/core/includes/xtime.vh"

    genvar col;
    generate
        for (col = 0; col < 4; col = col + 1) begin
            wire [7:0] a = state_in[127-32*col-:8];
            wire [7:0] b = state_in[119-32*col-:8];
            wire [7:0] c = state_in[111-32*col-:8];
            wire [7:0] d = state_in[103-32*col-:8];

            assign state_out[127-32*col-:8] = xtime(a) ^ (xtime(b) ^ b) ^ c ^ d;
            assign state_out[119-32*col-:8] = a ^ xtime(b) ^ (xtime(c) ^ c) ^ d;
            assign state_out[111-32*col-:8] = a ^ b ^ xtime(c) ^ (xtime(d) ^ d);
            assign state_out[103-32*col-:8] = (xtime(a) ^ a) ^ b ^ c ^ xtime(d);
        end
    endgenerate
endmodule
