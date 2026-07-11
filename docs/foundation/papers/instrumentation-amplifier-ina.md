---
schema_version: '1.0'
id: instrumentation-amplifier-ina
title: 仪表放大器INA在微弱信号测量中的应用
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - bridge-circuit-sensor-excitation
  - chopper-stabilized-amplifier
tags:
  - 仪表放大器
  - INA
  - CMRR
  - 电桥测量
  - 微弱信号
  - 差分放大
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 仪表放大器INA在微弱信号测量中的应用

> **难度**：🟡 中级 | **领域**：模拟前端 | **关键词**：INA, CMRR, 电桥 | **阅读时间**：约 16 分钟

## 日常类比

嘈杂宴会里听清对面低语，要靠“两耳之差”而不是把喇叭开到最大——仪表放大器（Instrumentation Amplifier, INA）放大差分、压制共模。称重电桥、心电与分流器微伏～毫伏信号，离开高共模抑制比（Common-Mode Rejection Ratio, CMRR）的 INA 很难干净进 ADC[2][4]。

## 摘要

对比普通运放差分接法与三运放 INA、增益电阻设定、CMRR/噪声与典型器件选型。CMRR 随频率下降，手册直流指标不可直接当交流保证[1][4]。

## 1. 为何不是普通运放

| 方案 | 输入阻抗 | 增益设定 | CMRR 可预期性 |
|------|----------|----------|----------------|
| 分立差分对 | 难对称 | 多电阻匹配 | 差 |
| 三运放 INA | 高 | 常单电阻 Rg | 片内匹配好 |
| 专用 INA IC | 高 | 固定或 Rg | 有规格保证 |

经典结构：两级缓冲差分 + 差分转单端；\(G = 1 + 2R/R_g\)（具体常数见手册）[1]。

## 2. 关键指标

| 指标 | 意义 | IoT 注意 |
|------|------|----------|
| CMRR | 抑制线路共模与电源干扰 | 看目标频率处数值 |
| 输入偏置/失调 | 电桥零点 | 斩波/自动归零类型更优 |
| 噪声密度 | 分辨率底噪 | 与带宽、源电阻匹配 |
| 供电与轨到轨 | 电池系统 | 选微功耗 INA |

| 器件方向 | 场景 |
|----------|------|
| INA128 类 | 通用精密 |
| INA333 等零漂 | 慢变电桥/温度 |
| 电流检测 INA | 分流器高边/低边（注意共模范围） |

## 3. 布局与应用

开尔文连传感器；Rg 靠近芯片；模拟地与回流干净；增益后加抗混叠再进 ADC。电桥激励可用恒压/恒流，注意激励噪声经 CMRR 泄漏[4][9]。

## 4. 局限、挑战与可改进方向

### 1. 高频 CMRR 恶化

**局限**：射频整流与工频谐波处抑制不足。
**改进**：输入 RC/共模滤波；屏蔽与电缆双绞[2]。

### 2. 增益带宽折中

**局限**：高增益下带宽与稳定裕度下降。
**改进**：增益分配（INA + 后级）；按信号频谱选型[1]。

### 3. 源阻抗不平衡

**局限**：破坏 CMRR，电桥引线不对称尤甚。
**改进**：等长布线、缓冲、护环[4]。

### 4. 功耗

**局限**：精密双电源 INA 不适合纽扣电池常开。
**改进**：微功耗零漂 INA + 占空比激励[5]。

## 总结

INA 是电桥与微弱差分信号的标准前端：先保证 CMRR 与布局，再追增益位数。选型看共模范围、零漂与噪声，而不是只看最大增益。

## 参考文献

[1] Texas Instruments, INA128/INA129 数据手册.
[2] Analog Devices, Instrumentation Amplifier Applications Guide.
[3] W. Jung, *Op Amp Applications Handbook*（INA 章节）.
[4] C. Kitchin, L. Counts, *A Designer's Guide to Instrumentation Amplifiers*, ADI.
[5] Texas Instruments, INA333 数据手册.
[6] 电桥传感器激励与读出应用笔记.
[7] 斩波稳零与自动归零放大器技术文献.
[8] ADC 驱动与抗混叠和 INA 接口笔记.
[9] PCB 护环与精密模拟布局指南.
[10] 分流器电流检测 INA 选型指南（TI/ADI）.
[11] 心电/生物电位前端特殊要求综述（安全隔离另论）.
[12] 噪声分析（电压/电流噪声与源电阻匹配）教材章节.
