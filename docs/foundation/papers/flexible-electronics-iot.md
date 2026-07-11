---
schema_version: '1.0'
id: flexible-electronics-iot
title: 柔性电子与 IoT 融合：从可弯曲基底到可穿戴传感贴片
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - flexible-pcb-rigid-flex-iot
  - tactile-sensing-iot
tags:
  - 柔性电子
  - 印刷电子
  - 可穿戴
  - OTFT
  - 可拉伸互连
  - IoT传感
  - 基底材料
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 柔性电子与 IoT 融合：从可弯曲基底到可穿戴传感贴片

> **难度**：🟡 中级 | **领域**：柔性电子 | **关键词**：PI/PET, 印刷电子, 可拉伸互连, OTFT | **阅读时间**：约 18 分钟

## 日常类比

创可贴能贴合弯曲指关节；柔性电子像“会传感的创可贴”——薄、可贴肤，但半导体脆、金属弯折易裂。物联网（IoT）可穿戴要把刚性芯片与柔性基底用岛–桥、蛇形线等结构“和解”[1][2]。

## 摘要

对比柔性基底、印刷工艺、有机薄膜晶体管（Organic Thin-Film Transistor, OTFT）与可拉伸互连，并给出贴片系统架构与可靠性要点。厚度、迁移率、循环次数为文献典型量级，**以材料与工艺规格为准**[3][4]。

## 1. 基底与印刷

| 基底 | 耐温倾向 | 柔性特点 | 常见用途 |
|------|----------|----------|----------|
| PI（聚酰亚胺） | 高 | 可很小弯曲半径 | FPC、高温传感 |
| PET | 较低 | 低成本大面积 | 一次性贴片、RFID |
| PDMS/TPU | 中 | 可拉伸 | 皮肤贴合 |

| 工艺 | 分辨倾向 | 速度倾向 | 适合 |
|------|----------|----------|------|
| 喷墨 | 较高 | 较慢 | 导体/半导体图案 |
| 丝网 | 中 | 中 | 厚膜导体、介质 |
| 凹版/柔版 | 中高 | 快 | 大面积量产 |

银纳米颗粒墨水烧结后电阻率可接近块体银量级；碳管/PEDOT 更适合可拉伸或生物相容场景，电导通常差一到数个数量级[5]。

## 2. 器件与互连

OTFT 迁移率远低于单晶硅，但可支撑传感读出与简单逻辑；氧化物（如 IGZO）常作性能更好的柔性有源层选项[3]。可拉伸策略：蛇形走线、预应变褶皱、液态金属微流道、刚性岛 + 柔性桥——量产贴片多用后者放置微控制器裸片[1][7]。

| 传感类型 | 敏感材料倾向 | 备注 |
|----------|--------------|------|
| 电阻应变 | CNT/弹性体 | 大应变、需抗疲劳 |
| 电容压力 | 微结构弹性体 | 静态压力友好 |
| 温度 | 印刷金属/NTC | 注意弯曲基线漂移 |

## 3. 制造与可靠性

典型流程：表面活化 → 印导体 → 烧结（热或强脉冲光）→ 介质/传感层 → 封装切割 → 电测与弯折抽检。良率杀手常是断线、短路、附着力与咖啡环导致的膜厚不均[5][10]。

可靠性：拐角圆弧化、敏感层靠近中性面、弯曲态下重新标定；湿热老化之外增加弯折循环考核[6][9]。

## 4. 局限、挑战与可改进方向

### 1. 疲劳裂纹与基线漂移

**局限**：反复弯折导致走线开裂；弯曲态与平放标定不一致。
**改进**：蛇形/中性面设计；出厂与佩戴姿态双标定[1]。

### 2. 有源器件稳定性差

**局限**：部分有机半导体对氧湿敏感，阈值漂移。
**改进**：阻隔封装；改用更稳的氧化物 TFT；关键功能用刚性岛上的硅芯片[3]。

### 3. 银墨成本与工艺窗口窄

**局限**：材料成本高；黏度/表面能不匹配则断线。
**改进**：缩短走线、碳墨一次性方案；等离子预处理与多层叠印[5]。

### 4. 供电与射频集成难

**局限**：薄膜电池容量小；印刷天线效率受弯曲影响。
**改进**：NFC 供能短时采样；柔性电池 + 占空比策略并实测[8]。

## 总结

柔性 IoT 贴片成功与否取决于基底–油墨–互连–封装一体设计，而不是单一“可弯”材料。优先岛–桥落地硅 MCU，印刷层做传感与互连，并用弯折与湿热试验锁可靠性。

## 参考文献

[1] J. A. Rogers et al., Materials and mechanics for stretchable electronics, Science.
[2] A. Nathan et al., Flexible electronics: The next ubiquitous platform, Proc. IEEE.
[3] S. Khan et al., Flexible and stretchable electronics for IoT, Adv. Mater. Technol.
[4] T. Yokota et al., Ultraflexible organic photonic skin, Sci. Adv.
[5] M. Gao et al., Inkjet-printed flexible electronics, Chem. Soc. Rev.
[6] W. Gao et al., Fully integrated wearable sensor arrays, Nature.
[7] D.-H. Kim et al., Epidermal electronics, Science.
[8] Y. Khan et al., Monitoring of vital signs with flexible medical devices, Adv. Mater.
[9] H. Matsui et al., Printed electronics manufacturing challenges, IEEE Access.
[10] S. Patel et al., Printed flexible sensors for IoT, Nature Electronics.
[11] IPC / 柔性印刷电子工艺与可靠性指南.
[12] IEEE Sensors, 可穿戴柔性湿度/应变传感器标定方法.
