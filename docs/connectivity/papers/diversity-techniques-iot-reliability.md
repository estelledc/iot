---
schema_version: '1.0'
id: diversity-techniques-iot-reliability
title: 分集技术提高IoT无线链路可靠性
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - fading-multipath-iot-channel
  - forward-error-correction-iot
tags:
- 分集
- MRC
- 宏分集
- LoRaWAN
- NB-IoT
- 衰落
- 可靠性
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 分集技术提高IoT无线链路可靠性

> **难度**：🔴 高级 | **领域**：无线可靠性、LPWAN | **阅读时间**：约 22 分钟

## 日常类比

山谷里只靠一座信号塔，暴风雨一来电话就断；周围三座塔则此消彼长。分集（Diversity）就是不把鸡蛋放同一篮子：提供多个尽量独立的信号副本，使同时深衰落的概率近似按独立度相乘下降——前提是副本真独立[1]。

## 摘要

概述空间/频率/时间/极化分集与选择合并、EGC、MRC，并对照 LoRaWAN 宏分集与 NB-IoT 重复传输。dB 增益与丢包率数字来自经典公式或特定部署，换环境须重测[1][2][4]。

## 1 为何需要

多径与遮挡造成衰落；单链路深衰落概率虽「不大」，对告警类业务仍不可接受。N 条独立链路同时失败概率约 P^N（独立假设）[1]。

| 类型 | 独立性来源 | IoT 常见落点 |
|------|------------|--------------|
| 空间 | 天线位置 | 网关多天线、多网关 |
| 频率 | 不同载波 | 跳频/多信道重传 |
| 时间 | 不同时刻 | ARQ/重复/HARQ |
| 极化 | 正交极化 | 紧凑网关天线 |
| 码 | 扩频/编码 | CSS、蜂窝重复 |

## 2 合并与空间

天线间距宜大于约半波长量级（Sub-GHz 间距更大）[1]。微分集：同站多天线；宏分集：地理分开的接收点（LoRaWAN 多网关天然契合）[2]。

| 合并 | 复杂度 | 信息需求 | 性能倾向（多分支） |
|------|--------|----------|-------------------|
| 选择合并 | 低 | 分支质量 | 有增益，非最优 |
| EGC | 中 | 相位对齐 | 接近 MRC |
| MRC | 高 | SNR+相位 | 线性最优合并 |

终端侧常选简单；网关侧可上 MRC[1]。

## 3 频率与时间

频率间隔大于相干带宽才近似独立。LoRaWAN 多上行信道随机选、重传换信道，兼得频率+时间分集；蓝牙跳频是另一极端例子[2]。静态节点相干时间可能很长，短间隔重传要配合换频或拉大间隔[1]。

NB-IoT 覆盖增强靠大量重复，理论功率增益约 10·log10(N) dB 量级，代价是空口时间与速率；与 LoRaWAN「堆网关」路线不同：一个耗终端空时，一个耗基础设施[4]。

## 4 LPWAN 组合策略

LoRaWAN 可叠：扩频处理增益、信道随机、多网关、确认重传、ADR——终端多「只发不管合并」[2][3]。网关先加双天线/极化，往往比立刻新布网关更省；宏分集增益通常更大但更贵——用覆盖与丢包曲线决策，避免固定「3–5 dB / 8–10 dB」当合同条款[1][2]。

## 5 局限、挑战与可改进方向

### 1. 独立性被高估

**局限**：相关衰落（共同遮挡）使 P^N 过于乐观。
**改进**：网关空间拉开；测分支相关系数；金属厂房做现场驱动测试[1][9]。

### 2. 时间分集换延迟/占空比

**局限**：重传与 NB 重复吃电池与法规占空比。
**改进**：仅关键帧确认；重复次数按 CE 等级自适应；能上宏分集则少靠极端重复[4][10]。

### 3. 终端多天线不现实

**局限**：硬币电池节点难做空间分集。
**改进**：分集放在网关/网络侧；终端侧靠编码、跳频与功率/SF 自适应[2][3]。

### 4. 案例丢包率叙事不可复制

**局限**：工厂「15%→0.001%」依赖具体网关密度与确认策略。
**改进**：分阶段加分集并每次只改一因子；用 packet delivery ratio 置信区间报告[2][9][12]。

## 参考文献

[1] A. Goldsmith, *Wireless Communications*, Cambridge University Press, 2005.
[2] M. Bor et al., "LoRa for the Internet of Things," EWSN, 2016.
[3] P. Marcelis et al., "DaRe: Data Recovery through Application Layer Coding for LoRaWAN," IoTDI, 2017.
[4] 3GPP TR 45.820, cellular IoT / coverage enhancement related material.
[5] M. Hata, empirical path-loss modeling, IEEE TVT, 1980 (propagation context).
[6] Diversity combining theory (selection/MRC/EGC) standard textbook chapters.
[7] LoRa Alliance regional parameters (channel plans enabling frequency diversity).
[8] NB-IoT repetition and HARQ procedural specifications (3GPP).
[9] Industrial indoor fading measurement studies.
[10] Duty-cycle constrained LPWAN reliability design notes.
[11] Polarization diversity in multipath environments.
[12] IoT reliability metrics and measurement methodology papers.
