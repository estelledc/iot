---
schema_version: '1.0'
id: ris-intelligent-surface
title: RIS 智能超表面
layer: 8
content_type: UNKNOWN
difficulty: advanced
reading_time: 30
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# RIS 智能超表面

> **难度**：🟠 进阶 | **领域**：无线通信 × 可编程电磁环境 | **阅读时间**：约 30 分钟

## 一句话总结

可重构智能超表面（Reconfigurable Intelligent Surface, RIS）是一种由大量可编程反射元件组成的"电磁镜子"，能智能调控无线信号的反射方向，将无线环境从"不可控"变为"可编程"。

## 从"适应环境"到"改造环境"

### 日常类比

传统无线通信像在一个布满障碍物的房间里喊话——你只能提高音量（增加发射功率）或换个位置（调整天线），但墙壁怎么反射你的声音，你无法控制。

RIS 相当于在墙上贴满了"智能声学瓷砖"，每块瓷砖都能独立调整角度。当你说话时，这些瓷砖协同工作，把你的声音精确地反射到听者的位置——即使你们之间隔着障碍物。

### 为什么现在需要 RIS？

随着 5G/6G 向毫米波和太赫兹频段演进，信号衰减急剧增加：

| 频段 | 路径损耗（100m） | 穿墙损耗 | 覆盖问题 |
|------|----------------|---------|---------|
| Sub-6GHz | 80 dB | 10-15 dB | 可接受 |
| mmWave (28GHz) | 110 dB | 25-40 dB | 严重遮挡 |
| mmWave (60GHz) | 128 dB | 35-50 dB | 极度受限 |
| THz (0.3THz) | 145 dB | >50 dB | 仅视距 |

高频段信号"怕墙怕雨怕人体"，覆盖空洞严重。传统解决方案（部署更多基站或中继）成本高昂。RIS 以极低功耗（无需射频链路）创造可控反射路径，成本仅为中继的 1/10。

## 超表面物理原理

### 电磁超材料基础

RIS 基于**超材料（Metamaterial）**概念——通过人工设计的亚波长结构单元实现自然材料不具备的电磁响应。

每个 RIS 单元（元素）的核心是一个可调谐的谐振结构：
- **尺寸**：亚波长（通常 λ/5 到 λ/2）
- **材料**：PCB 基板 + 金属贴片 + 可调元件（PIN 二极管/变容管/液晶）
- **功能**：通过改变偏置电压，调整反射信号的相位（0 到 2π）

### 反射相位调控

当电磁波入射到 RIS 时，每个元素独立调整反射相位：

```
入射波  →  ┌─────────────────────┐  →  反射波（可控方向）
            │ ϕ₁  ϕ₂  ϕ₃ ... ϕₙ │
            │ RIS 面板 (N个元素)   │
            └─────────────────────┘
            
相位梯度决定反射方向：
θ_reflect = arcsin(sinθ_incidence + λ/(2π) · dϕ/dx)
```

通过精心设计相位分布（codebook），RIS 可以实现：
- **镜面反射**：改变反射角度
- **聚焦**：将信号聚焦到特定位置
- **分束**：同时服务多个方向
- **异常反射**：反射到非镜面方向

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

### RIS 类型对比

| 类型 | 原理 | 相位分辨率 | 功耗 | 成本 | 成熟度 |
|------|------|-----------|------|------|--------|
| PIN 二极管型 | 1-bit 开关 | 1-2 bit（0°/180°） | 极低 | 低 | 高 |
| 变容管型 | 连续调谐 | 多 bit（近连续） | 低 | 中 | 中 |
| 液晶型 | 液晶相移 | 连续 | 中 | 高 | 低 |
| MEMS 型 | 机械调谐 | 连续 | 极低 | 高 | 低 |
| 相变材料型 | 非易失相位 | 多 bit | 0（保持态） | 高 | 实验室 |

**PIN 二极管型**最成熟，已有商用原型。虽然只有 1-bit 相位分辨率（0° 或 180°），但大规模阵列（256-1024 个元素）仍可实现有效波束赋形。

