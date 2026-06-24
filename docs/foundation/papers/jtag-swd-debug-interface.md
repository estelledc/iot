# JTAG与SWD调试接口原理与工具链
> **难度**：🟡 中级 | **领域**：嵌入式调试技术 | **阅读时间**：约 20 分钟

## 引言

调试接口就像城市的地下管网: 平时看不见, 但一旦出了问题(程序跑飞、硬件异常), 没有它就只能"挖地三尺"逐行排查. JTAG是老式的综合管廊(5条管道, 能接各种检修设备), SWD是后来优化的精简管廊(2条管道, 专修ARM芯片). 两种管廊都能让你从外部"透视"芯片内部状态: 暂停CPU、读写寄存器和内存、设断点、烧录Flash. 本文从JTAG标准出发, 讲解其状态机与边界扫描原理, 再过渡到SWD的精简设计, 最后覆盖工具链(探针、OpenOCD、GDB)和生产应用.

## 1 JTAG标准(IEEE 1149.1)

### 1.1 JTAG的起源与目标

JTAG(Joint Test Action Group)最初是为PCB板级连接测试而设计, 1990年成为IEEE 1149.1标准. 核心目标:

- **边界扫描**: 在不使用物理探针的情况下, 验证PCB上芯片之间的焊接连通性
- **内测试**: 通过测试访问端口(TAP)对芯片内部逻辑进行测试
- **后来扩展**: 调试(断点、单步)、Flash编程、设备配置等

### 1.2 JTAG信号定义

| 信号 | 方向 | 功能 |
|------|------|------|
| TCK | 主控->目标 | 测试时钟, 所有TAP状态转换的同步时钟 |
| TMS | 主控->目标 | 测试模式选择, 控制TAP状态机的状态转换 |
| TDI | 主控->目标 | 测试数据输入, 串行移入指令或数据 |
| TDO | 目标->主控 | 测试数据输出, 串行移出捕获的数据 |
| TRST | 主控->目标 | 测试复位(可选), 异步复位TAP状态机 |

TRST是可选信号, 多数设计通过TMS连续5个TCK周期为高来复位TAP(逻辑复位), 从而省去TRST引脚.

### 1.3 JTAG菊花链

多个JTAG设备可串联成菊花链, 共享TCK/TMS, TDI/TDO首尾相连:

```
主控
  TCK --------+--------+--------+
  TMS --------+--------+--------+
  TDI --> [芯片1] --> [芯片2] --> [芯片3]
  TDO <-- [芯片1] <-- [芯片2] <-- [芯片3]
```

菊花链只需一个探针即可访问所有设备, 但主控需知道每颗设备的IR长度才能正确寻址.

## 2 TAP控制器状态机

### 2.1 16状态有限状态机

TAP(Test Access Port)控制器是16状态FSM, 由TMS驱动:

```
                Test-Logic-Reset
                /              \
      TMS=0    /                \    TMS=1
              v                  v
      Run-Test/Idle    ...   Select-DR-Scan
          |                      |
          | TMS=1                | TMS=1
          v                      v
      Select-DR-Scan      Select-IR-Scan
          |                      |
          | TMS=0                | TMS=0
          v                      v
      Capture-DR           Capture-IR
          |                      |
          v                      v
      Shift-DR             Shift-IR    <-- 串行移位
          |                      |
          v                      v
      Exit1-DR             Exit1-IR
          |                      |
          +---> ... ---> Update-DR / Update-IR
```

### 2.2 关键状态说明

| 状态 | 功能 |
|------|------|
| Test-Logic-Reset | 复位状态, TAP逻辑禁用, IR置为IDCODE指令 |
| Run-Test/Idle | 空闲状态, 某些指令在此执行操作(如RUNBIST) |
| Capture-DR/IR | 捕获当前值到移位寄存器(DR捕获引脚状态, IR捕获上一指令) |
| Shift-DR/IR | 串行移位: TDI移入, TDO移出, 每TCK一个bit |
| Update-DR/IR | 将移位寄存器内容锁存到输出 |

### 2.3 状态转换编码

- **复位TAP**: TMS=11111(5个TCK), 从任意状态回到Test-Logic-Reset
- **进入Shift-IR**: TMS=01100(从Reset出发)
- **进入Shift-DR**: TMS=0100(从Run-Idle出发)

## 3 边界扫描

### 3.1 边界扫描寄存器(BSR)

边界扫描的核心是在芯片每个I/O引脚旁插入扫描单元(1-bit移位寄存器), 串联成BSR:

```
芯片引脚:  Pin1  Pin2  Pin3  ...  PinN
            |     |     |          |
BSR单元:  [C1]-[C2]-[C3]-...-[CN]  (TDI->TDO方向)
```

