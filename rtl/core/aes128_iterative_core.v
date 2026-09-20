// Connects the controller, key schedule, state path, and one shared S-box ROM.
module aes128_iterative_core (
    input wire clk,
    input wire rst,
    input wire start,
    input wire [127:0] key,
    input wire [127:0] plaintext,
    output wire [127:0] ciphertext,
    output wire busy,
    output wire done
);
    wire key_request, key_capture;
    wire state_request, state_capture, mix_step;
    wire [1:0] key_byte_index, column_index;
    wire [4:0] state_byte_index;
    wire [3:0] round_index;
    wire [1:0] key_reg_sel, state_reg_sel;
    wire [127:0] round_key;
    wire [127:0] state_reg;
    wire [7:0] key_rom_address, state_rom_address, rom_data;
    wire [7:0] rom_address;
    wire rom_enable;

    assign ciphertext  = state_reg;
    assign rom_enable  = key_request | state_request;
    // Two 8-bit input MUXes select which datapath addresses the shared ROM.
    assign rom_address = key_request ? key_rom_address : state_request ? state_rom_address : 8'd0;

    controller u_controller (
        .clk(clk),
        .rst(rst),
        .start(start),
        .key_request(key_request),
        .key_capture(key_capture),
        .state_request(state_request),
        .state_capture(state_capture),
        .mix_step(mix_step),
        .key_reg_sel(key_reg_sel),
        .state_reg_sel(state_reg_sel),
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
        .key_reg_sel(key_reg_sel),
        .key_in(key),
        .key_capture(key_capture),
        .key_byte_index(key_byte_index),
        .round_index(round_index),
        .rom_data(rom_data),
        .rom_address(key_rom_address),
        .round_key(round_key)
    );

    state_path u_state_path (
        .clk(clk),
        .rst(rst),
        .state_reg_sel(state_reg_sel),
        .plaintext(plaintext),
        .initial_key(key),
        .round_key(round_key),
        .state_capture(state_capture),
        .mix_step(mix_step),
        .state_byte_index(state_byte_index),
        .column_index(column_index),
        .rom_data(rom_data),
        .rom_address(state_rom_address),
        .state_reg(state_reg)
    );

    sbox_rom u_sbox_rom (
        .clk(clk),
        .enable(rom_enable),
        .address(rom_address),
        .data(rom_data)
    );
endmodule
