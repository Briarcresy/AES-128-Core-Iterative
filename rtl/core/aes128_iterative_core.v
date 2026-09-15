// AES-128 encryption-only top level. Ten key-expansion clocks and ten round clocks.
module aes128_iterative_core (
    input  wire         clk,
    input  wire         rst,
    input  wire         start,
    input  wire [127:0] key,
    input  wire [127:0] data_in,
    output reg  [127:0] data_out,
    output wire         busy,
    output wire         done
);
    wire [3:0] round_index, count;
    wire [  1:0] data_sel;
    reg  [127:0] round_keys[1:10];
    wire [127:0] old_key, next_key, round_result, add_round_key_result;
    reg [127:0] data_next;
    wire key_step, final_step;

    assign old_key = (count == 4'd0) ? key : round_keys[count];

    assign round_index = count + 1;

    controller u_controller (
        .clk(clk),
        .rst(rst),
        .start(start),
        .count(count),
        .key_step(key_step),
        .final_step(final_step),
        .data_sel(data_sel),
        .busy(busy),
        .done(done)
    );

    key_expansion u_key_expansion (
        .old_key(old_key),
        .round_index(round_index),
        .new_key(next_key)
    );

    round u_round (
        .state_in(data_out),
        .round_key(round_keys[round_index]),
        .final_round(final_step),
        .state_out(round_result)
    );

    add_round_key u_add_round_key (
        .state_in (data_out),
        .round_key(key),
        .state_out(add_round_key_result)
    );

    always @(posedge clk) begin
        if (key_step) begin
            round_keys[round_index] <= next_key;
        end
    end

    always @(posedge clk) begin
        if (rst) data_out <= 128'd0;
        else data_out <= data_next;
    end

    always @* begin
        case (data_sel)
            2'd0: data_next = data_in;
            2'd1: data_next = add_round_key_result;
            2'd2: data_next = round_result;
            default: data_next = data_out;
        endcase
    end

endmodule
