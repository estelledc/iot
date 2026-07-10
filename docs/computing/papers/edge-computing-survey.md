---
schema_version: '1.0'
id: edge-computing-survey
title: 边缘计算与物联网综述
layer: 4
content_type: UNKNOWN
difficulty: UNKNOWN
reading_time: UNKNOWN
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 边缘计算与物联网综述

## 摘要

随着物联网（IoT）设备数量的爆发式增长和应用场景对实时性、隐私性要求的不断提高，传统的云计算集中式架构面临延迟高、带宽不足、隐私泄露等挑战。边缘计算作为一种将计算、存储和网络服务下沉到靠近数据源的分布式计算范式，为物联网应用提供了有效的解决方案。本文从边缘计算的基本概念与架构出发，系统梳理了边缘计算在物联网中的核心技术方向，包括任务卸载、资源管理、边缘智能和联邦学习，深入分析了典型应用场景（智慧城市、自动驾驶、工业IoT、医疗健康），讨论了安全挑战与解决方案，对比分析了主流平台与开源框架及标准化进展，并展望了大模型边缘部署、边缘原生、Serverless边缘计算、数字孪生融合和绿色边缘计算等最新发展趋势。

**关键词**：边缘计算；物联网；任务卸载；边缘智能；联邦学习；云边端协同；边缘安全；数字孪生

## 1 引言

物联网（Internet of Things, IoT）通过将物理世界中的各类设备连接到互联网，实现了万物互联的愿景。据预测，到2025年全球IoT设备数量将超过300亿台，每天产生的数据量达到数百EB级别。IDC预测2024年全球边缘计算支出达2320亿美元，同比增长15.4%；Market Research Future报告显示，Edge Computing in IoT市场2025年规模为72.4亿美元，预计2035年将达425.6亿美元（CAGR 19.38%）。

然而，传统的云计算模式要求将所有数据上传至远端数据中心进行处理，这在面对海量IoT数据时暴露出严重的不足：网络往返延迟通常在100-500ms，远不能满足自动驾驶（<10ms）、工业控制等场景的实时性要求；一台自动驾驶汽车每天产生约4TB数据，全部上传至云端在带宽和成本上均不可行；此外，医疗、金融等领域的敏感数据受到GDPR等法规的严格约束，不允许随意传输至远端。

边缘计算（Edge Computing）的提出正是为了应对上述挑战。其核心思想是将计算资源部署在网络边缘——靠近数据产生的位置——从而实现低延迟处理、带宽节省和数据隐私保护。本文将从自上而下的视角，系统综述边缘计算与物联网的融合技术，涵盖基础架构、核心技术、应用场景、安全挑战、平台框架和前沿趋势。

## 2 基本概念与体系架构

### 2.1 边缘计算的定义与相关概念

边缘计算是一种分布式计算范式，将计算、存储和网络服务从集中式云数据中心下沉到靠近数据源的网络边缘节点执行。与之相关的概念包括：

- **MEC（Multi-access Edge Computing）**：由ETSI于2014年提出（最初称为Mobile Edge Computing），面向电信运营商，强调在无线接入网络侧部署计算能力，2016年更名以扩展到所有接入方式。ETSI MEC标准已进入Phase 4阶段（2024年至今），发布了完整的Phase 4规范集，并与Linux Foundation CAMARA项目和TM Forum合作推进Edge Native Connector。
- **雾计算（Fog Computing）**：由Cisco于2012年提出，强调从云到端之间的多层"雾"节点，不限定接入方式，侧重应用的分层部署。
- **Cloudlet**：由CMU的Satyanarayanan教授提出，定义为部署在网络边缘的"小型数据中心"，面向移动设备的计算卸载。

三者核心思想一致——将计算资源更靠近用户，区别在于MEC偏电信视角，雾计算偏部署视角，Cloudlet偏学术原型。

### 2.2 云-边-端三层架构

当前边缘计算最主流的体系结构为云-边-端（Cloud-Edge-Device）三层架构：

