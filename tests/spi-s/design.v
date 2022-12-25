`include "../../common/control.vh"

module spi_slv 
#(parameter DW=32, LOG2_DW=5)
(
    input sclk,
    input mosi,
    input ss,
    output miso,

    output [DW-1:0] rxd,
    output rxd_vld,

    input [LOG2_DW-1:0] cBITS_PER_WORD,
    input en,
    input clk,
    input rst_n
);

wire sm_en0 = en;
SmBegin
    local reg [LOG2_DW-1:0] i=0;
    reg [DW-1:0] word=0;
SmForever
    rxd_vld = 0;
    word = 0;
    `loop(i)
        `tick;
        if (~ss) begin
            word = (word << 1) | mosi;
        end
    `next(i, cBITS_PER_WORD);
    rxd = word;
    rxd_vld = 1;
SmEnd

endmodule
