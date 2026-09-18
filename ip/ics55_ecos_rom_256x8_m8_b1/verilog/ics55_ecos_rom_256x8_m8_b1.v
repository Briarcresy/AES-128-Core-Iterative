//macro define notes:
//1. POWER_PIN
//   if define it, add power pin in top module
//2. NO_MESSAGE
//   if define it, all warning/error message will not appear
//3. MEMFAULTINJ
//   if define it, enable fault injection feature
//4. TX_TIMING_UNIT
//   if define it, use typical corner timing
//5. TX_INITIALIZE_FAULT
//    Initialize the memory fault data in verilog format

`timescale 10ps/1ps

`ifdef TX_TIMING_UNIT
`define ACEM 1
`else
`define ACEM 0.1
`endif





module ics55_ecos_rom_256x8_m8_b1 (
`ifdef POWER_PIN
    VDD, VSS,
`endif
    A, CEB, CLK, 
    MARE, MAR,
    Q
);

`define    TRUE                1'b1
`define    FALSE               1'b0

parameter Q_NO_TOG = 0;
parameter MarginW = 4;
parameter Words   = 256;
parameter Bits    = 8;
parameter Mux     = 8;
parameter Bank    = 1;
parameter Addr    = 8;
parameter MuxAddr = 3.0;
parameter Trcqx = `ACEM*(54.7);
parameter Trcqx_7 = `ACEM*(54.7);
parameter leftio = 4;
parameter rightio = 4;

`ifdef POWER_PIN
inout VDD;
inout VSS;
`endif

input [7 : 0] A; 
input CLK;
input CEB;
input MARE;
input [3 : 0] MAR;

output [7 : 0] Q;

