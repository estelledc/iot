---
schema_version: '1.0'
id: fog-computing-architecture
title: 雾计算：云与端之间的多层计算架构
layer: 4
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - edge-computing-survey
  - mec-5g-integration
tags:
- 雾计算
- OpenFog
- IEEE 1934
- 多层架构
- 云边端协同
- 边缘计算
- Cloud-to-Thing
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 雾计算：云与端之间的多层计算架构

> **难度**：🟠 进阶 | **领域**：边缘/雾架构、云边端协同 | **阅读时间**：约 22 分钟

## 日常类比

把计算系统比作城市供水：云计算是远方水库（容量大但远），边缘计算是楼顶水箱（近但容量小），雾计算则是水库到楼宇之间的管网、加压站与净水站——多级处理、逐层过滤。传感器读数像原水，不必整桶运到水库；在中间站先沉淀、再过滤，云端只收摘要。

## 摘要

雾计算（Fog Computing）由思科（Cisco）于 2012 年提出，强调从云到物（Cloud-to-Thing）连续体上的多层计算，而非仅“最后一跳”[1][2]。本文厘清雾/边/云边界，解读 OpenFog / IEEE 1934-2018 八大支柱与功能平面，并以视频监控、工业物联网（Industrial Internet of Things, IIoT）说明逐层提炼；延迟与带宽数字为文献与部署经验的**量级示意**，现场须实测[4][5]。

## 1 起源与定义

### 1.1 命名

Cisco 的 Flavio Bonomi 等人用“雾”比喻比云更靠近地面的水汽——计算也应分布在网络中间层，而非只在远端数据中心[1]。

### 1.2 正式定义

Cisco 早期定义：在终端与传统云数据中心之间提供计算、存储与网络服务的高度虚拟化平台，且不排除在网络边缘设备上运行[1]。

IEEE 1934-2018（采纳 OpenFog 参考架构）给出规范表述：雾计算是一种系统级水平架构，在 Cloud-to-Thing 连续体中分配计算、存储、控制与网络功能，使之更靠近用户[2][3]。

要点：

- **系统级**：完整架构，而非单点技术
- **水平架构**：同层节点可横向协同，不只有垂直上传/下发
- **连续体**：云到端是光谱，不是离散两端

### 1.3 演进简表

| 时间 | 事件 | 意义 |
|------|------|------|
| 2012 | Cisco 提出 Fog Computing | 奠基愿景[1] |
| 2015 | OpenFog Consortium 成立 | 产业标准化推动 |
| 2017 | OpenFog 参考架构发布 | 首份全面参考架构[3] |
| 2018 | IEEE 1934-2018 | 雾计算 IEEE 标准[2] |
| 2019 | OpenFog 并入工业互联网联盟（Industrial Internet Consortium, IIC） | 与工业互联网融合 |
| 2020 以降 | 与边缘计算术语逐步混用 | 多层理念被边缘叙事吸收[5][9] |

## 2 雾 vs 边 vs 云

### 2.1 边界

| 维度 | 云计算 | 雾计算 | 边缘计算 |
|------|--------|--------|----------|
| 焦点 | 集中式数据中心 | 云–端之间多层中间节点 | 靠近数据源的最后一跳/设备侧 |
| 到用户距离 | 远（跨区域） | 中（局域网–城域） | 近（本地或设备） |
| 延迟量级（示意） | 数十–数百 ms 往返 | 十余–数十 ms 量级 | 数 ms–十余 ms 量级 |
| 算力/存储 | 近乎弹性扩展 | 中等、可多级累加 | 受限 |
| 管理复杂度 | 相对集中 | 多层协调，偏高 | 分布式，中等 |
| 典型节点 | 超大规模集群 | 网关、微数据中心、汇聚节点 | IoT 网关、基站侧多接入边缘计算（Multi-access Edge Computing, MEC）、智能摄像头 |

延迟区间随接入方式与路径变化，上表仅作相对比较[4][5]。

### 2.2 互补而非对立

