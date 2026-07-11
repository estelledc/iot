---
schema_version: '1.0'
id: pcb-antenna-design-iot
title: IoT设备PCB板载天线设计
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - chip-antenna-vs-pcb-antenna
  - antenna-impedance-matching-network
  - ble-module-hardware-design
tags:
  - PCB天线
  - IFA
  - PIFA
  - 阻抗匹配
  - 净空区
  - 2.4GHz
  - Sub-GHz
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT设备PCB板载天线设计

> **难度**：🟡 中级 | **领域**：射频与天线 | **关键词**：IFA, PIFA, S11, 净空 | **阅读时间**：约 18 分钟

## 日常类比

搭广播站：买专业天线效果好但贵；把屋顶钢梁弯成合适形状也能辐射——印刷电路板（Printed Circuit Board, PCB）天线同理，铜皮几何即辐射器。物联网（Internet of Things, IoT）省掉天线器件与连接器，也省掉一段馈线损耗，但布局与外壳金属会“改写”谐振[1][4]。

## 摘要

对比倒 F（Inverted-F Antenna, IFA）/平面倒 F（PIFA）、蛇形与环形板载天线，强调地平面、净空、匹配与制造公差。增益与效率为典型量级，须矢量网络分析仪实测[4][5]。

## 1. 为何用板载天线

| 优点 | 代价 |
|------|------|
| 近零天线 BOM | 增益/效率上限通常低于外置 |
| 无连接器损耗 | 对地平面与附近金属极敏感 |
| 供应链简单 | 调谐常需改版或可调匹配 |

## 2. 常见结构

| 类型 | 适用 | 要点 |
|------|------|------|
| IFA/PIFA | 2.4 GHz BLE/Wi-Fi 常用 | 尺寸与性能较均衡[4] |
| 蛇形 | Sub-GHz 或极小空间 | 以效率换尺寸 |
| 环形 | NFC/部分穿戴 | 磁偶极、近场为主 |

四分之一波长单极子在 PCB 上常演化为 IFA 以改善阻抗与高度。地平面是镜像与回流的一部分：缩短或开槽会漂频、掉效率[1][2]。

## 3. 指标、净空与调谐

| 指标 | 常见目标倾向 | 说明 |
|------|--------------|------|
| S11 / 回波损耗 | 工作带内足够深（如 < −10 dB 量级） | 看整机含外壳 |
| VSWR | 与 S11 对应 | 匹配网络可调 |
| 效率/增益 | 板载常低于外置 | 以暗室/OTAbox 为准 |

Keep-out：天线下方/周围禁铺铜与高大元件；塑料外壳相对介电常数会下拉频率，金属件需远离或当接地结构重新设计[4]。预留 π 型匹配；首板必测。蚀刻公差、板材 Dk 公差会漂谐振，匹配网络是量产安全网[5]。

## 4. 局限、挑战与可改进方向

### 1. 整机环境失谐

**局限**：电池、LCD、人手使谐振偏离认证状态。
**改进**：在最终外壳与握持姿态下调匹配；必要时改芯片天线/外置[4][5]。

### 2. 地平面过小

**局限**：Sub-GHz 效率崩溃。
**改进**：加大地；蛇形+匹配；或改外置鞭状[1]。

### 3. 仿真与实测偏差

**局限**：忽略外壳/线缆导致仿真乐观。
**改进**：含介质外壳联合仿真；以 VNA 实测闭环[2]。

### 4. 认证复测成本

**局限**：改天线几何触发射频重测。
**改进**：锁定模组认证天线设计；改匹配尽量在已评估包络内[4]。

## 总结

板载天线省成本，但把射频变成 PCB 与结构问题。IFA 做 2.4 GHz 起点，Sub-GHz 谨慎评估地尺寸；匹配与整机实测不可省。

## 参考文献

[1] Balanis, Antenna Theory.
[2] Wong, Planar Antennas for Wireless Devices.
[3] PIFA for Bluetooth 应用文献（如 Applied Microwave & Wireless 相关）.
[4] Texas Instruments, AN043 2.4 GHz IFA Design Guide.
[5] Johanson Technology, Chip Antenna / IoT 天线设计指南.
[6] IPC 射频 PCB 材料与公差相关实践.
[7] Keysight/R&S 天线 S 参数测量应用笔记.
[8] BLE/Wi-Fi 认证与天线改动政策说明（模块厂商）.
[9] 蛇形天线小型化效率权衡论文.
[10] NFC 环形天线设计应用笔记.
[11] 介质加载与人手效应对终端天线影响研究.
[12] π 型匹配网络设计基础应用笔记.
