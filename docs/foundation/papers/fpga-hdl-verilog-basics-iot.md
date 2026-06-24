# FPGA Verilog HDL基础与IoT外设实现

> **难度**：🟢 初级 | **领域**：FPGA开发入门 | **阅读时间**：约 20 分钟

## 引言

学编程时，你告诉计算机"先做A再做B"——这是顺序思维。但设计电路时，你需要想象一张桌子上有无数盏灯，所有灯在同一个时钟节拍下同时亮灭——这是并发思维。

Verilog HDL(Hardware Description Language)不是编程语言，而是一种描述硬件结构的语言。你写的每一行 Verilog 都会变成真实的晶体管连线。本文从零开始讲解 Verilog 基础，并用 IoT 场景中常见的外设(UART、SPI、PWM、GPIO)作为实战案例，帮助你在 FPGA 上迈出第一步。

## 1. HDL概念：硬件描述不是软件编程

### 1.1 核心区别

| 维度 | 软件编程(C/Python) | 硬件描述(Verilog/VHDL) |
|------|--------------------|-------------------------|
| 执行模型 | 顺序执行 | 并发执行，所有模块同时运行 |
| 本质 | 指令序列 | 电路结构 |
| 时间 | 指令周期 | 时钟周期 |
| 调试方式 | 打印/断点 | 仿真波形 |
| 输出 | 可执行文件 | 比特流(配置FPGA) |

### 1.2 并发思维

```verilog
// 两个 always 块同时运行，不是先后执行
always @(posedge clk) led1 <= counter1[24];  // LED1 闪烁
always @(posedge clk) led2 <= counter2[20];  // LED2 不同频率
// C语言: 顺序执行; Verilog: 两段独立硬件同时工作
```

关键：每个 `always` 块代表一块独立硬件，FPGA 上电后所有 `always` 块同时工作。

## 2. Verilog基础语法

### 2.1 模块与端口

模块(module)是 Verilog 基本单元，相当于电路板上的一个芯片：

```verilog
module my_module (
    input  wire        clk,
    input  wire        rst_n,    // 复位(低有效)
    input  wire [7:0]  data_in,  // 8位输入总线
    output reg  [7:0]  data_out, // 8位输出总线
    output wire        valid
);
endmodule
```

### 2.2 wire与reg

| 类型 | 含义 | 类比 | 使用场景 |
|------|------|------|---------|
| wire | 物理连线 | 电路板上的铜线 | 组合逻辑、模块间连接 |
| reg | 寄存器 | 存储1bit的触发器 | 时序逻辑、always块内赋值 |

```verilog
wire [7:0] result;
assign result = data_a + data_b;  // 组合逻辑：随输入立即变化

reg [7:0] counter;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) counter <= 8'd0;
    else        counter <= counter + 1;  // 时序逻辑：时钟驱动
end
```

**注意**：`reg` 在 `always @(*)` 中使用时综合成组合逻辑，不一定是寄存器。

### 2.3 assign与always

```verilog
assign y = a & b;          // 组合逻辑：与门
assign out = sel ? a : b;  // 二选一MUX

always @(posedge clk or negedge rst_n) begin  // 时序逻辑：D触发器
    if (!rst_n) q <= 1'b0;
    else        q <= d;
end

always @(*) begin  // 组合逻辑用reg类型
    case (sel) 2'd0: out = a; 2'd1: out = b; default: out = c; endcase
end
```

## 3. 综合与仿真

### 3.1 综合

综合(Synthesis)将 Verilog 转换为 FPGA 实际硬件：

```
Verilog代码 -> 综合 -> 门级网表 -> 布局布线 -> 比特流
   你写的      电路图      物理位置      最终配置
```

不是所有 Verilog 都能综合：`$display`、`#10` 延迟等仅供仿真，无对应硬件。

### 3.2 仿真与测试平台

测试平台(Testbench)是为仿真写的驱动程序：

```verilog
module tb_counter;
    reg clk, rst_n; wire [7:0] count;
    counter uut (.clk(clk), .rst_n(rst_n), .count(count));
    initial clk = 0;
    always #10 clk = ~clk;  // 50MHz时钟
    initial begin
        rst_n = 0; #100; rst_n = 1; #1000;
        $display("Counter = %d", count); $finish;
    end
endmodule
```

