`timescale 1ns/1ps

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

parameter LOG2_DW=5, DW=1<<LOG2_DW;

reg [LOG2_DW-1:0] cBITS_PER_WORD; 

reg sm_ena;
reg clk;
reg rst_n;

spi_slv #(.DW(DW), .LOG2_DW(LOG2_DW)) i_dut (.*); 


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
   cBITS_PER_WORD = 16; 
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
   
   while (~ret_r)
       @(posedge clk);
   @(posedge clk);
   $display($time, " got ret_r");
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
                   " acc=%x", i_dut.acc_r);
`else
   $display($time, " i=", i_dut.algofsm0.i_r, 
                   " j=", i_dut.algofsm0.j_r, 
                   " k=", i_dut.algofsm0.k_r, 
                   " acc=%x", i_dut.acc_r);
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
