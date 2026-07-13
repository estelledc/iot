---
schema_version: '1.0'
id: rf-filter-saw-baw-iot
title: SAW/BAW射频滤波器在IoT频段选择中的应用
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites:
  - rf-front-end-lna-pa-design
  - antenna-impedance-matching-network
tags:
  - SAW
  - BAW
  - 射频滤波器
  - 共存
  - Wi-Fi
  - LTE
  - IoT前端
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# SAW/BAW射频滤波器在IoT频段选择中的应用

> **难度**：🔴 高级 | **领域**：射频滤波器 | **关键词**：SAW, BAW, FBAR, 插入损耗, 共存 | **阅读时间**：约 18 分钟

## 日常类比

嘈杂音乐节里打电话：你只想听对方说话（目标频段），周围歌声与喊叫是干扰。耳朵与大脑做频率选择；干扰越近，越需要高品质因数（Quality factor, Q）的“耳朵”。声表面波（Surface Acoustic Wave, SAW）像水面涟漪，体声波（Bulk Acoustic Wave, BAW）像深井回声——用声学谐振实现电学难及的选择性。Wi-Fi、蓝牙低功耗（Bluetooth Low Energy, BLE）、长期演进（Long Term Evolution, LTE）挤在同一块板时，没有合适滤波器就会互相“串门”[1][5]。

## 摘要

对比 LC / 陶瓷 / SAW / BAW（含薄膜体声波谐振器 FBAR）在物联网（Internet of Things, IoT）频段的定位，梳理插入损耗、抑制、双工器与印刷电路板（Printed Circuit Board, PCB）布局要点。文中指标与价格为公开资料常见量级，选型以现行数据手册与实测为准[2][4][7]。

## 1. 为何需要射频滤波

多无线共存时，发射带外噪声、谐波与互调会落入邻系统接收带，轻则灵敏度下降，重则低噪声放大器（Low Noise Amplifier, LNA）阻塞。法规（如联邦通信委员会 FCC Part 15、欧洲电信标准协会 ETSI EN 300 328、第三代合作伙伴计划 3GPP 射频规范）对杂散与带外发射有硬限，滤波器是合规手段之一[3][6]。

| 类型 | 频率范围（量级） | Q（量级） | 插入损耗（量级） | 尺寸/成本倾向 |
|------|------------------|----------|------------------|---------------|
| LC | 直流至约数 GHz | 十余至数十 | 约 1–3 dB | 大 / 最低 |
| 陶瓷 | 约 0.5–6 GHz | 数十至数百 | 约 1–2 dB | 中 / 低 |
| SAW | 约 0.1–2.7 GHz | 数百至数千 | 约 1–3 dB | 小 / 中 |
| BAW/FBAR | 约 1.5–6 GHz | 更高 | 约 1–2.5 dB | 小 / 高 |

选型粗规则：亚百 MHz 偏 LC；约 0.1–2.5 GHz 且成本敏感偏 SAW；约 1.5–6 GHz 且要高选择性偏 BAW；宽带低成本可看陶瓷[1][2]。

## 2. SAW 原理与特性

叉指换能器（Interdigital Transducer, IDT）把电信号经压电效应变为声表面波，再逆变换回电信号；中心频率大致由声速与指条间距决定。指条对数增多通常收窄带宽、提高选择性，但插入损耗往往上升[1]。

| 维度 | SAW 常见倾向 |
|------|----------------|
| 频率上限 | 约 2.7 GHz 量级 |
| 功率承受 | 往往低于约 +24 dBm 量级 |
| 温度系数 | 约数十 ppm/°C 量级（负温漂常见） |
| 成本 | 相对 BAW 更低 |

## 3. BAW/FBAR 原理与特性

BAW 利用压电薄膜厚度方向驻波；频率由声速与膜厚决定。薄膜体声波谐振器（Film Bulk Acoustic Resonator, FBAR）多用空气桥获得高 Q；固态装配谐振器（Solidly Mounted Resonator, SMR）用布拉格反射器，机械更稳、Q 略折中[2][5]。

| 参数 | SAW | BAW/FBAR |
|------|-----|----------|
| 频率 | 约 0.1–2.7 GHz | 约 1.5–6 GHz |
| Q / 近端抑制 | 高 | 通常更高 |
| 功率 / 温漂 | 较弱 / 温漂更大 | 更强 / 温漂更小 |
| 成本与供应 | 更广、更便宜 | 更高；厂商更集中 |

粗判：低于约 1.5 GHz 优先 SAW；约 1.5–2.7 GHz 看成本与近端抑制；更高频或高功率/高温偏 BAW[2][7]。

## 4. 关键指标

插入损耗（Insertion Loss, IL）在接收链直接恶化噪声系数（Noise Figure, NF），在发射链直接吃掉输出功率。形状因子（如 20 dB 带宽与 3 dB 带宽之比）越小选择性越好。近端抑制最难做；群时延波动过大可导致宽带调制失真，Wi-Fi/LTE 对通带群时延波动常有数十纳秒量级约束——以标准与芯片手册为准[3][6]。

| 指标 | 含义 | 设计注意 |
|------|------|----------|
| IL | 通带衰减 | 与 NF / 链路预算联动 |
| 抑制 | 带外衰减 | 近端最难，决定共存能否成立 |
| 群时延 | 相位斜率 | 宽带调制敏感 |
| 功率承受 | 可承受入射功率 | 靠近功率放大器（Power Amplifier, PA）时必查 |

