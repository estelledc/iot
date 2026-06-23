# IPv6/6LoWPAN/RPL：物联网 IP 化协议栈

> 难度：🟡 中级 | 预计阅读：35 分钟 | 最后更新：2025-06

## 摘要

"让每一个 IoT 设备都有一个 IP 地址"——这个愿景听起来简单，实现起来却充满挑战。IPv6 提供了足够的地址空间（2^128 个地址），但 IPv6 的报头（40 字节）对于 IEEE 802.15.4（最大帧 127 字节）来说太大了。6LoWPAN 通过头部压缩和分片解决了这个问题，RPL 则为低功耗有损网络提供了 IPv6 路由能力。本文系统介绍 IPv6 在 IoT 中的适配技术栈——从 6LoWPAN 头部压缩到 RPL 路由协议再到 Thread 商业实现——并讨论性能、能耗和标准化现状。

**关键词**：IPv6；6LoWPAN；RPL；Thread；DODAG；IEEE 802.15.4；头部压缩

## 1 引言：为什么 IoT 需要 IPv6

想象每个 IoT 设备都是一户人家，IP 地址就是门牌号。IPv4 只有约 43 亿个地址——看起来不少，但全球仅智能手机就有 60 多亿部，加上路由器、服务器、IoT 设备，IPv4 地址早已不够用了。靠 NAT（网络地址转换）勉强维持，但 NAT 让设备之间直接通信变得困难。

IPv6 有 2^128 ≈ 3.4×10^38 个地址——这个数字大到给地球上每一粒沙子都分配一个地址还绰绰有余。每个 IoT 设备都可以拥有全球唯一的地址，实现真正的端到端通信，不再需要 NAT。

但 IPv6 不是"开箱即用"的。IPv6 报头最小 40 字节，而很多 IoT 设备使用的 IEEE 802.15.4 无线链路最大帧长只有 127 字节（减去 MAC 头和 FCS 后有效载荷约 81-102 字节）。如果直接把 IPv6 包塞进 802.15.4 帧，光报头就占了将近一半——留给实际数据的空间太少了。

这就是 6LoWPAN 和 RPL 存在的意义：6LoWPAN 把"胖"的 IPv6 报头压缩成"瘦"的几个字节，RPL 为这些低功耗、不可靠的无线链路设计了专用的路由协议。

## 2 IPv6 为 IoT 带来的关键能力

### 2.1 地址自动配置（SLAAC）

IPv6 的无状态地址自动配置（SLAAC，RFC 4862）让设备无需 DHCP 服务器就能获取全球唯一地址。设备根据路由器通告（Router Advertisement）中的网络前缀 + 自己的 MAC 地址（通过 EUI-64 扩展）自动生成 IPv6 地址。

对于 IoT 来说，这意味着设备"即插即用"——上电后自动获取地址，无需人工配置或 DHCP 服务器。在部署几千个传感器的场景中，这极大简化了部署流程。

### 2.2 IPsec 原生支持

IPv6 规范要求所有实现都支持 IPsec。虽然在受限设备上完整实现 IPsec 不现实，但 IPv6 的安全框架为端到端安全提供了基础。实际 IoT 部署中通常使用更轻量的 DTLS 或 OSCORE。

### 2.3 简化的报头

IPv6 的固定报头虽然比 IPv4（20-60 字节）更大（40 字节），但结构更规整——去掉了 IPv4 中的校验和（由上层协议负责）、分片（由源端负责）等字段，简化了路由器的处理逻辑。可选功能通过扩展头（Extension Header）实现，基本报头保持固定长度。

## 3 6LoWPAN：让 IPv6 适配低功耗无线

### 3.1 头部压缩（RFC 6282）

6LoWPAN（IPv6 over Low-Power Wireless Personal Area Networks）的核心任务是头部压缩。IPv6 报头（40 字节）+ UDP 报头（8 字节）= 48 字节，在 IEEE 802.15.4 的约 81-102 字节有效载荷中占比过高。

