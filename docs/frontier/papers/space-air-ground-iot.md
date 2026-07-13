---
schema_version: '1.0'
id: space-air-ground-iot
title: 天地一体化 IoT 网络
layer: 8
content_type: technical_analysis
difficulty: advanced
reading_time: 32
prerequisites:
  - satellite-iot
  - satellite-iot-leo-connectivity
tags:
- SAGIN
- LEO
- NTN
- 卫星物联网
- UAV
- HAP
- 天地一体化
- 3GPP
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 天地一体化 IoT 网络

> **难度**：🟠 进阶 | **领域**：卫星通信 × IoT × 异构网络 | **阅读时间**：约 32 分钟

## 一句话总结

天地一体化网络（Space-Air-Ground Integrated Network, SAGIN）将卫星、高空平台、无人机和地面网络融合为统一的物联网（Internet of Things, IoT）连接架构，目标是扩大覆盖并按业务选择合适层级。

## 为什么需要天地一体化？

### 地面网络的覆盖盲区

公开材料常指出：地球表面仅有一部分区域被地面移动网络有效覆盖，其余包括：

- 海洋（约占地球表面七成）
- 沙漠、极地、高山
- 偏远农村和森林
- 空中（商业航空高度）

而 IoT 需求恰恰遍布这些区域：远洋船舶追踪、野生动物监测、极地科考设备、管道泄漏检测、农业监测等。

### 日常类比

传统地面网络像城市里的路灯——覆盖了街道，但一旦离开城市（海洋、荒漠、天空），就完全黑暗了。

天地一体化网络则是一个"三层照明系统"：
- **地面路灯**（地面基站）：照亮城市和道路
- **无人机探照灯**（UAV/HAP）：灵活照亮应急区域
- **太空泛光灯**（卫星星座）：从太空覆盖广阔地表

三层协同，按需补盲。

## SAGIN 架构

### 四层异构网络

```
┌──────────────────────────────────────────┐
│           太空层 (Space Layer)             │
│  GEO (36,000km) / MEO / LEO (300-1500km) │
│  全球覆盖、长延迟、大容量回传             │
├──────────────────────────────────────────┤
│           空中层 (Air Layer)              │
│  HAP (20km) / UAV (0.1-10km)            │
│  区域覆盖、灵活部署、中等延迟             │
├──────────────────────────────────────────┤
│           地面层 (Ground Layer)            │
│  宏基站 / 小基站 / IoT 网关              │
│  热点覆盖、低延迟、大带宽                 │
├──────────────────────────────────────────┤
│           用户层 (User Layer)             │
│  IoT 设备 / 传感器 / 车辆 / 手机         │
└──────────────────────────────────────────┘
```

地球静止轨道（Geostationary Earth Orbit, GEO）、中地球轨道（Medium Earth Orbit, MEO）、低地球轨道（Low Earth Orbit, LEO）、高空平台（High Altitude Platform, HAP）与无人机（Unmanned Aerial Vehicle, UAV）构成异构拓扑；用户层设备按覆盖、时延、功耗与资费选择接入。

### 各层特征对比

| 维度 | GEO 卫星 | LEO 卫星 | HAP | UAV | 地面基站 |
|------|---------|---------|-----|-----|---------|
| 高度 | 约 36,000 km | 约 300–1,500 km | 约 20 km | 约 0.1–10 km | 0 |
| 覆盖半径 | 数千 km 量级 | 数百–千 km 量级 | 约 50–100 km | 约 1–10 km | 约 0.5–5 km |
| 往返延迟 | 约 600 ms 量级 | 约 5–40 ms 量级 | 通常 <1 ms | 通常 <1 ms | 通常 <1 ms |
| 带宽（单用户） | 约 1–10 Mbps 量级 | 约 10–100 Mbps 量级 | 约 10–50 Mbps 量级 | 约 1–20 Mbps 量级 | 可达 100+ Mbps |
| 移动性 | 静止（同步轨道） | 快速移动（约 7.8 km/s） | 准静止 | 灵活机动 | 固定 |
| 部署时间 | 数年 | 数月–年 | 数小时 | 数分钟 | 数周–月 |
| 寿命 | 约 15–20 年 | 约 5–7 年 | 数月量级 | 数小时–天 | 约 10+ 年 |
| 成本/节点 | 很高 | 高 | 中高 | 相对低 | 中 |
| IoT 适用性 | 广覆盖低频次 | 中频次中延迟 | 应急/临时 | 灵活应急 | 高频次低延迟 |

上表为工程量级对照，具体星座、载荷与终端能力会显著改变数字。

## LEO 卫星星座 IoT

### 当前主要星座

