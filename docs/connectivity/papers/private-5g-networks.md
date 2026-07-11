---
schema_version: '1.0'
id: private-5g-networks
title: 私有 5G 网络在工业 IoT 中的部署
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - 5g-private-network-industrial-iot
  - cellular-iot-evolution-2g-5g
tags:
  - 私有5G
  - URLLC
  - 网络切片
  - CBRS
  - SA组网
  - 工业物联网
  - 边缘核心网
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 私有 5G 网络在工业 IoT 中的部署

> **难度**：🟡 中级 | **领域**：蜂窝通信、工业物联网 | **阅读时间**：约 20 分钟

## 日常类比

音乐节万人抢公网像挤公交；工厂 AGV 要的是专车——私有 5G 自建/托管基站与核心网，带宽与策略自控。贵，但关键控制面可追求有界时延与隔离，而不是和访客抢空口[1][3]。

## 摘要

私有 5G = 园区 gNB + 本地/边缘 5GC（AMF/SMF/UPF）+ 企业频谱或运营商托管频谱。工业价值常落在超可靠低时延（URLLC）、网络切片与数据不出园。相对 Wi-Fi：初始投资与运维门槛更高；**“比 Wi-Fi 贵数倍”属量级叙事，须用本项目 BOM 核算**[6][7]。

## 1. 部署模式与频谱

| 模式 | 频谱 | 核心网 | 适合 |
|------|------|--------|------|
| 完全自建 | 本地/共享频段 | 本地 | 大制造、矿山 |
| 运营商托管 | 运营商授权 | 本地或远端 | 中企少运维 |
| 混合 | 共享/租用 | RAN 本地+核心混合 | 要数据本地、少养核心 |

| 地区示例 | 频段线索 | 备注 |
|----------|----------|------|
| 美国 | CBRS n48 | SAS 共享，GAA/PAL |
| 欧洲 | n78 本地许可等 | 国别政策不同 |
| 日本 | 本地 5G（如 n79 段） | 牌照制 |
| 中国 | 工业互联网/专网政策演进中 | 以主管部门当期文件为准 |

Sub-6 覆盖通常优于毫米波；工业主流先 Sub-6。毫米波高吞吐但遮挡与站址密度代价大[2][9]。

## 2. SA、URLLC 与切片

私有网从零建设时，独立组网（SA）才能完整用切片与 URLLC 能力；NSA 绑 4G 锚点，工业增益有限[1]。

| 机制 | 作用 |
|------|------|
| Mini-slot | 缩短调度粒度 |
| Grant-free 上行 | 减授权往返 |
| 多 TRP/冗余 | 抬可靠性 |
| 切片（S-NSSAI） | 控制/视频/海量传感隔离 QoS |

端到端“<1 ms / 99.999%”是 3GPP 场景目标量级，**现场受同步、回传、应用栈影响，验收用业务闭环时延百分位**[3]。

开源 5GC（Open5GS、free5GC、OAI 等）适合试验；产线仍需商用支持与冗余设计[4][5]。

## 3. 与 Wi-Fi 的决策表

| 条件 | 更偏 Wi-Fi | 更偏私有 5G |
|------|------------|-------------|
| 时延 | 尽力、可抖动 | 要有界/隔离 |
| 移动 | 低速人员 | 高速 AGV/跨区切换 |
| 安全 | 标准企业网 | 数据本地、专网隔离 |
| 面积/密度 | 小区域 | 大园区、高连接 |

办公与访客可留 Wi-Fi；产线关键切片走 5G——共存是常态，而非二选一[6]。

## 4. 局限、挑战与可改进方向

### 1. 成本与技能

**局限**：小基站、核心网、SIM/eSIM、专业运维推高 TCO。
**改进**：先单车间 POC；托管/NaaS；只把关键切片迁 5G。

### 2. 频谱不确定

**局限**：GAA 可能避让；各国牌照规则不一。
**改进**：关键产线评估 PAL/本地许可；设计降功率与备选信道。

### 3. 工业环境射频

**局限**：金属反射、阻挡使仿真乐观。
**改进**：强制现场勘测；与 iBwave 等工具互补，不以仿真代替路测。

### 4. URLLC 期望落差

**局限**：空口指标好不等于 PLC–应用闭环达标。
**改进**：测完整控制环；UPF 本地部署；应用侧减抖动缓冲。

## 5. 实践要点

1. 先写清业务：时延上界、可靠性、数据是否出园。
2. 优先 SA + 本地 UPF；切片从一类业务试点。
3. 成本对比用 5 年 TCO + 停机损失，不单比 AP 单价。

## 参考文献

[1] 3GPP TS 23.501, System architecture for the 5G System.
[2] CBRS Alliance / OnGo materials on private networks and spectrum sharing.
[3] 5G-ACIA, "5G for Connected Industries and Automation," white paper.
[4] Open5GS documentation.
[5] srsRAN / OAI private 5G lab deployment guides.
[6] Nokia / Ericsson private 5G enterprise white papers (KPIs case-specific).
[7] GSMA materials on private 5G use cases and spectrum.
[8] 3GPP URLLC / industrial IoT related TSs (e.g., scheduling, redundancy).
[9] National regulators' local 5G / shared spectrum notices (country-specific).
[10] ABI / analyst private 5G market notes (treat forecasts cautiously).
[11] Wi-Fi 6/6E vs private 5G industrial comparison studies.