**云层（Cloud Layer）**：由大规模数据中心构成，负责全局模型训练、长期数据存储、跨区域协同调度等计算密集型任务。云层拥有近乎无限的计算和存储资源，但距离终端用户较远。

**边缘层（Edge Layer）**：由边缘服务器、基站侧MEC节点、智能网关、微数据中心等构成。负责实时推理、数据预处理与过滤、内容缓存、区域性任务调度等。边缘层是连接云端与终端的关键枢纽，兼具一定的计算能力和低延迟优势。

**终端层（Device Layer）**：由IoT传感器、摄像头、智能手机、车载终端、工控设备等构成。负责数据采集、简单预处理和轻量级本地推理（如TinyML）。

三层之间的协同模式包括：云边协同（模型在云端训练、边缘部署推理）、边边协同（相邻边缘节点间迁移任务或共享资源）、边端协同（边缘节点调度终端设备执行子任务）。

### 2.3 定量性能对比：边缘 vs 云

根据2024-2025年的大规模实测研究，边缘计算与云计算在关键指标上的对比如下：延迟方面，边缘本地处理通常为1-10ms，而云计算为50-200ms（取决于网络距离），边缘计算在实时应用中可实现10-50倍的延迟降低；带宽方面，边缘预处理可减少60-90%的数据传输量；可靠性方面，边缘节点支持断网自治运行。然而，云计算在计算密集型任务（如大规模模型训练）和吞吐量密集型应用中仍具有不可替代的优势。

## 3 核心技术方向

### 3.1 任务卸载

任务卸载（Task Offloading）是边缘计算中最核心的研究问题之一，指移动设备将计算密集型任务全部或部分迁移到边缘/云服务器执行的决策与执行过程。其核心决策包括四个维度：是否卸载（本地处理还是远端执行）、卸载到哪里（选择哪个边缘节点或云端）、卸载什么（整个任务还是子任务）、如何优化（延迟、能耗还是成本）。

在优化方法方面，近年来深度强化学习（DRL）成为主流，利用DQN、PPO、A3C等算法处理动态环境下的在线卸载决策；多智能体强化学习（MARL）用于多用户多服务器的协同卸载场景；博弈论方法适用于信息不对称的资源竞争场景；启发式算法则在大规模场景中提供快速近似解。2025年的最新研究进一步考虑了任务间的依赖关系，采用双层优化等方法处理带有复杂DAG结构的任务卸载问题[1]。此外，数字孪生技术正被引入计算卸载决策中，通过构建边缘环境的虚拟镜像来预测和优化卸载策略[11]。

### 3.2 资源管理

边缘资源（计算、存储、带宽）相比云端极为有限且高度异构，资源管理面临独特挑战。主要研究方向包括：资源分配——如何将有限算力公平高效地分配给多个竞争用户或任务；内容缓存——在边缘预缓存热点内容以减少回源流量；容器调度——轻量容器（Docker）和Kubernetes编排在边缘环境的适配优化；弹性伸缩——根据负载动态调整边缘资源规模。

Serverless/FaaS（Function-as-a-Service）模式正在向边缘延伸，为资源管理带来新范式。2024年IEEE ICC提出了首个形式化的Serverless Function Scheduling问题，考虑冷启动延迟和动态工作负载[12]。Serverledge框架（2024）实现了去中心化架构，每个FaaS节点可自主调度和执行函数，支持函数卸载和迁移。关键挑战包括：冷启动延迟（边缘资源受限时更严重）、多租户隔离、函数调度优化和资源受限环境下的弹性扩展。Unikernel作为边缘FaaS的安全沙箱隔离机制也在被积极探索[13]。

### 3.3 边缘智能

边缘智能（Edge Intelligence）是边缘计算与人工智能深度融合的产物，包含两个方向：AI for Edge——用AI技术优化边缘系统本身（如用强化学习做资源调度）；AI on Edge——在边缘设备上部署和运行AI模型。

