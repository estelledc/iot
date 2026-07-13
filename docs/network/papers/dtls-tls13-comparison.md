---
schema_version: '1.0'
id: dtls-tls13-comparison
title: DTLS 与 TLS 1.3 在 IoT 协议安全中的对比
layer: 3
content_type: comparison
difficulty: intermediate
reading_time: 20
prerequisites:
  - iot-app-protocols
  - coap-lwm2m-constrained
tags:
- DTLS
- TLS
- IoT安全
- PSK
- mbedTLS
- CoAP
- MQTT
- 握手
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# DTLS 与 TLS 1.3 在 IoT 协议安全中的对比

> **难度**：🟡 中级 | **领域**：协议安全、IoT | **阅读时间**：约 20 分钟

## 日常类比

TLS（Transport Layer Security）像挂号信走铁路：有序、可靠、按轨送达（TCP）。DTLS（Datagram TLS）像加密快递走公路：每包独立，可能乱序或丢失（UDP），但单包仍可保密与完整性保护。CoAP/LwM2M 选 UDP 图轻量，DTLS 是其常见安全外壳；网关北向 MQTT/HTTPS 则多用 TLS 1.3。

## 摘要

对比 TLS 1.3（RFC 8446）与 DTLS 1.3（RFC 9147）在握手、记录层、分片与 IoT 密码套件/认证上的差异，并给出 CoAP+DTLS 与 MQTT+TLS 选型框架。握手毫秒数、RAM/Flash 占用随 MCU、库裁剪与证书链变化，表中数为公开或常见量级示意[1][2][4][5][9]。

## 1 基础对比

| 维度 | TLS 1.3 | DTLS 1.3 |
|------|---------|----------|
| 传输 | TCP | UDP |
| 典型上层 | HTTPS、MQTT、AMQP | CoAP、LwM2M、部分实时媒体 |
| 握手 | 1-RTT，可选 0-RTT | 需处理丢包重传；往返往往更多变 |
| 记录序 | 依赖 TCP | 显式序列号与重放窗 |
| 握手大消息 | 靠 TCP 分段 | 自行分片并按片重传 |
| 标准 | RFC 8446（2018） | RFC 9147（2022） |

```
MQTT/HTTP  → TLS 1.3 → TCP → IP
CoAP/LwM2M → DTLS    → UDP → IP
```

## 2 TLS 1.3 对 IoT 的意义

相对 TLS 1.2，1.3 去掉多余往返、简化密码套件、更强调 AEAD。蜂窝 RTT 较大时，少 1 个 RTT 可缩短连接建立与射频开启时间；具体省电比例随「每日握手次数 × 射频电流」变化，不宜用单一「省 33%」作承诺[1][9]。

0-RTT 可降时延，但有重放风险：**控制类指令（开阀、跳闸）不应走 0-RTT**[10]。

## 3 DTLS 核心机制

- **重传状态机**：握手飞行消息超时指数退避（RFC 建议量级：初始约 1s，上限可达数十秒，次数有上限）[2]。
- **分片**：证书链常超 UDP/IPv6 路径 MTU，按 fragment offset/length 切开，丢片只重传该片。
- **记录头**：1.3 倾向更紧凑的变长头，省链路字节[2]。
- **Connection ID** 等扩展改善地址变更/NAT 后的关联（见 RFC 9146 等）[3]。

## 4 密码套件与认证

TLS/DTLS 1.3 强制实现族常见：`TLS_AES_128_GCM_SHA256`、`TLS_AES_256_GCM_SHA384`、`TLS_CHACHA20_POLY1305_SHA256`。有 AES 硬件加速偏 GCM；无加速可评估 ChaCha20-Poly1305；极受限节点常退回 PSK + CCM-8 等历史套件（注意版本与合规）[1][4]。

| 特性 | PSK | X.509 证书 |
|------|-----|------------|
| 握手与代码体积 | 通常更轻 | 更重 |
| 密钥管理 | 预共享、轮换难 | CA/PKI，规模化更好 |
| 身份 | 共享秘密 | 独立公钥身份 |
| 适用 | 小规模/电表类 | 网关与大规模设备舰队 |

