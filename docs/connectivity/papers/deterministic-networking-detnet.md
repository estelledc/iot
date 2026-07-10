---
schema_version: '1.0'
id: deterministic-networking-detnet
title: 确定性网络DetNet在工业IoT中的应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - ethernet-industrial-iot-tsn
tags:
- DetNet
- TSN
- PREOF
- MPLS
- 确定性网络
- IETF
- 工业IoT
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 确定性网络DetNet在工业IoT中的应用

> **难度**：🔴 高级 | **领域**：确定性网络、工业广域互联 | **阅读时间**：约 22 分钟

## 日常类比

普通快递尽力排队；运移植器官则预留专线、站站留位。IETF DetNet（Deterministic Networking）在 IP/MPLS 上为指定流做资源预留与冗余，把「大概能到」变成「延迟有上界、规划内不因拥塞丢包」。TSN（Time-Sensitive Networking）像楼内确定性走廊；DetNet 像城际确定性高速——常见拼法是 TSN 岛经 DetNet WAN 再进另一 TSN 岛[1][4][5]。

## 摘要

讲解服务/转发子层、PREOF、MPLS/IP 数据面与集中控制。电力远动等用例中的毫秒级数字来自领域需求与试验配置，换拓扑必须重算路径延迟预算[5][6]。

## 1 目标与和 TSN 分工

DetNet 追求：有界延迟、低抖动、规划下零拥塞丢包、经冗余达高可靠[1]。

| 维 | TSN | DetNet |
|----|-----|--------|
| 层次 | 主要 L2 以太网 | 主要 L3 IP/MPLS |
| 范围 | 站点/园区局域网 | 跨站点广域 |
| 标准 | IEEE 802.1 | IETF |
| 可靠 | 802.1CB FRER 等 | PREOF（同类思想） |
| 成熟度 | 商用相对更多 | 标准化与试点并行 |

仅靠 TSN 不够的场景：跨厂协同、远动保护穿 IP 骨干、多场馆同步媒体等[5]。

## 2 架构与 PREOF

节点角色：PE（边缘，封装/解封装与 PREOF）、P（中继确定性转发）、控制器（路径、准入、下发）[1]。

服务子层：流识别、序列号、PREOF（Packet Replication, Elimination, and Ordering Functions）。转发子层：显式路径、队列/带宽预留、整形[1][6]。

```
源 --复制--> 路径A --+
     --复制--> 路径B --+--> 消除/排序 --> 宿
```

单路径故障时另一路径仍可交付；乱序由排序窗处理，窗过小丢、过大增延迟[6]。

## 3 数据面与控制面

| 承载 | 要点 |
|------|------|
| MPLS | F-Label 路径 + S-Label 流/PREOF，与 TE 自然结合[2] |
| IP/SRv6 等 | 显式路径编码，适无 MPLS 域[3] |
| 与 TSN 映射 | 流 ID、FRER、预留、QoS 门控在边缘对接[4] |

控制：拓扑发现 → 流需求（带宽/延迟/可靠）→ 准入 → 多路径计算 → 逐节点预留 → NETCONF/YANG 等下发[1]。相对 DiffServ：不只标优先级，而是占住资源。

## 4 用例与对比示意

电力 teleprotection、远程 SCADA、专业 AV 是常见叙事；专用 SDH 贵但行为熟，普通 IP VPN 抖动大，DetNet 意图在共享 IP 上逼近专线确定性[5]。

| 指标倾向 | SDH 专线 | IP VPN+DiffServ | DetNet（目标） |
|----------|----------|-----------------|----------------|
| 延迟 | 低且稳 | 可变 | 有上界（设计值） |
| 可靠 | 高 | 尽力偏高优 | PREOF 冗余 |
| 成本 | 高 | 较低 | 中（升级+控制器） |

表值为定性对照，验收用仪表测延迟 CDF 与丢包[5][9]。

## 5 局限、挑战与可改进方向

### 1. 逐流状态扩展性

**局限**：每节点流状态随流数增长，难比肩 DiffServ 的少量队列。
**改进**：聚合流类、分层域、只对真正关键流开 DetNet；其余用 TSN/普通 QoS[1][10]。

### 2. 与尽力流量共存

**局限**：预留过多挤占普通业务；预留不足则确定性破裂。
**改进**：严格准入与容量规划；切片/队列隔离；持续遥测违约率[1]。

### 3. 无线段不确定性

**局限**：无线跳延迟/丢包破坏端到端界时延假设。
**改进**：无线段用 5G URLLC/TSN 桥等有界技术；边界加抖动缓冲；跨域控制器协同[4][11]。

### 4. 产业成熟度

**局限**：芯片/路由器支持与运维工具仍不均。
**改进**：先在 MPLS 骨干试点单类流；选择声明支持 RFC 数据面的平台；与 TSN CNC 工具链对齐[2][4][12]。

## 参考文献

[1] RFC 8655, "Deterministic Networking Architecture," IETF.
[2] RFC 8939, "DetNet Data Plane: MPLS," IETF.
[3] RFC 9023 / related, DetNet IP data plane documents, IETF.
[4] RFC 9024, DetNet–TSN interworking, IETF.
[5] RFC 8578, "Deterministic Networking Use Cases," IETF.
[6] RFC 9037 (and related), PREOF / packet replication elimination ordering.
[7] RFC 8938, DetNet data plane framework.
[8] N. Finn et al., introductions to IETF DetNet, IEEE Comm. Standards Magazine.
[9] Utility teleprotection timing requirements literature (IEC domain).
[10] Scalability analyses of per-flow reservation vs class-based QoS.
[11] 5G URLLC and DetNet/TSN integration white papers.
[12] Vendor DetNet trial notes (router/chip support status — verify current).
