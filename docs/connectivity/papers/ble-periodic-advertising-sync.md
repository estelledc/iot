---
schema_version: '1.0'
id: ble-periodic-advertising-sync
title: BLE周期性广播与同步传输应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - ble-5-features-coded-phy
  - ble-power-consumption-profiling
tags:
  - BLE
  - 周期性广播
  - PAST
  - PAwR
  - Auracast
  - 同步
  - ESL
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# BLE周期性广播与同步传输应用

> **难度**：🔴 高级 | **领域**：BLE高级特性 | **阅读时间**：约 22 分钟

## 日常类比

火车站广播：控制中心按时刻表喊车次，显示屏对时后只在播报瞬间听，不必整天竖着耳朵。蓝牙低功耗（Bluetooth Low Energy, BLE）5.0 周期性广播（Periodic Advertising）让扫描者同步到固定间隔，仅在事件窗口开射频——一对多分发时比持续扫描省电得多[1]。

## 摘要

本文说明扩展广播与 SyncInfo、同步窗口、周期性广播同步传输（Periodic Advertising Sync Transfer, PAST）、带响应周期性广播（Periodic Advertising with Responses, PAwR）及 Auracast/电子货架标签（Electronic Shelf Label, ESL）场景。电流与续航估算依赖芯片与间隔，**作量级参考**[4][5]。

## 1. 传统广播局限

传统广播在信道 37/38/39 发送，间隔含随机延迟，扫描端难以精确预测，常需高占空比接收。接收电流多为毫安级，持续扫描会迅速耗尽纽扣电池——具体续航随电池容量与芯片而变[5]。

| 模式 | 接收端行为 | 功耗倾向 |
|------|------------|----------|
| 持续扫描 | RX 常开 | 很高 |
| 间歇扫描 | 降占空比 | 中，易漏包 |
| 周期同步 | 按时唤醒 | 低（间隔大时） |

## 2. 周期性广播原理

广播者维护扩展广播（带 AuxPtr）与辅助广播（含 SyncInfo），再按固定间隔发 `AUX_SYNC_IND`（数据信道跳频）。间隔由规范以 1.25 ms 为单位编码，可覆盖数毫秒至数十秒量级；单次用户数据可达约 254 字节并支持链式扩展[1]。

| 特性 | 普通广播 | 周期性广播 |
|------|----------|------------|
| 定时 | 含随机延迟 | 固定间隔 |
| 信道 | 主广播信道为主 | 数据信道跳频 |
| 接收 | 盲扫 | 同步窗口 |
| 方向 | 单向 | 单向（PAwR 可响应） |

SyncInfo 含偏移、间隔、信道映射、访问地址、CRC 初值、事件计数等[1]。

## 3. 同步与窗口

流程：收 `ADV_EXT_IND` → 跟 AuxPtr 收 `AUX_ADV_IND` 取 SyncInfo → 预测下一同步事件 → 维持跳频与窗口。窗口需覆盖双方睡眠时钟精度（Sleep Clock Accuracy, SCA）累积漂移；连续丢包时窗口放大，收复后再收缩[1][4]。

## 4. 功耗量级

设 RX 活跃数毫安、睡眠微安、窗口约毫秒级、间隔 100 ms～1 s，平均电流可落到数十微安量级——**须用功耗分析仪实测**[5]。相对持续扫描通常低一到两个数量级；与长连接间隔连接模式接近时，优势在一对多无连接数上限。

| 接收策略 | 平均电流倾向 | 备注 |
|----------|--------------|------|
| 持续扫描 | mA 级 | 短续航 |
| 低占空比扫描 | 亚 mA | 可能漏包 |
| 周期同步（较长间隔） | µA～百 µA | 适合广播分发 |

## 5. PAST 与 PAwR

**PAST（BLE 5.1）**：已同步设备经连接把同步参数传给第三方，跳过盲扫，利于 Auracast 手机→耳机、网关批量同步[1][3]。

**PAwR（BLE 5.4）**：在周期事件中划分子事件与响应时隙，广播者可收 ACK/短上行，支撑 ESL 等大规模可靠下发[2][6]。

| 能力 | 周期广播 | +PAST | +PAwR |
|------|----------|-------|-------|
| 一对多下行 | 有 | 有 | 有 |
| 快速帮同步 | 无 | 有 | 视部署 |
| 响应/ACK | 无 | 无 | 有 |

## 6. 选型与混合

| 需求 | 更合适 |
|------|--------|
| 海量接收、单向 | 周期性广播 |
| 需确认的批量下行 | PAwR |
| 点对点可靠双向 | 连接模式 |
| 音频广播 | Auracast（基于周期/BIS） |

楼宇中可：平面图用周期广播，门锁用连接，价签用 PAwR。

## 7. 局限、挑战与可改进方向

### 1. 单向与可靠性

**局限**：无 PAwR 时缺应用层 ACK，干扰下丢更新[1]。
**改进**：关键数据冗余发送；升级 PAwR；或混合连接补洞。

### 2. 同步丢失与时钟

**局限**：长间隔 + 劣质时钟 → 窗口过大、耗电回升或丢同步。
**改进**：选合适 SCA；丢包阈值触发重新同步；PAST 快速恢复。

### 3. 芯片与主机栈碎片

**局限**：主机/控制器对 PAST、PAwR 支持不一致。
**改进**：以特性比特与实机矩阵验收；模组选型写明 5.1/5.4 能力。

### 4. 广播者侧能耗与占空比法规

**局限**：短间隔高占空比抬升广播端耗电与共存压力。
**改进**：按业务选间隔；数据信道跳频与共存测试；ESL 用子事件分组。

## 8. 实践要点

1. 先稳定扩展广播 + SyncInfo，再优化间隔。
2. 用 Zephyr `bt_le_per_adv_*` / `bt_le_per_adv_sync_*` 验证回调与超时[4]。
3. ESL/音频场景分别核对 PAwR 与 BIG/BIS 参数，勿混用叙事。

## 参考文献

[1] Bluetooth SIG, "Bluetooth Core Specification," Periodic Advertising (e.g., v5.4 Vol 6).
[2] Bluetooth SIG, Periodic Advertising with Responses (PAwR) feature overviews.
[3] Woolley, M. / Bluetooth SIG, LE Audio / Auracast related whitepapers.
[4] Nordic Semiconductor / Zephyr, Periodic Advertising Sync samples.
[5] Nordic / TI BLE power measurement application notes (scan vs sync duty cycle).
[6] Bluetooth SIG, Electronic Shelf Label (ESL) profile materials.
[7] Bluetooth SIG, PAST (Periodic Advertising Sync Transfer) core feature description.
[8] Bluetooth SIG, Extended Advertising overview.
[9] Academic/industry evaluations of BLE periodic advertising energy use.
[10] Bluetooth SIG, LE Audio BIS/BIG informational documents.
[11] Silicon Labs or vendor app notes on periodic sync window and SCA.