6LoWPAN 的 IPHC（IP Header Compression）利用了一个关键洞察：在同一个 WSN 中，大部分 IPv6 字段是可以推断的。例如源地址可以从 802.15.4 的 MAC 地址推导、Hop Limit 在局域网内通常是固定值、Flow Label 大多为 0。

压缩效果：

| IPv6 字段 | 原始大小(字节) | 压缩后(字节) | 压缩方式 |
|-----------|-------------|------------|---------|
| Version(4) + Traffic Class(8) + Flow Label(20) | 4 | 0-1 | 大多为0，可省略 |
| Payload Length | 2 | 0 | 从链路帧长度推导 |
| Next Header | 1 | 0-1 | 常见值(UDP/ICMPv6)用编码替代 |
| Hop Limit | 1 | 0-1 | 常见值(1/64/255)用2位编码 |
| Source Address | 16 | 0-8 | 从链路地址推导/上下文压缩 |
| Destination Address | 16 | 0-8 | 同上 |
| **IPv6 总计** | **40** | **2-7** | **压缩率 82-95%** |

UDP 头部（NHC 压缩）：源/目的端口如果在特定范围内（61616-61631），可以从 16 位压缩到 4 位。

最好情况下，IPv6 + UDP 的 48 字节头部可以压缩到 **6-7 字节**，压缩率高达 **85%**。这使得 IEEE 802.15.4 帧中留给有效载荷的空间从 34-54 字节增加到 75-96 字节。

### 3.2 分片与重组（RFC 4944）

即使经过头部压缩，有些 IPv6 数据包仍然可能超过 802.15.4 的 MTU（约 81-102 字节）。6LoWPAN 的分片机制将大包切成多个 802.15.4 帧传输：

- 第一个片段携带 Datagram Size（原始包大小）、Datagram Tag（标识符）和 Datagram Offset（偏移量=0）
- 后续片段携带 Tag + Offset

接收端根据 Tag 和 Offset 重组原始 IPv6 包。每个片段独立传输、独立确认——如果某个片段丢失，只需重传该片段。

分片的挑战是**可靠性**：如果一个 6 片的包丢了 1 片，整个包的其他 5 片都白传了。802.15.4 链路的丢包率可能高达 10-30%，分片越多，整个包的投递概率越低。2024 年 IETF 的 6lo 工作组提出了 Fragment Recovery 机制（draft-ietf-6lo-fragment-recovery），允许选择性重传丢失的片段，将分片包的投递率提升 **20-40%**。

### 3.3 网状寻址（Mesh Addressing）

6LoWPAN 还定义了网状头（Mesh Header），允许 6LoWPAN 帧在 802.15.4 网格网络中多跳转发，而不需要在每一跳都做 IPv6 层的路由决策。这降低了中间节点的处理开销。

## 4 RPL：低功耗有损网络的路由协议

### 4.1 概述

RPL（Routing Protocol for Low-Power and Lossy Networks，RFC 6550，2012）是 IETF ROLL 工作组为 LLN（Low-Power and Lossy Networks）设计的 IPv6 路由协议。LLN 的特点是：链路不可靠（丢包率高）、节点能量受限、拓扑动态变化。

RPL 构建的路由拓扑叫 DODAG（Destination Oriented Directed Acyclic Graph，面向目的地的有向无环图）——以汇聚节点（DODAG Root，通常是边界路由器）为根，所有节点形成一棵"树"，数据沿树向上流向根节点。

### 4.2 DODAG 构建过程

DODAG 的构建通过三种 ICMPv6 控制消息实现：

**DIO（DODAG Information Object）**：由 DODAG Root 周期性广播，携带 DODAG 信息（DODAG ID、版本号、Rank 等）。节点收到 DIO 后，根据目标函数计算自己的 Rank（在 DODAG 中的位置），选择最优的父节点加入 DODAG。

**DIS（DODAG Information Solicitation）**：节点主动请求 DIO 信息。新加入网络的节点发送 DIS 来快速发现附近的 DODAG。

