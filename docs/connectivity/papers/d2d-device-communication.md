---
schema_version: '1.0'
id: d2d-device-communication
title: D2D 设备直连通信
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags:
  - D2D
  - Sidelink
  - ProSe
  - V2X
  - 邻近发现
  - 干扰管理
  - PC5
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# D2D 设备直连通信

> **难度**：🟡 中级 | **领域**：蜂窝旁路通信 | **阅读时间**：约 20 分钟

## 日常类比

同办公室传文件却先上传公司服务器再下载，等于绕路。设备到设备（Device-to-Device, D2D）让邻近终端直传，降低时延并卸载基站。工厂里传感器旁路控制器、车联网（Vehicle-to-Everything, V2X）安全消息走侧行链路（Sidelink），都是同一直觉[1][5]。

## 摘要

本文说明带内复用/覆盖与带外 D2D、邻近发现、资源分配与干扰场景，概述第三代合作伙伴计划（3GPP）邻近服务（Proximity Services, ProSe）与新空口（NR）Sidelink 模式，并讨论中继与能效。时延、可靠性与能耗倍数为标准目标或仿真/试点量级，部署须按频谱与功率约束复核[3][4][6]。

## 1. 频谱与模式

| 类型 | 频谱 | 优点 | 缺点 |
|------|------|------|------|
| 带内 Underlay | 复用蜂窝资源 | 谱效高 | 干扰管理难 |
| 带内 Overlay | 划出专用资源 | 隔离较好 | 占用蜂窝容量 |
| 带外 | 免授权等 | 不影响牌照谱 | 拥挤、难控 |

模式选择通常综合距离、D2D 信干噪比（SINR）、业务可靠性与蜂窝负载：太远或信道差则回落蜂窝中转；蜂窝拥塞且链路够好则直连[1][2]。

## 2. 邻近发现

网络辅助：基站据测量/位置提示可连对端。直接发现：终端广播/查询，类似低功耗蓝牙通告，不依赖覆盖但耗电耗谱。

| 模型 | 含义 | 场景例 |
|------|------|--------|
| Model A（I am here） | 主动通告存在 | 社交/广告 |
| Model B（Who is there?） | 查询特定对象 | V2X、IoT 组 |

发现周期在物联网可放宽到秒级省电，在 V2X 则需更短以跟踪相对运动[3]。

## 3. 干扰与资源

带内常复用**上行**资源：便于功率控制扩展，基站侧干扰处理相对成熟。需同时约束：D2D 发射对基站、蜂窝用户对 D2D 接收等链路[2][7]。

| 方法 | 复杂度倾向 | 适用规模倾向 |
|------|------------|--------------|
| 穷举 | 极高 | 极小 |
| 图着色/启发式 | 中 | 中 |
| 匈牙利等匹配 | 中高 | 中 |
| 分布式博弈/学习 | 训练或迭代成本 | 大 |

中继/多跳可延长覆盖，但时延与可靠性随跳数恶化，工程上常限制跳数[1]。

## 4. V2X 与 NR Sidelink

蜂窝 V2X：Uu 经基站，PC5/Sidelink 直连。NR Sidelink 相对长期演进（LTE）V2X 在时延、可靠性、混合自动重传请求（HARQ）与服务质量（QoS）框架上增强[4][6]。

| 项目 | LTE V2X 倾向 | NR V2X 倾向 |
|------|--------------|-------------|
| 时延 | 数十毫秒量级 | 更低（场景相关） |
| 可靠性目标 | 较低 | 更高 |
| 资源模式 | Mode 3/4 | Mode 1（基站调度）/ Mode 2（感知+预约自主选） |

Mode 2 通过传感窗口排除强占用资源并周期性预约，在无覆盖时仍可工作，但对隐藏节点与高密度仍敏感[6]。

## 5. ProSe 与能效

ProSe 功能实体负责授权与发现参数；终端经 PC5 传数[3]。近距直连缩短路径损耗、变两跳为一跳，每比特能量可显著下降——“十倍到百倍”仅在短距低功率假设下的示意，须用链路预算校准[1][8]。系统级上，近距流量卸载或降低基站负荷，试点增益因地而异，不宜引用单一运营商百分比作全球结论[10]。

## 6. 局限、挑战与可改进方向

### 1. Underlay 干扰难保证蜂窝 SLA

**局限**：D2D 密度一升，蜂窝上行质差投诉增加。
**改进**：严格功率上限与保护资源块；准入控制；优先 Overlay/专用谱给安全业务。

### 2. 发现与直连的隐私/安全

**局限**：广播存在性暴露轨迹；伪造发现消息。
**改进**：匿名标识轮换、相互认证与完整性保护；与证书体系衔接（尤其 V2X）。

### 3. 无覆盖 Mode 2 的资源碰撞

**局限**：高速高密度下感知过时，包碰撞上升。
**改进**：拥塞控制、地理分区资源池、路侧单元辅助。

### 4. IoT 能效 vs 发现开销

**局限**：为维持可发现性周期性发射，抵消直连省电。
**改进**：事件触发发现、网络辅助按需唤醒、固定供电节点做中继。

## 参考文献

[1] A. Asadi, Q. Wang, and V. Mancuso, "A Survey on Device-to-Device Communication in Cellular Networks," IEEE Communications Surveys & Tutorials, 2014.
[2] D. Feng et al., "Device-to-Device Communications Underlaying Cellular Networks," IEEE Trans. Communications, 2013.
[3] 3GPP TS 23.303, "Proximity-based services (ProSe); Stage 2."
[4] 3GPP TS 38.300, "NR; Overall description; Stage-2."
[5] G. Fodor et al., "Design Aspects of Network Assisted Device-to-Device Communications," IEEE Communications Magazine, 2012.
[6] S. A. A. Shah et al., "5G NR V2X Sidelink" 相关综述, IEEE Access, 2021.
[7] Z. Ding / 资源分配类 D2D 综述, IEEE Communications Surveys & Tutorials, 2018.
[8] L. Wei et al., "Enable Device-to-Device Communications Underlaying Cellular Networks," IEEE 相关工作.
[9] L. Liang et al., "Spectrum sharing in vehicular networks based on multi-agent reinforcement learning," IEEE JSAC, 2019.
[10] 运营商/研究机构, "5G D2D / Sidelink" 白皮书与试点报告（区域性数据，慎外推）.
[11] 3GPP TS 36.300, "E-UTRA and E-UTRAN; Overall description"（LTE Sidelink 基础）.
[12] 3GPP TS 38.321 / 38.331, NR MAC/RRC 中 Sidelink 过程相关条款.
