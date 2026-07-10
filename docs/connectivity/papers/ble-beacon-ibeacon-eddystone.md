---
schema_version: '1.0'
id: ble-beacon-ibeacon-eddystone
title: BLE信标iBeacon与Eddystone协议对比
layer: 2
content_type: comparison
difficulty: beginner
reading_time: 18
prerequisites:
  - ble-5-features-coded-phy
  - ble-channel-hopping-interference
tags:
  - iBeacon
  - Eddystone
  - BLE信标
  - RSSI
  - 室内定位
  - 广播
  - 近场感知
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# BLE信标iBeacon与Eddystone协议对比

> **难度**：🟢 初级 | **领域**：BLE广播应用 | **阅读时间**：约 18 分钟

## 日常类比

博物馆展品旁的“隐形导游”：你走近，手机自动弹出介绍。蓝牙低功耗（BLE）信标像灯塔——只广播、不连接；手机像船只，用接收信号强度指示（RSSI）粗估远近[1][2][5]。

## 摘要

对比 Apple iBeacon 与 Google Eddystone 帧格式、平台支持、距离估算与功耗，并强调伪造风险。距离分区与电池年数为经验量级，**室内误差常达米级**[5]。

## 1 信标是什么

纯广播设备周期发广告包，无需配对；一对多、单向、结构简单，纽扣电池可运行数年量级（视间隔与自放电）[3]。

## 2 iBeacon

2013 年 Apple 推出，载荷结构固定：前缀 + 16 字节通用唯一标识符（UUID）+ Major + Minor + 校准发射功率（1 m 处 RSSI）[1]。

| 层级 | 字段 | 用途示例 |
|------|------|----------|
| 组织 | UUID | 连锁品牌 |
| 区域 | Major | 某门店 |
| 节点 | Minor | 店内点位 |

iOS 经 Core Location 原生监控/测距；距离粗分为 Immediate / Near / Far（约 <0.5 m / 0.5–3 m / >3 m 经验带）[1]。

## 3 Eddystone

2015 年 Google 开源（Apache 2.0），多帧类型[2]：

| 帧 | 内容 |
|----|------|
| UID | Namespace + Instance |
| URL | 压缩 URL（物理网络） |
| TLM | 电池电压、温度、广播计数等遥测 |
| EID | 旋转短暂标识，防简单复制 |

URL 前缀/后缀编码节省字节；EID 用共享密钥与 HKDF 类派生，周期 2^K 秒可配[2]。

## 4 对比与选型

| 特性 | iBeacon | Eddystone |
|------|---------|-----------|
| 开放性 | 需遵循 Apple 指引 | 开源规范 |
| 帧类型 | 单一 | 多帧 |
| URL / TLM / EID | 无内置 | 有 |
| iOS | 原生 | 常需第三方 |
| Android | 常需 SDK | Nearby 等曾原生支持（生态有变迁，需核验现行 API） |

决策：偏 iOS 简洁部署 → iBeacon；要 URL/遥测/防伪 → Eddystone；双端均衡 → 双模同时广播[1][2]。

## 5 距离、功耗与部署

路径损耗模型：`RSSI(d) ≈ RSSI(d0) − 10 n log10(d/d0)`，室内 n 约 2–4。实际精度常约 1–3 m，受多径、人体、朝向、同频干扰与 RSSI 抖动（静止也可约数 dB）影响[5]。

| 广告间隔 | 检测延迟 | 相对功耗 |
|----------|----------|----------|
| 约 100 ms | 快 | 高 |
| 约 500–1000 ms | 中 | 常用折中 |
| 约 2 s | 慢 | 更省 |

CR2032 理论寿命可算到十余年，实际含自放电与峰值常约 2–3 年量级[3]。部署：高度约 2.5–3 m、避开金属水体、间距按触发半径规划，并做 RSSI 热力验证。

## 6 安全

iBeacon 标识明文，易被复制欺骗。缓解：Eddystone-EID、服务端校验、多信标指纹、时间窗；支付/门禁勿单靠距离[2][4]。

## 7 局限、挑战与可改进方向

### 1. 测距物理上限

**局限**：RSSI 测距米级误差，难做厘米级导览[5]。
**改进**：指纹/融合超宽带（UWB）；业务用“进区”而非精确米数。

### 2. Eddystone 生态收缩

**局限**：Google 物理网络等服务调整后，URL 免 App 路径变弱[2]。
**改进**：自建解析后端；关键体验仍引导轻量 App。

### 3. 伪造与隐私

**局限**：明文 UUID 可被重放；持续扫描损隐私[4]。
**改进**：EID + 后端；系统权限最小化与用户告知。

### 4. 电池与间隔拍脑袋

**局限**：100 ms 间隔耗尽电池却无业务收益[3]。
**改进**：按检测延迟预算选型；现场测平均电流。

## 参考文献

[1] Apple, iBeacon / Accessory 与 Core Location 文档.
[2] Google, Eddystone Protocol Specification (GitHub).
[3] Bluetooth SIG, Bluetooth Core Specification（Advertising）.
[4] Nordic Semiconductor, nRF5 SDK Beacon Examples.
[5] R. Faragher and R. Harle, Location Fingerprinting with BLE Beacons, IEEE JSAC, 2015.
[6] Bluetooth SIG, Bluetooth Core Specification Supplement（AD types）.
[7] Apple, Getting Started with iBeacon.
[8] Radius Networks / 开源双模信标实践文档.
[9] Android Nearby / BLE 扫描 API 现行文档.
[10] 电池寿命与广告间隔应用笔记（Nordic/Dialog 等）.
[11] GDPR/隐私与持续蓝牙扫描合规讨论（部署参考）.
