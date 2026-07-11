---
schema_version: '1.0'
id: potting-compound-sensor-protection
title: 灌封材料在传感器防护中的选型与工艺
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 15
prerequisites:
  - conformal-coating-iot-protection
tags:
  - 灌封
  - 环氧树脂
  - 硅胶
  - 聚氨酯
  - IP防护
  - 传感器封装
  - 热管理
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 灌封材料在传感器防护中的选型与工艺

> **难度**：🟡 中级 | **领域**：封装防护工艺 | **关键词**：Potting, 环氧, 硅胶, 聚氨酯, IP | **阅读时间**：约 15 分钟

## 日常类比

手机进水易坏；若整机封进树脂块，水进不去，但变重、难修、散热变差。**灌封**（Potting / Encapsulation）是把腔体填满固态材料的“密封铠甲”；相对只涂薄膜的**敷形涂层**（Conformal Coating），防护更强、代价更高[1][2]。

## 摘要

对比灌封与涂层、环氧/硅胶/聚氨酯取舍、工艺缺陷与传感器窗口保留。厚度、防护等级与硬度为典型量级，以材料数据表与实测 IP 为准[3]。

## 1. 灌封 vs 敷形涂层

| 对比项 | 灌封 | 敷形涂层 |
|--------|------|----------|
| 覆盖 | 填满腔体 | 表面薄膜 |
| 厚度量级 | 毫米级 | 数十 µm 量级 |
| 防护倾向 | 更高（可达较高 IP） | 中等防潮防尘 |
| 返修 | 困难/破坏性 | 相对可返工 |
| 重量与热 | 增重、导热路径改变 | 影响较小 |

## 2. 材料族

| 材料 | 优点 | 代价 | 常见用途 |
|------|------|------|----------|
| 环氧（Epoxy） | 硬、粘附强、耐化 | 应力大、难拆 | 高机械防护 |
| 硅胶（Silicone） | 柔韧、宽温、低应力 | 透气/粘附需底涂 | 精密传感、振动 |
| 聚氨酯（PU） | 韧性与成本折中 | 耐温/耐化中等 | 一般工业节点 |

关注：粘度与可灌性、固化放热、玻璃化转变温度（Glass Transition Temperature, Tg）、热膨胀系数（Coefficient of Thermal Expansion, CTE）与元件匹配、介电与阻燃等级、是否腐蚀铜/铝[4][5]。

## 3. 传感器特殊约束

压力/温湿度/气体/光学窗口常**不能**全封死：需保留通气孔、疏水膜、光窗或金属膜片暴露区，并用工装遮蔽连接器与测试点[6]。声呐/超声波换能器还要匹配声阻抗，随意灌封会改变灵敏度。

| 工艺风险 | 表现 | 对策 |
|----------|------|------|
| 气泡 | 漏电、渗水通道 | 真空脱泡、控制浇注速度 |
| 应力开裂 | 焊点疲劳、芯片漂移 | 选低模量；分步固化 |
| 热热点 | 功率器件温升 | 导热填料或局部导热垫 |
| 遮蔽失败 | 连接器报废 | 工装+灌注后立即检查 |

## 4. 工艺与验证

混合比、温度、湿度按厂商工艺窗；固化后做外观、绝缘耐压、温循、湿热与目标 IP 喷淋/浸水。量产固定批次与搅拌真空参数，避免“实验室一次成功、产线气泡率高”[3][7]。

## 5. 局限、挑战与可改进方向

### 1. 不可逆与售后成本

**局限**：返修几乎等于毁板。
**改进**：关键模块可拆腔+密封圈；仅对高风险区局部灌封[2]。

### 2. CTE 应力导致漂移

**局限**：硬环氧在温循下拉扯 MEMS/晶振。
**改进**：硅胶或软胶；元件底部填充与灌封分区[5][6]。

### 3. 热与射频性能退化

**局限**：厚胶层抬温升；近天线介电改变失配。
**改进**：导热配方；天线净空禁灌；复测回波损耗[8]。

### 4. 法规与挥发物

**局限**：部分体系含异氰酸酯等，工艺与出口受限。
**改进**：选合规配方；通风与固化完全后再密封包装[4]。

## 总结

灌封用在确需高防护且可接受重量/返修代价的传感器节点；材料与窗口设计必须和传感原理一起定，并用 IP 与温循验证，而不是只看硬度宣传。

## 参考文献

[1] IPC / industry guides on potting and encapsulation of electronics.
[2] Conformal coating vs potting selection application notes.
[3] IEC 60529 IP code testing context for sealed enclosures.
[4] Epoxy / silicone / polyurethane encapsulant datasheets (major vendors).
[5] CTE mismatch and thermomechanical stress in potting (reliability literature).
[6] MEMS pressure and environmental sensor packaging constraints.
[7] Vacuum degassing and void control in potting processes.
[8] Dielectric loading effects of encapsulants near antennas.
[9] UL 94 / flammability considerations for potting compounds.
[10] Hydrophobic membranes and vent design for sealed sensors.
[11] Automotive / industrial potting process control checklists.
[12] Reworkability and modular sealing alternatives to full potting.
