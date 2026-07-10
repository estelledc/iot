---
schema_version: '1.0'
id: flooding-vs-routing-mesh-iot
title: Mesh 网络泛洪与路由转发策略对比
layer: 2
content_type: comparison
difficulty: intermediate
reading_time: 20
prerequisites:
  - mesh-networking-topology
  - ble-mesh-networking-architecture
  - zigbee-mesh-routing-aodv
tags:
  - Mesh
  - 泛洪
  - RPL
  - AODV
  - BLE Mesh
  - Thread
  - 路由
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# Mesh 网络泛洪与路由转发策略对比

> **难度**：🟡 中级 | **领域**：Mesh 网络、转发策略 | **阅读时间**：约 20 分钟

## 日常类比

大楼紧急疏散：走廊大喊接力（人人传话）vs 按平面图派人点对点通知。前者简单吵闹，后者高效但要地图。Mesh 里对应**泛洪（flooding）**与**路由（routing）**。BLE Mesh 偏管理泛洪，Thread/Zigbee 等偏路由——选择驱动能耗、延迟与规模；案例中的传输次数与延迟为示意量级[1][4][5]。

## 摘要

对比纯/受控泛洪与反应式（AODV 类）、主动式（RPL 类）路由的机制与资源开销，给出照明广播 vs 传感单播等选型条件，并简述融合趋势[2][3][6]。

## 1 设计哲学

| 维度 | 泛洪 | 路由 |
|------|------|------|
| 下一跳 | 不预先知道，广泛转发 | 查表/按 DODAG 等转发 |
| 状态 | 主要是去重缓存 | 路由表 + 邻居表 |
| 拓扑变化 | 天然钝感 | 需修复/重建 |
| 冗余流量 | 高 | 低（单播路径） |
| 典型 | BLE Mesh 管理泛洪 | Thread/RPL、Zigbee 路由 |

## 2 泛洪机制

控制手段：消息缓存去重、TTL、网络缓存（relay 随机延迟减碰撞）、好友/低功耗节点角色等。BLE Mesh 用管理泛洪在多跳照明等场景换取实现简单与多路径冗余[4]。

纯泛洪下，一则消息可触发近 \(O(N)\) 次发送；节点增多易广播风暴。受控手段：限 TTL、概率转发、分区域、只选 relay 角色。

## 3 路由机制

**反应式（如 AODV 脉络）**：有业务才 RREQ/RREP 发现路径，适合流量稀疏；首包延迟高，路径缓存过期需重发现[2]。

**主动式（RPL）**：维护 DODAG，向上/向下路由适合多对一采集；控制消息有开销，客观函数（OF）决定“最优”[3]。

| 指标 | 泛洪倾向 | 路由倾向 |
|------|----------|----------|
| RAM | 缓存为主（较小～中） | 表项随目的地增长 |
| 能耗 | 广播多，密网易高 | 数据面省，控制面看稳定度 |
| 延迟 | 多路径，广播可较低 | 单路径，首包可能更高 |
| 可靠性 | 冗余路径 | 依赖链路质量与修复 |
| 规模 | 中小、广播友好 | 更大单播网更合适 |

## 4 选型条件

**偏泛洪**：以组播/广播为主（全屋灯控）、节点数中等、拓扑常变、实现资源极紧、可接受冗余空口。

**偏路由**：大量单播到网关、节点数百+、要省电与可扩展、能维护邻居度量（ETX 等）。

**混合**：广播控制面泛洪 + 单播数据面路由；或 BLE Mesh 路由扩展、RPL 多路径等演进[4][6]。

## 5 场景示意

| 维度 | 智能照明（泛洪友好） | 传感采集（路由友好） |
|------|----------------------|----------------------|
| 流量 | 组播/场景广播 | 多对一单播 |
| 每消息空口 | 多次 relay | 约路径跳数次 |
| 延迟目标 | 人眼可感的快响应 | 可容忍更高 |
| 规模压力 | 中等 | 更大 |

具体“200 灯 / 500 传感”的传输次数对比随密度、TTL、占空比剧烈变化，只能作直觉锚点，验收用抓包计数与电池曲线。

## 6 局限、挑战与可改进方向

### 1. 泛洪扩展性墙

**局限**：节点与消息率上升后，relay 占空比与碰撞恶化[4]。
**改进**：严格角色（少数 Friend/Relay）、TTL 与网径匹配、场景消息合并、评估路由扩展。

### 2. 路由表与内存

**局限**：MCU RAM 撑不住全网目的地表。
**改进**：分层/默认路由、RPL 多对一为主、边界路由器聚合。

### 3. 指标误导

**局限**：只比实验室跳数，忽略控制面风暴与重发现。
**改进**：统计控制/数据帧比、链路失败注入下的收敛时间。

### 4. 协议宗教化

**局限**：“BLE 一定泛洪、Thread 一定更好”脱离业务流量型。
**改进**：按单播/广播比例与规模做原型对比后再锁定栈。

## 7 总结

泛洪用冗余换简单与广播友好；路由用状态换空口效率与规模。照明类广播场景前者常见，采集类单播后者常见；混合与扩展正在消弭边界。用流量型与资源预算决策，而不是用品牌口号。

## 参考文献

[1] I. F. Akyildiz et al., "Wireless mesh networks: a survey," Computer Networks, 2005.
[2] C. Perkins, E. Belding-Royer, S. Das, "Ad hoc On-Demand Distance Vector (AODV) Routing," RFC 3561.
[3] T. Winter et al., "RPL: IPv6 Routing Protocol for Low-Power and Lossy Networks," RFC 6550.
[4] Bluetooth SIG, Bluetooth Mesh Profile / Model specifications.
[5] Thread Group, Thread specification overview.
[6] Zigbee Alliance, Zigbee PRO 路由相关规范.
[7] Y.-C. Tseng et al., "The Broadcast Storm Problem in a Mobile Ad Hoc Network," Wireless Networks, 2002.
[8] P. Levis et al., Trickle Algorithm, RFC 6206（控制面抑制相关）.
[9] BLE Mesh 性能与规模评估文献.
[10] RPL 客观函数与多路径扩展研究综述.
[11] IEEE 802.15.4 与 6LoWPAN 转发架构材料.
[12] 工业/楼宇 Mesh 部署测量报告（对照协议选择）.