完整物联网（Internet of Things, IoT）系统常同时使用三者：端侧采集与粗过滤，雾层区域聚合与规则，云端全局训练与长期存储。产业与学术上“edge/fog”并列使用增多，边界在模糊[5][9]。

## 3 多层架构

### 3.1 基础三层

| 层 | 组成 | 职责 | 能力量级 |
|----|------|------|----------|
| 终端（Thing） | 传感器、执行器、可编程逻辑控制器（Programmable Logic Controller, PLC） | 采集、简单滤波、执行 | MCU 级 |
| 雾（Fog） | 网关、边缘服务器、微数据中心 | 聚合、本地分析、缓存、规则 | 嵌入式 ARM–x86 服务器 |
| 云（Cloud） | 公有/私有云 | 全局分析、训练、长期存储 | 弹性集群 |

### 3.2 雾层再细分（常见）

- **设备级**：协议转换与异常过滤（如 Modbus → MQTT）
- **站点级**：车间/楼宇聚合与本地决策
- **区域级**：跨站点关联；可与 5G 基站侧 MEC 重叠[8]
- **骨干级**：核心网/内容分发网络（Content Delivery Network, CDN）节点上的较大处理

### 3.3 逐层提炼（示意）

```
终端: 原始采样（高频）
  ↓ 过滤、标准化
设备雾: 有效点（约降一个数量级）
  ↓ 统计聚合
站点雾: 站点摘要
  ↓ 跨站点关联
区域雾: 区域报告
  ↓ 建模与归档
云: 全局视图
```

具体压缩比取决于业务与采样率，上图为教学示意，非普适常数[10]。

## 4 OpenFog / IEEE 1934

### 4.1 八大支柱

| 支柱 | 英文 | 含义 |
|------|------|------|
| 安全 | Security | 端到端认证、加密、审计 |
| 可扩展性 | Scalability | 数十至大规模节点水平扩展 |
| 开放性 | Openness | 开放接口，降低锁定 |
| 自治性 | Autonomy | 断连时下层仍可运行 |
| 可编程性 | Programmability | 软件定义与远程配置 |
| 可靠性 | Reliability | 冗余与故障恢复 |
| 敏捷性 | Agility | 快速部署与变更 |
| 层次性 | Hierarchy | 明确多层组织关系 |

来源：OpenFog 参考架构与 IEEE 1934[2][3]。

### 4.2 功能平面（简述）

应用支撑、处理与加速、协议抽象、数据管理、安全（横切）。协议抽象需覆盖工业与物联网常见协议（OPC UA、Modbus、MQTT、CoAP 等）[3]。

### 4.3 部署模式

嵌入式（嵌在现有网络设备）、独立（专用雾服务器）、混合（最常见）。

## 5 应用场景

### 5.1 城市视频监控

万路级摄像头若全量上云，带宽与成本通常不可接受。多层方案示意：摄像头侧运动检测 → 街道级特征提取 → 区级追踪/告警 → 云端态势与训练。带宽可下降**数个数量级**，具体比例依赖码率、事件率与特征维度，须按项目测算[7][10]。

| 层级 | 处理 | 硬件示意 |
|------|------|----------|
| 摄像头侧 | 运动/感兴趣区域 | ISP / 轻量 SoC |
| 街道雾 | 检测与特征 | Jetson 类边缘 GPU |
| 区级雾 | 跨镜追踪、行为 | 边缘服务器 |
| 云 | 全城分析、再训练 | 数据中心 |

### 5.2 工业预处理

设备级滤波与联锁（毫秒级响应目标）、产线关联、车间预测维护、工厂/云长周期优化——层次与控制环时延预算绑定，不能一刀切“上云”[6]。

### 5.3 智能交通

车载融合 → 路侧单元（Roadside Unit, RSU）→ 区域信号协调 → 城市级仿真调度，对应多层雾/边协同。

## 6 技术挑战（简述）

异构编程模型（容器 / WebAssembly / 轻量运行时）、能力感知调度、移动性下的状态迁移、物理分散节点的信任与多租户隔离、数千节点编排与计量——均是落地瓶颈[5][9]。

## 7 现状与融合

