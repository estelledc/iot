---
schema_version: '1.0'
id: edge-computing-survey
title: 边缘计算与物联网综述
layer: 4
content_type: survey
difficulty: intermediate
reading_time: 32
prerequisites: []
tags:
  - 边缘计算
  - 物联网
  - 任务卸载
  - 边缘智能
  - 联邦学习
  - MEC
  - 云边端协同
  - 绿色边缘
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 边缘计算与物联网综述

> **难度**：🟡 中级 | **领域**：边缘计算、物联网体系 | **阅读时间**：约 32 分钟

## 日常类比

云计算像把所有食材运到远郊中央厨房再送回餐桌——量大但路远。物联网（Internet of Things, IoT）设备遍布现场，路途延迟、带宽与隐私都成问题。**边缘计算（Edge Computing）** 像在小区开前置厨房：能本地做完的菜不上高速；只有要全局配方（大模型训练、跨域对标）才回中央厨房[5][4]。

## 摘要

本文综述边缘计算与 IoT 的融合：概念与云-边-端架构、任务卸载与资源管理、边缘智能与联邦学习、典型行业场景、安全、平台与标准，以及大模型边缘、Serverless、数字孪生与绿色计算等趋势。市场与延迟等量化主张多来自咨询报告或单篇实验，**宜作量级参考而非精确预测**[4][5][8]。

## 1 引言

集中式云处理在海量 IoT 下暴露三类压力：往返延迟难稳满足车路/工控等紧约束；原始传感全量上云在带宽与成本上常不可行；医疗等数据受法规约束不宜随意离境[5]。边缘计算把算力放到靠近数据源处，换低延迟、省带宽与隐私边界。

咨询机构对设备数、边缘支出的预测口径不一且随年份修订；正文避免把单一预测写成事实，只保留"规模持续扩张、边缘投资受关注"这一方向性判断。

## 2 概念与架构

### 2.1 相关概念

| 概念 | 提出/语境 | 侧重点 |
|------|----------|--------|
| **MEC（Multi-access Edge Computing）** | ETSI，原 Mobile Edge Computing | 电信接入侧算力与 API |
| **雾计算（Fog Computing）** | Cisco 等 | 云到端之间多层"雾"节点 |
| **Cloudlet** | CMU 等学术原型 | 靠近移动用户的微型数据中心 |

三者都把算力前移；差别主要在运营商视角、部署层次与学术原型传统[4]。

### 2.2 云-边-端

| 层 | 典型职责 |
|----|---------|
| 云 | 全局训练、长期存储、跨域调度 |
| 边 | 实时推理、过滤缓存、区域调度、断网自治 |
| 端 | 采集、轻量 TinyML、就近执行 |

协同模式：云边（训推分离）、边边（迁移/共享）、边端（子任务下沉）。

### 2.3 相对云的性能倾向

| 指标 | 边缘倾向 | 云倾向 |
|------|---------|--------|
| 延迟 | 本地可达 ms～十余 ms 量级（视链路） | 常数十～数百 ms 往返 |
| 带宽 | 预处理可大幅减回传 | 适合大吞吐汇聚 |
| 可靠 | 可断网自治 | 依赖广域连接 |
| 重计算 | 受限 | 大规模训练更合适 |

具体倍数（"延迟降几十倍""带宽省百分之几十"）高度依赖应用与拓扑，综述中只作方向，不写入硬 SLA[4][8]。

## 3 核心技术方向

### 3.1 任务卸载

决策四维：是否卸、卸到哪、卸什么、优化目标（延迟/能耗/成本）。方法谱系含深度强化学习（DQN/PPO 等）、多智能体、博弈与启发式；近期工作处理 DAG 依赖与数字孪生辅助决策[1][11]。

### 3.2 资源管理

边缘算力/存储/带宽有限且异构。主题包括分配公平性、内容缓存、容器编排适配、弹性伸缩。Serverless/FaaS 下沉带来冷启动、多租户隔离与调度形式化问题[12][13]；Unikernel/Wasm 等被讨论作轻量沙箱。

### 3.3 边缘智能

| 方向 | 含义 |
|------|------|
| AI for Edge | 用学习优化调度/缓存本身 |
| AI on Edge | 在边/端跑模型 |

使能技术：量化/剪枝/蒸馏、TensorRT/ORT/TFLite、模型分割、NAS 等[6][9][14]。

### 3.4 联邦学习

