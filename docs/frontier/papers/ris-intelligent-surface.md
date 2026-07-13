---
schema_version: '1.0'
id: ris-intelligent-surface
title: RIS 智能超表面
layer: 8
content_type: technical_analysis
difficulty: advanced
reading_time: 30
prerequisites:
  - mimo-beamforming-iot-base-station
  - mimo-iot-applications
  - 6g-isac-iot
tags:
- RIS
- 可重构智能超表面
- 被动波束赋形
- 6G
- 毫米波
- 信道估计
- 物理层安全
- IoT覆盖
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# RIS 智能超表面

> **难度**：🟠 进阶 | **领域**：无线通信 × 可编程电磁环境 | **阅读时间**：约 30 分钟

## 一句话总结

可重构智能超表面（Reconfigurable Intelligent Surface, RIS）由大量可编程反射单元组成，能调控无线信号的反射相位/幅度，把无线传播环境从"只能适应"推进到"可部分编程"。

## 从"适应环境"到"改造环境"

### 日常类比

传统无线通信像在一个布满障碍物的房间里喊话——你只能提高音量（增加发射功率）或换个位置（调整天线），但墙壁怎么反射你的声音，你无法控制。

RIS 相当于在墙上贴满了"智能声学瓷砖"，每块瓷砖都能独立调整角度。当你说话时，这些瓷砖协同工作，把你的声音尽量反射到听者的位置——即使你们之间隔着障碍物。

### 为什么现在需要 RIS？

随着 5G/6G 向毫米波（mmWave）乃至太赫兹（THz）演进，自由空间与遮挡损耗显著上升：

| 频段 | 路径损耗（约 100 m，量级） | 穿墙损耗（量级） | 覆盖问题 |
|------|---------------------------|------------------|---------|
| Sub-6GHz | 较低 | 相对可接受 | 通常可管 |
| mmWave (~28 GHz) | 明显更高 | 遮挡敏感 | 易出现覆盖空洞 |
| mmWave (~60 GHz) | 更高 | 更敏感 | 强依赖视距/反射 |
| THz（约 0.3 THz） | 极高 | 极敏感 | 近距/视距为主 |

高频段对墙体、人体、降雨更敏感。传统补盲靠加密集基站或有源中继，成本与功耗高。RIS 以近似被动反射（控制电路功耗通常远低于有源射频链路）提供可控反射路径；相对有源中继的成本优势取决于面板规模、安装与运维，需按项目核算，不宜简单断言固定倍数。

## 超表面物理原理

### 电磁超材料基础

RIS 基于超材料（Metamaterial）思想：用亚波长人工结构实现自然材料少见的电磁响应。

每个 RIS 单元的核心是可调谐谐振结构：
- **尺寸**：亚波长（常见约 λ/5–λ/2）
- **材料**：PCB 基板 + 金属贴片 + 可调元件（PIN 二极管/变容管/液晶等）
- **功能**：改变偏置，调节反射相位（理想连续 0–2π；实际常量化）

### 反射相位调控

当电磁波入射到 RIS 时，各单元独立设置反射相位，形成相位梯度，从而偏折反射波束：

```
入射波  →  ┌─────────────────────┐  →  反射波（可控方向）
            │ ϕ₁  ϕ₂  ϕ₃ ... ϕₙ │
            │ RIS 面板 (N个元素)   │
            └─────────────────────┘
            
相位梯度决定反射方向（广义斯涅尔定律示意）：
θ_reflect = arcsin(sinθ_incidence + λ/(2π) · dϕ/dx)
```

通过设计相位码本（codebook），RIS 可实现：
- **镜面/偏折反射**：改变主反射方向
- **聚焦**：能量集中到目标区域
- **分束**：同时服务多方向
- **异常反射**：偏离几何光学镜面方向

实际面板还有幅度损耗、量化相位误差与互耦，波束方向图会偏离理想模型。

## RIS 硬件架构

### 典型 RIS 面板结构