每个单元三种模式: Capture(捕获引脚电平)、Update(驱动值到引脚)、Shift(TDI向TDO移位).

### 3.2 BSDL与测试流程

IEEE 1149.1要求每个JTAG设备提供BSDL文件, 描述JTAG端口配置、BSR长度和引脚映射、指令操作码. EDA工具(如UrJTAG、OpenOCD)使用BSDL自动配置边界扫描.

PCB连通性测试流程: 读取IDCODE确认设备存在 -> 对芯片A输出引脚加载测试值(BSR Update) -> 从芯片B输入引脚捕获值(BSR Capture) -> 比较A输出与B输入, 不一致则焊接开路/短路.

## 4 SWD(Serial Wire Debug)

### 4.1 SWD的设计动机

ARM在Cortex-M系列引入SWD: 将JTAG的5线精简为2线(SWDIO/SWCLK), 保留全部调试能力, 保留对Trace输出(SWO)的可选支持.

### 4.2 SWD信号与协议帧

| 信号 | 方向 | 功能 |
|------|------|------|
| SWCLK | 主控->目标 | 串行时钟, 对应JTAG的TCK |
| SWDIO | 双向 | 数据输入/输出复用, 对应TMS+TDI+TDO |

SWD通信以包为单位:

```
[Start(1)][APnDP(1)][RnW(1)][Addr(2)][Parity(1)][Park(1)]
[Turnaround][ACK(3)][Data(32)][Parity(1)][Turnaround]
```

APnDP选择DP/AP, RnW选择读/写, ACK响应(OK=001, WAIT=010, FAULT=100).

### 4.3 DP与AP两级端口

- **DP(Debug Port)**: SWD直接访问, 含IDCODE/ABORT(DP0)、CTRL/STAT(DP1)、SELECT(DP2)、RDBUFF(DP3)
- **AP(Access Port)**: 通过DP间接访问, MEM-AP(内存访问)、AHB-AP(Cortex-M通用)、APB-AP(部分外设)

### 4.4 SWD与JTAG的桥接

ARM的DPU同时支持SWD和JTAG, 上电时通过探测信号序列自动检测连接模式. 部分芯片(如STM32)支持运行时切换SWD/JTAG.

## 5 SWD与JTAG对比

| 特性 | JTAG | SWD |
|------|------|-----|
| 信号线数 | 4-5 | 2(SWCLK/SWDIO) |
| 数据方向 | TDI/TDO分离(全双工) | SWDIO复用(半双工) |
| 调试能力 | 完整 | 完整(等价) |
| 边界扫描 | 原生支持 | 不支持(需切换JTAG) |
| 菊花链 | 支持 | 不支持(点对点) |
| Trace输出 | 可选ETM(并行) | SWO/ITM(串行) |
| 标准化 | IEEE 1149.1 | ARM ADI v5/v6 |
| 适用范围 | 所有JTAG设备 | 仅ARM核 |

选择建议: Cortex-M项目、引脚受限选SWD; 需边界扫描、多设备链、非ARM核选JTAG.

## 6 调试探针

### 6.1 主流探针对比

| 探针 | 厂商 | 接口 | 最大时钟 | 特性 | 价格 |
|------|------|------|----------|------|------|
| J-Link | Segger | JTAG+SWD | 50MHz | 最快, 无限断点, RTT | 高($400+) |
| ST-Link | ST | SWD+JTAG | 25MHz | STM32专用 | 低(随Nucleo板) |
| CMSIS-DAP | ARM(开源) | SWD+JTAG | 10-20MHz | 标准协议, 可DIY | 极低($5-20) |

### 6.2 J-Link特性

J-Link是商用探针标杆: 无限断点(Flash断点技术)、RTT零开销调试输出(替代UART printf)、50MHz时钟下载速度3MB/s、支持ARM Cortex全系列和RISC-V.

### 6.3 CMSIS-DAP与DAPLink

CMSIS-DAP是ARM定义的标准调试探针协议(USB HID传输DAP命令), 任何实现该协议的探针都能被OpenOCD/pyOCD/Keil识别. DAPLink是ARM官方参考实现, 可烧录到KL25Z、STM32F103(Blue Pill)、LPC11U35等MCU, 使之变成USB调试探针.

```c
// CMSIS-DAP命令示例
uint8_t cmd[] = { 0x00, 0x02 };  // DAP_Connect (SWD模式)
dap_send(cmd, 2, resp, &len);

uint8_t read_idcode[] = { 0x05, 0x12, 0x00 };  // 复位序列 + 读DP IDCODE
dap_send(read_idcode, 3, resp, &len);
```

## 7 OpenOCD配置

### 7.1 OpenOCD架构

