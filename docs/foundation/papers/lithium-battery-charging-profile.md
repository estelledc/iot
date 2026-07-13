---
schema_version: '1.0'
id: lithium-battery-charging-profile
title: 锂电池CC-CV充电曲线与充电IC设计
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - battery-management-bms
  - battery-fuel-gauge-coulomb-counter
tags:
  - 锂电池
  - CC-CV
  - 充电IC
  - NTC
  - 电源路径
  - IoT电池
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 锂电池CC-CV充电曲线与充电IC设计

> **难度**：🟡 中级 | **领域**：电池与充电 | **关键词**：CC-CV, 充电IC, NTC | **阅读时间**：约 16 分钟

## 日常类比

给水杯接水：先大开水龙头快速涨水位（恒流 Constant Current, CC），快满时拧小避免溢出（恒压 Constant Voltage, CV），滴水到阈值就关阀。锂离子/锂聚合物电芯也按 CC-CV 曲线充；电压、温度越界就要保护，不能“一直灌”[3][4]。

## 摘要

讲解单节锂电 CC-CV 阶段、终止条件、充电 IC 与电源路径、NTC 与布局。标称 4.2 V 等参数因化学体系而异，以电芯规格书为准[1][2]。

## 1. CC-CV 曲线

| 阶段 | 行为 |
|------|------|
| 预充 | 过放电电芯小电流激活 |
| CC | 恒流至接近满充电压 |
| CV | 电压钳位，电流逐渐下降 |
| 终止 | 电流降至阈值或超时 |

| 保护 | 意义 |
|------|------|
| 过压/欠压 | 防析锂与过放损伤 |
| 过流/短路 | 安全 |
| 温度窗 | NTC 监测，超温停充 |

快充提高 CC 电流会牺牲循环寿命与温升，IoT 更常优先寿命与安全[4]。

## 2. IC、路径与太阳能

| 功能 | 说明 |
|------|------|
| 独立充电 IC | 少 MCU 干预（如 MCP738xx 类） |
| 带电源路径 | 无电池也能 USB 运行系统 |
| Ship mode | 仓储极低漏电 |
| 太阳能 | MPPT/输入弱源算法，忌简单并联 |

布局：大电流环路小、检流与感温靠近电芯；输入TVS 与 USB 规范共存[1][9]。

## 3. 局限、挑战与可改进方向

### 1. 用手机快充套 IoT

**局限**：温升与寿命不可接受。
**改进**：按电芯 C 率与外壳热阻选型[3]。

### 2. NTC 位置不准

**局限**：测到的是板温不是电芯温。
**改进**：NTC 贴电芯；热脂/卡扣固定[1]。

### 3. 输入源过弱

**局限**：太阳能/能量采集下充电状态机抖动。
**改进**：选支持弱输入的 IC；加大输入储能[6]。

### 4. 忽略老化与内阻

**局限**：末期 CV 时间变长、发热增加。
**改进**：库仑计/阻抗追踪；调整终止策略[4][7]。

## 总结

CC-CV 是锂电充电底线；选带温度与安全定时的充电 IC，电源路径服务产品形态。电压、电流、温度三道门都要关严。

## 参考文献

[1] Texas Instruments, BQ25180 等充电管理数据手册.
[2] Microchip, MCP73831/2 数据手册.
[3] TI, 锂离子充电与便携电源应用笔记.
[4] S. S. Zhang, 充电协议对循环寿命影响等期刊论文.
[5] USB-IF, Battery Charging Specification 相关修订.
[6] 太阳能充电与 MPPT 在 IoT 节点中的应用笔记.
[7] 电池电量计与内阻估计文献.
[8] UN38.3 / 运输与安全测试概述.
[9] 充电功率级 PCB 布局指南（TI/ADI）.
[10] JEITA 温度充电曲线行业实践说明.
[11] LiFePO4 与三元正极电压平台差异摘要.
[12] BMS 与单节充电 IC 的职责边界说明.
