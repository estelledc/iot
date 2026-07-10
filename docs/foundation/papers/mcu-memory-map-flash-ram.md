---
schema_version: '1.0'
id: mcu-memory-map-flash-ram
title: MCU存储器映射：Flash/SRAM/外设地址空间
layer: 1
content_type: UNKNOWN
difficulty: beginner
reading_time: 18
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# MCU存储器映射：Flash/SRAM/外设地址空间

> **难度**：🟢 初级 | **领域**：嵌入式存储体系 | **阅读时间**：约 18 分钟

## 引言

想象你住在一栋 4 层楼的大厦里。1 楼是书房 (存放书籍，只能读不能改)，2 楼是工作台 (可以随意写画擦除)，3 楼是控制面板 (拨动开关控制整栋楼的灯光和空调)，4 楼是物业管理处 (处理报警、定时器等系统事务)。每个房间都有唯一的门牌号，你只需要知道门牌号就能找到对应的功能。

MCU 的存储器映射就是这个逻辑：4GB 的地址空间就是整栋大厦，不同地址范围对应不同功能——存放代码的 Flash、存放运行数据的 SRAM、控制外设的寄存器。理解这个映射，是读懂 MCU datasheet 和编写可靠嵌入式程序的基础。

## 1. ARM Cortex-M 4GB 地址空间总览

### 1.1 为什么是 4GB

Cortex-M 使用 32 位地址总线，可寻址空间为 2^32 = 4GB。注意：这并不意味着芯片真的有 4GB 物理存储器，大部分地址是未使用的保留区。

### 1.2 地址空间分区

ARM 固定了各区域位置，所有 Cortex-M 芯片都遵循此分区：

| 地址范围 | 大小 | 名称 | 用途 |
|----------|------|------|------|
| 0xE0000000 - 0xFFFFFFFF | 512MB | 系统区 | NVIC, SysTick, SCB, 调试 |
| 0xA0000000 - 0xDFFFFFFF | 1GB | 外设区 (别名) | 外设 bit-band 别名 |
| 0x60000000 - 0x9FFFFFFF | 1GB | SRAM 区 (别名) | SRAM bit-band 别名 |
| 0x40000000 - 0x5FFFFFFF | 512MB | 外设区 | APB/AHB 外设寄存器 |
| 0x20000000 - 0x3FFFFFFF | 512MB | SRAM 区 | 片上 SRAM |
| 0x00000000 - 0x1FFFFFFF | 512MB | 代码区 | Flash (代码 + 常量) |

规律：地址从低到高，功能从"存代码"到"控硬件"再到"管系统"。这个分区是 ARM 硬编码的，芯片厂商 (ST, NXP, TI) 不能移动位置，只能决定各区域内放多少实际存储器和外设。

## 2. Flash 区域 (0x00000000 - 0x1FFFFFFF)

### 2.1 Flash 的角色与 XIP 执行

Flash 是 MCU 的"书房"——掉电不丢失，存储程序代码、常量数据和中断向量表。

Cortex-M 支持直接从 Flash 取指执行 (XIP, Execute In Place)，无需先拷贝到 RAM。代价是 Flash 读取速度通常比 SRAM 慢 (25-50MHz vs CPU 全速)，因此 STM32 提供 Flash 预取指和缓存来加速。

### 2.2 中断向量表与启动地址

地址 0x00000000 存放栈顶指针 (MSP 初始值)，0x00000004 存放 Reset_Handler 地址，后续每 4 字节一个中断入口。上电后 CPU 自动从这两个地址取值并跳转执行。

STM32F103 的 Flash 起始地址通常是 0x08000000 (不是 0x00000000)。0x00000000 区域通过 alias 指向不同存储器，由 BOOT 引脚决定：

| BOOT1 | BOOT0 | 0x00000000 映射到 | 启动模式 |
|-------|-------|-------------------|----------|
| x | 0 | 主 Flash (0x08000000) | 正常运行 |
| 0 | 1 | 系统存储器 (串口 Bootloader) | ISP 下载 |
| 1 | 1 | SRAM (0x20000000) | 调试用 |

## 3. SRAM 区域 (0x20000000 - 0x3FFFFFFF)

### 3.1 SRAM 的角色

SRAM 是 MCU 的"工作台"——速度快、可读写，但掉电丢失。运行时存储全局/静态变量 (.data + .bss)、堆 (heap) 和栈 (stack)。

