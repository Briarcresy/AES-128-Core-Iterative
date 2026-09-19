// Holds the AES state and performs the round transformations.
module state_path (
    input wire clk,
    input wire rst,
    input wire [1:0] state_reg_sel,
    input wire [127:0] plaintext,
    input wire [127:0] initial_key,
    input wire [127:0] round_key,
    input wire state_capture,
    input wire mix_step,
    input wire [4:0] state_byte_index,
    input wire [1:0] column_index,
    input wire [7:0] rom_data,
    output reg [7:0] rom_address,
    output reg [127:0] state_reg
);
    reg  [127:0] state_temp_reg;
    wire [127:0] shifted_state;
    reg  [ 31:0] mix_input;
    wire [ 31:0] mix_output;
    wire [127:0] initial_state;
    wire [127:0] round_output;
    reg  [127:0] state_reg_next;
    reg  [127:0] state_temp_next;

    add_round_key u_initial_add_key (
        .state_in (plaintext),
        .round_key(initial_key),
        .state_out(initial_state)
    );

    add_round_key u_round_add_key (
        .state_in (state_temp_reg),
        .round_key(round_key),
        .state_out(round_output)
    );

    mix_column u_mix_column (
        .column_in (mix_input),
        .column_out(mix_output)
    );

    shift_rows u_shift_rows (
        .state_in (state_reg),
        .state_out(shifted_state)
    );

    // Controller selects one of three inputs to the state register.
    always @* begin
        case (state_reg_sel)
            2'd1: state_reg_next = initial_state;
            2'd2: state_reg_next = round_output;
            default: state_reg_next = state_reg;
        endcase
    end

    // A 16-to-1 byte MUX chooses one wired ShiftRows output for the ROM.
    always @* begin
        case (state_byte_index)
            5'd0: rom_address = shifted_state[127:120];
            5'd1: rom_address = shifted_state[119:112];
            5'd2: rom_address = shifted_state[111:104];
            5'd3: rom_address = shifted_state[103:96];
            5'd4: rom_address = shifted_state[95:88];
            5'd5: rom_address = shifted_state[87:80];
            5'd6: rom_address = shifted_state[79:72];
            5'd7: rom_address = shifted_state[71:64];
            5'd8: rom_address = shifted_state[63:56];
            5'd9: rom_address = shifted_state[55:48];
            5'd10: rom_address = shifted_state[47:40];
            5'd11: rom_address = shifted_state[39:32];
            5'd12: rom_address = shifted_state[31:24];
            5'd13: rom_address = shifted_state[23:16];
            5'd14: rom_address = shifted_state[15:8];
            default: rom_address = shifted_state[7:0];
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

    // The temporary-state register has a hold/ROM/MixColumns input MUX.
    always @* begin
        state_temp_next = state_temp_reg;
        if (state_capture) begin
            case (state_byte_index)
                5'd0: state_temp_next[127:120] = rom_data;
                5'd1: state_temp_next[119:112] = rom_data;
                5'd2: state_temp_next[111:104] = rom_data;
                5'd3: state_temp_next[103:96] = rom_data;
                5'd4: state_temp_next[95:88] = rom_data;
                5'd5: state_temp_next[87:80] = rom_data;
                5'd6: state_temp_next[79:72] = rom_data;
                5'd7: state_temp_next[71:64] = rom_data;
                5'd8: state_temp_next[63:56] = rom_data;
                5'd9: state_temp_next[55:48] = rom_data;
                5'd10: state_temp_next[47:40] = rom_data;
                5'd11: state_temp_next[39:32] = rom_data;
                5'd12: state_temp_next[31:24] = rom_data;
                5'd13: state_temp_next[23:16] = rom_data;
                5'd14: state_temp_next[15:8] = rom_data;
                default: state_temp_next[7:0] = rom_data;
            endcase
        end
        if (mix_step) begin
            case (column_index)
                2'd0: state_temp_next[127:96] = mix_output;
                2'd1: state_temp_next[95:64] = mix_output;
                2'd2: state_temp_next[63:32] = mix_output;
                default: state_temp_next[31:0] = mix_output;
            endcase
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            state_reg <= 128'd0;
            state_temp_reg <= 128'd0;
        end else begin
            state_reg <= state_reg_next;
            state_temp_reg <= state_temp_next;
        end
    end
endmodule
