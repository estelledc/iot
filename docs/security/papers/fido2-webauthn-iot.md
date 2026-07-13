---
schema_version: '1.0'
id: fido2-webauthn-iot
title: 身份联邦 FIDO2/WebAuthn 在 IoT 中的应用
layer: 6
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - puf-device-authentication
  - secure-boot-root-of-trust
  - ota-secure-update
tags:
- FIDO2
- WebAuthn
- Passkeys
- 设备认证
- FDO
- 安全元件
- CTAP2
- IoT身份
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 身份联邦 FIDO2/WebAuthn 在 IoT 中的应用

> **难度**：🟡 中级 | **领域**：身份认证、设备管理 | **阅读时间**：约 22 分钟

## 日常类比

传统门禁靠钥匙或密码卡：丢了或被复制，别人就能冒充你。

FIDO2 / WebAuthn 更像“指纹永不离开身体”的门禁：设备里的私钥不出安全边界，服务器只存公钥“摘要”。即使服务器库被拖，攻击者也难伪造设备身份——没有私钥就签不出合法响应。

对物联网（Internet of Things, IoT）而言：每台设备出厂持有唯一密钥材料，注册时只上传公钥与证明；云被攻破不等于设备身份可被批量伪造。

## 摘要

本文说明 FIDO2（Fast IDentity Online 2）与 WebAuthn（Web Authentication）在 IoT 中的角色：平台认证器、CTAP2（Client to Authenticator Protocol）、设备证明（Attestation）、Passkeys 与用户凭证的差异，以及 FIDO Device Onboard（FDO）零接触配置。重点在百万级设备扩展、与 MQTT/CoAP 集成，以及局限与可执行改进。

## 1 FIDO2 架构

### 1.1 核心组件

```
依赖方 RP（云平台）          客户端（浏览器/网关代理）         认证器（SE/TPM）
  存：公钥 + 凭证 ID    <── WebAuthn/FIDO2 ──>    <── CTAP2 ──>   存：私钥（不导出）
```

- **依赖方（Relying Party, RP）**：验证签名、存公钥。
- **客户端**：转发挑战与响应。
- **认证器（Authenticator）**：在安全元件（Secure Element, SE）或可信平台模块（Trusted Platform Module, TPM）内生成密钥并签名。

### 1.2 协议栈

| 层级 | 协议 | 功能 |
|------|------|------|
| 应用 | WebAuthn API | 应用/代理与 RP 交互 |
| 传输 | CTAP2 | 客户端 ↔ 认证器 |
| 认证器命令 | CTAP2 | 密钥生成、签名、证明 |
| 硬件 | SE / TPM | 密钥存储与防导出 |

### 1.3 与传统方案对比

| 维度 | 密码 | PKI 证书 | OAuth 2.0 | FIDO2 |
|------|------|----------|-----------|-------|
| 长期密钥位置 | 服务器哈希 | 设备 + CA | 授权服务器令牌 | 主要在设备 |
| 钓鱼防护 | 弱 | 部分 | 部分 | 绑定 RP ID，较强 |
| 扩展性 | 差 | CA/证书生命周期成本高 | 好 | 好（无密码库） |
| 设备成本 | 无 | 中 | 低 | 低–中（常需 SE） |
| 离线能力 | 有 | 有 | 弱 | 本地签名可离线完成 |
| 泄露影响面 | 易撞库扩散 | 单证/单设备 | 令牌窗口 | 通常单设备 |

标准与实现细节见 FIDO Alliance / W3C 规范[1][2]。

## 2 注册与认证（机制要点）

### 2.1 注册（Registration）

1. RP 生成挑战（challenge）与公钥凭证参数（如 ES256 / EdDSA）[1]
2. 认证器生成密钥对，私钥留在 SE
3. 返回公钥、凭证 ID、可选 attestation 对象
4. RP 验证证明链后存储公钥

IoT 常见选项：`authenticatorAttachment=platform`、`userVerification=discouraged`（无人交互设备）、`attestation=direct`（需要供应链身份时）。

### 2.2 认证（Authentication）

1. RP 下发挑战
2. 认证器对 `authenticatorData || SHA-256(clientDataJSON)` 签名
3. RP 校验：RP ID 哈希、签名计数器（防重放）、ECDSA/EdDSA 签名
4. 更新 `signCount`

计数器回绕或停滞应视为克隆嫌疑，进入吊销/隔离流程。

## 3 Passkeys 与 IoT 设备凭证

| 特性 | 用户 Passkeys | IoT 设备凭证 |
|------|---------------|--------------|
| 同步 | 常经云密码管理器同步 | 应绑定单一硬件 |
| 用户验证 | 生物识别/PIN | 通常无（自动） |
| 生命周期 | 用户账户 | 设备全生命周期 |
| 证明 | 可选 | 量产场景常强制 |
| 规模 | 每人少量 | 可达百万级 |

Passkeys 是面向消费者的品牌化体验[9]；IoT 应避免把设备私钥同步到消费级密码库。

### 设备证明（Attestation）

出厂证明密钥对 attestation 对象签名，RP 校验制造商证书链，确认“是某型号真设备而非软件仿冒”[1][6][7]。证明密钥泄露影响整批型号，需与安全启动、密钥注入产线一起设计。

## 4 FIDO Device Onboard（FDO）

### 4.1 要解决的问题

传统部署：生产 → 物流 → 现场人工配 Wi‑Fi/证书 → 注册云。人工步骤贵且易错配、泄密。

FDO 目标：零接触完成所有权转移与配置[3]。

### 4.2 协议阶段（概念）