## 4. 基本构建块

### 4.1 多路选择器与译码器

```verilog
module mux4to1 (input [3:0] data, input [1:0] sel, output y);
    assign y = data[sel];
endmodule

module decoder2to4 (input [1:0] in, input en, output reg [3:0] out);
    always @(*) begin
        if (en) case (in) 2'b00: out=4'b0001; 2'b01: out=4'b0010;
                         2'b10: out=4'b0100; 2'b11: out=4'b1000; endcase
        else out = 4'b0000;
    end
endmodule
```

### 4.2 参数化计数器

```verilog
module counter_n #(parameter N=8) (
    input clk, rst_n, en, output [N-1:0] count
);
    reg [N-1:0] cnt;
    always @(posedge clk or negedge rst_n)
        if (!rst_n) cnt <= 0; else if (en) cnt <= cnt + 1;
    assign count = cnt;
endmodule
```

### 4.3 状态机

状态机是数字设计的核心模式，分 Moore 型(输出只依赖状态)和 Mealy 型(输出依赖状态和输入)：

```verilog
module traffic_light (input clk, rst_n, output reg [1:0] light);
    localparam RED=0, YELLOW=1, GREEN=2;
    reg [23:0] timer; reg [1:0] state;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin state<=RED; timer<=0; light<=RED; end
        else begin
            timer <= timer + 1;
            case (state)
                RED:    begin light<=RED;    if(timer==25_000_000) begin state<=GREEN;  timer<=0; end end
                GREEN:  begin light<=GREEN;  if(timer==25_000_000) begin state<=YELLOW;timer<=0; end end
                YELLOW: begin light<=YELLOW; if(timer==12_500_000) begin state<=RED;   timer<=0; end end
            endcase
        end
    end
endmodule
```

## 5. 时钟与复位设计

### 5.1 时钟

FPGA 中所有时序逻辑在时钟上升沿触发。不要用双沿触发(综合困难，时序差)。

### 5.2 复位策略

| 复位类型 | 写法 | 推荐 |
|---------|------|------|
| 同步复位 | `always @(posedge clk)` | 推荐，时序好 |
| 异步复位 | `always @(posedge clk or negedge rst_n)` | 常用，需释放同步 |

```verilog
// 异步复位、同步释放(推荐模式)
module reset_sync (input clk, rst_n_async, output rst_n_sync);
    reg d1, d2;
    always @(posedge clk or negedge rst_n_async)
        if (!rst_n_async) begin d1<=0; d2<=0; end
        else begin d1<=1; d2<=d1; end
    assign rst_n_sync = d2;
endmodule
```

## 6. FPGA开发流程与工具

```
设计(Verilog) -> 仿真 -> 综合 -> 布局布线 -> 比特流 -> 下载到FPGA
```

| 工具 | 厂商 | 目标FPGA | 价格 | 适合IoT入门 |
|------|------|---------|------|------------|
| Vivado | Xilinx/AMD | Zynq, Artix | 免费WebPack | 功能强大但庞大 |
| Quartus | Intel/Altera | Cyclone, Max | 免费Lite | 中等 |
| Yosys+nextpnr | 开源 | Lattice iCE40/ECP5 | 免费 | 轻量，推荐入门 |
| Gowin EDA | 高云 | Tang Nano系列 | 免费 | 国产，超低成本 |

## 7. IoT外设Verilog实现

### 7.1 UART发送器

```verilog
module uart_tx #(parameter CLK_FREQ=27_000_000, BAUD=115200) (
    input clk, rst_n, input [7:0] tx_data, input tx_start,
    output tx_busy, output tx_pin
);
    localparam CLKS_PER_BIT = CLK_FREQ / BAUD;  // 27MHz/115200=234
    reg [7:0] shift_reg; reg [15:0] bit_cnt; reg [3:0] bit_idx;
    reg busy, tx_out;
    assign tx_pin = tx_out; assign tx_busy = busy;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin busy<=0; tx_out<=1; bit_idx<=0; bit_cnt<=0; end
        else if (tx_start && !busy) begin
            busy<=1; shift_reg<=tx_data; tx_out<=0; bit_cnt<=0; bit_idx<=0;
        end else if (busy) begin
            bit_cnt <= bit_cnt + 1;
            if (bit_cnt == CLKS_PER_BIT - 1) begin
                bit_cnt <= 0;
                if (bit_idx == 0) begin tx_out<=shift_reg[0]; shift_reg<=shift_reg>>1; bit_idx<=1; end
                else if (bit_idx < 8) begin tx_out<=shift_reg[0]; shift_reg<=shift_reg>>1; bit_idx<=bit_idx+1; end
                else begin tx_out<=1; busy<=0; bit_idx<=0; end  // 停止位
            end
        end else tx_out <= 1;
    end
endmodule
```

