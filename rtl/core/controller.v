// Controls ten key-expansion cycles followed by ten round cycles.
module controller (
    input  wire       clk,
    input  wire       rst,
    input  wire       start,
    output reg  [3:0] count,
    output wire       final_step,
    output wire       key_step,
    output reg  [1:0] data_sel,
    output wire       busy,
    output reg        done
);
    localparam [1:0] IDLE = 2'd0, EXPAND = 2'd1, ROUND = 2'd2;
    reg [1:0] phase;

    // wire accept; 
    // wire round_step;

    // assign accept = (phase == IDLE) && start;
    assign key_step = (phase == EXPAND);
    // assign round_step = (phase == ROUND);
    assign final_step = (count == 4'd9);
    assign busy = (phase != IDLE);

    always @* begin
        if (phase == IDLE) data_sel = 2'd0;
        else if (phase == EXPAND && final_step) data_sel = 2'd1;
        else if (phase == ROUND) data_sel = 2'd2;
        else data_sel = 2'd3;
    end

    always @(posedge clk) begin
        if (rst) begin
            phase <= IDLE;
            count <= 4'd0;
            done  <= 1'b0;
        end else begin
            done <= 1'b0;
            case (phase)
                IDLE:
                if (start) begin
                    count <= 4'd0;
                    phase <= EXPAND;
                end
                EXPAND:
                if (final_step) begin
                    count <= 4'd0;
                    phase <= ROUND;
                end else count <= count + 4'd1;
                ROUND:
                if (final_step) begin
                    done  <= 1'b1;
                    phase <= IDLE;
                end else count <= count + 4'd1;
                default: phase <= IDLE;
            endcase
        end
    end
endmodule
