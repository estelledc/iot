---
schema_version: '1.0'
id: buck-converter-design-iot
title: Buck降压转换器在IoT设备中的设计要点
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites: UNKNOWN
tags:
  - Buck
  - 降压转换器
  - 轻载效率
  - EMI
  - 电感选型
  - CCM
  - PFM
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# Buck降压转换器在IoT设备中的设计要点

> **难度**：🟡 中级 | **领域**：开关电源 | **阅读时间**：约 14 分钟

## 日常类比

高位水塔要往桶里放平稳低水位水：一直大开会溅（纹波），快速点动开关水龙头则更稳，但开关越勤“磨损”（开关损耗）越大。Buck 就是这只高频水龙头，把电池/USB 高压轨降到 MCU 等低压轨[1][2]。

## 摘要

覆盖 CCM/DCM、电感与陶瓷电容选型、开关频率权衡、轻载 PFM/脉冲跳跃、EMI 与布局。效率与纹波数字为量级，**随 Vin/Vout/Iload 与 PCB 寄生变化**[3][4]。

## 1. 原理与导通模式

理想关系：\(D\approx V_{\mathrm{out}}/V_{\mathrm{in}}\)。电感电流三角波；CCM 电流不归零，DCM 出现零电流区间。

| 模式 | 倾向 | IoT 含义 |
|------|------|----------|
| CCM | 中高负载纹波可预期 | 射频突发可能仍在 CCM |
| DCM/PFM | 轻载减开关次数 | 睡眠电流友好，纹波/频谱变 |
| 强制 PWM | 频谱固定 | 利于敏感模拟，轻载效率差 |

## 2. 关键选型

| 元件 | 关注点 |
|------|--------|
| 电感 L | 纹波约 20–40% \(I_{\mathrm{load}}\) 量级起步；Isat/Ir 留裕量；DCR 影响效率 |
| Cout | 陶瓷优先；计及直流偏置容值跌落；ESR 贡献纹波 |
| Cin | 紧靠开关节点输入，控输入尖峰 |
| MOSFET/IC | Iq、轻载模式、最大占空比（低压差场景） |

频率升高→被动件缩小，但开关损耗与 EMI 上升。电池近压差（如 3.7 V→3.3 V）时注意最小离时间与效率曲线[2][5]。

## 3. 轻载、EMI 与布局

IoT 大部分时间睡眠：看透 Iq 与 PFM 行为；有的负载需要“低噪声模式”牺牲效率。输入π滤波、摆率控制、短热环路（Vin–开关–电感–地）是辐射关键。铜皮与过孔服务热与回流[4][6]。

| 场景 | 设计倾向 |
|------|----------|
| 长寿命电池节点 | 低 Iq + 自动 PFM |
| 精密传感同步采样 | 固定频率或与 ADC 同步 |
| 认证敏感 | 早做传导/辐射预扫 |

## 4. 局限、挑战与可改进方向

### 1. 轻载效率与纹波两难

**局限**：PFM 省电但纹波包络干扰射频/ADC。
**改进**：分轨；测量窗强制 PWM；加大滤波或后级 LDO[3][7]。

### 2. 陶瓷电容偏置失效

**局限**：标称 10 µF 偏置后可能只剩几 µF。
**改进**：按厂商偏置曲线选型；并联多颗；电压降额[5][8]。

### 3. 布局寄生导致振铃与 EMI

**局限**：仿真理想、板级失败。
**改进**：紧凑热环；开尔文取样；必要时 RC 缓冲[4][6]。

### 4. 低压差高占空比

**局限**：电池末期接近 Vout 时掉线或效率崩。
**改进**：选支持高 D 的 IC；评估旁路/直通；或调低 Vout 需求[2][9]。

## 5. 实践要点

1. 用最差 Vin、最大与最小负载核验模式与温升。
2. 睡眠电流测整机，不只看转换器峰值效率。
3. 布局评审与原理图同等优先级。

## 参考文献

[1] Erickson & Maksimović, Fundamentals of Power Electronics.
[2] TI / ADI buck converter design application notes (IoT PMICs).
[3] Light-load PFM/PSM mode behavior vendor ANs.
[4] PCB layout guidelines for switch-mode regulators (hot loop).
[5] Ceramic capacitor DC bias derating charts (Murata/TDK class).
[6] CISPR / FCC conducted and radiated EMI context for DC-DC.
[7] Post-regulation LDO after buck for low-noise rails.
[8] Inductor saturation and DCR loss estimation guides.
[9] Low dropout buck / 100% duty cycle operation notes.
[10] Input filter damping for buck converters.
[11] Thermal metrics (θJA) and copper pour practice.
[12] Battery to MCU rail design examples (Li-ion 3.7 V class).
