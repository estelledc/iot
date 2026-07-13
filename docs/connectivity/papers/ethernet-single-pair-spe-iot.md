---
schema_version: '1.0'
id: ethernet-single-pair-spe-iot
title: 单对以太网 SPE 在 IoT 边缘连接中的应用
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - hart-protocol-4-20ma-digital
  - ethernet-industrial-iot-tsn
tags:
  - SPE
  - 10BASE-T1L
  - PoDL
  - Ethernet-APL
  - 单对以太网
  - 过程自动化
  - 现场连接
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 单对以太网 SPE 在 IoT 边缘连接中的应用

> **难度**：🟡 中级 | **领域**：工业以太网演进、边缘连接 | **阅读时间**：约 20 分钟

## 日常类比

自来水主管用粗管，到水龙头用细管就够。传统四对以太网像消防水管接花洒——对办公室合适，对每个小传感器过重。单对以太网（Single Pair Ethernet, SPE）用一对双绞线传数据，并可经数据线供电（Power over Data Line, PoDL）同缆供电，专攻工厂/楼宇“最后一公里”。距离与功率等级以标准与线规为准，**改造 ROI 须按本厂重算**[1][2]。

## 摘要

对比现场模拟/总线与传统以太的缺口，梳理 10BASE-T1L / 100BASE-T1 / 1000BASE-T1，说明 PoDL、连接器与 Ethernet-APL（Advanced Physical Layer）在防爆过程工业中的角色，并给出迁移注意点[1][4]。

## 1 为何需要 SPE

| 技术 | 带宽倾向 | 距离倾向 | 供电 | 诊断 |
|------|----------|----------|------|------|
| 4–20 mA | 单模拟量 | 可达 km 级 | 回路 | 弱 |
| HART | kbps 量级 | 长 | 回路 | 有限 |
| PROFIBUS PA | 数十 kbps | 长 | 总线 | 中 |
| 传统以太 | 100 Mbps+ | 常～100 m | PoE | 强 |
| 10BASE-T1L | 10 Mbps | 可达～1000 m | PoDL | 以太级 |

SPE 填补“远距 + IP 可达 + 细缆”空白；10 Mbps 对多数传感/执行器遥测足够，对原始视频等仍可能不够。

## 2 物理层标准族

| 标准 | 速率 | 距离量级 | 典型场景 |
|------|------|----------|----------|
| 10BASE-T1L (802.3cg) | 10 Mbps 全双工 | 最长约 1000 m | 过程/建筑/基建传感 |
| 100BASE-T1 (802.3bw) | 100 Mbps | 约 15 m | 车载等短距 |
| 1000BASE-T1 (802.3bp) | 1 Gbps | 约 15 m（屏蔽可更长） | 车载高速 |

IoT 边缘长距核心是 **10BASE-T1L**；车载短距高速看 T1/T1 千兆。本质安全与分区安装需结合 APL 工程指南，而非只看 PHY 数据手册[4]。

## 3 PoDL 与布线

PoDL 在同一对线上供电，等级（Class）覆盖从亚瓦级传感器到更高功率摄像头/网关——**具体瓦数、电压以 IEEE 与器件选型表为准**，下表仅示意量级[1]：

| 应用倾向 | 功率量级 | 说明 |
|----------|----------|------|
| 简单传感 | 亚瓦～数瓦 | 低电压类 |
| 智能仪表/阀门 | 数瓦～十余瓦 | 中功率类 |
| 摄像头/网关 | 可达更高 | 需匹配线损与温升 |

相对四对 Cat5e：单对外径更细、铜材更少、连接器更小（IEC 63171 等 SPE 连接器族）；具体“省 50% 槽位”类营销数字随线规变化，布线设计以厂商与标准电缆规格为准[2]。

| 项目 | 四对以太倾向 | SPE 倾向 |
|------|--------------|----------|
| 线对 | 4 | 1 |
| 连接器 | RJ45 常见 | 微型 SPE |
| 长距现场 | 弱 | 10BASE-T1L 强 |
| 协议 | IP 原生 | IP 原生 |

## 4 Ethernet-APL

APL 在 10BASE-T1L 上叠加过程工业工程约定：拓扑（干线/支线）、本安与电源开关、诊断与互操作配置文件，使防爆区仪表可走以太网语义而无需 4–20 mA 网关丛林[4]。迁移常经代理/网关并存旧 HART/现场总线，分步替换仪表。

## 5 应用与迁移

| 领域 | 价值点 |
|------|--------|
| 过程自动化 | 多参数 + 远程固件/诊断 |
| 建筑自动化 | 细缆穿管、总线供电传感 |
| 基建监测 | 隧道/桥梁长距 IP |
| 智能制造 | 到边缘仪表的统一 IP |

迁移：先骨干 SPE/APL 交换机 → 关键仪表换型 → 保留模拟回路作安全相关冗余直至认证完成。芯片生态（ADI、TI 等 PHY/MAC-PHY）已可用，仍需 EMC、浪涌与本安体系工程[3][5]。

## 6 局限、挑战与可改进方向

### 1. 生态与技能断层

**局限**：仪表、施工队仍熟悉 4–20 mA；SPE/APL 工具链与备件初期贵[2][4]。
**改进**：试点一条产线；培训按 APL 工程指南；合同绑定互操作测试。

### 2. 功率与线损边界

**局限**：长距大功率同时要本安时，可用功率急剧下降。
**改进**：按最坏线阻与分区算功率预算；高耗设备靠近交换机或本地供电。

### 3. 带宽预期管理

**局限**：把 SPE 当成“万兆到传感器”，10BASE-T1L 撑不起无压缩视频洪流。
**改进**：边缘聚合/压缩；视频走光纤或传统多对以太。

### 4. 混布干扰与接地

**局限**：与大功率动力电缆并行、错误屏蔽接地导致误码。
**改进**：遵循分隔与接地规范；链路质量（SQI 等）纳入巡检。

## 7 总结

SPE（尤其 10BASE-T1L + PoDL + APL）把 IP 与供电延伸到传统现场总线领地。成功关键是工程规范（本安、功率、EMC）与分步迁移，而不是只换 PHY。

## 参考文献

[1] IEEE Std 802.3cg-2019, 10 Mb/s single-pair Ethernet and associated power delivery.
[2] SPE Industrial Partner Network, Single Pair Ethernet technology overviews.
[3] Analog Devices / Texas Instruments 10BASE-T1L PHY 与 MAC-PHY 技术手册.
[4] Ethernet-APL Engineering Guideline (PI 等联合发布).
[5] IEEE 802.3bw / 802.3bp, 100BASE-T1 / 1000BASE-T1.
[6] IEC 63171 SPE 连接器相关标准.
[7] IEEE 802.3bu PoDL 相关条款与修订.
[8] HART / 4–20 mA 迁移到以太网的产业白皮书.
[9] ODVA / PI / FieldComm Group 关于 APL 互操作材料.
[10] 车载 SPE 应用与工业长距 SPE 对比综述.
[11] 本安与 Zone 安装相关 IEC 标准（与 APL 联读）.
[12] 水处理/过程工厂 SPE 试点案例公开报告（引用时核对边界条件）.
