module tpg 
#(parameter PW=8, H_BITS=12, V_BITS=12)
(
   output hs,
   output vs,
   output [3*PW-1:0] rgb,
   output vld,
   input [H_BITS-1:0] tHS_START,
   input [H_BITS-1:0] tHS_END,
   input [H_BITS-1:0] tHACT_START,
   input [H_BITS-1:0] tHACT_END,
   input [H_BITS-1:0] tH_END,
   input [V_BITS-1:0] tVS_START,
   input [V_BITS-1:0] tVS_END,
   input [V_BITS-1:0] tVACT_START,
   input [V_BITS-1:0] tVACT_END,
   input [H_BITS-1:0] tV_END,
   input clk,
   input rst_n
);

SmBegin
   reg hs = 1'b0, vs = 1'b0, vld = 1'b0, y_active = 1'b0;
   reg [PW-1:0] cnt = 8'b0;
   reg [H_BITS-1:0] x = 0;
   reg [V_BITS-1:0] y = 0;
SmForever
    y=0;
    do begin
        x = 0;
        do begin

            if (x == tHS_START)
                hs = 1;
            else if (x == tHS_END)
                hs = 0;

            if (x == tHACT_START)
                vld = y_active;
            else if (x == tHACT_END)
                vld = 1'b0;

            if (vld)
                cnt = cnt + 1;

            x = x + 1'b1;
            `tick;
        end while (x != tH_END);

        if (y == tVS_START)
            vs = 1;
        else if (y == tVS_END)
            vs = 0;

        if (y == tVACT_START)
            y_active = 1'b1;
        else if (y == tVACT_END) 
            y_active = 1'b0;

        `tick;
        y=y+1;
    end while (y != tV_END);
SmEnd

assign rgb={cnt, cnt, cnt};

endmodule
