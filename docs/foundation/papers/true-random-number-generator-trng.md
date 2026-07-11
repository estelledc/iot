---
schema_version: '1.0'
id: true-random-number-generator-trng
title: 真随机数发生器TRNG原理与IoT安全应用
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - arm-trustzone-iot-security
  - secure-element-se-iot
  - puf-physical-unclonable-function
tags:
  - TRNG
  - 熵源
  - 密码学
  - IoT安全
  - 随机数
  - NIST
  - 密钥生成
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 真随机数发生器TRNG原理与IoT安全应用

> **难度**：🔴 高级 | **领域**：嵌入式安全 | **关键词**：TRNG, 熵, CSPRNG, NIST | **阅读时间**：约 16 分钟

## 日常类比

掷公平骰子得真随机；用固定公式算“随机”是伪随机。真随机数发生器（True Random Number Generator, TRNG）采集物理噪声当熵，再健康检测与调理，供密钥与 nonce[1][2]。

## 摘要

区分熵源、TRNG 与密码学安全伪随机（CSPRNG）、常见电路噪声源、健康测试与物联网（IoT）使用模式。安全声明需对照标准与认证，而非仅有“TRNG”外设名[2][3]。

## 1. 架构

| 级 | 作用 |
|----|------|
| 熵源 | 热噪声、抖动、亚稳态等 |
| 数字化 | 采样比较 |
| 健康测试 | 卡死/重复检测 |
| 调理 | 压缩偏差 |
| CSPRNG | 用种子扩展大量比特 |

| 用途 | 要求 |
|------|------|
| 密钥生成 | 高熵、保密 |
| Nonce/IV | 不重复 |
| 协议挑战 | 不可预测 |
| 抖动延迟 | 可用较弱熵（视威胁） |

## 2. IoT 实践

上电先积累熵再生成密钥；种子注入安全元件更佳。无 TRNG 时慎用仅 ADC 噪声，需评估攻击面[3][4]。

## 3. 局限、挑战与可改进方向

### 1. 熵枯竭与启动

**局限**：冷启动熵不足仍出密钥。
**改进**：阻塞至健康通过；外部熵种子[2]。

### 2. 实现漏洞

**局限**：偏置或可操纵噪声。
**改进**：遵循 NIST SP 800-90B 等评估；认证芯片[1]。

### 3. 侧信道

**局限**：功耗泄露随机操作。
**改进**：常量时间；安全元件内生成[4]。

### 4. 把 PRNG 当 TRNG

**局限**：可预测种子导致全盘崩溃。
**改进**：架构审查；独立熵路径[3]。

## 总结

随机性是安全协议的燃料。IoT 设备应把 TRNG 健康状态当安全依赖，密钥在受保护环境中派生，并避免“裸 ADC 噪声”幻想。

## 参考文献

[1] NIST SP 800-90B, Entropy Sources.
[2] NIST SP 800-90A, DRBG 机制.
[3] ARM / MCU TRNG 外设应用笔记.
[4] 安全元件密钥生成最佳实践.
[5] AIS 31 / 欧洲随机数评估方法概述.
[6] 抖动熵源设计文献.
[7] IoT 设备身份与设备密钥生命周期.
[8] 侧信道与随机数实现安全.
[9] PUF 与 TRNG 分工说明.
[10] FIPS 140 随机数相关要求概述.
[11] 健康测试失效模式案例.
[12] TLS 中的随机数使用注意.