### 3.2 栈与堆

栈从高地址向低地址增长 (向下生长)，Cortex-M 使用满递减栈 (Full Descending)：

```
高地址 0x20005000 ──┐
                    │ 栈顶 (SP 指向最后一个压入的数据)
                    │ 返回地址
                    │ 局部变量
                    │ ...
低地址              │ 栈底
         ──────────┘
```

堆从低地址向高地址增长。SRAM 的典型布局：

```
.data --> .bss --> heap --> ... <-- stack
                    |               |
                    向上增长         向下增长
```

heap 和 stack 之间的空间是两者的动态可用空间，相遇则崩溃。栈溢出是最常见的运行时错误之一。

### 3.3 .data 和 .bss 段

- **.data**：已初始化的全局/静态变量。Flash 中存初始值，启动时拷贝到 SRAM。
- **.bss**：未初始化或初始化为 0 的全局/静态变量。不占 Flash，启动时 SRAM 中清零。

```c
int g_counter = 42;     // .data (有初始值, Flash + SRAM 各一份)
int g_buffer[100];       // .bss (初始为 0, 仅占 SRAM)
const int g_magic = 7;   // .rodata (只读, 仅 Flash)
```

## 4. 外设寄存器空间 (0x40000000 - 0x5FFFFFFF)

### 4.1 内存映射 I/O (Memory-Mapped I/O)

外设寄存器被映射到内存地址空间中，读写某个地址就是操作硬件外设，不需要特殊 I/O 指令：

```c
#define GPIOA_BASE  0x40010800
#define GPIOA_ODR  (*(volatile uint32_t *)(GPIOA_BASE + 0x0C))
GPIOA_ODR |= (1 << 5);  // 点亮 LED
```

关键：必须加 `volatile`，告诉编译器不要优化掉对硬件寄存器的读写。

### 4.2 APB/AHB 总线与外设地址

不同总线挂载不同速度的外设：

| 总线 | 地址 (典型) | 速度 | 典型外设 |
|------|-------------|------|----------|
| APB1 | 0x40000000 起 | 36MHz | USART, SPI, I2C, TIM2-7 |
| APB2 | 0x40010000 起 | 72MHz | GPIO, ADC, TIM1 |
| AHB  | 0x40018000 起 | 最高 | DMA, Flash 接口 |

Datasheet 的 Memory Map 章节列出各外设基地址，每个外设内部寄存器按偏移排列 (如 GPIOA 的 CRL 偏移 0x00, ODR 偏移 0x0C)。基地址 + 偏移 = 寄存器绝对地址。

## 5. 系统区域 (0xE0000000 - 0xFFFFFFFF)

### 5.1 核心系统外设

此区域是 ARM Cortex-M 内核自带的，不属于芯片厂商外设：

| 地址 | 名称 | 用途 |
|------|------|------|
| 0xE000E000 | SCB | 系统控制块 |
| 0xE000E100 | NVIC | 嵌套向量中断控制器 |
| 0xE000E010 | SysTick | 系统定时器 |
| 0xE000EDF0 | DWT | 数据观察点与跟踪 |

### 5.2 NVIC 与 SysTick 示例

```c
// NVIC: 使能中断并设置优先级
NVIC->ISER[0] = (1 << 6);     // 使能 EXTI0
NVIC->IP[6] = (5 << 4);       // 优先级 5 (只用高 4 位)

// SysTick: 1ms 中断 (72MHz 时钟)
SysTick->LOAD = 72000 - 1;    // 重载值
SysTick->VAL  = 0;            // 清空
SysTick->CTRL = 0x07;         // 使能 + 中断 + CPU 时钟源
```

## 6. Bit-Banding 机制

### 6.1 问题：位操作的开销

传统方式修改寄存器某一位需要"读-改-写"三步：

```c
// 传统方式：设置 GPIOA 第 5 位
uint32_t temp = GPIOA->ODR;  // 读
temp |= (1 << 5);             // 改
GPIOA->ODR = temp;            // 写
```

在多中断环境下，"读-改-写"之间可能被中断打断，导致数据不一致。

### 6.2 Bit-Banding 解决方案

Bit-banding 将 SRAM 和外设区的每个 bit 映射到别名区的一个 32 位字。对别名区写 1/0 等效于对原 bit 置 1/0，且是原子操作。

