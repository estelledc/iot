---
schema_version: '1.0'
id: antenna-impedance-matching-network
title: 天线阻抗匹配网络设计与Smith圆图
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - chip-antenna-vs-pcb-antenna
  - pcb-antenna-design-iot
tags:
  - 阻抗匹配
  - Smith圆图
  - S11
  - PI网络
  - VNA
  - 射频
  - 天线
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 天线阻抗匹配网络设计与Smith圆图

> **难度**：🔴 高级 | **领域**：射频匹配设计 | **阅读时间**：约 16 分钟

## 日常类比

粗管硬接细管会在接口湍流反射；加渐变接头水流才顺。射频里信号源常按 50 Ω 设计，天线可能是 20−j40 Ω 一类复数阻抗——不匹配则功率反射，辐射变少。匹配网络就是“渐变接头”，把天线阻抗变换到系统期望阻抗，逼近最大功率传输[1][2]。

## 摘要

共轭匹配使负载等于源阻抗共轭；反射系数 Γ 与失配损耗描述回损。Smith 圆图把串联/并联 L/C 变成等 r / 等 g 圆弧。IoT 常用 L 或 PI 网络；元件选高 Q 电感与 C0G 电容，并计入焊盘寄生。调谐以最终壳体 VNA 实测为准。文中元件值与 dB 为算例量级[1][3][4]。

## 1. 为什么匹配

最大功率传输：\(Z_L = Z_S^*\)。\(\Gamma=(Z_L-Z_0)/(Z_L+Z_0)\)，失配损耗 \(-10\log_{10}(1-|\Gamma|^2)\) dB[1]。

| \|Γ\|（约） | S11 叙事 | 传输功率比叙事 |
|-------------|----------|----------------|
| 0 | 理想 | 100% |
| 0.32 | 约 −10 dB | 约 90% |
| 0.5 | 约 −6 dB | 约 75% |

边际 BLE 链路上，零点几到 1 dB 级失配差可能影响能否连上——**需放进链路预算，而非孤立看 S11**[4][5]。

## 2. Smith 圆图操作

归一化 \(z=Z/Z_0\)。等 r 圆上串联感/容；等 g 圆上并联感/容。记忆：串联走等 r，并联走等 g[1][2]。

| 区域 | 特征 |
|------|------|
| 实轴 | 纯阻 |
| 上/下半平面 | 感/容 |
| 圆心 | \(Z=Z_0\) 匹配 |

VNA：SOL 校准到馈点；在最终外壳/电池状态下测 S11；低激励避免前端压缩[3][6]。

| 天线类型 | 2.4 GHz 阻抗叙事 |
|----------|------------------|
| 优化 PIFA | 常接近 50 Ω |
| IFA | 可调到近 50 Ω |
| 蛇形/部分芯片天线 | 常明显偏离，需匹配 |

## 3. 拓扑与元件

| 需求 | 倾向拓扑 |
|------|----------|
| 最少元件 | L 型（Q 由阻抗比锁定） |
| 谐波抑制 + 可调 Q | PI（IoT 前端常见） |
| PA 输出等 | T 型等视设计 |
| 双频 | 级联 L、宽带 PI 折中或开关分路 |

电感：关注工作频点 Q、SRF（宜明显高于工作频）、DCR。电容：射频匹配优先 NP0/C0G。0402 寄生通常小于 0603，但须仿真/实测纳入焊盘[2][7]。

带宽约 \(f_0/Q_{\mathrm{tot}}\)。BLE 需覆盖数十 MHz 信道跨度时，匹配网络不宜 Q 过高；天线自身高 Q 时更要压低网络 Q[5][8]。

## 4. 布局与调谐

紧邻馈点、短走线、并联地过孔紧贴、完整回流地。禁忌：匹配区远离天线、跨地缝、旁路高速线[6][7]。

流程：首板预留 0402 位（串 0 Ω、并开路）→ 测裸天线阻抗 → 算/仿匹配 → 焊接再测 → 每次改一颗。谐振偏低常减 L/C；深度不够查 Q 与损耗[3][4]。

## 5. 局限、挑战与可改进方向

### 1. 仿真完美、装电池后失配

**局限**：人手/外壳/电池是天线的一部分。
**改进**：只认最终态 VNA；产线抽测 S11 或传导功率[6][8]。

### 2. 忽略寄生把理想 L/C 当真

**局限**：SRF 附近感抗漂移，焊盘电容改变轨迹。
**改进**：选 SRF 裕量；版图寄生进 SimSmith/ADS；用实测反推[2][7]。

### 3. 单频匹配硬撑多频

**局限**：一组 L 难同时深匹配 GPS+BLE 等大频比。
**改进**：独立天线+开关、级联优化或接受折中带宽[5][9]。

### 4. 只追 S11 最深忽略效率

**局限**：有损匹配可“看起来很匹配”但辐射效率差。
**改进**：结合效率/总辐射功率与链路预算，不只看回损尖点[1][4]。

## 6. 实践要点

1. 先测最终态阻抗，再选 L/PI，避免抄参考设计元件值。
2. 匹配位永远可调；量产锁定前完成温漂与壳体角评估。
3. 工具链：SimSmith 快估 → 电路仿真 → VNA 收口。

## 参考文献

[1] D. M. Pozar, Microwave Engineering, Wiley.
[2] C. Bowick et al., RF Circuit Design, Newnes.
[3] Analog Devices, AN-742 Impedance Matching and the Smith Chart.
[4] Keysight/R&S VNA antenna impedance measurement application notes.
[5] Bluetooth Core Spec / LE PHY link budget related design guides.
[6] Antenna measurement best practices with fixtures and plastics (vendor app notes).
[7] Murata/Coilcraft RF inductor selection guides (Q, SRF).
[8] SimSmith documentation, https://simsmith.audio
[9] G. Gonzalez, Microwave Transistor Amplifiers (matching chapters).
[10] IEEE literature on dual-band matching network synthesis.
[11] PCB RF layout guidelines for matching networks (TI/ADI app notes).
