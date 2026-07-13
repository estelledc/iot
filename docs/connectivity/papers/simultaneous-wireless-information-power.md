---
schema_version: '1.0'
id: simultaneous-wireless-information-power
title: 无线信息与能量同传SWIPT在IoT中的应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 14
prerequisites: UNKNOWN
tags:
  - SWIPT
  - 能量收集
  - 无线供电
  - 功率分割
  - 时间切换
  - 无电池IoT
  - RF能量
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 无线信息与能量同传SWIPT在IoT中的应用

> **难度**：🔴 高级 | **领域**：能量收集 | **阅读时间**：约 14 分钟

## 日常类比

植物同时从阳光里“取能”和“感知季节”；无线信息与能量同传（Simultaneous Wireless Information and Power Transfer, SWIPT）希望同一束射频（Radio Frequency, RF）既解码比特又整流成直流电。理想很美，实际受路径损耗与整流效率限制——**远场可收集功率通常极低，下文不作“部署即遗忘”承诺**[1][2]。

## 摘要

信息要波形保真（相位/幅度），能量要接收功率；接收机用时间切换（Time Switching, TS）或功率分割（Power Splitting, PS）等在速率-能量（Rate-Energy）区域折中。适合近距离、低占空比传感；大规模室外无电池仍多依赖专用无线电力传输或混合供能[1][3]。

## 1. 动机与约束

| 供能方式 | 典型问题 |
|----------|----------|
| 一次电池 | 更换运维贵 |
| 太阳能 | 室内/遮挡失效 |
| 专用无线充电 | 额外发射机，未必传数 |
| SWIPT | 复用通信波形，但能量密度受距离平方律约束 |

接收功率大致随距离快速下降；解码要信噪比（SNR），整流要足够输入功率与非线性效率——二者同向要“强信号”，电路上却常互抢资源[2][4]。

## 2. 接收机架构

| 架构 | 做法 | 优点 | 代价 |
|------|------|------|------|
| 时间切换 TS | 时段分给整流/解码 | 开关简单 | 时间互斥 |
| 功率分割 PS | 功率按 ρ 分两路 | 可同时进行 | 功分器损耗、噪声折中 |
| 天线切换等 | 多天线分角色 | 灵活 | 硬件与调度复杂 |

```
TS:  αT 收集能量，(1-α)T 传信息
PS:  ρ·P_r → 整流，(1-ρ)·P_r → 信息解码
```

转换效率 η 随输入功率非线性变化，低功率区效率往往很差，线性模型易高估可收集能量[3][5]。

## 3. 与波束成形/多用户

多天线发射可将能量波束对准能量用户、信息波束对准信息用户；存在干扰与安全（能量信号也可被窃听）权衡。物联网场景更常见的是：接入点间歇发“能量帧”，终端积够电再短包上报——接近无线电力传输（Wireless Power Transfer, WPT）调度，而非理想同传[6][7]。

| 场景叙事 | 可行性倾向 |
|----------|------------|
| 桌面/货架米级内传感 | 相对可谈 |
| 厂房数十米无电池 | 困难，需高 EIRP/定向 |
| 广域 LPWAN 终端 | 基本不靠 SWIPT 单独供能 |

## 4. 局限、挑战与可改进方向

### 1. 链路预算残酷

**局限**：自由空间损耗使 μW 级收集常见，难驱动持续射频。
**改进**：缩短距离、提高占空比休眠、混合光伏/振动；诚实写清可收集功率实测。

### 2. 整流非线性与模型失配

**局限**：论文常设恒定 η，现场随功率剧烈变化。
**改进**：用实测二极管模型；按输入功率分段仿真。

### 3. 信息与能量资源互抢

**局限**：提高 ρ 或 α 伤吞吐/时延。
**改进**：按电池状态自适应；能量优先仅在欠压时。

### 4. 法规与人体安全

**局限**：抬高发射功率受 SAR/EIRP 限制。
**改进**：合规预留余量；室内定向波束优于盲目加大功率。

## 5. 实践要点

1. 先测目标距离处可用 RF 功率密度，再谈协议。
2. 终端以 μA 级休眠电流设计，SWIPT 只补“偶尔醒来”。
3. 与 RFID/后向散射区分：后者常由阅读器近场/受控场供电，模型不同。

## 参考文献

[1] Varshney, L. R., "Transporting information and energy simultaneously," IEEE ISIT, 2008.
[2] Zhang, R. & Ho, C. K., "MIMO broadcasting for simultaneous wireless information and power transfer," IEEE Trans. Wireless Commun., 2013.
[3] Clerckx, B. et al., "Fundamentals of Wireless Information and Power Transfer," IEEE JSAC, 2019.
[4] Zhou, X. et al., "Wireless information and power transfer: architecture design and rate-energy tradeoff," IEEE Trans. Commun., 2013.
[5] Boshkovska, E. et al., "Practical non-linear energy harvesting model," IEEE Commun. Lett., 2015.
[6] Ulukus, S. et al., "Energy harvesting wireless communications: A review," IEEE JSAC, 2015.
[7] Lu, X. et al., "Wireless networks with RF energy harvesting: A contemporary survey," IEEE COMST, 2015.
[8] Perera, T. D. P. et al., "Simultaneous wireless information and power transfer (SWIPT): Recent advances and future challenges," IEEE COMST, 2018.
[9] FCC / ETSI RF exposure and EIRP related rules (jurisdiction-specific).
[10] Sample, A. P. et al., "Analysis of RF energy harvesting," related RFID/WPT literature.
[11] 3GPP / academic studies on WPT-assisted IoT (survey level).
