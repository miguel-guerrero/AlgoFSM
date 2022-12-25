`define wait1(cond) `tick; while(~(cond)) `tick 
`define wait0(cond)        while(~(cond)) `tick 
`define incr(x, val)  x = x + val

module matmul 
#(parameter MEM_AW=16, MEM_DW=32, DIM_BITS=16, PREC=16)
(
    output mem_write, mem_req,
    output [MEM_AW-1:0] mem_addr,
    output [MEM_DW-1:0] mem_wdata, 
    input mem_rdata_vld,
    input [MEM_DW-1:0] mem_rdata,

    input [MEM_AW-1:0] aBASE, bBASE, cBASE,
    input [DIM_BITS-1:0] aSTRIDE, bSTRIDE, cSTRIDE,
    input [DIM_BITS-1:0] aROWS, aCOLS, bCOLS,

    output ret,
    input go,
    input clk,
    input rst_n
);

SmBegin
    reg mem_write = 0;
    reg mem_req = 0;
    reg [MEM_AW-1:0] mem_addr = 0;
    reg [MEM_DW-1:0] mem_wdata = 0; 
    reg [DIM_BITS-1:0] i = 0;
    reg [DIM_BITS-1:0] j = 0;
    reg ret = 0;
SmForever
    ret = 0;
    i = 0;

    `wait0(go);

    `tick;
    while (i != aROWS) begin

        j = 0;
        while (j != aCOLS) begin

            MEM_write(aBASE+aSTRIDE*i+j+1, ~(i+j+1)); 
            `tick;
            MEM_done;
            `incr(j, 1);
        end
        `tick;
        `incr(i, 1);
    end
    ret = 1;
SmEnd

task MEM_write;
    input [MEM_AW-1:0] addr;
    input [MEM_DW-1:0] wdata;
    begin
        {algofsm0.mem_wdata, algofsm0.mem_addr, algofsm0.mem_write} = {wdata, addr, 1'b1};
        algofsm0.mem_req = 1'b1;
    end
endtask

task MEM_read;
    input [MEM_AW-1:0] addr;
    begin
        {algofsm0.mem_addr, algofsm0.mem_write} = {addr, 1'b0};
        algofsm0.mem_req = 1'b1;
    end
endtask

task MEM_done;
    algofsm0.mem_req = 1'b0;
endtask

endmodule
