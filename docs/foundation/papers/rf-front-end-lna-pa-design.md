---
schema_version: '1.0'
id: rf-front-end-lna-pa-design
title: 射频前端LNA/PA设计基础与指标
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites:
  - rf-filter-saw-baw-iot
  - antenna-impedance-matching-network
tags:
  - LNA
  - PA
  - FEM
  - 噪声系数
  - PAE
  - 射频前端
  - IoT
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 射频前端LNA/PA设计基础与指标

> **难度**：🔴 高级 | **领域**：射频前端设计 | **关键词**：LNA, PA, NF, PAE, FEM | **阅读时间**：约 18 分钟

## 日常类比

助听器：微弱外界声先经高灵敏麦克风放大且尽量不引入沙沙声——对应低噪声放大器（Low Noise Amplifier, LNA）；播放端扬声器要把信号推到可听响度——对应功率放大器（Power Amplifier, PA）。麦克风本底噪声高，后面再放大也是噪声；扬声器失真，声音刺耳。物联网（Internet of Things, IoT）前端还要在时分双工（Time Division Duplex, TDD）下用单刀双掷（Single-Pole Double-Throw, SPDT）开关共享天线。前端在物料清单（Bill of Materials, BOM）里占比常不大，却强约束链路距离与可靠性——具体比例随产品而异，勿当固定百分比[1][5]。

## 摘要

梳理接收/发射链路、LNA 与 PA 关键指标、工作类别、前端模组（Front-End Module, FEM）、Friis 级联噪声与法规等效全向辐射功率（Equivalent Isotropically Radiated Power, EIRP）约束。数值为常见量级，设计以数据手册与认证限值为准[2][3][6]。

## 1. 前端架构

接收：天线 → 带通滤波 → LNA → 混频 → 中频处理 → 模数转换。发射：基带 → 数模 → 滤波 → 调制 → PA → 滤波 → 天线。TDD 用 SPDT；频分双工（Frequency Division Duplex, FDD）用双工器[1]。

| 维度 | 手机倾向 | IoT 倾向 |
|------|----------|----------|
| 频段数 | 很多 | 常 1–2 |
| PA 功率 | 更高 | 约 0–+20 dBm 量级常见 |
| LNA 噪声系数（Noise Figure, NF） | 极低 | 中等即可 |
| 成本/功耗 | 相对宽裕 | 紧 |

## 2. LNA 指标与权衡

NF(dB) = 10·log10(SNR_in/SNR_out)。灵敏度粗式：−174 + NF + 10·log10(BW) + SNR_min（单位与假设需与标准一致）。NF 恶化约 1 dB 往往对应覆盖距离可感知缩短，但“缩短 10%”仅为自由空间粗估，室内传播勿照搬[4][6]。

| 参数 | 含义 | IoT 常见量级 |
|------|------|--------------|
| 增益 | 放大倍数 | 约十余至二十余 dB |
| IIP3 | 三阶输入截点，抗干扰线性度 | 约 −5–+10 dBm |
| P1dB | 1 dB 压缩点 | 常低于 IIP3 约 9–10 dB |

噪声匹配（最小 NF 的源阻抗）与功率匹配（最小反射）通常不一致；IoT 多折中。稳定性需满足 Rollett 因子等条件，常用源极电感负反馈[1]。

| 方案 | NF 倾向 | 适用 |
|------|---------|------|
| SoC 内置 LNA | 较高 | 多数短距 |
| 外置分立 LNA | 更低 | 远距离 |
| FEM 集成 LNA | 中等 | Wi-Fi/蜂窝模组 |

## 3. PA 指标、类别与效率

功率附加效率（Power-Added Efficiency, PAE）= (Pout−Pin)/Pdc。邻道功率比（Adjacent Channel Power Ratio, ACPR）约束 Wi-Fi/LTE 等非恒包络系统的线性度。谐波与杂散受法规限制，Sub-GHz 二次谐波常落入蜂窝频段，需滤波[2][3]。

| 类别 | 效率倾向 | 线性度 | IoT 用途 |
|------|----------|--------|----------|
| A/AB | 中 | 较好 | Wi-Fi/LTE 等 |
| C/E/F | 高 | 差（需滤波） | 恒包络如部分 BLE/LoRa |

功率回退时 AB 类 PAE 常急剧下降，近场通信未必更省电——可用动态偏置缓解[2]。