关键使能技术包括：模型压缩（量化至INT8/INT4、结构化剪枝、知识蒸馏）、推理加速（TensorRT、ONNX Runtime、TFLite等框架）、模型分割（将DNN切分为设备端和边缘端两部分协同推理）、以及神经架构搜索（NAS）自动设计边缘友好的轻量模型。

2025年ACM Computing Surveys发表的综述"Empowering Edge Intelligence: A Comprehensive Survey on On-Device AI Models"系统梳理了AI模型在边缘和终端设备上的部署技术[14]。CEVA发布的"2025 Edge AI Technology Report"指出，边缘AI正在车辆、IoT和计算机视觉领域快速落地。

### 3.4 联邦学习

联邦学习（Federated Learning, FL）是一种分布式机器学习范式，多个边缘设备协同训练全局模型，原始数据不离开本地，仅共享模型参数或梯度更新。联邦学习与边缘计算天然契合：数据留在端侧保护隐私，边缘节点作为中间聚合器减轻云端通信压力，且能适配异构设备和非独立同分布（Non-IID）数据。

核心挑战包括：通信效率（梯度压缩、异步聚合）、数据异构性（个性化联邦学习）、系统异构性（不同设备算力差异下的客户端选择）、安全威胁（模型投毒、梯度泄露攻击）以及激励机制设计。典型应用涵盖智能手机键盘预测、跨医院医疗影像协同诊断、工厂间质检模型共享等场景。2025年IEEE INFOCOM发表的FedGPA[3]提出了全局-个性化协作的联邦学习方法用于边缘异常检测，进一步推动了联邦学习在边缘场景的实用化。

## 4 典型应用场景

### 4.1 智慧城市

边缘计算在智慧城市中的应用涵盖智能交通、环境监测、公共安全等多个领域。在智能交通方面，边缘节点部署在路侧单元（RSU）和交通信号灯控制器中，实时处理来自摄像头和雷达的数据流，实现车辆检测、交通流量统计和自适应信号控制。2024年Springer Journal of Grid Computing发表的研究提出了基于概率混合鲸鱼-蜻蜓优化（p-H-WDFOA）的边缘计算模型，显著降低了智慧城市车辆运输中的延迟。

在环境监测方面，分布式传感器网络通过边缘网关进行数据聚合和异常检测，实现空气质量、噪声水平和水质的实时监控。IEEE OTCON 2024的论文"The Convergence of Edge Computing and IoT: Driving Smarter Decision Making"系统分析了边缘计算与IoT融合如何驱动智慧城市的实时决策。

在公共安全方面，边缘AI赋能的视频分析系统可在本地完成人脸识别、异常行为检测和人群密度估计，避免将大量视频流上传至云端。区块链、IoT和边缘计算的协同正在被探索用于智能交通管理系统（STMS），结合强化学习实现自适应交通信号控制，在减少平均等待时间30-40%的同时保障数据不可篡改。

### 4.2 自动驾驶

自动驾驶是边缘计算最具挑战性的应用场景之一。V2X（Vehicle-to-Everything）场景要求端到端延迟低于10ms（安全关键决策）到100ms（非安全辅助功能）。自动驾驶系统需要融合来自激光雷达（LiDAR）、摄像头、毫米波雷达和超声波传感器的多模态数据，单车每秒产生的原始数据量可达数GB。

边缘计算在自动驾驶中的角色体现在三个层面：车载边缘（车内高性能计算平台处理感知和规划）、路侧边缘（RSU提供超视距感知和协同决策）、以及MEC边缘（基站侧提供高精地图更新和全局交通优化）。2024年的研究"EC-Drive: Edge-Cloud Collaborative Motion Planning for Autonomous Driving with Large Language Models"引入漂移检测算法管理边缘与云端数据处理，实现了实时性能和效率的平衡[15]。

IEEE VTC 2024 Spring发表的"Task Offloading for MEC-V2X Assisted Autonomous Driving"研究了MEC和V2X通信如何支持自动驾驶延迟敏感应用的任务卸载，提出了基于深度强化学习的动态卸载策略，在保证安全约束的前提下最小化端到端延迟。IJACSA 2024的研究则提供了边缘计算在自动驾驶实时决策中的实际实现案例，展示了在真实道路环境中边缘推理相比云端推理可将感知延迟从120ms降低至8ms。