```
别名区地址计算公式:
bit_word_addr = bit_band_base + (byte_offset * 32) + (bit_number * 4)

其中:
  - SRAM bit-band base:    0x22000000
  - Peripheral bit-band base: 0x42000000
  - byte_offset = 目标地址 - 区域起始地址
  - bit_number = 0~31
```

示例——用 bit-band 原子操作 GPIOA 第 5 位：

```c
// GPIOA_ODR 地址: 0x4001080C
// byte_offset = 0x4001080C - 0x40000000 = 0x1080C
// bit_number = 5
// alias_addr = 0x42000000 + 0x1080C * 32 + 5 * 4
//            = 0x42000000 + 0x210180 + 0x14
//            = 0x42210194

#define PA5_BIT  (*(volatile uint32_t *)0x42210194)

PA5_BIT = 1;   // 原子置位 GPIOA pin5
PA5_BIT = 0;   // 原子清零 GPIOA pin5
```

注意：Cortex-M0/M0+ 不支持 bit-banding，仅 M3/M4/M7 有此特性。

## 7. Linker Script 与段映射

### 7.1 基本段 (Section) 说明

链接脚本 (通常 .ld 后缀) 告诉链接器各段放到什么地址。核心段：

| 段名 | 存放内容 | 最终位置 | 特点 |
|------|----------|----------|------|
| .text | 代码 + 只读常量 | Flash | 只读，不修改 |
| .rodata | 只读数据 (const) | Flash | 只读 |
| .data | 已初始化全局/静态变量 | Flash(存初值) + SRAM(运行时) | 启动时从 Flash 拷贝到 SRAM |
| .bss | 未初始化全局/静态变量 | SRAM | 启动时清零 |
| .stack | 栈空间 | SRAM 高地址 | 向下增长 |

### 7.2 STM32 链接脚本示例

```ld
/* STM32F103C8T6: 64KB Flash, 20KB SRAM */
MEMORY {
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 64K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 20K
}
SECTIONS {
    .isr_vector : { KEEP(*(.isr_vector)) } > FLASH
    .text : { *(.text*) *(.rodata*) } > FLASH
    _sidata = LOADADDR(.data);
    .data : {
        _sdata = .; *(.data*) _edata = .;
    } > RAM AT > FLASH   /* 运行在 RAM, 加载在 Flash */
    .bss : {
        _sbss = .; *(.bss*) *(COMMON) _ebss = .;
    } > RAM
    _estack = ORIGIN(RAM) + LENGTH(RAM);
}
```

### 7.3 Scatter Loading 与启动拷贝

`AT > FLASH` 语法是 scatter loading 的体现：.data 段的加载地址 (LMA) 在 Flash，运行地址 (VMA) 在 SRAM。启动代码负责拷贝：

```c
// 从 Flash 拷贝 .data 到 SRAM, 再清零 .bss
uint32_t *src = &_sidata, *dst = &_sdata;
while (dst < &_edata) *dst++ = *src++;
dst = &_sbss;
while (dst < &_ebss) *dst++ = 0;
```

如果启动代码未正确拷贝 .data，全局变量值将是随机值 (SRAM 上电内容不确定)。

## 8. STM32F103 内存映射实例与程序布局

| 地址 | 内容 | 大小 |
|------|------|------|
| 0x08000000 | 主 Flash | 64KB |
| 0x20000000 | SRAM | 20KB |
| 0x40000000 | APB1 外设起始 | - |
| 0x40010000 | APB2 外设起始 | - |
| 0x1FFFF800 | 系统存储器 (Bootloader) | 2KB |

编译一个 LED 闪烁程序后，arm-none-eabi-size 输出：

```
Program Size: Code=2048  RO-data=320  RW-data=16  ZI-data=1028

Flash 占用 = Code + RO-data + RW-data = 2384 bytes
SRAM 占用  = RW-data + ZI-data + stack = 1044 + stack_size
```

- Code = .text (函数代码)，RO-data = .rodata (只读常量)
- RW-data = .data (Flash 存初值 + SRAM 存运行值)，ZI-data = .bss (仅 SRAM)

## 9. 如何阅读 Datasheet 中的内存布局

关键章节：**Memory Map** (地址分区表)、**Register Map** (寄存器偏移与复位值)、**Bus Architecture** (总线连接)。