```
+----------------------------------+
|   GDB Server (TCP:3333)         |
+----------------------------------+
|   Debug Interface Layer          |
|   (JTAG/SWD命令生成)            |
+----------------------------------+
|   Transport Layer (JTAG/SWD)     |
+----------------------------------+
|   Interface Driver               |
|   (J-Link/ST-Link/CMSIS-DAP/FTDI)|
+----------------------------------+
```

### 7.2 配置文件与常用命令

```tcl
source [find interface/jlink.cfg]    # 探针配置
transport select swd                  # 传输层选择
source [find target/stm32h7x.cfg]    # 目标配置
adapter speed 5000                    # SWD时钟频率
reset_config srst_only               # 复位配置
```

| 命令 | 功能 |
|------|------|
| `reset halt` | 复位目标并暂停CPU |
| `mdw 0x20000000 16` | 从地址读16个word |
| `flash write_image erase firmware.bin 0x08000000` | 烧录固件 |
| `bp 0x08000100 2 hw` | 设硬件断点 |

## 8 GDB远程调试

### 8.1 调试架构

```
GDB客户端 <--TCP:3333--> OpenOCD <--SWD/JTAG--> 目标芯片
```

GDB通过远程串行协议(RSP)与OpenOCD通信, 格式: `$packet-data#checksum`

### 8.2 调试工作流

```bash
# 1. 启动OpenOCD
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg &
# 2. 启动GDB, 连接OpenOCD
arm-none-eabi-gdb firmware.elf
(gdb) target extended-remote :3333
(gdb) load                    # 加载固件
(gdb) break main              # 设断点
(gdb) continue                # 运行
(gdb) step                    # 单步
(gdb) print sensor_data       # 查看变量
(gdb) x/10bx 0x20000000      # 查看内存
```

### 8.3 常用GDB命令

| 命令 | 功能 |
|------|------|
| `break func` | 在函数入口设断点 |
| `watch var` | 设数据观察点(写) |
| `backtrace` | 打印调用栈 |
| `set var x=5` | 修改变量值 |

## 9 Flash编程

### 9.1 通过调试接口烧录Flash

烧录流程: 暂停CPU -> 解锁Flash控制器(KEY1+KEY2) -> 擦除扇区 -> 逐字编程 -> 锁定Flash -> 复位启动.

### 9.2 编程速度对比

| 方法 | STM32F4(256KB) | STM32H7(1MB) |
|------|----------------|--------------|
| J-Link(50MHz SWD) | ~2s | ~5s |
| ST-Link(25MHz SWD) | ~4s | ~10s |
| CMSIS-DAP(10MHz) | ~8s | ~20s |
| UART Bootloader | ~30s | ~120s |

### 9.3 OpenOCD烧录脚本

```tcl
proc flash_firmware {binfile} {
    reset halt
    flash write_image erase $binfile 0x08000000 bin
    verify_image $binfile 0x08000000 bin
    reset run
}
init; flash_firmware firmware.bin; shutdown
```

## 10 ITM/SWO Trace输出

### 10.1 ITM(Instrumentation Trace Macrocell)

ITM通过SWO引脚输出trace: 软件stimulus端口(0-31, 写ITM_STIMx寄存器)、DWT硬件事件(PC采样/数据观测/异常跟踪)、自动时间戳.

SWO支持两种编码: UART模式(可用UART接收器捕获)和Manchester编码(自带时钟, 需专用解码器).

### 10.2 printf重定向到ITM

```c
// 将printf重定向到ITM stimulus端口0
int fputc(int ch, FILE *f)
{
    while (!(ITM->STIM[0] & 1));  // 等待端口0就绪
    ITM->STIM[0] = ch;            // 写入字符
    return ch;
}
// 在调试器中: OpenOCD -> itm port 0 on
```

ITM printf优势: 零CPU开销, 不占UART, 速率可达2Mbps. 仅在调试器连接时有效.

J-Link的RTT(Real-Time Transfer)是ITM替代方案: 用目标RAM环形缓冲区, 不需SWO引脚, 速度更快(1MB/s), 但与J-Link绑定.

## 11 断点机制

### 11.1 硬件断点与软件断点

| Cortex-M版本 | 硬件断点数 | 比较器类型 |
|-------------|-----------|-----------|
| Cortex-M0/M0+ | 2-4 | 指令地址比较 |
| Cortex-M3/M4 | 6 | 指令地址+上下文 |
| Cortex-M7 | 6-8 | 指令地址+上下文 |

硬件断点: CPU执行前比较PC与断点地址, 不修改代码, 可在ROM中设断, 数量有限.

软件断点: 替换目标指令为BKPT指令, 数量无限制, 需修改内存, 不能在只读ROM中设.

### 11.2 数据观测点(DWT)

Cortex-M的DWT提供: 读观测点(变量被读时暂停)、写观测点(被写时暂停)、读写观测点、值匹配(写入特定值时暂停).