### 4.3 工业IoT

工业IoT（IIoT）对边缘计算的需求体现在实时控制、预测性维护和质量检测等方面。在智能制造场景中，生产线上的传感器每秒产生数千个数据点，边缘计算节点需要在毫秒级时间内完成异常检测和控制指令下发，任何延迟都可能导致产品缺陷或设备损坏。

预测性维护是IIoT中边缘计算最成熟的应用之一。通过在设备侧部署轻量级机器学习模型（如振动频谱分析、温度趋势预测），边缘节点可以实时监测设备健康状态，在故障发生前数小时甚至数天发出预警，将非计划停机时间减少30-50%。

2025年Nature Scientific Reports发表的研究提出了统一的Edge-AI框架，结合LoRaWAN + 5G双无线连接、联邦学习和PoA区块链，为工业IoT提供安全、低延迟的智能服务[16]。该框架在实际工厂环境中验证了边缘AI在质量检测中的有效性，检测准确率达到99.2%，推理延迟仅为12ms。数字孪生技术与边缘计算的融合在工业场景中尤为突出——2025年IEEE发表的研究探索了5G增强边缘计算结合数字孪生用于能源密集型工业系统的实时监控和优化，实现了能耗降低15-25%的效果。

### 4.4 医疗健康

边缘计算在医疗健康领域的应用正在快速增长，主要驱动力包括：患者数据隐私保护（HIPAA合规）、实时生命体征监测的低延迟需求、以及偏远地区医疗资源不足的现实。

在远程患者监测方面，可穿戴设备（智能手表、心电贴片、血氧仪）持续采集生理数据，边缘网关在本地完成心律失常检测、跌倒识别等实时分析，仅在检测到异常时才上报云端，既保护了患者隐私又降低了网络负载。MDPI Future Internet 2024发表的综述"Edge Computing in Healthcare: Innovations, Opportunities, and Challenges"系统梳理了边缘计算在医疗中的创新应用[17]。

在医学影像方面，边缘AI可在本地完成X光片初筛、CT影像分割等计算密集型任务，将诊断辅助结果在数秒内反馈给医生，而非等待云端处理的数分钟延迟。Springer Journal of Cloud Computing 2024的研究展示了MEC结合5G如何在IoT医疗系统中降低延迟、加速临床决策。

在IoMT（Internet of Medical Things）系统方面，2025年Nature Scientific Reports提出了混合雾-边缘计算架构用于实时健康监测，通过三层架构（设备层-雾层-边缘层）实现了数据处理的分级优化，在保证99.5%数据可用性的同时将端到端延迟控制在50ms以内。ScienceDirect 2024的研究集成可穿戴传感器贴片与边缘计算用于远程医疗实时健康监测，验证了在慢性病管理中边缘计算可将异常事件响应时间从分钟级缩短至秒级。

### 4.5 其他新兴应用

除上述四大领域外，边缘计算在以下场景也展现出巨大潜力：智能农业（无人机巡检+边缘图像分析实现精准施肥和病虫害检测）、智能零售（边缘视觉AI实现无人结算和客流分析）、增强现实/虚拟现实（AR/VR需要<20ms的运动到光子延迟，边缘渲染是关键使能技术）、以及智能电网（分布式能源管理和需求响应的实时优化）。

## 5 安全挑战与解决方案

### 5.1 威胁分类

边缘计算的分布式特性带来了独特的安全挑战。2025年MDPI Future Internet发表的综述"A Survey on Edge Computing Security Challenges: Classification, Threats, and Solutions"系统分类了边缘计算安全威胁[18]，主要包括：

**物理层威胁**：边缘设备部署在开放环境中，面临物理篡改、侧信道攻击和固件替换等风险。攻击者可能直接接触设备，提取密钥或注入恶意代码。

