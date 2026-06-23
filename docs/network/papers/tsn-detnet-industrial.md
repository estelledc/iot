# TSN/DetNet 确定性网络：工业物联网的实时通信基石

> 难度：🟠 进阶 | 预计阅读：40 分钟 | 最后更新：2025-06

## 摘要

传统以太网是"尽力而为"的——数据包可能快也可能慢，甚至可能丢失。但在工厂车间里，一个机械臂的控制指令迟到 1 毫秒就可能意味着产品报废甚至安全事故。TSN（Time-Sensitive Networking）和 DetNet（Deterministic Networking）正是为了解决这个问题而生：它们给以太网装上了"确定性引擎"，保证关键数据在有界延迟内、零丢包地送达。本文系统介绍 TSN 标准族和 DetNet 架构，分析 5G+TSN 融合方案，对比传统工业以太网，并给出工业部署实践。

**关键词**：TSN；DetNet；确定性网络；工业以太网；802.1Qbv；802.1AS；PROFINET；EtherCAT

## 1 引言：工厂里的网络为什么必须"守时"

日常生活中，网页加载多花 200ms，你可能感觉不到。但在工业场景中，时间的含义完全不同。

想象一条汽车焊接产线：6 台焊接机器人必须在精确的时刻、以精确的角度焊接车身。控制器每 250 微秒发出一次运动指令，如果某个指令因为网络拥塞晚到了 500 微秒，机器人的动作就会失步——轻则焊缝歪了，重则机械臂相撞。

这就是"确定性"的含义：不只是"平均延迟低"，而是**最坏情况下的延迟也有严格的上界**。传统以太网的延迟分布是一个"长尾"：99% 的包在 1ms 内到达，但偶尔会有 10ms 甚至 100ms 的异常值。工业控制要求的是"100% 的包都在 X 微秒内到达，没有例外"。

为了实现这个目标，工业界过去 20 年发展出了多种专用工业以太网协议（PROFINET IRT、EtherCAT、POWERLINK、SERCOS III 等），但它们互不兼容，形成了"协议孤岛"。TSN 的目标是用一套 IEEE 标准统一所有工业以太网的确定性需求，同时保持与标准以太网的完全兼容。

## 2 TSN 标准族全景

TSN 不是一个单一标准，而是 IEEE 802.1 工作组下的一组标准的总称。每个标准解决确定性的一个维度：

### 2.1 IEEE 802.1AS — 时间同步（gPTP）

**核心问题**：要实现"准时"，首先所有设备得有一个共同的时间基准。

802.1AS 是 IEEE 1588 PTP 的一个子集（profile），专门为 TSN 网络定义了精密时间同步机制。它被称为 gPTP（generalized PTP），与通用 PTP 的主要区别是：仅支持一步（one-step）和两步（two-step）同步、仅使用端到端路径延迟测量（peer-delay）、强制硬件时间戳。

工作原理可以用"对表"来类比：网络中选出一个"最准的表"（Grand Master Clock），其他设备（slaves）通过交换带时间戳的消息来计算自己和 master 之间的时间偏差和路径延迟，然后不断微调自己的时钟。802.1AS-2020 修订版增加了多域时间同步（多个独立的时间域可以共存）和热备份 Grand Master 支持。

典型精度：在支持硬件时间戳的交换机上，802.1AS 可以实现 **<1 微秒** 的全网时间同步精度，每跳增加约 10-50 纳秒的误差累积。

### 2.2 IEEE 802.1Qbv — 时间感知整形器（TAS）

**核心问题**：如何保证高优先级流量在精确的时间窗口内通过交换机？

802.1Qbv 是 TSN 中最核心的流量调度标准。它引入了"门控列表"（Gate Control List, GCL）的概念：交换机的每个出端口有 8 个优先级队列，每个队列都有一个"门"（gate），门可以在预定的时间点打开或关闭。

打个比方：这就像一条高速公路上的定时红绿灯。在 t=0 到 t=50μs 的时间窗口内，只有"紧急车道"（高优先级队列）的门是打开的，其他车道的门关闭——这意味着在这段时间内，只有控制流量可以通过，所有 IT 流量（邮件、视频等）必须等待。到了 t=50μs 到 t=1000μs 的窗口，IT 流量的门才打开。

