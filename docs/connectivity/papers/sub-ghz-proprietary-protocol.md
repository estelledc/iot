---
schema_version: '1.0'
id: sub-ghz-proprietary-protocol
title: Sub-GHz私有协议设计与频段规划
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites:
  - sub-ghz-band-comparison
tags:
  - 私有协议
  - Sub-GHz
  - 频段规划
  - FSK
  - 低功耗
  - 帧设计
  - ISM
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# Sub-GHz私有协议设计与频段规划

> **难度**：🟡 中级 | **领域**：私有无线协议 | **阅读时间**：约 14 分钟

## 日常类比

农场喂食器只需偶尔送达“倒 200 克饲料”短指令：不必上美团级调度（标准协议全家桶），可自建最简送餐流程——信封格式（帧）、冷清路线（Sub-GHz 信道）、省电驾驶（休眠策略）。私有协议换来比特级贴合，也换来生态与安全自担[1][2]。

## 摘要

先论证标准协议（LoRaWAN/Zigbee 等）是否真不够；再按目标国法规选频与占空比；调制多用 OOK/FSK/GFSK；帧头压到个位数字节并做鉴权。灵敏度与速率强权衡，**数据手册 dBm 须加实现余量**[3][4]。

## 1. 为何私有 / 为何不

| 动机 | 说明 |
|------|------|
| 开销墙 | 标准入网/保活吃光电池 |
| 确定性 | 需要更严时隙，忌路由发现抖动 |
| 载荷极短 | 标准帧头相对 4 B 数据过重 |
| 算法/成本 | 国密或认证费约束 |

代价：无现成互通、工具链与安全审计自建、人员培训成本。多数情况“标准+配置裁剪”更省[2]。

## 2. 频段规划要点

| 地区 | 常见 Sub-GHz | 法规线索 |
|------|--------------|----------|
| 欧洲 | 433 / 868 MHz 子带 | ETSI EN 300 220，占空比分档 |
| 北美 | 315 / 915 MHz 等 | FCC Part 15，跳频/带宽条款 |
| 中国 | 470–510、微功率段等 | 工信部目录与限制 |
| 日本等 | 920 MHz 附近 | LBT 等 |

欧 868 子带功率与占空比不同（如严格 0.1% 与相对宽松高功率窄带）；美 915 常靠跳频换较高功率、无欧式统一占空比——协议的信道状态机必须按市场分叉[5][6]。

## 3. 调制与帧

| 调制 | 优点 | 代价 |
|------|------|------|
| OOK/ASK | 简单、发射可极省 | 灵敏度/抗扰差 |
| FSK | 成熟、多数芯片支持 | 占带与频偏要调 |
| GFSK | 谱更干净 | 实现稍复杂 |

| 字段 | 作用 |
|------|------|
| Preamble / Sync | 同步与网络识别 |
| Addr / Seq | 寻址与去重 |
| Payload | 业务比特编排 |
| CRC / MIC | 检错与防篡改 |

短包场景优先低速率换链路裕量；安全至少：密钥分发、重放计数、完整性，勿只靠“保密 SyncWord”[4][7]。

## 4. 局限、挑战与可改进方向

### 1. 低估合规

**局限**：实验室能通，认证因占空比/杂散失败。
**改进**：设计初期嵌入法规状态机与预扫描。

### 2. 安全形式化缺失

**局限**：私有“加密”常被重放/克隆。
**改进**：用成熟 AEAD；渗透测试；密钥在安全元件。

### 3. 维护与人才

**局限**：唯一懂协议的人离职即风险。
**改进**：规范文档化、抓包样例、仿真测试套件。

### 4. 共存恶化

**局限**：部署放大后自干扰超预期。
**改进**：跳频/LBT、网关监听、自适应速率与功率。

## 5. 实践要点

1. 写清：日空中时间、最大载荷、是否需下行确认。
2. 芯片选型同时锁定目标国频率表与认证路径。
3. 能用 LoRaWAN Class A 等标准满足则优先标准。

## 参考文献

[1] ETSI EN 300 220, SRD 25 MHz–1 GHz.
[2] LoRa Alliance / CSA materials (when to use standards).
[3] TI / Silicon Labs Sub-GHz transceiver application notes (CC11xx/CC13xx etc.).
[4] Stallings, W., Cryptography and Network Security (embedded crypto hygiene).
[5] FCC Part 15.247 materials.
[6] 中国工信部微功率短距离无线电相关规定（现行文本）.
[7] IEEE 802.15.4 (frame design contrast).
[8] ARIB STD-T108 (Japan 920 MHz context).
[9] Semtech / HopeRF FSK module design guides.
[10] Rappaport, T. S., Wireless Communications (link budget).
[11] NIST lightweight cryptography / AEAD recommendations for constrained devices.
