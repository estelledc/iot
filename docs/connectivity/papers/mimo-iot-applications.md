---
schema_version: '1.0'
id: mimo-iot-applications
title: MIMO 技术在 IoT 中的应用
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites: UNKNOWN
tags:
  - MIMO
  - Massive-MIMO
  - 空间分集
  - 空间复用
  - MU-MIMO
  - 波束赋形
  - RedCap
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# MIMO 技术在 IoT 中的应用

> **难度**：🟡 中级 | **领域**：无线通信 | **阅读时间**：约 18 分钟

## 日常类比

食堂里单嘴对单耳要喊（SISO）；多嘴多耳可并行说不同话（空间复用），或同一句话多路传送更稳（分集）。基站侧 Massive MIMO 像多只定向喇叭：能量对准桌子，邻桌干扰更小——IoT 常受益于**网络侧多天线**，而非手表里塞满天线[1][2]。

## 摘要

区分分集与复用、说明 Massive MIMO 对连接数/覆盖/能效的意义、终端紧凑天线与 MU-MIMO/grant-free 要点。电池寿命随发射功率下降的倍数叙事高度依赖业务占空比，**不可直接当续航承诺**[5][9]。

## 1. 分集与复用

| 方案 | 思路 | IoT 含义 |
|------|------|----------|
| 接收 MRC 等 | 多天线合并 | 终端难放多天线时受限 |
| STBC / Alamouti | 发射分集 | 可放在基站，终端单天线仍受益 |
| 空间复用 | 并行流 | 受 \(\min(N_{tx},N_{rx})\) 限制；单天线终端复用度有限 |

对单天线传感器，64×1 的价值主要在阵列/波束 SNR，而非多层复用[1][3]。

## 2. Massive MIMO 与 IoT 价值

基站 64–256 天线量级在 5G 中已常见。对 IoT：同一时频空分多用户、上行合并改善链路、可能降低终端所需发射功率。部署规模与“每站同时用户数”随运营商配置变化，引用市场站数时需标注来源与时间[1][6][9]。

CSI 与导频：正交导频受相干时间/带宽约束；导频污染使天线数→∞ 时 SINR 仍可能受限。静止 IoT 有利于拉长相干，但突发短包使估计时效与开销更棘手[2][4][7]。

## 3. 终端天线与频段

Sub-GHz 半波长可达分米级，小设备难做空间分集；可用极化/模式/寄生单元等折中。毫米波半波长毫米级，手表级多天线更可行，但覆盖与阻塞另论[8]。

| 频段直觉 | 小设备多天线难度 |
|----------|------------------|
| ~900 MHz | 高 |
| 2.4 / 5 GHz | 中–高 |
| 28 / 60 GHz | 相对更易摆阵 |

## 4. MU-MIMO、调度与蜂窝 IoT

用户数 ≫ 天线数时需选空间可分用户子集；IoT 流量极度异构（字节级传感 vs 图像）使传统手机调度器不一定合适。Grant-free / NOMA 等减少调度往返，依赖接收机分离能力与碰撞模型，标准化与产品支持需单独核实[10][11]。

RedCap/NB-IoT 等终端 MIMO 层数通常远低于 eMBB；设计时应读清 UE 能力，避免按手机 MIMO 假设选型[6]。

## 5. 局限、挑战与可改进方向

### 1. 终端侧硬上 MIMO

**局限**：尺寸、隔离度与成本不达标，增益名存实亡。
**改进**：优先网络侧阵列；终端用极化等单孔径技巧。

### 2. 续航线性外推

**局限**：把阵列增益 dB 直接乘成“电池寿命 ×N”。
**改进**：按实际 TX 占空比与休眠电流建模；样机测平均电流。

### 3. 导频污染与反馈饿死上行

**局限**：CSI 开销挤占小包上行。
**改进**：SRS/互易、粗码本、减少反馈；静止设备降低估计频率。

### 4. 把 eMBB 指标当 IoT KPI

**局限**：追求层数与峰值 Mbps，忽视连接密度与边缘成功率。
**改进**：KPI 改为连接失败率、边缘 MCL、每焦耳报文数。

## 6. 实践要点

1. 单天线 IoT：把 MIMO 预算留给基站。
2. 选型对照 3GPP UE 能力（RedCap/NB-IoT 层数）。
3. 实验室 MIMO 容量仿真只作直觉，现场以边缘链路为准。

## 参考文献

[1] Larsson, E. G. et al., "Massive MIMO for next generation wireless systems," IEEE Commun. Mag., 2014.
[2] Marzetta, T. L., IEEE TWC, 2010 (unlimited BS antennas).
[3] Lu, L. et al., "An overview of massive MIMO," IEEE JSAC, 2014.
[4] Hoydis, J. et al., "How many antennas do we need?" IEEE JSAC, 2013.
[5] Ngo, H. Q. et al., energy and spectral efficiency of very large MU-MIMO, IEEE TCOM, 2013.
[6] 3GPP TS 38.214, NR physical layer procedures for data.
[7] Björnson, E. et al., Massive MIMO networks foundations (FnT Signal Processing).
[8] Compact / mmWave IoT antenna design literature.
[9] Ericsson technology reviews on 5G mMIMO energy efficiency (treat KPIs as vendor claims).
[10] Ding, Z. et al., MIMO-NOMA related works, IEEE TWC.
[11] 3GPP RedCap / NB-IoT UE capability overviews.
