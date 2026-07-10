---
schema_version: '1.0'
id: iot-radio-certification-process
title: IoT无线设备射频认证流程与测试
layer: 2
content_type: tutorial
difficulty: intermediate
reading_time: 20
prerequisites:
  - frequency-band-regulation-iot
  - antenna-testing-ota-measurement
tags:
  - 射频认证
  - FCC
  - CE RED
  - SRRC
  - EMC
  - 预认证模组
  - 杂散辐射
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT无线设备射频认证流程与测试

> **难度**：🟡 中级 | **领域**：合规认证 | **阅读时间**：约 20 分钟

## 日常类比

上路要车检与行驶证；无线产品要射频认证才能合法销售。频谱是公共资源，认证用来约束发射功率、杂散与电磁兼容（Electromagnetic Compatibility, EMC），避免“抢道乱鸣”[1][3]。

## 摘要

有意辐射体（Intentional Radiator）通常走实验室认证；无意辐射体偏 EMC。预认证模组可缩短周期，但天线增益与集成方式仍受证书约束。费用与周期随实验室与改版次数变化，**文中区间仅供量级参考**[5]。

## 1. 为何强制

| 市场 | 依据/机构 | 未认证销售后果（概要） |
|------|-----------|------------------------|
| 美国 | FCC（Communications Act 等） | 罚款、禁售等，以现行执法为准 |
| 欧盟 | RED 2014/53/EU，CE | 扣押、召回、成员国执法 |
| 中国 | 无线电管理条例，SRRC 型号核准 | 没收、行政处罚等 |
| 日本 | 电波法，MIC/TELEC | 限值严、需合规证明 |

技术上验证：功率限值、杂散、占用带宽、频率稳定度、整机 EMC[1][2]。

## 2. 主要体系

| 地区 | 名称 | IoT 常见路径 |
|------|------|--------------|
| 美国 | FCC Part 15 等 | 多数有意辐射体走 Certification |
| 欧盟 | CE RED | EN 300 220 / 328 / 301 893 等 |
| 中国 | SRRC | 含发射功能设备型号核准 |
| 加拿大 | ISED | 与 FCC 报告常可部分复用 |
| 日/韩/澳/印 | MIC、KCC、RCM、WPC 等 | 本地代理或本地测常见 |

FCC 示意：有意辐射体 → Certification；无意 → SDoC 等简化路径（以现行规则为准）[1]。

## 3. 有意 vs 无意

典型 IoT 节点 = MCU/电源（无意辐射）+ 无线模组/天线（有意辐射），常需 **RF + EMC** 双线。Wi-Fi/BLE/LoRa/蜂窝/LPWAN 发射功能属有意辐射。

## 4. 关键测试项

| 项目 | 含义 | 失败常见度 |
|------|------|------------|
| 传导功率 | 天线口功率（不含天线增益） | 中 |
| 杂散/谐波 | 工作频外不需要的辐射 | 高 |
| 占用带宽 | 含约 99% 功率的带宽 | 中 |
| 频率稳定度 | 温/压变化下频偏（常以 ppm 计） | 中 |

限值因标准而异：如 Part 15.247 扩频传导功率上限与 ETSI EN 300 220 的 ERP 上限不同，**以目标市场现行版为准**[1][2]。杂散常是首败项；设计阶段预留滤波与功率余量。

## 5. 实验室与设施

选 ISO/IEC 17025 认可实验室，并确认目标市场认可（如 NVLAP、CNAS）。设施含全/半电波暗室、屏蔽室、开阔场（OATS）等。

## 6. 模组策略

| 策略 | 优点 | 限制 |
|------|------|------|
| 预认证模组 | 周期短、费用常显著下降 | 天线类型/增益、布局须符合集成指南 |
| 自研射频 | 成本与形态可控 | 全量 RF 认证，风险高 |

改射频参数或超增益天线会使模组证书失效。Espressif、Murata、Quectel、Nordic 等常见模组多国证书需按料号核对，**勿假设“同系列全覆盖”**。

## 7. 流程与成本量级

典型：预扫 → 整改 → 正式测 → 递交 → 发证。单市场数周到数月；多市场并行可复用部分报告。公开报价常见数千至上万美元量级（含公告机构），**以询价为准**；预算应含至少一次失败整改[5]。

## 8. 案例要点（Sub-GHz LoRa）

谐波落入其他业务频段时，馈点低通滤波常有效；区域固件锁定合法带宽（如欧区限制过宽 SF/BW 组合）。验收看限值余量（数 dB），而非“刚好压线”。时间线含一次改版时，数月量级较常见。

## 9. 局限、挑战与可改进方向

### 1. 杂散与谐波

**局限**：数字噪声与功放非线性易导致带外超标[1][2]。
**改进**：分区布局、完整地平面、预留谐波滤波、功率低于限值数 dB 余量。

### 2. 多市场重复测

**局限**：限值与流程不一，成本叠加。
**改进**：FCC/ISED 报告复用；系列化申请；优先预认证模组。

### 3. 模组误用

**局限**：换高增益天线或改匹配导致证书失效仍上市。
**改进**：严格遵循集成指南；变更走变更评估/重测。

### 4. 晚测风险

**局限**：定型后才预扫，改版伤工期。
**改进**：原理样机即 pre-scan；全模式（含最大占空比）覆盖。

## 10. 实践要点

1. 立项即定目标市场与有意/无意路径。
2. 能用预认证模组则优先；自研则预留滤波与功率余量。
3. 材料包：原理图/布局、框图、说明书、照片、标签、天线规格。

## 参考文献

[1] FCC, 47 CFR Part 15, Radio Frequency Devices.
[2] ETSI EN 300 220, Short Range Devices (25 MHz to 1 GHz), current version.
[3] Directive 2014/53/EU, Radio Equipment Directive (RED).
[4] 中华人民共和国无线电管理条例（现行有效文本）.
[5] Vendor/lab wireless certification guides (e.g. TI Sub-1 GHz certification app notes); treat cost/schedule as indicative.
[6] ETSI EN 300 328 / EN 301 893 (2.4 / 5 GHz related).
[7] ISED Canada RSS series and FCC report acceptance notes.
[8] ISO/IEC 17025, General requirements for testing laboratory competence.
[9] MIC/TELEC Japan radio equipment conformity materials.
[10] Module vendor integration guidelines (antenna gain, host conditions).
[11] FCC KDB publications on intentional radiators and modular approval.
[12] CNAS/NVLAP laboratory accreditation overviews for RF/EMC.
