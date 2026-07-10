---
schema_version: '1.0'
id: anti-aliasing-filter-design
title: 抗混叠滤波器设计与截止频率选择
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 15
prerequisites:
  - signal-conditioning-amplifier-filter
  - adc-sar-vs-sigma-delta
tags:
  - 抗混叠
  - 奈奎斯特
  - ADC
  - Sallen-Key
  - 过采样
  - 巴特沃斯
  - 滤波器
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 抗混叠滤波器设计与截止频率选择

> **难度**：🟡 中级 | **领域**：采样系统设计 | **阅读时间**：约 15 分钟

## 日常类比

手机拍高速风扇，快门不够快时叶片像静止甚至反转——频闪。混叠（aliasing）同理：采样跟不上，高频在离散序列里伪装成低频。抗混叠滤波器（Anti-Aliasing Filter, AAF）是 ADC 前的安检门：拦下采样率处理不了的高频。混叠一旦发生，数字滤波救不回来[1][2]。

## 摘要

奈奎斯特要求 \(f_s > 2f_{\max}\)；工程上靠过采样放宽模拟滤波器阶数。阶数决定阻带斜率；截止 \(f_c\) 需覆盖信号又远离 \(f_s/2\)。SAR 常需外置有源滤波；Σ-Δ 因高 OSR 往往一阶 RC 即可。文中衰减 dB 为巴特沃斯近似量级[2][3]。

## 1. 混叠机制

表观频率 \(f_{\mathrm{alias}}=|f-n f_s|\)（取落入基带者）。高于 \(f_s/2\) 的成分折叠进 0–\(f_s/2\)，与真低频不可分[1]。

| 错误认知 | 正确理解 |
|----------|----------|
| \(f_s=2f_{\max}\) 刚好够 | 需严格大于，且要抑噪声/干扰 |
| 信号低于 \(f_s/2\) 就安全 | 带外噪声同样会混叠进来 |
| 数字滤波可替代 AAF | 数字域发生在采样之后 |

## 2. 阶数、截止与过采样

n 阶低通阻带约 −20n dB/decade。ADC 动态范围粗估约 6.02n+1.76 dB；若要求混叠残差低于约 1 LSB，阻带衰减应与之同量级——**实际按噪声与干扰谱预算**[2][4]。

| 过采样比 K（约） | 过渡带 | 模拟阶数倾向 |
|------------------|--------|--------------|
| 2–3 | 很窄 | 高阶 |
| 4–5 | 中等 | 2–4 阶常见 |
| 8–16 | 宽 | 1–2 阶 |
| ≫ | 极宽 | 简单 RC（Σ-Δ 常见） |

实用：\(f_c \approx (1.2\text{–}1.5)\,f_{\mathrm{signal}}\) 留通带余量；巴特沃斯在 \(f_c\) 已有 −3 dB[3][5]。

## 3. 拓扑选择

| 类型 | 通带 | 过渡带 | 相位 | 抗混叠倾向 |
|------|------|--------|------|------------|
| 巴特沃斯 | 最平 | 中 | 中 | 通用首选 |
| 切比雪夫 | 有纹波 | 更陡 | 较差 | 频谱分析 |
| 贝塞尔 | 较平 | 缓 | 最好 | 时域波形保真 |

一阶 RC：简单稳定，单独难满足较高位数 SAR。Sallen-Key 二阶/级联四阶：运放 GBW 宜远高于 \(f_c\)（常引用 ≫10–100× 量级）；增益过高易不稳[3][5]。

| 因素 | Σ-Δ | SAR + 外置 AAF |
|------|-----|----------------|
| 带宽 | 偏低速高精度 | 更宽带宽 |
| 外置 AAF | 常简单 RC | 需设计 |
| 多路切换 | 建立慢，慎用 | 更合适 |

数字后滤波清理 \(f_{\mathrm{signal}}\)–\(f_s/2\) 残余，**不能替代**模拟防混叠[2][6]。

## 4. 元件容差

| 元件 | 容差叙事 | 备注 |
|------|----------|------|
| 金属膜电阻 | 约 1% | 优选 |
| C0G/NP0 | 约 5% 量级 | 射频/滤波常用 |
| X7R | 更大 | 截止易漂 |

高阶对容差敏感；\(f_c\) 留裕量，关键产品可测校准[5][7]。

## 5. 局限、挑战与可改进方向

### 1. 欠采样却指望软件“去混叠”

**局限**：折叠后真假低频数学等价。
**改进**：先定 \(f_s\) 与带外威胁谱，再定 AAF；协议上禁止“先采后滤”侥幸[1][2]。

### 2. 阶数堆高却不稳/噪声变差

**局限**：多运放引入噪声、直流误差与振荡风险。
**改进**：提高 OSR 换低阶；或改 Σ-Δ；运放噪声纳入 ENOB 预算[4][6]。

### 3. 把 \(f_c\) 贴在信号边缘

**局限**：容差与 −3 dB 点吞掉有用带宽。
**改进**：\(f_c\) 留 20–50% 量级余量；通带内用数字滤波收紧[3][5]。

### 4. 忽略传感器自身带宽与干扰

**局限**：电机/开关电源谐波远高于信号带宽。
**改进**：在传感器端就近滤波；屏蔽与接地与 AAF 一体设计[7][8]。

## 6. 实践要点

1. 口诀：定信号带宽 → 选 \(f_s\) → 算过渡带衰减 → 选拓扑。
2. 振动类 1 kHz 带宽：优先评估 Σ-Δ；若用 SAR，用过采样+四阶级思路做预算。
3. 量产用 C0G+1% 电阻，并抽测幅频。

## 参考文献

[1] A. V. Oppenheim, R. W. Schafer, Discrete-Time Signal Processing, Pearson.
[2] W. Kester (ed.), Data Conversion Handbook, Analog Devices.
[3] Texas Instruments, AN-779 A Basic Introduction to Filters.
[4] Maxim/ADI, AN-928 Anti-Aliasing Analog Filters for Data Acquisition.
[5] B. Razavi, Principles of Data Conversion System Design, IEEE Press.
[6] ADC oversampling and decimation application notes (TI/ADI).
[7] Passive filter design handbooks (Sallen-Key coefficient tables).
[8] Sensor signal chain EMI/RFI filtering guides.
[9] Nyquist-Shannon sampling theorem — classic statements and engineering caveats.
[10] MCP600x / general-purpose op-amp datasheets (GBW for filter stages).
[11] IEC/IEEE literature on vibration measurement sampling practice.