| 星座 | 运营商 | 卫星数量(计划) | 轨道高度 | IoT 服务 | 状态（约 2025–2026） |
|------|--------|-------------|---------|---------|-----------|
| Starlink | SpaceX | 万级（远期更高） | 约 550 km | Direct-to-Cell 等 | 部分商用 |
| OneWeb | Eutelsat | 约 648 | 约 1,200 km | IoT 网关等 | 商用推进中 |
| Kuiper | Amazon | 约 3,236 | 约 590–630 km | 计划中 | 部署/测试阶段 |
| 天通/鸿雁等 | 中国相关 | 数百级规划 | 约 800–1,400 km | 卫星物联网 | 分阶段推进 |
| Iridium | Iridium | 66 | 约 780 km | IoT (SBD 等) | 商用 |
| Globalstar | Globalstar | 数十级 | 约 1,414 km | IoT/应急 | 商用 |
| Lacuna Space 等 | 多家 | 数十级规划 | 约 500 km 量级 | LoRa over satellite 等 | 试商用/试点 |

数量与状态变化快，应以运营商与监管公开信息为准。

### 卫星直连终端（Direct-to-Device）

近年热点方向：手机/IoT 设备以更少专用硬件直接连接卫星。

| 技术方案 | 代表 | 频段 | 终端要求 | 速率（量级） |
|---------|------|------|---------|------|
| 3GPP NTN (Rel-17+) | 标准化 | S/L 等 | 现有蜂窝芯片+软件/能力升级 | 视能力集，可到 Mbps 或更低 |
| AST SpaceMobile 等 | 商业星座 | 蜂窝频段等 | 强调兼容现有手机 | 公开演示为 Mbps 量级 |
| Starlink Direct-to-Cell | SpaceX 等合作 | 合作方蜂窝频段 | 现有手机 | 早期多为短信/低速数据 |
| Globalstar + Apple 等 | 消费电子 | L/S 等 | 特定机型 | 紧急消息类 |
| 卫星 IoT（NB-IoT NTN） | 多厂商 | S 等 | NB-IoT 能力升级 | 约百 Kbps 量级 |

**3GPP 非地面网络（Non-Terrestrial Network, NTN）**是标准化主线：

- Rel-17：基础 NR-NTN 与 IoT-NTN
- Rel-18：移动性、覆盖与效率增强
- Rel-19+：多波束、干扰管理、多层协同等持续增强

窄带物联网（Narrowband IoT, NB-IoT）NTN 适配重点在定时提前、HARQ 时序与省电，使电池供电终端能在大时延链路上工作。

## 跨层切换（Inter-Layer Handover）

### 切换场景

```
场景1：地面 -> 空中
  车辆驶出城市进入无覆盖区域 -> 切换到 LEO 卫星

场景2：空中 -> 空中
  LEO 卫星快速移动，波束覆盖区切换 -> 切换到下一颗卫星

场景3：空中 -> 地面
  船舶靠近港口 -> 从卫星切换到港口 5G 基站

场景4：无人机中继
  临时部署 UAV 填补覆盖空洞 -> 设备先连 UAV 再回传卫星
```

### 切换挑战对比

| 切换类型 | 主要挑战 | 典型切换时间（量级） | 中断时间目标（量级） |
|---------|---------|------------|------------|
| 地面同层（4G/5G） | 信号强度判断 | 约 50–100 ms | 常 <50 ms |
| 地面到卫星 | 传播延迟突变、频率切换 | 约 200–500 ms | 常希望 <200 ms |
| LEO 卫星间 | 卫星高速移动（数分钟级切换周期） | 约 100–300 ms | 常希望 <100 ms |
| 卫星到 UAV | 异构协议适配 | 约 300–800 ms | 场景依赖 |
| 多层协同切换 | 全局最优选择 | 复杂 | 场景依赖 |

### 预测性切换

LEO 轨道可预测，为切换准备提供独特优势：

```python
# LEO 卫星切换预测
def predict_handover(current_satellite, user_position, time):
    """基于轨道力学预测切换时机和目标卫星"""
    # LEO 卫星轨道完全可预测
    future_coverage = compute_coverage(current_satellite, time + delta_t)
    
    if user_position not in future_coverage:
        # 当前卫星即将离开，寻找下一颗
        next_satellite = find_best_visible_satellite(user_position, time + delta_t)
        trigger_handover_preparation(next_satellite)
        return next_satellite, time + delta_t - margin
    
    return None  # 不需要切换
```

机制上：星历 → 可见性窗口 → 提前测量/预配置 → 条件触发执行。可显著降低中断，但"零中断"仍受终端能力、波束边界与负载影响，不宜绝对化。

## IoT 应用场景

