---
schema_version: '1.0'
id: lorawan-relay-coverage-extension
title: LoRaWAN中继节点覆盖扩展方案
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - lorawan-gateway-design-deployment
tags:
  - LoRaWAN
  - 中继
  - TS011
  - WOR
  - 覆盖扩展
  - 盲区
  - 电池
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# LoRaWAN中继节点覆盖扩展方案

> **难度**：🟡 中级 | **领域**：LoRaWAN网络扩展 | **阅读时间**：约 16 分钟

## 日常类比

山谷手机信号：山顶基站满格，谷底无信号；半山腰放大器收山顶再转谷底。LoRaWAN 中继（Relay）用终端级设备经 LoRa 再传一跳到网关，**不新增 IP 回程**[1][2]。

## 摘要

TS011 定义标准中继行为：Wake-on-Radio（WOR）唤醒、透明转发、端到端安全仍由终端与网络侧密钥保证。容量与电池受占空比和双倍空口占用约束；**适合小规模补盲，不是网关替代品**[1][3]。

## 1. 盲区与为何不用总加网关

| 盲区 | 例 | 加网关痛点 |
|------|-----|------------|
| 距离/遮挡 | 农田深处、地下室 | 回程/供电/审批 |
| 临时 | 活动、工地 | CAPEX 不值 |

中继：终端 →（LoRa）→ 中继 →（LoRa）→ 网关 → IP → NS[1]。

## 2. TS011 要点

中继自身也是入网终端，可被 MAC 命令管理。终端先发 WOR 前导唤醒中继，再发数据；中继在标准信道转发并附带射频元数据。下行常存于中继，待终端再上行时捎回——延迟高于直连[1][4]。

| 对比 | 中继 | 网关 |
|------|------|------|
| 回程 | 不需要 | 需要 |
| 成本/供电 | 终端级、可电池/太阳能 | 更高、常持续供电 |
| 容量 | 有限（数十设备量级叙事） | 高得多 |
| 跳数 | 规范侧重受控中继模型 | 单跳星型 |

端到端：中继不解密应用载荷；MIC 仍由网络验证[1]。

## 3. WOR 与容量

中继多数时间休眠，周期性侦听 WOR，以换电池寿命；前导须覆盖监听周期。转发使同一业务多占空口，占空比区域下每小时可转发次数随 SF 急剧下降[3][5]。

| 上报越频 / SF 越高 | 单中继可服务终端 |
|--------------------|-------------------|
| 倾向 | 越少 |
| 缓解 | 降频、降 SF、市电中继、改网关 |

## 4. 场景与选型

地下车库、谷地农业、深层楼宇外墙中继等：中继须**同时**可靠看见网关与盲区终端。TS011 非任意多跳 Mesh；需要多跳时应评估 Mesh 产品或加网关/漏缆[6]。

| 因素 | 偏中继 | 偏加网关 |
|------|--------|----------|
| 盲区设备数 | 少 | 多 |
| 回程 | 无 | 有 |
| 标准互通 | 要 TS011 | 标准星型 |

## 5. 局限、挑战与可改进方向

### 1. 单跳与位置苛刻

**局限**：中继到网关链路不足则整片失明。
**改进**：选址留足裕量；无法直连则加网关而非堆中继。

### 2. 容量与占空比

**局限**：双倍空口 + 高 SF 很快触顶。
**改进**：限制挂载终端数；ADR/减载荷；超量改网关。

### 3. 电池寿命低估

**局限**：按深睡电流估，忽略 WOR 与转发峰值。
**改进**：按实际转发次数算 mAh；关键中继改市电/太阳能。

### 4. 与专有 Mesh 混淆

**局限**：采购“能多跳”的非标设备导致运维分裂。
**改进**：要互通就坚持 TS011；要多跳就接受非标并单列运维。

## 6. 实践要点

1. 先路测：候选点到网关、盲区到候选点双向连通。
2. 写清最大挂载终端与上报周期。
3. 监控中继自身电量与转发成功率。

## 参考文献

[1] LoRa Alliance, TS011 LoRaWAN Relay Specification.
[2] LoRa Alliance, Relay coverage extension white papers.
[3] Adelantado, F. et al., "Understanding the Limits of LoRaWAN," IEEE Commun. Mag., 2017.
[4] Semtech, relay implementation guides for SX126x class devices.
[5] Bor, M. et al., LoRa scaling / airtime related studies, MSWiM/EWSN.
[6] Comparisons of LoRaWAN relay vs mesh (Wirepas/Meshtastic et al.)—treat as architecture choice.
[7] Caillouet, C. et al., relay placement optimization research.
[8] LoRaWAN Specification (baseline star topology context).
[9] Regional Parameters (duty cycle constraints affecting relay TX).
[10] Vendor case studies: underground parking / agriculture relay deployments.
[11] Security notes: transparent forwarding and end-to-end MIC/AppSKey.
