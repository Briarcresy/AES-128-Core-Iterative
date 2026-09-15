// Produce one new 128-bit encryption round key from the previous key.
module key_expansion (
    input  wire [127:0] old_key,
    input  wire [  3:0] round_index,
    output reg  [127:0] new_key
);

    `include "rtl/core/includes/xtime.vh"

    localparam [7:0] RCON1 = 8'h01;
    localparam [7:0] RCON2 = xtime(RCON1);
    localparam [7:0] RCON3 = xtime(RCON2);
    localparam [7:0] RCON4 = xtime(RCON3);
    localparam [7:0] RCON5 = xtime(RCON4);
    localparam [7:0] RCON6 = xtime(RCON5);
    localparam [7:0] RCON7 = xtime(RCON6);
    localparam [7:0] RCON8 = xtime(RCON7);
    localparam [7:0] RCON9 = xtime(RCON8);
    localparam [7:0] RCON10 = xtime(RCON9);

    wire [31:0] rotated, substituted;
    reg [31:0] w0, w1, w2, w3, temp;
    reg [7:0] rcon;

    assign rotated = {old_key[23:0], old_key[31:24]};
    genvar byte_index;
    generate
        for (byte_index = 0; byte_index < 4; byte_index = byte_index + 1) begin
            sbox_byte u_sbox (
                .in_byte (rotated[31-8*byte_index-:8]),
                .out_byte(substituted[31-8*byte_index-:8])
            );
        end
    endgenerate

    always @* begin
        case (round_index)
            4'd1: rcon = RCON1;
            4'd2: rcon = RCON2;
            4'd3: rcon = RCON3;
            4'd4: rcon = RCON4;
            4'd5: rcon = RCON5;
            4'd6: rcon = RCON6;
            4'd7: rcon = RCON7;
            4'd8: rcon = RCON8;
            4'd9: rcon = RCON9;
            4'd10: rcon = RCON10;
            default: rcon = 8'h00;
        endcase
    end

    always @* begin
        temp = substituted ^ {rcon, 24'h0};
        w0 = old_key[127:96] ^ temp;
        w1 = old_key[95:64] ^ w0;
        w2 = old_key[63:32] ^ w1;
        w3 = old_key[31:0] ^ w2;
        new_key = {w0, w1, w2, w3};
    end
endmodule
