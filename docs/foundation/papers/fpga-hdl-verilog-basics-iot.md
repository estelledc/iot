---
schema_version: '1.0'
id: fpga-hdl-verilog-basics-iot
title: FPGA Verilog HDL基础与IoT外设实现
layer: 1
content_type: tutorial
difficulty: beginner
reading_time: 18
prerequisites:
  - fpga-iot-acceleration
  - gpio-configuration-modes
tags:
  - FPGA
  - Verilog
  - HDL
  - UART
  - SPI
  - PWM
  - 数字逻辑
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# FPGA Verilog HDL基础与IoT外设实现

> **难度**：🟢 初级 | **领域**：FPGA 入门 | **关键词**：Verilog, 并发, UART/SPI/PWM | **阅读时间**：约 18 分钟

## 日常类比

写软件像按菜谱一步步做；写硬件描述语言（Hardware Description Language, HDL）像同时安排厨房所有工位——同一时钟边沿，多块逻辑一起动作。Verilog 描述的是电路结构，综合后变成现场可编程门阵列（Field-Programmable Gate Array, FPGA）上的查找表与触发器，不是 CPU 指令序列[1][2]。

## 摘要

建立并发思维、`wire`/`reg`、时序与组合 always，并用通用异步收发传输器（UART）、串行外设接口（SPI）、脉冲宽度调制（PWM）说明物联网外设骨架。语法以 IEEE 1364/SystemVerilog 常用可综合子集为准[3]。

## 1. 软件 vs HDL

| 维度 | C/Python | Verilog HDL |
|------|----------|-------------|
| 模型 | 顺序 | 并发 |
| 时间 | 指令 | 时钟周期 |
| 产物 | 可执行文件 | 比特流 |

每个 `always`/`assign` 对应并行硬件。`wire` 像连线；`reg` 在时钟 always 中通常推断寄存器，在组合 always 中可为组合逻辑[1]。

## 2. 可综合骨架

同步复位计数器、有限状态机（Finite State Machine, FSM）是外设核心。IoT 上常见：波特率分频的 UART TX/RX、SPI 主模式移位寄存器、PWM 比较计数器驱动发光二极管或电机[4][5]。

| 外设 | 关键硬件块 | 注意 |
|------|------------|------|
| UART | 波特计数 + 移位 | 亚稳态：异步 RX 需同步 |
| SPI | 移位 + SCLK 生成 | CPOL/CPHA 模式 |
| PWM | 计数器 + 比较 | 分辨率 vs 频率权衡 |
| GPIO | 三态/寄存输出 | 与 MCU 电平与上拉 |

仿真（testbench）先看波形再上板；引脚约束与时序约束（时钟、输入延迟）不可省[6]。

## 3. 工具链一瞥

综合 → 布局布线 → 比特流；厂商工具如 Vivado / Quartus / 开源 Yosys+nextpnr。初学可用小容量 FPGA 点亮 LED、再做 UART 环回[7]。

## 4. 局限、挑战与可改进方向

### 1. 把 HDL 当软件写

**局限**：在 always 里写长“算法式”顺序思维，仿真过但面积时序爆炸。
**改进**：显式流水线/FSM；每级寄存器清晰；对照 RTL 原理图[2]。

### 2. 异步与亚稳态

**局限**：未同步的跨时钟/外部输入导致偶发错误。
**改进**：双触发器同步；CDC 用握手或异步 FIFO[8]。

### 3. 阻塞/非阻塞混用

**局限**：时序 always 用 `=` 导致仿真与综合不一致风险。
**改进**：时序用 `<=`，组合用 `=`；避免同一 reg 多驱动[3]。

### 4. 外设只“能跑”未验证

**局限**：上板偶发波特率不准、SPI 采样沿错误。
**改进**：自检环回；逻辑分析仪；约束真实 IO 延迟[5][6]。

## 总结

先掌握并发、时钟与 FSM，再用 UART/SPI/PWM 练可综合外设；仿真与约束和代码同等重要。进阶再学总线与软核，而不是堆更长组合逻辑。

## 参考文献

[1] IEEE Std 1364, Verilog Hardware Description Language.
[2] C. Maxfield, The Design Warrior's Guide to FPGAs.
[3] Sutherland, Verilog-2001 / 可综合编码指南相关文献.
[4] Xilinx/AMD, UG901 Vivado 综合用户指南（编码建议）.
[5] 开源 UART/SPI 核与 FPGA4Fun 等教程（入门对照）.
[6] IEEE 时序约束与 SDC 基础应用笔记.
[7] Yosys / nextpnr 开源 FPGA 工具链文档.
[8] Clifford Cummings, 异步信号同步与 CDC 论文（SNUG）.
[9] Intel Quartus, Recommended HDL Coding Styles.
[10] Pong P. Chu, FPGA Prototyping by Verilog Examples.
[11] ARM AMBA / 简单APB外设接口入门对照.
[12] Lattice / 低成本 FPGA 入门板用户手册.