| 技术 | 输出功率常见量级 |
|------|------------------|
| BLE | 约 0–+4 dBm（等级相关） |
| Wi-Fi 消费级 | 约 +15–+20 dBm |
| LoRa 模组 | 约 +14–+20 dBm |
| LTE | 约 +23 dBm（功率等级相关） |

## 4. SPDT、FEM 与外置前端

SPDT 关注插入损耗、隔离与切换时间（微秒量级常见）。FEM 把 PA+LNA+开关集成，减面积、提一致性，但须跟参考设计、去耦与收发时序[5][7]。

| 方案 | 元件数倾向 | 注意 |
|------|------------|------|
| 分立 PA/LNA/开关 | 多 | 匹配与一致性自负 |
| FEM | 少 | 勿随意改匹配；注意热 |

外置前端可把发射从数 dBm 抬到约 +20 dBm 量级，但 SoC 输出不可超过 PA 的线性区/P1dB，必要时加衰减或降驱动[5]。

## 5. Friis 级联与链路预算

总噪声因子 F_total = F1 + (F2−1)/G1 + …——第一级 NF 与增益主导。滤波器在 LNA 前：保护过载、NF≈叠加插入损耗；在 LNA 后：NF 更好、强干扰风险更高。IoT 干扰不可控时多选先滤波[4][8]。

| 项目 | 要点 |
|------|------|
| 接收预算 | 级联 NF → 灵敏度；FEM 改善有限但可测 |
| 发射预算 | 驱动勿压垮 PA；计及滤波插损 |
| 热 | 耗散≈Pdc−Pout；壳温升需降额 |

## 6. 法规与 EIRP

限值常针对 EIRP = 传导功率 + 天线增益 − 馈线损耗。换高增益天线可能超标，须降传导功率。杂散/谐波另有绝对或相对限值[3][9]。

| 地区/频段（示例） | 约束类型 |
|-------------------|----------|
| 中国/欧盟 2.4 GHz ISM | EIRP 上限（以现行国标/EN 为准） |
| 美国 FCC Part 15 | 传导/辐射限值组合 |
| 欧盟 868 MHz 等 | 按 EN 300 220 等 |
| LTE | 3GPP 功率等级 |

## 7. 局限、挑战与可改进方向

### 1. NF 与线性度、功耗三角

**局限**：降 NF、提 IIP3 常要加偏置电流，与电池预算冲突。
**改进**：按场景选内置/外置/FEM；空闲关断前端偏置[1][5]。

### 2. 回退区效率陷阱

**局限**：非恒包络在功率回退时 PAE 很差，近距未必省电。
**改进**：动态偏置/包络跟踪（若芯片支持）；协议侧控速率与功率[2]。

### 3. 参考设计被随意改匹配

**局限**：改 FEM 匹配导致增益、ACPR、杂散全面恶化。
**改进**：锁定参考网络；改版必做传导与辐射复测[5][7]。

### 4. EIRP 与天线增益脱节

**局限**：只盯芯片“最大 dBm”，忽略天线增益导致认证失败。
**改进**：以 EIRP 预算表驱动传导功率上限[3][9]。

## 总结

LNA 守 NF 与抗阻塞，PA 守效率与线性/杂散，开关与滤波决定双工方式。Friis 强调第一级；FEM 是主流集成路径；合规看 EIRP 与杂散而非单一传导读数。

## 参考文献

[1] B. Razavi, *RF Microelectronics*, 2nd ed. Pearson, 2011.
[2] S. C. Cripps, *RF Power Amplifiers for Wireless Communications*, 2nd ed. Artech House, 2006.
[3] ETSI EN 300 328（现行版本）.
[4] H. T. Friis, "Noise Figures of Radio Receivers," *Proc. IRE*, 1944.
[5] Skyworks, SKY66112 等 IoT FEM 数据手册与应用笔记.
[6] IEEE / Bluetooth SIG, 接收灵敏度与链路预算相关规范背景.
[7] Qorvo / 康希等 Wi-Fi FEM 参考设计.
[8] Keysight, 级联噪声与噪声系数测量应用笔记.
[9] FCC Part 15；GB/T 等相关 2.4 GHz 限值文件.
[10] 3GPP TS 36.101 发射功率与 ACLR 要求.
[11] TI CC2592 等范围扩展器数据手册（外置前端示例）.
[12] R. Ludwig, *RF Circuit Design*（匹配与稳定补充）.
