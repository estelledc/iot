---
schema_version: '1.0'
id: noma-iot-access
title: NOMA 非正交多址接入技术：让更多设备"同时说话"
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - 5g-mmtc-massive-iot-connection
  - grant-free-access-massive-iot
tags:
  - NOMA
  - SIC
  - 功率域
  - 免调度
  - SCMA
  - mMTC
  - MUST
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# NOMA 非正交多址接入技术：让更多设备"同时说话"

> **难度**：🟡 中级 | **领域**：多址接入、5G mMTC | **阅读时间**：约 22 分钟

## 日常类比

正交多址像点名：同时只一人发言（时分）或各用不同频道（频分）。非正交多址（Non-Orthogonal Multiple Access, NOMA）像两人同时答、音量不同：老师先听清大声的，脑中减去后再听小声的——即逐次干扰消除（Successive Interference Cancellation, SIC）。

## 摘要

讲清功率域叠加与 SIC、相对正交多址（OMA）的取舍、免调度（grant-free）与稀疏码多址（SCMA）要素，以及 3GPP MUST/研究项背景。频谱效率与延迟增益多为仿真量级，**实网受信道估计与错误传播约束**[1][2][4]。

## 1. 功率域模型

下行两用户：基站发 `x = √P1·s1 + √P2·s2`（P1+P2=P），通常远端分更大功率。近端先解远端（当噪声中的强分量），SIC 减去后再解己方；远端常把近端当噪声直接解[1][2]。

| 用户 | 解码策略（理想） |
|------|------------------|
| 远端 | 近端干扰当噪声 |
| 近端 | 先解远端 → SIC → 解己方 |

理想 SIC 下近端 SINR 可接近无多用户干扰；实际残留与信道估计误差会吃掉增益。

## 2. 相对 OMA

| 维度 | OMA（如 OFDMA） | 功率域 NOMA |
|------|-----------------|-------------|
| 资源占用 | 一块资源一用户 | 同块叠加多用户 |
| 频谱效率 | 基准 | 文献常报两用户有可观增益 |
| 接收机 | 单用户 | 多级 SIC/迭代 |
| CSI/功率 | 中等 | 分配与排序更敏感 |
| 错误传播 | 无 | 前级错影响后级 |
| mMTC 信令 | 调度 grant 重 | 可与免调度结合 |

信息论上，下行叠加编码可逼近广播容量域边界；OMA 往往只达子集——**不等于商用必选 NOMA**[1]。

## 3. 免调度与码域要点

传统接入：前导→授权→数据，时延与信令对小包不友好。Grant-free NOMA：预配置资源上直接发，基站做活跃检测+多用户分离[3][4]。

| 要素 | 作用 |
|------|------|
| 导频/序列 | 活跃检测、区分用户 |
| 稀疏码本（SCMA） | 过载映射，MPA 等检测 |
| 压缩感知 | 稀疏活跃用户检测 |
| SIC/MPA/EP | 分离叠加信号 |

SCMA 典型叙事：多于资源数的用户稀疏占用子载波，过载率 >100%——具体因子图与过载以方案论文为准[5]。

## 4. MIMO 与标准化语境

同波束内功率域复用、波束间空间隔离是常见组合；用户配对常看信道增益差或相关性。天线远多于用户时，纯空间分离已强，NOMA 相对增益可能缩小；过载（用户>空间自由度）时更有价值[1][6]。

3GPP 曾研究 MUST（下行多用户叠加）与 NR NOMA SI；复杂度与增益权衡下，**未简单等同于“5G 已全面标配功率域 NOMA”**——读 TR 结论，勿营销化[4]。

## 5. 局限、挑战与可改进方向

### 1. SIC 错误传播

**局限**：强用户解错则弱用户全毁。
**改进**：保证级间 SINR 余量；CRC 门控再消除；失败回退 OMA。

### 2. CSI 与功率分配

**局限**：分配依赖过时/粗糙 CSI 时公平与中断恶化。
**改进**：鲁棒功率比；按大尺度分组；上行利用自然功率差。

### 3. 接收复杂度与标准化

**局限**：基站多用户检测成本高，标准采纳谨慎。
**改进**：限制每资源复用数；热点动态开启；跟进 Rel 研究项而非假设已冻结。

### 4. 仿真增益落地难

**局限**：理想 SIC/完美 CSI 的百分比不可当 SLA。
**改进**：用本网路测中断与活跃检测率验收；与 grant-free 流程联调。

## 6. 实践要点

1. IoT 优先想上行+基站侧检测，避免抬高终端复杂度。
2. 先定最大复用阶数与失败回退，再谈过载率。
3. 与调度式 OMA 混用：空闲 OMA、拥塞再叠加。

## 参考文献

[1] L. Dai et al., "A Survey of Non-Orthogonal Multiple Access for 5G," IEEE Commun. Surveys Tuts., 2018.
[2] Z. Ding et al., "Application of Non-Orthogonal Multiple Access in LTE and 5G Networks," IEEE Commun. Mag., 2017.
[3] M. Shirvanimoghaddam et al., "Massive Non-Orthogonal Multiple Access for Cellular IoT," IEEE Commun. Mag., 2017.
[4] 3GPP TR 38.812, Study on Non-Orthogonal Multiple Access (NOMA) for NR.
[5] H. Nikopour, H. Baligh, "Sparse Code Multiple Access," IEEE PIMRC, 2013 (SCMA).
[6] Y. Saito et al., "Non-Orthogonal Multiple Access (NOMA) for Cellular Future Radio Access," IEEE VTC, 2013.
[7] 3GPP MUST related study materials (LTE multiuser superposition transmission).
[8] Z. Yuan et al., "Multi-User Shared Access for Internet of Things," IEEE VTC (MUSA context).
[9] T. Cover, J. Thomas, Elements of Information Theory (broadcast/MAC capacity context).
[10] Grant-free access surveys for mMTC (compressive sensing active user detection).
[11] MIMO-NOMA clustering and beamforming survey literature.
[12] Outage probability analyses of downlink power-domain NOMA under fading.
