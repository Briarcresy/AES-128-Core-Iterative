// Replace the example behavior while preserving the five-port frame contract.

module Aes128Iterative #(
    parameter int IO_WIDTH = 66
) (
    input  logic                clock,
    input  logic                reset,
    input  logic [IO_WIDTH-1:0] io_in,
    output logic [IO_WIDTH-1:0] io_out,
    output logic [IO_WIDTH-1:0] io_oe
);

    logic heartbeat;

    always_ff @(posedge clock) begin
        if (reset) heartbeat <= 1'b0;
        else heartbeat <= ~heartbeat;
    end

    always_comb begin
        io_out = '0;
        io_oe = '0;
        io_out[0] = heartbeat;
        io_oe[0] = 1'b1;
        io_out[1] = io_in[2];
        io_oe[1] = 1'b1;
    end

endmodule
