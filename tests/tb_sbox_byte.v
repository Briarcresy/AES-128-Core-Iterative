`timescale 1ns / 1ps
module tb_sbox_byte;
    reg [7:0] in_byte;
    wire [7:0] out_byte;
    reg [7:0] forward[0:255];
    integer i;

    sbox_byte dut (
        .in_byte (in_byte),
        .out_byte(out_byte)
    );

    initial begin
        $readmemh("mem/sbox.mem", forward);
        for (i = 0; i < 256; i = i + 1) begin
            in_byte = i;
            #1;
            if (out_byte !== forward[i]) begin
                $display("FAIL: S-box address %02h", in_byte);
                $stop;
            end
        end
        $display("S-box ROM: all 256 inputs PASS");
        $finish;
    end
endmodule