**DAO（Destination Advertisement Object）**：子节点向父节点/根节点通告自己的存在和可达信息。DAO 使根节点了解整个 DODAG 的拓扑，支持"下行"通信（根 → 叶子节点）。

### 4.3 目标函数（Objective Function）

RPL 的灵活性体现在"目标函数"（Objective Function, OF）——它定义了节点如何选择父节点、如何计算 Rank。不同的 OF 可以针对不同的优化目标：

**OF0（RFC 6552）**：最简单的目标函数，Rank = 父节点 Rank + 固定增量。不考虑链路质量，只选最近的路径。

**MRHOF（Minimum Rank with Hysteresis Objective Function，RFC 6719）**：使用 ETX（Expected Transmission Count，预期传输次数）作为链路度量。ETX 考虑了链路的丢包率——ETX=1 表示完美链路，ETX=3 表示平均需要传 3 次才能成功一次。MRHOF 选择 ETX 总和最小的路径，并用迟滞（Hysteresis）防止频繁切换父节点。

| 目标函数 | 优化指标 | 优点 | 缺点 |
|----------|---------|------|------|
| OF0 | 跳数最少 | 简单、收敛快 | 不考虑链路质量和能量 |
| MRHOF(ETX) | 链路可靠性最高 | 丢包率最低 | 不考虑能量均衡 |
| 自定义OF(能量) | 能量均衡 | 延长网络寿命 | 需要能量信息交换 |
| 自定义OF(混合) | 多目标(ETX+能量+延迟) | 综合最优 | 计算复杂 |

### 4.4 RPL 模式

RPL 支持两种操作模式：

**Storing Mode**：每个节点维护路由表，支持节点间直接通信（不经过根节点）。内存开销大（每个节点要存路由表），适合资源较充裕的设备。

**Non-Storing Mode**：只有根节点维护完整路由表。下行数据必须先到根节点，根节点用 IPv6 源路由（Source Routing Header）指定完整路径。内存节省但增加了延迟和根节点负担。

## 5 Thread 协议

### 5.1 概述

Thread 是 Thread Group（成员包括 Google、Apple、Amazon、Samsung 等）推动的商业化 IoT 网络协议。它本质上是 6LoWPAN + RPL 的"工程化最佳实践"打包——在标准协议栈之上定义了具体的配置参数、安全方案和运维机制。

Thread 的协议栈：IEEE 802.15.4（物理层/MAC 层）→ 6LoWPAN（适配层）→ RPL（路由层，Non-Storing Mode）→ MLE（Mesh Link Establishment，链路建立）→ UDP/CoAP/DTLS（传输层/应用层）。

### 5.2 Thread 的关键特性

| 特性 | 说明 |
|------|------|
| 网络规模 | 最多约 250 个路由器 + 数百个终端设备 |
| 带宽 | 250 kbps (802.15.4) |
| 延迟 | 典型 30-100ms (多跳) |
| 安全 | DTLS 1.2 + 网络密钥 + 设备凭证 |
| 自愈 | 路由器故障后自动重新选择路径（RPL 特性） |
| 低功耗 | 终端设备(SED)可长期睡眠，轮询父节点获取数据 |
| 边界路由器 | Thread Border Router 连接 Thread 网络到 IP 网络 |
| 商业认证 | Thread Group 认证确保互操作性 |
| Matter 集成 | Thread 是 Matter 协议的两个底层网络之一（另一个是 Wi-Fi） |

### 5.3 Thread 与 Matter

Matter（前 Project CHIP）是 Connectivity Standards Alliance 推动的智能家居统一应用层协议。Matter 支持两种底层网络传输：Thread（IEEE 802.15.4）和 Wi-Fi（IEEE 802.11）。

Thread 与 Wi-Fi 在 Matter 中的分工：低功耗传感器和执行器（门锁、温控器、窗帘）使用 Thread——因为 802.15.4 的功耗远低于 Wi-Fi，适合电池设备；高带宽设备（摄像头、音箱、屏幕）使用 Wi-Fi——因为 Thread 的 250kbps 带宽不够。