```
┌─────────────────────────────────┐
│        控制层（FPGA/MCU）         │  ← 相位配置
├─────────────────────────────────┤
│     偏置网络（DC 供电线路）        │  ← 供电/控制信号
├─────────────────────────────────┤
│   可调元件层（PIN二极管/变容管）    │  ← 相位调节
├─────────────────────────────────┤
│      金属贴片层（辐射单元）        │  ← 电磁耦合
├─────────────────────────────────┤
│         介质基板（PCB）           │  ← 机械支撑
├─────────────────────────────────┤
│           接地层                  │  ← 反射
└─────────────────────────────────┘
```

控制链路本身需要供电与同步；"近被动"不等于零功耗，大规模面板的偏置网络与控制器仍需纳入能耗预算。

### RIS 类型对比

| 类型 | 原理 | 相位分辨率 | 功耗 | 成本 | 成熟度 |
|------|------|-----------|------|------|--------|
| PIN 二极管型 | 开关量化相位 | 1–2 bit（如 0°/180°） | 极低–低 | 低 | 相对高 |
| 变容管型 | 连续/准连续调谐 | 更高 | 低 | 中 | 中 |
| 液晶型 | 液晶相移 | 连续潜力 | 中 | 高 | 较低 |
| MEMS 型 | 机械调谐 | 连续潜力 | 极低保持 | 高 | 较低 |
| 相变材料型 | 非易失相位 | 多 bit 潜力 | 保持态可极低 | 高 | 实验室 |

**PIN 二极管型**最常见于原型：即便 1-bit 量化，在数百至数千单元阵列上仍可形成可用波束，但量化损失与旁瓣抬升需要在链路预算中计入。

## 被动波束赋形

### 与传统有源波束赋形的对比

| 维度 | 有源波束赋形（Massive MIMO） | 被动波束赋形（RIS） |
|------|---------------------------|-------------------|
| 工作方式 | 天线阵列主动发射/接收 | 反射面调控反射 |
| 射频链路 | 每通道常需 RF chain | 通常无完整 RF chain |
| 功耗 | 高（PA/ADC 等） | 控制电路为主，通常更低 |
| 信号增益 | 与天线数等相关 | 理想模型下可呈 N² 量级趋势（双跳路径） |
| 硬件成本 | ADC/DAC/PA/LNA 昂贵 | PCB + 二极管相对便宜 |
| 全双工 | 需自干扰管理 | 反射天然双向，但仍有控制与估计问题 |
| 部署灵活性 | 多固定于基站 | 可贴墙/天花板，选址关键 |

**关于 N² 增益**：在理想相位对齐、远场与忽略损耗的简化模型中，级联信道幅度可随单元数 N 近似线性叠加，功率呈 N² 趋势；实测会因量化、损耗、估计误差与几何遮挡打折扣。

### 波束赋形优化

单用户场景的直观最优：使各反射路径相干叠加。

θᵢ* ≈ −arg(hᵢ) − arg(gᵢ)

其中 hᵢ 为基站到第 i 单元信道，gᵢ 为第 i 单元到用户信道。多用户/干扰约束下转为非凸优化，常用交替优化、流形优化或基于码本的搜索。

| 优化目标 | 典型约束 | 常用方法 |
|----------|----------|----------|
| 最大化接收功率/SNR | 恒模相位、离散相位 | 相位对齐、量化投影 |
| 最大化最小用户速率 | 多用户干扰 | 交替优化、SDR 松弛 |
| 能效/覆盖折中 | 有限码本、切换时延 | 码本调度 + 测量反馈 |

## 信道估计：RIS 的核心挑战

### 为什么 RIS 信道估计困难？

传统 MIMO 靠收发两端导频。RIS 近被动：不能像有源节点那样方便发导频，也缺少完整接收机做本地估计。

需要估计的对象通常包括：
- 基站 → RIS（G，规模随天线数 M 与单元数 N 增长）
- RIS → 用户（h，长度 N）
- 直射路径：基站 → 用户