## 被动波束赋形

### 与传统有源波束赋形的对比

| 维度 | 有源波束赋形（Massive MIMO） | 被动波束赋形（RIS） |
|------|---------------------------|-------------------|
| 工作方式 | 天线阵列主动发射 | 反射面被动反射 |
| 射频链路 | 每天线需 1 条 RF chain | 无 RF chain |
| 功耗 | 高（每链路数瓦） | 极低（mW 级控制电路） |
| 信号增益 | O(N)（天线数） | O(N²)（元素数的平方） |
| 硬件成本 | 高（ADC/DAC/PA/LNA） | 低（PCB + 二极管） |
| 全双工 | 需要自干扰消除 | 天然全双工（反射） |
| 部署灵活性 | 固定在基站 | 贴墙/贴天花板/可移动 |

**关键优势**：RIS 的阵列增益与元素数 N 的平方成正比（因为反射的路径损耗补偿效果），这意味着增加元素数量的收益非常显著。

### 波束赋形优化

RIS 被动波束赋形的数学核心是**相位优化**：

**目标**：最大化接收端信号功率（或 SINR）
**变量**：N 个 RIS 元素的反射相位 θ₁, θ₂, ..., θₙ
**约束**：|e^(jθᵢ)| = 1（恒模约束）；离散相位约束（1-bit 时为 0/π）

对于单用户场景，最优解是让所有反射路径相干叠加：
θᵢ* = -arg(hᵢ) - arg(gᵢ)

其中 hᵢ 是基站到 RIS 第 i 元素的信道，gᵢ 是 RIS 第 i 元素到用户的信道。

## 信道估计：RIS 的核心挑战

### 为什么 RIS 信道估计困难？

传统 MIMO 信道估计靠发送导频信号。但 RIS 是**被动设备**——它不能发射导频，也没有接收链路来估计信道。

需要估计的信道：
- 基站 → RIS（G 矩阵，M×N）
- RIS → 用户（h 向量，N×1）
- 直射路径：基站 → 用户

总参数量：M×N + N + M，当 N=256, M=64 时达到 16,000+，传统方法导频开销巨大。

### 主流解决方案

| 方案 | 原理 | 导频开销 | 精度 | 复杂度 |
|------|------|---------|------|--------|
| ON/OFF 协议 | 逐个开关 RIS 元素 | O(N) | 高 | 低但慢 |
| 分组估计 | 将元素分组，组内相同相位 | O(N/G) | 中 | 中 |
| 压缩感知 | 利用信道稀疏性 | O(K log N) | 高 | 高 |
| 深度学习 | 端到端学习信道映射 | O(少量导频) | 中-高 | 训练高，推理低 |
| 双时间尺度 | 快时间尺度估计用户端 | 大幅降低 | 中 | 中 |
| 元素共享 | 部分 RIS 元素带传感 | 少量 | 高 | 硬件改造 |

**双时间尺度方案**是目前最实用的折中：
- 慢时间尺度：估计 G（基站→RIS），变化缓慢（RIS 固定部署）
- 快时间尺度：只估计 h（RIS→用户），开销与用户数成正比

## 硬件原型与实测

### 代表性原型系统

| 原型 | 团队 | 规模 | 频段 | 成果 |
|------|------|------|------|------|
| RISnet 2.0 | 清华大学 | 2304 元素 | 5.8GHz | 室外 200m 覆盖增强 15dB |
| LAIA-RIS | NTT DoCoMo | 768 元素 | 28GHz | 非视距覆盖，速率提升 10x |
| Greenerwave | 法国初创 | 1600 元素 | 26GHz | 商用原型，2024 年商用 |
| Samsung RIS | 三星 | 256 元素 | 28GHz | 5G 毫米波覆盖验证 |
| 中兴 RIS | 中兴通讯 | 1024 元素 | 4.9GHz | Sub-6G 室内覆盖增强 |

### 实测性能数据

清华 RISnet 2.0 室外测试（2024）：

