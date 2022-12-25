module mem (
    // inputs
    clk,
    mem_wdata,
    mem_addr,
    mem_req,
    mem_write,

    // output
    mem_rdata,
    mem_rdata_vld     
);

parameter MEM_AW = 12;
parameter MEM_DW = 32;
parameter MEM_DEPTH = 1 << MEM_AW;

input                      clk;
input  [MEM_AW-1:0]        mem_addr;
input  [MEM_DW-1:0]        mem_wdata;
input                      mem_req;
input                      mem_write;
output reg [MEM_DW-1:0]    mem_rdata;
output reg                 mem_rdata_vld;


reg [MEM_DW-1:0]           raw_mem_rdata;
reg                        raw_mem_rdata_vld;
reg [MEM_DW:0]             bank[0:MEM_DEPTH-1];

    wire active_wr = mem_req &  mem_write;
    wire active_rd = mem_req & ~mem_write;
    wire active    = active_wr | active_rd;

    always @(posedge clk) begin : write
        mem_rdata <= #1 raw_mem_rdata;
        mem_rdata_vld <= #1 raw_mem_rdata_vld;
        if (active_wr) begin
            bank[mem_addr] <= #1 mem_wdata;
            $display($time, " MEM[%x] <= %x %m", mem_addr, mem_wdata);
        end
    end


    always @(posedge clk) begin :  read
        if (active_rd) begin
            $display($time, " MEM[%x] => %x %m", mem_addr,  bank[mem_addr]);
            raw_mem_rdata <= #1 bank[mem_addr];
            raw_mem_rdata_vld <= #1 1'b1;
        end    
        else begin
            raw_mem_rdata <= #1 {MEM_DW{1'bx}};
            raw_mem_rdata_vld <= #1 1'b0;
        end 
    end

    always @(posedge clk) begin : read_dly
        mem_rdata <= #1 raw_mem_rdata;
        mem_rdata_vld <= #1 raw_mem_rdata_vld;
    end

    task init_random;
        reg [3:0] n;
        integer i;
        begin
            $display ($time, " init_random called %m", $time);
            for (i = 0; i < (1 << MEM_AW); i=i+1) begin
                n = $random;
                bank[i] = n;
            end
        end
    endtask	 

    task init_decr;
        integer i;
        begin
            $display ($time, " init_decr called %m", $time);
            for (i = 0; i < (1 << MEM_AW); i=i+1) begin
                bank[i] = ~i;
            end
        end
    endtask	 

    task init_incr;
        integer i;
        begin
            $display ($time, " init_incr called %m", $time);
            for (i = 0; i < (1 << MEM_AW); i=i+1) begin
                bank[i] = i;
            end
        end
    endtask	 

    task dump;
        input [MEM_AW-1:0] addr;
        input [MEM_AW:0] len;
        integer i;
        begin
            for (i = 0; i < len; i=i+1) begin
                $display("[%d] => %x", addr+i, bank[addr+i]);
            end
        end
    endtask

endmodule