**网络层威胁**：中间人攻击（MITM）、DDoS攻击、DNS劫持和流量嗅探。边缘节点之间的通信链路通常缺乏端到端加密保护。

**数据层威胁**：数据注入攻击（向传感器注入虚假数据）、数据泄露（未加密存储的敏感信息被窃取）、以及隐私推断攻击（通过分析边缘节点的通信模式推断用户行为）。

**应用层威胁**：恶意容器/函数注入、API滥用、模型投毒（针对边缘AI模型的对抗攻击）和供应链攻击。

### 5.2 解决方案

**硬件级安全**：Physical Unclonable Functions (PUFs)结合AI自适应管理增强设备身份认证；可信执行环境（TEE，如ARM TrustZone、Intel SGX）为敏感计算提供隔离执行空间；安全启动链确保固件完整性。

**隐私保护技术**：联邦学习在保护数据隐私的同时实现协同安全检测；差分隐私为数据发布和模型训练提供形式化的隐私保证；同态加密允许在密文上直接计算，但当前计算开销仍然较大。

**分布式信任机制**：区块链技术增强数据完整性和可追溯性，为边缘节点间的信任建立提供去中心化方案；零信任架构（Zero Trust Architecture）在边缘环境中的适配，要求每次访问都进行身份验证和授权。

**AI驱动的安全**：基于深度学习的入侵检测系统（IDS）部署在边缘节点，实现本地化的实时威胁检测；联邦学习驱动的协同威胁情报共享，在不暴露各节点原始数据的前提下构建全局安全态势感知。

IEEE ISVLSI 2024的研究进一步强调了隐私保护和安全框架的重要性，探索了安全、鲁棒和隐私保护的边缘计算框架设计，提出了多层防御策略以应对日益复杂的攻击手段。

## 6 主流平台、框架与标准化

### 6.1 商业云平台

主要商业平台包括：AWS IoT Greengrass支持将Lambda函数和ML推理推送到边缘，与AWS生态深度集成；Azure IoT Edge采用容器化模块架构，支持Custom Vision等AI模型下发；华为IEF（Intelligent Edge Fabric）与昇腾AI芯片集成，适合国内政企客户；阿里云Link IoT Edge支持函数计算和流计算在边缘运行。

### 6.2 开源框架

开源框架方面，KubeEdge是华为发起的CNCF毕业项目（2024年9月），基于Kubernetes原生扩展，通过CloudCore与EdgeCore的消息通道实现云边协同，支持边缘节点离线自治；OpenYurt是阿里发起的CNCF孵化项目，以无侵入方式将Kubernetes扩展到边缘，保留完整K8s API，引入NodePool实现单元化管理；EdgeX Foundry是Linux Foundation下的IoT边缘中间件平台，专注设备接入和数据抽象，提供协议适配层和规则引擎。

在选型上，KubeEdge/OpenYurt解决"如何管理边缘节点上的工作负载"，EdgeX Foundry解决"如何接入异构IoT设备和数据"，两者常配合使用形成完整的边缘计算栈。

### 6.3 标准化进展

ETSI MEC标准已经历四个阶段：Phase 1（2014-2017）定义基础架构；Phase 2（2017-2020）建立API框架和NFV集成；Phase 3（2020-2023）完成与3GPP的协同架构白皮书；Phase 4（2024至今）发布了完整的新一代规范集，与Linux Foundation CAMARA项目和TM Forum合作，推进Edge Native Connector（STF 678），并与oneM2M合作促进边缘IoT部署和API暴露。关键标准文档包括ETSI GS MEC 003（基于NFV架构的边缘计算参考架构）和ETSI GS MEC 045 V3.2.1（2025-08，Multi-access Edge Computing QoS Measurement API）。

3GPP方面，5G核心网与MEC的集成支持URLLC（超可靠低延迟通信）场景，为边缘计算提供了网络层面的标准化保障。Release 18（5G-Advanced）进一步增强了边缘计算支持，包括网络切片的精细化管理和边缘应用的服务发现机制。

## 7 优势与局限性

### 7.1 优势

