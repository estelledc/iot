---
schema_version: '1.0'
id: magnetoresistive-sensor-tmr-gmr
title: TMR与GMR磁阻传感器技术对比
layer: 1
content_type: comparison
difficulty: advanced
reading_time: 16
prerequisites: UNKNOWN
tags:
  - TMR
  - GMR
  - AMR
  - 磁阻
  - 自旋电子学
  - 电流传感
  - 角度传感
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# TMR与GMR磁阻传感器技术对比

> **难度**：🔴 高级 | **领域**：磁传感 | **关键词**：TMR, GMR, AMR, MR 比 | **阅读时间**：约 16 分钟

## 日常类比

电子自旋像司机“朝向”：与磁层取向一致时通行顺畅（电阻低），不一致则拥堵（电阻高）。GMR（Giant Magnetoresistance，巨磁阻）像旋转门——阻力随取向变；TMR（Tunnel Magnetoresistance，隧道磁阻）像密码门——自旋匹配才容易隧穿，开关比往往更大，因而灵敏度/功耗上常更有优势（仍取决于具体器件）[1][2]。

## 摘要

从 AMR→GMR→TMR 演进对比结构、MR 比、噪声与应用（电流/角度/开关）。性能数字跨产品差异大，**以目标型号数据手册为准**[3][4]。

## 1. 效应对比

| 类型 | 机制倾向 | MR 比量级印象 | 备注 |
|------|----------|---------------|------|
| AMR | 各向异性磁阻 | 较小 | 成熟、成本低 |
| GMR | 多层自旋阀散射 | 中 | 硬盘读头历史功臣 |
| TMR | 隧道结 | 常更大 | 消费与工业传感增长快 |

| 应用 | 关注点 |
|------|--------|
| 电流传感 | 灵敏度、温漂、磁饱和、隔离 |
| 角度/位置 | 正交桥、360° 线性化 |
| 开关/ quantizer | 阈值稳定与迟滞 |

## 2. 工程选型维度

| 维度 | 常见考量 |
|------|----------|
| 灵敏度 | 弱场检测能力 |
| 功耗 | 电桥激励与 ASIC |
| 噪声 | 1/f 与热噪声，限分辨率 |
| 温度 | 汽车级 vs 消费级 |
| 成本与供货 | GMR/AMR 生态 vs TMR 溢价 |
| 磁场设计 | 集磁器、屏蔽、永磁偏置 |

前端常接仪表放/专用 ASIC；PCB 上远离大电流环路与扬声器磁铁[5]。

## 3. 局限、挑战与可改进方向

### 1. 磁场干扰

**局限**：地磁、电机、导线磁场污染读数。
**改进**：磁屏蔽、差分/梯度结构、机械布局远离干扰源。

### 2. 温度与偏移

**局限**：零点与灵敏度随温度漂。
**改进**：片内补偿、标定查找表、选择低漂移工艺。

### 3. 饱和与非线性

**局限**：强场进入饱和，角度误差增大。
**改进**：限制耦合磁场；分段标定；换大量程方案。

### 4. 规格不可比

**局限**：不同厂商 MR 比测试条件不同。
**改进**：按应用指标（nT/√Hz、mA 精度）横向评测，而非只看宣传 MR%。

## 4. 实践要点

1. 先定义被测磁场范围与带宽，再选 AMR/GMR/TMR。
2. 样机做温循与干扰注入测试。
3. 电流传感场景同时评估分流电阻方案。

## 参考文献

[1] Baibich et al., Giant Magnetoresistance foundational papers.
[2] Moodera / Miyazaki TMR early works and reviews.
[3] TDK, Crocus, Sensitec 等 TMR/GMR 产品数据手册.
[4] NVE GMR sensor application catalog.
[5] Magnetic current sensor design application notes.
[6] AMR angle sensor vendor guides (Infineon 等).
[7] Spintronics textbook chapters on multilayers and MTJ.
[8] 1/f noise in magnetoresistive sensors surveys.
[9] Automotive magnetic sensor AEC-Q qualification overviews.
[10] PCB layout for magnetic sensors（间距与屏蔽）.
[11] Comparison articles: Hall vs MR technologies.