`protect 

`ifdef TX_INITIALIZE_FAULT
reg [Bits-1:0] mem_fault  [Words-1:0];
reg [Bits-1:0] Pre_Loading2 [Words-1:0];
`endif
reg [Bits-1:0] mem [Words-1:0];
reg [Bits-1:0] Pre_Loading [Words-1:0];

event EVQ;

reg [Addr-1:0] Last_A;
reg [Addr-1:0] latch_Last_A;

wire [Addr-1:0]    A_buf;
wire               CEB_buf;
wire               MARE_buf;
wire [MarginW-1:0] MAR_buf;
wire [Bits-1:0]    Q_buf;

reg [Addr-1:0]     A_int;
reg                CEB_int;

reg [Addr-1:0]     Latch_A;
reg                Latch_CEB;
reg              Latch_MARE;
reg  [MarginW-1:0] Latch_MAR;

reg [Bits-1:0]     Q_int;
reg [Bits-1:0]     Q_tmp;
reg [Bits-1:0]     Q_reg;

integer i;
reg [Bits-1:0] mem_fault_array_XOR [Words-1:0];
reg [Bits-1:0] mem_fault_array_sa0 [Words-1:0];
reg [Bits-1:0] mem_fault_array_sa1 [Words-1:0];
reg faultinj_en;
reg [Bits-1:0] mem_XOR_data;
initial
begin
    faultinj_en = 1'b0;
    `ifdef MEMFAULTINJ
    faultinj_en = 1'b1;
    `endif
    for(i=0; i<Words; i=i+1)
    begin
        if(faultinj_en == 1'b1)
            mem_fault_array_XOR[i] = {Bits{1'b0}};
        else
        begin
            mem_fault_array_sa0[i] = {Bits{1'b1}};
            mem_fault_array_sa1[i] = {Bits{1'b0}};
        end
    end
    if (faultinj_en == 1'b1)
    begin
        if($test$plusargs("asap_error"))
            mem_fault_array_XOR[1] = 1'b1 << (Bits - 1);
    end
end
                   
//define for timing  flag
wire sdfcond_A;
wire sdfcond_MAR;
wire sdfcond_MARE;
wire sdfcond_CEB;
wire sdfcond_CLK;
wire sdfcond_CLK7;

assign sdfcond_A    = ~CEB_buf ;
assign sdfcond_MAR    = ~CEB_buf ;
assign sdfcond_MARE    = ~CEB_buf ;

assign sdfcond_CLK = ~CEB_buf  & ~MARE;
assign sdfcond_CLK7 = ~CEB_buf  & MARE & !MAR[3] & MAR[2] & MAR[1] & MAR[0] ;
assign sdfcond_CLK  = ~CEB_buf ;

reg Tflag_MAR;
reg Tflag_MARE;
reg Tflag_A7;
reg Tflag_A6;
reg Tflag_A5;
reg Tflag_A4;
reg Tflag_A3;
reg Tflag_A2;
reg Tflag_A1;
reg Tflag_A0;
reg [Addr-1:0] Tflag_A_bus;
reg Tflag_CEB;
reg Tflag_CLK_period ;
reg Tflag_CLK_high_pluse ;
reg Tflag_CLK_low_pluse ;

reg Last_Tflag_A7 ;
reg Last_Tflag_A6 ;
reg Last_Tflag_A5 ;
reg Last_Tflag_A4 ;
reg Last_Tflag_A3 ;
reg Last_Tflag_A2 ;
reg Last_Tflag_A1 ;
reg Last_Tflag_A0 ;
reg [Addr-1:0] Last_Tflag_A_bus;
reg Last_Tflag_CEB ;
reg Last_Tflag_CLK_period ;
reg Last_Tflag_CLK_high_pluse ;
reg Last_Tflag_CLK_low_pluse ;
//enddefine for timing flag

buf Abuf7  (A_buf[7], A[7]);
buf Abuf6  (A_buf[6], A[6]);
buf Abuf5  (A_buf[5], A[5]);
buf Abuf4  (A_buf[4], A[4]);
buf Abuf3  (A_buf[3], A[3]);
buf Abuf2  (A_buf[2], A[2]);
buf Abuf1  (A_buf[1], A[1]);
buf Abuf0  (A_buf[0], A[0]);

buf CEBbuf (CEB_buf, CEB);

buf MAREbuf  (MARE_buf, MARE);
buf MARbuf0  (MAR_buf[0], MAR[0]);
buf MARbuf1  (MAR_buf[1], MAR[1]);
buf MARbuf2  (MAR_buf[2], MAR[2]);
buf MARbuf3  (MAR_buf[3], MAR[3]);




buf Qbuf7  (Q[7], Q_buf[7]);
buf Qbuf6  (Q[6], Q_buf[6]);
buf Qbuf5  (Q[5], Q_buf[5]);
buf Qbuf4  (Q[4], Q_buf[4]);
buf Qbuf3  (Q[3], Q_buf[3]);
buf Qbuf2  (Q[2], Q_buf[2]);
buf Qbuf1  (Q[1], Q_buf[1]);
buf Qbuf0  (Q[0], Q_buf[0]);

assign Q_buf = Q_int;

reg CEBxCLK_buf;
wire CEBxCLK;
reg CEBxCLK_latency_buf;
wire CEBxCLK_SDF;
initial
begin
    CEBxCLK_buf = 1'b0;
    CEBxCLK_latency_buf = 1'b0;
end
always@(posedge CLK)
begin 
    CEBxCLK_latency_buf = CEBxCLK_buf;
    CEBxCLK_buf = CEB_buf;
end
buf CEBCLK1 (CEBxCLK, CEBxCLK_buf);
xor CEBCLK2 (CEBxCLK_SDF, CEBxCLK_buf, CEBxCLK_latency_buf);

parameter INIT_DELAY = 0.1;
parameter codefile = "verilog/ics55_ecos_rom_256x8_m8_b1.romcode";

initial
begin
    #(INIT_DELAY);
    PreLoadData(codefile);
end

`ifdef TX_INITIALIZE_FAULT
parameter codefile2 = "ics55_ecos_rom_256x8_m8_b1.fault.code";
initial
begin
    `ifdef INIT_CODE_FORMAT_BIN
    $readmemb(codefile2, Pre_Loading2, 0, Words-1);
    `else
    $readmemh(codefile2, Pre_Loading2, 0, Words-1);
    `endif
    for(i=0; i < Words; i=i+1) 
    begin
        mem_fault[i] = Pre_Loading2[i];
    end
end
`endif 


//   1. power pin check
`ifdef POWER_PIN
always@(VDD) 
begin
    if (VDD !== 1'b1 && $realtime !=0 ) begin
        `ifdef NO_MESSAGE
        `else
        $display("Error_Message: Power down, memory data is destroyed at %t in %m", $time);
        `endif
    end
