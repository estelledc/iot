---
schema_version: '1.0'
id: full-duplex-radio-iot
title: 全双工无线电在IoT中的自干扰消除
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - cognitive-radio-spectrum
  - fading-multipath-iot-channel
tags:
- 全双工
- 自干扰消除
- SIC
- 中继
- RFID
- IBFD
- 频谱效率
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 全双工无线电在IoT中的自干扰消除

> **难度**：🔴 高级 | **领域**：无线通信 | **阅读时间**：约 22 分钟

## 日常类比

全双工像边说边听电话：自己的声音比对方大许多个数量级，大脑必须「滤掉自己」。同频同时收发（In-Band Full-Duplex, IBFD）要把本机发射从接收链路抹掉——自干扰消除（Self-Interference Cancellation, SIC）。半双工像对讲机轮流说；频分双工（FDD）像两条车道各走各的。

## 摘要

说明 IBFD 相对 TDD/FDD 的频谱效率动机，拆解天线域/模拟域/数字域三级 SIC，并讨论 IoT 中继、RFID 与基站侧全双工的适用边界。消除量与延迟数字来自公开实验与综述量级，跨硬件须复测[1][2][3]。

## 1 双工方式与自干扰量级

| 方式 | 时频关系 | 频谱代价 |
|------|----------|----------|
| 半双工 / TDD | 同频交替收发 | 时间对半分 |
| FDD | 不同频率同时 | 需成对频谱 |
| IBFD | 同频同时 | 理论吞吐可近翻倍 |

发射与远端接收功率差常达约 100 dB 量级（例如 +20 dBm 对 −90 dBm），需把自干扰压到噪声底附近才能解调[1][2]。

## 2 三级 SIC 架构

单独一级通常不够：仅数字域会在 ADC 前饱和；仅模拟域受元器件精度限制；仅天线域难消反射路径。典型级联目标总消除约 100–130 dB 量级[1][3]：

| 域 | 手段 | 公开报告消除量级 |
|----|------|------------------|
| 天线域 | 间距、极化、方向性、对称相消 | 约 30–50 dB |
| 模拟域 | 抽头延迟/反相自适应抵消 | 约 30–50 dB（窄带更高） |
| 数字域 | 线性 + 非线性（PA）建模 | 约 20–40 dB |

窄带（如百 kHz 级 IoT）多径色散弱，模拟/数字 SIC 相对宽带 Wi-Fi 更容易做深[3]。

## 3 天线域与模拟域

天线域：空间隔离、正交极化（公开材料常报约 20–30 dB）、方向图后瓣衰减；对称双 TX 反相可在 RX 处相消。模拟域从 TX 抽头，经多抽头自适应滤波器在 RX 路径相减；带宽越宽，多径跟踪越难。难点含 PA 非线性、温度漂移、本振相位噪声（部分分量难消）[2][3]。

## 4 数字域与非线性

数字 SIC 用已知 TX 样本估计残余信道并减去。PA 的三阶/五阶项若不建模，消除深度常停在约 20–25 dB；含非线性与 IQ 失衡补偿可更深，但算力上升[2]：

| 建模 | 消除量级（公开） | 复杂度 |
|------|------------------|--------|
| 线性 | 约 20–25 dB | 低 |
| 三阶非线性 | 约 30–35 dB | 中 |
| 五阶 + IQ | 约 35–42 dB | 高 |

示意（非生产代码）：

```python
# 线性+三阶项最小二乘数字 SIC（示意）
X = np.concatenate([toeplitz_tx(tx, L), toeplitz_tx(tx * np.abs(tx)**2, L)], 1)
h = np.linalg.lstsq(X, rx, rcond=None)[0]
clean = rx - X @ h
```

## 5 IoT 价值与角色边界

