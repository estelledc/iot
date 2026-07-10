---
schema_version: '1.0'
id: iot-app-protocols
title: IoT 应用层协议全面对比：MQTT vs CoAP vs LwM2M vs AMQP vs HTTP
layer: 3
content_type: comparison
difficulty: intermediate
reading_time: 28
prerequisites:
  - mqtt5-deep-dive
  - coap-lwm2m-constrained
tags:
  - MQTT
  - CoAP
  - LwM2M
  - AMQP
  - HTTP
  - 应用层协议
  - 协议选型
  - QoS
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT 应用层协议全面对比：MQTT vs CoAP vs LwM2M vs AMQP vs HTTP

> **难度**：🟡 中级 | **领域**：应用层协议、选型 | **阅读时间**：约 28 分钟

## 日常类比

超文本传输协议（Hypertext Transfer Protocol, HTTP）像标准纸箱：结实通用，但箱子本身有重量。寄电视合适；寄一颗“药丸”（几字节温湿度）时，纸箱可能比货还重。物联网（Internet of Things, IoT）才需要更“薄”的信封：消息队列遥测传输（Message Queuing Telemetry Transport, MQTT）、受限应用协议（Constrained Application Protocol, CoAP）等[8][9]。

## 摘要

从架构模型、报头开销、服务质量（Quality of Service, QoS）、传输绑定与场景选型对比 MQTT、CoAP、轻量机器到机器（Lightweight M2M, LwM2M）、高级消息队列协议（Advanced Message Queuing Protocol, AMQP）与 HTTP。延迟/吞吐表为文献与基准的**量级示意**，测量拓扑不同不可横比硬 SLA[5][6][9]。

## 1 为何不能全用 HTTP

HTTP 请求-响应与偏大的头部，对电池与低带宽不友好；发布/订阅也非其长项。HTTP/2、HTTP/3（基于 QUIC）改善了多路与握手，但受限终端上仍常逊于专用 IoT 协议[5][8]。

## 2 五协议速览

| 协议 | 模型 | 典型传输 | 定位 |
|------|------|----------|------|
| MQTT | 发布/订阅 + Broker | TCP（亦有 QUIC 实验） | 设备到云遥测主流 |
| CoAP | REST 风格 + Observe | UDP（可 TCP/WebSocket） | 受限设备、易 HTTP 映射 |
| LwM2M | 对象模型 + 生命周期 | 常基于 CoAP | 运营商级设备管理 |
| AMQP | Exchange/Queue/Binding | TCP | 企业可靠路由 |
| HTTP | 请求/响应 | TCP / QUIC | 大文件、管理 API、Web 生态 |

- **MQTT**：固定头可小至 2 字节量级；QoS 0/1/2；5.0 含共享订阅、消息过期、主题别名等[1]。
- **CoAP**：约 4 字节固定头；CON/NON；与 HTTP 语义接近，便于代理[2][12]。
- **LwM2M**：Bootstrap/注册/管理/上报；IPSO 对象；1.1+ 可绑 TCP/MQTT 等[3]。
- **AMQP**：路由强、可持久化与事务；资源开销高于 MQTT/CoAP，多在网关/服务器侧[4]。
- **HTTP**：工具链最全；低频大数据仍实用[8]。

## 3 开销与性能（量级）

### 3.1 报头与小载荷

| 指标 | MQTT | CoAP | AMQP 1.0 | HTTP/1.1 | HTTP/2 |
|------|------|------|----------|----------|--------|
| 最小固定头（B，量级） | ~2 | ~4 | ~8 | 数百级文本头 | 帧头更小但仍有头压缩态 |
| 传 2B 传感值总大小（量级） | 十余～数十 | 十余～数十 | 数十～百 | 数百～千 | 数十～百（视头表） |
| 传输层 | TCP | UDP 为主 | TCP | TCP | TCP/QUIC |

“差几十倍”只在特定小载荷对比中成立；加密握手、主题字符串、JSON 封装会显著抬高实际字节数[5][9]。

### 3.2 延迟与吞吐倾向

| 倾向 | 更常见观察 |
|------|------------|
| 单次请求、无长连接 | CoAP（UDP）建连成本低 |
| 持续高频小消息 | MQTT 长连接 + 极简头更占优 |
| 弱网可靠投递 | MQTT QoS1/2 或 CoAP CON；依赖实现与重传参数 |
| 通用 Web/CDN | HTTP/2 或 HTTP/3 |

具体 ms 与 msg/s 随 Broker、硬件、TLS、QoS 剧烈变化，表意在机制而非绝对值[5][6]。

## 4 QoS 机制对比

| 特性 | MQTT | CoAP | AMQP | LwM2M | HTTP |
|------|------|------|------|-------|------|
| 确认 | QoS 1/2 | CON+ACK | 显式确认 | 继承 CoAP | 响应码 |
| 恰好一次 | QoS 2 | 无对等 | 事务等 | 无对等 | 靠幂等设计 |
| 持久化 | Broker 可配 | 通常无 | 原生强 | 通常无 | 不适用 |
| 离线/遗嘱 | Session / Will | 弱 | 队列 | 弱 | 弱 |