当 N 与 M 同时较大时，未知参数量迅速膨胀，导频开销成为实用化瓶颈。

### 主流解决方案

| 方案 | 原理 | 导频开销 | 精度 | 复杂度 |
|------|------|---------|------|--------|
| ON/OFF 协议 | 逐个/分组开关单元 | 随 N 增长 | 高潜力 | 慢 |
| 分组估计 | 组内同相位 | 随组数 | 中 | 中 |
| 压缩感知 | 利用稀疏/几何结构 | 可低于 O(N) | 条件好时高 | 高 |
| 深度学习 | 学习导频到信道映射 | 可较少 | 依赖数据 | 训练贵 |
| 双时间尺度 | 慢变 G + 快变用户侧 | 可显著降低 | 中 | 中 |
| 半被动传感 | 少量单元带接收 | 较少 | 高潜力 | 需改硬件 |

**双时间尺度**常作为工程折中：RIS 固定时，基站–RIS 信道变化较慢，可低频估计；用户侧快变分量更频繁更新。

## 硬件原型与实测

### 代表性原型系统（公开报道量级）

| 原型 | 团队 | 规模（量级） | 频段 | 报道成果（需核验原文） |
|------|------|--------------|------|------------------------|
| RISnet 等 | 高校团队 | 数千单元 | Sub-6 | 室外覆盖增强演示 |
| 运营商试验 | NTT DoCoMo 等 | 数百–上千 | mmWave | 非视距速率提升演示 |
| Greenerwave 等 | 初创 | 上千 | mmWave | 商用化推进 |
| 设备商试验 | 三星/中兴等 | 数百–上千 | Sub-6/mmWave | 覆盖增强验证 |

### 实测解读注意点

公开试验常报告十余 dB 量级的接收强度改善，但结果强烈依赖：
- 几何是否接近理想反射路径
- 有无直射、是否严格 NLoS
- 相位量化比特与校准质量
- 对照基线（无 RIS vs 随机相位 vs 优化相位）

因此不宜把单次试验增益外推为普遍覆盖倍数。

## RIS 辅助 IoT 通信

### 场景 1：低功耗广域覆盖增强

室内/地下传感器难直达基站时，可在外墙/走廊部署 RIS，把泄漏或绕射能量导向网关方向，降低终端重传与发射功率。

### 场景 2：大规模接入

RIS 可形成有限个空间波束，配合空分多址（Space Division Multiple Access, SDMA）服务多设备；可同时服务的流数受面板孔径、码本与信道正交性限制，通常远小于单元数 N。

### 场景 3：物理层安全

通过在合法用户方向相干增强、在窃听方向构造弱接收（甚至接近零陷），可提升保密速率；具体增益随几何与 CSI 质量变化，文献中报告范围很宽，部署前需场景化评估。

### 场景 4：无线能量传输（SWIPT）

同时无线信息与功率传输（Simultaneous Wireless Information and Power Transfer, SWIPT）场景下，RIS 可把能量波束与信息波束导向不同终端，缓解能量受限 IoT 的供能与通信矛盾，但仍受双跳损耗制约。

| IoT 场景 | RIS 作用 | 关键瓶颈 |
|----------|----------|----------|
| 室内传感器回传 | 补盲、降发射功率 | 安装位置与回程控制 |
| 厂房遮挡区 AGV | 动态波束跟随 | 跟踪时延与估计开销 |
| 物理层安全传感 | 定向增强/抑制 | CSI 与窃听者位置不确定性 |
| 射频供能标签 | 能量聚焦 | 双跳损耗与法规 EIRP |

## 挑战与未来方向

### 近期挑战（工程窗口）

1. **标准化**：3GPP 等对 RIS 仍以研究/早期立项为主，空口控制与测量框架未完全定型
2. **信道估计开销**：大规模面板仍是瓶颈
3. **部署优化**：位置、朝向、高度缺乏可复制方法论
4. **多 RIS 协同**：干扰、同步与归属控制复杂

