---
schema_version: '1.0'
id: relay-solid-state-relay-iot
title: 继电器与固态继电器在IoT控制中的选型
layer: 1
content_type: comparison
difficulty: beginner
reading_time: 14
prerequisites:
  - pwm-motor-control-embedded
tags:
  - 继电器
  - 固态继电器
  - SSR
  - 强电控制
  - 光耦
  - 触点
  - IoT执行器
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 继电器与固态继电器在IoT控制中的选型

> **难度**：🟢 入门 | **领域**：执行器控制 | **关键词**：继电器, SSR, 触点, 光耦隔离 | **阅读时间**：约 14 分钟

## 日常类比

细绳拉不动铁门，加滑轮就能省力。电磁继电器用微控制器（MCU）的弱电信号驱动线圈，去通断强电；**固态继电器**（Solid-State Relay, SSR）是无机械触点的“电子滑轮”——更快、无火花，但有通态压降与漏电流等代价[1][2]。

## 摘要

对比机械继电器与 SSR 的原理、电气特性、驱动与安全隔离，给出物联网场景选型表。寿命与漏电流为典型量级，以型号数据手册为准[3]。

## 1. 电磁继电器

线圈励磁 → 衔铁动作 → 触点通断。优点：通态接近短路、关断接近开路、可切交流/直流（视触点）。代价：寿命有限、有动作声与弹跳、线圈功耗、需续流二极管[1]。

| 参数 | 关注 |
|------|------|
| 触点额定 | 电压/电流/负载类型（阻性/感性） |
| 线圈电压 | 与驱动电平匹配，注意吸合/释放 |
| 绝缘 | 线圈-触点耐压与爬电 |

## 2. 固态继电器

输入侧发光，输出侧晶闸管/晶体管导通；交流 SSR 常过零触发降干扰。优点：无机械磨损、开关快、耐震。代价：通态压降发热、关断漏电流、直流/交流类型不可混用、浪涌需保护[2][4]。

| 维度 | 机械继电器 | SSR |
|------|------------|-----|
| 寿命 | 有限动作次数 | 通常更长（热是瓶颈） |
| 通态损耗 | 极低 | 有压降，需散热 |
| 漏电流 | 近零 | 不可忽略 |
| 噪声/EMI | 触点电弧 | 开关边沿/dv/dt |
| 多路成本 | 常较低 | 功率级更贵 |

## 3. 驱动与安全

MCU 勿直接灌大线圈电流：用晶体管/驱动芯片 + 续流。SSR 输入注意电流限流电阻。外壳、爬电距离、保险丝与浪涌吸收（压敏/RC）按安规；隔离并不自动等于触电安全设计[5]。

## 4. 局限、挑战与可改进方向

### 1. 感性负载拉弧

**局限**：电机/电磁阀缩短触点寿命。
**改进**：RC/压敏；选合适触点材料；改 SSR 或接触器[3]。

### 2. SSR 漏电流点亮 LED 灯

**局限**：关断仍微亮或误测。
**改进**：并联假负载；选低漏型号；改机械继电器[4]。

### 3. 发热与密闭壳

**局限**：多路 SSR 温升触发降额。
**改进**：散热片、降额曲线、分散布局[2]。

### 4. 隔离与布线混用

**局限**：强弱电共地或爬电不足。
**改进**：分区布线；遵循安规间距；独立电源[5]。

## 总结

偶发通断、要真正开路、低发热 → 机械继电器；频繁开关、怕触点磨损、可接受漏电与散热 → SSR。按负载类型与安规，而不是只看“能不能吸合”。

## 参考文献

[1] Electromechanical relay application notes (coil, contact ratings).
[2] Solid-state relay manufacturer handbooks (Crydom/Omron class).
[3] Inductive load suppression and contact protection.
[4] SSR leakage current and snubber network notes.
[5] Isolation, creepage, and safety standards context for mains switching.
[6] MCU driver circuits for relay coils (flyback diode).
[7] Zero-cross vs random-fire AC SSR selection.
[8] Inrush of lamps/motors vs relay/SSR surge ratings.
[9] Thermal derating curves for SSR modules.
[10] Relay bounce and software debounce practices.
[11] Hybrid approaches: relay for isolation + SSR for wear.
[12] IoT smart-plug design EMC and safety checklists.