边缘计算为物联网带来的核心优势包括：低延迟（本地处理避免网络往返，可实现毫秒级响应）、带宽节省（仅上传必要数据，减少核心网压力80-95%）、隐私增强（敏感数据不出域，满足数据安全法规要求）、高可靠性（断网时边缘自治运行，不依赖中心连接）、可扩展性（新增边缘节点分摊负载，水平扩展灵活）、以及降低云端成本。

### 7.2 局限性

同时，边缘计算也面临显著挑战：资源受限（边缘设备算力和内存远小于云数据中心）、管理复杂（海量异构节点的部署、监控和更新困难）、安全暴露面大（物理分散导致易被攻击）、一致性难保（分布式状态同步挑战）、标准碎片化（缺乏统一标准，各厂商接口不一）、以及复合型人才缺口。

## 8 最新发展趋势

### 8.1 大模型边缘部署

2024-2025年最热门的方向之一是将大语言模型（LLM）部署到边缘设备。核心驱动力包括隐私保护、离线可用和低延迟交互。技术路线包括：小语言模型（SLMs）如Phi-3、Gemma 2B等专为边缘设计的小参数模型；极致量化（4-bit/2-bit GPTQ、AWQ、GGUF格式）；推理优化（投机解码、KV-Cache优化）；以及多设备协作推理——如Jupiter系统[2]通过流水线并行和投机解码实现多台边缘设备协同运行LLM，在4台Jetson设备上实现最高26.1倍的端到端延迟缩减。PowerInfer-2（2024）首次在智能手机上运行47B参数LLM，达到11.68 tokens/s的生成速度，相比llama.cpp实现25倍加速[19]。

### 8.2 边缘原生

边缘原生（Edge-Native）不是将云原生技术简单缩小搬到边缘，而是从边缘场景出发原生设计系统架构，强调离线优先（offline-first）设计、资源感知调度、轻量运行时和自愈自治能力。核心理念包括：数据本地性优先（计算跟着数据走而非数据跟着计算走）、渐进式一致性（容忍短暂不一致以换取可用性）、以及自适应降级（资源不足时优雅降低服务质量而非完全失败）。

### 8.3 WebAssembly在边缘

WebAssembly（Wasm）作为边缘轻量运行时正在快速崛起：冷启动时间<1ms（对比容器100-300ms）、沙箱安全隔离、跨平台支持（ARM/x86/RISC-V）。2026年CNCF调研显示31%的云原生开发者已在使用Wasm，其中54%用于边缘场景。WasmEdge、Spin等运行时正在成为边缘Serverless的新选择，相比传统容器可将资源占用降低90%以上。

### 8.4 数字孪生与边缘计算融合

数字孪生（Digital Twin）技术与边缘计算的融合正在成为重要趋势。2025年ScienceDirect发表的综述"Digital Twin-empowered intelligent computation offloading for edge computing"系统分析了数字孪生如何赋能边缘计算的智能计算卸载决策[11]。

数字孪生在边缘计算中的应用体现在三个层面：第一，构建边缘环境的虚拟镜像，通过仿真预测不同卸载策略的效果，避免在真实系统上试错；第二，实时同步物理边缘节点的状态到数字空间，实现全局可观测性和智能调度；第三，利用数字孪生进行"what-if"分析，优化边缘基础设施的规划和扩容决策。

关键应用场景包括：6G EoT（Edge of Things）系统架构设计、能源密集型工业系统的实时监控和优化、以及智慧城市基础设施的全生命周期管理。2024年AIOTI白皮书探讨了AI驱动的数字孪生在分布式能源系统中的边缘部署案例，展示了通过数字孪生实现能源调度优化可降低运营成本20-30%。

### 8.5 Serverless边缘计算

Serverless/FaaS模式向边缘的延伸为IoT应用提供了更灵活的部署方式。开发者无需管理底层基础设施，只需编写事件驱动的函数，系统自动处理资源分配、弹性伸缩和故障恢复。2024年Pervasive and Mobile Computing发表的研究比较了微服务和Serverless函数在边缘实时IoT分析中的生命周期、性能和资源利用，发现Serverless在事件驱动的IoT场景中具有显著优势：资源利用率提升40-60%，部署复杂度降低70%[20]。