Cortex-M 类公开基准常显示：对称加解密微秒–数十微秒级/KB；ECDHE 数百毫秒量级；PSK 握手远快于完整证书链——以本板 mbedTLS/wolfSSL 实测为准[4][5]。

## 5 CoAP+DTLS vs MQTT+TLS

| 维度 | CoAP + DTLS | MQTT + TLS |
|------|-------------|------------|
| 传输 | UDP | TCP |
| 消息模型 | REST 请求/响应 + Observe | Pub/Sub |
| 连接 | 偏无连接；观察需状态 | 长连接 + keepalive |
| NAT | 需保活/队列模式 | TCP 保活相对直观 |
| 内存 | 常更省（实现相关） | 通常更高 |
| 场景 | 低频、受限、LPWAN | 事件驱动、网关、生态工具 |

粗决策：RAM 极紧 → CoAP+DTLS（优先 PSK/OSCORE 评估）；高频事件且资源尚可 → MQTT+TLS 1.3；控制指令禁用 0-RTT，启用会话恢复减少满握手。

## 6 实践建议

1. OpenSSL `s_client` / Wireshark 看清 1.2 vs 1.3 飞行消息。
2. 设备侧用 mbedTLS/wolfSSL 跑 PSK 与证书两条路径，记录握手字节与峰值 RAM。
3. DTLS MTU 设为链路 MTU 减去 IP/UDP 开销，避免 IP 分片。
4. NB-IoT 等大延迟链路增大初始重传超时，避免误判拥塞。
5. 证书优先 ECDSA P-256 等较短链，减少分片次数。

## 7 局限、挑战与可改进方向

### 1. DTLS 实现质量参差

**局限**：重传、重放窗、分片边界在嵌入式库中的 bug 面大于「只跑 TLS」的路径[6][9]。
**改进**：固定库版本与模糊测试；互通矩阵（Californium/Leshan 等）纳入 CI。

### 2. PSK 运营陷阱

**局限**：出厂统一 PSK 或硬编码 identity 导致批量泄露[4][9]。
**改进**：一机一钥、安全元件注入、可吊销清单；规模上升迁证书/EST。

### 3. 中间盒与 NAT

**局限**：UDP 映射超时导致「上行正常、下行 DTLS 失败」难查[3]。
**改进**：Connection ID、应用层保活、Queue Mode；或边缘终止 DTLS 再北向 TLS。

### 4. 0-RTT 与「省电叙事」滥用

**局限**：把 0-RTT 或「TLS 1.3 必省电三分之一」写进产品承诺，忽略重放与业务模型[10]。
**改进**：按消息敏感度分级；用焦耳/日模型测算，而非只比 RTT 次数。

## 参考文献

[1] E. Rescorla, "The Transport Layer Security (TLS) Protocol Version 1.3," RFC 8446, 2018.
[2] E. Rescorla et al., "The Datagram Transport Layer Security (DTLS) Protocol Version 1.3," RFC 9147, 2022.
[3] E. Rescorla et al., "Connection Identifier for DTLS 1.2," RFC 9146, 2022.
[4] Arm Mbed TLS documentation and configuration guides, 2024.
[5] wolfSSL, embedded TLS/DTLS benchmark materials, 2024.
[6] Implementation experience reports on DTLS for IoT (academic and industry), 2020s.
[7] S. Raza et al., work on DTLS record compression / constrained IoT security, IEEE IoT-J and related.
[8] Eclipse Californium, CoAP + DTLS documentation, 2024.
[9] M. Sethi et al., measurement studies of IoT security handshakes (e.g. NDSS and related venues).
[10] Analyses of 0-RTT key exchange security and replay, Crypto/security literature.
[11] G. Selander et al., "OSCORE," RFC 8613, 2019.
[12] Z. Shelby et al., "CoAP," RFC 7252, 2014.