- 部署场景：校园 NLoS 场景，基站与用户被建筑物遮挡
- RIS 面板：2304 元素（48×48），1-bit 相位
- 无 RIS 时：接收信号强度 -85dBm，连接中断
- 有 RIS 时：接收信号强度 -70dBm，稳定连接
- 增益：约 15dB，相当于覆盖距离扩展 5.6 倍

## RIS 辅助 IoT 通信

### 场景 1：低功耗广域覆盖增强

大量 IoT 传感器部署在室内或地下，信号无法直接到达基站。RIS 部署在建筑物外墙，将室内泄漏信号增强并反射到基站方向。

### 场景 2：大规模接入

RIS 可以同时形成多个波束服务多个 IoT 设备。通过 SDMA（空分多址），一个 RIS 面板可同时服务的设备数与分束能力成正比（通常 4-8 个独立波束）。

### 场景 3：物理层安全

RIS 可以在增强合法接收方向信号的同时，在窃听者方向制造零陷（null），实现物理层安全通信。研究表明安全速率可提升 50-200%。

### 场景 4：无线能量传输（SWIPT）

RIS 可同时反射信息信号和能量信号到不同方向，使得通信和无线充电共用同一 RIS 面板。对能量受限的 IoT 设备尤为重要。

## 挑战与未来方向

### 近期挑战（2024-2026）

1. **标准化缺失**：3GPP 尚未将 RIS 纳入标准，仅处于 Study Item 阶段
2. **信道估计开销**：大规模 RIS 的信道估计仍是实用化瓶颈
3. **部署优化**：RIS 放置位置的最优选择缺乏系统方法论
4. **多 RIS 协同**：多个 RIS 面板协同工作时的干扰管理

### 长期方向

- **有源 RIS**：部分元素配备放大器，克服"双路径损耗"问题
- **STAR-RIS**：同时透射和反射，服务 RIS 两侧的用户
- **自持续 RIS**：集成能量收割，无需外部供电
- **AI-Native RIS**：RIS 控制器集成 AI 芯片，本地决策无需回传

## 参考文献

1. M. Di Renzo et al., "Reconfigurable Intelligent Surfaces: A New Frontier for 6G," IEEE Vehicular Technology Magazine, vol. 19, no. 1, pp. 21-30, 2024.
2. Q. Wu et al., "Intelligent Reflecting Surface-Aided Wireless Communications: A Tutorial," IEEE Transactions on Communications, vol. 72, no. 2, pp. 1234-1278, 2024.
3. X. Wei et al., "Channel Estimation for RIS-Assisted Wireless Communications: A Comprehensive Survey," IEEE Communications Surveys & Tutorials, vol. 26, no. 1, pp. 456-503, 2024.
4. S. Zeng et al., "RIS Prototyping and Field Trials: Lessons Learned," IEEE Communications Magazine, vol. 62, no. 4, pp. 86-92, 2024.
5. C. Pan et al., "Active RIS: A New Architecture for Coverage Extension," IEEE Journal on Selected Areas in Communications, vol. 42, no. 4, pp. 890-908, 2024.
6. H. Zhang et al., "STAR-RIS: Simultaneous Transmitting and Reflecting for Full-Space Coverage," IEEE Transactions on Wireless Communications, vol. 23, no. 7, pp. 7234-7250, 2024.
7. Z. Wang et al., "Multi-RIS Cooperative Communication: Deployment, Channel Estimation, and Beamforming," IEEE Transactions on Signal Processing, vol. 72, pp. 2890-2906, 2024.
8. Y. Liu et al., "RIS-Aided IoT Communications: Massive Access and Energy Efficiency," IEEE Internet of Things Journal, vol. 11, no. 14, pp. 24567-24583, 2024.
9. NTT DoCoMo, "Transparent RIS Prototype for 5G Advanced: Field Trial Results," NTT Technical Review, 2024.
10. Greenerwave, "Commercial RIS Deployment: First Pilot Results," White Paper, 2024.
