// AES state byte (row, col) is stored at index 4*col + row.
module shift_rows (
    input  wire [127:0] state_in,
    output wire [127:0] state_out
);
    genvar col, row;
    generate
        for (col = 0; col < 4; col = col + 1) begin
            for (row = 0; row < 4; row = row + 1) begin
                assign state_out[127-8*(4*col+row) -: 8] =
                    state_in[127-8*(4*((col+row)%4)+row) -: 8];
            end
        end
    endgenerate
endmodule
