# IoT 应用层协议全面对比：MQTT vs CoAP vs LwM2M vs AMQP vs HTTP

> 难度：🟡 中级 | 预计阅读：35 分钟 | 最后更新：2025-06

## 摘要

物联网应用层协议是设备与云端"对话"的语言。面对 MQTT、CoAP、LwM2M、AMQP、HTTP 等多种选择，工程师常常困惑于"该用哪个"。本文从架构模型、报文开销、QoS 机制、传输层绑定四个维度进行系统对比，结合具体场景给出选型指南，并附带定量性能数据。目标是让读者建立一个清晰的决策框架：看到需求就能快速判断用什么协议。

**关键词**：MQTT；CoAP；LwM2M；AMQP；HTTP；应用层协议；IoT 协议选型

## 1 引言：为什么不能全用 HTTP？

在传统 Web 开发中，HTTP 是绝对的王者——浏览器和服务器之间几乎所有通信都走 HTTP。那么 IoT 设备为什么不能也都用 HTTP 呢？

打个比方：HTTP 就像寄快递用的标准纸箱，结实、通用，但箱子本身就有一定重量和体积。寄一台电视用这种箱子很合适，但如果你要寄一颗药丸，纸箱的重量可能比药丸还重——这就是 IoT 设备面临的窘境。一个温度传感器每次只发 2 字节的温度值，但 HTTP 请求头可能就有 500-800 字节，报头比数据大几百倍，这在电池供电、低带宽的场景下完全不可接受。

更关键的是，HTTP 是"请求-响应"模式：客户端问一次，服务器答一次。但很多 IoT 场景需要的是"发布-订阅"模式——传感器有新数据就推出去，谁感兴趣谁就收。HTTP 天生不擅长这个。虽然 HTTP/2 的 Server Push 和 WebSocket 部分弥补了这一缺陷，但它们引入了额外的复杂性和开销。

这就是为什么 IoT 世界需要专门的应用层协议。

## 2 五大协议概览

### 2.1 MQTT — 发布/订阅的标杆

MQTT（Message Queuing Telemetry Transport）由 IBM 的 Andy Stanford-Clark 和 Arlen Nipper 于 1999 年设计，最初用于石油管道的卫星遥测。它的设计哲学是"极简"：最小的报文开销、最少的网络带宽、能在不稳定网络中可靠工作。

核心架构是"发布/订阅"（Pub/Sub）：发布者（Publisher）把消息发到一个"主题"（Topic），代理服务器（Broker）负责把消息转发给所有订阅了这个主题的接收者（Subscriber）。发布者和订阅者完全解耦——发布者不需要知道谁在听，订阅者不需要知道谁在说。

MQTT 的固定头部只有 2 字节，是所有主流 IoT 协议中最精简的。它运行在 TCP 之上，提供三个级别的 QoS：QoS 0（最多一次）、QoS 1（至少一次）、QoS 2（恰好一次）。2019 年发布的 MQTT 5.0 引入了共享订阅、消息过期、主题别名、用户属性等重要特性。

### 2.2 CoAP — 受限设备的 REST

CoAP（Constrained Application Protocol）由 IETF CoRE 工作组设计（RFC 7252，2014），专门面向资源受限的设备。它的设计理念是"把 HTTP 的 RESTful 模型搬到受限网络中"。

CoAP 运行在 UDP 之上（而非 TCP），报头只有 4 字节。它支持 GET/PUT/POST/DELETE 四种方法，和 HTTP 一一对应，但去掉了 HTTP 中冗余的文本头部。CoAP 还有一个 HTTP 没有的"Observe"机制——客户端注册观察某个资源后，服务器会在资源变化时主动推送更新，类似轻量级的发布/订阅。

CoAP 的另一个特色是"代理友好"：可以很容易地在 CoAP 和 HTTP 之间做协议转换，让受限设备通过 CoAP 网关无缝接入 HTTP 世界。

### 2.3 LwM2M — 设备管理专家

LwM2M（Lightweight M2M）由 OMA SpecWorks 定义，建立在 CoAP 之上，专注于设备管理和服务赋能。如果说 MQTT 和 CoAP 解决的是"数据怎么传"，LwM2M 解决的是"设备怎么管"。

