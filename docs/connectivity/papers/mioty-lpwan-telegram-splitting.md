---
schema_version: '1.0'
id: mioty-lpwan-telegram-splitting
title: MIOTY LPWAN电报分割技术分析
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 20
prerequisites:
  - lorawan-scalability
tags:
  - MIOTY
  - LPWAN
  - Telegram-Splitting
  - ETSI-TS-103-357
  - DBPSK
  - 工业物联网
  - 抗干扰
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# MIOTY LPWAN电报分割技术分析

> **难度**：🔴 高级 | **领域**：新型LPWAN | **阅读时间**：约 20 分钟

## 日常类比

重要信件若装一个大信封，半路被拦就整封丢失；若撕成多片分时分路寄出，丢若干片仍可能拼回——MIOTY 的电报分割（Telegram Splitting）把报文经前向纠错（Forward Error Correction, FEC）后拆成多个子包，在时间与频率上分散发送[1][3]。

## 摘要

介绍 Fraunhofer IIS 起源、ETSI TS 103 357 定位、分割与时频分集、星型架构及与 LoRaWAN/Sigfox/NB-IoT 的对比边界。容量“十万级/基站”、距离与电池年数多为宣传/试验量级，**以标准参数与现场试验为准**[1][2][5]。

## 1. 背景与目标

MIOTY 面向强干扰、大规模传感上报；物理/MAC 由 ETSI TS 103 357 等 LTN 相关规范描述，生态仍相对小众[1][2]。设计叙事强调可靠性、大连接、长续航与公里级覆盖，适合工业监测、抄表等小包上行[2][5]。

## 2. 电报分割机制

流程概要：载荷 → CRC → FEC → 拆为固定数量子包（常见叙述为 24）→ 按调度在不同时隙/频率发射 → 基站收集部分子包后仍可能解码[1][3]。

| 分集 | 对抗 |
|------|------|
| 时间 | 突发干扰 |
| 频率 | 窄带干扰、频率选择性 |
| 编码 | 随机错误与部分子包丢失 |

相对“单包连续空中时间”技术，干扰需命中更多碎片才致失败；具体丢包曲线依赖子包错误率与 FEC 门限，文中百分比仅作定性[3][7]。

## 3. 物理层与容量直觉

| 参数（常见叙述） | 说明 |
|------------------|------|
| 频段 | Sub-GHz ISM（如 EU 868 / US 915 类） |
| 子包带宽 | 极窄带（约百 Hz 量级叙述） |
| 调制 | DBPSK 等 |
| 速率 | kbps 以下量级 |
| 载荷 | 小字节级，适传感 |

极窄带子包提高灵敏度与频谱并行度，但基站需宽带监听与子包关联，复杂度高于“单包解调”网关[1][4]。拓扑多为星型；下行与占空比受限，偏上行上报[2][6]。

## 4. 与其他 LPWAN

| 维度 | MIOTY | LoRaWAN | NB-IoT |
|------|-------|---------|--------|
| 抗干扰思路 | 分割+分集 | CSS 扩频 | 授权谱+重复等 |
| 生态 | 较小 | 大 | 运营商 |
| 下行 | 有限 | Class 分级 | 相对强 |
| 部署 | 私有网为主 | 私有/公网 | 蜂窝 |

工业强电磁与金属多径是其差异化叙事场景；模块与基站选择少于 LoRa，集成风险需评估[4][5][8]。

## 5. 局限、挑战与可改进方向

### 1. 生态与供应链

**局限**：模组/工具链/人才少于主流 LPWAN。
**改进**：概念验证对比 LoRa 丢包；锁定双源或可迁移应用层。

### 2. 下行与时延

**局限**：分割拉长发送窗，控制类下行弱。
**改进**：下行稀有命令聚合；实时控制改用其他链路。

### 3. 基站算力与成本

**局限**：宽带 SDR + 关联解码推高关口成本。
**改进**：按连接密度测算关口 TCO；与多 LoRa 网关方案比总拥有成本。

### 4. 指标不可照搬白皮书

**局限**：10 万设备、99.9% 到达率等缺场景边界。
**改进**：按报文率、占空比法规、干扰谱做试验矩阵。

## 6. 实践要点

1. 先在目标厂房做共存干扰扫描与对比试点。
2. 应用层按最小载荷设计，避免逼近模式上限。
3. 运维监控子包丢失分布，而不只看最终解码成功率。

## 参考文献

[1] ETSI TS 103 357, Short Range Devices; Low Throughput Networks (LTN); radio interface related.
[2] Fraunhofer IIS, mioty technical white papers / product materials.
[3] Kilian, G. et al., telegram splitting reliability, IEEE Trans. Commun. related, 2015.
[4] Radiocrafts RC1882CEF (and similar) MIOTY module datasheets.
[5] Schlicht, M. et al., MIOTY industrial IoT evaluation (e.g. IEEE WCNC related).
[6] ETSI LTN overview materials comparing radio interfaces.
[7] Analytical notes on erasure coding + time-frequency hopping under interference.
[8] LoRa Alliance / LoRaWAN capacity literature (for contrast).
[9] Sigfox technical overviews (UNB contrast).
[10] 3GPP NB-IoT overviews (licensed-band contrast).
[11] OMS / metering LPWAN deployment surveys mentioning MIOTY (if applicable; verify).
