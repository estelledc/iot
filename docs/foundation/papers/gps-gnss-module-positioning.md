---
schema_version: '1.0'
id: gps-gnss-module-positioning
title: GPS/GNSS定位模组硬件接口与精度分析
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - antenna-impedance-matching-network
  - duty-cycling-sensor-node
tags:
  - GNSS
  - GPS
  - NMEA
  - TTFF
  - RTK
  - 低功耗定位
  - 天线
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# GPS/GNSS定位模组硬件接口与精度分析

> **难度**：🟡 中级 | **领域**：定位模组 | **关键词**：GNSS, NMEA, TTFF, RTK, 天线 | **阅读时间**：约 18 分钟

## 日常类比

全球导航卫星系统（Global Navigation Satellite System, GNSS）像同时问多座远处灯塔要距离，交会出你的位置。模组负责收星、解算，再通过串口用 NMEA 等语句把经纬度交给微控制器；天线与天空视野决定“听得清不清”[1][2]。

## 摘要

覆盖多星座、硬件接口、NMEA、精度等级（含实时动态 RTK）、首次定位时间（Time To First Fix, TTFF）与功耗策略。米级/厘米级与冷热启动时间为典型量级，**以模组手册与实测环境为准**[3][4]。

## 1. 系统与接口

GPS/BDS/Galileo/GLONASS 等多星座可提高城市可用性。硬件：UART（主）、I²C/SPI（部分）、1PPS、天线供电（有源天线）、备份电源保星历[2][3]。

| 语句/信号 | 用途 |
|-----------|------|
| RMC/GGA 等 | 时间、位置、质量指示 |
| 1PPS | 时间同步 |
| Assist 数据 | 缩短 TTFF（A-GNSS） |

## 2. 精度与增强

| 等级 | 精度倾向 | 条件 |
|------|----------|------|
| 单点标准 | 米级 | 开阔天空 |
| SBAS 等 | 亚米～米 | 服务区 |
| RTK/PPP | 厘米～分米 | 基站/改正链 |

多径、城市峡谷、天线净空不足会显著变差。资产追踪常用周期唤醒定位 + 深睡；连续导航功耗高一个数量级以上并不罕见[5][6]。

## 3. TTFF 与天线

冷启动最长，温/热启动与 A-GNSS 可明显缩短。天线：远离开关电源与蜂窝天线；有源天线注意增益与电缆损耗；接地与匹配按模组参考设计[7]。短时丢星可用惯性航位推算补，误差随时间累积，不能长期替代[8]。

## 4. 局限、挑战与可改进方向

### 1. 室内/峡谷不可用

**局限**：可见星不足导致漂或无 fix。
**改进**：多星座；融合 Wi-Fi/蜂窝；业务允许时室外补点[1]。

### 2. 功耗与 TTFF 矛盾

**局限**：睡太死每次冷启动耗电耗时。
**改进**：备份电源保星历；A-GNSS；拉长定位间隔并测平均电流[5]。

### 3. 天线布局失败

**局限**：金属壳/电池遮挡导致标称精度达不到。
**改进**：早期打板按参考设计；有源天线外置；看载噪比[7]。

### 4. NMEA 解析脆弱

**局限**：只信坐标不看质量字段，用无效点。
**改进**：校验和、fix 质量、HDOP/卫星数门控[2]。

## 总结

GNSS 模组选型先定精度等级与功耗预算，再抠天线与辅助定位。物联网追踪的成功多半在射频与电源策略，而不在“解析一句 GGA”。

## 参考文献

[1] E. D. Kaplan, Understanding GPS/GNSS, Artech House.
[2] u-blox, NEO-M9N Integration Manual.
[3] Quectel, LC29H 等 GNSS 产品规格书.
[4] P. Misra, Global Positioning System: Signals, Measurements, and Performance.
[5] GNSS 模组低功耗周期定位应用笔记（多厂商）.
[6] RTK/PPP 服务与物联网精度需求对照白皮书.
[7] 天线厂商 GNSS 有源天线与净空设计指南.
[8] B. Hofmann-Wellenhof, GNSS — Global Navigation Satellite Systems, Springer.
[9] NMEA 0183 协议说明（语句字段）.
[10] 3GPP / 蜂窝 A-GNSS 辅助数据概述.
[11] IMU 航位推算与 GNSS 紧组合入门文献.
[12] FCC/CE 对 GNSS 接收机无意辐射测试注意（模组认证语境）.
