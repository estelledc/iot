---
schema_version: '1.0'
id: capacitive-level-sensor-liquid
title: 电容式液位传感器原理与防腐设计
layer: 1
content_type: technical_analysis
difficulty: beginner
reading_time: 15
prerequisites: UNKNOWN
tags:
  - 电容传感
  - 液位
  - 介电常数
  - 防腐
  - FDC1004
  - 非接触测量
  - PTFE
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 电容式液位传感器原理与防腐设计

> **难度**：🟢 初级 | **领域**：液位测量 | **阅读时间**：约 15 分钟

## 日常类比

往玻璃杯倒水，听声音变调能猜快满了——空气柱变短。电容式液位传感不听声，而测两极板间“蓄电能力”：液体与空气的相对介电常数（relative permittivity, εᵣ）不同，液面上升时液体置换空气，电容变大，据此估液位[1][2]。

## 摘要

讲清棒式/板式/同轴电极、接触与非接触、电容数字转换器（Capacitance-to-Digital Converter, CDC）与防腐材料选择。介电常数与精度为量级叙事，**须按介质与罐体实测校准**[1][4]。

## 1. 原理

平行板近似：`C ≈ εᵣ ε₀ A / d`。液位高度 h 使液体段与空气段并联，总电容随 h 近似线性变化（圆柱几何理想时）[1]。

| 介质 | εᵣ 量级 | 检测难度叙事 |
|------|---------|--------------|
| 空气 | ~1 | 基准 |
| 汽油/柴油 | ~2 | ΔC 小，需更高分辨率 |
| 乙醇/甲醇 | 数十 | 较易 |
| 水 | ~80（随温度变） | ΔC 大，易测 |

水基易测；油类 εᵣ 低，对 CDC 分辨率与噪声更敏感[1][4]。

## 2. 电极结构

| 结构 | 要点 | 适用 |
|------|------|------|
| 棒式 | 棒 + 金属罐壁为另一极 | 金属罐、非导电液 |
| 板式外壁 | 电极贴非金属罐外 | 无湿件、食品/制药友好 |
| 同轴 | 中心棒 + 外管，电场集中 | 小口径、抗外扰 |

非接触依赖非金属罐壁；壁厚、冷凝与结垢会引入固定/漂移电容，需校准与屏蔽驱动抑制电缆寄生[2][3]。

## 3. 读出与防腐

| 方案 | 特点 | 注意 |
|------|------|------|
| FDC1004 等 CDC | I²C、高分辨率、可有屏蔽驱动 | 按手册布局净空 |
| AD7746 类 | 高精度双通道叙事 | 成本更高 |
| LC 测频 | 电路简单 | 温漂与非线性大 |

导电液体会“短路”裸电极 → 常用聚四氟乙烯（Polytetrafluoroethylene, PTFE）包覆；316L、哈氏合金等按腐蚀等级选型。密封（环氧/玻璃烧结/O 形圈）决定电气端寿命[5]。

| 材料 | 耐蚀叙事 | 成本叙事 |
|------|----------|----------|
| 316L | 食品/一般化学 | 中 |
| 哈氏 C276 | 强酸/强氧化 | 高 |
| PTFE 包覆 | 极广介质 | 中 |
| 陶瓷 | 高温强腐蚀 | 高 |

## 4. 现场挑战

泡沫 εᵣ 介于气液之间 → 偏高或抖动；导波管/滤波可缓解。温度使水的 εᵣ 明显变化 → 需温补。乳化/分层使单一 εᵣ 假设失效 → 常需辅助传感[4][5]。

| 对比 | 电容式 | 超声波 | 雷达 | 浮球 |
|------|--------|--------|------|------|
| 非接触可能 | 有（非金属壁） | 有 | 有 | 否 |
| 成本叙事 | 低–中 | 中 | 高 | 极低 |
| 泡沫影响 | 有 | 大 | 较小 | 小 |
| 导电液 | 需绝缘 | 无妨 | 无妨 | 无妨 |

## 5. 局限、挑战与可改进方向

### 1. 两点校准当万能

**局限**：非圆柱罐体积–液位非线性；介质更换后 εᵣ 变。
**改进**：罐表（strapping）或分段校准；换液必重校。

### 2. 忽略温度与结垢

**局限**：εᵣ 温漂与电极沉积被当成液位变化。
**改进**：近旁温度探头查表；光滑 PTFE/定期清洗策略。

### 3. 电缆寄生吃掉分辨率

**局限**：长线无屏蔽驱动，空满差被寄生淹没。
**改进**：CDC 屏蔽驱动或前端靠近探头；短线优先。

### 4. 导电液绝缘破损静默失效

**局限**：PTFE 破损后读数异常或短路，难自诊断。
**改进**：绝缘完整性自检、冗余探头或与压力/雷达交叉校验。

## 6. 实践要点

1. 先定罐材（接触/非接触）与液体是否导电。
2. 按 εᵣ 选分辨率；油类别用“水箱经验”硬套。
3. IoT：慢变过程用低采样率 + 休眠；高低位与变化率告警分开设计。

## 参考文献

[1] L. K. Baxter, "Capacitive Sensors: Design and Applications," IEEE Press, 1997.
[2] Texas Instruments, "FDC1004: Basics of Capacitive Sensing and Applications," SNOA941.
[3] Analog Devices, AD7746 Capacitance-to-Digital Converter datasheet.
[4] N. M. Mohan et al., "A Novel Capacitive Sensor for Liquid Level Measurement," IEEE Sensors Journal, 2011.
[5] IEC 63007, Capacitive level transmitters for industrial applications (family/related).
[6] Microchip / Infineon CapSense application notes (capacitive sensing layout).
[7] PTFE material dielectric and chemical resistance handbooks (vendor).
[8] TI, Shielding and active guard drive for capacitive sensors (app notes).
[9] Endress+Hauser / Vega capacitive level transmitter technical principles (industry).
[10] ASTM / process industry practices on tank strapping and level calibration.
[11] IEEE Sensors tutorials on dielectric constant of liquids vs temperature.
