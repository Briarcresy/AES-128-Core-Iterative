`timescale 1ns / 1ps
module tb_sbox_rom;
    reg clk, enable;
    reg [7:0] address;
    wire [7:0] data;
    reg [7:0] expected [0:255];
    integer i;

    always #5 clk = ~clk;

    sbox_rom dut (
        .clk(clk), .enable(enable), .address(address), .data(data)
    );

    initial begin
        $readmemh("mem/sbox.mem", expected);
        clk = 1'b0;
        enable = 1'b0;
        address = 8'd0;

        for (i = 0; i < 256; i = i + 1) begin
            @(negedge clk);
            address = i[7:0];
            enable = 1'b1;
            @(posedge clk);
            #1;
            if (data !== expected[i]) begin
                $display("FAIL: address=%02h got=%02h expected=%02h", i, data, expected[i]);
                $finish;
            end
        end

        @(negedge clk);
        enable = 1'b0;
        address = 8'h00;
        @(posedge clk);
        #1;
        if (data !== expected[255]) begin
            $display("FAIL: output changed while ROM was disabled");
            $finish;
        end

        $display("S-box synchronous ROM: PASS");
        $finish;
    end
endmodule