end
always@(VSS) 
begin
    if (VSS !== 1'b0 && $realtime !=0 ) begin
        `ifdef NO_MESSAGE
        `else
        $display("Error_Message: Ground power don't equal to 0, memory data is destroyed at %t in %m", $time);
        `endif
    end
end
`endif 

//1. mare, marc deffault value check
always@(posedge CLK)
begin
    if (MARE_buf === 1'bx && CEB_buf === 1'b0)
    begin
        `ifdef NO_MESSAGE
        `else
        $display("Error_Message: MARE is unknown in %m, at %t", $realtime);
        `endif
        Q_int = {Bits{1'bx}};
    end

    if (^MAR_buf === 1'bx && CEB_buf === 1'b0)
    begin
        `ifdef NO_MESSAGE
        `else
        $display("Error_Message: MAR is unknown in %m, at %t", $realtime);
        `endif
        Q_int = {Bits{1'bx}};
    end

    if (MARE_buf === 1'b1 && CEB_buf === 1'b0)
    begin
        if ((MAR_buf === 4'b0111) && $realtime != 0) begin
        end
        else begin
            `ifdef NO_MESSAGE
            `else
            $display("Error_Message: The MAR must be 4'b0111  when MARE=1'b1 at %t", $realtime);
            $display("Error_Message: The MAR value please refer to datasheet, please check it");
            `endif
        end
    end
end


always@(
    A_buf or
    CEB_buf or
    MAR_buf or
    MARE_buf
)
begin
    #0.1;
    Latch_A = A_buf;
    Latch_CEB = CEB_buf;
    Latch_MAR = MAR_buf;
    Latch_MARE = MARE_buf;
end

always@(posedge CLK) //posedge clock 
begin
    if ($realtime != 0)
    begin 
            Last_A = latch_Last_A;
            memory_active;
            latch_Last_A = A_buf;
    end
end

always@(
   Tflag_A7 or
   Tflag_A6 or
   Tflag_A5 or
   Tflag_A4 or
   Tflag_A3 or
   Tflag_A2 or
   Tflag_A1 or
   Tflag_A0 or
   Tflag_CEB or
   Tflag_CLK_period or
   Tflag_CLK_high_pluse or
   Tflag_CLK_low_pluse
) begin
    timing_volation_function; 
end

//   3. colnum red define

// 2. timing volation
task timing_volation_function;
integer i;
begin
    if (Tflag_CLK_period !== Last_Tflag_CLK_period || Tflag_CLK_low_pluse !== Last_Tflag_CLK_low_pluse || Tflag_CLK_high_pluse !== Last_Tflag_CLK_high_pluse)
    begin
        if($realtime != 0 )
        begin
            `ifdef NO_MESSAGE
            `else
            $display("Error_Message: The clock cycle is unconformable in %m at %t", $realtime);
            `endif
            Q_int = {Bits{1'bx}};
        end
    end
    else
    begin
        Tflag_A_bus = {Tflag_A7,Tflag_A6,Tflag_A5,Tflag_A4,Tflag_A3,Tflag_A2,Tflag_A1,Tflag_A0};
        for (i=0; i< Addr; i=i+1)
        begin
            Latch_A[i] = (Tflag_A_bus[i] !== Last_Tflag_A_bus[i]) ? 1'bx : Latch_A[i];
        end
        Latch_CEB = (Tflag_CEB !== Last_Tflag_CEB) ? 1'bx : Latch_CEB;
        #0.1;
        memory_active;
    end
    Last_Tflag_CLK_period = Tflag_CLK_period;
    Last_Tflag_CLK_low_pluse = Tflag_CLK_low_pluse;
    Last_Tflag_CLK_high_pluse = Tflag_CLK_high_pluse;
    Last_Tflag_A_bus = Tflag_A_bus;
    Last_Tflag_CEB = Tflag_CEB;
end
endtask

always@(Latch_A  or
       Latch_CEB)
begin
    // #0.1;
    A_int = Latch_A;
    CEB_int = Latch_CEB;
end
// 3. memory active 
task memory_active;
begin
    casez({CEB_int})
    1'b0: begin // read function
        if (CheckReadAddress(A_int))
        begin
            if (Q_NO_TOG == `FALSE) begin
                 if (A_int !== Last_A)
                 begin
                     if(faultinj_en == 1'b1)
                     begin
                         mem_XOR_data = mem[A_int] ^ mem_fault_array_XOR[A_int];
                     end
                     else
                     begin
                         mem_XOR_data = mem[A_int] & mem_fault_array_sa0[A_int];
                         mem_XOR_data = mem_XOR_data | mem_fault_array_sa1[A_int];
                     end
                     //Q_tmp = mem[A_int];
                     `ifdef TX_INITIALIZE_FAULT
                     Q_tmp = mem_XOR_data ^ mem_fault[A_int];
                     `else
                     Q_tmp = mem_XOR_data;
                     `endif
                     if (Q_int !== Q_tmp)
                         -> EVQ;
                     else 
                         Q_int = Q_tmp;
                 end
                 else 
                 begin
                     if (Q_int !== Q_tmp)
                     begin
                         if(faultinj_en == 1'b1)
                         begin
                             mem_XOR_data = mem[A_int] ^ mem_fault_array_XOR[A_int];
                         end
                         else
                         begin
                             mem_XOR_data = mem[A_int] & mem_fault_array_sa0[A_int];
                             mem_XOR_data = mem_XOR_data | mem_fault_array_sa1[A_int];
                         end
                         //Q_tmp = mem[A_int];
                         `ifdef TX_INITIALIZE_FAULT
                         Q_tmp = mem_XOR_data ^ mem_fault[A_int];
                         `else
                         Q_tmp = mem_XOR_data;
                         `endif
                         -> EVQ;
                     end
                     else 
                     begin
                         if(faultinj_en == 1'b1)
                         begin
                             mem_XOR_data = mem[A_int] ^ mem_fault_array_XOR[A_int];
                         end
                         else
                         begin
                             mem_XOR_data = mem[A_int] & mem_fault_array_sa0[A_int];
                             mem_XOR_data = mem_XOR_data | mem_fault_array_sa1[A_int];
                         end
                         //Q_tmp = mem[A_int];
                         `ifdef TX_INITIALIZE_FAULT
                         Q_tmp = mem_XOR_data ^ mem_fault[A_int];
                         `else
                         Q_tmp = mem_XOR_data;
                         `endif
                         Q_int = Q_tmp;
                     end
                 end
             end
             else // elseif`Q_NO_TOG 
             begin
                 if(faultinj_en == 1'b1)
                 begin
                     mem_XOR_data = mem[A_int] ^ mem_fault_array_XOR[A_int];
                 end
                 else
                 begin
                     mem_XOR_data = mem[A_int] & mem_fault_array_sa0[A_int];
                     mem_XOR_data = mem_XOR_data | mem_fault_array_sa1[A_int];
                 end
                 //Q_tmp = mem[A_int];
                 `ifdef TX_INITIALIZE_FAULT
                 Q_tmp = mem_XOR_data ^ mem_fault[A_int];
                 `else
                 Q_tmp = mem_XOR_data;
                 `endif
                 -> EVQ;
             end
        end
        else  // read address out of range
        begin
            Q_int = {Bits{1'bx}};
            disable EVQ_ACTIVE;
        end
    end
    1'b1: begin
    end
    1'bx: begin
        `ifdef NO_MESSAGE
        `else
        $display("Error_Message: The Chip enable is unknown in %m at %t", $realtime);
        `endif
        Q_int = {Bits{1'bx}};
    end
    endcase
end
endtask

always@(EVQ)
begin:EVQ_ACTIVE
    if (MARE_buf === 1'b0)
    begin
        #Trcqx
        Q_int   =  {Bits{1'bx}};
        Q_int   <= Q_tmp;
    end
    else if (MARE_buf === 1'b1 && MAR_buf[3] === 1'b0 && MAR_buf[2] === 1'b1 && MAR_buf[1] === 1'b1 && MAR_buf[0] === 1'b1 ) 
    begin
        #Trcqx_7
        Q_int   =  {Bits{1'bx}};
        Q_int   <= Q_tmp;
    end
end



// function for address range check 
function CheckReadAddress;
    input [Addr-1:0] Address;
    reg Addressxor;
    begin
        Addressxor = ^Address;
        if(Addressxor !== 1'bx)
        begin
            if (Address >= Words)
            begin
                `ifdef NO_MESSAGE
                `else
                $display("Error_Message : Read address out of range occured at = (%t) on address = (%m)", $realtime);
                `endif
                CheckReadAddress = 1'b0;
            end
            else
            begin
                CheckReadAddress = 1'b1;
            end
        end 
        else 
        begin
            `ifdef NO_MESSAGE
            `else
            $display("Error_Message : There is X in Read address occured at = (%t) on address = (%m)", $realtime);
            `endif
            CheckReadAddress = 1'b0;
            Q_int = {Bits{1'bx}};
        end
    end
endfunction



task PreLoadData;
    input [256*8:1] inputfile; //max is 256 character for file name
    reg [Addr:0] i;
    begin
        $display("Pre-Load data from file %s", inputfile);
        $readmemb(inputfile, Pre_Loading, 0, Words-1);
        for(i=0; i < Words; i=i+1) 
        begin
            mem[i] = Pre_Loading[i];
        end
    end
endtask



specify
    specparam  Trcq     = `ACEM*82.7;
    specparam  Trcq_7     = `ACEM*82.7;
    specparam  Trc     = `ACEM*125.8;
    specparam  Trc7    = `ACEM*125.8;
    specparam  Tckl     = `ACEM*48.7;
    specparam  Tckh     = `ACEM*21.1;
    specparam  Tces     = `ACEM*46.1;
    specparam  Tceh     = `ACEM*14.6;
    specparam  Tas      = `ACEM*34.1;
    specparam  Tah      = `ACEM*15.9;
    specparam  Tmars    = `ACEM*46.1;
    specparam  Tmarh    = `ACEM*14.6;
    specparam  Tmares   = `ACEM*46.1;
    specparam  Tmareh   = `ACEM*14.6;

    $setuphold(posedge CLK &&& sdfcond_A, posedge A[7], Tas, Tah, Tflag_A7);
    $setuphold(posedge CLK &&& sdfcond_A, negedge A[7], Tas, Tah, Tflag_A7);
    $setuphold(posedge CLK &&& sdfcond_A, posedge A[6], Tas, Tah, Tflag_A6);
    $setuphold(posedge CLK &&& sdfcond_A, negedge A[6], Tas, Tah, Tflag_A6);
    $setuphold(posedge CLK &&& sdfcond_A, posedge A[5], Tas, Tah, Tflag_A5);
    $setuphold(posedge CLK &&& sdfcond_A, negedge A[5], Tas, Tah, Tflag_A5);
    $setuphold(posedge CLK &&& sdfcond_A, posedge A[4], Tas, Tah, Tflag_A4);
    $setuphold(posedge CLK &&& sdfcond_A, negedge A[4], Tas, Tah, Tflag_A4);
    $setuphold(posedge CLK &&& sdfcond_A, posedge A[3], Tas, Tah, Tflag_A3);
    $setuphold(posedge CLK &&& sdfcond_A, negedge A[3], Tas, Tah, Tflag_A3);
    $setuphold(posedge CLK &&& sdfcond_A, posedge A[2], Tas, Tah, Tflag_A2);
    $setuphold(posedge CLK &&& sdfcond_A, negedge A[2], Tas, Tah, Tflag_A2);
    $setuphold(posedge CLK &&& sdfcond_A, posedge A[1], Tas, Tah, Tflag_A1);
    $setuphold(posedge CLK &&& sdfcond_A, negedge A[1], Tas, Tah, Tflag_A1);
    $setuphold(posedge CLK &&& sdfcond_A, posedge A[0], Tas, Tah, Tflag_A0);
    $setuphold(posedge CLK &&& sdfcond_A, negedge A[0], Tas, Tah, Tflag_A0);
    $setuphold(posedge CLK &&& sdfcond_MAR, posedge MAR[3], Tmars, Tmarh, Tflag_MAR);
    $setuphold(posedge CLK &&& sdfcond_MAR, negedge MAR[3], Tmars, Tmarh, Tflag_MAR);
    $setuphold(posedge CLK &&& sdfcond_MAR, posedge MAR[2], Tmars, Tmarh, Tflag_MAR);
    $setuphold(posedge CLK &&& sdfcond_MAR, negedge MAR[2], Tmars, Tmarh, Tflag_MAR);
    $setuphold(posedge CLK &&& sdfcond_MAR, posedge MAR[1], Tmars, Tmarh, Tflag_MAR);
    $setuphold(posedge CLK &&& sdfcond_MAR, negedge MAR[1], Tmars, Tmarh, Tflag_MAR);
    $setuphold(posedge CLK &&& sdfcond_MAR, posedge MAR[0], Tmars, Tmarh, Tflag_MAR);
    $setuphold(posedge CLK &&& sdfcond_MAR, negedge MAR[0], Tmars, Tmarh, Tflag_MAR);
    $setuphold(posedge CLK &&& sdfcond_MARE, posedge MARE, Tmares, Tmareh, Tflag_MARE);
    $setuphold(posedge CLK &&& sdfcond_MARE, negedge MARE, Tmares, Tmareh, Tflag_MARE);

    $setuphold(posedge CLK, posedge CEB, Tces, Tceh, Tflag_CEB);
    $setuphold(posedge CLK, negedge CEB, Tces, Tceh, Tflag_CEB);
   

    $period ( posedge CLK &&& sdfcond_CLK, Trc,     Tflag_CLK_period);
    $period ( negedge CLK &&& sdfcond_CLK, Trc,     Tflag_CLK_period);
    $period ( posedge CLK &&& sdfcond_CLK7, Trc7,     Tflag_CLK_period);
    $period ( negedge CLK &&& sdfcond_CLK7, Trc7,     Tflag_CLK_period);
    $width  ( posedge CLK &&& sdfcond_CLK,  Tckh, 0, Tflag_CLK_high_pluse);
    $width  ( negedge CLK &&& sdfcond_CLK,  Tckl, 0, Tflag_CLK_low_pluse);

    if (!CEB  && !MARE) (posedge CLK => (Q[7] : 1'bx)) = Trcq;
    if (!CEB  && !MARE) (posedge CLK => (Q[6] : 1'bx)) = Trcq;
    if (!CEB  && !MARE) (posedge CLK => (Q[5] : 1'bx)) = Trcq;
    if (!CEB  && !MARE) (posedge CLK => (Q[4] : 1'bx)) = Trcq;
    if (!CEB  && !MARE) (posedge CLK => (Q[3] : 1'bx)) = Trcq;
    if (!CEB  && !MARE) (posedge CLK => (Q[2] : 1'bx)) = Trcq;
    if (!CEB  && !MARE) (posedge CLK => (Q[1] : 1'bx)) = Trcq;
    if (!CEB  && !MARE) (posedge CLK => (Q[0] : 1'bx)) = Trcq;
    if (!CEB  && MARE && !MAR[3] && MAR[2] && MAR[1] && MAR[0] ) (posedge CLK => (Q[7] : 1'bx)) = Trcq_7;
    if (!CEB  && MARE && !MAR[3] && MAR[2] && MAR[1] && MAR[0] ) (posedge CLK => (Q[6] : 1'bx)) = Trcq_7;
    if (!CEB  && MARE && !MAR[3] && MAR[2] && MAR[1] && MAR[0] ) (posedge CLK => (Q[5] : 1'bx)) = Trcq_7;
    if (!CEB  && MARE && !MAR[3] && MAR[2] && MAR[1] && MAR[0] ) (posedge CLK => (Q[4] : 1'bx)) = Trcq_7;
    if (!CEB  && MARE && !MAR[3] && MAR[2] && MAR[1] && MAR[0] ) (posedge CLK => (Q[3] : 1'bx)) = Trcq_7;
    if (!CEB  && MARE && !MAR[3] && MAR[2] && MAR[1] && MAR[0] ) (posedge CLK => (Q[2] : 1'bx)) = Trcq_7;
    if (!CEB  && MARE && !MAR[3] && MAR[2] && MAR[1] && MAR[0] ) (posedge CLK => (Q[1] : 1'bx)) = Trcq_7;
    if (!CEB  && MARE && !MAR[3] && MAR[2] && MAR[1] && MAR[0] ) (posedge CLK => (Q[0] : 1'bx)) = Trcq_7;
endspecify
`endprotect

endmodule