数据不出域，交换参数/梯度；边缘可作聚合点。挑战：通信、Non-IID、系统异构、投毒与梯度泄露、激励。FedGPA 等个性化/选择性聚合工作推动异常检测等落地叙事[3][7][10]。

## 4 应用场景

### 4.1 智慧城市

路侧单元与信号机上的视觉/雷达处理、环境传感聚合、本地视频分析减少回传。优化算法与区块链协同等论文报告等待时间或安全属性改善，**幅度随城市与基线而变**，不宜写成统一百分比。

### 4.2 自动驾驶

V2X 对端到端延迟分档要求严格（安全相关更紧）。角色分车载、路侧、MEC 三层。边缘-云协同规划与 MEC 卸载研究强调安全约束下的延迟[15]。单车数据率与"云 120ms vs 边 8ms"类对比属特定实现口径。

### 4.3 工业 IoT

毫秒级异常检测与控制、预测维护。统一 Edge-AI + 连接 + FL + 区块链等框架有工厂验证报告（高准确率、十余 ms 推理等）[16]；数字孪生结合能耗优化亦有两位数百分比量级案例，需独立复现。

### 4.4 医疗健康

隐私（如 HIPAA 语境）、可穿戴实时分析、影像初筛。综述与 MEC+5G 工作讨论延迟与可用性指标[17]；混合雾-边缘架构的"99.x% 可用性 / 数十 ms"同样是论文设定下的结果。

### 4.5 其他

精准农业、智能零售、AR/VR（运动到光子延迟紧）、智能电网等。

## 5 安全

### 5.1 威胁面

| 层 | 例 |
|----|----|
| 物理 | 篡改、侧信道、固件替换 |
| 网络 | MITM、DDoS、流量嗅探 |
| 数据 | 注入、泄露、隐私推断 |
| 应用 | 恶意负载、API 滥用、模型投毒、供应链 |

系统分类见安全综述[18]。

### 5.2 对策方向

硬件根信任与 TEE、联邦/差分隐私/同态（后者开销仍大）、区块链与零信任适配、边侧 IDS 与协同情报。多层防御是共识，无银弹。

## 6 平台与标准

### 6.1 商业与开源

| 类型 | 代表 | 角色 |
|------|------|------|
| 云厂商边缘 | Greengrass、Azure IoT Edge、IEF、Link IoT Edge 等 | 函数/ML 下沉与云生态 |
| 工作负载编排 | KubeEdge、OpenYurt、K3s 等 | 管边缘上的容器负载 |
| 设备接入 | EdgeX Foundry 等 | 协议抽象与规则 |

编排与接入常组合，而非二选一。

### 6.2 标准化

ETSI MEC 多阶段演进至与 CAMARA/TM Forum 等协作的 API 暴露；3GPP 将 MEC 与 5G 核心、URLLC、切片结合。标准文档号与版本以 ETSI/3GPP 发布页为准，正文不绑定易变的次版本号。

## 7 优势与局限（总览）

| 优势 | 局限 |
|------|------|
| 低延迟本地闭环 | 单节点算力/内存有限 |
| 减少回传 | 海量异构节点难运维 |
| 数据不出域 | 物理暴露面大 |
| 断网可降级运行 | 分布式一致性难 |
| 水平加节点 | 标准与接口碎片化 |

## 8 趋势

### 8.1 大模型边缘

小参数模型、低比特量化、投机解码与多设备协同（如 Jupiter 报告的显著延迟缩减）[2]；手机侧大模型推理亦有系统工作[19]。加速比依赖硬件与实现。

### 8.2 边缘原生

离线优先、资源感知、轻量运行时、渐进一致与自适应降级——不是简单"缩小版云原生"。

### 8.3 Wasm 与 Serverless

Wasm 冷启动与沙箱吸引边缘 FaaS；微服务 vs Serverless 对比研究给出利用率与复杂度改善的报告口径[20]。CNCF 等调研中的采用率随样本变，作趋势即可。

### 8.4 数字孪生融合

用孪生做卸载 what-if、状态镜像与规划[11]。

### 8.5 5G/6G 与绿色计算

UPF 侧 MEC、切片与 URLLC；6G 语境下通感一体、RIS、语义通信与"计算内生"。能耗方面：DVFS、休眠整合、碳感知调度与可再生能源节点；综述称综合策略可显著降耗并维持服务质量，具体百分比视负载[21]。

## 9 局限、挑战与可改进方向

### 1. 指标不可比

**局限**：不同论文的延迟/能耗/准确率基线、拓扑与设备差过大，综述若并列百分比易误导决策者[4][8]。
**改进**：引用时注明设定；工程选型以目标场景复测为准；报告中强制给基线与硬件。