802.1Qbv 的效果是把以太网的"尽力而为"变成了"时分复用"——不同优先级的流量被安排在不同的时间槽内传输，相互之间零干扰。配合 802.1AS 的全网时间同步，每个交换机的门控列表可以精确协调，形成端到端的"绿波通道"。

关键性能指标：在标准千兆以太网上，802.1Qbv 可以将关键流量的端到端延迟保证在 **数十微秒到低毫秒** 级别，抖动控制在 **<1 微秒**。

### 2.3 IEEE 802.1Qbu/802.3br — 帧抢占

**核心问题**：如果一个低优先级的大包正在传输过程中，突然来了一个高优先级的小包怎么办？

在没有帧抢占的传统以太网中，必须等大包传完才能发小包。一个 1518 字节的以太网帧在千兆网络上需要约 12 微秒传输——如果控制指令正好在这时到达，就要白白等 12 微秒。

802.1Qbu（MAC 层帧抢占）和 802.3br（物理层帧抢占）解决了这个问题：允许高优先级帧打断正在传输的低优先级帧。被打断的帧会被分成片段（fragment），每个片段有自己的 CRC，接收端可以重新组装。

这就像救护车可以让前面的社会车辆靠边让路：低优先级帧被"暂停"（而非丢弃），等高优先级帧传完后再继续。帧抢占与 802.1Qbv 配合使用时，可以进一步降低保护带（guard band）的大小，提高带宽利用率。

### 2.4 IEEE 802.1CB — 帧复制与消除（FRER）

**核心问题**：关键帧在传输路径上丢了怎么办？

802.1CB 通过"双发选收"（frame replication and elimination for reliability）实现零丢包保证。发送端将同一帧复制两份（或多份），沿不同的物理路径发送。接收端根据序列号选择先到的帧、丢弃重复帧。

这和航空领域的"双冗余飞控"思路一致：两条独立链路同时传输，只要有一条通就不会丢。802.1CB 可以实现 **切换时间为 0** 的无损冗余（与传统 RSTP 的秒级切换形成鲜明对比）。

### 2.5 其他重要 TSN 标准

| 标准 | 功能 | 一句话说明 |
|------|------|-----------|
| 802.1Qcc | 流预留协议增强 | 集中式/分布式/混合三种 TSN 配置模型 |
| 802.1Qci | 每流过滤与策略 | 入口处检查流是否符合预约的带宽/突发规格 |
| 802.1Qcr | 异步流量整形(ATS) | 无需全网时间同步的确定性整形（Credit-Based + 紧急度） |
| 802.1Qch | 循环排队转发(CQF) | 用循环缓冲区简化 Qbv 的门控调度 |
| 802.1Qdj | TSN 配置增强 | 集中式网络配置(CNC)的 YANG 数据模型 |

## 3 DetNet：将确定性从 L2 扩展到 L3

TSN 工作在二层（以太网），而 IETF 的 DetNet（Deterministic Networking，RFC 8655）将确定性的概念扩展到了三层（IP 网络）及以上。

### 3.1 DetNet 架构

DetNet 架构定义了三个层面：

**服务层面（Service Sub-layer）**：提供 DetNet 流的端到端服务保障，包括流的建立、维护和拆除。DetNet 流通过六元组（源地址、目的地址、协议、源端口、目的端口、DSCP）标识。

**转发层面（Forwarding Sub-layer）**：负责数据包在 DetNet 域内的转发。支持 MPLS 和 IPv6 两种数据面技术。DetNet-over-MPLS 使用 MPLS 标签栈标识 DetNet 流；DetNet-over-IPv6 使用 SRv6（Segment Routing over IPv6）。

**数据面（Data Plane）**：复用 802.1CB 的 FRER 机制实现冗余保护，复用 802.1Qbv/ATS 等 TSN 整形机制保证有界延迟。

### 3.2 DetNet 与 TSN 的关系

DetNet 不是要替代 TSN，而是在更高层面上统一管理。一个典型的工业网络中：车间内部用 TSN（L2）提供微秒级确定性，车间之间或跨厂区用 DetNet（L3/MPLS）提供毫秒级确定性，两者通过 DetNet-TSN 互通接口衔接。