| 阶段 | 参与方 | 作用 |
|------|--------|------|
| TO0 | Owner ↔ Rendezvous | 所有者注册可达信息 |
| TO1 | Device ↔ Rendezvous | 设备发现当前 Owner |
| TO2 | Device ↔ Owner | 互认证、下发配置、替换凭证 |

### 4.3 与传统配置对比

| 维度 | 手动配置 | 预绑定客户镜像 | FDO |
|------|----------|----------------|-----|
| 现场人工 | 必须 | 通常不需要 | 不需要 |
| 供应链灵活性 | 高 | 低 | 高 |
| 安全绑定 | 弱（明文口令常见） | 中 | 密码学所有权转移 |
| 规模化 | 差 | 中 | 好 |
| 二次转售/易主 | 复杂 | 需重刷 | 协议支持 |

## 5 百万级扩展

挑战：密钥与吊销规模、批量上电认证洪峰、跨区延迟。

常见架构：全局凭证库 + 区域认证节点 + 边缘网关缓存已认证设备状态。优化手段包括批量取公钥、硬件加速验签、短期 JWT/会话令牌降低每次 MQTT 全量 FIDO 往返[4]。

| 层级 | 职责 | 延迟目标（示意） |
|------|------|------------------|
| 边缘网关 | 缓存会话、本地策略 | 毫秒–数十毫秒 |
| 区域 RP | 验签、发令牌 | 数十–百毫秒 |
| 全局注册 | 吊销同步、审计 | 秒级可接受 |

具体 QPS/延迟以压测为准，公开论文数字不可直接当容量规划[4]。

## 6 与 IoT 协议集成

| 路径 | 模式 | 说明 |
|------|------|------|
| MQTT | FIDO 认证 → 短期 JWT → CONNECT 密码字段 | Broker 验 JWT；TLS 仍建议开启 |
| CoAP | DTLS；密钥可由 FIDO 会话派生 | 适合受限节点 |
| 网关代理 | 设备 ↔ 网关用本地凭证；网关 ↔ 云用 FIDO/mTLS | 终端无浏览器栈时常见 |

SE 选型示意：低成本 P-256 芯片（如 ATECC608B 类）[7]；需更强认证/FDO 时考虑更高端 SE（如 NXP SE050 类）[6]。价格与认证级别随批次变化，采购以数据手册与 Common Criteria 声明为准。

## 7 局限、挑战与可改进方向

### 1. 无浏览器栈的设备难“原生 WebAuthn”

**局限**：MCU 固件通常不跑完整 WebAuthn 客户端；需自研 CTAP 子集或网关代理，互操作成本高。
**改进**：在网关实现标准 WebAuthn/FIDO；终端只保留 SE 签名 API；对齐 COSE/CBOR 编码[8]。

### 2. Attestation 与隐私、供应链密钥风险

**局限**：直接证明暴露型号/批次；证明根密钥泄露可导致大规模仿冒。
**改进**：生产型可改用匿名证明或企业自签；证明密钥分片与 HSM 保管；异常注册速率告警。

### 3. 吊销与离线窗口

**局限**：海量设备 CRL/OCSP 式吊销延迟大；离线设备仍用已吊销凭证。
**改进**：短寿命会话令牌；网关定期拉取吊销布隆过滤器；发现克隆计数器则立即隔离。

### 4. FDO 生态与运维复杂度

**局限**：Rendezvous/Owner 服务可用性、跨厂商互操作仍不均衡。
**改进**：先在单一 Owner 域试点；契约测试 TO1/TO2；与安全 OTA 联动，配置与固件同源签名策略。

### 5. 与遗留口令设备并存

**局限**：存量设备无 SE，双栈增加攻击面（弱口令旁路）。
**改进**：网络分段；强制升级路径；对无 FIDO 设备缩短证书/口令寿命并加强异常检测。

## 8 实践要点（简）

1. 浏览器体验 WebAuthn 流程后再迁到设备代理
2. 用 SE 做不可导出密钥，勿把设备私钥放可读写 Flash
3. MQTT 用短 JWT，勿把长期私钥当 MQTT 密码
4. 规模化：FDO + 区域 RP + 网关缓存
5. 对齐 NIST 数字身份指南中的认证器保证级思路[10]

## 参考文献

[1] FIDO Alliance / W3C, "Web Authentication (WebAuthn)," W3C Recommendation, 2021–2025 现行版本.
[2] FIDO Alliance, "Client to Authenticator Protocol (CTAP) v2.1," 2022–2024.
[3] FIDO Alliance, "FIDO Device Onboard (FDO) Specification," v1.1, 2023.
[4] N. Bindel et al., "FIDO2 for IoT: Scalable Device Authentication," IEEE Internet of Things Journal / 相关工作, 2023–2024.
[5] Yubico, "java-webauthn-server" 及服务端实现实践, GitHub, 持续维护.
[6] NXP, "SE050 FIDO2 / 安全元件应用笔记," 2023–2024.
[7] Microchip, "ATECC608B Trust Platform Design Guide," 2023.
[8] IETF, "RFC 8152: CBOR Object Signing and Encryption (COSE)," 2017.
[9] Google / Apple / FIDO, "Passkeys" 开发者指南与联盟材料, 2023–2024.
[10] NIST, "SP 800-63B Digital Identity Guidelines — Authentication and Lifecycle Management," 近年版本.
[11] IETF, "RFC 8392: CBOR Web Token (CWT)" / JWT 在受限设备中的用法相关讨论, 2018–2024.
[12] OASIS / MQTT 规范与 IoT 身份联合部署白皮书（厂商与联盟材料）, 近年版本.
