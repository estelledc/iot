---
schema_version: '1.0'
id: one-wire-protocol-ds18b20
title: 1-Wire协议与DS18B20温度传感器实战
layer: 1
content_type: tutorial
difficulty: beginner
reading_time: 16
prerequisites:
  - humidity-sensor-capacitive-resistive
  - ntc-thermistor-linearization
tags:
  - 1-Wire
  - DS18B20
  - 温度传感器
  - 单总线
  - CRC
  - 寄生供电
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 1-Wire协议与DS18B20温度传感器实战

> **难度**：🟢 初级 | **领域**：单总线通信 | **关键词**：1-Wire, DS18B20, CRC | **阅读时间**：约 16 分钟

## 日常类比

教室里老师只用一根麦克风线逐个点名、收回答——不必每人一根线，线还能带一点电。这就是 **1-Wire**：一根数据线加地线，完成供电、寻址与通信。物联网（Internet of Things, IoT）里 **DS18B20** 是最常见的 1-Wire 温度计，冷链、温室、机柜巡检常靠它“一根线串一串”[1][2]。

## 摘要

梳理 1-Wire 复位/时隙、ROM 与功能命令、DS18B20 分辨率与循环冗余校验（Cyclic Redundancy Check, CRC），以及多点与长线注意点。时序以数据手册微秒值为准；文中时间为典型量级[1]。

## 1. 总线与供电

开漏总线需上拉（常见约 4.7 kΩ）。外部供电：VDD 接 3.0–5.5 V。寄生供电：VDD 接地，靠 DQ 高电平给片内电容充电；温度转换电流较大时需强上拉（如 MOSFET），否则易失败[1][2]。

每器件 64 位 ROM：家族码（DS18B20 为 0x28）+ 48 位序列号 + CRC-8，支持多点寻址[1]。

## 2. 时序与命令

通信由主机发起：复位脉冲（拉低约 ≥480 µs）→ 从机存在脉冲 → 写/读时隙（写 0 拉低较长，写 1 短拉低后释放；读则短拉低后采样）[2]。

| 操作 | 时间量级（手册典型） |
|------|----------------------|
| 复位拉低 | ≥480 µs |
| 存在检测窗口 | 约 60–75 µs 量级 |
| 写 0 / 写 1 | 约 60 µs / 数 µs 拉低 |
| 读采样 | 时隙前约 15 µs 内 |

| ROM 命令 | 码 | 用途 |
|----------|-----|------|
| Search ROM | 0xF0 | 枚举 |
| Read ROM | 0x33 | 单器件读 ID |
| Match ROM | 0x55 | 指定器件 |
| Skip ROM | 0xCC | 单器件或广播 |
| Alarm Search | 0xEC | 报警器件 |

| 功能命令 | 码 | 用途 |
|----------|-----|------|
| Convert T | 0x44 | 启动转换 |
| Read Scratchpad | 0xBE | 读 9 字节 |
| Write Scratchpad | 0x4E | 写 TH/TL/配置 |
| Copy Scratchpad | 0x48 | 写入 EEPROM |

多点推荐：Skip ROM + Convert T 广播转换，再逐个 Match ROM + Read Scratchpad，总等待约一次满分辨率转换时间而非 N 倍[1]。

## 3. DS18B20 数据与 CRC

| 参数 | 典型规格 |
|------|----------|
| 范围 | −55 ~ +125 °C |
| 精度 | −10 ~ +85 °C 约 ±0.5 °C |
| 分辨率 | 9–12 bit 可选（默认 12） |
| 转换时间 | 约 94 ms（9-bit）~ 750 ms（12-bit） |

温度 16 位补码，12-bit 时约 0.0625 °C/LSB。暂存器 9 字节，末字节 CRC-8（多项式 \(x^8+x^5+x^4+1\)）；长线必须校验[1][3]。

## 4. 实现与排障

GPIO 位带需要微秒级延时（Cortex-M 可用 DWT）；关键段关中断或提高优先级，避免实时操作系统（Real-Time Operating System, RTOS）切换打断时隙[5]。

| 现象 | 常见原因 | 处理 |
|------|----------|------|
| 恒为 85.0 °C | 上电默认，转换未完成 | 查存在脉冲、等待、强上拉 |
| 偶发错误 | 中断/电容/CRC | 关中断、降上拉、校验 |
| 长线丢器件 | 电容与压降 | 降上拉阻值、双绞、避免乱星形、必要时中继[3] |

线长数十米内常可工作；更长需屏蔽双绞、约 2.2 kΩ 量级上拉、拓扑与终端策略，以应用笔记为准[3]。

## 5. 局限、挑战与可改进方向

### 1. 软件时序脆弱

**局限**：无独立时钟，位带被中断打断即通信失败。
**改进**：硬件 1-Wire 主控（如 DS2482）；或硬件定时器 + 关中断临界区[2][5]。

### 2. 寄生供电扩展性差

**局限**：多点同时转换电流叠加，强上拉设计复杂。
**改进**：外部供电；或分组转换限制并发电流[1]。

### 3. 总线电容限制点数与距离

**局限**：长线上升沿变慢，枚举与读数不稳。
**改进**：按 AN148 做线规/上拉/拓扑；超长用中继[3]。

### 4. 转换延迟影响控制环

**局限**：12-bit 约 0.75 s，不适合快环温控。
**改进**：降分辨率；或换更快数字温度计/本地模拟前端[1]。

## 总结

1-Wire + DS18B20 用最少线数做多点测温；时序、CRC 与 85 °C 默认值是调试三件套。多点用广播转换+逐个读；长线按应用笔记做电气，而不是只改代码延时。

## 参考文献

[1] Analog Devices / Maxim, DS18B20 Datasheet.
[2] Maxim, Application Note 937, 1-Wire Communication Protocol.
[3] Maxim, Application Note 148, Long Line 1-Wire Networks.
[4] Dallas Semiconductor, Book of iButton Standards（历史背景）.
[5] STMicroelectronics, STM32 参考手册 / HAL 延时与 GPIO.
[6] Maxim, DS2482 1-Wire 主控数据手册.
[7] CRC-8 算法与查表实现（标准通信教材/应用笔记）.
[8] IEC/相关温度测量不确定度基础文献.
[9] RTOS 环境下位带总线临界区设计实践.
[10] CAT5 等线缆在 1-Wire 布线中的应用讨论.
[11] DS18B20 分辨率与转换时间表（数据手册章节）.
[12] 多点传感器总线拓扑（线型 vs 星型）应用笔记.
