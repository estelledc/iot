---
schema_version: '1.0'
id: dlms-cosem-smart-meter-protocol
title: DLMS/COSEM智能电表通信协议标准
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - iot-connectivity-selection-framework
tags:
- DLMS
- COSEM
- OBIS
- 智能电表
- AMI
- IEC 62056
- PLC
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# DLMS/COSEM智能电表通信协议标准

> **难度**：🟡 中级 | **领域**：智能计量、AMI | **阅读时间**：约 20 分钟

## 日常类比

换城市发现电表「方言」不同，供电公司抄表系统听不懂——厂商私有协议的痛。DLMS/COSEM 像计量界的普通话：DLMS（Device Language Message Specification）管消息怎么说，COSEM（Companion Specification for Energy Metering）管表内数据怎么建模；合在 IEC 62056 系列里，电/气/水/热都可沿用同一套对象思维[1][2]。

## 摘要

讲解 COSEM 接口类、OBIS、ACSE/xDLMS、HDLC 与 IP 包装、安全套件，以及 PLC/NB-IoT 承载。全球设备存量、抄表成功率与「投资回收期」等运营数字因项目而异，本文不作统一承诺[1][9]。

## 1 对象模型与 OBIS

接口类（IC）定义属性/方法；实例用逻辑名访问。常用 IC：Data、Register、Profile Generic、Clock、Association LN、Disconnect Control 等[1]。

OBIS（Object Identification System）形如 A.B.C.D.E.F，标识介质、量、费率、历史等。例如电力正向有功电能常用约定码点（如 1.0.1.8.0.255 一类），使跨厂商读数语义对齐——仍以现行 OBIS 表为准[3]。

| 层次 | 作用 |
|------|------|
| COSEM 应用 | 对象、服务（GET/SET/ACTION） |
| 包装 | HDLC 或 TCP/UDP Wrapper |
| 承载 | RS-485、光口、PLC、蜂窝、RF Mesh… |

## 2 服务与安全

GET/SET/ACTION 对应读、写、方法调用（如拉合闸）。Profile 可用选择性访问与分块传输拉负荷曲线[2]。

| 级别倾向 | 机制 | 备注 |
|----------|------|------|
| 无/低级 | 无或明文口令 | 仅限非敏感 |
| 高级认证 | 挑战-响应 | 基线推荐方向 |
| 加密套件 | AES-GCM 等；Suite 升档含签名/ECDH | 拉闸与计费数据必评[1][2] |

访问权限按 Association 绑定到对象属性/方法；固件 Image Transfer 等需最高管控[1]。

## 3 AMI 中的位置

AMI（Advanced Metering Infrastructure）含智能表、通信、Head-End、MDMS。DLMS/COSEM 主要在表计↔前端；MDMS 北向常用其他企业集成标准[9]。组网：PLC+集中器、蜂窝直连、RF Mesh 各有基础设施与资费权衡[4][5][10]。

| 承载 | 优点 | 风险 |
|------|------|------|
| G3-PLC / PRIME | 借电力线，少布新线 | 噪声、衰减、速率受限 |
| NB-IoT 等蜂窝 | 部署快、少集中器 | 订阅费、运营商依赖 |
| RF Mesh | 自组织 | 规划与干扰管理 |

DLMS APDU 可经 CoAP/UDP 等在受限蜂窝上承载，细节看项目剖面[10]。

## 4 局限、挑战与可改进方向

### 1. 剖面与互操作仍「同标不同行为」

**局限**：可选 IC/属性组合多，认证表与现场表行为差。
**改进**：采购绑定 DLMS UA 认证与国家companion profile；入网抽测 GET 清单[1][11]。

### 2. 安全套件落地不均

**局限**：老旧表停在低级认证；密钥生命周期管理弱。
**改进**：新装强制 Suite 适当档；HSMs/密钥注入流程；拉闸双人授权与审计[2][12]。

### 3. 承载与应用层故障难拆

**局限**：抄表失败分不清 PLC 噪声还是 Association/安全失败。
**改进**：分层指标（物理成功率 vs DLMS 结果码）；集中器保留原始轨迹[4][5]。

### 4. 与中国 DL/T 等本地标准并存

**局限**：出口/进口项目协议混用增加头端复杂度。
**改进**：头端多协议适配；对象模型在 MDMS 统一；文档化 OBIS↔本地点表映射[3][9]。

## 参考文献

[1] DLMS UA, *Green Book* — COSEM interface classes and OBIS, recent edition.
[2] IEC 62056-5-3, DLMS/COSEM application layer.
[3] IEC 62056-6-2, OBIS object identification system.
[4] PRIME Alliance, PRIME specification (PLC).
[5] G3-PLC Alliance, G3-PLC specification.
[6] IEC 62056-21, direct local data exchange (optical port related).
[7] DLMS UA security / suite documentation.
[8] HDLC profiling for DLMS (IEC 62056-46 and related).
[9] AMI / MDMS architecture references (utility industry).
[10] DLMS over CoAP / cellular IoT metering profiles.
[11] DLMS UA conformance certification program documents.
[12] Smart meter cybersecurity guidelines (ENISA/NIST-style utility guidance).
