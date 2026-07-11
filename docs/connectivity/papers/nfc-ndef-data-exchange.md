---
schema_version: '1.0'
id: nfc-ndef-data-exchange
title: NFC NDEF数据交换格式与标签类型
layer: 2
content_type: tutorial
difficulty: beginner
reading_time: 18
prerequisites:
  - rfid-vs-nfc-vs-barcode
tags:
  - NFC
  - NDEF
  - 标签类型
  - Type 2
  - 配网
  - URI
  - NTAG
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# NFC NDEF数据交换格式与标签类型

> **难度**：🟢 初级 | **领域**：NFC基础 | **阅读时间**：约 18 分钟

## 日常类比

超市条码用统一规则编码商品信息；近场通信（Near Field Communication, NFC）标签像“可写的数字条码”，手机一碰即可打开链接、配 Wi-Fi 或启动应用。NFC 数据交换格式（NFC Data Exchange Format, NDEF）就是这套“大家都能读懂”的组织规则。

## 摘要

介绍 13.56 MHz NFC 模式、NDEF 消息/记录、常用记录类型与 NFC Forum 标签 Type 1–5，以及配网与 Matter 入网用法。容量、距离与单价随型号与批次变化，**以数据手册为准**[1][3]。

## 1. NFC 要点

| 参数 | 典型值 |
|------|--------|
| 频率 | 13.56 MHz |
| 距离 | 通常数厘米量级（常称 <10 cm） |
| 速率 | 约 106/212/424 kbps（依模式） |
| 相关标准 | ISO/IEC 14443、18092；Forum 规范 |

| 模式 | 角色 | RF 场 | 用途 |
|------|------|-------|------|
| 读写 | 主动读标签 | 设备提供 | URL/配置 |
| 卡模拟 | 设备扮卡 | 读卡器提供 | 支付/门禁 |
| 点对点 | 对等 | 协商 | 设备交换（较少） |

被动标签由读卡器场供电，无需自带电池即可被读[1][5]。

## 2. NDEF 结构

无统一格式时各厂私有布局难互通；NDEF 以消息（Message）含多条记录（Record）。记录含 Flags、Type、Payload；TNF（Type Name Format）解释 Type 字段含义[1][2]。

| TNF（示例） | 含义 | Type 例 |
|-------------|------|---------|
| Well-known | Forum 定义 | `U` URI、`T` Text |
| MIME | 媒体类型 | `text/plain`、Wi-Fi/BLE OOB |
| External | 厂商扩展 | `vendor.com:mytype` |

URI 记录可用前缀码压缩（如 `https://www.`），对仅百字节级用户区很关键。Text 带语言码；Smart Poster 嵌套 URI+标题+动作；MIME/External 承载 Wi-Fi、蓝牙带外（OOB）与自定义配置[2][6]。

## 3. 标签类型选型

| 类型 | 基础 | 用户容量量级 | 特点 |
|------|------|--------------|------|
| Type 1 | ISO 14443A | 很小–约 KB | 较少用 |
| Type 2 | ISO 14443A | 数十–约百字节级 | 常见 NTAG |
| Type 3 | FeliCa 系 | KB 级 | 部分地区常用 |
| Type 4 | ISO 14443 | 更大、可安全 | DESFire 等 |
| Type 5 | ISO 15693 | 可变 | 相对更远读距 |

Type 2（如 NTAG21x）常够存一条 URL 或配网载荷；高安全门禁倾向 Type 4；仓储盘点可看 Type 5。具体字节数、密码与单价查型号手册，勿写死“一元以内”[3]。

内存常见：UID、能力容器（Capability Container, CC）、用户区 TLV（Type-Length-Value）包装 NDEF，以 `FE` 等终止标记结束[1][3]。

## 4. IoT 用法

- **配网**：MIME 存 Wi-Fi 凭证或 BLE OOB，一碰传参。
- **Matter**：标签可携 Setup Payload，类 QR 但免对准摄像头。
- **动态内容**：NTAG I2C 等双接口，MCU 经 I2C 更新 NDEF，手机读到最新传感/状态[3][7]。

## 5. 局限、挑战与可改进方向

### 1. 容量与载荷膨胀

**局限**：短标签塞不下复杂配置或多语言海报。
**改进**：URI 前缀压缩；外链+短 ID；升 Type 4/更大用户区。

### 2. 互操作碎片

**局限**：私有 External 类型手机系统未必识别。
**改进**：优先 Well-known/标准 MIME；App 深链兜底。

### 3. 安全错觉

**局限**：明文 NDEF 可被复制或改写。
**改进**：只放非敏感引导信息；敏感用加密卡/挑战响应；写保护与密码页。

### 4. 环境与读距

**局限**：金属外壳、错位导致读失败。
**改进**：铁氧体与天线布局；验收多姿态读距；关键流程提供 QR 备份。

## 6. 实践要点

1. 先定载荷字节与安全等级，再选 Type/型号。
2. 配网优先标准 Wi-Fi/BLE OOB MIME，少造私有格式。
3. 产线写入后抽检多品牌手机可读性。

## 参考文献

[1] NFC Forum, NFC Data Exchange Format (NDEF) Technical Specification.
[2] NFC Forum, Record Type Definition (RTD) Technical Specification.
[3] NXP, NTAG213/215/216 Type 2 Tag IC datasheets.
[4] NFC Forum, Type 1–5 Tag Operation Specifications.
[5] ISO/IEC 14443 / ISO/IEC 18092 (proximity / NFC interface overview).
[6] Wi-Fi Alliance / Bluetooth SIG materials on NFC handover / OOB pairing payloads.
[7] NXP, NTAG I2C Plus product data (dual-interface + energy harvesting context).
[8] Android Developers, NFC NDEF read/write guides.
[9] Apple, Core NFC documentation.
[10] CSA / Matter commissioning documentation (NFC onboarding option).
[11] ISO/IEC 15693 (vicinity cards; Type 5 context).
[12] NFC Forum, URI Record Type Definition.