## 5. IoT 频段与共存

2.4 GHz 上 Wi-Fi 与 BLE 频谱重叠，滤波器无法“切开”二者，实际多靠时分与协议共存；滤波器更多用于谐波抑制与带外保护。Sub-GHz（如约 470/868/915 MHz）常用 SAW 做发射谐波与接收邻带抑制。频分双工（Frequency Division Duplex, FDD）LTE 需双工器；时分双工（Time Division Duplex, TDD）如 B41 与 2.4 GHz Wi-Fi 间隔很近时，往往需要 BAW 才能提供足够近端抑制[5][6]。

| 场景 | 滤波思路 |
|------|----------|
| Wi-Fi + BLE | 时分为主；滤波辅助谐波/带外 |
| Sub-GHz LoRa 等 | SAW 带通常见 |
| LTE FDD | SAW/BAW 双工器 |
| Wi-Fi + LTE B41 | 近端抑制优先 BAW / 多工器 |

## 6. 双工器、多工器与链路位置

双工器 = 发射滤波 + 接收滤波 + 匹配，发射–接收隔离常需数十 dB 量级。多工器把多通带组合，使各口在其他通带呈高阻抗。接收链把带通滤波器（Band-Pass Filter, BPF）放在 LNA 前可保护过载，但 IL 直接进 NF；放在 LNA 后对 NF 更友好但 LNA 暴露于强干扰——IoT 干扰不可控时多选“先滤波”[4][8]。

| 链路位置 | 优点 | 代价 |
|----------|------|------|
| 天线→BPF→LNA | 保护 LNA | NF 恶化约等于 IL |
| 天线→LNA→BPF | NF 更优 | 强干扰易过载 |
| PA→BPF/LPF→天线 | 抑谐波与杂散 | 插损吃功率 |

## 7. 产品与 PCB 布局

公开目录中常见 SAW（如村田等）与 BAW（如 Qorvo 等）器件；指标以数据手册为准，文中型号仅作检索线索[4][7]。布局要点：靠近天线或 PA 输出；输入输出最短且避免平行直通；器件下方地完整；接地焊盘多过孔；远离板边与电源噪声路径。接地不良可使 IL 与抑制明显恶化——须用网络分析仪在板实测[8][9]。

| 常见错误 | 后果倾向 | 处理 |
|----------|----------|------|
| 输入输出过近 | 直通耦合、抑制塌 | 分侧引出 + 地屏蔽 |
| 缺接地过孔 | IL↑、抑制↓ | 每接地焊盘多过孔 |
| 贴板边 | 边缘场改变响应 | 留足边距 |
| 电源穿下方 | 噪声耦合 | 绕行 |

## 8. 局限、挑战与可改进方向

### 1. 重叠频段无法靠滤波分离

**局限**：Wi-Fi 与 BLE 同处 2.4 GHz，SAW/BAW 无法按协议切开。
**改进**：协议/时分共存；系统级调度与实测灵敏度恶化预算[5][6]。

### 2. 近端抑制与成本冲突

**局限**：LTE B41 与 Wi-Fi 间隔很近时 SAW 往往不够，BAW/多工器成本与供应集中。
**改进**：早期做频谱冲突矩阵；关键口用 BAW；非关键口降规格[2][7]。

### 3. 在板性能偏离数据手册

**局限**：布局、匹配与壳体使 IL/抑制偏离手册数 dB 量级并不罕见。
**改进**：严格参考设计；矢量网络分析仪（Vector Network Analyzer, VNA）在板校准；系统共存联测[8][9]。

### 4. 温度与功率降额

**局限**：SAW 温漂与功率上限在高温/高占空比下更紧。
**改进**：高温场景优先 BAW；按峰值功率与壳温降额[1][2]。

## 总结

IoT 多无线设备的滤波器选型是频谱冲突、NF、功率与成本的联合优化：低频/成本敏感看 SAW，高频/近端/高功率看 BAW，重叠频段靠时分而非滤波。布局与在板实测决定最终能否过共存与法规。

## 参考文献

[1] K. Y. Hashimoto, *Surface Acoustic Wave Devices in Telecommunications*. Springer, 2000.
[2] R. Ruby, "A Snapshot in Time: The Future in Filters for Cell Phones," *IEEE Microwave Magazine*, 2015.
[3] ETSI EN 300 328（现行版本），2.4 GHz 宽带传输系统.
[4] Murata, SAW Filter Application Manual / 相关数据手册.
[5] Qorvo, BAW Filter Technology for Carrier Aggregation and Coexistence（白皮书）.
[6] 3GPP TS 36.101 / 相关射频发射与接收要求（现行版本）.
[7] Broadcom / Qorvo / TDK 等 BAW/FBAR 产品与应用说明.
[8] Skyworks, 前端模组与滤波器参考设计说明.
[9] Keysight / R&S, 滤波器与共存测试应用笔记（VNA、杂散）.
[10] FCC Part 15 与对应地区杂散/带外发射要求概览.
[11] IEEE 802.11 / Bluetooth Core Spec 共存与频谱占用背景.
[12] GSMA / 运营商共存测试实践综述（网关类设备）.
