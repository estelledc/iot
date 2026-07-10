---
schema_version: '1.0'
id: nfc-wireless-charging-qi-integration
title: NFC与Qi无线充电集成方案
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - nfc-ndef-data-exchange
tags:
  - NFC
  - Qi
  - WLC
  - 无线充电
  - 能量收集
  - 电磁感应
  - 天线共存
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# NFC与Qi无线充电集成方案

> **难度**：🟡 中级 | **领域**：NFC能量传输 | **阅读时间**：约 20 分钟

## 日常类比

电磁炉主要加热锅底；若同一套“感应”思路既能传数据又能给小夜灯供电，就接近 NFC 与 Qi 共存的故事。两者都靠电磁感应耦合，只是频率与功率目标不同：NFC 偏 13.56 MHz 通信，Qi 偏约 100–200 kHz 送电。

## 摘要

对比 Qi 与 NFC Forum 无线充电（Wireless Charging, WLC）、能量收集标签，以及同机天线/铁氧体/热与时分问题。功率与效率数字为规范或案例量级，**耦合与温升必须实测**[1][4]。

## 1. 物理与定位

| 参数 | NFC（通信/WLC） | Qi |
|------|-----------------|-----|
| 频率 | 13.56 MHz | 约 100–200 kHz |
| 主目标 | 数据；WLC 小功率能量 | 较大功率充电 |
| 功率量级 | 通信数十 mW；WLC 最高约 1 W 级 | 常见数瓦–十余瓦级 |
| 距离 | 通常数厘米 | 通常更贴合 |

高频利于小天线与数据；低频利于较高功率效率。二者互补多于替代：Qi 常是“板充手机”，WLC 常是“手机给小配件应急充”[1][4]。

## 2. NFC WLC 要点

角色：WLC Poller（常为手机）与 Listener（耳机/笔/传感器等）。同载波上协商功率、增强场强送能，并周期性交换电压/电流/温度等状态；通信与充电常时分，避免强场毁通信质量[1]。

| 功率等级（规范类） | 量级 | 场景方向 |
|--------------------|------|----------|
| 较低 Class | 约数百 mW | 标签刷新、极小穿戴 |
| 较高 Class | 接近约 1 W | 笔、小耳机等 |

效率常明显低于 Qi（高频损耗、手机 NFC 天线非为功率优化）——对小电池仍可能够用，但**勿宣传“接近有线效率”**[1][5]。

## 3. 能量收集（非完整 WLC）

无源标签本就从场取电；扩展后经 VOUT 短时供 MCU/传感器，手机离开即掉电。NTAG I2C / ST25DV 等方案：场→取电→采样→写入共享内存→手机读回。可读功率预算仅数十 mW 量级，只适合短任务[2][3]。

## 4. 与 Qi 同机集成

| 挑战 | 现象 | 常见对策 |
|------|------|----------|
| 天线互耦 | 谐振/Q 值漂移 | 分层+铁氧体隔离；匹配滤波 |
| 金属结构 | 屏蔽、涡流发热 | 铁氧体导磁；布局避电池壳 |
| 热 | 损耗变温升 | 功率降额、占空比、导热路径 |
| 时序 | 强场与通信冲突 | TDM：多充少通 |

手机堆叠常见：背壳侧 NFC 线圈 / 共用铁氧体 / Qi 线圈 / 散热 / 电池。反向 Qi（手机当发射）与 NFC WLC 目标不同，勿混为一谈[4][6]。

## 5. IoT 价值

冷链/巡检标签“一扫上电读数”；产线“一贴：取电+配网+写参”；小配件忘带充电器时的应急补能。大功率快充仍归 Qi/有线。

## 6. 局限、挑战与可改进方向

### 1. 功率天花板

**局限**：约 1 W 级撑不起中大电池快充叙事。
**改进**：明确应急/微功率定位；更大能量走 Qi 或触点。

### 2. 天线与结构敏感

**局限**：外壳、握持、错位使耦合骤降。
**改进**：多姿态效率图；对齐磁吸/凹槽；产测耦合窗口。

### 3. 热与安全

**局限**：小腔体温升快，有皮肤接触风险。
**改进**：温度闭环降功率；超时停充；材料与安规测试。

### 4. 标准与生态碎片

**局限**：手机 WLC 支持度不均，IoT 不能假设“任意手机可充”。
**改进**：产品说明写明支持机型/模式；提供有线或 Qi 备份。

## 7. 实践要点

1. 先算 Listener 电池与可接受充电时间，再选 WLC 或仅能量收集。
2. NFC+Qi 共板必须联合仿真/实测互耦与 SAR/温升。
3. “充电+配置”流程要定义失败回退（场弱、电量不足、写失败）。

## 参考文献

[1] NFC Forum, Wireless Charging (WLC) Technical Specification.
[2] STMicroelectronics, ST25DV-W / energy harvesting application notes.
[3] NXP, NTAG I2C Plus datasheet (I2C + energy harvesting).
[4] Wireless Power Consortium, Qi specification (version per product needs).
[5] Academic/industry analyses of NFC-based wireless charging efficiency for low-power IoT.
[6] Handset antenna stack-up and ferrite isolation design notes (vendor app notes).
[7] ISO/IEC 18092 / NFC Forum analog related docs (13.56 MHz field context).
[8] WPC Qi Extended Power Profile materials (higher-power contrast).
[9] Nordic / PMICs pairing notes for harvested NFC power (system design context).
[10] Regulatory guidance on wireless power and RF exposure (region-specific).
[11] NFC Forum, Listener/Poller role definitions in WLC.
[12] Comparative surveys of energy harvesting for passive sensor tags.
