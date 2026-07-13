---
schema_version: '1.0'
id: eddy-current-sensor-proximity
title: 涡流传感器接近检测与金属识别
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - signal-conditioning-amplifier-filter
  - ultrasonic-distance-measurement
tags:
  - 涡流传感
  - 电感式接近开关
  - LDC
  - 金属识别
  - 趋肤效应
  - 工业IoT
  - 非接触检测
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 涡流传感器接近检测与金属识别

> **难度**：🟡 中级 | **领域**：接近传感 | **关键词**：Eddy Current, LDC, Sn, 趋肤深度 | **阅读时间**：约 18 分钟

## 日常类比

机场安检门不碰你也能“看见”钥匙：门框线圈发交变磁场，金属上感应出涡流（Eddy Current），涡流反作用改变线圈阻抗。工业物联网（Internet of Things, IoT）里的涡流接近开关同理，只是更小、更准——能判“有没有金属、多远、大致什么金属”[1][3]。

## 摘要

梳理电磁感应与趋肤深度、接近开关与阻抗分析/多频识别、探头与电感数字转换器（Inductance-to-Digital Converter, LDC）电路、材料修正系数及与电容/光电/超声对比。检测距离与趋肤深度为典型量级，**以目标材料、线圈直径与厂家 Sn 标定为准**[3][5]。

## 1. 物理机制

交变电流激励线圈 → 交变磁场 → 导电目标表面感应涡流 → 按楞次定律反作用于线圈，等效阻抗变化。铁磁目标常抬高电感；铝/铜等非铁磁导电目标常压低电感并增大损耗电阻[2][4]。

趋肤深度：

```
δ = √(2 / (ω · μ · σ))
```

频率越高，穿透越浅，更偏表面特性；低频更利于较厚导体层。公开资料中，约百 kHz 量级下铝/铜趋肤深度常在亚毫米级，具体随电导率与磁导率变化[2]。

## 2. 测量模式

| 模式 | 输出 | 典型用途 |
|------|------|----------|
| 电感式接近开关 | 有/无或粗距离 | 气缸到位、齿轮测速 |
| 阻抗幅相分析 | 材料族 + 距离 | 分拣、合金粗分 |
| 多频涡流 | 深度/层结构信息 | 镀层、多层结构 |

接近开关常把线圈放进 LC 振荡器：目标靠近阻尼增大，幅度过阈值则开关输出。标称检测距离（Sn）多与线圈直径同量级（常见约 0.1–1 倍直径），有效/可靠距离再按标准折减[3]。

## 3. 材料修正与对比

标准目标多为边长约等于敏感面、厚度约 1 mm 的低碳钢；其他材料用修正系数缩小有效距离（示意，以数据手册为准）[3]：

| 材料 | 修正系数示意 |
|------|-------------|
| 低碳钢 | 1.0 |
| 铁磁不锈钢 | 约 0.8–0.9 |
| 铝 | 约 0.3–0.5 |
| 黄铜/铜 | 约 0.3–0.4 |

| 特性 | 涡流（电感式） | 电容式 | 光电 | 超声 |
|------|----------------|--------|------|------|
| 对象 | 金属 | 多材料 | 多材料 | 多材料 |
| 距离倾向 | mm 级 | 更短 | 可更长 | 可更长 |
| 油污/尘 | 通常强 | 一般 | 弱 | 一般 |
| 响应 | 快 | 快 | 极快 | 较慢 |

## 4. 电路与频率

| 方案 | 要点 |
|------|------|
| 振荡器 + 解调 | 振幅/频率变化 → 比较器 |
| LDC（如 TI LDC 系列） | 电感数字化，经 SPI/I2C 读 MCU[1][5] |

| 频率倾向 | 场景 |
|----------|------|
| 约 0.1–1 MHz | 较大距离、铁磁目标 |
| 约 1–5 MHz | 通用接近与识别 |
| 更高 | 薄金属、高分辨，寄生更敏感 |

## 5. IoT 场景要点

位置/阀门到位、齿轮脉冲测速、废金属粗分拣、涂层厚度（基体与涂层电导率差）。PCB 线圈一致性好；温度用参考通道差分或软件补偿；远离变频器等强电磁干扰（Electromagnetic Interference, EMI）源[1][5]。

## 6. 局限、挑战与可改进方向

### 1. 材料与尺寸折减

**局限**：铝/铜有效距离显著短于钢；目标小于敏感面时 Sn 达不到。
**改进**：按最差材料与最小目标选型；验收用真实工件而非仅钢标靶。

### 2. 温度与漂移

**局限**：线圈电阻与目标电导率随温漂，假触发或漏检。
**改进**：双线圈差分、板载温度补偿、上电基线校准。

### 3. EMI 与寄生

**局限**：线圈兼收发天线；高频下 PCB 寄生改变谐振。
**改进**：屏蔽线、合理铺地留距保 Q；产线锁频率与布局版本。

### 4. “金属识别”过度承诺

**局限**：幅相可分铁磁/非铁磁，合金细分受几何与提离耦合。
**改进**：多频 + 标定库；关键分拣加视觉/称重冗余。

## 7. 实践要点

1. 先定目标材料与最小尺寸，再选 Sn 与线圈直径。
2. 恶劣油污环境优先涡流而非光电。
3. 需要亚毫米连续位移时评估 LDC + 差分通道，而非仅开关型接近开关。

## 参考文献

[1] Texas Instruments, LDC1612 EVM / application notes (SNOA930 等).
[2] G. Y. Tian et al., Pulsed eddy current NDT, NDT & E International.
[3] IEC 60947-5-2, Low-voltage switchgear — Proximity devices.
[4] H. Saguy et al., Eddy current testing for metal identification, Insight.
[5] Texas Instruments, Coil design guidelines for LDC (SNOA957).
[6] J. García-Martín et al., Non-destructive techniques based on eddy current testing, Sensors.
[7] ASNT, Nondestructive Testing Handbook — Electromagnetic Testing.
[8] Omron / Pepperl+Fuchs inductive proximity sensor application notes（材料修正与安装）.
[9] ISO 14119 / machine safety related proximity interlocking guidance（选型语境）.
[10] TI LDC3114 / inductive touch button application notes.
[11] Skin effect and conductivity tables in electromagnetic NDT textbooks.
