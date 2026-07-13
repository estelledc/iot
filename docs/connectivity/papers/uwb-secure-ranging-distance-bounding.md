---
schema_version: '1.0'
id: uwb-secure-ranging-distance-bounding
title: UWB安全测距与距离限界协议
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites:
  - uwb-ieee-802-15-4z-ranging
tags:
  - UWB
  - 距离限界
  - STS
  - 中继攻击
  - Distance-Bounding
  - FiRa
  - CCC
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# UWB安全测距与距离限界协议

> **难度**：🔴 高级 | **领域**：UWB安全 | **阅读时间**：约 18 分钟

## 日常类比

用对讲机问“你到门口了吗”，远处同伙可代答——这是中继。距离限界（Distance Bounding）像用秒表测问答往返：光速不可超越，答得“太快且内容正确”才可能真在附近。UWB 提供足够细的时间尺，STS 提供“答句不可伪造”[1][2][3]。

## 摘要

访问控制若依赖“靠近”，必须同时防中继与距离缩减。802.15.4z STS 把密码学验证嵌入测距物理过程；FiRa/CCC 将其落成配置与车钥匙流程。文中延迟/分辨率数字为物理量级说明，**攻击可行性随实现与阈值策略而变**[3][4]。

## 1. 威胁：中继与距离欺诈

中继攻击不破解密钥，只转发合法挑战/响应，使验证者以为证明者在附近。公开报道中，被动进入系统曾被低成本中继演示——**个案不可外推为全行业同一数字**[4][5]。

简单 RSSI“测距”可被抬功率欺骗；无密码绑定的 ToF 仍可能被早期比特猜测、伪造时间戳等手段威胁，故需要距离限界思想[1][2]。

## 2. 距离限界三阶段（概念）

1. **慢阶段**：承诺、密钥材料，不严格计时。
2. **快阶段**：随机挑战—立即响应，往返时延给出距离上界。
3. **验证**：检查响应正确性与时延是否低于阈值[1][2]。

| 对比 | 普通测距 | 距离限界式安全测距 |
|------|----------|-------------------|
| 密码绑定 | 可无 | 需要 |
| 防中继 | 弱 | 以时延+正确性为目标 |
| 防距离缩减 | 弱 | 依赖不可预测响应 |

## 3. UWB 为何更合适

带宽大 → 时间分辨率细，中继引入的额外延迟更可能超出安全裕量。窄带 BLE/NFC 的时间分辨粗，难以单独承担“密码学距离证明”[3][6]。

UWB 首达路径检测降低“用反射路径假装更近”的部分空间，但仍需协议层 STS/密钥[3][7]。

## 4. 802.15.4z STS

STS 由共享密钥与计数器经 AES 等原语扩展为伪随机序列，置于测距相关结构中；接收端相关峰决定是否采信 ToA。攻击者无密钥难以提前构造通过验证的序列；纯转发则增加延迟[3][8]。

| 攻击 | STS 侧要点 |
|------|------------|
| 中继转发 | 延迟抬高测距 |
| 距离缩减/抢先发 | 难预测 STS |
| 早期检测猜测 | 伪随机比特难局部预测 |
| 密钥已泄露（Cicada 类） | 需 SE、轮换、异常检测等上层 |

## 5. FiRa / CCC 落地

FiRa 定义安全配置档（STS 模式、密钥管理强度与场景映射）。CCC Digital Key 典型流：BLE 建信任 → 派生 UWB 会话/STS 密钥 → DS-TWR+STS → 按区域执行解锁/启动[8][9][10]。

| 技术 | 精度叙事 | 中继抗性叙事 |
|------|----------|--------------|
| BLE RSSI | 米级、易扰 | 弱 |
| NFC | 近场短距 | 体验差，非通用 ToF 证明 |
| UWB+STS | 厘米量级潜力 | 以标准安全测距为目标 |

## 6. 局限、挑战与可改进方向

### 1. 阈值过松或过紧

**局限**：过松漏过中继；过紧导致合法 NLOS 误拒。
**改进**：分区阈值 + 置信度；劣链路降级为显式用户确认[9][10]。

### 2. 密钥与 SE 落地不完整

**局限**：STS 密钥留在主 CPU 明文，侧信道/提取风险。
**改进**：SE/安全飞地存钥与派生；会话密钥短生命[8][11]。

### 3. 实现侧信道与时间作弊

**局限**：标准正确不等于芯片/协议栈无漏洞。
**改进**：跟进学术攻击面与厂商勘误；渗透测试含物理层时序[2][7]。

### 4. 多锚点融合逻辑漏洞

**局限**：单锚通过、融合策略错误仍可能误动作。
**改进**：多锚一致性、驾驶座几何约束、安全状态机评审[9][10]。

## 7. 实践要点

1. 威胁模型写清：防中继、防缩距、是否假设密钥安全。
2. 量产配置禁止 Mode 0 用于门禁/车钥匙。
3. 验收含中继演练与 NLOS 误拒率，不只看平均精度。

## 参考文献

[1] Brands, S. and Chaum, D., "Distance-Bounding Protocols," EUROCRYPT, 1993.
[2] Rasmussen, K. and Capkun, S., "Realization of RF Distance Bounding," USENIX Security, 2010.
[3] IEEE Std 802.15.4z-2020, Enhanced Impulse Radio.
[4] Public analyses of relay attacks on passive keyless entry (treat as anecdotal).
[5] Francillon, A. et al., relay attacks on PKE systems (academic references).
[6] Singh, M. et al., UWB ranging security-related survey/tutorial material.
[7] Academic work on UWB secure ranging attacks and defenses (Cicada et al. lineage).
[8] FiRa Consortium, UWB security white paper / profiles.
[9] Car Connectivity Consortium, Digital Key 3.x.
[10] Coppens, D. et al., UWB standards and organizations, IEEE Access, 2022.
[11] NXP / vendor SE + UWB digital key application notes.
[12] Bluetooth SIG materials on RSSI limitations (contrast).
