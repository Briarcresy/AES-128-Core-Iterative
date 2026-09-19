// Controls the byte-serial S-box ROM and the iterative AES rounds.
module controller (
    input wire clk,
    input wire rst,
    input wire start,
    output wire load_input,
    output wire key_request,
    output wire key_capture,
    output wire key_update,
    output wire state_request,
    output wire state_capture,
    output wire mix_step,
    output wire add_key_step,
    output reg [1:0] key_byte_index,
    output reg [4:0] state_byte_index,
    output reg [1:0] column_index,
    output reg [3:0] round_index,
    output wire busy,
    output reg done
);
    localparam [3:0] IDLE = 4'd0, KEY_REQUEST = 4'd1,
        KEY_CAPTURE = 4'd2, KEY_UPDATE = 4'd3,
        STATE_REQUEST = 4'd4, STATE_CAPTURE = 4'd5,
        MIX_COLUMN = 4'd6, ADD_KEY = 4'd7;
    reg [3:0] phase;

    assign load_input = (phase == IDLE) && start;
    assign key_request = (phase == KEY_REQUEST);
    assign key_capture = (phase == KEY_CAPTURE);
    assign key_update = (phase == KEY_UPDATE);
    assign state_request = (phase == STATE_REQUEST);
    assign state_capture = (phase == STATE_CAPTURE);
    assign mix_step = (phase == MIX_COLUMN);
    assign add_key_step = (phase == ADD_KEY);
    assign busy = (phase != IDLE);

    always @(posedge clk) begin
        if (rst) begin
            phase <= IDLE;
            key_byte_index <= 2'd0;
            state_byte_index <= 5'd0;
            column_index <= 2'd0;
            round_index <= 4'd0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            case (phase)
                IDLE:
                if (start) begin
                    key_byte_index <= 2'd0;
                    round_index <= 4'd1;
                    phase <= KEY_REQUEST;
                end
                KEY_REQUEST: phase <= KEY_CAPTURE;
                KEY_CAPTURE: begin
                    if (key_byte_index == 2'd3) begin
                        key_byte_index <= 2'd0;
                        phase <= KEY_UPDATE;
                    end else begin
                        key_byte_index <= key_byte_index + 2'd1;
                        phase <= KEY_REQUEST;
                    end
                end
                KEY_UPDATE: begin
                    state_byte_index <= 5'd0;
                    phase <= STATE_REQUEST;
                end
                STATE_REQUEST: phase <= STATE_CAPTURE;
                STATE_CAPTURE: begin
                    if (state_byte_index == 5'd15) begin
                        state_byte_index <= 5'd0;
                        column_index <= 2'd0;
                        if (round_index == 4'd10) phase <= ADD_KEY;
                        else phase <= MIX_COLUMN;
                    end else begin
                        state_byte_index <= state_byte_index + 5'd1;
                        phase <= STATE_REQUEST;
                    end
                end
                MIX_COLUMN: begin
                    if (column_index == 2'd3) begin
                        column_index <= 2'd0;
                        phase <= ADD_KEY;
                    end else column_index <= column_index + 2'd1;
                end
                ADD_KEY: begin
                    if (round_index == 4'd10) begin
                        done  <= 1'b1;
                        phase <= IDLE;
                    end else begin
                        round_index <= round_index + 4'd1;
                        key_byte_index <= 2'd0;
                        phase <= KEY_REQUEST;
                    end
                end
                default: phase <= IDLE;
            endcase
        end
    end
endmodule