### 7.2 SPI主机

```verilog
module spi_master #(parameter CLK_FREQ=27_000_000, SPI_CLK=1_000_000) (
    input clk, rst_n, input [7:0] mosi_data, input spi_start,
    output [7:0] miso_data, output spi_busy,
    output spi_clk_pin, output spi_mosi_pin, input spi_miso_pin, output spi_cs_n
);
    localparam HALF = CLK_FREQ/(2*SPI_CLK);  // 27MHz/2MHz=13
    reg [7:0] tx_sh, rx_sh; reg [15:0] div; reg [3:0] bcnt;
    reg busy, sclk, cs_n;
    assign spi_clk_pin=sclk; assign spi_mosi_pin=tx_sh[7];
    assign miso_data=rx_sh; assign spi_busy=busy; assign spi_cs_n=cs_n;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin busy<=0; sclk<=0; cs_n<=1; bcnt<=0; div<=0; end
        else if (spi_start && !busy) begin busy<=1; tx_sh<=mosi_data; rx_sh<=0; cs_n<=0; sclk<=0; div<=0; bcnt<=0; end
        else if (busy) begin
            div <= div + 1;
            if (div == HALF - 1) begin
                div<=0; sclk<=~sclk;
                if (sclk) begin tx_sh<=tx_sh<<1; bcnt<=bcnt+1; end  // 下降沿移出
                else rx_sh <= {rx_sh[6:0], spi_miso_pin};            // 上升沿采样
                if (bcnt == 8) begin busy<=0; cs_n<=1; end
            end
        end
    end
endmodule
```

### 7.3 PWM发生器

```verilog
module pwm_gen #(parameter BITS=8) (
    input clk, rst_n, input [BITS-1:0] duty, output pwm_out
);
    reg [BITS-1:0] cnt;
    always @(posedge clk or negedge rst_n)
        if (!rst_n) cnt <= 0; else cnt <= cnt + 1;
    assign pwm_out = (cnt < duty);
endmodule
```

### 7.4 GPIO控制器

```verilog
module gpio_ctrl #(parameter W=8) (
    input clk, rst_n, input [W-1:0] out_data, input out_en,
    output [W-1:0] in_data, inout [W-1:0] pins
);
    reg [W-1:0] out_reg, dir;
    genvar i; generate
        for (i=0; i<W; i=i+1) assign pins[i] = dir[i] ? out_reg[i] : 1'bz;
    endgenerate
    assign in_data = pins;
    always @(posedge clk or negedge rst_n)
        if (!rst_n) begin out_reg<=0; dir<=0; end
        else if (out_en) begin out_reg<=out_data; dir<={W{1'b1}}; end
endmodule
```

## 8. 测试平台与仿真

```verilog
module tb_uart_tx;
    reg clk, rst_n, tx_start; reg [7:0] tx_data; wire tx_busy, tx_pin;
    uart_tx #(.CLK_FREQ(27_000_000), .BAUD(115200))
    uut (.clk(clk), .rst_n(rst_n), .tx_data(tx_data),
         .tx_start(tx_start), .tx_busy(tx_busy), .tx_pin(tx_pin));
    initial clk = 0; always #18 clk = ~clk;  // 约27MHz
    initial begin
        rst_n=0; tx_data=8'h55; tx_start=0; #200; rst_n=1; #100;
        tx_start=1; #40; tx_start=0; wait(tx_busy==0); #1000; $finish;
    end
endmodule
```

## 9. 时序约束入门

综合工具不知道你的时钟频率，需要通过约束文件指定：

