`define wait1(cond) `tick; while(~(cond)) `tick 
`define wait0(cond)        while(~(cond)) `tick 
`define incr(x) x=x+1'b1

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
    input sm_ena,
    input clk,
    input rst_n
);

wire sm_ena0 = sm_ena;

SmBegin
   local reg [DIM_BITS-1:0] i=0, j=0, k=0;
   local reg [MEM_AW-1:0] a_i0=0, a_ik=0, b_0j=0, b_kj=0, c_i0=0, c_ij=0;
   reg ret=0, mem_write=0, mem_req=0, row_end=0;
   reg [MEM_AW-1:0] mem_addr=0;
   reg [MEM_DW-1:0] mem_wdata=0;
SmForever
    ret = 0;

    `wait1(go);
    a_i0 = aBASE;
    c_i0 = cBASE;
    i = 0;
    `tick;
    while (i != aROWS) begin
        /// rows loop
        c_ij = c_i0;
        b_0j = bBASE;

        j = 0;
        `tick;
        while (j != aCOLS) begin
            /// cols loop
            a_ik = a_i0;
            b_kj = b_0j;
            k = 0;
            while (k != bCOLS) begin
                /// dot product loop
                `tick; MEM_read(a_ik); `incr(a_ik);
                `tick; MEM_read(b_kj); b_kj = b_kj + bSTRIDE; 
                `incr(k);
            end
            MEM_done;
            row_end=1;
            `wait1(acc_rdy);
            MEM_write(c_ij, acc); `incr(b_0j); `incr(c_ij); `incr(j); row_end=0;
        end
        MEM_done;
        c_i0 = c_i0 + cSTRIDE;
        a_i0 = a_i0 + aSTRIDE;
        `incr(i);
        `tick;
    end
    ret = 1;
    `tick;
SmEnd

wire sm_ena1 = sm_ena;
SmBegin
   local reg [PREC-1:0] a=0, b=0;
   reg [MEM_DW-1:0] acc=0;
   reg acc_rdy=0;
SmForever
    acc=0;
    acc_rdy=0;
    do begin
        `wait1(mem_rdata_vld);
        a = mem_rdata;
        `wait1(mem_rdata_vld);
        b = mem_rdata;
        acc = acc + a[PREC-1:0]*b[PREC-1:0];
    end while (~row_end);
    acc_rdy=1;
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
