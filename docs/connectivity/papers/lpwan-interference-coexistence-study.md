---
schema_version: '1.0'
id: lpwan-interference-coexistence-study
title: LPWAN技术间干扰共存研究
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - lpwan-comparison
  - lpwan-capacity-planning-dense
tags:
  - LPWAN
  - 共存
  - 干扰
  - LoRaWAN
  - Sigfox
  - ISM
  - 占空比
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# LPWAN技术间干扰共存研究

> **难度**：🔴 高级 | **领域**：频谱共存 | **阅读时间**：约 22 分钟

## 日常类比

美食街里火锅油烟铺得宽（LoRa 宽带啁啾）、烧烤摊烟柱极窄但冲（Sigfox 超窄带）、面馆偶尔冒蒸汽（Wireless M-Bus 短突发）。共用一条街时，谁呛谁、怎么错峰，就是免许可频段上多 LPWAN 共存问题[1][4]。

## 摘要

分析欧洲 868 MHz 等 ISM（Industrial, Scientific and Medical）子带上 LoRaWAN、Sigfox、Wireless M-Bus 的互干扰机制、密度阈值与缓解手段。文中 PDR 下降百分比、设备/km² 多来自文献或试点量级，**不可直接外推到任意城市**[1][2][5]。

## 1. 频谱与信号形态

| 子带倾向 (MHz) | 常见用途 | 占空比倾向 |
|----------------|----------|------------|
| 868.0–868.6 | LoRa 上行信道、Sigfox UL 等 | 常 1% |
| 868.7–869.2 | LoRa / W-MBus 等 | 常 0.1% |
| 869.4–869.65 | Sigfox DL、LoRa RX2 等 | 常 10% |

LoRa：CSS，典型 125 kHz 信道扫频。Sigfox：~100 Hz 微信道，在数百 kHz 内随机选频并常发 3 次。W-MBus：GFSK 短突发。带宽差三个数量级，决定干扰不对称[4][5]。

## 2. LoRa → Sigfox

Chirp 扫过时，对 Sigfox 接收机像快速窄带脉冲串；完整帧含大量符号，累积可显著抬升干扰。功率落入 100 Hz 通道时，相对 125 kHz 有约 30 dB 量级的带宽稀释，但近距离仍可能相对 Sigfox 灵敏度留下很大负裕量——**近端 LoRa 可严重伤 Sigfox**[1][5]。

文献与城市试点常见叙事：随 LoRa 密度升高，Sigfox PDR 从轻微退化到两位数百分点下降；曲线常呈非线性，过临界密度后加速恶化[1]。

## 3. Sigfox → LoRa

Sigfox 对 LoRa 是窄带干扰；LoRa 扩频处理增益随 SF 增加，高 SF 更耐窄带干扰，但 ToA 更长、更易与其他 LoRa 自撞。多设备同时落入同一 125 kHz 时，干扰功率按个数近似非相干累加[1][8]。

| 方向 | 典型结论倾向 |
|------|----------------|
| LoRa 伤 Sigfox | 更明显（缺扩频保护） |
| Sigfox 伤 LoRa | 相对较轻，高 SF 更耐、低 SF 更脆 |
| W-MBus | 占空比低、突发短，影响常最小 |

## 4. 监管：占空比与 LBT

占空比按**每设备**计算，但干扰按**聚合空口**累积——千台各自合规，热点仍可“塞满”。Listen Before Talk（LBT）可作部分频段替代策略，但低功率谱密度信号可能低于检测门限，出现隐藏节点[4][6]。

## 5. 密度阈值（示意）

| 阶段 | 总密度量级 | 共存含义 |
|------|------------|----------|
| 安全 | 较低千级/km² 以下 | 互扰常可忽略 |
| 注意 | 数千 | 轻微 PDR 损失 |
| 警告 | 更高数千～近万 | 需功率/信道措施 |
| 危险 | 更高 | 必须干预或改技术 |

均值安全不等于热点安全：商业区密度可比城市均值高一个数量级[2]。

## 6. 缓解策略

| 手段 | 思路 | 难点 |
|------|------|------|
| 功率控制 / ADR | 够用即可，减溢出干扰 | 依赖测量质量 |
| 频率分区 | 协商半带子带 | 多运营商协调 |
| 时间错峰 | 时隙或随机退避 | 跨技术时钟难 |
| 礼貌接入框架 | ETSI 等“合理接入”概念 | 商业不愿共享细节 |

代尔夫特等试点叙事：共存后 Sigfox PDR 降幅常大于 LoRa；功率与信道优化可收回相当比例损失——具体数字随实验设计变化[1][7]。

## 7. 局限、挑战与可改进方向

### 1. 仿真假设均匀

**局限**：均匀泊松部署低估热点碰撞[2]。
**改进**：用真实建筑/业务热力图驱动仿真。

### 2. 单侧优化

**局限**：只给 LoRa 加网关可能更伤邻居 Sigfox。
**改进**：跨运营商干扰预算与联合 Pilot。

### 3. 静态监管不足

**局限**：纯占空比不管聚合密度[4]。
**改进**：探索动态频谱数据库、密度感知退避；跟进 ETSI 演进。

### 4. 新制式入场

**局限**：mioty、Sidewalk、DECT-2020 NR+ 等再挤同一 ISM[9]。
**改进**：选型阶段做共存清单；高可靠业务迁授权频谱。

## 8. 实践要点

1. 部署前扫描子带占用与已有 LPWAN 密度。
2. 默认开启 ADR/最小功率；避免全员 SF12+满功率。
3. PDR SLA 分技术、分热点写，不写城市平均值。

## 参考文献

[1] K. Mikhaylov et al., "On LoRaWAN Scalability: Empirical Evaluation of Susceptibility to Inter-Network Interference," EuCNC.
[2] M. Lauridsen et al., coverage comparison GPRS/NB-IoT/LoRa/Sigfox, IEEE VTC.
[3] M. Haghighi et al., game-theoretic spectrum management surveys (context).
[4] ETSI TR 103 526, LP-WAN-CSS system reference document.
[5] C. Orfanidis et al., interference between LoRa and IEEE 802.15.4g, WoWMoM.
[6] ETSI EN 300 220, SRD duty cycle / LBT related requirements.
[7] Academic/city pilot reports on LoRa–Sigfox coexistence (treat as case-specific).
[8] F. Adelantado et al., "Understanding the Limits of LoRaWAN," IEEE Commun. Mag.
[9] Industry notes on emerging sub-GHz LPWAN entrants and coexistence.
[10] U. Raza et al., IEEE COMST LPWAN overview (background).
[11] Semtech / Sigfox coexistence application notes (vendor perspective).
[12] Wireless M-Bus (EN 13757) physical layer overview for burst interference context.
