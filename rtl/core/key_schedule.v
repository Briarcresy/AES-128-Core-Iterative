// Holds the current round key and reuses the shared S-box for SubWord.
module key_schedule (
    input wire clk,
    input wire rst,
    input wire [1:0] key_reg_sel,
    input wire [127:0] key_in,
    input wire key_capture,
    input wire [1:0] key_byte_index,
    input wire [3:0] round_index,
    input wire [7:0] rom_data,
    output reg [7:0] rom_address,
    output reg [127:0] round_key
);
    reg  [31:0] key_temp_reg;
    reg  [31:0] key_temp_next;
    reg  [ 7:0] rcon;
    wire [31:0] w0 = round_key[127:96];
    wire [31:0] w1 = round_key[95:64];
    wire [31:0] w2 = round_key[63:32];
    wire [31:0] w3 = round_key[31:0];
    wire [31:0] new_w0 = w0 ^ key_temp_reg ^ {rcon, 24'h000000};
    wire [31:0] new_w1 = w1 ^ new_w0;
    wire [31:0] new_w2 = w2 ^ new_w1;
    wire [31:0] new_w3 = w3 ^ new_w2;
    reg [127:0] round_key_next;

    // Controller drives the input MUX of the round-key register.
    always @* begin
        case (key_reg_sel)
            2'd1: round_key_next = key_in;
            2'd2: round_key_next = {new_w0, new_w1, new_w2, new_w3};
            default: round_key_next = round_key;
        endcase
    end

    // RotWord: the final byte of the old key moves to the end.
    always @* begin
        case (key_byte_index)
            2'd0: rom_address = round_key[23:16];
            2'd1: rom_address = round_key[15:8];
            2'd2: rom_address = round_key[7:0];
            default: rom_address = round_key[31:24];
        endcase
    end

    always @* begin
        case (round_index)
            4'd1: rcon = 8'h01;
            4'd2: rcon = 8'h02;
            4'd3: rcon = 8'h04;
            4'd4: rcon = 8'h08;
            4'd5: rcon = 8'h10;
            4'd6: rcon = 8'h20;
            4'd7: rcon = 8'h40;
            4'd8: rcon = 8'h80;
            4'd9: rcon = 8'h1b;
            4'd10: rcon = 8'h36;
            default: rcon = 8'h00;
        endcase
    end

    // Each byte has a hold/ROM-data input MUX, selected by the controller.
    always @* begin
        key_temp_next = key_temp_reg;
        if (key_capture) begin
            case (key_byte_index)
                2'd0: key_temp_next[31:24] = rom_data;
                2'd1: key_temp_next[23:16] = rom_data;
                2'd2: key_temp_next[15:8] = rom_data;
                default: key_temp_next[7:0] = rom_data;
            endcase
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            key_temp_reg <= 32'd0;
            round_key <= 128'd0;
        end else begin
            key_temp_reg <= key_temp_next;
            round_key <= round_key_next;
        end
    end
endmodule
