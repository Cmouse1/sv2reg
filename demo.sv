// demo.sv - 综合测试用例，覆盖所有语法
module sys_xxx "top register block"

//ctrl "control registers"
.rst_n    ( pin_rst ) ,   // input "reset"
.mode     ( cfg_mode ) ,  // input, width=3 "mode select"
.enable   ,               // input "enable switch"
.status   ,               // output "status flag"
.version  ,               // output [3:0] "version number"

//dma "dma engine config"
.src_addr ,               // input [31:0] "source address"
.dst_addr ,               // input [31:0] "destination address"
.tx_len   ,               // input [15:0] "transfer length"
.done     ,               // output "transfer done"

//intr "interrupt"
.intr_en  ,               // input "interrupt enable"
.intr_pend,               // output "interrupt pending"
.intr_clr ,               // input "interrupt clear"

//spare "spare registers"
.spare_0                 // input "spare 0"
.spare_1                 // input "spare 1"

//override "manual access override"
.ro_reg                  // input, sw=ReadOnly, hw=ReadOnly "force RO"
.rw_reg                  // output, sw=ReadWrite, hw=ReadWrite "force RW"
.hw_only                 // input, hw=WriteOnly "hw write only"

endmodule
