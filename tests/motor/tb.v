
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

reg clk;
initial begin
    clk = 0;
    forever begin
        #10;
        clk = ~clk;
    end
end

reg rst_n;
initial begin
    rst_n <= 1'b0;
    #100;
    rst_n <= 1'b1;
end

`define tick @(posedge clk)
`define wait1(cond) `tick; while(~(cond)) `tick 

reg activate, up_limit, dn_limit;
wire motor_up, motor_dn;

motor motor_0 (.*);

initial begin
    activate <= 0;
    up_limit <= 1; // door is up
    dn_limit <= 0;
    wait(rst_n == 1);
    `tick;
    $display($time, " ACTIVATING");
    activate <= 1;
    `wait1(motor_dn == 1);
    activate <= 0;
    up_limit <= 0;
    `tick;
    `tick;
    `tick;
    `tick;
    $display($time, " REPORTING dn_limit");
    dn_limit <= 1;
    `wait1(motor_dn == 0);
    `tick;

    $display($time, " ACTIVATING");
    activate <= 1;
    `wait1(motor_up == 1);
    activate <= 0;
    dn_limit <= 0;
    `tick;
    `tick;
    `tick;
    `tick;
    `tick;
    `tick;
    $display($time, " REPORTING up_limit");
    up_limit <= 1;
    `wait1(motor_up == 0);
    `tick;

    $display($time, " Normal termination");
    $finish;
end

initial forever begin
    `tick;
    $display($time, " activate ", activate, " up_limit ", up_limit, " dn_limit ", dn_limit,
                    " motor_dn ", motor_dn, " motor_up ", motor_up);
end

initial begin
    #2000;
    $display($time, " Time-out termination");
    $finish;
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

endmodule