LwM2M 定义了完整的设备生命周期管理：引导（Bootstrap）——设备首次上线时获取配置；注册（Registration）——设备向服务器报告自己有哪些能力；设备管理（Device Management）——远程固件升级、参数配置、诊断；信息上报（Information Reporting）——周期性或事件触发的数据上报。

LwM2M 使用对象模型（Object Model）来描述设备能力。例如，Object 3 是设备信息（厂商、型号、序列号），Object 3303 是温度传感器，Object 3323 是压力传感器。IPSO Smart Objects 定义了一套标准的对象 ID，使不同厂商的设备可以互操作。

LwM2M 1.1 版本增加了对 TCP 和 MQTT 传输的支持，不再局限于 UDP/CoAP。LwM2M 1.2 版本（2022）进一步引入了复合操作（Composite Operations）和网关模式。

### 2.4 AMQP — 企业级消息中间件

AMQP（Advanced Message Queuing Protocol）最初由 J.P. Morgan 等金融机构推动（2003 年），后成为 OASIS 标准（2012），目前版本 1.0。它是企业级消息中间件的标准协议，RabbitMQ 和 Azure Service Bus 等都支持。

AMQP 的架构比 MQTT 复杂得多：引入了 Exchange（交换机）、Queue（队列）、Binding（绑定）等概念。消息先到 Exchange，再根据 Binding 规则路由到一个或多个 Queue，消费者从 Queue 中取消息。这种架构提供了强大的路由灵活性——可以做扇出（fanout）、直连（direct）、主题匹配（topic）、头部匹配（headers）等多种路由模式。

AMQP 运行在 TCP 之上，报头开销约 8 字节，支持事务和确认机制，保证消息的可靠传递。但它的协议复杂度和资源消耗远高于 MQTT 和 CoAP，更适合网关/边缘服务器级别的通信，而非直接部署在受限设备上。

### 2.5 HTTP/REST — 万能但笨重

HTTP 是 Web 的基石，凭借其广泛的生态和工具链支持，在 IoT 中也占有一席之地。特别是对于"数据量大但频率低"的场景（如固件下载、批量数据上传、配置管理），HTTP 仍然是最实用的选择。

HTTP/2（2015）和 HTTP/3（2022，基于 QUIC/UDP）显著改善了性能：HTTP/2 的头部压缩（HPACK）和多路复用减少了延迟和连接开销；HTTP/3 基于 UDP 的 QUIC 协议消除了 TCP 的队头阻塞问题。但即便如此，HTTP 的请求-响应模式、较大的头部开销（即使压缩后仍有数十字节）和 TLS 握手开销，使其在受限设备场景中仍不如 MQTT 和 CoAP 高效。

## 3 定量对比：报文开销与性能

### 3.1 报头开销与消息尺寸

协议的报头开销直接影响带宽利用率和能耗。以下数据综合了 RFC 规范和 2024 年的实测研究：

| 指标 | MQTT 3.1.1 | MQTT 5.0 | CoAP | LwM2M (CoAP) | AMQP 1.0 | HTTP/1.1 | HTTP/2 |
|------|-----------|----------|------|--------------|----------|----------|--------|
| 最小固定头部 (B) | 2 | 2 | 4 | 4 | 8 | ~200-800 | ~9 (帧头) |
| 典型请求开销 (B) | 14-20 | 16-30 | 10-20 | 15-30 | 60-100 | 500-1000 | 50-150 |
| 传输 2B 传感器数据的总消息大小 (B) | 16-22 | 18-32 | 12-22 | 17-32 | 62-102 | 502-1002 | 52-152 |
| 传输层 | TCP | TCP | UDP | UDP | TCP | TCP | TCP(QUIC) |
| TLS/DTLS 握手开销 (B) | ~6000-7000 | ~6000-7000 | ~1500-2500(DTLS) | ~1500-2500 | ~6000-7000 | ~6000-7000 | ~3000(0-RTT) |

从表中可以看出，传输一个 2 字节的温度值，CoAP 只需要 12-22 字节，而 HTTP/1.1 需要 500-1000 字节——差距高达 40-80 倍。这在电池供电设备中意味着能量消耗的巨大差异。