| 对比维度 | TSN (IEEE 802.1) | DetNet (IETF) |
|----------|-----------------|---------------|
| 网络层次 | L2（以太网） | L3（IP/MPLS） |
| 覆盖范围 | 局域网（同一 L2 域） | 广域网（跨 L3 域） |
| 典型延迟保证 | 数十微秒 ~ 低毫秒 | 毫秒 ~ 数十毫秒 |
| 时间同步 | 802.1AS（强制） | 可选（取决于子网技术） |
| 冗余机制 | 802.1CB FRER | 复用 802.1CB 或 DetNet PREOF |
| 配置模型 | CNC（集中网络控制器） | DetNet 控制器 + YANG 模型 |
| 数据面 | 以太网帧 | MPLS 或 SRv6 |
| 标准化状态 | 核心标准已发布 | 架构(RFC 8655)已发布，数据面规范持续演进 |

## 4 5G + TSN 融合

5G 的 URLLC（Ultra-Reliable Low-Latency Communication）能力与 TSN 的确定性需求天然互补：TSN 在有线网络中提供确定性，5G 在无线接入中提供确定性，两者融合可以实现端到端的工业级确定性通信。

### 4.1 3GPP 5G-TSN 集成架构

3GPP 在 Release 16（2020）中首次引入了 5G 与 TSN 的集成架构。核心思想是将 5G 系统（包括 UE、gNB、UPF）"伪装"成一个 TSN 交换机（Logical TSN Bridge）：

从 TSN 网络的视角看，5G 无线链路就像一个透明的以太网交换机，具有已知的（但时变的）延迟和抖动特性。TSN 网络的 CNC（集中网络控制器）可以像管理普通 TSN 交换机一样管理这个 5G "虚拟交换机"。

5G 系统通过 AF（Application Function）向 CNC 暴露自己的时间同步能力、可用带宽和延迟特性。CNC 据此计算全网的门控调度（GCL），并将 5G 段的 QoS 需求通过 NEF/PCF 下发到 5G 核心网。

### 4.2 关键挑战

5G+TSN 融合面临的最大挑战是**5G 无线链路的延迟抖动**。有线 TSN 的单跳延迟抖动可以控制在纳秒级，而 5G 的无线链路延迟受信道条件、调度周期等影响，抖动在百微秒级。3GPP 通过以下手段缓解：

- **时间感知调度（Time-Aware Scheduling）**：5G gNB 根据 TSN GCL 对齐自己的调度时间
- **包延迟预算（Packet Delay Budget）**：为 TSN 流预留确定的空口资源
- **5G 时钟同步**：5G 系统可以作为 802.1AS 的 Relay，实现跨有线/无线的时间同步，精度目标 <1μs（Release 16）到 <500ns（Release 17/18）

2024 年 IEEE TSN/DetNet Working Group 的联合报告显示，5G Release 17/18 的实验室测试中，5G+TSN 端到端延迟可控制在 **5-10ms** 以内，满足大部分工厂自动化场景需求（运动控制等超低延迟场景除外）。

## 5 工业应用场景与性能实测

### 5.1 工厂自动化

工厂自动化是 TSN 最典型的应用场景，涵盖从运动控制到过程监控的多种需求层次：

| 应用类型 | 周期时间 | 延迟要求 | 抖动要求 | 可靠性 |
|----------|----------|----------|----------|--------|
| 运动控制（Motion Control） | 250μs ~ 1ms | <1ms | <1μs | 99.9999% |
| 离散控制（PLC ↔ I/O） | 1ms ~ 10ms | <10ms | <10μs | 99.999% |
| 过程控制（温度/压力） | 10ms ~ 100ms | <100ms | <1ms | 99.99% |
| HMI/SCADA 可视化 | 100ms ~ 1s | <1s | 不敏感 | 99.9% |
| 非关键 IT 流量（日志/邮件） | 尽力而为 | 无保证 | 无保证 | 尽力而为 |

