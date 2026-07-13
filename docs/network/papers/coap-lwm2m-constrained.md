---
schema_version: '1.0'
id: coap-lwm2m-constrained
title: CoAP 与 LwM2M：受限设备的轻量协议栈
layer: 3
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - iot-app-protocols
  - ipv6-6lowpan-rpl
tags:
- CoAP
- LwM2M
- 受限设备
- DTLS
- OSCORE
- IPSO
- Observe
- NB-IoT
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# CoAP 与 LwM2M：受限设备的轻量协议栈

> **难度**：🟡 中级 | **领域**：受限设备、设备管理 | **阅读时间**：约 22 分钟

## 日常类比

给候鸟背的追踪器只有纽扣电池：TCP 三次握手、冗长 HTTP 头像每次报位置前先开一场短会。CoAP（Constrained Application Protocol）把「REST 语义」收成短二进制明信片，走 UDP；LwM2M（Lightweight Machine-to-Machine）则是在明信片之上的「设备户口本」——注册、读写下发、固件升级、观察上报都按标准对象填表。

## 摘要

按 RFC 7228 设备等级说明为何需要 CoAP；梳理消息层/Observe/Block、与 HTTP 对比，以及 LwM2M 接口与 IPSO 对象模型、DTLS/OSCORE。报文「约数十字节」为含 IP/UDP 头的量级示意，链路与选项不同会变[1][5][10]。

## 1 受限设备与协议动机

| 等级 (RFC 7228) | RAM / Flash 量级 | 能力印象 |
|-----------------|------------------|----------|
| Class 0 | ≪10KB / ≪100KB | 难直接跑完整 IP，常需代理 |
| Class 1 | ~10KB / ~100KB | 可跑受限 IP 栈（如 6LoWPAN+CoAP） |
| Class 2 | ~50KB / ~250KB | 完整 IP 更可行；TCP+MQTT 仍可能吃力 |

CoAP（RFC 7252）保留 GET/PUT/POST/DELETE 与 URI/状态码映射，固定头 4 字节，默认 UDP，安全侧常用 DTLS；目标是 Class 1 类节点[1][5]。

## 2 CoAP 设计要点

**消息层**：CON（需确认，指数退避重传）/ NON / ACK / RST。
**请求响应层**：方法与 2.xx/4.xx/5.xx 类响应码。
**Observe（RFC 7641）**：带 Observe 的 GET 建立观察，资源变化时推送——轻量「一对一推」，非 MQTT 式多对多 Broker[2]。
**Block（RFC 7959）**：大资源分块，适配 UDP/小 MTU，支持按块重传[3]。
**代理**：正向代理；跨协议代理（CoAP↔HTTP）是边缘常见落地[1]。

| 维度 | CoAP | HTTP/1.1 | HTTP/2 |
|------|------|----------|--------|
| 传输 | UDP（另有 TCP/WS 扩展） | TCP | TCP（H3 为 QUIC） |
| 头 | 二进制，固定 4B + Options | 文本，常数百字节级 | 二进制压缩 |
| 多播 | UDP 多播原生更自然 | 无 | 无 |
| 推送 | Observe | 需 SSE/WebSocket 等 | 曾有 Server Push |
| 安全 | DTLS / OSCORE | TLS | TLS |
| 发现 | `/.well-known/core` | 无统一等价 | 无 |
| NAT | UDP 映射超时更棘手 | 长连接相对稳 | 相对稳 |

CoAP over TCP/WebSocket（RFC 8323）改善 NAT，但加重栈，需权衡「轻量初衷」[8]。

## 3 LwM2M 架构

实体：Client（设备）、Server（管理/数据）、Bootstrap Server（首配地址与凭证）[4]。

| 接口 | 作用 |
|------|------|
| Bootstrap | 出厂/智能卡/客户端或服务器发起引导 |
| Registration | 注册 Endpoint 与对象能力，Lifetime 续约 |
| Management & Service | Read/Write/Execute/Create/Delete/Discover；含 FOTA |
| Information Reporting | Observe/Notify；1.1+ 复合观察 |

对象模型：`/{ObjectID}/{InstanceID}/{ResourceID}`。例：`/3303/0/5700` 为温度实例 0 的当前值。IPSO/OMA 对象（Device=3、Firmware=5、Temperature=3303 等）支撑多厂商互操作[4][9]。