### 3.2 延迟与吞吐量

2024 年 Yokotani 等人的实测研究（IEEE Access，2024）和 Eclipse IoT Working Group 的基准测试提供了以下参考数据：

| 指标 | MQTT (QoS 0) | MQTT (QoS 1) | CoAP (NON) | CoAP (CON) | HTTP/1.1 | HTTP/2 |
|------|-------------|-------------|------------|------------|----------|--------|
| 单消息平均延迟 (ms) | 5-15 | 15-50 | 3-10 | 10-40 | 50-200 | 30-100 |
| 建立连接延迟 (ms) | 200-500(TCP+TLS) | 同左 | 0(无连接) | 0 | 200-500 | 100-200(0-RTT) |
| 持续发送吞吐量 (msg/s) | 5000-20000 | 2000-8000 | 3000-15000 | 1000-5000 | 500-2000 | 2000-8000 |
| 弱网环境(10%丢包)可靠性 | 高(TCP重传) | 高 | 中(需应用层ACK) | 高(CoAP重传) | 高(TCP) | 中高(QUIC) |

关键发现：CoAP 在单次请求场景下延迟最低（无需建连），但在持续大量消息推送场景下 MQTT 的吞吐量更优（TCP 连接复用 + 极简头部）。HTTP/1.1 在所有 IoT 相关指标上都处于劣势，HTTP/2 有所改善但仍逊于专用 IoT 协议。

## 4 QoS 机制深度对比

QoS（Quality of Service，服务质量）机制决定了"消息是否会丢"以及"丢了怎么办"。不同协议的 QoS 设计反映了它们的应用定位。

**MQTT** 的三级 QoS 是其标志性特性：QoS 0 是"发出去就不管了"（fire-and-forget），适合频繁发送的传感器数据，丢一条也无所谓；QoS 1 是"至少到一次"（at-least-once），通过 PUBACK 确认保证送达，但可能重复；QoS 2 是"恰好一次"（exactly-once），通过四步握手（PUBLISH → PUBREC → PUBREL → PUBCOMP）保证不丢不重，但开销最大。实际部署中 QoS 1 最常用，因为 QoS 2 的四步握手在高吞吐场景下会显著增加延迟。

**CoAP** 的可靠性通过消息类型实现：CON（Confirmable）消息会得到 ACK 确认，等价于 MQTT 的 QoS 1；NON（Non-confirmable）消息不确认，等价于 QoS 0。CoAP 没有 QoS 2 的等价物——这是有意为之的简化，因为受限设备通常没有足够资源维护四步握手的状态机。

**AMQP** 提供最强的消息保障：支持事务（Transaction）、消息持久化、死信队列（Dead Letter Queue）。消息可以在 Broker 端持久化到磁盘，即使 Broker 重启也不丢失。这使 AMQP 成为金融交易等高可靠性场景的首选，但也带来了更高的资源开销。

**LwM2M** 继承 CoAP 的 CON/NON 机制，并在其上增加了观察（Observe）模式的条件通知——可以设置阈值，只有当传感器值变化超过阈值时才上报，兼顾可靠性和节能。

| QoS 特性 | MQTT | CoAP | AMQP | LwM2M | HTTP |
|----------|------|------|------|-------|------|
| 消息确认 | QoS 1/2 | CON + ACK | 显式确认 | CON + ACK | 响应码 |
| 恰好一次 | QoS 2 | 不支持 | 事务 | 不支持 | 幂等性保证 |
| 消息持久化 | Broker 可配 | 不支持 | 原生支持 | 不支持 | 不适用 |
| 离线消息 | Retained + Session | 不支持 | 队列持久化 | 不支持 | 不适用 |
| 遗嘱消息 | 支持(Will) | 不支持 | 不支持 | 不支持 | 不适用 |
| 消息排序 | 每主题有序 | 无保证 | 队列内有序 | 无保证 | 无保证 |

## 5 传输层绑定：TCP vs UDP vs QUIC

应用层协议的选择与其底层传输协议密不可分。