实践中 MQTT QoS 1 最常用：QoS 2 四次握手在高吞吐下成本高[1][9]。

## 5 传输绑定：TCP / UDP / QUIC

- **TCP 系（MQTT、AMQP、HTTP/1.1–2）**：可靠有序，有握手与队头阻塞；长连接可摊薄建连成本。
- **UDP 系（CoAP、经典 LwM2M）**：无连接，可靠性上移到应用；NAT 存活需应用保活。
- **QUIC（HTTP/3，MQTT-over-QUIC 实验）**：0-RTT、多路无 TCP 式队头阻塞；移动弱网叙事积极，端侧栈与中间盒仍是部署变量[7]。

## 6 选型框架

| 场景 | 更常推荐 | 理由（机制） |
|------|----------|--------------|
| 家居传感 | MQTT QoS 0/1 | 小消息、推送、生态成熟 |
| 工业大规模遥测 | MQTT 5.0 | 共享订阅、主题别名 |
| 运营商电表/管理 | LwM2M | 生命周期 + 对象模型 |
| Class 0/1 受限节点 | CoAP / LwM2M | 难扛完整 TCP 栈 |
| IT/OT 企业总线 | AMQP 或桥接 | 路由与持久化 |
| OTA / 大文件 | HTTP/2 或 CoAP Block | 分块与工具链 |

资源：极小 RAM 优先 CoAP 系；网关级才优先 AMQP。模式：Pub/Sub→MQTT；REST→CoAP；管设备→LwM2M[3][8]。

## 7 多协议共存

现实架构常为：末端 CoAP/LwM2M → 边缘汇聚 MQTT → 云侧 AMQP/Kafka → 应用 HTTP/gRPC。协议网关与 Sparkplug、DDS-MQTT Bridge 等补齐互操作；数据分发服务（Data Distribution Service, DDS）更偏去中心实时横向，与 MQTT 中心化南向互补[10][11]。

## 8 局限、挑战与可改进方向

### 1. 基准不可横比

**局限**：公开延迟/吞吐表混合实验室拓扑、是否含 TLS、不同 QoS，易被误当成通用排名。
**改进**：固定载荷、丢包、TLS、硬件后复测；选型写清测量口径[5][9]。

### 2. “一个协议打天下”

**局限**：设备管理、遥测、文件、人机 API 需求冲突，单协议要么过重要么缺能力。
**改进**：按平面拆协议 + 边缘归一；用 LwM2M/MQTT 分工而非互相替代[3][6]。

### 3. 安全与中间盒

**局限**：UDP/DTLS、QUIC 穿越与证书生命周期在现场常比选协议本身更痛。
**改进**：先验证 NAT/防火墙路径；证书轮换与时钟同步纳入验收；必要时 CoAP over TCP/WebSocket[12]。

### 4. 语义互操作

**局限**：MQTT 只保证管道，主题与载荷混乱导致多厂商无法协作。
**改进**：工业侧评估 Sparkplug 等；管理侧用 LwM2M 对象；Schema 与版本策略与网关篇对齐[10]。

## 9 总结

选型是资源开销、功能、生态的权衡，不是找“冠军协议”。MQTT 主导设备到云遥测，CoAP/LwM2M 守住受限与管理，AMQP 守企业路由，HTTP 守 Web 与大对象；用场景矩阵与同口径实测决策。

## 参考文献

[1] OASIS, "MQTT Version 5.0," OASIS Standard, 2019.

[2] Z. Shelby et al., "The Constrained Application Protocol (CoAP)," RFC 7252, IETF, 2014.

[3] OMA SpecWorks, "Lightweight M2M Technical Specification v1.2," 2022.

[4] OASIS, "AMQP Version 1.0," OASIS Standard, 2012.

[5] T. Yokotani et al., "Performance Comparison of IoT Protocols: MQTT, CoAP and HTTP," IEEE Access, 2024.

[6] Eclipse IoT Working Group, "IoT Developer Survey 2024," Eclipse Foundation, 2024.

[7] R. Banno et al., "MQTT over QUIC: Leveraging Modern Transport for IoT Communication," IEEE Internet of Things Journal, 2024.

[8] N. Naik, "Choice of Effective Messaging Protocols for IoT Systems," IEEE Systems Journal, 2017.

[9] D. Thangavel et al., "Performance evaluation of MQTT and CoAP via a common middleware," IEEE ISSNIP, 2014.

[10] Eclipse Sparkplug Working Group, "Sparkplug Specification v3.0," 2022.

[11] Connectivity Standards Alliance, "Matter Specification," 2022–.

[12] A. Betzler et al., "CoAP over TCP, TLS, and WebSockets," RFC 8323, IETF, 2018.

[13] OMG, "DDS-MQTT Bridge," Object Management Group, related specifications.