### 场景 1：远洋船舶监控

- 全球商船需要持续或准持续通信
- 传统 VSAT 资费通常较高
- LEO/专用卫星 IoT 更适合低频次遥测（位置、机舱状态、货舱温湿度、安全告警）
- 设计关键是：消息大小、上报周期与过顶窗口匹配

### 场景 2：全球资产追踪

- 集装箱、铁路车厢、航空货运的全球追踪
- 需求常为每数十分钟报告位置 + 状态
- 卫星 IoT 匹配：低频次、低数据量、广覆盖
- 市场规模随年份与统计口径变化大，应以最新市场报告为准

### 场景 3：精准农业

- 偏远农田可能无地面网络
- 监测：土壤湿度、气象、灌溉控制、作物健康
- 常见组合：田间传感器 --(LoRa)--> 网关 --(卫星)--> 云平台

### 场景 4：灾害应急

- 地震/洪水后地面网络可能瘫痪
- UAV 快速部署临时基站（分钟级）
- HAP 提供区域持续覆盖（小时级，视平台而定）
- 卫星保障回传不中断

### 场景 5：极地/深海科考

- 南极/北极科考站、部分深海系统
- 卫星链路常是主要或唯一远程通道
- 上行：环境监测与遥测；下行：指令与软件更新
- 需配合延迟容忍网络（Delay/Disruption Tolerant Networking, DTN）

## 关键技术挑战

### 1. 频谱共享与干扰管理

卫星与地面网络使用相邻或相同频段时，干扰管理是硬约束：

| 方法 | 原理 | 效果 | 复杂度 |
|------|------|------|--------|
| 频率分离 | 不同层用不同频段 | 干扰低 | 低（频谱效率差） |
| 动态频谱共享 | 按需分配频率 | 效率较高 | 高 |
| 波束零陷 | 卫星波束避开地面热点 | 中等 | 中 |
| 认知无线电 | 检测并避免已占用频段 | 中等 | 中 |
| NOMA | 非正交多址区分信号 | 潜力高 | 高 |

非正交多址（Non-Orthogonal Multiple Access, NOMA）在 NTN 中仍受功率差、信道估计误差与终端复杂度限制。

### 2. 传播延迟补偿

LEO 往返延迟约数毫秒到数十毫秒，与地面 5G 超低时延目标不同。3GPP NTN 常见适配：

- HARQ（Hybrid Automatic Repeat Request）时序调整（延长或限制反馈）
- 定时提前（Timing Advance, TA）预补偿
- 基于星历的传播延迟预测
- 自适应调度间隔

### 3. 多普勒频移

LEO 相对地面约 7.8 km/s，多普勒显著：

- S 频段（约 2 GHz）：最大约数十 kHz 量级
- Ka 频段（约 26 GHz）：最大约数百 kHz 量级

接收端/网络侧需频率预补偿，否则子载波正交性被破坏。补偿误差会直接抬高 BLER。

### 4. 能量受限

卫星 IoT 终端多为电池供电：

| 省电技术 | 原理 | 功耗影响（量级） |
|---------|------|---------|
| eDRX（扩展非连续接收） | 延长休眠周期 | 可大幅降低空闲功耗 |
| PSM（省电模式） | 深度休眠直到有数据 | 可达极低待机功耗 |
| 预调度唤醒 | 仅在卫星过顶窗口唤醒 | 避免无效监听 |
| 自适应调制 | 信道好时缩短空口时间 | 中等收益 |

扩展非连续接收（extended Discontinuous Reception, eDRX）与省电模式（Power Saving Mode, PSM）需与过顶可预测性联合设计，否则会错过接入窗口。

## 标准化进展

### 3GPP NTN 演进

| Release | 完成时间（约） | NTN 相关内容 |
|---------|---------|------------|
| Rel-17 | 2022 | 首版 NR-NTN/IoT-NTN，透明载荷等 |
| Rel-18 | 2024 | 移动性、覆盖、功耗等增强 |
| Rel-19 | 2025+ | 多层协同、干扰与能力扩展等 |
| Rel-20 | 后续 | 再生载荷、星上处理、AI-native 等方向 |

### ITU WRC-23 相关决议

2023 年世界无线电通信大会（World Radiocommunication Conference, WRC-23）推动了与卫星直连、IMT 频段用于 NTN 等相关的频谱讨论与协调；具体可用频段与共存条件以各国落地规则为准。

## 天地一体化 IoT 系统设计考量

### 协议栈适配