```tcl
create_clock -period 37.037 [get_ports clk]  # 27MHz
set_false_path -from [get_ports rst_n]        # 异步信号
```

关键时序指标：

| 指标 | 含义 | 目标 |
|------|------|------|
| Setup Slack | 时钟沿前数据到达余量 | > 0 |
| Hold Slack | 时钟沿后数据保持余量 | > 0 |
| WNS | 最差负裕量 | 必须为0或正 |
| Max Freq | 最高可达频率 | > 目标频率 |

WNS < 0 说明时序不满足，需降低时钟频率或优化逻辑。

## 10. 实战项目：LED闪烁与UART回环

### 10.1 顶层模块(Tang Nano 9K)

```verilog
module tang_nano_top (
    input clk, rst_n, output led, output uart_tx, input uart_rx
);
    reg [26:0] blink;  // 27MHz/2^27 约0.2Hz
    always @(posedge clk or negedge rst_n)
        if (!rst_n) blink<=0; else blink<=blink+1;
    assign led = blink[26];

    wire [7:0] rx_data; wire rx_valid, tx_busy;
    uart_rx #(.CLK_FREQ(27_000_000),.BAUD(115200))
    u_rx (.clk(clk),.rst_n(rst_n),.rx_pin(uart_rx),.rx_data(rx_data),.rx_valid(rx_valid));
    uart_tx #(.CLK_FREQ(27_000_000),.BAUD(115200))
    u_tx (.clk(clk),.rst_n(rst_n),.tx_data(rx_data),.tx_start(rx_valid),.tx_busy(tx_busy),.tx_pin(uart_tx));
endmodule
```

### 10.2 开发步骤

1. 安装 Gowin EDA 或 Yosys + nextpnr
2. 创建工程，选择 GW1NR-9K 芯片
3. 添加 Verilog 源文件
4. 编写引脚约束(CST文件)：

```
IO_LOC "clk" 45; IO_LOC "led" 15;
IO_LOC "uart_tx" 18; IO_LOC "uart_rx" 17;
```

5. 综合 -> 布局布线 -> 生成比特流 -> USB 下载
6. 串口终端(115200, 8N1)测试 Echo

### 10.3 资源利用率报告

```
资源利用率示例 (Tang Nano 9K):
+--------+------+-------+-------+
| 资源   | 已用 | 总量  | 利用率|
+--------+------+-------+-------+
| LUT    | 312  | 8640  | 3.6%  |
| FF     | 189  | 8640  | 2.2%  |
| BRAM   |   2  |   26  | 7.7%  |
+--------+------+-------+-------+
```

**经验法则**：LUT 利用率 > 80% 时序闭合困难；BRAM > 90% 注意不可用 LUT 替代。

## 总结

| 知识点 | 核心要义 |
|-------|---------|
| HDL vs 编程语言 | 并发 vs 顺序，描述电路 vs 编写指令 |
| wire vs reg | wire = 连线(组合)，reg = 可存状态(时序) |
| 综合与仿真 | 综合生成硬件，仿真验证逻辑 |
| 状态机 | 数字设计核心模式，Moore/Mealy 两类 |
| 时钟与复位 | 异步复位同步释放是推荐模式 |
| UART/SPI/PWM | IoT 三大外设，Verilog 实现不复杂 |
| 时序约束 | 指定时钟频率，检查 WNS 是否为正 |
| 资源利用率 | LUT/FF/BRAM/DSP 使用量，>80% 需警惕 |

**下一步**：购买 Tang Nano 9K(约 50 元)，跑通 LED 闪烁 + UART Echo，然后添加 SPI 连接传感器。

## 参考文献

1. Pong P. Chu. "FPGA Prototyping by Verilog Examples." Wiley, 2008.
2. Samir Palnitkar. "Verilog HDL: A Guide to Digital Design and Synthesis." Prentice Hall, 2nd Ed., 2003.
3. Clifford E. Cummings. "Cumulative Synthesis and Coding Guidelines." Sunburst Design, 2022.
4. Xilinx/AMD. "Vivado Design Suite User Guide: Synthesis." UG901, 2023.
5. Gowin Semiconductor. "Gowin EDA User Guide." 2023.
