---
schema_version: '1.0'
id: wifi-power-save-dtim-twt
title: WiFi省电机制DTIM/TWT在IoT中的配置
layer: 2
content_type: tutorial
difficulty: intermediate
reading_time: 14
prerequisites:
  - wifi-6-ofdma-mu-mimo-iot
tags:
  - DTIM
  - TWT
  - PSM
  - 省电
  - Beacon
  - IoT功耗
  - 802.11ax
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# WiFi省电机制DTIM/TWT在IoT中的配置

> **难度**：🟡 中级 | **领域**：WiFi功耗管理 | **阅读时间**：约 14 分钟

## 日常类比

保安通宵盯屏（Always On）最耗神；设闹钟隔一阵看一眼（DTIM/传统 PSM）能睡但不能睡死；跟物业约好整点才喊你（TWT）则可大块休眠。电池 IoT 的核心是：**尽量缩短射频处于 RX/TX 的时间**[1][4]。

## 摘要

覆盖 Legacy PSM、DTIM（Delivery Traffic Indication Map）与 Wi‑Fi 6 TWT（Target Wake Time）在 IoT 上的配置权衡。电流与寿命估算为示意，**以模组手册与库仑计实测为准**[5][6]。

## 1. 功耗量级认知

| 状态（ESP32 类叙事） | 电流量级 | 含义 |
|----------------------|----------|------|
| TX | 百 mA 级 | PA 开 |
| RX | 近百 mA 级 | 持续听 |
| Light / Deep sleep | mA～μA 级 | CPU/射频大多关 |

省电重点常不是“少发几个字节”，而是减少空闲监听与无意义唤醒[5]。

## 2. Legacy PSM 与 DTIM

STA 置 PM=1 后，AP 缓存下行；STA 在 Beacon 周期醒来看 TIM。DTIM 每隔 N 个 Beacon 出现，常指示组播/广播是否有缓存。DTIM 间隔大 → 睡得久、组播更迟；间隔小 → 更及时、更耗电[1][2]。

| 参数 | 调大 | 调小 |
|------|------|------|
| Beacon interval | 更省电、发现/同步变慢 | 相反 |
| DTIM period | 更省电、下行/组播延迟升 | 相反 |

PS‑Poll 逐帧取缓存较慢；现代实现多用 U‑APSD 等一次取多帧——以芯片与 AP 能力为准[2]。

## 3. TWT（802.11ax）

TWT 让 STA 与 AP **协商唤醒日程**，非 TWT 窗内可更深睡，减少争用。Individual TWT 一对一约定；Broadcast TWT 共享日程。对周期上报传感器极友好；对突发下行（云推送）要设计缓冲与可接受延迟[3][4]。

| 模式 | 适合 | 注意 |
|------|------|------|
| 仅 DTIM PSM | 广兼容旧 AP | 仍可能频繁听 Beacon |
| TWT | Wi‑Fi 6 AP + 6 终端 | 协商失败需回退 |
| 业务侧深睡+短连 | 极低占空比传感 | 每次重关联成本 |

## 4. 配置实践提纲

1. 算电池：容量 / 目标小时 → 允许平均电流；反推每小时最大活跃时间。
2. AP 侧：Beacon/DTIM 与 IoT SSID 策略一致；避免对 IoT SSID 过密组播。
3. 终端：能 TWT 则协商；否则 PSM + 合理 listen interval；应用层合并上报。
4. 验证：电流探头看唤醒尖峰；抓包看是否按约定窗通信[6][7]。

## 5. 局限、挑战与可改进方向

### 1. 延迟与省电对立

**局限**：DTIM/TWT 间隔大则云到端命令变慢。
**改进**：按 SLA 分档 SSID；紧急命令用唤醒销/第二射频（如 BLE）。

### 2. AP 兼容与协商失败

**局限**：宣称 Wi‑Fi 6 但 TWT 行为不完整。
**改进**：入网测试矩阵；失败自动回退 PSM 并打点告警。

### 3. 组播/广播强迫醒

**局限**：mdns/发现风暴在 DTIM 拉高唤醒。
**改进**：抑制无用组播；IoT VLAN；单播化管理。

### 4. 时钟漂移与窗错过

**局限**：廉价晶振导致 TWT 窗对不齐，空醒或丢下行。
**改进**：留 guard time；周期重协商；温度补偿策略。

## 6. 实践要点

1. 先定最大可接受下行延迟，再定 DTIM/TWT。
2. 量产前用真实 AP 固件做 48h 电流曲线，而不是只看数据手册。
3. 文档化回退路径：TWT → PSM → 短连深睡。

## 参考文献

[1] IEEE 802.11 — Power management / TIM / DTIM clauses.
[2] IEEE 802.11 — PS-Poll, U-APSD related power save mechanisms.
[3] IEEE Std 802.11ax — Target Wake Time.
[4] Wi-Fi Alliance, Wi-Fi 6 features overview (TWT for IoT narratives).
[5] Espressif ESP32 power management / current consumption tables.
[6] Vendor application notes on measuring Wi-Fi sleep current.
[7] AP vendor guides for Beacon interval and DTIM tuning.
[8] Academic / industry studies on DTIM vs battery life tradeoffs.
[9] Broadcast/multicast impact on Wi-Fi power save clients.
[10] TWT negotiation failure and fallback case studies (anecdotal).
[11] IoT design guides combining application duty-cycling with 802.11 PSM.
