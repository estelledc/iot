---
schema_version: '1.0'
id: lte-cat-m1-vs-nbiot
title: LTE Cat-M1与NB-IoT技术选型决策
layer: 2
content_type: comparison
difficulty: intermediate
reading_time: 20
prerequisites:
  - cellular-iot-evolution-2g-5g
  - lpwan-comparison
tags:
  - LTE-M
  - Cat-M1
  - NB-IoT
  - 蜂窝物联网
  - PSM
  - 移动性
  - 双模
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# LTE Cat-M1与NB-IoT技术选型决策

> **难度**：🟡 中级 | **领域**：蜂窝IoT选型 | **阅读时间**：约 20 分钟

## 日常类比

北京寄上海：顺丰（快、服务全、稍贵）对平邮（慢、便宜、功能少）。LTE Cat-M1（亦称 LTE-M / eMTC）与窄带物联网（NB-IoT）同属 3GPP 低功耗广域蜂窝，但一个偏“全能减配 LTE”，一个偏“极简传感器管道”[1][2]。

## 摘要

从带宽、覆盖、移动性、语音、功耗与模组成本对比二者，并给出地区部署差异与双模策略。速率、MCL、模组美元价为规格或市场**量级**，随 Release 与供应链变化[3][5]。

## 1. 定位

| 技术 | 设计思路 | 典型瞄准 |
|------|----------|----------|
| Cat-M1 | LTE 做减法：缩带宽、单天线、半双工等 | 移动追踪、语音、中等数据 |
| NB-IoT | 窄带做加法：只留 IoT 必需 | 表计、深覆盖、海量小包 |

3GPP Release 13 起双轨并行，不是简单重复建设[1]。

## 2. 规格对照

| 参数 | Cat-M1 | NB-IoT |
|------|--------|--------|
| 带宽量级 | 1.4 MHz | ~200 kHz（180 kHz PRB） |
| 峰值速率倾向 | ~Mbps | 数百 kbps 量级（随版本/配置） |
| 移动性 | 连接态切换更成熟 | 早期以重选为主 |
| 语音 | 可 VoLTE | 通常无 |
| MCL 目标引用 | 较低一档增强 | 常引用更高深覆盖目标 |

NB-IoT 可独立/保护带/带内部署；Cat-M1 更贴近 LTE 载波资源占用叙事[1][5]。

## 3. 关键差异

**速率与 OTA**：带宽差使大固件、波形类突发在 Cat-M1 上更从容；传输时长影响无法深睡的窗口。

**覆盖**：NB-IoT 靠窄带功率谱密度与重复传输换深覆盖，适合地下室表计；Cat-M1 室内增强仍强于传统 LTE，但极端地下常让位 NB-IoT[2][5]。

**移动性与语音**：车载/穿戴连续上报、紧急呼叫按钮 → Cat-M1。固定点小包 → NB-IoT。

**功耗**：二者均有 PSM（Power Saving Mode）、eDRX（extended Discontinuous Reception）。活跃期 NB-IoT 协议更瘦；极低频次时建链开销占比大，需按剖面测算，而非背电池年数广告[2][9]。

| 成本项 | 倾向 |
|--------|------|
| 模组复杂度/标价 | NB-IoT 常更低 |
| 双模溢价 | 换全球 SKU 灵活性 |
| 连接费 | 视运营商套餐，不单看模组 |

## 4. 地区与双模

| 地区倾向 | 常见主推 |
|----------|----------|
| 北美 | Cat-M1 较强 |
| 中国 | NB-IoT 规模大 |
| 欧洲 | 常混合 |

不确定市场或漫游：Cat-M1 + NB-IoT 双模模组，按覆盖与业务策略选网；代价是物料与认证成本[3][4]。

## 5. 决策树（压缩）

需要语音？→ Cat-M1。会移动且要连续会话？→ Cat-M1。极深覆盖固定点？→ NB-IoT。追求最低物料且小包？→ NB-IoT。地区未定？→ 双模。其余用本地运营商覆盖图与资费裁决[2]。

## 6. 演进

Rel-14+ 增强定位、多播、速率等；均可向 5G 核心演进叙事靠拢。5G RedCap / eRedCap 填中端，但行业预期 Cat-M1/NB-IoT 仍会长尾共存至至少本年代末——新项目短期仍可大胆用，中期预留迁移评估[2][10]。

## 7. 局限、挑战与可改进方向

### 1. 用峰值速率选型

**局限**：IoT 业务受覆盖重复与信令支配，峰值很少达到[5]。
**改进**：按链路预算与日流量算能量，不按 Mbps 广告。

### 2. 忽视运营商差异

**局限**：同技术不同国家的频段、PSM 参数、资费差很大[4]。
**改进**：以目标国覆盖证明与 APN/QoS 条款招标。

### 3. 单模锁死全球 SKU

**局限**：北美设备抄中国 NB-IoT BOM 会失败。
**改进**：双模或分区域 SKU；认证矩阵前置。

### 4. 被 RedCap 叙事干扰

**局限**：过早押注未商用档位延误交付[10]。
**改进**：1–3 年项目用成熟 Cat-M1/NB-IoT；并行跟踪 RedCap。

## 8. 实践要点

1. 三问：动吗？说话吗？埋地下吗？
2. 用流量剖面算电池，不抄白皮书年限。
3. 验收含切换/重选、深覆盖点与 OTA 时间窗。

## 参考文献

[1] 3GPP TR 45.820, CIoT, Release 13.
[2] GSMA, Mobile IoT in the 5G Future: NB-IoT and LTE-M, 2018/2020 updates.
[3] Qualcomm, LTE IoT evolution materials (Cat-M1/NB-IoT).
[4] Ericsson, Cellular IoT evolution white papers.
[5] Y. P. E. Wang et al., "A Primer on 3GPP Narrowband Internet of Things," IEEE Commun. Mag., 2017.
[6] 3GPP TS 36.300 / 36.321, E-UTRA overall and MAC (relevant features).
[7] 3GPP feature summaries for eMTC / NB-IoT Rel-14 enhancements.
[8] Vendor module datasheets for power and throughput (case-specific).
[9] GSMA guidelines on PSM and eDRX configuration.
[10] 3GPP RedCap / eRedCap overviews (positioning vs LPWAN cellular).
[11] Operator deployment maps (AT&T/Verizon/China Mobile etc., verify current).
[12] U. Raza et al., IEEE COMST LPWAN overview (context among LPWANs).
