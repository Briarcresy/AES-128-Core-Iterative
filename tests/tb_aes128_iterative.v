`timescale 1ns / 1ps
module tb_aes128_iterative;
    reg clk, rst, start;
    reg [127:0] key, data_in;
    wire [127:0] data_out;
    wire busy, done;
    integer cycles;

    always #5 clk = ~clk;

    aes128_iterative_core dut (
        .clk(clk),
        .rst(rst),
        .start(start),
        .key(key),
        .data_in(data_in),
        .data_out(data_out),
        .busy(busy),
        .done(done)
    );

    task check;
        input [127:0] test_key, plaintext, expected;
        begin
            @(negedge clk);
            key = test_key;
            data_in = plaintext;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            if (!busy) begin
                $display("FAIL: busy not asserted");
                $stop;
            end
            if (data_out !== dut.state_reg) begin
                $display("FAIL: data_out must follow state_reg");
                $stop;
            end
            cycles = 0;
            while (!done && cycles < 500) begin
                @(negedge clk);
                cycles = cycles + 1;
            end
            if (!done || cycles != 456) begin
                $display("FAIL: wrong latency: %0d cycles", cycles);
                $stop;
            end
            if (data_out !== expected) begin
                $display("FAIL: got %032h expected %032h", data_out, expected);
                $stop;
            end
            if (busy) begin
                $display("FAIL: busy not deasserted");
                $stop;
            end
            @(negedge clk);
            if (done) begin
                $display("FAIL: done must be one clock wide");
                $stop;
            end
        end
    endtask

    initial begin
        clk = 1'b0;
        rst = 1'b1;
        start = 1'b0;
        key = 128'd0;
        data_in = 128'd0;
        repeat (2) @(negedge clk);
        rst = 1'b0;
        check(128'h000102030405060708090a0b0c0d0e0f, 128'h00112233445566778899aabbccddeeff,
              128'h69c4e0d86a7b0430d8cdb78070b4c55a);
        check(128'h00000000000000000000000000000000, 128'h00000000000000000000000000000000,
              128'h66e94bd4ef8a2c3b884cfa59ca342b2e);
        check(128'h2b7e151628aed2a6abf7158809cf4f3c, 128'h6bc1bee22e409f96e93d7e117393172a,
              128'h3ad77bb40d7a3660a89ecaf32466ef97);
        check(128'h2b7e151628aed2a6abf7158809cf4f3c, 128'hae2d8a571e03ac9c9eb76fac45af8e51,
              128'hf5d3d58503b9699de785895a96fdbaaf);
        check(128'h2b7e151628aed2a6abf7158809cf4f3c, 128'h30c81c46a35ce411e5fbc1191a0a52ef,
              128'h43b1cd7f598ece23881b00e3ed030688);
        check(128'h2b7e151628aed2a6abf7158809cf4f3c, 128'hf69f2445df4f9b17ad2b417be66c3710,
              128'h7b0c785e27e8ad3f8223207104725dd4);
        $display("AES-128 encryption RTL: PASS");
        $finish;
    end
endmodule
