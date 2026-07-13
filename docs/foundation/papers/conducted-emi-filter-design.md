---
schema_version: '1.0'
id: conducted-emi-filter-design
title: 传导EMI滤波器设计：共模/差模抑制
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 15
prerequisites: UNKNOWN
tags:
  - 传导EMI
  - 共模
  - 差模
  - CISPR
  - 共模扼流圈
  - X电容
  - Y电容
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 传导EMI滤波器设计：共模/差模抑制

> **难度**：🟡 中级 | **领域**：EMI滤波设计 | **阅读时间**：约 15 分钟

## 日常类比

铁路旁公寓：货车轰鸣像差模（Differential Mode, DM）——沿电源线“线间”传；整楼共振像共模（Common Mode, CM）——对地同向耦合。滤波器像双层隔音窗 + 减震地基：X 电容/差模电感管线间，共模扼流圈（CMC）+ Y 电容管对地[1][2]。

## 摘要

梳理传导发射测量（LISN）、CISPR 限值叙事、DM/CM 分型、单级/多级拓扑与安全约束（漏电流、X/Y 等级），以及布局与迭代调试。衰减与案例数字为示意量级，**以实测与认证实验室为准**[1][3]。

## 1. 噪声源与测量

IoT 常见源：开关电源（SMPS）开关边沿、电机 PWM、高速数字同步开关噪声。LISN（Line Impedance Stabilization Network）提供稳定阻抗并把噪声耦合到接收机[1][4]。

消费级多媒体/IT 设备常对标 CISPR 32 Class B（住宅）叙事；Class A（工业）通常更松。限值随频段与检波器（准峰值/平均值）变化，设计以现行标准文本为准[1]。

| 关注 | DM | CM |
|------|----|----|
| 电流路径 | L–N 线间 | L/N 同向经地返回 |
| 典型来源 | 输入脉动、负载突变 | 开关节点对地寄生、变压器跨接电容 |
| 主元件 | 差模电感 + X 电容 | CMC + Y 电容 |

## 2. 分型与滤波拓扑

调试可用电流探头加减、DM/CM 分离器或临时拔 Y 电容观察变化；“低频偏 DM、高频偏 CM”仅为经验，**必须实测确认**[2][5]。

截止频率示意：\(f_c \approx 1/(2\pi\sqrt{LC})\)。单级 L 型约 20 dB/decade 量级叙事，Pi/T 更陡；两级用于更大衰减需求，但体积、压降与成本上升[3][6]。

| 需求倾向 | 拓扑叙事 | 场景 |
|----------|----------|------|
| 中等衰减、成本敏感 | 单级 L / Pi | 消费 IoT |
| 大衰减 | 两级 | 工业/严苛余量 |
| DM 主导 | L + X | 开关电源输入 |
| CM 主导 | CMC + Y | 电机/高速数字 |

## 3. 元件与安全

CMC：共模磁通叠加、差模抵消（剩漏感可兼作差模）；看目标频段阻抗曲线，额定电流留裕量防饱和。X 电容跨 L–N（常用 X2 安全类）；Y 电容线–地，容值受漏电流上限约束（I/II 类设备不同）[3][7]。

| 约束 | 要点 |
|------|------|
| 漏电流 | \(I \propto fVC_Y\)，II 类更严 |
| X/Y 等级 | 须安全认证件，禁普通电容替代 |
| 放电 | 断电后电容残留电压需泄放路径 |

AC 入口常串保险丝、并 MOV（压敏）再进滤波器；额定与钳位按电网与浪涌规范选型[7][8]。

## 4. 布局与迭代

滤波器放电源入口；输入/输出隔离，避免耦合绕过；Y 电容接地短而多过孔。脏地/净地可单点或磁珠隔离，避免噪声电流灌入信号地[2][4]。

流程：裸机测 → 分型 → 针对性加件 → 再测 → 对照限值。一次堆满元件会掩盖因果；理论衰减远好于实测时先查布局耦合与 CMC 寄生电容[5][6]。

## 5. 局限、挑战与可改进方向

### 1. 盲目堆元件

**局限**：未分 DM/CM 就加电容/电感，认证反复失败。
**改进**：先分型再选型；记录每步频谱变化。

### 2. Y 电容与安规冲突

**局限**：为压 CM 加大 Y，漏电流超标或触电风险。
**改进**：按设备类算上限；优先降源端 dv/dt、优化寄生与 CMC。

### 3. 高频旁路电感

**局限**：CMC 绕组寄生电容使高频阻抗塌陷，>10 MHz 难压。
**改进**：看阻抗–频率曲线；必要时多级、布局屏蔽或源端软开关。

### 4. 布局绕过

**局限**：滤波器居中、进出线平行，噪声耦合绕过滤波。
**改进**：入口放置、隔离带、短接地；复测验证。

## 6. 实践要点

1. 以 CISPR/产品标准限值为目标，预留数 dB 余量叙事，最终以实验室为准。
2. X/Y 必须安全认证料号；BOM 替代要重做安规评估。
3. DC 输入设备同样有传导路径，勿默认“无交流就无滤波”。

## 参考文献

[1] CISPR 32, Electromagnetic compatibility of multimedia equipment — Emission requirements.
[2] Ott H. W., *Electromagnetic Compatibility Engineering*, Wiley.
[3] Würth Elektronik, EMI filter design application notes for power supplies.
[4] Schaffner / filter vendors, Conducted EMI filter design for SMPS application notes.
[5] Texas Instruments, Common-mode filter design guides (e.g. SNVA-class notes).
[6] IEC / CISPR LISN and conducted emission measurement practice guides.
[7] IEC 60950/62368-class leakage current and Y-capacitor safety discussions.
[8] MOV and fuse coordination application notes for AC inlet protection.
[9] CMC impedance vs frequency and saturation guidance (magnetics vendors).
[10] PCB layout for EMI filters: input/output isolation best practices.
[11] DM/CM separator and current-probe diagnostic methods (EMC lab notes).