TSN 的核心价值是这些流量可以**在同一张以太网上共存**，而不需要像过去那样为控制网络和 IT 网络分别建设独立的物理基础设施（即 IT/OT 融合）。

2024 年 Huawei 和 Siemens 联合发表的测试报告显示，在 10 跳千兆 TSN 网络中：关键控制流量的端到端延迟 <100μs（确定性上界），同时 IT 流量（视频监控）以 200Mbps 带宽共存。这一结果验证了 TSN 在实际工厂环境中的可行性。

### 5.2 汽车车载网络

汽车电子架构正从分布式 ECU 向"域控制器 + 高速骨干网"转变。TSN 被定位为下一代车载骨干网技术：

- 自动驾驶传感器数据（摄像头、LiDAR 点云）需要高带宽（Gbps 级）
- 底盘控制（制动、转向）需要确定性低延迟（<1ms）
- 信息娱乐系统需要适度的 QoS 保证

IEEE 802.1DG（TSN Profile for Automotive In-Vehicle Ethernet）定义了车载 TSN 的配置文件。2024 年多家车企（BMW、Continental、NXP）发布了量产级 TSN 交换机芯片，支持 802.1AS、802.1Qbv 和 802.1CB。

## 6 TSN vs 传统工业以太网对比

在 TSN 出现之前，工业界已有多种专用工业以太网方案。TSN 的目标是以开放标准替代这些"碎片化"的专有方案：

| 对比维度 | TSN | PROFINET IRT | EtherCAT | POWERLINK | CC-Link IE TSN |
|----------|-----|-------------|----------|-----------|---------------|
| 标准组织 | IEEE | Siemens/PI | Beckhoff/ETG | EPSG | CLPA |
| 兼容标准以太网 | 完全兼容 | 部分兼容 | 需专用硬件 | 需专用调度 | 兼容(基于TSN) |
| 最小周期时间 | ~31.25μs | 31.25μs | ~12.5μs | 200μs | 31.25μs |
| 最大网络规模 | 理论无限制 | ~150 节点 | ~65535 节点 | ~240 节点 | ~128 节点 |
| 带宽 | 100M/1G/10G/25G | 100M/1G | 100M | 100M | 1G |
| 冗余切换时间 | 0μs (802.1CB) | ~0μs (MRP) | ~0μs | ~0μs | 0μs |
| 多厂商互操作 | 高（开放标准） | 中（需认证） | 中（需认证） | 低 | 高（基于TSN） |
| 与 IT 网络融合 | 原生支持 | 需网关 | 需网关 | 需网关 | 原生支持 |
| 5G 集成 | 3GPP 标准化 | 无 | 无 | 无 | 继承 TSN |

从表中可以看出，TSN 的最大优势不是性能（EtherCAT 在极低周期时间上甚至更快），而是**开放性和融合能力**。TSN 可以让 OT（操作技术）和 IT（信息技术）在同一张网上和平共处，而传统工业以太网需要在 OT 和 IT 之间放网关。

值得注意的是，CC-Link IE TSN 是第一个直接建立在 TSN 之上的工业协议，由三菱电机主导的 CLPA 联盟推动。这代表了工业以太网从"私有标准"向"TSN+应用层协议"的演进方向。

## 7 部署实践与工具链

### 7.1 TSN 配置模型

802.1Qcc 定义了三种 TSN 网络配置模型：

**全分布式（Fully Distributed）**：每个终端和交换机通过 SRP/RAP 协议自行协商流的预留。简单但功能有限，只能做基于优先级的保证。

**集中式网络/分布式用户（Centralized Network / Distributed User）**：CNC 集中计算网络调度，终端通过 SRP 向网络请求资源。适合中等规模网络。

**全集中式（Fully Centralized）**：CUC（Centralized User Configuration）+ CNC 共同管理。终端向 CUC 报告需求，CUC 汇总后交给 CNC 计算全局调度，再下发到所有交换机。适合大规模工业部署，也是目前主流方案。

### 7.2 开源与商业工具

TSN 生态在 2024-2025 年快速成熟：

Linux 内核从 5.x 版本开始支持 taprio（802.1Qbv 的 Linux 实现）、etf（最早截止时间优先调度）和 mqprio（多队列优先级映射）。Intel 的 i210/i225/i226 网卡和 NXP 的 SJA1105 交换机芯片提供硬件 TSN 支持。

