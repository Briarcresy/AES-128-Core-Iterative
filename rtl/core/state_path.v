// Holds the AES state and performs the round transformations.
module state_path (
    input wire clk,
    input wire rst,
    input wire load_input,
    input wire [127:0] data_in,
    input wire [127:0] initial_key,
    input wire [127:0] round_key,
    input wire state_capture,
    input wire mix_step,
    input wire add_key_step,
    input wire [4:0] state_byte_index,
    input wire [1:0] column_index,
    input wire [7:0] rom_data,
    output reg [7:0] rom_address,
    output reg [127:0] state_reg
);
    reg [127:0] state_temp_reg;
    reg [31:0] mix_input;
    wire [31:0] mix_output;
    wire [127:0] round_output = state_temp_reg ^ round_key;

    mix_column u_mix_column (
        .column_in(mix_input), .column_out(mix_output)
    );

    // Select source bytes in ShiftRows order; store ROM results in order.
    always @* begin
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
        end else begin
            if (load_input) state_reg <= data_in ^ initial_key;
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
            if (add_key_step) state_reg <= round_output;
        end
    end
endmodule