Thread Border Router（如 Apple HomePod Mini、Google Nest Hub）同时连接 Thread 和 Wi-Fi/以太网，充当两个世界之间的桥梁。所有 Matter 设备通过 Thread Border Router 获得 IPv6 可达性，可以被云端或手机 App 直接访问。

2024 年 Matter 1.3 进一步完善了 Thread 的多 Border Router 支持和 Thread 1.3.1 集成。Thread 1.3.1 增加了对低功耗蓝牙（BLE）辅助配网和 DNS-SD 服务发现的改进。

## 6 性能评估

### 6.1 6LoWPAN 头部压缩效果

在实际部署中（Contiki-NG + CC2650 硬件），6LoWPAN 头部压缩的效果如下：

| 通信场景 | IPv6+UDP 原始(B) | 6LoWPAN 压缩后(B) | 压缩率 | 有效载荷增加 |
|----------|-----------------|------------------|--------|------------|
| 同一子网内通信 | 48 | 7 | 85% | +41B |
| 跨子网通信(全局地址) | 48 | 15 | 69% | +33B |
| 含扩展头(RPL HbH) | 56 | 11-19 | 66-80% | +37-45B |

### 6.2 RPL 收敛与能耗

| 指标 | RPL(MRHOF/ETX) | RPL(OF0) | 静态路由 |
|------|---------------|----------|---------|
| 拓扑收敛时间(50节点) | 30-60s | 10-20s | 0(预配置) |
| 控制消息开销(占比) | 5-15% | 3-8% | 0% |
| 链路故障修复时间 | 2-10s | 5-20s | 不支持 |
| 数据投递率(10%丢包链路) | 95-98% | 88-93% | 70-85% |
| 网络寿命(相对) | 1.0x | 0.8-0.9x | 1.1x(无控制开销) |

RPL 的 Trickle Timer 机制是控制开销的关键：网络稳定时，DIO 发送间隔指数增长（最长可达数分钟）；检测到拓扑变化时，间隔重置为最小值（快速传播更新）。这种自适应机制在稳定网络中几乎不产生控制开销。

### 6.3 与其他 IoT 路由协议的对比

| 协议 | 标准化 | 目标网络 | IPv6 支持 | 多跳 | 自愈 | 能耗 |
|------|--------|---------|-----------|------|------|------|
| RPL | IETF RFC 6550 | LLN(802.15.4) | 原生 | 是 | 是(DODAG重建) | 中 |
| AODV(改) | IETF RFC 3561 | Ad-hoc | 可(需适配) | 是 | 是(路由发现) | 高(泛洪) |
| LOAD | Zigbee | 802.15.4 | 否(ZigBee专用) | 是 | 部分 | 中 |
| CTP | TinyOS | WSN | 否 | 是 | 是 | 低 |
| Thread(RPL) | Thread Group | 802.15.4 | 原生 | 是 | 是 | 低(优化实现) |

## 7 部署现实与挑战

### 7.1 碎片化

虽然 6LoWPAN/RPL 是 IETF 标准，但实际部署中存在碎片化问题：不同的协议栈实现（Contiki-NG、Zephyr、RIOT、OpenThread）之间的互操作性并不完美。RPL 的 Storing Mode 和 Non-Storing Mode 之间不兼容，不同的目标函数之间也没有统一的交互方式。

### 7.2 RPL 在大规模网络中的可扩展性

RPL 在超过 200-300 个节点的网络中可能出现性能问题：DODAG 层数增加导致延迟上升（每跳约 10-50ms），控制消息开销随节点数增长。2024 年的研究建议在大规模部署中使用多个 DODAG Root（多实例 RPL）来分区管理。

### 7.3 安全

RPL 规范（RFC 6550）定义了三种安全模式——不安全（Unsecured）、预共享密钥（Preinstalled）和已认证（Authenticated），但大多数 RPL 实现默认使用不安全模式。已知的 RPL 攻击包括版本号攻击（恶意节点增大 DODAG 版本号导致全网重建）、黑洞攻击（节点声称自己 Rank 很低吸引流量然后丢弃）等。