| 特性 | 1.0 | 1.1 | 1.2 |
|------|-----|-----|-----|
| 传输 | CoAP/UDP 为主 | + TCP/MQTT 等 | + HTTP 等扩展 |
| 复合读写/观察 | 弱 | 增强 | 继续增强 |
| 网关代表子设备 | 无 | 无 | Gateway 相关能力 |
| 安全 | DTLS PSK/RPK/Cert | + OSCORE | + EST 等证书自动化方向 |

## 4 安全：DTLS 与 OSCORE

| 模式 | 特点 | 适用印象 |
|------|------|----------|
| PSK | 握手轻，密钥分发/轮换难 | 大批量电表等 |
| RPK | 非对称无完整 X.509 | 中等安全、省 PKI |
| Certificate | PKI 最完整，证书体积与校验更重 | 网关/Class 2+ |
| OSCORE (RFC 8613) | 对象级保护，经代理仍可端到端 | 多跳/代理场景[6] |

「OSCORE 比 DTLS 省一半量级」类说法依赖配置与实现，选型以目标板上握手字节与 RAM 实测为准[6][7]。

## 5 实现与部署

| 角色 | 实现 | 备注 |
|------|------|------|
| Server | Eclipse Leshan | Java，参考实现较全 |
| Client/Server C | Eclipse Wakaama | 嵌入式常见 |
| 商业平台 | 如 AVSystem Coiote 等 | 大规模运维能力 |
| 纯 CoAP | libcoap、Californium | 与 LwM2M 可组合 |
| RTOS | Zephyr LwM2M | 与网络栈集成 |

智能电表/资产追踪：NB-IoT 或 LTE-M 上 CoAP/LwM2M，Queue Mode 适合长睡短醒；OTA 走 Object 5。单次上报「整包约几十字节」为常见公开描述量级，非保证上限[10]。

前沿方向：CoAP over QUIC 草案、SCHC（RFC 8724）把头压到极少数字节级以适配 LPWAN、对象模型与数字孪生对齐——均以标准进展为准[7]。

## 6 局限、挑战与可改进方向

### 1. NAT 与防火墙

**局限**：纯 UDP CoAP 在运营商 NAT 下映射易过期，下行难达[1][8]。
**改进**：Queue Mode/定期注册；必要时 RFC 8323；或边缘常驻代理。

### 2. Observe ≠ 总线级 Pub/Sub

**局限**：一对一观察难直接替代 MQTT 百万级扇出与共享订阅。
**改进**：扇出放 Broker/网关；设备侧保持 Observe 或周期 Notify。

### 3. 安全运维成本

**局限**：全局 PSK 泄露面大；证书对 Class 1 过重；OSCORE 生态仍不均[4][6]。
**改进**：一机一钥；Bootstrap+EST 自动化；代理场景优先评估 OSCORE。

### 4. 对象模型碎片

**局限**：私有 Object ID 导致「同叫温度、语义不同」。
**改进**：优先标准 IPSO；私有对象文档化并做 Server 侧适配测试。

## 7 选型一句话

跑不起可靠 TCP 栈、要标准设备管理 → CoAP + LwM2M；资源充足、要 Brokers 生态与海量扇出 → MQTT（可经网关与 LwM2M 并存）。

## 参考文献

[1] Z. Shelby et al., "The Constrained Application Protocol (CoAP)," RFC 7252, 2014.
[2] K. Hartke, "Observing Resources in the CoAP," RFC 7641, 2015.
[3] C. Bormann, Z. Shelby, "Block-Wise Transfers in the CoAP," RFC 7959, 2016.
[4] OMA SpecWorks, "Lightweight Machine to Machine Technical Specification," v1.2, 2022.
[5] C. Bormann et al., "Terminology for Constrained-Node Networks," RFC 7228, 2014.
[6] G. Selander et al., "Object Security for Constrained RESTful Environments (OSCORE)," RFC 8613, 2019.
[7] A. Minaburo et al., "SCHC: Static Context Header Compression," RFC 8724, 2020.
[8] C. Bormann et al., "CoAP over TCP, TLS, and WebSockets," RFC 8323, 2018.
[9] IPSO Alliance / OMA, "IPSO Smart Objects" guidelines, 2018.
[10] AVSystem and operator white papers on LwM2M smart metering, 2024.
[11] Eclipse Leshan / Wakaama documentation, Eclipse Foundation.
[12] G. Selander et al., related CoRE security drafts; CoAP over QUIC work-in-progress, IETF.