阅读步骤：

1. Memory Map 章节确认 Flash/SRAM 基地址和大小
2. 找到目标外设 (如 USART1) 基地址
3. Register Map 查找寄存器偏移，基地址 + 偏移 = 绝对地址
4. 对照位定义表理解每个 bit 含义

示例：Datasheet 写 "USART1 base = 0x40013800, USART_SR offset = 0x00, TXE = bit7"，则 TXE 状态 = `(0x40013800 >> 7) & 1`。现代开发通常使用厂商头文件 (stm32f1xx.h) 自动映射，但理解原理才能在出错时快速定位。

## 10. 常见错误与避坑

### 10.1 栈溢出 (Stack Overflow)

**错误认知**：栈空间够用就行，不用精确计算。
**正确理解**：必须计算最坏情况栈用量 (所有嵌套调用 + 中断 + 局部变量)。工具：`-fstack-usage` 编译选项或 Stack Analyzer。

典型溢出场景：
- 深度递归
- 大数组做局部变量 (应该用 static 或 malloc)
- 中断嵌套层数过多

### 10.2 .data 段未初始化

**错误认知**：全局变量有初始值，上电后自动正确。
**正确理解**：.data 段的初始值存在 Flash 中，必须由启动代码拷贝到 SRAM。如果启动代码有 bug 或被跳过，全局变量将是随机值。

检查方法：在调试器中观察 `_sdata` 到 `_edata` 区域是否在 main() 之前被正确填充。

### 10.3 忘记 volatile

**错误认知**：编译器知道我在操作硬件寄存器，会正确处理。
**正确理解**：编译器可能优化掉看似"多余"的读写。所有外设寄存器指针必须加 volatile。

```c
// 错误: 第二次写可能被优化掉
uint32_t *reg = (uint32_t *)0x4001080C;
*reg = 0x01; *reg = 0x02;  // *reg = 0x02 可能消失

// 正确: volatile 阻止优化
volatile uint32_t *reg = (volatile uint32_t *)0x4001080C;
*reg = 0x01; *reg = 0x02;  // 两次写入都保留
```

### 10.4 对 Flash 的误操作

**错误认知**：Flash 和 SRAM 一样可以随意读写。
**正确理解**：Flash 写入需要先解锁、擦除 (整页)、再编程。不能像 RAM 一样直接赋值。Flash 擦写次数有限 (典型 10K-100K 次)，频繁擦写会损坏。

### 10.5 忽略对齐要求

**错误认知**：任何地址都可以读写 32 位数据。
**正确理解**：M3/M4 支持非对齐访问但有性能惩罚，DMA 缓冲区等要求严格对齐。建议始终 4 字节对齐。

## 总结

MCU 存储器映射的核心模型可以压缩为一句话：**4GB 地址空间按功能分区，代码在 Flash，数据在 SRAM，控制硬件靠外设寄存器，内核管理靠系统区**。

关键要点回顾：

1. 地址空间是固定的 (ARM 定义)，物理存储器是可变的 (芯片厂商决定)
2. Flash 存代码和常量 (掉电不丢失)，SRAM 存运行数据 (掉电丢失)
3. 外设寄存器通过内存映射访问，必须用 volatile
4. .data 段需要启动代码从 Flash 拷贝到 SRAM，.bss 段需要清零
5. bit-banding 提供原子位操作能力 (M3/M4/M7)
6. 栈从高地址向低地址增长，必须预留足够空间

掌握存储器映射后，阅读 Datasheet 的 Memory Map 章节、编写 Linker Script、调试内存相关问题都会变得有迹可循。

## 参考文献

1. ARM. *Cortex-M3 Technical Reference Manual (DDI 0337)*. ARM Limited, 2010. Chapter 3: Memory Model.
2. STMicroelectronics. *STM32F103xx Reference Manual (RM0008)*. STMicroelectronics, 2018. Section 2.3: Memory Map.
3. Joseph Yiu. *The Definitive Guide to ARM Cortex-M3 and Cortex-M4 Processors*. 3rd ed. Newnes, 2014. Chapter 5: Memory System.
4. GNU Linker Documentation. *LD (GNU Linker) Manual: Section 3: Linker Scripts*. Free Software Foundation.
5. Chris Svec. "Understanding the C/C++ memory model: .text, .data, .bss". Embedded Artistry, 2020.
