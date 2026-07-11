---
schema_version: '1.0'
id: nor-flash-spi-qspi-xip
title: NOR Flash SPI/QSPI接口与XIP执行
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - spi-protocol-modes-timing
  - nand-flash-wear-leveling-ftl
tags:
  - NOR Flash
  - QSPI
  - XIP
  - SPI
  - 嵌入式存储
  - 启动
  - 存储器映射
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# NOR Flash SPI/QSPI接口与XIP执行

> **难度**：🟡 中级 | **领域**：嵌入式存储接口 | **关键词**：NOR, QSPI, XIP, Dummy cycle | **阅读时间**：约 16 分钟

## 日常类比

NOR Flash 像一本可随机翻页的说明书：任意地址可读一个字节，适合存放程序。NAND 更像必须整章擦写的笔记本。MCU 通过 SPI/QSPI（Quad SPI）读这本说明书；**XIP**（Execute-In-Place）则是不把整书抄进 RAM，边翻边执行——省 RAM，但翻页（总线）慢时会卡顿[1][2]。

## 摘要

对比 NOR/NAND、SPI→Dual/Quad/QPI 带宽演进、命令与 Dummy 周期、XIP/Cache/预取，以及写入擦除与 OTP。吞吐量为时钟与模式估算量级，以芯片与控制器手册为准[3]。

## 1. NOR 角色

| 对比 | NOR | NAND |
|------|-----|------|
| 随机读 | 强 | 弱（页） |
| 容量单价 | 较高 | 较低 |
| 代码原地执行 | 常见 | 需 FTL+拷贝 |
| IoT 用途 | 固件/参数 | 大日志/文件系统 |

## 2. 接口模式

| 模式 | 数据线 | 直觉 |
|------|--------|------|
| SPI | 1 | 兼容最好 |
| Dual | 2 | 读加速 |
| Quad | 4 | IoT 主流高速 |
| QPI | 命令也四线 | 需进/出 QPI 序列 |

读命令含指令、地址、Dummy、数据。Dummy 周期给 Flash 阵列时间，过少则数据错误；时钟越高往往 Dummy 越多[3][4]。

## 3. XIP 与性能

控制器把 Flash 映射到地址空间，取指即发 QSPI 事务。Cache 与预取命中时接近片上性能；冷启动、密集跳转或擦写冲突时延迟尖峰。持续写/擦期间通常不能同时 XIP 同颗粒——需双 Bank、拷贝关键 ISR 到 RAM 或暂停执行策略[2][5]。

| 芯片例 | 注意 |
|--------|------|
| STM32 QSPI | Memory-mapped 模式配置 |
| ESP32 | 外部 Flash 映射缓存 |

页编程、扇区/块擦除、状态寄存器 WIP 位轮询；OTP（One-Time Programmable）区可存密钥指纹/序列号（不可改）[6]。

## 4. 局限、挑战与可改进方向

### 1. XIP 抖动导致实时失败

**局限**：Cache 未命中使控制环超时。
**改进**：关键代码链到 RAM/ITCM；提高 Cache；测最坏取指延迟[5]。

### 2. 擦写时取指冲突

**局限**：OTA 擦除同 Flash 导致跑飞。
**改进**：双区/双芯片；擦写期间向量表与 ISR 在 RAM[2]。

### 3. 高速信号完整性

**局限**：Quad 高 MHz 下飞线样板失败。
**改进**：短等长、完整地、按手册串阻；降频换稳定[4]。

### 4. 安全启动与明文固件

**局限**：外部 NOR 可被探针读出。
**改进**：片上加密引擎 + 安全启动链；OTP 存哈希[6]。

## 总结

SPI/QSPI NOR + XIP 是 IoT MCU 扩展固件容量的标准做法。带宽靠 Quad 与 Dummy 调对，实时性靠 Cache/RAM 驻留，可靠性靠擦写与启动策略，而不是只拉高 SCLK。

## 参考文献

[1] NOR vs NAND Flash 基础白皮书（Micron/Spansion 等）.
[2] ST, Quad-SPI 接口与 XIP 应用笔记.
[3] JEDEC SFDP / 串行 Flash 命令集公开材料.
[4] Winbond / Macronix / ISSI 等 SPI NOR 数据手册.
[5] 嵌入式 XIP 性能与 Cache 应用笔记.
[6] Flash OTP 与安全启动应用笔记.
[7] Espressif 外部 Flash 映射文档.
[8] SPI 时序与模式（CPOL/CPHA）基础.
[9] OTA 双区更新与 Flash 布局实践.
[10] QPI 进入/退出序列厂商说明.
[11] 信号完整性与高速 QSPI 布局指南.
[12] 页编程/擦除时间与磨损注意（NOR 亦有限 P/E）.