FaaS@Edge（GECON 2024）提出了利用志愿者资源进行边缘FaaS部署的分布式中间件架构，通过激励机制吸引闲置设备贡献算力。关键技术挑战包括：冷启动优化（预热策略、快照恢复）、函数编排（有状态工作流的边缘执行）、以及多租户安全隔离（Wasm/Unikernel轻量沙箱）。

### 8.6 5G/6G与MEC深度融合

运营商将MEC部署在5G用户面功能（UPF）侧，结合网络切片实现差异化服务质量保障，URLLC（超可靠低延迟通信）场景成为杀手级应用的驱动力。5G-Advanced（Release 18/19）进一步增强了边缘计算支持，包括AI/ML驱动的网络优化、精细化的QoS管理和边缘应用的标准化服务发现。

展望6G时代，边缘计算将进一步与通感一体化（Integrated Sensing and Communication, ISAC）、智能超表面（Reconfigurable Intelligent Surface, RIS）、以及语义通信等新技术融合。6G网络预计将原生支持"计算即服务"，边缘计算不再是网络的附加功能，而是网络架构的内生组成部分。

### 8.7 绿色边缘计算

随着边缘AI设备的普及和AI模型复杂度的超线性增长，能耗和碳排放成为不可忽视的问题。2024年ScienceDirect发表的综述"A comprehensive survey of energy-efficient computing to enable sustainable IoT networks"涵盖了绿色边缘计算、绿色雾计算和绿色云计算的全面分析[21]。

关键解决方案包括：可再生能源集成（太阳能/风能驱动的边缘节点，配合储能系统实现能源自给）、动态电压频率调节（DVFS，根据负载动态调整处理器功耗）、工作负载整合和休眠策略（将任务集中到少数节点执行，空闲节点进入低功耗模式）、以及碳感知调度（将计算任务调度到当前使用清洁能源的节点）。

Wiley 2024的研究"Sustainable edge computing: Challenges and future directions"提出了三方面的可持续计算方案：节能经济部署（优化边缘节点的地理分布和硬件选型）、容错自动化运维（减少人工干预的能耗和碳足迹）和协作资源管理（跨组织的边缘资源共享以提高整体利用率）。研究表明，通过综合应用上述策略，边缘计算系统的能耗可降低30-50%，同时维持95%以上的服务质量。

## 9 总结与展望

边缘计算与物联网的融合正在从概念验证走向规模化落地。从技术演进来看，任务卸载和资源管理等基础问题的研究已趋于成熟，边缘智能和联邦学习正在成为主流应用范式，而大模型边缘部署、边缘原生架构、Serverless边缘计算、数字孪生融合和绿色边缘计算代表了下一代边缘计算的发展方向。

从应用落地来看，智慧城市、自动驾驶、工业IoT和医疗健康等领域已有大量实际部署案例，边缘计算正在从"技术可行"走向"商业可用"。从标准化来看，ETSI MEC Phase 4和3GPP 5G-Advanced标准的持续演进为边缘计算的规模化部署提供了坚实基础。从产业生态来看，开源框架（KubeEdge、OpenYurt）的成熟和商业平台的完善正在降低边缘计算的部署门槛。

未来的关键挑战在于：如何在资源极度受限的边缘环境中高效运行日益复杂的AI模型；如何实现跨厂商、跨平台的标准化互操作；如何在开放的物理环境中保障安全性；如何实现绿色可持续的边缘计算；以及如何构建自适应、自治的边缘系统以应对动态多变的IoT场景。随着5G/6G网络的普及、AI芯片的持续进步和开源生态的完善，边缘计算有望成为支撑下一代智能物联网应用的核心基础设施。

## 参考文献

[1] W. Xu et al., "Dependency-Aware Task Offloading in Edge Computing: A Bi-Level Optimization Approach," IEEE Internet of Things Journal, 2025.

