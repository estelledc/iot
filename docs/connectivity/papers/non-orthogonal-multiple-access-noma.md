---
schema_version: '1.0'
id: non-orthogonal-multiple-access-noma
title: 非正交多址NOMA在大规模IoT中的应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - noma-iot-access
  - grant-free-access-massive-iot
tags:
  - NOMA
  - 上行
  - 码域
  - 过载
  - SIC
  - LPWAN
  - mMTC
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 非正交多址NOMA在大规模IoT中的应用

> **难度**：🔴 高级 | **领域**：多址接入 | **阅读时间**：约 22 分钟

## 日常类比

资源块像教室话筒：正交多址（OMA）同时只给一人。大规模物联网设备远多于话筒时，允许多人叠着说、靠基站“先听强再消再听弱”，把过载（overloading）从事故变成设计——这是面向海量连接的 NOMA 叙事。

## 摘要

侧重上行功率域、码域（SCMA/MUSA 等）对比、与免授权及 LPWAN 的结合，以及基站侧 SIC 部署边界。连接数倍增与时隙节省为场景推演，**依赖检测算法与负载模型，须仿真/外场复核**[1][3][4]。

## 1. OMA 瓶颈与过载

FDMA/TDMA/OFDMA 等：一块正交资源服务一设备。蜂窝物联网载波上同时可调度的正交单元有限，设备数上万时只能靠排队与重试。NOMA 目标：同一时频上 K>1 设备，系统连接能力可超过正交资源数[1][3]。

## 2. 上行功率域（IoT 最相关）

传感以上行为主。远近不同使到达功率天然分层，基站按强→弱 SIC；**终端可保持“正常发送”**，复杂度集中在基站——这是相对下行终端 SIC 的关键工程优势[2][3]。

| 步骤 | 动作 |
|------|------|
| 1 | 解最强，弱者当噪声 |
| 2 | 重建并减去 |
| 3 | 对残余重复直至最弱 |

风险：误差传播。缓解：级间 SINR 余量、CRC 确认再消除、失败回退正交解码、限制复用阶数[1]。

功率策略：固定发射靠几何差；或按接收功率分簇——簇内 NOMA、簇间 OMA。

## 3. 码域与功率域

| 特性 | 功率域 | 码域（SCMA/MUSA 等） |
|------|--------|---------------------|
| 分离依据 | 功率差 | 码本/序列 |
| 过载叙事 | 常 2–3 量级讨论 | 方案相关，可更高叙事 |
| 检测 | SIC 为主 | MPA/SIC 等 |
| 功率控制 | 很关键 | 相对不那么依赖功率差 |
| IoT | 上行自然分层 | 大规模免授权候选 |

LoRa 不同扩频因子近似正交、同 SF 捕获效应等，可作“类 NOMA”直觉，但**不等于蜂窝 NOMA 标准**；网关增强 SIC 的容量增益以研究/试点为准[7][8]。

## 4. 免授权 + 活跃检测

设备预配置资源直发；基站用稀疏活跃假设做压缩感知式检测与联合解码。注册数大、同时活跃少时才划算——突发同步上报会抬高碰撞与漏检[3][10]。

| 更适 NOMA | 更适 OMA |
|-----------|----------|
| 多设备低速率、拥塞 | 少设备高速率 |
| 可接受基站复杂检测 | 要极简接收机 |
| 免授权小包 | 严格正交 QoS |

混合：空闲正交、热点过载；NOMA/OMA 终端可共存于同一小区叙事下，取决于实现[4]。

## 5. 标准化现实

多方案（SCMA、MUSA、PDMA 等）在 3GPP 研究中评估；Rel-16 等结论强调增益与复杂度权衡，**未等于已全面写入 NR 必选特性**。规划应写“研究项/可选增强”，并读现行 TR/CR[4][5]。

## 6. 局限、挑战与可改进方向

### 1. 信道估计与导频污染

**局限**：多用户叠加使导频与估计变难，弱用户尤甚。
**改进**：稀疏导频设计；联合活跃检测与估计；限制同时叠加数。

### 2. 误差传播与公平

**局限**：弱用户中断敏感，功率差过大伤边缘。
**改进**：分簇+最小速率约束；动态降阶；边缘保底正交资源。

### 3. 标准与多厂商互操作

**局限**：终端透明不等于空口已统一 NOMA 波形。
**改进**：优先基站接收机增强类方案；跟进正式 ASN.1/能力比特再规模商用。

### 4. LPWAN 占空比与监管

**局限**：多发冗余/重试受占空比与共存规则约束。
**改进**：与 ADR/SF 规划联合；容量增益用网关侧算法而非盲目加密集度。

## 7. 实践要点

1. 写清“终端是否改动”——上行基站 SIC 与终端码本是两条产品线。
2. 验收看活跃检测率、每级 CRC 失败率、边缘中断，而非只看过载倍数。
3. 高峰模型用真实上报相关（上班潮汐），避免均匀泊松乐观。

## 参考文献

[1] L. Dai et al., "A Survey of Non-Orthogonal Multiple Access for 5G," IEEE COMST, 2018.
[2] Z. Ding et al., "Application of NOMA in LTE and 5G Networks," IEEE Commun. Mag., 2017.
[3] M. Shirvanimoghaddam et al., "Massive NOMA for Cellular IoT," IEEE Commun. Mag., 2017.
[4] 3GPP TR 38.812, Study on Non-Orthogonal Multiple Access for NR.
[5] H. Nikopour, H. Baligh, "Sparse Code Multiple Access," IEEE PIMRC, 2013.
[6] Z. Yuan et al., "Multi-User Shared Access for Internet of Things," IEEE VTC.
[7] Studies on LoRa capture effect and SIC at gateways (capacity analyses).
[8] Semtech / LoRa Alliance materials on SF orthogonality (approximate; verify in product docs).
[9] Y. Saito et al., "Non-Orthogonal Multiple Access for Cellular Future Radio Access," IEEE VTC, 2013.
[10] Compressive sensing based grant-free NOMA / active user detection surveys.
[11] PDMA / NOCA and other 3GPP NOMA candidate overview papers.
[12] Information-theoretic MAC capacity and SIC receiver fundamentals (Cover & Thomas; Tse & Viswanath).
