// 32-bit shared-IO wrapper for the iterative AES-128 encryption core.
module Aes128Iterative #(
    parameter IO_WIDTH = 66
) (
    input  wire                clock,
    input  wire                reset,
    input  wire [IO_WIDTH-1:0] io_in,
    output wire [IO_WIDTH-1:0] io_out,
    output wire [IO_WIDTH-1:0] io_oe
);

    reg  [127:0] key_reg;
    reg  [127:0] plaintext_reg;
    reg  [127:0] ciphertext_reg;
    reg  [ 31:0] ciphertext_word;
    reg          done_reg;

    wire [  1:0] word_index;
    wire         input_select;
    wire         write_enable;
    wire         start;
    wire         read_enable;
    wire         write_allowed;
    wire         write_key;
    wire         write_plaintext;
    wire         word_select_0;
    wire         word_select_1;
    wire         word_select_2;
    wire         word_select_3;
    wire [127:0] core_data_out;
    wire         core_busy;
    wire         core_done;

    assign word_index      = io_in[33:32];
    assign input_select    = io_in[34];
    assign write_enable    = io_in[35];
    assign start           = io_in[36];
    assign read_enable     = io_in[37];

    assign write_allowed   = write_enable & ~core_busy;
    assign write_key       = write_allowed & input_select;
    assign write_plaintext = write_allowed & ~input_select;

    assign word_select_0   = ~word_index[1] & ~word_index[0];
    assign word_select_1   = ~word_index[1] & word_index[0];
    assign word_select_2   = word_index[1] & ~word_index[0];
    assign word_select_3   = word_index[1] & word_index[0];

    aes128_iterative_core u_core (
        .clk     (clock),
        .rst     (reset),
        .start   (start),
        .key     (key_reg),
        .data_in (plaintext_reg),
        .data_out(core_data_out),
        .busy    (core_busy),
        .done    (core_done)
    );

    always @(posedge clock) begin
        if (reset) key_reg[127:96] <= 32'd0;
        else if (write_key & word_select_0) key_reg[127:96] <= io_in[31:0];
    end

    always @(posedge clock) begin
        if (reset) key_reg[95:64] <= 32'd0;
        else if (write_key & word_select_1) key_reg[95:64] <= io_in[31:0];
    end

    always @(posedge clock) begin
        if (reset) key_reg[63:32] <= 32'd0;
        else if (write_key & word_select_2) key_reg[63:32] <= io_in[31:0];
    end

    always @(posedge clock) begin
        if (reset) key_reg[31:0] <= 32'd0;
        else if (write_key & word_select_3) key_reg[31:0] <= io_in[31:0];
    end

    always @(posedge clock) begin
        if (reset) plaintext_reg[127:96] <= 32'd0;
        else if (write_plaintext & word_select_0) plaintext_reg[127:96] <= io_in[31:0];
    end

    always @(posedge clock) begin
        if (reset) plaintext_reg[95:64] <= 32'd0;
        else if (write_plaintext & word_select_1) plaintext_reg[95:64] <= io_in[31:0];
    end

    always @(posedge clock) begin
        if (reset) plaintext_reg[63:32] <= 32'd0;
        else if (write_plaintext & word_select_2) plaintext_reg[63:32] <= io_in[31:0];
    end

    always @(posedge clock) begin
        if (reset) plaintext_reg[31:0] <= 32'd0;
        else if (write_plaintext & word_select_3) plaintext_reg[31:0] <= io_in[31:0];
    end

    always @(posedge clock) begin
        if (reset) ciphertext_reg <= 128'd0;
        else if (core_done) ciphertext_reg <= core_data_out;
    end

    always @(posedge clock) begin
        if (reset) done_reg <= 1'b0;
        else done_reg <= core_done;
    end

    always @* begin
        case (word_index)
            2'd0: ciphertext_word = ciphertext_reg[127:96];
            2'd1: ciphertext_word = ciphertext_reg[95:64];
            2'd2: ciphertext_word = ciphertext_reg[63:32];
            default: ciphertext_word = ciphertext_reg[31:0];
        endcase
    end

    assign io_out[31:0] = read_enable ? ciphertext_word : 32'd0;
    assign io_oe[31:0] = {32{read_enable}};

    assign io_out[37:32] = 6'd0;
    assign io_oe[37:32] = 6'd0;

    assign io_out[38] = core_busy;
    assign io_oe[38] = 1'b1;
    assign io_out[39] = done_reg;
    assign io_oe[39] = 1'b1;

    assign io_out[IO_WIDTH-1:40] = {(IO_WIDTH - 40) {1'b0}};
    assign io_oe[IO_WIDTH-1:40] = {(IO_WIDTH - 40) {1'b0}};

endmodule