开源工具方面：OpenTSN 是国内清华大学团队主导的开源 TSN 协议栈，DepVeri（Dependency Verification）工具可以验证 GCL 配置的正确性。Industrial Automation 领域，OPC UA over TSN（OPC UA Pub/Sub + TSN 传输）正在成为事实标准组合。

## 8 2024-2025 年前沿动态

**IEEE 802.1Qdj（2024）**：完善了 CNC 的 YANG 数据模型和 RESTCONF 接口，使 TSN 配置更易于自动化和 SDN 集成。

**P802.1ASdm（修订中）**：增强 802.1AS 的多域同步和时钟恢复能力，目标是支持 <100ns 的广域同步精度。

**DetNet Scaling（IETF, 2024-2025）**：IETF DetNet 工作组正在解决大规模 DetNet 部署的可扩展性问题，包括分层 DetNet 域和域间互通。

**AI-assisted TSN Scheduling（2024 IEEE RTSS）**：利用深度强化学习自动生成门控列表（GCL），在大规模网络中优化带宽利用率和调度可行性，相比传统 SMT/ILP 求解器在计算时间上降低了 2-3 个数量级。

## 9 总结

TSN 和 DetNet 共同构成了工业物联网确定性通信的技术基础。TSN 在二层以太网上实现了微秒级的确定性保障，通过时间同步（802.1AS）、时间感知整形（802.1Qbv）、帧抢占（802.1Qbu）和无缝冗余（802.1CB）四大核心机制，将"尽力而为"的以太网升级为可用于工业控制的确定性网络。DetNet 则将这种确定性从局域网扩展到了广域 IP/MPLS 网络。

5G+TSN 融合是当前最具前景的方向之一，3GPP Release 16-18 逐步完善了 5G 作为"逻辑 TSN 交换机"的能力。虽然无线链路的固有抖动使其暂时无法满足运动控制等极低延迟场景（<1ms），但已能覆盖大部分工厂自动化需求（5-10ms 级别）。

展望未来，TSN 的趋势是从"工业专用"走向"全场景通用"：汽车（车载骨干网）、电力（智能变电站）、航空航天、轨道交通等行业都在加速采纳 TSN。而 AI 辅助的自动化调度、OPC UA over TSN 的标准化、以及 TSN 硬件成本的持续下降，将进一步加速这一进程。

## 参考文献

1. IEEE 802.1AS-2020. Timing and Synchronization for Time-Sensitive Applications. IEEE, 2020.
2. IEEE 802.1Qbv-2015. Enhancements for Scheduled Traffic. IEEE, 2015.
3. IEEE 802.1Qbu-2016. Frame Preemption. IEEE, 2016.
4. IEEE 802.1CB-2017. Frame Replication and Elimination for Reliability. IEEE, 2017.
5. Finn, N., et al. "Deterministic Networking Architecture." RFC 8655, IETF, 2019.
6. 3GPP TR 23.734. Study on 5GS Enhanced Support for Vertical and LAN Services. Release 16, 2020.
7. Nasrallah, A., et al. "Ultra-Low Latency (ULL) Networks: The IEEE TSN and IETF DetNet Standards and Related 5G ULL Research." IEEE Communications Surveys & Tutorials, 2019.
8. Cavalcanti, D., et al. "Extending Accurate Time Distribution and Timeliness Capabilities over the Air for Enabling Future Wireless Industrial Automation." Proceedings of the IEEE, 2019.
9. Seol, Y., et al. "AI-Assisted TSN Gate Control List Scheduling Using Deep Reinforcement Learning." IEEE RTSS, 2024.
10. Gogolev, A., et al. "TSN-Enabled 5G for Industrial IoT: Experimental Evaluation." IEEE Access, 2024.
11. OPC Foundation. OPC UA over TSN: A Joint White Paper. 2023.
12. Wisniewski, L., et al. "Comparison of Industrial Ethernet Solutions: PROFINET, EtherCAT, and TSN." IEEE Industrial Electronics Magazine, 2024.