---
schema_version: '1.0'
id: ble-security-pairing-bonding
title: BLE安全机制：配对/绑定/加密详解
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - ble-gatt-profile-custom-service
tags:
  - BLE
  - 配对
  - 绑定
  - LE Secure Connections
  - SMP
  - RPA
  - AES-CCM
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# BLE安全机制：配对/绑定/加密详解

> **难度**：🟡 中级 | **领域**：BLE安全 | **阅读时间**：约 20 分钟

## 日常类比

第一次做客：对讲确认身份再开门——配对（Pairing）；主人记住你下次免介绍——绑定（Bonding）；进屋私聊不被走廊听见——链路加密。蓝牙低功耗（Bluetooth Low Energy, BLE）安全管理器协议（Security Manager Protocol, SMP）把这三件事串起来，并叠加地址隐私[1][2]。

## 摘要

本文对比传统配对与低功耗安全连接（LE Secure Connections）、关联模型、长期密钥（Long Term Key, LTK）等密钥角色、AES-CCM 加密与可解析私有地址（Resolvable Private Address, RPA），并简述 KNOB/BLESA 等风险。安全级别与攻击可行性随实现与配置变化，**清单不能替代威胁建模**[2][3]。

## 1. 安全级别与 SMP

| 级别 | 含义 | 典型场景 |
|------|------|----------|
| 1 | 无加密无认证 | 公开传感器广播 |
| 2 | 未认证加密（如 Just Works） | 低敏感 |
| 3 | 认证加密（抗 MITM 关联） | 敏感数据 |
| 4 | LE SC + 认证 | 高安全需求 |

SMP 走固定逻辑链路控制与适配协议（L2CAP）通道 CID 0x0006[1]。

## 2. 配对三阶段

1. 交换 IO 能力、带外（Out-of-Band, OOB）、认证需求、密钥长度。
2. 传统：临时密钥（TK）→短期密钥（STK）；LE SC：椭圆曲线迪菲-赫尔曼（ECDH）→ LTK。
3. 分发 LTK、身份解析密钥（IRK）、连接签名解析密钥（CSRK）等[1]。

| 方法 | MITM 保护倾向 | 说明 |
|------|---------------|------|
| Just Works | 弱 | 无用户确认 |
| Passkey | 较强（视实现） | 六位输入 |
| Numeric Comparison | 强（LE SC） | 双方确认同号 |
| OOB | 强（通道可信时） | NFC/二维码等 |

## 3. Legacy vs LE Secure Connections

| 特性 | Legacy | LE SC（4.2+） |
|------|--------|----------------|
| 密钥交换 | 对称 TK 方案 | ECDH |
| Just Works 抗被动窃听 | 很弱（TK=0） | 显著更好 |
| 前向安全叙事 | 差 | 更好 |
| 推荐 | 遗留互通 | **新设计默认** |

Legacy Passkey 空间有限，存在离线猜测叙事；LE SC 下 Passkey 按位验证，在线暴力成本更高，仍需尝试次数限制[1][3]。

## 4. 绑定、加密与隐私

绑定把密钥写入非易失存储，重连用 LTK 快速开加密，避免重复配对。链路层 AES-128-CCM：密文 + MIC，Nonce 含计数与方向，防重放[1]。

| 地址类型 | 可追踪性 | 备注 |
|----------|----------|------|
| Public | 高 | IEEE 分配 |
| Random Static | 中 | 可上电变更 |
| RPA | 低（对陌生人） | 持 IRK 可解析 |
| Non-resolvable | 低 | 友方也难认 |

RPA 轮换周期可配置；过短增解析成本，过长增被追踪窗口[1][5]。

## 5. 已知问题与实践

| 问题 | 要点 | 缓解 |
|------|------|------|
| KNOB | 密钥长度被压低 | 强制 128-bit[3] |
| BLESA | 重连认证不足 | 实现补丁/策略[4] |
| 固定 Passkey | 可预测 | 动态或 OOB |
| 无头设备 | 仅 Just Works | 物理窗口+应用层令牌 |

## 6. 局限、挑战与可改进方向

### 1. Just Works 被当成“已安全”

**局限**：LE SC 下仍不抗主动中间人[1]。
**改进**：有显示用 Numeric Comparison；无 IO 用 OOB 或配对按钮窗口+应用认证。

### 2. 绑定存储与刷机

**局限**：明文存 LTK、槽位耗尽、克隆 Flash。
**改进**：加密存储；限绑定数量；提供清除绑定与重新配网流程。

### 3. 隐私与可运营性冲突

**局限**：强 RPA 使售后扫描难认设备。
**改进**：售后模式限时可解析；二维码含身份；审计日志不落永久公钥地址。

### 4. 栈与手机差异

**局限**：同一外设在 iOS/Android 上配对体验与密钥分发不一致。
**改进**：双端测试矩阵；避免依赖未文档化超时；关键权限用 GATT 加密许可。

## 7. 实践要点

1. 新项目仅启用 LE Secure Connections，最小密钥 16 字节。
2. 敏感特征值权限设为需加密/认证。
3. 生产关闭“任意时刻可配对”，改为授时窗口。

## 参考文献

[1] Bluetooth SIG, Core Specification Vol 3 Part H: Security Manager.
[2] NIST SP 800-121, Guide to Bluetooth Security.
[3] Antonioli, D. et al., "The KNOB Attack," USENIX Security, 2019.
[4] Wu, J. et al., "BLESA," WOOT, 2020.
[5] Nordic Semiconductor, nRF Connect SDK security / privacy guides.
[6] Bluetooth SIG, LE Secure Connections feature descriptions.
[7] Research on BLURtooth / cross-transport key derivation issues.
[8] SweynTooth related BLE controller vulnerability reports (implementation DoS class).
[9] Bluetooth SIG, privacy / RPA generation and resolution sections.
[10] IETF/industry notes on AES-CCM usage in constrained radios (contextual).
[11] OWASP / IoT pairing guidance for headless devices (practical checklists).