[2] S. Ye, B. Ouyang, L. Zeng, T. Qian, X. Chu, J. Tang, and X. Chen, "Jupiter: Fast and Resource-Efficient Collaborative Inference of Generative LLMs on Edge Devices," IEEE INFOCOM, 2025.

[3] Z. Chen, L. Xue, L. Zhong, and G. Min, "FedGPA: Federated Learning with Global-Personalized Collaboration for Edge Anomaly Detection," IEEE INFOCOM, 2025.

[4] Y. Mao, C. You, J. Zhang, K. Huang, and K. B. Letaief, "A Survey on Mobile Edge Computing: The Communication Perspective," IEEE Communications Surveys & Tutorials, vol. 19, no. 4, pp. 2322-2358, 2017.

[5] W. Shi, J. Cao, Q. Zhang, Y. Li, and L. Xu, "Edge Computing: Vision and Challenges," IEEE Internet of Things Journal, vol. 3, no. 5, pp. 637-646, 2016.

[6] J. Chen and X. Ran, "Deep Learning with Edge Computing: A Review," Proceedings of the IEEE, vol. 107, no. 8, pp. 1655-1674, 2019.

[7] Q. Yang, Y. Liu, T. Chen, and Y. Tong, "Federated Machine Learning: Concept and Applications," ACM Transactions on Intelligent Systems and Technology, vol. 10, no. 2, pp. 1-19, 2019.

[8] X. Wang, Y. Han, V. C. M. Leung, D. Niyato, X. Yan, and X. Chen, "Convergence of Edge Computing and Deep Learning: A Comprehensive Survey," IEEE Communications Surveys & Tutorials, vol. 22, no. 2, pp. 869-904, 2020.

[9] Z. Zhou, X. Chen, E. Li, L. Zeng, K. Luo, and J. Zhang, "Edge Intelligence: Paving the Last Mile of Artificial Intelligence with Edge Computing," Proceedings of the IEEE, vol. 107, no. 8, pp. 1738-1762, 2019.

[10] S. Wang, T. Tuor, T. Salonidis, K. K. Leung, C. Makaya, T. He, and K. Chan, "Adaptive Federated Learning in Resource Constrained Edge Computing Systems," IEEE Journal on Selected Areas in Communications, vol. 37, no. 6, pp. 1205-1221, 2019.

[11] Y. Zhang et al., "Digital Twin-empowered intelligent computation offloading for edge computing," ScienceDirect, 2025.

[12] M. Russo et al., "Serverless Function Scheduling in Edge Computing: A Formal Problem Definition," IEEE ICC, 2024.

[13] Serverledge Team, "Serverledge: Decentralized Function-as-a-Service for the Edge," Pervasive and Mobile Computing, 2024.

[14] Y. Li et al., "Empowering Edge Intelligence: A Comprehensive Survey on On-Device AI Models," ACM Computing Surveys, 2025.

[15] H. Zhang et al., "EC-Drive: Edge-Cloud Collaborative Motion Planning for Autonomous Driving with Large Language Models," arXiv:2408.09972, 2024.

[16] A. Kumar et al., "Unified Edge-AI Framework with LoRaWAN, 5G, Federated Learning and PoA Blockchain for Industrial IoT," Nature Scientific Reports, 2025.

[17] R. Patel et al., "Edge Computing in Healthcare: Innovations, Opportunities, and Challenges," MDPI Future Internet, 2024.

[18] S. Ahmed et al., "A Survey on Edge Computing Security Challenges: Classification, Threats, and Solutions," MDPI Future Internet, 2025.

[19] Z. Xue et al., "PowerInfer-2: Fast Large Language Model Inference on a Smartphone," arXiv:2406.06282, 2024.

[20] G. Ferraro et al., "Comparing Microservices and Serverless Functions for Edge Real-Time IoT Analytics," Pervasive and Mobile Computing, 2024.

[21] M. Hassan et al., "A comprehensive survey of energy-efficient computing to enable sustainable IoT networks," ScienceDirect, 2024.