Thread 在 RPL 之上增加了强制的 DTLS 安全和网络密钥管理，是目前安全性最好的 6LoWPAN/RPL 部署方案。

## 8 2024-2025 年前沿

**6LoWPAN Fragment Recovery（IETF draft）**：选择性重传丢失的 6LoWPAN 片段，提升分片包的可靠性。

**RPL-Lite（Contiki-NG）**：精简版 RPL 实现，RAM 占用从约 8KB 降至约 3KB，去掉了不常用的功能（如多实例、安全模式）。

**Thread 1.3.1 / 1.4.0**：增强的多 Border Router 支持、改进的设备配网流程、与 Matter 更紧密的集成。

**SCHC + 6LoWPAN**：SCHC（Static Context Header Compression）进一步压缩 IPv6/UDP/CoAP 头部，在 LPWAN（LoRaWAN、NB-IoT）场景中将总头部压缩到 1-5 字节。SCHC 被设计为 6LoWPAN 在 LPWAN 中的对应方案。

**IPv6 over BLE（RFC 7668 / Bluetooth Mesh）**：6LoWPAN 的 BLE 适配层允许 BLE 设备加入 IPv6 网络。随着 Bluetooth 5.x 和 Bluetooth Mesh 的普及，IPv6-over-BLE 在智能家居和可穿戴设备中的应用日益增多。

## 9 总结

IPv6/6LoWPAN/RPL 协议栈是 IoT 设备融入全球 IP 互联网的标准路径。6LoWPAN 通过 82-95% 的头部压缩率解决了 IPv6 与 802.15.4 之间的"尺寸不匹配"问题，RPL 通过 DODAG 拓扑和可插拔的目标函数为低功耗有损网络提供了灵活的路由能力。Thread 将这些标准协议工程化，提供了"开箱即用"的商业解决方案。

在智能家居领域，Thread + Matter 正在成为事实标准——2024 年所有主要智能家居平台（Apple HomeKit、Google Home、Amazon Alexa、Samsung SmartThings）都支持 Thread/Matter。在工业和基础设施领域，6LoWPAN/RPL 通过 Wi-SUN 等行业 Profile 在智能电网、智慧城市中持续扩展部署。

对于 IoT 开发者来说，理解 6LoWPAN 的头部压缩原理和 RPL 的 DODAG 路由机制是进入低功耗 IoT 网络领域的必备知识。而 Thread/Matter 作为"最佳实践"的打包方案，是当前智能家居项目的首选网络技术。

## 参考文献

1. Kushalnagar, N., et al. "IPv6 over Low-Power Wireless Personal Area Networks (6LoWPANs): Overview, Assumptions, Problem Statement, and Goals." RFC 4919, IETF, 2007.
2. Hui, J., Thubert, P. "Compression Format for IPv6 Datagrams over IEEE 802.15.4-Based Networks." RFC 6282, IETF, 2011.
3. Winter, T., et al. "RPL: IPv6 Routing Protocol for Low-Power and Lossy Networks." RFC 6550, IETF, 2012.
4. Thubert, P. "Objective Function Zero for the Routing Protocol for Low-Power and Lossy Networks (RPL)." RFC 6552, IETF, 2012.
5. Gnawali, O., Levis, P. "The Minimum Rank with Hysteresis Objective Function." RFC 6719, IETF, 2012.
6. Thread Group. "Thread Specification v1.3.1." Thread Group, 2024.
7. Connectivity Standards Alliance. "Matter 1.3 Specification." CSA, 2024.
8. Bormann, C., et al. "Terminology for Constrained-Node Networks." RFC 7228, IETF, 2014.
9. Watteyne, T., et al. "Industrial IEEE802.15.4e Networks: Performance and Trade-offs." IEEE ICC, 2015.
10. Kim, H., et al. "RPL Routing Pathology in a Network with a Mix of Nodes Operating in Storing and Non-Storing Modes." IETF Internet-Draft, 2024.