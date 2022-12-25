`define loop(var, val='b0)  var=val; do begin
`define next(var, limit, incr=1'b1) var=var+incr; end while(var != limit)

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
   reg [2:0] z = 0;
SmForever
    cnt=0;
    while(1) begin
        `loop(z)
            `loop(y)
                `loop(x)
                    cnt = cnt+1;
                    `tick;
                `next(x, 15);
            `next(y, 10);
        `next(z, 5);
    end
SmEnd

assign rgb={cnt, cnt, cnt};

endmodule