**TCP 系（MQTT、AMQP、HTTP/1.1-2）**：TCP 提供可靠、有序的字节流传输，但代价是三次握手建连延迟（1.5 RTT）和队头阻塞（一个丢包会阻塞后续所有数据）。对于长连接场景（设备保持常在线），TCP 的建连开销可以摊薄；但对于"发一条就走"的场景，每次重新建连的开销很大。MQTT 通过 Keep Alive 机制维持长连接，减少重连频率。

**UDP 系（CoAP、LwM2M）**：UDP 是无连接的，没有建连延迟和队头阻塞。但 UDP 不保证可靠性和顺序，需要应用层自己处理（CoAP 的 CON/ACK 机制就是在做这件事）。UDP 在 NAT 穿越方面也有挑战——NAT 映射超时后需要重新建立。对于受限设备，UDP 的内存占用（无需维护连接状态）和计算开销远低于 TCP。

**QUIC（HTTP/3）**：QUIC 是 Google 开发的基于 UDP 的传输协议，综合了 TCP 的可靠性和 UDP 的低延迟优势。QUIC 支持 0-RTT 建连（对于曾经连过的服务器）、多路复用（无队头阻塞）、内建加密。MQTT-over-QUIC 是近年来的热门研究方向——EMQX 5.0 已经实验性支持。2024 年的研究表明，MQTT-over-QUIC 在弱网环境下的消息延迟比 MQTT-over-TCP 降低 30-50%，且连接恢复时间从秒级降至毫秒级。

## 6 协议选型决策指南

选择协议不应该从"哪个最好"出发，而应该从"我的场景需要什么"出发。以下是一个实用的决策框架：

**设备资源**：如果设备只有几 KB RAM 和几十 KB Flash（如 Class 0/1 受限设备），CoAP/LwM2M 是唯一选择，因为 TCP 协议栈本身就可能占用 10-20 KB RAM。如果设备有 100 KB 以上 RAM，MQTT 是首选。如果在网关/服务器级别，AMQP 提供最强的路由和可靠性保证。

**通信模式**：需要发布/订阅模型→MQTT；需要 RESTful 请求/响应→CoAP；需要设备生命周期管理→LwM2M；需要复杂消息路由→AMQP。

**网络条件**：高丢包率、频繁断连的环境→MQTT（QoS 1/2 + 遗嘱消息 + 持久会话）最佳；低带宽卫星链路→CoAP（UDP + 极简报头）最佳；稳定的企业局域网→AMQP 或 HTTP/2 均可。

**数据模式**：高频小数据（每秒几十到上百条）→MQTT QoS 0；低频大数据（固件下载、批量上传）→HTTP/2 或 CoAP 块传输；需要双向设备管理→LwM2M。

| 应用场景 | 推荐协议 | 理由 |
|----------|----------|------|
| 智能家居传感器（温湿度、门窗） | MQTT QoS 0/1 | 数据量小、频率适中、需要实时推送 |
| 工业传感器集群（几千节点） | MQTT 5.0 | 共享订阅做负载均衡、主题别名降开销 |
| 智能电表远程抄表 | LwM2M | 需要设备管理+数据上报，运营商级部署 |
| 受限传感器（LPWAN接入） | CoAP + LwM2M | RAM<10KB，无法跑 TCP 栈 |
| 车联网 V2X | MQTT 5.0 / DDS | 低延迟推送 + 高吞吐 |
| 企业 IT/OT 融合网关 | AMQP / MQTT 桥接 | 需要可靠消息路由、与企业 MQ 对接 |
| 移动 App 与设备交互 | HTTP/2 + WebSocket | 利用现有 Web 生态和 CDN |
| 固件 OTA 升级 | HTTP/2 或 CoAP Block | 大文件分块传输 + 断点续传 |

## 7 混合架构：多协议共存的现实

实际的 IoT 系统很少只用一种协议。一个典型的智慧工厂可能同时使用：CoAP/LwM2M 连接末端传感器 → MQTT 在边缘网关做数据汇聚和转发 → AMQP/Kafka 在云端做消息队列 → HTTP/gRPC 提供 API 给应用层。

协议网关（Protocol Gateway）是多协议共存的关键组件。开源项目如 Eclipse Kura、ThingsBoard 和 AWS IoT Core 都提供了多协议接入能力。2024 年的趋势是将协议转换下沉到边缘：边缘网关将异构的设备协议统一转换为 MQTT 或 gRPC，再上传到云端，减少了云端的协议适配复杂度。

