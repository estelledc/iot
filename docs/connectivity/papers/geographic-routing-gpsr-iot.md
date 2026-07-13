---
schema_version: '1.0'
id: geographic-routing-gpsr-iot
title: 地理路由GPSR在IoT传感器网络中的应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - energy-efficient-routing-wsn
  - flooding-vs-routing-mesh-iot
tags:
- GPSR
- 地理路由
- 贪心转发
- 周边模式
- WSN
- 局部最小值
- 平面化
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 地理路由GPSR在IoT传感器网络中的应用

> **难度**：🔴 高级 | **领域**：路由协议 | **阅读时间**：约 22 分钟

## 日常类比

地理路由像「只知道目的地在东北、没有地铁图」：每到路口选更朝东北的路。贪心模式 = 能直走就直走；遇到墙（覆盖空洞）就沿墙绕——即 GPSR（Greedy Perimeter Stateless Routing）的周边模式。传统 AODV/RPL 像人手一本完整时刻表，节点多时表太大。

## 摘要

阐述 GPSR 贪心/周边双模式、RNG/GG 平面化与右手规则，对比拓扑路由的内存与扩展性，并讨论定位误差与 IoT 适用边界。路径长度、到达率等为仿真/案例量级，实网须复测[1][2][5]。

## 1 地理路由要点

节点需：自身位置、邻居位置（beacon）、目的位置（位置服务）。转发变为几何选择：选离目的更近的邻居。相对拓扑路由：

| 维度 | 地理路由（GPSR） | 拓扑路由（AODV/RPL） |
|------|------------------|----------------------|
| 路由表 | 不需要 | 需要，规模随 N 增 |
| 位置 | 必须 | 不必须 |
| 状态量 | 邻居表，约 O(度) | 可达目的表，约 O(N) |
| 空洞 | 周边模式处理 | 路由发现可绕开 |
| 室内 | 定位难则受限 | 更自然 |

## 2 GPSR 双模式

**贪心**：选使到目的欧氏距离最小的邻居；若无邻居比自己更近 → 局部最小值，切周边。

**周边**：在平面化图上用右手规则沿面边界绕行；当到达比进入周边时记录点 Lp 更接近目的的节点，切回贪心[1]。

「Stateless」指转发不依赖全局路由状态，只依赖包内目的坐标与本地邻居。

## 3 贪心示例

农田节点 A(0,0) → Sink(100,80)，A 到 Sink 距离约 128：

| 邻居 | 坐标 | 到 Sink 距离（约） |
|------|------|-------------------|
| B | (20,15) | 102 |
| C | (25,10) | 103 |
| D | (15,25) | 98 |

选 D。重复直至到达或遇空洞。

## 4 局部最小值与平面化

空洞、河流、稀疏部署会导致「所有邻居都更远」。周边模式前需平面化，避免交叉边破坏面遍历：

| 算法 | 规则直觉 | 边密度 |
|------|----------|--------|
| RNG（相对邻域图） | 有更近「中间人」则删边 | 较密 |
| GG（Gabriel 图） | 直径圆内有点则删边 | 更稀，RNG 子集 |

右手规则：相对来边逆时针扫第一条出边，沿面绕行[1][2]。

## 5 位置获取与误差

| 方式 | 特点 | 对 GPSR 风险 |
|------|------|--------------|
| GNSS/GPS | 户外可用，功耗与成本较高 | 室内不可用 |
| 锚点 + 测距 | 少锚点、多估算 | 误差累积 |
| RSSI 三角 | 实现易 | 多径下误差大 |
| DV-Hop | 均匀网较合适 | 非均匀拓扑偏差大 |

位置误差可致错选下一跳、环路或错误平面化。文献指出中等误差下性能可部分保持，但阈值与百分比勿跨场景照搬；应做本网灵敏度实验[3][4]。

缓解：距离容差、缩短 beacon、多次测距平均、环路检测回退。

## 6 IoT 优势与选型

邻居表通常远小于全网路由表，适合 RAM 紧张的 MCU；无洪泛路由发现，控制面主要是本地 beacon；拓扑变化随邻居更新自然适应[1][4]。

**倾向 GPSR**：大规模、户外可定位、节点可移动、内存极紧。
**倾向拓扑路由**：小规模、室内无可靠定位、链路质量与地理距离弱相关、有清晰汇聚树（如 RPL）。

## 7 变种

GEAR 在距离外加权剩余能量；组播地理路由在分叉点复制；3D（楼宇/水下/无人机）平面化与绕行更复杂[3][4]。

## 8 案例要点（农业传感）

大规模户外传感若 RAM 装不下全网表、且 GNSS 可用，GPSR 可避免路由发现洪泛；河道等空洞靠周边绕行。公开对比中 GPSR 内存远低于 AODV 类，到达率可能略低（空洞路径更长）——具体百分比依赖拓扑，仅作方向参考[1][5]。

## 9 局限、挑战与可改进方向

### 1. 定位依赖

**局限**：无可靠位置则贪心决策失真。
**改进**：混合锚点定位；室内改 RPL/AODV；或「地理启发 + 链路质量」联合度量。

### 2. 空洞绕行开销

**局限**：周边模式路径变长、延迟与能耗上升。
**改进**：部署时填洞或加中继；面路由变种（GOAFR+ 等）改善最坏情况[2]。

### 3. 「地理近 ≠ 链路好」

**局限**：障碍物使近邻丢包率高。
**改进**：邻居表过滤 RSSI/ETX；跨层选路。

### 4. Beacon 与移动性权衡

**局限**：beacon 过稀则邻居过时，过密则耗能。
**改进**：自适应 beacon；移动节点提高更新率。

## 参考文献

[1] B. Karp, H. T. Kung, "GPSR: Greedy Perimeter Stateless Routing for Wireless Networks," ACM MobiCom, 2000.
[2] F. Kuhn, R. Wattenhofer, A. Zollinger, "Worst-Case Optimal and Average-Case Efficient Geometric Ad-Hoc Routing," ACM MobiHoc, 2003.
[3] I. Stojmenovic, "Position-Based Routing in Ad Hoc Networks," IEEE Commun. Mag., 2002.
[4] M. Mauve, J. Widmer, H. Hartenstein, "A Survey on Position-Based Routing in Mobile Ad Hoc Networks," IEEE Network, 2001.
[5] H. Frey, I. Stojmenovic, "On Delivery Guarantees of Face and Combined Greedy-Face Routing," ACM MobiCom, 2006.
[6] Y. Yu, R. Govindan, D. Estrin, "Geographical and Energy Aware Routing (GEAR)," UCLA/CSD Technical Report, 2001.
[7] P. Bose et al., "Routing with Guaranteed Delivery in Ad Hoc Wireless Networks," Wireless Networks, 2001.
[8] B. Leong, B. Liskov, R. Morris, "Geographic Routing Without Planarization," NSDI, 2006.
[9] T. Melodia, D. Pompili, I. F. Akyildiz, "On the Interdependence of Distributed Topology Control and Geographical Routing in Ad Hoc and Sensor Networks," IEEE JSAC, 2005.
[10] A. Rao et al., "Geographic Routing Without Location Information," ACM MobiCom, 2003.
[11] IETF ROLL, "RPL: IPv6 Routing Protocol for Low-Power and Lossy Networks," RFC 6550, 2012.
[12] C. Perkins, E. Belding-Royer, S. Das, "Ad hoc On-Demand Distance Vector (AODV) Routing," RFC 3561, 2003.
