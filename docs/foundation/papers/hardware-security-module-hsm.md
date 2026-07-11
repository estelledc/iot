---
schema_version: '1.0'
id: hardware-security-module-hsm
title: 硬件安全模块HSM在IoT设备中的集成
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites:
  - arm-trustzone-iot-security
  - mcu-boot-process-secure-boot
tags:
  - HSM
  - 安全元件
  - FIPS
  - 密钥管理
  - ATECC
  - 设备配给
  - 安全启动
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 硬件安全模块HSM在IoT设备中的集成

> **难度**：🔴 高级 | **领域**：设备安全 | **关键词**：HSM, SE, FIPS, 密钥配给, 安全元件 | **阅读时间**：约 18 分钟

## 日常类比

把家门钥匙藏在保险柜里，签字也在柜内完成——私钥永不出门。硬件安全模块（Hardware Security Module, HSM）或安全元件（Secure Element, SE）在物联网设备上扮演这只保险柜：生成/存储密钥并在片内完成签名与解密[1][2]。

## 摘要

区分网络 HSM 与嵌入式 SE、认证等级、密钥操作与配给流程，并给出与云物联网核心对接要点。价格与认证级别随型号变化，**以厂商与实验室报告为准**[3][4]。

## 1. 价值与形态

| 形态 | 典型位置 | 用途 |
|------|----------|------|
| 网络/云 HSM | 数据中心 | 根密钥、签发 |
| 嵌入式 SE/HSM | 设备 PCB | 设备身份、TLS、安全启动辅助 |
| TEE（如 TrustZone） | SoC 内 | 软件隔离，物理防护弱于 SE |

密钥运算在模块内完成，明文私钥不进 MCU 内存，是核心收益[1][5]。

## 2. 认证与产品

常见参照：FIPS 140-2/3、Common Criteria、GlobalPlatform SE 配置文件。物联网常用 I²C 器件（如 ATECC608A、SE050 等）提供椭圆曲线签名、安全存储与防篡改对策（能力因型号而异）[2][3][6]。

| 操作 | 说明 |
|------|------|
| 生成密钥 | 片内 RNG + 私钥槽 |
| 签名/验签 | 摘要进、签名出 |
| 协商 | ECDH 等会话材料 |
| 配给 | 产线写入证书/策略 |

## 3. 集成架构

MCU 经 I²C 发命令；安全启动可验证镜像签名；云连接用 SE 持有的设备证书做双向 TLS。产线配给需防夹具泄密：密钥注入在受控工位，日志审计[4][7]。勿把同一调试密钥烧进所有量产设备。

## 4. 局限、挑战与可改进方向

### 1. 产线配给薄弱

**局限**：统一密钥或明文烧录，一破全军覆没。
**改进**：单设备唯一密钥；授权工装；审计与报废流程[7]。

### 2. 侧信道与物理攻击

**局限**：低成本 SE 防护有限，实验室攻击仍可能。
**改进**：按威胁模型选认证等级；结合外壳与防拆[1][6]。

### 3. 性能与接口瓶颈

**局限**：I²C SE 高频握手延迟大。
**改进**：会话票证缓存；非热点路径异步签名[3]。

### 4. 与 TEE 职责不清

**局限**：重复存储或错误信任边界。
**改进**：根身份放 SE；会话与应用策略放 TEE/MCU 并文档化[5]。

## 总结

嵌入式 HSM/SE 是设备身份的根，不是可选外设。先定威胁与认证需求，再选器件，并把唯一化配给与云证书链路一次做对。

## 参考文献

[1] NIST FIPS 140-3, Security Requirements for Cryptographic Modules.
[2] Microchip, ATECC608A Data Sheet.
[3] NXP, SE050 Product Data Sheet.
[4] AWS, Connecting devices with ATECC608A to IoT Core（文档）.
[5] GlobalPlatform, Secure Element Protection Profile.
[6] Common Criteria, 安全芯片评估公开资料.
[7] PSA Certified / 设备配给最佳实践白皮书.
[8] ARM TrustZone 与 SE 协同架构应用笔记.
[9] RFC 5280 / 设备证书配置文件实践.
[10] ISO/IEC 19790（与 FIPS 相关的国际对照）.
[11] 侧信道攻击与抗性对策综述选篇.
[12] MQTT/TLS 物联网安全部署指南（云厂商）.