值得一提的是 **DDS（Data Distribution Service）** ——一种面向实时数据分发的中间件标准。DDS 在自动驾驶（ROS 2 的默认通信层）和国防领域广泛使用，提供细粒度的 QoS 策略（截止时间、可靠性、持久性等 20+ 种），以及基于 RTPS（Real-Time Publish-Subscribe）协议的去中心化发现和数据分发。DDS 与 MQTT 的定位不同：MQTT 依赖中心化 Broker，适合"设备到云"的南向通信；DDS 是去中心化的，更适合"设备到设备"的横向通信。OMG（Object Management Group）已发布 DDS-MQTT Bridge 规范，允许两者互通。

## 8 2024-2025 年前沿动态

**MQTT-over-QUIC**：EMQX 5.x 和 NanoMQ 已实验性支持 MQTT-over-QUIC。2024 年 IEEE IoT Journal 的研究表明，QUIC 的 0-RTT 连接恢复和多路复用特性特别适合移动 IoT 设备（如车载终端），可将高速移动场景下的消息投递成功率从 TCP 的 85% 提升至 98%。

**Sparkplug B**：Eclipse 基金会推动的 MQTT 互操作性规范，定义了工业 IoT 场景下的 MQTT 主题命名空间、有效载荷编码（Protobuf）和状态管理语义。Sparkplug 3.0 于 2022 年发布，2024 年已被多家工业自动化厂商采纳。

**CoAP over TCP/WebSocket**（RFC 8323）：允许 CoAP 运行在 TCP 或 WebSocket 之上，解决 NAT 穿越问题，使 CoAP 可以用于需要持久连接的场景。

**Matter over Thread/Wi-Fi**：智能家居统一标准 Matter 在应用层采用了基于 UDP 的消息可靠性层（MRP），而非直接使用 CoAP 或 MQTT。Matter 的出现可能重新定义智能家居设备的协议格局。

## 9 总结

IoT 应用层协议的选择本质上是一个"trade-off 三角"——在**资源开销**、**功能丰富性**、**生态成熟度**三者之间做平衡。MQTT 以其简洁高效和庞大的生态稳居 IoT 应用层协议的主导地位，CoAP/LwM2M 在受限设备领域不可替代，AMQP 守住企业级消息路由的阵地，HTTP 凭借 Web 生态的惯性仍不可忽视。

未来的趋势是"协议融合"：MQTT-over-QUIC 模糊了 TCP/UDP 的边界，LwM2M 支持 MQTT 传输模糊了设备管理/数据传输的边界，Sparkplug B 在 MQTT 之上叠加了工业互操作语义。工程师需要理解的不是"一个最好的协议"，而是一个"多协议协同的架构"。

## 参考文献

1. OASIS. MQTT Version 5.0 (OASIS Standard), 2019.
2. Shelby, Z., et al. The Constrained Application Protocol (CoAP). RFC 7252, IETF, 2014.
3. OMA SpecWorks. Lightweight M2M Technical Specification v1.2, 2022.
4. OASIS. AMQP Version 1.0 (OASIS Standard), 2012.
5. Yokotani, T., et al. "Performance Comparison of IoT Protocols: MQTT, CoAP and HTTP." IEEE Access, 2024.
6. Eclipse IoT Working Group. "IoT Developer Survey 2024." Eclipse Foundation, 2024.
7. Banno, R., et al. "MQTT over QUIC: Leveraging Modern Transport for IoT Communication." IEEE Internet of Things Journal, 2024.
8. Naik, N. "Choice of Effective Messaging Protocols for IoT Systems: MQTT, CoAP, AMQP and HTTP." IEEE Systems Journal, 2017.
9. Thangavel, D., et al. "Performance evaluation of MQTT and CoAP via a common middleware." IEEE ISSNIP, 2014.
10. Eclipse Sparkplug Working Group. Sparkplug Specification v3.0, 2022.
11. Connectivity Standards Alliance. Matter 1.0 Specification, 2022.
12. Betzler, A., et al. "CoAP over TCP, TLS, and WebSockets." RFC 8323, IETF, 2018.
