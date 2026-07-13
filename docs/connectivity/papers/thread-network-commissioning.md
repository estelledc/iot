---
schema_version: '1.0'
id: thread-network-commissioning
title: Thread网络调试入网流程与安全凭证
layer: 2
content_type: tutorial
difficulty: intermediate
reading_time: 16
prerequisites:
  - thread-protocol-openthread-overview
  - matter-commissioning-flow
tags:
  - Thread
  - Commissioning
  - PSKd
  - J-PAKE
  - DTLS
  - Matter
  - 安全入网
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# Thread网络调试入网流程与安全凭证

> **难度**：🟡 中级 | **领域**：Thread安全 | **阅读时间**：约 16 分钟

## 日常类比

入住公寓：物业（Commissioner）核验合同验证码（设备预共享密钥 PSKd），再发卡（Network Master Key）。旁人偷听对话也难伪造卡——对应调试入网（Commissioning）里基于口令认证密钥交换与加密分发[1][2]。

## 摘要

梳理 Commissioner / Joiner / Joiner Router 三角色、PSKd/PSKc、数据报传输层安全（Datagram Transport Layer Security, DTLS）上的 J-PAKE，以及 Active Operational Dataset 与 Matter 联合入网。组合数与“10–30 秒”为量级/体验值，**随射频环境与实现而变**[1][4]。

## 1. 三角色

| 角色 | 职责 |
|------|------|
| Commissioner | 认证 Joiner，分发网络凭证；可在手机或网内 |
| Joiner | 持 PSKd 请求入网 |
| Joiner Router | 已入网节点，中继 Commissioner↔Joiner 报文 |

出厂写死同一网络密钥会放大单点泄露；Commissioning 要求物理可得的设备特定 PSKd，降低邻居误入与批量克隆风险[1]。

## 2. 凭证

**PSKd（Pre-Shared Key for Device）**：约 6–32 字符，大写字母+数字并排除易混字符；印在标签/二维码。短 PSKd 组合空间有限，规范与厂商常建议更长[1]。

**PSKc（Pre-Shared Key for Commissioner）**：由口令、网络名、扩展个人区域网标识（Extended PAN ID）等经密钥派生得到，用于 Petition 成为活跃 Commissioner；全网同时通常仅一个活跃 Commissioner[1]。

## 3. 流程要点

1. Commissioner 向 Leader Petition（PSKc）。
2. 指定允许入网的 IEEE EUI-64 等。
3. Joiner 发 Discovery；经 Joiner Router 中继。
4. DTLS + J-PAKE（口令即 PSKd）建立会话：抗离线字典、双向认证、前向安全叙事见文献[2][3]。
5. 加密下发 Active Operational Dataset。
6. Joiner 用网格链路建立（Mesh Link Establishment, MLE）附着入网。

| Dataset 字段 | 含义 |
|--------------|------|
| Network Master Key | 128 bit，派生 MAC/MLE 等密钥 |
| Network Name / Channel | 可读名与 802.15.4 信道 |
| PAN ID / Ext PAN ID | MAC 与网络唯一标识 |
| Mesh-Local Prefix | mesh 内寻址 |
| PSKc / Security Policy | Commissioner 与策略位 |
| Active Timestamp | 数据集版本 |

密钥序列计数递增触发轮换；旧密钥保留守卫时间以平滑过渡（具体时长见规范默认值）[1]。

## 4. Commissioner 形态与 Matter

- **Native**：跑在 mesh 内。
- **External**：手机经 Border Router 入网——消费级主流。

Matter over Thread 常一次扫码：QR 含 Thread 连接码与 Matter Setup Code，先 Thread Commissioning，再 PASE/Fabric 加入[4][6]。NFC 触碰等价带出凭证。

## 5. 攻击面与排障

| 威胁 | 缓解叙事 |
|------|----------|
| 窃听握手 | J-PAKE 不直接暴露 PSKd |
| 中间人 | 双向证明知悉 PSKd |
| 离线猜解 | 协议设计抗离线字典；加长 PSKd |
| 重放 | DTLS 随机数/序列 |
| 拒绝服务 | 连接数与超时 |

失败常见：PSKd/二维码误读、信道扫描慢、Commissioner 会话过期、距离过远导致中继丢包[5]。

## 6. 局限、挑战与可改进方向

### 1. 短 PSKd 物理暴露

**局限**：包装盒二维码在开箱前可被拍摄。
**改进**：加长码；安装后遮盖；仓库与开箱流程管控[1]。

### 2. 单活跃 Commissioner

**局限**：并发批量入网需串行或企业级扩展机制。
**改进**：评估 Thread 商业调试/域代理能力；产线预配 + 现场仅激活[1]。

### 3. 用户只看到“扫码失败”

**局限**：底层 DTLS/信道问题被 UI 糊成笼统错误。
**改进**：App 区分凭证错误、无 Joiner Router、BR 不可达；提供手动码与靠近重试[5]。

### 4. Matter 与 Thread 状态不一致

**局限**：Thread 已入网但 Fabric 失败，成“半入网”。
**改进**：编排事务化回滚；运维可读 Thread 与 Matter 两侧状态[4]。

## 参考文献

[1] Thread Group, Thread specification — Commissioning and operational dataset.
[2] F. Hao and P. Ryan, J-PAKE: authenticated key exchange without PKI, Springer, 2010.
[3] E. Rescorla and N. Modadugu, RFC 6347, DTLS 1.2 (and successors as applicable).
[4] Connectivity Standards Alliance, Matter specification — device commissioning.
[5] OpenThread, Commissioning guide and CLI examples.
[6] Thread Group / CSA materials on Matter over Thread unified onboarding UX.
[7] PBKDF2 / PSKc derivation notes in Thread commissioning annexes.
[8] IETF work related to SRP and secure device onboarding (ecosystem context).
[9] DTLS denial-of-service and rate-limiting operational practices.
[10] QR / NFC out-of-band commissioning encoding examples (Thread/Matter).
[11] Key sequence counter and guard-time behavior in Thread security policy.
