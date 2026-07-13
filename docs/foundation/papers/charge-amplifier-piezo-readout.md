---
schema_version: '1.0'
id: charge-amplifier-piezo-readout
title: 电荷放大器在压电传感器读出电路中的设计
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - piezoelectric-vibration-sensor
  - signal-conditioning-amplifier-filter
tags:
  - 电荷放大器
  - 压电
  - 模拟前端
  - 振动传感
  - 反馈电容
  - 低噪声运放
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 电荷放大器在压电传感器读出电路中的设计

> **难度**：🟡 中级 | **领域**：传感器模拟前端 | **阅读时间**：约 16 分钟

## 日常类比

压电传感器像只吐“电脉冲”的微型发电机：敲一下吐出一股电荷，很快经漏电阻溜走。电荷放大器像用固定容量的桶接住这杯水——桶的水位（电压）由电荷量与反馈电容决定，电缆这根“管子粗细”不再直接改灵敏度[1][2]。

## 摘要

说明为何电压模式读出怕电缆电容，电荷放大器如何把 `Vout ≈ −Q/Cf`，以及 Rf/Cf、运放与频率边界。数值为设计量级，**以传感器灵敏度与运放数据手册核算**[3][4]。

## 1. 压电源特性

正压电：`Q = d · F`。等效为电荷源并联传感器电容 Cp 与极高绝缘电阻 Rp；只擅长动态量，准静态会被泄漏掉[1][5]。

| 类型 | 材料叙事 | 灵敏度叙事 | 用途 |
|------|----------|------------|------|
| 加速度计 | PZT 等 | pC/g 量级 | 振动 |
| 力/压力 | 石英等 | pC/N 或 pC/psi 量级 | 冲击/压力 |
| PVDF | 薄膜 | 较低 | 声学等 |

## 2. 电压模式 vs 电荷模式

电压模式：`V = Q / (Cp + Ccable + Cin)`——换线缆灵敏度就变。电荷放大器用运放虚地把电荷导入反馈电容 Cf，`Vout = −Q/Cf`，电缆主要影响噪声与高频，而非一阶灵敏度[2][3]。

| 特性 | 电压放大器 | 电荷放大器 |
|------|------------|------------|
| 增益决定 | 总电容 | 主要是 Cf |
| 电缆影响 | 大 | 相对小 |
| 低频 | 受 Cp·Rp 等 | 受 Rf·Cf |
| 线长 | 宜短 | 可更长 |

## 3. 关键设计量

低频截止约 `f_L ≈ 1/(2π Rf Cf)`；高频受增益带宽积（Gain-Bandwidth Product, GBW）与源电容负载影响。Cf 用 C0G/NPO 等稳定介质；Rf 常用数十 MΩ 至 GΩ 量级，过高则偏置电流造成失调[3][6]。

| Cf 量级 | 灵敏度叙事 | 场景 |
|---------|------------|------|
| 更小 | 更高 V/pC | 微弱电荷 |
| 更大 | 更低 | 大信号防饱和 |

| 运放关注 | 原因 |
|----------|------|
| 低偏置电流 | 高阻节点 |
| 低电流噪声 | 高阻源 |
| 足够 GBW | 带宽与稳定 |
| 输入保护 | 电缆 ESD/浪涌 |

## 4. 局限、挑战与可改进方向

### 1. 用通用运放搭高阻节点

**局限**：偏置与泄漏让输出缓慢爬走。
**改进**：选飞安–皮安级偏置器件；防护环（guard）与清洁助焊剂。

### 2. Cf 用 X7R

**局限**：电压系数、压电微音与介质吸收破坏精度。
**改进**：C0G/NPO 或薄膜电容；Cf 远离应力区。

### 3. 只看灵敏度不看带宽

**局限**：冲击测量高频不够或低频截止吃掉能量。
**改进**：按频谱定 Rf/Cf 与 GBW；时域用已知冲击源验收。

### 4. 电缆当“随便一根线”

**局限**：微音、泄漏与干扰抬高噪声底。
**改进**：低噪声同轴、固定走线、屏蔽单点策略。

## 5. 实践要点

1. 先定最大电荷与满幅电压 → 选 Cf。
2. 再按最低频率选 Rf，并检查偏置×Rf 失调。
3. 布局：高阻节点极短、防护环、电源去耦。

## 参考文献

[1] W. P. Mason, piezoelectric transducer fundamentals (classic references).
[2] Kistler / PCB Piezotronics, charge amplifier technical notes.
[3] Analog Devices, "Charge Amplifier" / piezo interface application notes.
[4] TI, piezo sensor signal conditioning application reports.
[5] IEEE standards related to piezoelectric vibration transducers (family).
[6] Op-amp selection guides for high-impedance photodiode/charge amps (ADI/TI).
[7] Endevco / Brüel & Kjær charge amp user manuals (industry practice).
[8] Capacitor dielectric guides: C0G vs X7R for precision feedback.
[9] Cabling and triboelectric noise notes for piezoelectric measurement.
[10] Piezoelectric coefficients datasheets (PZT, quartz, PVDF vendors).
[11] Horowitz & Hill, "The Art of Electronics" (charge amp related sections).
