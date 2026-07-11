---
schema_version: '1.0'
id: rfid-vs-nfc-vs-barcode
title: RFID/NFC/条码在IoT识别中的对比选型
layer: 2
content_type: comparison
difficulty: beginner
reading_time: 16
prerequisites:
  - rfid-uhf-passive-tag-iot
tags:
  - RFID
  - NFC
  - 条码
  - 二维码
  - AutoID
  - 选型
  - 对比
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# RFID/NFC/条码在IoT识别中的对比选型

> **难度**：🟢 初级 | **领域**：自动识别技术 | **阅读时间**：约 16 分钟

## 日常类比

管 10 万册书：翻封面看编号像扫条码；拿感应器沿书架走一圈自动“报到”像超高频射频识别（UHF RFID）；手机贴一下借书卡确认身份像近场通信（NFC）。自动识别（AutoID）三大主流各有甜蜜区，选错则成本或能力错配[1][3]。

## 摘要

按距离、速度、成本、容量、环境、安全六维对比一维/二维条码、NFC 与 UHF RFID，并给场景决策树与融合标签边界。单价与速率为量级，**随批量、封装与地区变化**[2][4]。

## 1. 选型维度

| 维度 | 关键问题 |
|------|----------|
| 距离 | 接触、近距还是米级自动感知 |
| 速度 | 逐个还是批量 |
| 标签/读写器成本 | 是否大规模、是否可手机当读写器 |
| 容量 | 仅 ID 还是要富文本 |
| 安全 | 防伪/支付级还是物流级 |
| 环境 | 脏污、金属、液体、遮挡 |

## 2. 技术要点

**条码/二维码**：光学、需可视、通常只读；二维码容量远高于一维，纠错等级可配；智能手机即可读，标签成本极低[3]。

**NFC（13.56 MHz）**：读距通常约 10 cm 内，短距即“有意贴近”的安全特性；读写器模式/点对点/卡模拟；近场数据交换格式（NDEF）；可配合安全元件做支付级场景[2]。

**UHF RFID（约 860–960 MHz）**：米级、批量、无源常见；电子产品代码（EPC）；读写器成本显著高于手机扫码；金属/液体需特殊标签[1][4]。

| 技术 | 距离直觉 | 批量 | 标签成本直觉 | 读写器 |
|------|----------|------|--------------|--------|
| 1D/QR | 近距可视 | 否 | 极低 | 扫描枪/手机 |
| NFC | 约 ≤10 cm | 否 | 低–中 | 手机常见 |
| UHF RFID | 约 1–十余米叙事 | 是 | 低（量大） | 专用，成本高 |

## 3. 六维对比摘要

| 维度 | 条码/QR | NFC | UHF RFID |
|------|---------|-----|----------|
| 速度 | 约 1 个/次 | 单次贴近 | 每秒数百叙事 |
| 容量 | QR 可很大 | 数百字节–数 KB 叙事 | EPC 短 + 可选用户区 |
| 脏污 | 光学易失效 | 射频较稳 | 射频较稳 |
| 金属/液体 | 可视即可 | 需注意 | 常需特殊标签 |
| 安全 | 易复制 | 可强（加密/SE） | Gen2 基础弱，v2 可增强 |
| 系统成本 | 最低起步 | 标签贵于条码 | 读写器与集成为大头 |

人工盘点成本常主导总拥有成本：高频盘点场景下 RFID 初始投资可能被运营节省覆盖——**须用本企业工时与差错率核算**[4][5]。

## 4. 场景与决策

| 场景 | 常见首选 | 理由 |
|------|----------|------|
| 商超收银 | 条码 | 生态与成本 |
| 服装库存/防损 | UHF RFID | 批量与准确率 |
| 门禁/支付 | NFC | 短距+安全 |
| 供应链托盘/箱 | UHF RFID | 吞吐与非可视 |
| 消费品防伪 | NFC（或 Gen2v2） | 手机可验 |
| 图书馆 | HF RFID | 行业惯例与金属架 |

决策树直觉：要批量自动读 → UHF；要强安全贴近 → NFC；要手机零硬件且可视 → QR；其余最低成本 → 一维条码。

融合：UHF+NFC 双频、RFID 面印 QR，覆盖供应链与消费者触点，成本高于单技术但可能低于两套系统。

## 5. 局限、挑战与可改进方向

### 1. “一种技术打天下”

**局限**：用 UHF 做支付级交互或用条码做封闭箱批量盘点都会失败。
**改进**：按距离×批量×安全矩阵选型；复杂链路允许多技术。

### 2. 成本只看标签单价

**局限**：忽略读写器、中间件、流程改造与培训。
**改进**：算三年总拥有成本与人工盘点对比。

### 3. 环境未试读

**局限**：金属货架、液体商品使实验室指标失效。
**改进**：目标物料现场试贴试读再招标。

### 4. 安全预期错位

**局限**：把普通 UHF 标签当防伪；或对 QR 期望不可复制。
**改进**：防伪用加密 NFC/Gen2v2；票务用动态码+服务端校验。

## 6. 实践要点

1. 先写清“谁在什么距离以什么频次读什么对象”，再选技术。
2. 零售存量 POS 常保留条码兼容，RFID 先服务库存。
3. 公开市场“万亿标签”类预测仅作趋势，不作项目承诺[5]。

## 参考文献

[1] Finkenzeller, K., "RFID Handbook," 3rd ed., Wiley, 2010.
[2] NFC Forum, technology overviews, nfc-forum.org.
[3] GS1, "GS1 General Specifications" (barcode/QR related).
[4] AIM Global, Automatic Identification and Data Capture comparison guides.
[5] RAIN RFID Alliance market outlook materials (treat forecasts as non-binding).
[6] ISO/IEC 18000-63 / EPC Gen2 for UHF air interface.
[7] ISO/IEC 14443 / 15693 family notes for HF/NFC adjacency.
[8] QR Code / ISO/IEC 18004 capacity and Reed-Solomon levels.
[9] GS1 EPC Tag Data Standard.
[10] Retail RFID inventory accuracy case literature (study-bound KPIs).
[11] Dual-frequency UHF+NFC tag vendor application notes.
