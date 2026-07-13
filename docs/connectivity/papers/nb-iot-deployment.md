---
schema_version: '1.0'
id: nb-iot-deployment
title: NB-IoT 规模部署：从标准到实践
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - cellular-iot-evolution-2g-5g
  - lte-cat-m1-vs-nbiot
tags:
  - NB-IoT
  - LPWAN
  - 规模部署
  - 覆盖增强
  - 智能抄表
  - 运营商
  - 带内部署
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# NB-IoT 规模部署：从标准到实践

> **难度**：🟡 中级 | **领域**：蜂窝物联网 | **阅读时间**：约 22 分钟

## 日常类比

地下管井水表、厨房铁柜燃气表：要穿墙、要电池撑多年、还要全市海量并发。Wi-Fi 进不了井，蓝牙不够远，普通 4G 太费电。窄带物联网（Narrowband IoT, NB-IoT）正是为“深覆盖 + 小包 + 海量连接”设计的蜂窝低功耗广域技术，多在现有长期演进（LTE）基站上以软件/频谱配置方式开通[1][2]。

## 摘要

从部署模式、覆盖增强代价、中国规模化应用经验到时延/移动性边界。基站数、连接数等公开统计随口径与年份变化，文中为量级描述，**需对照最新运营商/监管披露**[8][9]。

## 1. 协议要点

NB-IoT 占用约 180 kHz（一个物理资源块量级），优化小数据与覆盖；省电模式（PSM）、扩展非连续接收（eDRX）、重复传输是三大工程杠杆。控制面/用户面优化降低每次上报的信令开销，但极端覆盖下空口仍可能很慢[1][3]。

## 2. 三种部署模式

| 模式 | 频谱位置 | 特点 |
|------|----------|------|
| 带内（In-band） | LTE 载波内 | 与 LTE 共享；需功率/资源协调 |
| 保护带（Guard-band） | LTE 保护带 | 少占业务 PRB；实现依赖设备能力 |
| 独立（Standalone） | 重耕 GSM 等 | 干扰隔离相对清晰 |

中国运营商公开材料中常见差异化选择（Band 与模式随网络演进可能调整）[4][8]：

| 运营商（示意） | 常见叙述 | 频段叙事 |
|----------------|----------|----------|
| 中国移动 | 带内/独立等 | 如 Band 8 等 |
| 中国电信 | 独立等 | 如重耕低频 |
| 中国联通 | 保护带等 | 如 Band 8 相关 |

选型看干扰、站址与终端频段认证，而非只看白皮书一张表。

## 3. 覆盖增强与代价

最大耦合损耗（Maximum Coupling Loss, MCL）规划常提到相对 GPRS 约 +20 dB 量级目标（如 164 dB 叙事）[1][5]。手段包括重复、功率增强、低阶调制、单音上行、基站接收分集等——增益可叠加叙述，但**延迟、容量与功耗同步恶化**，不可把“分贝相加”当成无代价余量[5][6]。

| 技术 | 作用 | 主要代价 |
|------|------|----------|
| 重复传输 | 合并增益 | 时延、占空比、容量 |
| 功率增强 | 下行更易听清 | 基站功率预算 |
| 单音上行 | 能量更集中 | 速率与调度灵活性 |
| 低阶调制 | 更鲁棒 | 吞吐下降 |

## 4. 规模应用与边界

公开报道中，智能抄表、烟感等是中国 NB-IoT 的主力叙事；路灯、停车、农业监测等亦有部署。共享单车等高移动性场景往往暴露小区重选与连续切换短板——更宜评估 LTE-M/5G RedCap 等[7][9]。

| 约束 | 实践含义 |
|------|----------|
| 时延 | 深覆盖或长 eDRX 下，秒级到小时级可达性都可能出现 |
| 移动性 | 连接态移动弱于智能手机 LTE |
| 下行 | 依赖寻呼窗口；长睡眠难“随时遥控” |
| 容量 | 高重复用户显著占用小区资源 |

## 5. 演进方向

Release 14+ 增加定位、多播、多载波等；再往后有唤醒信号、非地面网络（NTN）等议题。部署要以终端/核心网实际开通能力为准，标准有不等于商用有[3][10]。

## 6. 局限、挑战与可改进方向

### 1. 深覆盖挤占容量

**局限**：CE 高等级用户拖慢整小区调度[5][6]。
**改进**：分区覆盖；天线/安装优化降重复；非关键数据降频。

### 2. 下行与运维预期错配

**局限**：业务方按“4G 随时在线”验收烟感/阀控[7]。
**改进**：合同写清最大下行延迟与 PSM/eDRX 参数；紧急场景用可本地执行策略。

### 3. 移动与漫游

**局限**：跨小区、跨省物流体验不稳定[7]。
**改进**：静止/准静止优先；移动资产改 LTE-M 或多模。

### 4. 统计口径

**局限**：连接数含测试卡/休眠卡，难直接当活跃设备[8][9]。
**改进**：运营看板区分附着、活跃上报、成功投递率。

## 7. 实践要点

1. 先做目标安装点的路测与 MCL 估算，再锁模组与套餐。
2. 与 `nbiot-power-saving-psm-edrx`、`nbiot-coverage-enhancement-repetition` 参数联调。
3. 验收看成功率百分位与电池温度剖面，不看实验室峰值速率。

## 参考文献

[1] 3GPP TS 36.300 / NB-IoT overall description related specs.
[2] 3GPP TR 45.820 cellular system support for ultra-low complexity IoT.
[3] 3GPP Release 13–18 NB-IoT feature summaries.
[4] GSMA Mobile IoT / NB-IoT deployment guides.
[5] NB-IoT coverage enhancement and MCL analyses.
[6] Repetition vs latency/capacity trade-off studies.
[7] Industry reports on NB-IoT mobility limitations vs LTE-M.
[8] China operator / MIIT public statistics on NB-IoT scale (verify year/口径).
[9] Smart metering and smoke-detector NB-IoT case studies.
[10] NB-IoT NTN / satellite related 3GPP work items (deployment-dependent).
[11] In-band / guard-band / standalone deployment comparisons.
[12] Module vendor power and CE level application notes.
