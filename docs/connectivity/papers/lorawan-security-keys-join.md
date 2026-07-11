---
schema_version: '1.0'
id: lorawan-security-keys-join
title: LoRaWAN安全密钥体系与入网流程
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - lpwan-comparison
  - low-power-wide-area-network-survey
tags:
  - LoRaWAN
  - OTAA
  - ABP
  - AES-128
  - AppKey
  - Join Server
  - 安全元件
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# LoRaWAN安全密钥体系与入网流程

> **难度**：🟡 中级 | **领域**：LoRaWAN安全 | **阅读时间**：约 20 分钟

## 日常类比

加入需验身份的私密俱乐部：出示会员卡（根密钥 AppKey）→ 门卫核验后发当天储物柜钥匙（会话密钥）→ 你只能开自己的柜，看不到别人的。LoRaWAN（Long Range Wide Area Network）同理：永久身份凭证完成入网（Join），临时会话钥匙做日常通信；网络服务器（Network Server, NS）与应用服务器（Application Server, AS）各管一层，互不越权[1][2]。

## 摘要

梳理 LoRaWAN 1.0/1.1 密钥层次、空中激活（Over-The-Air Activation, OTAA）与激活即用（Activation By Personalization, ABP）、帧加密与消息完整性码（Message Integrity Code, MIC），并给出制造/运营侧密钥管理要点。文中密钥长度、轮换周期为规范或实践量级，**落地以联盟规范与威胁模型为准**[1][3]。

## 1. 双层安全架构

| 层 | 密钥 | 持有者 | 作用 |
|----|------|--------|------|
| 应用层 | AppSKey | 设备 + AS | 端到端加密 FRMPayload |
| 网络层 | NwkSKey（1.0）/ 多把网络密钥（1.1） | 设备 + NS | MIC、MAC 命令完整性/加密 |

NS 可验帧真伪但通常读不到应用明文；AS 可解密数据但不参与空口调度。一层泄露不自动击穿另一层[1][2]。

## 2. 根密钥 AppKey

| 属性 | 说明 |
|------|------|
| 长度 | 128 bit（AES-128） |
| 生命周期 | 设备全寿命根密钥 |
| 预置 | 制造写入设备与 Join Server（JS） |
| 唯一性 | **每设备一把**，禁止共享 |

固件硬编码 AppKey 是常见事故源。安全元件（Secure Element, SE，如 ATECC608A 类）内完成 CMAC/派生，密钥不离开硬件[4][5]。

## 3. OTAA 入网

JoinRequest 含 AppEUI/JoinEUI、DevEUI、DevNonce 与 AppKey 计算的 MIC。JS 验 MIC、查 DevNonce 防重放，再发 JoinAccept（含 AppNonce 等）。双方用同一输入独立派生会话密钥，**密钥本身不空口传输**[1]：

| 派生 | 输入前缀（示意） | 用途 |
|------|------------------|------|
| NwkSKey | `0x01 ‖ AppNonce ‖ NetID ‖ DevNonce` | 网络完整性 |
| AppSKey | `0x02 ‖ …`（同结构） | 应用加密 |

1.1 将网络侧细分为 FNwkSIntKey、SNwkSIntKey、NwkSEncKey，并强调独立 JS，利于漫游与 NS 失陷隔离[1][3]。

## 4. OTAA vs ABP

| 特性 | OTAA | ABP |
|------|------|-----|
| 密钥更新 | 每次入网可换 | 预置后常长期不变 |
| 前向安全 | 较好 | 弱 |
| DevAddr | 动态分配 | 常固定 |
| 帧计数器 | 入网可安全重置 | 断电回零易被拒收 |
| 适用 | 生产部署默认 | 原型/受控实验 |

ABP 设备重启后 FCnt 回零，NS 按重放拒绝——这是现场“突然全哑”的高频原因。优先 OTAA；若必须 ABP，FCnt 须非易失持久化[2][3]。

## 5. 帧安全

载荷常用 AES-128 CTR，计数块绑定方向、DevAddr、FCnt。MIC 用网络密钥对 `B0 ‖ 消息体` 做 AES-CMAC，取前 4 字节。接收方只接受严格递增的 FCnt，从而抑制重放与篡改[1]。

| 威胁 | 主要防护 |
|------|----------|
| 窃听 | AppSKey 加密 |
| 重放 | FCnt |
| 伪造/篡改 | MIC |
| 密钥提取 | SE / HSM |
| 流氓网关 | 可转发与窥元数据，难读明文、难造合法 MIC |

## 6. 密钥管理实践

制造：HSM 生成唯一 AppKey → 安全通道写入 SE → 同步注册 JS → 制造系统不落盘长期留存。运营：以重新入网做轮换；监控异常高频 Join；固件用 `memset_s` 等清理内存中的会话材料[2][4]。

## 7. 局限、挑战与可改进方向

### 1. ABP 与计数器

**局限**：ABP 无入网握手，FCnt 回零导致拒收或削弱重放防护[3]。
**改进**：默认 OTAA；ABP 强制 NVM 计数器与运维告警。

### 2. 1.0 密钥粒度

**局限**：单把 NwkSKey 使 NS 侧权限偏粗；漫游场景边界模糊[1][3]。
**改进**：新部署优先 1.1；独立 JS；漫游走规范密钥分发。

### 3. 软件密钥存储

**局限**：Flash/固件提取可拿走 AppKey，端到端承诺失效[5]。
**改进**：量产强制 SE；产线审计禁止明文密钥日志。

### 4. Join 侧可用性

**局限**：DevNonce 窗口、JS 可用性与时钟/随机源质量影响入网成功率。
**改进**：Nonce 策略按规范实现；JS 高可用；入网失败退避与遥测。

## 8. 实践要点

1. 生产禁用共享 AppKey 与源码硬编码。
2. 选型默认 OTAA + 1.1（或明确兼容矩阵）。
3. 验收：SE 内 MIC、FCnt 掉电保持、流氓网关无法解密应用载荷。

## 参考文献

[1] LoRa Alliance, LoRaWAN 1.1 Specification, 2017.
[2] LoRa Alliance, LoRaWAN Security FAQ and Best Practices, 2020.
[3] G. Avoine et al., "Rescuing LoRaWAN 1.0," Financial Cryptography, 2019.
[4] Microchip, ATECC608A Secure Element for LoRaWAN (Application Note).
[5] X. Yang, "LoRaWAN: Vulnerability Analysis and Practical Exploitation," 2020.
[6] LoRa Alliance, LoRaWAN 1.0.4 Specification, 2020.
[7] NIST SP 800-38B, CMAC Mode for Authentication.
[8] NIST FIPS 197, Advanced Encryption Standard (AES).
[9] Semtech, LoRaWAN security and key management application notes.
[10] IETF/industry notes on LoRaWAN roaming and Join Server separation.
[11] ETSI/EN materials on short-range device security considerations (context).