| 角色 | 适用性 | 原因 |
|------|--------|------|
| 微型传感器 | 差 | 尺寸难隔离、数字 SIC 耗电、模拟电路贵 |
| 网关/中继（市电） | 较好 | 可放天线间距与算力 |
| 蜂窝基站 | 研究/演进中 | 空间与供电充裕；3GPP 有全双工研究[5] |
| RFID 读写器 | 已成熟应用 | 连续波供电同时收反向散射 |

半双工中继每跳「收再发」占两时隙；全双工中继可同频同时转发，多跳延迟在实验设定下可明显下降（具体毫秒数依赖 MAC 与跳数，勿照搬）[1][4]。RFID 中环形器 + 泄漏消除 + 数字处理的级联 SIC 与读取距离正相关，是 IoT 侧最落地的 SIC 场景之一。

## 6 成本与功耗（量级）

公开与工程估算常给出：额外天线/RF、模拟多抽头、更大 DSP/FPGA 使中继节点 BOM 与功耗明显高于半双工；对壁挂市电可接受，对电池 MCU 不现实。具体元与瓦数随方案变化，部署前应做本机 BOM/热设计，勿用单一案例数字做预算[3]。

## 7 产业与 5G

斯坦福等早期演示推动了实用 IBFD 研究；商用 SIC 方案与基站侧研究并行[2][5]。即使终端保持半双工，网络侧更灵活的上下行也可缩短调度等待——IoT 间接受益路径。

## 8 局限、挑战与可改进方向

### 1. 终端侧不可行

**局限**：尺寸、功耗、成本使传感器级 IBFD 不现实。
**改进**：SIC 只放在中继/网关/基站；终端维持半双工。

### 2. 动态反射破坏消除余量

**局限**：人员/金属移动改变自干扰信道，固定抽头失效。
**改进**：自适应多抽头 + 周期性重估；工业场景控制中继安装环境。

### 3. 非线性与相位噪声底

**局限**：高阶失真与本振噪声限制数字消除上限。
**改进**：更好 PA 线性化、本振共享架构、按带宽选择模型阶数。

### 4. 「频谱翻倍」被高估

**局限**：协议开销、残余干扰、半双工邻站共存使实际增益常低于 2×。
**改进**：用系统级吞吐与 P99 延迟评测，而非仅物理层消除 dB。

## 参考文献

[1] A. Sabharwal et al., "In-Band Full-Duplex Wireless: Challenges and Opportunities," IEEE JSAC, 2014.
[2] D. Bharadia, E. McMilin, S. Katti, "Full Duplex Radios," ACM SIGCOMM, 2013.
[3] K. E. Kolodziej et al., "In-Band Full-Duplex Technology: Techniques and Systems Survey," IEEE Trans. MTT, 2019.
[4] I. P. Roberts et al., "Millimeter-Wave Full Duplex Radios," IEEE Commun. Mag., 2020.
[5] 3GPP, "TR 38.858: Study on Full Duplex for NR," Release 18.
[6] M. Duarte, C. Dick, A. Sabharwal, "Experiment-Driven Characterization of Full-Duplex Wireless Systems," IEEE Trans. Wireless Commun., 2012.
[7] Z. Zhang et al., "Full-Duplex Wireless Communications: Challenges, Solutions, and Future Research Directions," Proc. IEEE, 2016.
[8] G. Liu et al., "In-Band Full-Duplex Relaying: A Survey, Research Issues and Challenges," IEEE COMST, 2015.
[9] D. Kim, H. Lee, D. Hong, "A Survey of In-Band Full-Duplex Transmission: From the Perspective of PHY and MAC Layers," IEEE COMST, 2015.
[10] J. Zhou et al., "Integrated Full Duplex Radios," IEEE Commun. Mag., 2017.
[11] A. K. Khandani, "Methods for Teaching Wireless Communications and Full Duplex," related tutorials / patents context, 2010s.
[12] EPCglobal / ISO RFID air interface materials on reader continuous-wave and backscatter (SIC context).