### 长期方向

- **有源 RIS**：部分单元带放大，缓解双跳损耗
- **STAR-RIS**：同时透射与反射，服务面板两侧
- **自持续 RIS**：能量收集降低布线
- **AI-Native 控制**：本地推理减少回传

## 局限、挑战与可改进方向

### 1. 双跳路径损耗被理想模型低估

**局限**：基站–RIS–用户两段路损相乘，若几何不佳，即使 N 很大也难超过直连或有源中继。
**改进**：部署前做射线追踪/场地测量选址；优先保证 RIS 对基站近似视距；评估有源/半主动 RIS 仅用于深衰落点。

### 2. 信道估计与控制开销侵蚀增益

**局限**：为获得 CSI 消耗的导频、反馈与相位切换时间，可能吃掉吞吐与时延预算，对小包 IoT 尤甚。
**改进**：双时间尺度 + 码本波束扫描；对静止传感器用慢更新；控制面与数据面分离并压缩相位配置。

### 3. 1-bit 量化与互耦导致波束质量下降

**局限**：低成本 PIN 面板旁瓣高、指向误差大，多用户干扰抑制变差。
**改进**：在链路预算预留量化损失；关键场景升级 2-bit/变容；出厂与现场校准互耦与单元失效图。

### 4. 标准化与互操作缺失

**局限**：缺乏统一的 RIS 能力发现、测量上报与多厂商控制接口，难进运营商规模采购。
**改进**：跟进 3GPP Study/Work Item；先在园区私网用专有控制器验证 KPI；抽象"波束 ID + 测量"接口便于未来替换。

### 5. 安全与隐私新攻击面

**局限**：恶意控制 RIS 可操纵信道，实施窃听增强或拒绝服务；错误配置也可造成邻区干扰。
**改进**：控制信道鉴权与完整性保护；相位配置签名；异常波束/干扰监测与回滚到安全码本。

## 参考文献

[1] M. Di Renzo et al., "Smart Radio Environments Empowered by Reconfigurable Intelligent Surfaces: How It Works, State of Research, and The Road Ahead," IEEE Journal on Selected Areas in Communications, 2020.
[2] Q. Wu et al., "Intelligent Reflecting Surface-Aided Wireless Communications: A Tutorial," IEEE Transactions on Communications, 2021.
[3] X. Wei et al., "Channel Estimation for RIS-Assisted Wireless Communications: A Comprehensive Survey," IEEE Communications Surveys & Tutorials, 2024.
[4] S. Zeng et al., "RIS Prototyping and Field Trials: Lessons Learned," IEEE Communications Magazine, 2024.
[5] C. Pan et al., "An Overview of Signal Processing Techniques for RIS/IRS-Aided Wireless Systems," IEEE Journal of Selected Topics in Signal Processing, 2022.
[6] H. Zhang et al., "Intelligent Omni-Surfaces for Full-Dimensional Wireless Communications: Principles, Technology, and Implementation," IEEE Communications Magazine, 2022.
[7] Z. Wang et al., "Multi-RIS Cooperative Communication: Deployment, Channel Estimation, and Beamforming," IEEE Transactions on Signal Processing, 2024.
[8] Y. Liu et al., "Reconfigurable Intelligent Surfaces: Principles and Opportunities," IEEE Communications Surveys & Tutorials, 2021.
[9] NTT DoCoMo, "Transparent RIS Prototype for 5G Advanced: Field Trial Results," NTT Technical Review, 2024.
[10] Greenerwave, "Commercial RIS Deployment: First Pilot Results," White Paper, 2024.
[11] E. Basar et al., "Wireless Communications Through Reconfigurable Intelligent Surfaces," IEEE Access, 2019.
[12] C. Huang et al., "Reconfigurable Intelligent Surfaces for Energy Efficiency in Wireless Communication," IEEE Transactions on Wireless Communications, 2019.