| 协议层 | 地面方案 | SAGIN 适配 |
|--------|---------|-----------|
| 应用层 | MQTT/CoAP | DTN + Store-and-Forward |
| 传输层 | TCP | QUIC / PEP（性能增强代理） |
| 网络层 | IP | 段路由（SRv6）+ 多路径 |
| 链路层 | 4G/5G NR | NTN 定制帧结构/定时 |
| 物理层 | OFDM | 更大子载波间隔 + 预补偿 |

### 路由策略

```
IoT 数据包路由决策树：
1. 地面网络可用且满足 QoS？ -> 走地面（通常最低延迟）
2. 地面不可用，UAV 在覆盖范围？ -> 走 UAV 中继
3. 都不可用，等待 LEO 卫星过顶？
   - 数据紧急（告警） -> 可走 GEO/即时链路（成本/时延权衡）
   - 数据非紧急 -> 存储等待 LEO 过顶（Store-and-Forward）
```

## 局限、挑战与可改进方向

### 1. 跨层切换与会话连续性不足

**局限**：地面–卫星–UAV 异构切换涉及定时、频偏、核心网锚点与应用层会话，IoT 小包场景下控制开销占比高，易出现短暂不可达。
**改进**：基于星历的预测性切换 + 多连接（dual connectivity）预配置；应用层默认 DTN；对告警类消息做多路径冗余发送。

### 2. 终端功耗与过顶窗口难匹配

**局限**：eDRX/PSM 与 LEO 可见窗口若不同步，会漏接或无效唤醒，抵消省电收益。
**改进**：终端侧维护简化星历/过顶表；网络下发唤醒窗口；按业务 SLA 选择 GEO 常在线 vs LEO 突发。

### 3. 频谱共存与监管碎片化

**局限**：D2D/NTN 与地面 IMT 共享频段时，干扰与国家许可差异导致全球终端难以一套射频打天下。
**改进**：按目标市场裁剪频段 SKU；波束级功率与空口占空比约束；在标准测试用例中固化共存场景。

### 4. 星上处理与回传瓶颈

**局限**：透明转发简单但频谱与时延效率有限；再生/星上计算能力与散热、辐射加固成本高。
**改进**：先对 IoT 小包做星上汇聚/过滤再回传；区分控制面与用户面卸载；用数字孪生评估再生载荷收益。

### 5. 安全与供应链信任

**局限**：跨多层异构链路扩大攻击面（假星历、干扰、网关劫持），且供应链跨国。
**改进**：星历与系统信息完整性保护；终端互认证与密钥分层；关键遥测走端到端加密并做异常流量检测。

## 实践建议

- **先定业务画像**：上报周期、消息大小、最大可容忍时延，再选 GEO/LEO/地面
- **默认 DTN**：广域 IoT 不要假设端到端始终在线
- **功耗按窗口设计**：把过顶表写进固件测试用例
- **切换要可观测**：记录层间切换原因码与中断时长，避免黑盒劣化
- **合规先行**：频段与功率以目标国许可为准，实验室指标不能替代入网

## 参考文献

[1] J. Liu et al., "Space-Air-Ground Integrated Network: A Survey," IEEE Communications Surveys & Tutorials, 2024.
[2] 3GPP, "Solutions for NR to support non-terrestrial networks (NTN)," TR 38.821, 2024.
[3] X. Lin et al., "5G-Advanced and 6G NTN: Toward Ubiquitous 3D Connectivity," IEEE Communications Magazine, 2024.
[4] M. Giordani et al., "Non-Terrestrial Networks in the 6G Era: Challenges and Opportunities," IEEE Network, 2024.
[5] Y. Su et al., "LEO Satellite IoT: Architecture, Protocols, and Performance Analysis," IEEE Internet of Things Journal, 2024.
[6] Z. Qu et al., "Handover Management in LEO Satellite Networks: A Machine Learning Approach," IEEE Transactions on Wireless Communications, 2024.
[7] AST SpaceMobile, "Commercial Direct-to-Device Broadband from Space: First Results," White Paper, 2024.
[8] K. An et al., "UAV-Satellite Cooperative Communication for IoT: Resource Optimization and Protocol Design," IEEE Transactions on Vehicular Technology, 2024.
[9] ITU-R, "WRC-23 Final Acts: Decisions on Non-Terrestrial IMT," International Telecommunication Union, 2023.
[10] H. Chen et al., "Integrated LEO Satellite and Terrestrial 6G Networks: Architecture and Key Technologies," Science China Information Sciences, 2024.
[11] R. Rinaldo et al., "Non-Geostationary Satellite IoT Systems: Technology Evolution and Market Outlook," IEEE Aerospace and Electronic Systems Magazine, 2024.
[12] 3GPP, "NB-IoT/eMTC support for Non-Terrestrial Networks," related Rel-17/18 specifications, 2022–2024.
