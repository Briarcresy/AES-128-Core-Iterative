// Fixed byte wiring for AES ShiftRows; no register or arithmetic is needed.
module shift_rows (
    input  wire [127:0] state_in,
    output reg  [127:0] state_out
);
    always @* begin
        // Output column 0: rows come from input columns 0, 1, 2, 3.
        state_out[127:120] = state_in[127:120];
        state_out[119:112] = state_in[87:80];
        state_out[111:104] = state_in[47:40];
        state_out[103:96]  = state_in[7:0];

        // Output column 1.
        state_out[95:88] = state_in[95:88];
        state_out[87:80] = state_in[55:48];
        state_out[79:72] = state_in[15:8];
        state_out[71:64] = state_in[103:96];

        // Output column 2.
        state_out[63:56] = state_in[63:56];
        state_out[55:48] = state_in[23:16];
        state_out[47:40] = state_in[111:104];
        state_out[39:32] = state_in[71:64];

        // Output column 3.
        state_out[31:24] = state_in[31:24];
        state_out[23:16] = state_in[119:112];
        state_out[15:8]  = state_in[79:72];
        state_out[7:0]   = state_in[39:32];
    end
endmodule
