---
schema_version: '1.0'
id: uwb-module-dw1000-ranging
title: 超宽带UWB模组DW1000测距原理与硬件
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - sensor-network-time-sync-hardware
  - pcb-antenna-design-iot
tags:
  - UWB
  - DW1000
  - 测距
  - TWR
  - 室内定位
  - 超宽带
  - IoT
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 超宽带UWB模组DW1000测距原理与硬件

> **难度**：🟡 中级 | **领域**：室内定位 | **关键词**：UWB, DW1000, TWR, TDoA | **阅读时间**：约 16 分钟

## 日常类比

用秒表测枪声与回声差估距离；超宽带（Ultra-Wideband, UWB）用极窄脉冲获得精细时间戳，实现分米级测距与定位（视部署）[1][2]。

## 摘要

以 Decawave/Qorvo DW1000 类芯片为例，说明双边双向测距（Two-Way Ranging, TWR）、天线与频道法规、以及与蓝牙定位对比。精度受 NLOS 与天线延迟校准影响[2][3]。

## 1. 为何准

大带宽 → 细时间分辨 → 飞行时间估计更准。TWR 交换消息消除部分时钟偏差；TDoA 需锚节点时间同步[1]。

| 方法 | 同步需求 | 特点 |
|------|----------|------|
| SS-TWR | 低 | 简单，误差项更多 |
| DS-TWR | 低 | 更准，交互多 |
| TDoA | 锚节点高同步 | 标签省电 |

## 2. 硬件要点

| 项 | 注意 |
|----|------|
| 天线 | 匹配与方向图；延迟校准 |
| 晶振 | 频偏影响 |
| 电源 | 发射尖峰去耦 |
| 频道/功率 | 地区法规 |
| 屏蔽 | 减少数字噪声 |

| 对比 | UWB | BLE RSSI |
|------|-----|----------|
| 精度倾向 | 分米级可能 | 米级常见 |
| 功耗 | 脉冲但协议开销 | 可极低 |
| 成本 | 较高 | 低 |
| 多径 | 更鲁棒倾向 | 脆弱 |

## 3. 局限、挑战与可改进方向

### 1. 非视距 NLOS

**局限**：穿墙偏大或跳点。
**改进**：多锚融合、NLOS 识别、地图约束[3]。

### 2. 天线延迟未校准

**局限**：固定偏差。
**改进**：产线校准写入 OTP/Flash[2]。

### 3. 同址干扰与信道拥塞

**局限**：多标签冲突。
**改进**：时隙调度、频道规划[1]。

### 4. 芯片世代更替

**局限**：DW1000 后继器件与生态变化。
**改进**：按现行 Qorvo/竞品选型，抽象测距 API[4]。

## 总结

UWB 测距强在时间分辨率，弱在 NLOS 与系统工程。硬件校准与锚节点几何，往往比换算法更能提升体验。

## 参考文献

[1] Decawave/Qorvo DW1000 User Manual.
[2] IEEE 802.15.4z / UWB 测距相关概述.
[3] UWB 室内定位 NLOS 缓解综述.
[4] 新一代 UWB SoC 产品白皮书（对照）.
[5] TWR 误差分析文献.
[6] 天线延迟校准应用笔记.
[7] 各国 UWB 法规功率限制概述.
[8] BLE 与 UWB 融合定位案例.
[9] TDoA 锚节点同步方案.
[10] PCB 天线与净空设计.
[11] 多标签 MAC 调度策略.
[12] 工业仓储定位部署指南.
