
`define wait1(cond) `tick; while(~(cond)) `tick 

module motor(
    input clk, activate, up_limit, dn_limit, rst_n,
    output motor_up, motor_dn
);

SmBegin
   reg motor_up = 0;
   reg motor_dn = 0;
SmForever
   if (up_limit) begin
      `wait1(activate);
      motor_dn = 1;
      `wait1(dn_limit);
      motor_dn = 0;
   end
   else begin
      `wait1(activate);
      motor_up = 1;
      `wait1(up_limit);
      motor_up = 0;
   end
SmEnd

endmodule
