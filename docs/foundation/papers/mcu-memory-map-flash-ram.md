---
schema_version: '1.0'
id: mcu-memory-map-flash-ram
title: MCU存储器映射：Flash/SRAM/外设地址空间
layer: 1
content_type: tutorial
difficulty: beginner
reading_time: 15
prerequisites:
  - arm-cortex-m-architecture-overview
tags:
  - 存储器映射
  - Flash
  - SRAM
  - 外设寄存器
  - Cortex-M
  - 链接脚本
  - 位带
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# MCU存储器映射：Flash/SRAM/外设地址空间

> **难度**：🟢 初级 | **领域**：嵌入式存储体系 | **关键词**：Memory Map, Flash, SRAM, MMIO | **阅读时间**：约 15 分钟

## 日常类比

四层大厦：1 楼书房（Flash，代码常驻）、2 楼工作台（SRAM，可读写）、3 楼控制面板（外设寄存器）、4 楼物业（系统/私有外设）。门牌号就是地址；Cortex-M 的 32 位地址空间约 4 GB，但芯片真实存储器远小于此，大量为保留区[1][2]。

## 摘要

解释 ARM Cortex-M 典型地址分区、Flash/SRAM/MMIO 用途、链接脚本与启动相关性。具体基址**以芯片参考手册 Memory Map 章节为准**（厂商并不完全相同）[2][3]。

## 1. 典型分区（Cortex-M 惯例）

| 区域倾向 | 地址量级（常见） | 用途 |
|----------|------------------|------|
| Code | 0x0000_0000 起 | Flash / 别名执行区 |
| SRAM | 0x2000_0000 起 | 数据、堆栈、堆 |
| Peripheral | 0x4000_0000 起 | 外设 MMIO |
| Vendor / System | 高地址 | 私有外设总线、调试等 |

注意：有的系列 Flash 在 0x0800_0000 并通过别名映射到 0x0000_0000 启动[2]。

| 存储器 | 特点 |
|--------|------|
| Flash | 非易失；按页/扇区擦写；执行原地或经加速器 |
| SRAM | 易失；快；可分 DTCM/多 bank |
| 外设 | 读写作副作用；需 volatile |

## 2. 和软件的关系

| 产物 | 作用 |
|------|------|
| 链接脚本 | 把 `.text/.data/.bss` 放到正确区域 |
| 启动文件 | 拷贝 `.data`、清 `.bss`、设栈顶 |
| 寄存器头文件 | 外设基址 + 偏移结构体 |

误把代码链到无存储器的地址会硬 fault；写 Flash 需用编程接口而非普通指针乱写[3]。

部分 Cortex-M3/M4 有 bit-band 别名区，便于原子改位；M0/M7 等支持情况不同，**查手册**[1]。

## 3. 局限、挑战与可改进方向

### 1. 手册与板级不一致

**局限**：拷贝他芯片地址导致外设全错。
**改进**：只使用本型号 CMSIS/pack；启动后读 ID 校验。

### 2. 栈/堆碰撞

**局限**：SRAM 小，深调用 + 大缓冲覆盖。
**改进**：链接脚本设栈极限；运行时水位染色；避免大局部数组。

### 3. 缓存/加速器一致性

**局限**：改 Flash 或 DMA 后 CPU 见旧数据。
**改进**：按手册清理缓存；MPU 属性配置正确。

### 4. 安全分区缺失

**局限**：应用可改任意外设。
**改进**：MPU/TrustZone 划分；见安全启动相关文。

## 4. 实践要点

1. 读手册 Memory map + 打开 `.map` 文件核对。
2. 外设访问一律 `volatile`。
3. 架构总览见 `arm-cortex-m-architecture-overview`。

## 参考文献

[1] ARM, Cortex-M generic user guides / ARMv7-M ARM.
[2] ST/NXP/Nordic 等 MCU Reference Manual — Memory map.
[3] Linker script and startup code tutorials (MCU vendor).
[4] CMSIS Core documentation.
[5] MPU configuration application notes.
[6] Flash programming model manuals.
[7] SRAM retention in low-power modes notes.
[8] Bit-banding usage and limitations articles.
[9] Memory barriers and volatile in embedded C.
[10] DMA and cache coherency guides.
[11] Executable in place (XIP) from external Flash notes.
