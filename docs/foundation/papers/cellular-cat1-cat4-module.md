---
schema_version: '1.0'
id: cellular-cat1-cat4-module
title: 蜂窝Cat.1/Cat.4模组硬件选型与集成
layer: 1
content_type: comparison
difficulty: intermediate
reading_time: 16
prerequisites:
  - chip-antenna-vs-pcb-antenna
tags:
  - LTE
  - Cat.1
  - Cat.4
  - 蜂窝模组
  - 模组集成
  - VoLTE
  - 电源设计
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 蜂窝Cat.1/Cat.4模组硬件选型与集成

> **难度**：🟡 中级 | **领域**：蜂窝模组集成 | **阅读时间**：约 16 分钟

## 日常类比

蜂窝网像现成高速公路：基站已建好，插用户识别模块（Subscriber Identity Module, SIM）就能跑。长期演进（Long Term Evolution, LTE）Category 像车道等级：Cat.4 像多车道快道（下行峰值叙事约 150 Mbps），Cat.1 像单车道够用道（约 10 Mbps）。选车道看日流量、时延与账单，不看广告峰值[1][2]。

## 摘要

对比 Cat.1 / Cat.1bis / Cat.4 能力、模组接口、电源与天线集成要点。速率与价格为量级，**以 3GPP 类别定义与模组数据手册为准**[1][3]。

## 1. Category 定位

| Category | 下行/上行峰值叙事 | 空间复用叙事 | 典型用途 |
|----------|-------------------|--------------|----------|
| Cat.1 | ~10 / ~5 Mbps | 1 层 | IoT 中速 |
| Cat.1bis | 同量级，效率增强 | 1 层 | 新品主流 |
| Cat.4 | ~150 / ~50 Mbps | 2 层 MIMO | 视频/CPE |
| Cat.M1 等 | 更低 | — | 低频上报 |

Cat.4 基带更复杂（多输入多输出 MIMO、更宽带宽），功耗与成本通常明显高于 Cat.1。Cat.1bis 为 Rel-14 增强，常补齐 64QAM/VoLTE 等能力叙事[1][2]。

## 2. 选型线索

| 需求 | 更常见选择 |
|------|------------|
| 日流量大或需视频 | Cat.4 |
| 图片/语音/中速遥测 | Cat.1 / 1bis |
| 需语音通话 | 选支持 VoLTE 的 Cat.1bis/Cat.4 |
| 需定位 | GNSS 可选版本 |
| 主机只有 UART | Cat.1 更匹配；Cat.4 宜 USB |

模组品牌与料号迭代快（移远/SIMCom/广和通等），以当时区域频段认证与供货为准，勿死记单一料号[3][4]。

## 3. 硬件集成

| 接口 | 速率叙事 | 注意 |
|------|----------|------|
| UART | 常用至数百 kbps–约 1 Mbps 级 | 建议硬件流控 |
| USB 2.0 | 更高吞吐 | Cat.4 发挥速率常用 |

电源：VBAT 常见约 3.3–4.2 V；发射瞬态可达安培级。需足够体电容（钽电 + 多层陶瓷电容组合常见）、宽铜与合适直流-直流变换，避免与微控制器（MCU）抢同一脆弱低压差线性稳压器（LDO）[5][6]。

SIM：时钟/数据/复位走线短，数据上拉，静电放电（ESD）保护；天线覆盖目标运营商频段，驻波比（VSWR）与效率按手册，Cat.4 常需主集+分集[7][8]。

| 项目 | 要求叙事 |
|------|----------|
| VSWR | 常见目标 < 2:1 量级 |
| 效率 | 内置天线常见数成以上，看手册 |
| 净空 | 无铜/无器件区按模组指南 |
| MIMO 间距 | 与波长相关，需结构预留 |

## 4. 局限、挑战与可改进方向

### 1. 用峰值 Mbps 估月流量成本

**局限**：实际吞吐受信号、调度与协议开销限制。
**改进**：按业务报文与重试做流量模型；外场测 RSRP/吞吐。

### 2. 电源按平均电流设计

**局限**：发射尖峰掉电复位，难复现。
**改进**：按峰值电流与压降设计；示波器抓 VBAT 跌落。

### 3. 天线净空被结构件侵占

**局限**：实验室 OK，金属壳/电池上量后掉网。
**改进**：早期结构协同；OTA/传导联合验收。

### 4. AT 固件与证书碎片

**局限**：TLS/证书存储、模组 SDK 差异导致量产差异。
**改进**：锁定固件版本；安全存储与证书注入流程标准化。

## 5. 实践要点

1. 日流量与是否视频先分流 Cat.1 vs Cat.4。
2. 电源与天线是集成两大坑，优先于“先调通 AT”。
3. 认证：模组预认证 ≠ 整机免测，见 CE/FCC 专文。

## 参考文献

[1] 3GPP TS 36.306, User Equipment (UE) radio access capabilities.
[2] 3GPP Release 14 Cat.1bis related specifications.
[3] Quectel EC200/EC800 series hardware design documents (examples).
[4] SIMCom SIM7600 / A7670 series hardware design documents (examples).
[5] Cellular module power supply design application notes (vendor).
[6] TI/ADI app notes on pulsed load and bulk capacitance for RF PAs.
[7] Antenna design guidelines for LTE modules (vendor AN).
[8] GSMA / operator band plans (regional) overview notes.
[9] USB CDC / PPP / QMI host interface documentation (module vendors).
[10] ETSI / FCC cellular device certification overview.
[11] 3GPP TS 27.007 AT command set (related).
