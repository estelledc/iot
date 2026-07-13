---
schema_version: '1.0'
id: backscatter-communication
title: 反向散射通信：迈向零功耗物联网
layer: 2
content_type: survey
difficulty: advanced
reading_time: 22
prerequisites:
  - backscatter-communication-ambient-iot
  - link-budget-calculation-lpwan
tags:
  - 反向散射
  - 零功耗
  - RFID
  - WiFi Backscatter
  - Ambient IoT
  - 能量收集
  - 超低功耗
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 反向散射通信：迈向零功耗物联网

> **难度**：🔴 高级 | **领域**：超低功耗通信 | **阅读时间**：约 22 分钟

## 日常类比

照镜子并不“发光”：灯的光照到你，身体反射后镜子里才有像。传统无线要自带“手电筒”（振荡器+功放），发射毫秒级蓝牙低功耗（Bluetooth Low Energy, BLE）往往比微控制器跑一秒更耗电。反向散射（Backscatter）改“借光”：用射频开关改天线阻抗，把环境里已有的 Wi-Fi/BLE/蜂窝/电视信号调制成数据，通信功耗可从毫瓦（mW）量级降到微瓦（μW）量级——具体倍数随占空比与实现变化，不宜写死“必降 1000 倍”[1][3][9]。

## 摘要

综述单基地/双基地/环境反向散射架构，Wi-Fi、BLE、LoRa 反向散射路线，功耗对比与多标签/机器学习解码前沿，并指向第三代合作伙伴计划（3rd Generation Partnership Project, 3GPP）Ambient IoT。距离、速率、电池年数为研究原型或厂商宣传量级，**非通用 SLA**[5][8][9]。

## 1 三种架构

| 架构 | 载波来源 | 优点 | 局限 |
|------|----------|------|------|
| 单基地（Monostatic） | 读写器自发自收 | 系统简单、标签极便宜 | 自干扰；超高频射频识别（UHF RFID）典型约数米量级 |
| 双基地（Bistatic） | 发射与接收分离 | 自干扰小，距离可至数十米量级 | 专用基础设施成本 |
| 环境（Ambient） | 已有 Wi-Fi/广播/蜂窝 | 少专用载波源 | 信号不可控，解调难 |

UHF RFID 代表：EPC Gen2 / ISO 18000-6C[10]。Ambient 概念由华盛顿大学等在 SIGCOMM 2013 提出[1]。

## 2 Wi-Fi / BLE / LoRa 反向散射

**Wi-Fi**：标签以 MHz 量级切换阻抗，把入射信号频移到另一信道，使普通 Wi-Fi 接收机解码（Passive Wi-Fi、Interscatter 等）[2][3][4]。

| 指标 | 传统 Wi-Fi SoC（示意） | Wi-Fi 反向散射原型（示意） |
|------|------------------------|----------------------------|
| 发送功耗 | 约数百 mW 量级 | 约十余 μW 量级 |
| 数据率 | 数十～数百 Mbps | 约 1–11 Mbps 量级（研究） |
| 距离 | 数十米量级 | 约数米至数十米量级 |

**BLE**：反射并整形为广播包，手机可直接收——适合智能标签、贴片传感等近场交互[4]。

**LoRa**：高灵敏度（可在负 SNR 量级解调）利于极弱反射；LoRea 等报告室外约数百米、后续工作宣称公里量级——依赖载波布局与调制，需独立复现[5][6][7]。

## 3 硬件与功耗

典型标签：印刷天线 + 射频开关（约 1–10 μW 量级）+ 低功耗微控制器 + 可选传感器/能量采集。没有振荡器与功放是功耗断崖的主因。

| 技术 | 通信功耗量级 | 备注 |
|------|--------------|------|
| Wi-Fi / NB-IoT 发送 | 约 10² mW | 占空比决定寿命 |
| BLE / LoRa 有源 | 约数～数十 mW | 低占空比可至年 |
| Wi-Fi/BLE/LoRa 反向散射 | 约数～十余 μW | 研究/产品宣称 |
| 被动 UHF RFID | 近 0（射频供能） | 依赖读写器场强 |

纽扣电池“十年”叙事假设极低占空比与理想休眠，须用焦耳/日模型核算[8][9]。

## 4 前沿与应用

机器学习端到端解码、多标签碰撞（传统 EPC Q 算法效率有限）、全双工自干扰消除扩距、多跳中继等仍在会议系统阶段，论文名与数字随年份变化，选型时核对原始实验条件[11][12][13]。

应用：Wiliot 类无电池 BLE 传感贴纸（冷链/零售试点）；体内反向散射传感；土壤埋入式 UHF 传感。IEEE 802.11ba 唤醒无线电（Wake-Up Radio, WUR）偏超低功耗**接收**；反向散射偏超低功耗**发送**，可互补[14]。3GPP Rel-19 Ambient IoT 研究把蜂窝基础设施作射频源，目标海量低成本终端[9]。

## 5 局限、挑战与可改进方向

### 1. 双重路径损耗

**局限**：源→标签→接收两次传播，功率近似随距离四次方衰减，距离难与有源比[5][10]。
**改进**：双基地布局、靠近接收机部署、定向天线、必要时有源中继。

### 2. 环境载波不可控

**局限**：Wi-Fi 间歇、蜂窝结构复杂，吞吐抖动大[1][2]。
**改进**：多源融合；关键链路保留专用激励器。

### 3. 标准化与安全滞后

**局限**：除 RFID 外互操作弱；明文反射易伪造/窃听[9][10]。
**改进**：跟进 3GPP Ambient IoT；物理层密钥/PUF 与应用层鉴权。

### 4. 宣传数字外推

**局限**：把实验室峰值速率/距离写进产品承诺[3][8]。
**改进**：按目标场景复现 PER、占空比与能量收集功率密度。

## 参考文献

[1] V. Liu et al., Ambient Backscatter: Wireless Communication Out of Thin Air, ACM SIGCOMM, 2013.
[2] B. Kellogg et al., Wi-Fi Backscatter, ACM SIGCOMM, 2014.
[3] B. Kellogg et al., Passive Wi-Fi, USENIX NSDI, 2016.
[4] V. Iyer et al., Inter-Technology Backscatter, ACM SIGCOMM, 2016.
[5] P. Zhang et al., LoRea, USENIX NSDI, 2018.
[6] A. Varshney et al., LoRa Backscatter, ACM HotNets, 2017.
[7] Y. Peng et al., PLoRa, ACM SIGCOMM, 2018.
[8] Wiliot, Battery-Free Bluetooth Sensing Platform, 厂商资料, 2024.
[9] 3GPP TR 38.848 / 相关 Ambient IoT 研究, Release 19.
[10] S. Thomas and M. S. Reynolds, QAM Backscatter for Passive UHF RFID, IEEE RFID, 2012.
[11] J. Zhao et al., NeuralRFID 等深度学习防碰撞工作, NSDI 等, 2024.
[12] X. Wang et al., TurboScatter 等全双工反向散射, MobiCom 等, 2024.
[13] 多跳/远距 LoRa 反向散射研究（NSDI 等会议系统）.
[14] IEEE 802.11ba-2021, Wake-Up Radio.
