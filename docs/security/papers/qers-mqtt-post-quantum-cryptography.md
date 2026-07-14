---
schema_version: '1.0'
id: qers-mqtt-post-quantum-cryptography
title: MQTT、HTTP 与 HTTPS 在后量子密码下的 QERS 韧性评估
layer: 6
content_type: paper_reading
difficulty: advanced
reading_time: 18
prerequisites:
  - post-quantum-crypto-iot
  - mqtt5-deep-dive
  - compliance-framework-nist-etsi
tags:
  - Post-Quantum Cryptography
  - MQTT
  - HTTP
  - IIoT
  - Security Metrics
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "Quantum Encryption Resilience Score (QERS) for MQTT, HTTP, and HTTPS under Post-Quantum Cryptography in Computer, IoT, and IIoT Systems"
  authors:
    - Jonatan Rassekhnia
  year: 2026
  doi: UNKNOWN
  url: https://arxiv.org/abs/2601.13423v1
---
# MQTT、HTTP 与 HTTPS 在后量子密码下的 QERS 韧性评估

> 初读范围：本文基于 arXiv 元数据、摘要和公开条目信息建立阅读卡片；尚未完成 PDF 全文逐段复核、QERS 指标定义核验或实验环境复现，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

后量子密码能提高长期安全性，但密钥、签名和计算开销可能让 IoT/IIoT 设备吃不消。QERS 试图给 MQTT、HTTP、HTTPS 在 PQC 方案下的“加密韧性”打分，帮助比较安全收益和资源成本。

这篇论文适合补 `post-quantum-crypto-iot` 的协议级开销视角，尤其适合 MQTT 设备迁移到 PQC 时参考。

## 论文要回答的问题

1. PQC 引入的计算和通信开销如何影响 MQTT、HTTP、HTTPS。
2. QERS 指标如何定义安全韧性和资源代价。
3. IoT 与 IIoT 设备在 PQC 迁移中面临哪些限制。
4. 不同协议在后量子场景下的适配优先级如何判断。

## 初读要点

| 协议 | IoT 角色 | PQC 风险 |
| --- | --- | --- |
| MQTT | 轻量发布订阅 | 握手和证书开销 |
| HTTP | 管理接口和上报 | 资源占用增加 |
| HTTPS | 安全 Web/API 通信 | 密钥交换和签名变大 |
| IIoT | 工业控制和监测 | 实时性与合规压力 |

## 放进全栈框架

- Layer 3 包含 MQTT、HTTP/HTTPS 等传输和应用协议。
- Layer 6 负责后量子密码、合规和迁移风险。
- Layer 7 的工业设备会放大实时性和生命周期问题。

## 初读结论

这篇论文的价值在于把 PQC 迁移从“算法安全”拉回“协议和设备能不能承受”。后续深读要核验 QERS 是否透明、可复现，以及是否真实测量 IoT/IIoT 设备而不只是桌面环境。

## 后续核验清单

- 抽取 QERS 的指标公式和权重。
- 核对 PQC 算法、协议实现和测试设备。
- 比较延迟、带宽、CPU、内存和安全分数。
- 对接 `post-quantum-crypto-iot` 与 `mqtt5-deep-dive`。

## 参考文献

[1] J. Rassekhnia, "Quantum Encryption Resilience Score (QERS) for MQTT, HTTP, and HTTPS under Post-Quantum Cryptography in Computer, IoT, and IIoT Systems," arXiv:2601.13423, 2026.
