function [7:0] xtime;
    input [7:0] x;
    begin
        xtime = {x[6:0], 1'b0} ^ (8'h1b & {8{x[7]}});
    end
endfunction
