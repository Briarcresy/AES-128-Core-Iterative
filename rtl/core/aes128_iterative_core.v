// Connects the controller, key schedule, state path, and one shared S-box ROM.
module aes128_iterative_core (
    input wire clk,
    input wire rst,
    input wire start,
    input wire [127:0] key,
    input wire [127:0] data_in,
    output wire [127:0] data_out,
    output wire busy,
    output wire done
);
    wire load_input, key_request, key_capture, key_update;
    wire state_request, state_capture, mix_step, add_key_step;
    wire [1:0] key_byte_index, column_index;
    wire [4:0] state_byte_index;
    wire [3:0] round_index;
    wire [127:0] round_key;
    wire [127:0] state_reg;
    wire [7:0] key_rom_address, state_rom_address, rom_data;
    reg [7:0] rom_address;
    wire rom_enable = key_request | state_request;

    assign data_out = state_reg;

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
        .key_byte_index(key_byte_index),
        .state_byte_index(state_byte_index),
        .column_index(column_index),
        .round_index(round_index),
        .busy(busy),
        .done(done)
    );

    key_schedule u_key_schedule (
        .clk(clk),
        .rst(rst),
        .load_input(load_input),
        .key_in(key),
        .key_capture(key_capture),
        .key_update(key_update),
        .key_byte_index(key_byte_index),
        .round_index(round_index),
        .rom_data(rom_data),
        .rom_address(key_rom_address),
        .round_key(round_key)
    );

    state_path u_state_path (
        .clk(clk),
        .rst(rst),
        .load_input(load_input),
        .data_in(data_in),
        .initial_key(key),
        .round_key(round_key),
        .state_capture(state_capture),
        .mix_step(mix_step),
        .add_key_step(add_key_step),
        .state_byte_index(state_byte_index),
        .column_index(column_index),
        .rom_data(rom_data),
        .rom_address(state_rom_address),
        .state_reg(state_reg)
    );

    // The two datapaths take turns using the same ROM.
    always @* begin
        rom_address = 8'd0;
        if (key_request) rom_address = key_rom_address;
        else if (state_request) rom_address = state_rom_address;
    end

    sbox_rom_adapter u_sbox_rom (
        .clk(clk),
        .enable(rom_enable),
        .address(rom_address),
        .data(rom_data)
    );
endmodule
