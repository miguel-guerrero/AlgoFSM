module ahb_lite_m 
#(parameter AW=32, DW=32, LOG2_DW=5)
(
    // app side
    input write,
    input req, 
    input [AW-1:0] addr,
    input [DW-1:0] wdata,
    output [DW-1:0] rdata,
    output rdata_vld,

    // AHB side
    output [31:0] HADDR,
    output HWRITE,
    output [2:0] HSIZE,
    output [2:0] HBURST,
    output [3:0] HPROT,
    output [1:0] HTRANS,
    output HMASTLOCK,
    output [DW-1:0] HWDATA,

    input en,
    input HREADY,
    input HRESP,
    output [DW-1:0] HRDATA,
    input HCLK,
    input HRESETn
);

SmBegin
    local reg [4:0] i=0;
    local reg [3:0] count=0; // init value should be optional
    local reg write=0;
    reg [DW-1:0] dout=0;
    reg dout_vld=0;
SmForever
    in_data = 0;
    if (req) begin
        HRADDR = addr;
        if (write) begin
            /// write address phase
            do begin
                HWRITE = 1;
                `tick;
            end while(~HREADY);
            /// write data phase
            do begin
                if (HREADY) begin
                    HWDATA = wdata;
                    HADDR++;
                    i++;
                end
                `tick;
            end while (i != count);
        end 
        else begin
            // read address phase
            do begin
                HWRITE = 0;
                `tick;
            end while(~HREADY);
            /// read data phase
            do begin
                if (HREADY) begin
                    HADDR++;
                    dout = HRDATA;
                    dout_vld = 1;
                    i++;
                end
                else begin
                    dout = {DW{1'bx}};
                    dout_vld = 0;
                end
                `tick;
            end while (i != count);
        end
    end
SmEnd

endmodule
