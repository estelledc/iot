---
schema_version: '1.0'
id: mcu-peripheral-multiplexing
title: MCU外设引脚复用与引脚分配策略
layer: 1
content_type: tutorial
difficulty: beginner
reading_time: 15
prerequisites:
  - mcu-memory-map-flash-ram
tags:
  - 引脚复用
  - GPIO
  - AFIO
  - 引脚分配
  - UART
  - SPI
  - PCB
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# MCU外设引脚复用与引脚分配策略

> **难度**：🟢 初级 | **领域**：MCU 系统设计 | **关键词**：Pin Mux, AF, GPIO, 冲突 | **阅读时间**：约 15 分钟

## 日常类比

活动中心同一房间可当会议室或健身房，但不能同时。MCU 引脚复用（multiplexing）同样：一颗物理脚可选 UART/SPI/GPIO/ADC 等功能，同一时刻只能一种。引脚分配就是排课表——排不好，PCB 画到一半才发现功能打架[1][2]。

## 摘要

说明复用概念、查阅数据手册 Pinout、工具链配置与冲突处理、高速/模拟脚特殊约束。具体 AF 编号**以封装数据手册为准**[1]。

## 1. 复用如何工作

| 层次 | 内容 |
|------|------|
| 物理焊盘 | 唯一 |
| GPIO 电路 | 输入/输出/上下拉 |
| 复用开关 | 接到选定外设信号 |
| 外设 | UART/SPI/I2C/TIM/ADC… |

配置顺序通常：开时钟 → 设模式/复用号 → 再初始化外设。部分系列用矩阵式“任意脚映射”，自由度更高但更易配错[2]。

| 约束类型 | 例子 |
|----------|------|
| 固定脚 | 启动模式、SWD、复位、电源 |
| 模拟脚 | ADC/比较器，注意数字噪声 |
| 高速脚 | SPI/时钟，走线长度与干扰 |
| 5V 容忍 | 并非所有 IO 都容忍 |

## 2. 分配策略

| 步骤 | 做法 |
|------|------|
| 1 | 列出必须外设与速率 |
| 2 | 锁定调试脚与启动脚 |
| 3 | 用 CubeMX/MCUXpresso 等查可行组合 |
| 4 | 优先让高速/模拟短且分区清晰 |
| 5 | 预留测试点与复用冲突备选脚 |

| 常见冲突 | 处理 |
|----------|------|
| 同一 TIM 通道被两处占用 | 换通道/换定时器 |
| I2C 与调试脚重叠 | 改映射或改调试接口 |
| USB 固定 DP/DM | 不能挪，先占位 |

## 3. 局限、挑战与可改进方向

### 1. 晚期改需求

**局限**：硬件已打样，软件要加外设无脚可用。
**改进**：早期预留 GPIO；选脚数裕量更大的封装。

### 2. 文档误读

**局限**：看错封装的 AF 表。
**改进**：核对 Package 列；读 Errata。

### 3. 模拟/数字相邻

**局限**：SPI 边沿耦合进 ADC。
**改进**：空间分离、采样时静默高速外设、加屏蔽地。

### 4. 上电默认态

**局限**：复位后脚为输入浮空，外设误动作。
**改进**：外部上下拉；尽快软件初始化；安全默认电平。

## 4. 实践要点

1. 原理图阶段就导出引脚表进版本库。
2. 量产锁定复用配置，禁止“临时改脚”无文档。
3. 与 PCB 分区结合，见低噪声布局文。

## 参考文献

[1] MCU datasheet — Pinouts and alternate functions tables.
[2] STCubeMX / vendor pin configuration tool manuals.
[3] GPIO electrical characteristics application notes.
[4] SWD/JTAG pin reservation guidance.
[5] ADC pin analog switch limitations.
[6] High-speed SPI routing and pin selection notes.
[7] I2C open-drain pin requirements.
[8] USB physical layer fixed pins documentation.
[9] PCB design for MCU breakout and test points.
[10] Errata sheets related to remapping bugs.
[11] Power-on reset GPIO default state notes.
