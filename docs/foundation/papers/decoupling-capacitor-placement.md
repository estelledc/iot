---
schema_version: '1.0'
id: decoupling-capacitor-placement
title: 去耦电容选型与PCB放置策略
layer: 1
content_type: technical_analysis
difficulty: beginner
reading_time: 14
prerequisites:
  - power-integrity-pdn-design
  - signal-integrity-crosstalk
tags:
  - 去耦电容
  - PDN
  - MLCC
  - ESL
  - PCB布局
  - 电源完整性
  - DC偏压
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 去耦电容选型与PCB放置策略

> **难度**：🟢 初级 | **领域**：PCB电源完整性 | **阅读时间**：约 14 分钟

## 日常类比

大楼某一层突然多开水龙头，主管道来不及补压。楼层小水箱可就地顶住高峰。IC 开关电流尖峰像突然开阀；去耦电容是焊在电源脚旁的小水箱，压住 PDN（Power Distribution Network，电源分配网络）上的电压跌落[1][2]。

## 摘要

目标是在关心频段把 PDN 阻抗压到目标以下。实际电容有 ESR/ESL，存在 SRF（Self-Resonant Frequency）；**小封装、短回路、过孔贴焊盘**决定高频是否有效。容值与 SRF 表为量级示意，**以厂商阻抗曲线与板级实测为准**[1][3]。

## 1. 为何去耦

数字脚翻转 di/dt 大时，走线/过孔电感上的压降表现为轨上纹波与地弹。目标阻抗示意：`Z_target ≈ V_ripple_allow / I_transient`[2][4]。

## 2. 频率角色与 MLCC

| 级别 | 容值量级 | 作用频段倾向 | 放置 |
|------|----------|--------------|------|
| Bulk | 十余～百 μF | 较低频 | 电源入口 |
| Mid | 1～10 μF | 中频 | IC 附近 |
| Local | ~100 nF | 较高频 | 紧贴电源脚 |
| 可选高频 | 1～10 nF | 更高频 | 紧贴电源脚 |

| 封装 | ESL 倾向 | 同容值 SRF |
|------|----------|------------|
| 更小（如 0402） | 更低 | 更高 |
| 更大（如 0805） | 更高 | 更低 |

MLCC 选 X7R/X5R 等稳定介质；Y5V 温漂与压漂大，户外 IoT 慎用。**DC bias**：工作电压接近额定时有效容值可大幅下降，工程上常提高电压额定档[3][5]。

## 3. 放置与并联

规则：靠近 VDD/GND 脚、最小化电流回路面积、地过孔紧贴焊盘（via-in-pad 更短但工艺贵）。多容值并联拓宽频段，但大/小电容 SRF 之间可能出现反谐振峰；容值比过大时更明显，可用相近容值、平面电容或实测压峰[1][6]。

| 叠层要点 | 作用 |
|----------|------|
| 紧邻电源/地平面对 | 低 ESL 分布电容，利极高频 |
| 信号层旁完整地 | 缩短回流 |

## 4. 案例线索

MCU：每 VDD 一颗本地 100 nF 量级，勿多脚共用一颗；模拟 VDDA 单独就近去耦。RF SoC：内部 LDO 脚常要求 C0G/NP0，X5R 压漂可能导致振荡——跟参考设计[7][8]。

## 5. 局限、挑战与可改进方向

### 1. “电源网上有电容就行”

**局限**：远离 IC 的电容被走线电感隔离，高频失效。
**改进**：按脚就近；评审回路面积与过孔距离[2][7]。

### 2. 忽视 DC bias 与介质

**局限**：标称 10 μF 在偏压下只剩几分之一。
**改进**：查厂商 bias 曲线；提高额定电压或并联[3][5]。

### 3. 只堆容值不看反谐振

**局限**：某频段阻抗尖峰反而变差。
**改进**：VNA/仿真看 PDN；调整容值组合[1][4]。

### 4. 多 VDD 共用一颗电容

**局限**：脚间噪声耦合、各脚回路电感不均。
**改进**：一脚一本地电容，bulk 可共享[7]。

## 6. 实践要点

1. 先算/估 Z_target，再选容值组合。
2. 布局检查清单：距离、过孔、VDDA/RF 特殊脚。
3. 高速或射频板用阻抗曲线验收，不靠“经验贴满”。

## 参考文献

[1] I. Novak, J. Miller, Frequency-Domain Characterization of Power Distribution Networks.
[2] E. Bogatin, Signal and Power Integrity — Simplified.
[3] Murata / MLCC vendor capacitor selection & impedance data.
[4] Texas Instruments, PDN design guidance for high-speed devices.
[5] MLCC DC bias derating application guides (Kemet/Murata class).
[6] Anti-resonance in parallel decoupling networks — SI/PI notes.
[7] STMicroelectronics, PCB design guidelines for STM32 (e.g. AN4325 class).
[8] Nordic / RF SoC reference designs on DEC pin capacitor dielectric.
[9] IPC PCB via inductance and decoupling placement notes.
[10] Keysight/Ansys PDN simulation tool documentation (methodology).
[11] Target impedance calculation application notes.