```c
(gdb) watch global_counter    // 写观测点
(gdb) rwatch status_reg       // 读观测点
(gdb) awatch control_reg      // 读写观测点
```

## 12 常见调试场景

### 12.1 程序跑飞(HardFault)

```bash
(gdb) target remote :3333
(gdb) halt
(gdb) print/x *(uint32_t*)0xE000ED28  # CFSR(配置错误状态)
(gdb) print/x *(uint32_t*)0xE000ED2C  # HFSR(硬错误状态)
(gdb) print/x *(uint32_t*)0xE000ED38  # MMFAR(错误地址)
(gdb) backtrace                         # 调用栈
(gdb) x/i $pc                           # 出错位置指令
```

### 12.2 变量意外修改

```bash
(gdb) watch critical_flag    # 设写观测点
(gdb) continue               # 运行, 命中后查看调用栈
(gdb) backtrace
```

### 12.3 实时性能分析

```bash
# 使用DWT周期计数器
(gdb) set *(uint32_t*)0xE0001000 = 1   # 启用CYCCNT
# ... 运行一段时间 ...
(gdb) print/x *(uint32_t*)0xE0001004   # 读取CYCCNT
```

## 13 生产编程考量

### 13.1 SWD在生产中的应用

生产线上SWD是最常用的烧录方式: 速度快(256KB在2-4秒)、连线少(2信号+VCC+GND)、标准接口(10/5针SWD连接器)、可验证(回读校验+读UID追溯).

### 13.2 标准调试连接器

| 连接器 | 针数 | 信号 | 常见应用 |
|--------|------|------|----------|
| ARM 10-pin | 10 | VTref,SWDIO,SWCLK,SWO,RESET等 | Cortex-M开发板 |
| ARM 20-pin | 20 | 标准JTAG 20针 | Cortex-A/R开发板 |
| Tag-Connect | 6(无腿) | SWDIO,SWCLK,RESET,VCC,GND | 生产工装(无连接器成本) |

### 13.3 生产烧录流程

```
1. 工装夹具压接PCB焊盘, 探针通过SWD连接目标
2. 读IDCODE验证芯片型号
3. 擦除Flash, 烧录固件(Bootloader+App)
4. 校验烧录内容(回读比较)
5. 写入配置数据(校准参数/序列号)到Option Bytes
6. 设置读保护(RDP)级别
7. 复位目标, 验证固件自检通过
8. 断开SWD, 释放夹具
```

### 13.4 安全考量: 读保护

- **RDP Level 0**: 无保护, SWD可自由读写
- **RDP Level 1**: SWD可连接但无法读Flash(读回全0), 擦除全片后可恢复
- **RDP Level 2**: 永久禁用SWD/JTAG, 不可逆

```c
// STM32设置RDP Level 1
void set_read_protection_level1(void)
{
    FLASH_OBProgramInitTypeDef ob;
    HAL_FLASHEx_OBGetConfig(&ob);
    ob.RDPLevel = OB_RDP_LEVEL_1;
    HAL_FLASHEx_OBProgram(&ob);
    HAL_FLASH_OBLaunch();  // 生效(需复位)
}
```

RDP Level 2不可逆, 生产环境必须谨慎, 建议只在量产固件确认无误后设置.

## 总结

JTAG和SWD是嵌入式系统的两条"地下管廊": JTAG是通用型(5线, IEEE标准, 支持菊花链和边界扫描), SWD是ARM精简型(2线, 等价调试能力, 引脚最少). 对于绝大多数Cortex-M项目, SWD是首选; 需要边界扫描或多设备链时选JTAG.

调试探针从商用J-Link(最快, 功能最全)到开源CMSIS-DAP(DIY友好)覆盖不同需求. OpenOCD+GDB组合是开源调试的标准工具链, 支持所有主流探针和ARM目标. ITM/SWO提供了零开销的调试输出, 断点机制(硬件+软件+数据观测点)覆盖了各类调试需求.

在生产环境中, SWD因连线少、速度快而成为固件烧录的主流方式, 但读保护(RDP)的设置需要谨慎--Level 2不可逆. 理解JTAG/SWD的原理和工具链, 是嵌入式开发者从"能写代码"到"能排错"的关键一步.

## 参考文献

1. IEEE Std 1149.1-2013, "IEEE Standard for Test Access Port and Boundary-Scan Architecture", 2013
2. ARM Ltd, "ARM Debug Interface Architecture Specification ADIv5/ADIv6", ARM IHI 0031, 2021
3. Segger Microcontroller, "J-Link User Guide", 2022
4. OpenOCD Project, "OpenOCD User's Guide", https://openocd.org/doc/html/index.html
5. J. Yiu, "The Definitive Guide to ARM Cortex-M0/M0+/M3/M4/M7 Processors", 2nd Edition, 2020
