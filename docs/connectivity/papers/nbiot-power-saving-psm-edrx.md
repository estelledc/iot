---
schema_version: '1.0'
id: nbiot-power-saving-psm-edrx
title: NB-IoT省电模式PSM与eDRX配置优化
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - lte-cat-m1-vs-nbiot
  - nb-iot-deployment
tags:
  - NB-IoT
  - PSM
  - eDRX
  - 低功耗
  - TAU
  - 电池寿命
  - 寻呼
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# NB-IoT省电模式PSM与eDRX配置优化

> **难度**：🟡 中级 | **领域**：蜂窝 IoT 功耗 | **阅读时间**：约 20 分钟

## 日常类比

无聊会议里老板可能点名：要么约定“每小时我来报到，其他时间别找我”（省电模式 Power Saving Mode, PSM），要么“每十几分钟抬头看一眼有没有人叫我”（扩展非连续接收 extended Discontinuous Reception, eDRX）。窄带物联网（NB-IoT）要靠电池撑多年，必须少醒来，又要在业务上可接受的下行可达性之间折中[1][2]。

## 摘要

解释 PSM/eDRX 定时器、协商、场景选型与常见陷阱。电流与寿命估算依赖模组、温度、覆盖等级与上报模型，文中微安/毫安为量级，**须用功耗分析仪实测**[7][9]。

## 1. 为何需要特殊省电

传统 LTE 空闲态仍较频繁听寻呼与做跟踪区更新（Tracking Area Update, TAU）。对小包传感器，射频周期性醒来可占掉大部分平均电流。NB-IoT 用 PSM 深度睡眠、eDRX 拉长寻呼周期来压低占空比[1][3]。

## 2. PSM

设备完成通信后进入不可达的深度睡眠，保留注册；到 TAU/主动上行时再醒。关键定时器由终端请求、网络授权（可能改小）[2][4]。

| 点 | 含义 |
|----|------|
| 可达性 | PSM 睡眠期间网络难寻呼到 |
| 下行 | 通常等设备下次上行/TAU |
| 电流 | 睡眠可到微安量级（模组相关） |

适合：纯上行周期上报（抄表）、可接受“命令要等下次醒来”。

## 3. eDRX

在空闲态按超长周期醒来，于寻呼时间窗口（Paging Time Window, PTW）内听寻呼。周期选项从数十秒到约数小时量级（以网络支持与协商结果为准）[2][5]。

| 周期倾向 | 适用直觉 |
|----------|----------|
| 数十秒 | 需较快下行的执行器 |
| 数分钟 | 一般监控 |
| 数十分钟–更长 | 接近 PSM，仍保留一定可达性 |

## 4. 选型对照

| 特性 | PSM | eDRX |
|------|-----|------|
| 睡眠期寻呼 | 基本不可达 | 周期内可达 |
| 下行延迟 | 等到主动醒 | 最大约一个 eDRX 周期 |
| 额外醒来 | 主要 TAU/数据 | 每周期听寻呼 |
| 典型业务 | 定时上报 | 需远程命令但非实时 |

二者常组合：活跃期用 eDRX，长期静默用 PSM。网络可能拒绝过激进请求，**必须以授权值为准**[4][6]。

## 5. 陷阱与优化

| 问题 | 后果 | 对策 |
|------|------|------|
| 以为请求值=生效值 | 电池模型失真 | 读网络返回定时器 |
| 覆盖差导致高重复 | 抵消省电 | 先改善射频/安装 |
| 应用层频繁 DNS/TLS | 睡眠被打断 | 会话复用、减握手 |
| 时钟不准错过 PTW | 丢下行 | 同步策略与重试 |

## 6. 局限、挑战与可改进方向

### 1. 可达性与运维习惯冲突

**局限**：平台按“在线设备”运维，PSM 设备显示离线引发误告警[6]。
**改进**：状态机区分睡眠/离线；工单允许延迟下行。

### 2. 网络改写参数

**局限**：运营商钳制最大 PSM/eDRX，实验室寿命算不准[4]。
**改进**：目标网络实网协商测试；合同写清支持的定时器范围。

### 3. 温度与电池非线性

**局限**：低温内阻上升，寿命远短于室温估算[8]。
**改进**：按部署气候做放电曲线；预留裕量。

### 4. 与 CE 重复叠加

**局限**：深覆盖每次醒来很贵[7][9]。
**改进**：降上报频率；批量数据；天线优先于堆电池。

## 7. 实践要点

1. 用库仑计/PPK 类工具测完整剖面：附着、上报、PTW、PSM。
2. AT/SDK 配置后立刻查询网络授予值。
3. 验收同时测：电池、下行命令成功延迟、丢寻呼率。

## 参考文献

[1] 3GPP TS 23.682 architecture enhancements for cellular IoT (PSM/eDRX).
[2] 3GPP TS 24.301 / 24.008 NAS timer related descriptions for PSM/eDRX.
[3] 3GPP TS 36.304 idle mode procedures (eDRX).
[4] GSMA Mobile IoT energy efficiency / PSM-eDRX guidelines.
[5] NB-IoT eDRX cycle values and PTW configuration notes.
[6] Operator policy impacts on granted PSM/eDRX timers.
[7] Module vendor power profiling application notes (nRF91/Quectel etc.).
[8] Primary battery performance vs temperature for IoT.
[9] Interaction of coverage enhancement repetitions with power saving.
[10] TAU periodicity trade-offs in PSM deployments.
[11] Application-layer session keep-alive anti-patterns on cellular IoT.
[12] Field battery lifetime case studies (treat as scenario-bound).
