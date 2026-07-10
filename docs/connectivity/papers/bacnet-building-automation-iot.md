---
schema_version: '1.0'
id: bacnet-building-automation-iot
title: BACnet楼宇自动化IoT通信协议
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - knx-smart-building-protocol
  - dali-lighting-control-iot
tags:
  - BACnet
  - 楼宇自动化
  - HVAC
  - BACnet/SC
  - 对象模型
  - 智慧楼宇
  - IoT集成
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# BACnet楼宇自动化IoT通信协议

> **难度**：🟡 中级 | **领域**：楼宇自动化 | **阅读时间**：约 20 分钟

## 日常类比

办公楼里空调、灯光、电梯、门禁像说不同方言的邻居。楼宇自动化与控制网络（Building Automation and Control Networks, BACnet）是这栋楼的“通用语”：不管哪家暖通空调（Heating, Ventilation, and Air Conditioning, HVAC）控制器，只要讲 BACnet，就能用统一对象与服务交换温度、设定值与报警[1][2]。

## 摘要

概述美国采暖制冷与空调工程师学会（ASHRAE）标准 135 / ISO 16484-5 的对象模型、服务、网络层（含安全连接 BACnet/SC），以及到消息队列遥测传输（MQTT）/云的集成路径。文中节能百分比为案例示意，**非保证收益**[1][4][5]。

## 1 定位与覆盖

1995 年 ASHRAE 135 首发，2003 年入 ISO 16484-5，商业楼控主流协议之一。目标：多厂商互操作、覆盖 HVAC/照明/门禁/消防/电梯/能源、匹配建筑数十年寿命[1][2]。

| 子系统 | 典型对象 | 应用 |
|--------|----------|------|
| HVAC | 模拟输入/输出 | 送风温度、阀门 |
| 照明 | 二进制输出、调度 | 开关、场景 |
| 门禁 | 凭证、门锁 | 刷卡 |
| 消防 | 报警对象 | 烟感联动 |
| 能源 | 累积器 | 电/水/气表 |

## 2 对象模型与优先级

一切皆对象（Object）+ 属性（Property），如 Analog Input 的 Present_Value、Units、Status_Flags、高低限。常用：AI/AO/AV、BI/BO/BV、多状态、Schedule、Calendar、Trend Log、Loop、Notification Class、Event Enrollment[1]。

模拟/二进制输出有 16 级优先级数组：生命安全（消防）高于操作员覆写，高于默认自动控制——多源写入时执行最高有效优先级[1][3]。

## 3 服务与网络层

发现：Who-Is / I-Am。读写：ReadProperty / WriteProperty / ReadPropertyMultiple。变化值（Change of Value, COV）订阅：超增量才通知，契合事件驱动物联网（IoT）[1]。

| 网络层 | 要点 |
|--------|------|
| BACnet/IP | UDP 47808（0xBAC0），与 IT 网兼容 |
| BBMD | 跨子网广播管理，转发 Who-Is |
| MS/TP | RS-485、令牌、约 9600–115200 bps、最多约 127 节点、约 1.2 km 量级 |
| BACnet/SC | WebSocket + 强制传输层安全（TLS）1.3 + X.509，Hub-Spoke，云/NAT 友好 |

典型分层：云/远程 ←SC— 工作站 ←IP— 楼层直接数字控制（DDC）←MS/TP— 末端[4]。

## 4 IoT 集成与协议对比

路径：BACnet/SC 直连保语义；BACnet/MQTT 网关把 COV 映到主题；REST 封装点位。Trend Log 可断网缓存后补传时序库。

| 协议 | 优势领域 | 特点 |
|------|----------|------|
| BACnet | HVAC、综合管理 | 开放对象模型 |
| KNX | 房间照明/遮阳 | 欧洲分布式 |
| Modbus | 仪表监测 | 极简、无标准语义 |
| DALI | 照明专用 | 照明总线 |

常见组合：KNX 管房间，BACnet 管中央 HVAC 与能源[3]。

## 5 安全与案例要点

传统 BACnet/IP、MS/TP 几乎无认证/加密（历史假设物理隔离）。BACnet/SC 用证书 + TLS；即便不用 SC，也应虚拟局域网（VLAN）隔离、限制 47808、虚拟专用网（VPN）远程、异常流量监测[4]。

案例示意：多层办公楼 AHU（IP）+ 大量变风量（VAV，MS/TP）+ SC 上云；数据驱动优化宣称风机/综合能效约一成至两成量级改善——**依赖气候、运营与控制策略**[5]。

## 6 局限、挑战与可改进方向

### 1. 遗留明文平面

**局限**：大量在役 IP/MS/TP 无加密，IT 互通后风险暴露[4]。
**改进**：分区隔离 + 优先新项目上 SC；远程只走 VPN/SC Hub。

### 2. 语义到云的阻抗

**局限**：MQTT/REST 网关易丢优先级、报警确认等语义[1]。
**改进**：保留对象标识与优先级元数据；关键写回仍走原生 WriteProperty。

### 3. BBMD 与跨网运维

**局限**：广播发现跨子网配置易错，导致“看不见设备”[1]。
**改进**：标准化 BBMD 表与变更流程；用 SC 减少广播依赖。

### 4. 节能数字被夸大

**局限**：把单楼试点百分比写成产品保证[5]。
**改进**：以 kWh 基线与对照季测量；AI 写设定值须操作员确认与回滚。

## 参考文献

[1] ASHRAE, ANSI/ASHRAE Standard 135, BACnet.
[2] ISO 16484-5, Building automation and control systems — Part 5.
[3] H. M. Newman, *BACnet: The Global Standard for Building Automation and Control Networks*, Momentum Press.
[4] ASHRAE, Addendum bj / BACnet Secure Connect 相关修订.
[5] BACnet International, BTL Listing Program.
[6] BACnet International, 互操作与测试指南.
[7] KNX Association, KNX 标准概览（对比参考）.
[8] OPC Foundation, OPC UA for BACnet 伴随规范进展.
[9] NIST / 楼宇网络安全实践指南（IT/OT 隔离）.
[10] Modbus Organization, Modbus Application Protocol（对比参考）.
[11] DALI Alliance, DALI 规范概览（照明对比）.
