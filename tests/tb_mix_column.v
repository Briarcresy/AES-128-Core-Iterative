`timescale 1ns / 1ps
module tb_mix_column;
    reg [31:0] column_in;
    wire [31:0] column_out;

    mix_column dut (.column_in(column_in), .column_out(column_out));

    initial begin
        column_in = 32'hdb135345;
        #1;
        if (column_out !== 32'h8e4da1bc) begin
            $display("FAIL: got=%08h expected=8e4da1bc", column_out);
            $finish;
        end

        column_in = 32'hf20a225c;
        #1;
        if (column_out !== 32'h9fdc589d) begin
            $display("FAIL: got=%08h expected=9fdc589d", column_out);
            $finish;
        end

        $display("Single-column MixColumns: PASS");
        $finish;
    end
endmodule
