---
schema_version: '1.0'
id: low-noise-pcb-layout-analog
title: 低噪声模拟信号PCB布局设计规则
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - pcb-ground-plane-partitioning
  - decoupling-capacitor-placement
tags:
  - 低噪声
  - 模拟PCB
  - 地平面
  - 屏蔽
  - ADC
  - 串扰
  - 布局
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 低噪声模拟信号PCB布局设计规则

> **难度**：🔴 高级 | **领域**：模拟 PCB | **关键词**：分区、星形地、屏蔽、去耦 | **阅读时间**：约 16 分钟

## 日常类比

嘈杂工厂里打电话：数字开关噪声像机器轰鸣，微弱模拟信号像对方轻声说话。布局分区、完整地平面与滤波，就是隔音房和降噪耳机——16 位 ADC（Analog-to-Digital Converter）的 1 LSB 可能只有亚毫伏甚至更低量级，几毫伏耦合就能“听不清”[1][2]。

## 摘要

归纳噪声源、模拟/数字分区、回流路径、去耦与屏蔽要点。具体噪声幅度与分辨率关系**随满量程与带宽变化，以计算与实测为准**[1][3]。

## 1. 噪声从哪来

| 类型 | 来源倾向 | 频域特征 |
|------|----------|----------|
| 热噪声 | 电阻等 | 宽带 |
| 开关噪声 | 数字边沿 di/dt | MHz–GHz |
| 电源纹波 | 开关电源 | 开关频及谐波 |
| EMI | 线缆/空间耦合 | 视环境 |

高分辨率前端优先压传导与近场耦合，而不是只堆软件滤波[2]。

## 2. 布局规则（可执行）

| 规则 | 做法 |
|------|------|
| 分区 | 模拟前端、ADC、数字、电源分块；敏感线最短 |
| 回流 | 高速数字下方完整地；避免跨缝分割地 |
| AGND/DGND | 单点或规定桥接点汇合，禁止多处随意短接成环 |
| 去耦 | 电源引脚旁放置合适容值；大电容+小电容搭配 |
| 差分对 | 对称、等长、远离开关节点 |
| 屏蔽 | 必要时装屏蔽罩或地护环；开孔注意泄漏 |

| 实践 | 说明 |
|------|------|
| 晶振/时钟 | 远离模拟输入 |
| 开关电感 | 远离高阻模拟节点 |
| 采样保持输入 | 防过冲与串扰，注意驱动能力 |

更多地平面策略见 `pcb-ground-plane-partitioning`[4]。

## 3. 局限、挑战与可改进方向

### 1. 过度分割地平面

**局限**：为“隔离”乱切开，回流绕路，辐射与串扰更差。
**改进**：优先完整地 + 分区布线；分割需有明确回流桥。

### 2. 只靠滤波电容

**局限**：布局差时电容无法拯救环路天线。
**改进**：先缩环路面积，再选容值与铁氧体。

### 3. 忽略机械与线缆

**局限**：板内很好，传感器线缆引入工频与射频。
**改进**：屏蔽线、正确单端接地策略、共模扼流。

### 4. 仿真缺失

**局限**：凭经验量产翻车。
**改进**：关键网络做 PI/SI 粗仿真；样机扫频谱与时域噪声。

## 4. 实践要点

1. 先画电流回流路径，再画信号线。
2. ADC 参考与模拟供电独立滤波。
3. 去耦细节对照 `decoupling-capacitor-placement`。

## 参考文献

[1] Henry Ott, Electromagnetic Compatibility Engineering（布局与接地章节）.
[2] ADI/TI, Analog layout and grounding application notes.
[3] ADC noise, SNR and layout guides from major vendors.
[4] PCB ground plane partitioning best practices.
[5] Decoupling capacitor selection and placement notes.
[6] IPC PCB design guidelines related to analog sections.
[7] Shielding effectiveness basics for small enclosures.
[8] Switch-mode power supply EMI layout guidelines.
[9] Differential pair routing for precision analog.
[10] IEC EMC testing overview for IoT hardware.
[11] Op-amp and PGA PCB layout techniques.
