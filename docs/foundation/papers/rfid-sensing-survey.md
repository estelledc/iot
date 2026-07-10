---
schema_version: '1.0'
id: rfid-sensing-survey
title: RFID 感知识别技术综述
layer: 1
content_type: survey
difficulty: beginner
reading_time: 20
prerequisites:
  - rf-energy-harvesting-rectenna
  - ble-module-hardware-design
tags:
  - RFID
  - NFC
  - EPC Gen2
  - 反向散射
  - 感知
  - RAIN
  - 物联网
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# RFID 感知识别技术综述

> **难度**：🟢 入门 | **领域**：射频识别 | **关键词**：RFID, NFC, EPC Gen2, 反向散射, 感知 | **阅读时间**：约 20 分钟

## 日常类比

地铁刷卡“嘀”一下、超市防盗门响一声——都是射频识别（Radio Frequency Identification, RFID）。条形码像要你凑近看的名片；RFID 更像物品自己报出身份，甚至无源标签也可由读写器电磁波供能。近场通信（Near Field Communication, NFC）是高频 RFID 的近距、可双向子集，手机最常见[1][8]。

## 摘要

综述标签/读写器/后端组成、频段与供电类型、电子产品编码第 2 代（Electronic Product Code Generation 2, EPC Gen2）要点，以及从“只读 ID”走向相位/接收信号强度指示（Received Signal Strength Indicator, RSSI）感知的路径。出货量、精度与市场份额等为公开报告常见口径，随年份变化，文中作量级表述[2][3][9]。

## 1. 原理与分类

无源标签：读写器辐射能量 → 标签整流供电 → 芯片调制反向散射 → 读写器解调 ID。半有源/有源则带电池，读距与成本上升[1][7]。

| 频段 | 频率量级 | 读距倾向 | 典型用途 |
|------|----------|----------|----------|
| 低频 LF | 约 125–134 kHz | 厘米级 | 动物芯片、门禁 |
| 高频 HF | 13.56 MHz | 分米至约 1 m | NFC、图书、公交 |
| 超高频 UHF | 约 860–960 MHz | 米至十余米 | 物流零售（RAIN） |
| 微波 | 2.45/5.8 GHz 等 | 更远（视系统） | ETC 等 |

| 类型 | 电源 | 成本/寿命倾向 |
|------|------|----------------|
| 无源 | 读写器 | 最低 / 无电池寿命问题 |
| 半有源 | 电池辅助 | 中 / 数年量级 |
| 有源 | 自供电发射 | 高 / 受电池约束 |

## 2. EPC Gen2 与防碰撞

UHF 物流零售主流为 ISO/IEC 18000-63 / EPC Gen2（GS1）。标签存储分保留区、EPC、标签识别号（Tag Identifier, TID）、用户区等。多标签用基于时隙 ALOHA 的 Q 算法调节；理论吞吐有 1/e 量级上限，实际标签/秒强依赖场景密度与读写器实现[6][7]。

| 能力 | Gen2 早期 | Gen2v2 方向 |
|------|-----------|-------------|
| 访问控制 | 口令类 | 更强密码学选项 |
| 认证/加密 | 弱或无 | 挑战响应、AES 等（部署仍分层） |
| 隐私 | Kill 等 | Untraceable 等机制 |

## 3. 从识别到感知

RSSI、相位、多普勒等受距离、姿态、介质影响，可做温度/湿度/应变/粗定位/生命体征等研究与试点；相位对距离敏感（波长约数十厘米量级的 UHF），实验室可报亚毫米运动分辨，商用定位仍常为分米级，需区分论文与落地[4][5][9]。

| 感知类型 | 原理线索 | 落地注意 |
|----------|----------|----------|
| 温湿度等 | 阻抗/天线介电变化 | 标定与漂移 |
| 形变 | 天线几何→频偏 | 安装一致性 |
| 定位 | 相位差/到达角 | 多径与标定 |
| 生命体征 | 胸腔微动调相 | 隐私与法规 |

## 4. 应用与 NFC

零售库存、航空行李、医疗器械清点、产线追溯是 UHF 主战场；公开案例常报库存准确率与盘点时长改善，具体数字因企业而异，宜作方向性参考[2][3]。NFC 强调厘米级、点对点与卡模拟，适合支付、车钥匙配对、防伪触碰；可与超宽带（Ultra-Wideband, UWB）测距组合[10]。

| 维度 | NFC | UHF RFID |
|------|-----|----------|
| 读距 | 约数厘米 | 米级为主 |
| 手机 | 广泛支持 | 需专用读写器 |
| 安全 | 短距+可选加密 | 需额外机制 |
| 密度盘点 | 弱 | 强 |

## 5. 挑战与产业

液体/金属、密集碰撞、定位精度、隐私扫描、环境鲁棒性仍是瓶颈。芯片侧有传感集成与计算型标签；系统侧有机器学习分类与数字孪生接入。市场规模与出货（如年百亿枚量级 UHF 标签）见 RAIN/IDTechEx 等，引用时核对年份[2][3]。

| 层级 | 角色示例 |
|------|----------|
| 芯片 | Impinj、NXP 等 |
| 标签 | Avery 等 inlay |
| 读写器 | Zebra、Impinj 等 |
| 集成 | 行业解决方案商 |

## 6. 局限、挑战与可改进方向

### 1. 把论文精度当成仓库指标

**局限**：相位感知实验室分辨远好于多径仓库的稳定定位。
**改进**：用现场基准测试集；分离“检测微动”与“绝对定位”目标[4][9]。

### 2. 金属液体场景照搬消费标签

**局限**：UHF 在金属/液体上读距崩溃。
**改进**：抗金属天线、安装工艺规范、必要时改 HF/有源[1][7]。

### 3. 安全仍按“能读到 ID 即可”

**局限**：远距离扫描与克隆风险在高价值品上不可接受。
**改进**：启用 Gen2v2 密码学特性、TID 认证、业务层防伪[6][10]。

### 4. 感知标签缺乏长期标定

**局限**：阻抗式传感随老化漂移，无补偿则误报。
**改进**：周期校准、多特征融合、与专用传感器分工[5][9]。

## 总结

RFID 是无源物联网与零售自动化的基础设施；UHF Gen2 负责规模盘点，NFC 负责近距交互，感知是增强而非替代 ID。选型先看介质与密度，再谈算法精度。

## 参考文献

[1] K. Finkenzeller, *RFID Handbook*, Wiley（现行版次）.
[2] RAIN RFID Alliance, Annual Report / 出货统计（核对年份）.
[3] IDTechEx, RFID Forecasts, Players and Opportunities（对应年份）.
[4] J. Wang et al., TagFi 等 RFID 定位研究（ACM MobiCom 等）.
[5] F. Adib et al., 射频生命体征监测相关工作（SIGCOMM 等）.
[6] GS1, EPC Tag Data Standard / Gen2 规范.
[7] Impinj, RAIN RFID Technology Overview.
[8] R. Want, "An Introduction to RFID Technology," *IEEE Pervasive Computing*, 2006.
[9] T. Zhang et al., "A Survey on RFID-based Sensing," *IEEE Communications Surveys & Tutorials*.
[10] NFC Forum Technical Specifications（现行）.
[11] ISO/IEC 18000-63 UHF RFID 空中接口.
[12] EU FMD / 药品与医疗器械唯一标识相关合规背景.