### 2. 卸载算法到生产的鸿沟

**局限**：DRL 仿真假设（完美状态、稳定信道）与现场异构、掉线不符[1]。
**改进**：数字孪生/影子流量验证；保留启发式兜底；优化目标加入安全与合规约束。

### 3. 安全与运维叠加

**局限**：节点越散，补丁、密钥与供应链审计成本越高；FL 不自动等于隐私合规[18][7]。
**改进**：设备身份与安全启动默认开；最小权限网络策略；隐私技术按威胁模型组合而非口号。

### 4. 绿色与智能目标冲突

**局限**：追 AI 精度与多模型常抬功耗，与碳约束打架[21]。
**改进**：碳/焦耳纳入调度目标；夜间或清洁能源窗口跑重任务；模型档位随能源状态降级。

## 10 总结

边缘与 IoT 融合已从概念走向行业试点与部分规模化。基础卸载与资源问题文献充分，边缘智能与 FL 成应用主叙事，大模型边缘、边缘原生、Serverless、孪生与绿色计算构成下一波议题。落地关键仍是：在受限硬件上跑复杂 AI、跨厂商互操作、开放环境安保，以及可持续运维。

## 参考文献

[1] W. Xu et al., "Dependency-Aware Task Offloading in Edge Computing: A Bi-Level Optimization Approach," IEEE Internet of Things Journal, 2025.
[2] S. Ye et al., "Jupiter: Fast and Resource-Efficient Collaborative Inference of Generative LLMs on Edge Devices," IEEE INFOCOM, 2025.
[3] Z. Chen et al., "FedGPA: Federated Learning with Global-Personalized Collaboration for Edge Anomaly Detection," IEEE INFOCOM, 2025.
[4] Y. Mao et al., "A Survey on Mobile Edge Computing: The Communication Perspective," IEEE Communications Surveys & Tutorials, 2017.
[5] W. Shi et al., "Edge Computing: Vision and Challenges," IEEE Internet of Things Journal, 2016.
[6] J. Chen and X. Ran, "Deep Learning with Edge Computing: A Review," Proceedings of the IEEE, 2019.
[7] Q. Yang et al., "Federated Machine Learning: Concept and Applications," ACM TIST, 2019.
[8] X. Wang et al., "Convergence of Edge Computing and Deep Learning: A Comprehensive Survey," IEEE Communications Surveys & Tutorials, 2020.
[9] Z. Zhou et al., "Edge Intelligence: Paving the Last Mile of Artificial Intelligence with Edge Computing," Proceedings of the IEEE, 2019.
[10] S. Wang et al., "Adaptive Federated Learning in Resource Constrained Edge Computing Systems," IEEE JSAC, 2019.
[11] Y. Zhang et al., "Digital Twin-empowered intelligent computation offloading for edge computing," 2025.
[12] M. Russo et al., "Serverless Function Scheduling in Edge Computing: A Formal Problem Definition," IEEE ICC, 2024.
[13] Serverledge Team, "Serverledge: Decentralized Function-as-a-Service for the Edge," Pervasive and Mobile Computing, 2024.
[14] Y. Li et al., "Empowering Edge Intelligence: A Comprehensive Survey on On-Device AI Models," ACM Computing Surveys, 2025.
[15] H. Zhang et al., "EC-Drive: Edge-Cloud Collaborative Motion Planning for Autonomous Driving with Large Language Models," arXiv:2408.09972, 2024.
[16] A. Kumar et al., "Unified Edge-AI Framework with LoRaWAN, 5G, Federated Learning and PoA Blockchain for Industrial IoT," Scientific Reports, 2025.
[17] R. Patel et al., "Edge Computing in Healthcare: Innovations, Opportunities, and Challenges," Future Internet, 2024.
[18] S. Ahmed et al., "A Survey on Edge Computing Security Challenges: Classification, Threats, and Solutions," Future Internet, 2025.
[19] Z. Xue et al., "PowerInfer-2: Fast Large Language Model Inference on a Smartphone," arXiv:2406.06282, 2024.
[20] G. Ferraro et al., "Comparing Microservices and Serverless Functions for Edge Real-Time IoT Analytics," Pervasive and Mobile Computing, 2024.
[21] M. Hassan et al., "A comprehensive survey of energy-efficient computing to enable sustainable IoT networks," 2024.
[22] ETSI, "Multi-access Edge Computing (MEC); Framework and Reference Architecture," GS MEC 003.
