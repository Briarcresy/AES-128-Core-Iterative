// One encryption round, reused in all ten processing cycles.
module round (
    input  wire [127:0] state_in,
    input  wire [127:0] round_key,
    input  wire         final_round,
    output wire [127:0] state_out
);
    wire [127:0] after_sub, after_shift, after_mix;
    wire [127:0] before_key;

    sub_bytes u_sub_bytes (
        .state_in(state_in), .state_out(after_sub)
    );
    shift_rows u_shift_rows (
        .state_in(after_sub), .state_out(after_shift)
    );
    mix_columns u_mix_columns (
        .state_in(after_shift), .state_out(after_mix)
    );
    assign before_key = final_round ? after_shift : after_mix;
    add_round_key u_add_round_key (
        .state_in(before_key), .round_key(round_key), .state_out(state_out)
    );
endmodule
