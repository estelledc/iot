---
schema_version: '1.0'
id: terahertz-communication-future-iot
title: 太赫兹通信在未来IoT中的潜力与挑战
layer: 2
content_type: survey
difficulty: advanced
reading_time: 18
prerequisites:
  - thz-communication-iot
tags:
  - 太赫兹
  - 6G
  - ISAC
  - 纳米物联网
  - 毫米波
  - RIS
  - 波束管理
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 太赫兹通信在未来IoT中的潜力与挑战

> **难度**：🔴 高级 | **领域**：前沿通信 | **阅读时间**：约 18 分钟

## 日常类比

浇花园：普通水管像蜂窝低频，消防栓像毫米波，瀑布像太赫兹（Terahertz, THz）——水量（带宽）极大，但水雾在空气里很快散掉（传播极短、分子吸收重）。物联网（IoT）要的往往不是处处 Tbps，而是在极短距、极密部署或纳米尺度上，把“最后一厘米”做厚[1][2]。

## 摘要

定位 0.1–10 THz 的带宽潜力、大气窗、器件与集成感知通信（Integrated Sensing and Communication, ISAC），并对照 5G 毫米波。峰值速率、覆盖米数与商用年份为研究/路线图**量级**，标准化与器件功率仍是主瓶颈[2][5]。

## 1. 频谱与带宽量级

| 频段 | 连续带宽量级 | 峰值速率叙事 |
|------|--------------|--------------|
| 5G Sub-6 | 百 MHz 级 | Gbps 级 |
| 5G mmWave ~28 GHz | 数百 MHz–约 1 GHz | 约 10 Gbps 级 |
| 低 THz 0.1–0.3 THz | 十余–数十 GHz | 约 100 Gbps 叙事 |
| 更高 THz | 更宽但吸收更狠 | 实验室/极短距 |

“THz 间隙”指电子学上变频与光子学下变频长期都难高效覆盖该段；CMOS/InP/量子级联激光器（Quantum Cascade Laser, QCL）等在推进，但输出功率与室温效率仍受限[1][3]。

## 2. 传播：FSPL + 水汽

同距下频率升高使自由空间路径损耗（FSPL）显著增加；另加水汽旋转吸收线。室内数米内吸收有时不是主矛盾，室外百米级则常是硬限制。工程上优先大气透过率较高的窗口（如约 0.1–0.3 THz 叙事）[2][5]。

| 对比（示意） | 5G mmWave ~28 GHz | THz ~0.3 THz |
|--------------|-------------------|--------------|
| 带宽 | 较窄 | 极宽 |
| 覆盖 | 数十–数百米叙事 | 常 1–10 m 级 |
| 穿透 | 轻薄材料尚可 | 人体/家具易阻断 |
| 波束 | 窄 | 极窄，对准苛刻 |
| 成熟度 | 已商用 | 研究/原型为主 |
| 标准 | 3GPP 已有 FR2 | IEEE 802.15.3d 等起步，6G 研究中 |

## 3. 器件与天线

波长毫米级：厘米级孔径可放大规模阵列，易得高增益“铅笔波束”，也迫使波束管理与遮挡恢复成为系统问题。信号源路线含电子倍频、光电导差频、QCL、共振隧穿二极管（Resonant Tunneling Diode, RTD）等，功率常在 μW–mW 量级（视频率）[3][4]。

## 4. IoT 相关方向

**纳米物联网（Internet of Nano-Things）**：天线尺寸与 THz 波长匹配；脉冲开关键（如 TS-OOK 类）降占空比。距离多为厘米级叙事[1]。

**ISAC**：短波长利于高分辨感知；同一波形可兼通信与材料/手势/定位——仓储、安检、产线是常见故事线，落地依赖校准与法规[2][4]。

**智能超表面（Reconfigurable Intelligent Surface, RIS）**：用反射路径缓解遮挡；THz 单元更密、相位精度要求更高，覆盖扩展倍数为仿真/试验量级[4]。

## 5. 局限、挑战与可改进方向

### 1. 链路预算常为负 SNR

**局限**：宽带宽噪声底高，加上 FSPL，短距也可能 SNR 不足。
**改进**：更大阵列增益、降带宽/降阶调制、缩小区半径[2][3]。

### 2. 遮挡与波束失配

**局限**：人体一挡即断；移动需亚度级追踪。
**改进**：多接入点（Access Point, AP）密布 + 快速切换；低频辅助粗对准；RIS 旁路[4]。

### 3. 功放效率与 IoT 能耗

**局限**：THz 功放效率常远低于 Sub-6/部分 mmWave。
**改进**：优先固定无线/回程等高价值链路；终端侧用突发短包[3][5]。

### 4. 把 THz 写成“取代 5G”

**局限**：覆盖与穿透决定其是互补层而非宏覆盖替代。
**改进**：分层：mmWave/Sub-6 管中距，THz 管极短距超高速与感知[2]。

## 6. 部署叙事（示意）

工厂天花板密布 Sub-THz AP、光纤回程、多层波束管理——适合论证密度与带宽，**不作为 2026 年可采购 BOM**。路线图常见：先 Sub-THz 固定链路，再室内热点，纳米网络更靠后[5][8]。

## 参考文献

[1] I. F. Akyildiz, J. M. Jornet, C. Han, Terahertz band: next frontier for wireless communications, Physical Communication, 2014.
[2] T. S. Rappaport et al., Wireless communications and applications above 100 GHz, IEEE Access, 2019.
[3] Z. Chen et al., A survey on terahertz communications, China Communications, 2019.
[4] H. Sarieddeen et al., Signal processing techniques for terahertz communications, Proc. IEEE, 2020.
[5] H. Elayan et al., Terahertz band: the last piece of RF spectrum puzzle, IEEE OJ-COMS, 2020.
[6] IEEE Std 802.15.3d, 100 Gbps wireless switched point-to-point physical layer (approx. 252–325 GHz).
[7] ITU / WRC agenda items on IMT identification above 100 GHz (treat as regulatory process).
[8] 3GPP study items on sub-THz / 6G frequency ranges (release-dependent).
[9] QCL and electronic THz source review literature (power/temperature limits).
[10] RIS-assisted THz coverage studies (simulation-heavy; validate cautiously).
[11] Nano-network TS-OOK and pulse-based THz MAC papers (Jornet/Akyildiz line).
