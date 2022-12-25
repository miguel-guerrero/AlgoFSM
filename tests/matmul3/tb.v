
module tb;

`ifdef BEHAV
   initial $display("#RUNNING BEHAVIORAL code");
`else
   `ifdef GLS
      initial $display("#RUNNING GLS code");
   `else
      initial $display("#RUNNING RTL code");
   `endif
`endif

parameter MEM_AW=16, MEM_DW=32, DIM_BITS=16, PREC=16;

wire mem_write, mem_req;
wire [MEM_AW-1:0] mem_addr;
wire [MEM_DW-1:0] mem_wdata;
wire mem_rdata_vld;
wire [MEM_DW-1:0] mem_rdata;

reg [MEM_AW-1:0] aBASE; 
reg [MEM_AW-1:0] bBASE; 
reg [MEM_AW-1:0] cBASE;
reg [DIM_BITS-1:0] aSTRIDE; 
reg [DIM_BITS-1:0] bSTRIDE; 
reg [DIM_BITS-1:0] cSTRIDE; 
reg [DIM_BITS-1:0] aROWS;
reg [DIM_BITS-1:0] aCOLS;
reg [DIM_BITS-1:0] bCOLS;

wire ret;
reg sm_ena;
reg go;
reg clk;
reg rst_n;

matmul #(.MEM_AW(MEM_AW), .MEM_DW(MEM_DW), .DIM_BITS(DIM_BITS), .PREC(PREC)) i_dut (.*); 
mem #(.MEM_AW(MEM_AW), .MEM_DW(MEM_DW)) i_mem (.*);

initial begin
    clk = 1;
    forever begin
        #5;
        clk = ~clk;
    end
end

initial begin
   #1; // allow dump to open 1st
   $display($time, " TEST starts");
   $display($time, " Reseting");
   go = 0;
   sm_ena = 1;
   i_mem.init_incr;
   aBASE = 'h100; 
   bBASE = 'h200;
   cBASE = 'h300;
   aROWS = 6;
   aCOLS = 4;
   bCOLS = 5;
   aSTRIDE = 8;
   bSTRIDE = 8; 
   cSTRIDE = 8;
   rst_n = 0;
   #99;
   rst_n = 1;
   #500;
   $display($time, " Reseting");
   rst_n = 0;
   #100;
   rst_n = 1;
   #295;
   $display($time, " Start");
   go = 1;
   #105;
   go = 0;
   #300
   sm_ena = 0;
   #200
   sm_ena = 1;
   
   while (~ret)
       @(posedge clk);
   @(posedge clk);
   $display($time, " got ret");
   #100;
   $display("A"); i_mem.dump(aBASE, aROWS*aSTRIDE);
   $display("B"); i_mem.dump(bBASE, aCOLS*bSTRIDE);
   $display("C"); i_mem.dump(cBASE, aROWS*cSTRIDE);
   $display($time, " ending");
   $finish;
end


always @(posedge clk) begin
   #0;
`ifdef GLS
   $display($time, " i=", i_dut.\algofsm0.i_r , 
                   " j=", i_dut.\algofsm0.j_r , 
                   " k=", i_dut.\algofsm0.k_r , 
                   " acc=%x", i_dut.acc);
`else
   $display($time, " i=", i_dut.algofsm0.i_r, 
                   " j=", i_dut.algofsm0.j_r, 
                   " k=", i_dut.algofsm0.k_r, 
                   " acc=%x", i_dut.acc);
`endif
end

initial begin
`ifdef BEHAV
   $dumpfile("tb.beh.vcd");
`else
   `ifdef GLS
       $dumpfile("tb.gls.vcd");
   `else
       $dumpfile("tb.sm.vcd");
   `endif
`endif
   $dumpvars;
end

initial begin
   #1000;
   repeat(1000 + aROWS*aCOLS*aROWS*bCOLS*10)
      @(posedge clk);

   $display($time, " ending timeout");
   $finish;
end

endmodule
