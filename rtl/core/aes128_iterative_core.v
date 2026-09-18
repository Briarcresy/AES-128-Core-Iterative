// AES-128 encryption core using one shared synchronous S-box ROM.
module aes128_iterative_core (
    input wire clk,
    input wire rst,
    input wire start,
    input wire [127:0] key,
    input wire [127:0] data_in,
    output reg [127:0] data_out,
    output wire busy,
    output wire done
);
    reg [127:0] state_reg, state_temp_reg, key_reg;
    reg [31:0] key_temp_reg;
    wire load_input, key_request, key_capture, key_update;
    wire state_request, state_capture, mix_step, add_key_step, final_round;
    wire [1:0] key_byte_index, column_index;
    wire [4:0] state_byte_index;
    wire [3:0] round_index;
    reg [7:0] rom_address, rcon;
    wire rom_enable = key_request | state_request;
    wire [7:0] rom_data;
    wire [31:0] w0 = key_reg[127:96];
    wire [31:0] w1 = key_reg[95:64];
    wire [31:0] w2 = key_reg[63:32];
    wire [31:0] w3 = key_reg[31:0];
    wire [31:0] new_w0 = w0 ^ key_temp_reg ^ {rcon, 24'h000000};
    wire [31:0] new_w1 = w1 ^ new_w0;
    wire [31:0] new_w2 = w2 ^ new_w1;
    wire [31:0] new_w3 = w3 ^ new_w2;
    wire [127:0] next_round_key = {new_w0, new_w1, new_w2, new_w3};
    reg [31:0] mix_input;
    wire [31:0] mix_output;
    wire [127:0] round_output = state_temp_reg ^ key_reg;

    controller u_controller (
        .clk(clk),
        .rst(rst),
        .start(start),
        .load_input(load_input),
        .key_request(key_request),
        .key_capture(key_capture),
        .key_update(key_update),
        .state_request(state_request),
        .state_capture(state_capture),
        .mix_step(mix_step),
        .add_key_step(add_key_step),
        .final_round(final_round),
        .key_byte_index(key_byte_index),
        .state_byte_index(state_byte_index),
        .column_index(column_index),
        .round_index(round_index),
        .busy(busy),
        .done(done)
    );
    sbox_rom_adapter u_sbox_rom (
        .clk(clk),
        .enable(rom_enable),
        .address(rom_address),
        .data(rom_data)
    );
    mix_column u_mix_column (
        .column_in (mix_input),
        .column_out(mix_output)
    );

    // The state address mapping performs ShiftRows while SubBytes is read.
    always @* begin
        rom_address = 8'd0;
        if (key_request) begin
            case (key_byte_index)
                2'd0: rom_address = key_reg[23:16];
                2'd1: rom_address = key_reg[15:8];
                2'd2: rom_address = key_reg[7:0];
                default: rom_address = key_reg[31:24];
            endcase
        end else if (state_request) begin
            case (state_byte_index)
                5'd0: rom_address = state_reg[127:120];
                5'd1: rom_address = state_reg[87:80];
                5'd2: rom_address = state_reg[47:40];
                5'd3: rom_address = state_reg[7:0];
                5'd4: rom_address = state_reg[95:88];
                5'd5: rom_address = state_reg[55:48];
                5'd6: rom_address = state_reg[15:8];
                5'd7: rom_address = state_reg[103:96];
                5'd8: rom_address = state_reg[63:56];
                5'd9: rom_address = state_reg[23:16];
                5'd10: rom_address = state_reg[111:104];
                5'd11: rom_address = state_reg[71:64];
                5'd12: rom_address = state_reg[31:24];
                5'd13: rom_address = state_reg[119:112];
                5'd14: rom_address = state_reg[79:72];
                default: rom_address = state_reg[39:32];
            endcase
        end
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

    always @* begin
        case (column_index)
            2'd0: mix_input = state_temp_reg[127:96];
            2'd1: mix_input = state_temp_reg[95:64];
            2'd2: mix_input = state_temp_reg[63:32];
            default: mix_input = state_temp_reg[31:0];
        endcase
    end

    always @(posedge clk) begin
        if (rst) begin
            state_reg <= 128'd0;
            state_temp_reg <= 128'd0;
            key_reg <= 128'd0;
            key_temp_reg <= 32'd0;
            data_out <= 128'd0;
        end else begin
            if (load_input) begin
                state_reg <= data_in ^ key;
                key_reg   <= key;
            end
            if (key_capture) begin
                case (key_byte_index)
                    2'd0: key_temp_reg[31:24] <= rom_data;
                    2'd1: key_temp_reg[23:16] <= rom_data;
                    2'd2: key_temp_reg[15:8] <= rom_data;
                    default: key_temp_reg[7:0] <= rom_data;
                endcase
            end
            if (key_update) key_reg <= next_round_key;
            if (state_capture) begin
                case (state_byte_index)
                    5'd0: state_temp_reg[127:120] <= rom_data;
                    5'd1: state_temp_reg[119:112] <= rom_data;
                    5'd2: state_temp_reg[111:104] <= rom_data;
                    5'd3: state_temp_reg[103:96] <= rom_data;
                    5'd4: state_temp_reg[95:88] <= rom_data;
                    5'd5: state_temp_reg[87:80] <= rom_data;
                    5'd6: state_temp_reg[79:72] <= rom_data;
                    5'd7: state_temp_reg[71:64] <= rom_data;
                    5'd8: state_temp_reg[63:56] <= rom_data;
                    5'd9: state_temp_reg[55:48] <= rom_data;
                    5'd10: state_temp_reg[47:40] <= rom_data;
                    5'd11: state_temp_reg[39:32] <= rom_data;
                    5'd12: state_temp_reg[31:24] <= rom_data;
                    5'd13: state_temp_reg[23:16] <= rom_data;
                    5'd14: state_temp_reg[15:8] <= rom_data;
                    default: state_temp_reg[7:0] <= rom_data;
                endcase
            end
            if (mix_step) begin
                case (column_index)
                    2'd0: state_temp_reg[127:96] <= mix_output;
                    2'd1: state_temp_reg[95:64] <= mix_output;
                    2'd2: state_temp_reg[63:32] <= mix_output;
                    default: state_temp_reg[31:0] <= mix_output;
                endcase
            end
            if (add_key_step) begin
                state_reg <= round_output;
                if (final_round) data_out <= round_output;
            end
        end
    end
endmodule
