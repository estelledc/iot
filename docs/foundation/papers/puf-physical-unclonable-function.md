---
schema_version: '1.0'
id: puf-physical-unclonable-function
title: 物理不可克隆函数PUF设备指纹技术
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - arm-trustzone-iot-security
tags:
  - PUF
  - 硬件安全
  - 设备指纹
  - SRAM PUF
  - 密钥生成
  - 模糊提取
  - IoT安全
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 物理不可克隆函数PUF设备指纹技术

> **难度**：🔴 高级 | **领域**：硬件安全原语 | **关键词**：PUF, CRP, 模糊提取, SRAM | **阅读时间**：约 16 分钟

## 日常类比

没有两片完全相同的树叶；同一晶圆上的芯片也因制造随机性有微观差异。**物理不可克隆函数**（Physical Unclonable Function, PUF）把这些差异变成设备“指纹”：密钥不必长期明文存放在非易失存储器，而可在需要时从物理响应重建[1][2]。

## 摘要

介绍挑战-响应（Challenge-Response Pair, CRP）、可靠性与唯一性指标、静态随机存储器（SRAM）/环形振荡器等实现，以及模糊提取与辅助数据。误码率与熵值为条件相关量级[3]。

## 1. 基本模型

输入挑战 → 物理乱序映射 → 响应。理想：同挑战同器件可重复；不同器件不可预测；难以物理克隆。评价指标含可靠性（噪声下稳定）、唯一性（器件间汉明距离）、均匀性与 thruput[1]。

| 类型 | 机制概要 | IoT 常见度 |
|------|----------|------------|
| SRAM PUF | 上电初始态倾向 | 高（多 MCU 可做） |
| RO PUF | 振荡器频率差 | 中 |
| Arbiter PUF | 延时竞赛 | 研究/部分安全芯片 |
| DRAM/Flash 等 | 其他熵源 | 视平台 |

## 2. 噪声与模糊提取

温度、电压、老化使响应比特翻转。用模糊提取器（Fuzzy Extractor）/辅助数据（Helper Data）纠错并派生密钥，同时避免辅助数据泄露过多熵[2][4]。注册阶段在安全环境采集，现场重建。

| 步骤 | 内容 |
|------|------|
| 注册 | 多次测量、生成 helper、存非敏感辅助数据 |
| 重建 | 测量响应 + helper → 稳定密钥 |
| 使用 | 作为根密钥密封、设备身份、挑战响应认证 |

## 3. 攻击面与系统集成

建模攻击（机器学习预测 CRP）、辅助数据泄露、半侵入探测、故障注入均可削弱 PUF。强 PUF 需大 CRP 空间；弱 PUF 更适合成密钥根。与信任根、安全启动、证书供给链结合时，仍要保护重建路径与调试口[5][6]。

## 4. 局限、挑战与可改进方向

### 1. 可靠性随环境恶化

**局限**：极限温/压下误码升高导致认证失败。
**改进**：加余量纠错；多温注册；电压监测后再重建[3][4]。

### 2. 熵与唯一性不足

**局限**：部分批次相关性高，身份碰撞风险。
**改进**：熵测试；与芯片唯一 ID 混合派生；选经评估的 IP[7]。

### 3. 辅助数据安全假设被打破

**局限**：helper 设计不当泄露密钥信息。
**改进**：用标准模糊提取构造；威胁建模审查存储位置[4]。

### 4. 建模与侧信道

**局限**：公开 CRP 接口可被学习。
**改进**：限制挑战接口；用弱 PUF 作根+密码协议；物理防护[5]。

## 总结

PUF 提供“生而有之”的设备密钥素材，但必须配齐纠错、熵评估与系统威胁模型；它替代的是密钥存储方式，不是整体安全架构。

## 参考文献

[1] Gassend et al., Silicon physical random functions (early PUF).
[2] Maes, Physically Unclonable Functions: Constructions and Applications.
[3] SRAM PUF reliability under temperature/voltage variation studies.
[4] Dodis et al., Fuzzy extractors and helper data theory.
[5] Machine-learning modeling attacks on arbiter PUFs (survey papers).
[6] Integration of PUF with secure boot and device identity.
[7] NIST / industry guidance on entropy sources (contextual).
[8] RO-PUF design and aging effects literature.
[9] Side-channel considerations for PUF key reconstruction.
[10] Commercial MCU PUF / device-unique key features (vendor ANs).
[11] Weak vs strong PUF taxonomy and use-case mapping.
[12] Helper data manipulation and countermeasures.
