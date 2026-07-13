---
schema_version: '1.0'
id: adc-sar-vs-sigma-delta
title: SAR ADC与Sigma-Delta ADC架构对比与选型
layer: 1
content_type: comparison
difficulty: intermediate
reading_time: 16
prerequisites:
  - adc-resolution-snr-enob
  - oversampling-noise-shaping-adc
tags:
  - SAR
  - Sigma-Delta
  - ADC选型
  - 过采样
  - 多路复用
  - ENOB
  - 低功耗
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# SAR ADC与Sigma-Delta ADC架构对比与选型

> **难度**：🟡 中级 | **领域**：数据转换器选型 | **阅读时间**：约 16 分钟

## 日常类比

逐次逼近（Successive Approximation Register, SAR）像快手称菜：加减砝码，N 步出结果——快，精度受“砝码”精细度限制。Sigma-Delta（ΔΣ）像耐心统计员：高速过采样再平均/整形——慢工出细活。物联网传感器多在这两者间选型[1][3]。

## 摘要

对比 SAR 与 ΔΣ 的速度–分辨率、噪声谱、多路切换、延迟与功耗，并给决策树。采样率、功耗与价格为**代表器件量级**，以数据手册为准[3][5]。

## 1. 原理速写

| | SAR | Sigma-Delta |
|--|-----|-------------|
| 核心 | 电容 DAC 二分搜索 | 过采样 + 噪声整形 + 抽取 |
| 转换 | 约 N 个时钟/次 | 连续调制 + 数字滤波 |
| 典型分辨率线索 | 约 12–18 bit | 输出常 24 bit 格式 |
| 典型速率线索 | 可达 MSPS 级 | 高精度时常 SPS–kSPS |

ΔΣ：过采样稀释量化噪声，环路把噪声推向高频，数字滤波器清掉带外；故 1-bit 量化器也可得高 ENOB[4][5]。

## 2. 关键权衡表

| 维度 | 更偏 SAR | 更偏 ΔΣ |
|------|----------|---------|
| 带宽/速率 | 更高 | 更低（高精度时） |
| 有效精度 | 中高 | 直流/低频极高 |
| 通道切换 | 快，几乎每样独立 | 滤波器重建慢 |
| 延迟 | µs 量级常见 | ms 群延迟常见 |
| 抗混叠 | 更依赖模拟 AA | 过采样放宽模拟 |
| 间歇关断 | 易做极低平均功耗 | 常有静态偏置 |

| 应用线索 | 常见选择 |
|----------|----------|
| 振动/电机闭环 | SAR |
| 温度/称重/uV 电桥 | ΔΣ（常带 PGA） |
| 多路快速扫描 | SAR |
| 同步电能计量 | 多通道 ΔΣ 或同步 SAR |

注意：24-bit ΔΣ 的 ENOB 常明显低于 24，须看噪声与输出速率曲线[3][4]。

## 3. 选型流程（简）

```
带宽高或切换快？ → SAR
需要 20+ bit 有效或 uV 级？ → ΔΣ
超低功耗间歇唤醒？ → 常 SAR
否则看成本、驱动与供货
```

检查：输入范围、基准、AA 滤波、同步需求、SPI/I2C、生命周期供货[3]。

## 4. 局限、挑战与可改进方向

### 1. 只比标称位数

**局限**：选错架构，系统延迟或精度不合格。
**改进**：用 ENOB@目标数据率对比；读噪声 vs OSR 图。

### 2. ΔΣ 多路当 SAR 用

**局限**：每通道等待建立，吞吐崩盘。
**改进**：降切换率、每通道一颗、或改 SAR/同步采样器件。

### 3. SAR 省掉抗混叠

**局限**：带外折叠进带内。
**改进**：按 fs 设计模拟低通；或提高采样率再数字滤。

### 4. 低速场景仍选高功耗 ΔΣ

**局限**：电池寿命短。
**改进**：看关断电流与单次能量；评估 SAR 突发采样。

## 5. 实践要点

1. 口诀：**快变多路选 SAR，慢而求精选 ΔΣ**。
2. 先定信号带宽与通道策略，再挑具体料号。
3. 用同条件测 ENOB/延迟验收，不采信首页位数。

## 参考文献

[1] W. Kester, Data Conversion Handbook, Analog Devices.
[2] B. Razavi, Principles of Data Conversion System Design.
[3] Texas Instruments, SAR vs Delta-Sigma ADCs (SBAA385 lineage).
[4] Analog Devices, Sigma-Delta ADC tutorial (MT-022 lineage).
[5] R. Schreier and G. C. Temes, Understanding Delta-Sigma Data Converters.
[6] Representative datasheets: ADS1115, ADS1256, ADS131M04, AD76xx/MAX111xx class.
[7] Multiplexed delta-sigma settling time application notes.
[8] SAR CDAC architecture primers (vendor training).
[9] Anti-aliasing filter requirements for Nyquist SAR converters.
[10] PGA + ADC noise calculations for bridge sensors.
[11] Low-power ADC duty-cycling strategies for IoT nodes.
