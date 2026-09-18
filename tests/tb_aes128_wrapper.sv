`timescale 1ns / 1ps

module tb_aes128_wrapper;
    localparam int IO_WIDTH = 66;

    logic clock = 1'b0;
    logic reset = 1'b1;
    logic [IO_WIDTH-1:0] io_in = '0;
    wire  [IO_WIDTH-1:0] io_out;
    wire  [IO_WIDTH-1:0] io_oe;
    logic [127:0] result;

    always #5 clock = ~clock;

    Aes128Iterative dut (
        .clock(clock), .reset(reset), .io_in(io_in),
        .io_out(io_out), .io_oe(io_oe)
    );

    task write_word;
        input select_key;
        input [1:0] index;
        input [31:0] value;
        begin
            @(negedge clock);
            io_in[31:0]  = value;
            io_in[33:32] = index;
            io_in[34]    = select_key;
            io_in[35]    = 1'b1;
            @(negedge clock);
            io_in[35]    = 1'b0;
        end
    endtask

    task read_word;
        input [1:0] index;
        output [31:0] value;
        begin
            @(negedge clock);
            io_in[33:32] = index;
            io_in[37] = 1'b1;
            @(posedge clock);
            #1;
            value = io_out[31:0];
            if (io_oe[31:0] !== 32'hffff_ffff)
                $fatal(1, "data bus output-enable is incorrect");
            @(negedge clock);
            io_in[37] = 1'b0;
        end
    endtask

    initial begin
        repeat (2) @(posedge clock);
        @(negedge clock);
        reset = 1'b0;

        write_word(1'b1, 2'd0, 32'h00010203);
        write_word(1'b1, 2'd1, 32'h04050607);
        write_word(1'b1, 2'd2, 32'h08090a0b);
        write_word(1'b1, 2'd3, 32'h0c0d0e0f);

        write_word(1'b0, 2'd0, 32'h00112233);
        write_word(1'b0, 2'd1, 32'h44556677);
        write_word(1'b0, 2'd2, 32'h8899aabb);
        write_word(1'b0, 2'd3, 32'hccddeeff);

        @(negedge clock);
        io_in[36] = 1'b1;
        @(negedge clock);
        io_in[36] = 1'b0;

        wait (io_out[39] === 1'b1);
        #1;
        if (io_out[38] !== 1'b0)
            $fatal(1, "busy must be low when the wrapper reports done");

        read_word(2'd0, result[127:96]);
        read_word(2'd1, result[95:64]);
        read_word(2'd2, result[63:32]);
        read_word(2'd3, result[31:0]);

        if (result !== 128'h69c4e0d86a7b0430d8cdb78070b4c55a)
            $fatal(1, "wrapper ciphertext mismatch: %032h", result);

        if (io_oe[39:38] !== 2'b11 || io_oe[65:40] !== '0)
            $fatal(1, "wrapper output-enable mapping is incorrect");

        $display("AES-128 wrapper test: PASS");
        $finish;
    end
endmodule