独立“雾计算”品牌影响力弱于“边缘计算”：OpenFog 并入 IIC；主流云厂商产品多用 edge 命名；论文引用量 edge 显著高于 fog[5]。但其多层与水平协同思想已被边缘编排（如 KubeEdge、OpenYurt）吸收。

| 融合方向 | 说明 |
|----------|------|
| 术语 | fog/edge 并列 |
| 架构 | 现代边缘部署本就多层 |
| 标准 | IIC 与 ETSI MEC 等对话 |
| 技术 | K8s 边缘方案支持分层拓扑 |

## 8 局限、挑战与可改进方向

### 1. 术语与标准碎片化

**局限**：雾/边/MEC 定义重叠，采购与论文口径不一致，易导致架构图“看起来对、落地错位”。
**改进**：项目内固定词汇表（哪一层叫 fog/edge/MEC）；对照 IEEE 1934 支柱做差距清单，而非争论品牌名[2][5]。

### 2. 多层编排与可观测性不足

**局限**：跨层任务放置、故障域与计费缺少统一控制面；中间层“黑盒”难排障。
**改进**：以声明式期望状态 + 分层遥测（每层延迟/丢弃率/队列）验收；优先复用已有边缘 Kubernetes 与消息总线，少自研编排内核。

### 3. 安全与信任链断裂

**局限**：路侧/杆上节点物理暴露；多级处理后数据溯源与完整性难证明。
**改进**：硬件可信根 + 节点身份；关键路径端到端完整性校验；多租户强隔离；敏感推理尽量数据不出域（联邦/本地模型）[9]。

### 4. 移动性与状态迁移成本被低估

**局限**：车/无人机切换雾节点时，会话与缓存迁移延迟可抵消“靠近用户”的收益。
**改进**：预测式预热、无状态优先、状态外置到可跟随的存储；用切换事件 API（若在 MEC）触发迁移窗口[8]。

## 9 总结

雾计算的品牌热度不及边缘计算，但 Cloud-to-Thing 多层协同仍是大规模 IoT 的设计刚需。IEEE 1934 提供可检查的架构维度；实践中应把雾层当作可观测、可编排的中间处理带，而不是又一个营销标签。

## 参考文献

[1] F. Bonomi, R. Milito, J. Zhu, and S. Addepalli, "Fog Computing and Its Role in the Internet of Things," MCC Workshop on Mobile Cloud Computing, ACM, 2012.

[2] IEEE Standards Association, "IEEE 1934-2018: Standard for Adoption of OpenFog Reference Architecture for Fog Computing," 2018.

[3] OpenFog Consortium, "OpenFog Reference Architecture for Fog Computing," February 2017.

[4] M. Chiang and T. Zhang, "Fog and IoT: An Overview of Research Opportunities," IEEE Internet of Things Journal, vol. 3, no. 6, pp. 854-864, 2016.

[5] C. Mouradian et al., "A Comprehensive Survey on Fog Computing: State-of-the-Art and Research Challenges," IEEE Communications Surveys & Tutorials, vol. 20, no. 1, pp. 416-464, 2018.

[6] Industrial Internet Consortium, "The Industrial Internet of Things: An Evolution to a Smart Manufacturing Platform," 2020.

[7] Y. N. Malek et al., "On the Use of IoT and Big Data Technologies for Real-Time Monitoring and Data Processing," Procedia Computer Science, vol. 113, pp. 429-434, 2017.

[8] T. H. Luan et al., "Fog Computing: Focusing on Mobile Users at the Edge," arXiv:1502.01815, 2015.

[9] P. Hu et al., "Survey on Fog Computing: Architecture, Key Technologies, Applications and Open Issues," Journal of Network and Computer Applications, vol. 98, pp. 27-42, 2017.

[10] R. Dautov et al., "Data Processing in Fog Computing: Taxonomy, Requirements, and Architecture," IEEE Access, vol. 6, pp. 71545-71558, 2018.

[11] ETSI, "Multi-access Edge Computing (MEC); Framework and Reference Architecture," ETSI GS MEC 003, 2024.
