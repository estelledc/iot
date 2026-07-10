---
schema_version: '1.0'
id: chopper-stabilized-amplifier
title: 斩波稳定放大器消除低频噪声与失调
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - instrumentation-amplifier-ina
  - signal-conditioning-amplifier-filter
tags:
  - 斩波放大器
  - 失调电压
  - 1/f噪声
  - 自动调零
  - 精密模拟
  - 低漂移
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 斩波稳定放大器消除低频噪声与失调

> **难度**：🔴 高级 | **领域**：精密放大器技术 | **阅读时间**：约 16 分钟

## 日常类比

普通运放像略近视的测量员：有固定视差（输入失调电压 Vos）和越来越粗的手抖（1/f 闪烁噪声）。斩波稳定像给镜架加高频振动：把有用信号搬到“手抖最弱”的频段放大，再搬回基带；失调与 1/f 被搬到斩波频率附近，用低通滤掉[1][2]。

## 摘要

讲清调制–放大–解调链路、残余失调/纹波、与自动调零对比及选型。Vos、噪声密度为器件量级，**以具体型号数据手册与应用电路为准**[3][4]。

## 1. 低频精度杀手

| 问题 | 表现 | 传感器场景 |
|------|------|------------|
| Vos | μV–mV 级被增益放大 | 热电偶、分流 |
| Vos 温漂 | μV/°C 量级累积 | 长期监测 |
| 1/f 噪声 | 越近直流越大 | 慢变桥路 |

高增益直流测量中，误差源常大于被测增量[1][5]。

## 2. 斩波原理

输入斩波开关把信号乘以方波，频谱移到 f_chop；放大器在白噪声区工作；输出同步解调把信号搬回直流，同时把放大器自身失调与 1/f 搬到 f_chop，再经低通（Low-Pass Filter, LPF）[2][6]。

| 项目 | 叙事 |
|------|------|
| f_chop | 常 kHz–MHz 级，高于 1/f 拐角 |
| 理想 Vos | 可压到 μV 以下甚至 nV 级叙事 |
| 代价 | 斩波纹波、带宽受 LPF、开关电荷注入 |

残余来自电荷注入失配、时钟馈通等；可用互补开关、伪开关、全差分与纹波消除环路缓解[2][7]。

## 3. 斩波 vs 自动调零

| 特性 | 斩波 | 自动调零 |
|------|------|----------|
| 时间域 | 连续调制 | 两相采样 |
| 1/f | 搬移滤除 | 采样相消除 |
| 白噪声 | 通常不因折叠倍增 | 常有噪声折叠 |
| 输出伪影 | 纹波 | 切换毛刺 |
| 带宽 | 受 LPF | 受采样率 |

混合架构（斩波 + 自动调零）常见于现代精密运放，兼顾极低失调与噪声[3][4]。

## 4. 应用与选型线索

| 应用 | 为何需要 |
|------|----------|
| 热电偶/RTD 前端 | 微伏级、近直流 |
| 应变/桥路 | 高增益放大 |
| 分流电流检测 | 微伏压降 |
| pH/电化学 | 高阻+慢变 |

关注：Vos 与温漂、低频噪声、输入偏置、斩波纹波规格、供电范围与 GBW。输出后常需与 ADC 带宽/滤波匹配，避免把纹波当信号[8][9]。

## 5. 局限、挑战与可改进方向

### 1. 当“零失调万能运放”

**局限**：纹波与有限带宽在脉冲/交流路径惹祸。
**改进**：看清信号频谱；必要时后级滤波或选低纹波型号。

### 2. 高阻源不看电流噪声与偏置

**局限**：斩波再好也被偏置×源阻淹没。
**改进**：匹配传感器阻抗；防护环与泄漏控制。

### 3. 布局把开关噪声耦合进输入

**局限**：数字时钟边沿经寄生进差分对。
**改进**：对称布线、短输入、模拟地策略、电源去耦。

### 4. 忽略温度循环迟滞

**局限**：焊点应力与封装迟滞造成“慢失调”。
**改进**：应力隔离、合适封装、温循老化筛选。

## 6. 实践要点

1. 直流微伏级优先斩波/零漂移系列，并读纹波指标。
2. 用信号带宽定 LPF，不要只抄典型电路。
3. 与仪表放大器/ADC 链路统一噪声预算。

## 参考文献

[1] C. C. Enz and G. C. Temes, "Circuit techniques for reducing the effects of op-amp imperfections," Proc. IEEE, 1996.
[2] C. C. Enz et al., chopper stabilization tutorial literature.
[3] Texas Instruments, OPA388 / zero-drift amplifier datasheets and ANs.
[4] Analog Devices, ADA4522 and zero-drift amplifier design notes.
[5] Maxim/ADI, MAX44246 and related precision amp docs.
[6] Wongkomet / analog IC texts on chopper amplifiers.
[7] Papers on charge injection and clock feedthrough cancellation.
[8] Bridge sensor and thermocouple conditioning application notes (ADI/TI).
[9] Noise analysis: 1/f corner and input-referred noise density guides.
[10] Auto-zero vs chopper comparison app notes (vendor).
[11] Horowitz & Hill, precision amplifier chapters.
