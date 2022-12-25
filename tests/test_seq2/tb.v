
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
reg go;
reg clk;
reg rst_n;

matmul 
`ifndef GLS
#(.MEM_AW(MEM_AW), .MEM_DW(MEM_DW), .DIM_BITS(DIM_BITS), .PREC(PREC)) 
`endif
i_dut (.*); 

mem #(.MEM_AW(MEM_AW), .MEM_DW(MEM_DW)) i_mem (.*);

initial begin
    clk = 1;
    forever begin
        #5;
        clk = ~clk;
    end
end

initial begin
   #1; // allow dump to start before
   $display($time, " TEST starts");
   $display($time, " Reseting");
   go = 0;
   i_mem.init_incr;
   aBASE = 0; 
   bBASE = 'h100;
   cBASE = 'h200;
   aSTRIDE = 4;
   bSTRIDE = 4; 
   cSTRIDE = 4;
   aROWS = 4;
   aCOLS = 4;
   bCOLS = 4;
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
   #50;
   go = 0;
   while (~ret)
       @(posedge clk);
   $display($time, " got ret");
   #10;
   $display("A"); i_mem.dump('h000, 16);
   $display("B"); i_mem.dump('h100, 16);
   $display("C"); i_mem.dump('h200, 16);
   $display($time, " ending");
   #90;
   $finish;
end


always @(posedge clk) begin
   #0;
   $display($time, " i=", i_dut.i);
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
