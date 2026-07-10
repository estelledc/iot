---
schema_version: '1.0'
id: space-air-ground-iot
title: 天地一体化 IoT 网络
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
# 天地一体化 IoT 网络

> **难度**：🟠 进阶 | **领域**：卫星通信 × IoT × 异构网络 | **阅读时间**：约 30 分钟

## 一句话总结

天地一体化网络（Space-Air-Ground Integrated Network, SAGIN）将卫星、高空平台、无人机和地面网络融合为统一的 IoT 连接架构，实现真正的"全球无死角"覆盖。

## 为什么需要天地一体化？

### 地面网络的覆盖盲区

一个令人惊讶的事实：地球表面只有约 20% 被移动网络覆盖。剩余 80% 包括：

- 海洋（地球表面的 71%）
- 沙漠、极地、高山
- 偏远农村和森林
- 空中（商业航空高度）

但 IoT 的需求恰恰遍布这些区域：远洋船舶追踪、野生动物监测、极地科考设备、管道泄漏检测、农业监测……

### 日常类比

传统地面网络像城市里的路灯——覆盖了街道，但一旦离开城市（海洋、荒漠、天空），就完全黑暗了。

天地一体化网络则是一个"三层照明系统"：
- **地面路灯**（地面基站）：照亮城市和道路
- **无人机探照灯**（UAV/HAP）：灵活照亮应急区域
- **太空泛光灯**（卫星星座）：从太空覆盖整个地球表面

三层协同，无处不亮。

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

### 各层特征对比

| 维度 | GEO 卫星 | LEO 卫星 | HAP | UAV | 地面基站 |
|------|---------|---------|-----|-----|---------|
| 高度 | 36,000 km | 300-1,500 km | 20 km | 0.1-10 km | 0 |
| 覆盖半径 | 数千 km | 数百-千 km | 50-100 km | 1-10 km | 0.5-5 km |
| 往返延迟 | 600ms | 5-40ms | <1ms | <1ms | <1ms |
| 带宽（单用户） | 1-10 Mbps | 10-100 Mbps | 10-50 Mbps | 1-20 Mbps | 100+ Mbps |
| 移动性 | 静止（同步轨道） | 快速移动（7.8km/s） | 准静止 | 灵活机动 | 固定 |
| 部署时间 | 数年 | 数月-年 | 数小时 | 数分钟 | 数周-月 |
| 寿命 | 15-20 年 | 5-7 年 | 数月 | 数小时-天 | 10+ 年 |
| 成本/节点 | 数亿美元 | 数百万美元 | 数十万美元 | 数千-万美元 | 数十万美元 |
| IoT 适用性 | 广覆盖低频次 | 中频次中延迟 | 应急/临时 | 灵活应急 | 高频次低延迟 |

## LEO 卫星星座 IoT

### 当前主要星座

| 星座 | 运营商 | 卫星数量(计划) | 轨道高度 | IoT 服务 | 状态(2025) |
|------|--------|-------------|---------|---------|-----------|
| Starlink | SpaceX | 12,000+(42,000) | 550 km | Direct-to-Cell | 部分商用 |
| OneWeb | Eutelsat | 648 | 1,200 km | IoT 网关 | 商用 |
| Kuiper | Amazon | 3,236 | 590-630 km | 计划中 | 测试阶段 |
| 天通/鸿雁 | 中国 | 300+ | 800-1,400 km | 卫星物联网 | 部分商用 |
| Iridium | Iridium | 66 | 780 km | IoT (SBD) | 商用 |
| Globalstar | Globalstar | 48 | 1,414 km | IoT/卫星应急 | 商用（iPhone） |
| Lacuna Space | Lacuna | 32(计划) | 500 km | LoRa over satellite | 试商用 |

### 卫星直连终端（Direct-to-Device）

2024-2025 年最热门的方向：普通手机/IoT 设备无需特殊硬件即可直接连接卫星。

| 技术方案 | 代表 | 频段 | 终端要求 | 速率 |
|---------|------|------|---------|------|
| 3GPP NTN (Rel-17) | 标准化 | S/L band | 现有4G/5G芯片+软件升级 | 1-10 Mbps |
| AST SpaceMobile | AST | 蜂窝频段 | 现有手机（无需改造） | 5-20 Mbps |
| Starlink Direct-to-Cell | SpaceX/T-Mobile | PCS频段 | 现有手机 | 短信/低速数据 |
| Globalstar+Apple | 苹果 | L/S band | iPhone 14+ | 紧急 SOS |
| 卫星 IoT（NB-IoT NTN） | 多厂商 | S band | NB-IoT 芯片升级 | 100+ Kbps |

**3GPP NTN（非地面网络）**是标准化核心：

- Rel-17（2022）：基础 NR-NTN 和 IoT-NTN 规范
- Rel-18（2024）：增强移动性、减少延迟、提升效率
- Rel-19（2025）：多波束、频段扩展、高级干扰管理

## 跨层切换（Inter-Layer Handover）

### 切换场景

当用户/设备在不同网络层之间移动时，需要无缝切换：

```
场景1：地面 -> 空中
  车辆驶出城市进入无覆盖区域 -> 切换到LEO卫星

场景2：空中 -> 空中
  LEO卫星快速移动，波束覆盖区切换 -> 切换到下一颗卫星

场景3：空中 -> 地面
  船舶靠近港口 -> 从卫星切换到港口5G基站

场景4：无人机中继
  临时部署UAV填补覆盖空洞 -> 设备先连UAV再回传卫星
```

### 切换挑战对比

| 切换类型 | 主要挑战 | 典型切换时间 | 中断时间目标 |
|---------|---------|------------|------------|
| 地面同层（4G/5G） | 信号强度判断 | 50-100ms | <50ms |
| 地面到卫星 | 传播延迟突变、频率切换 | 200-500ms | <200ms |
| LEO 卫星间 | 卫星高速移动（每5-10min切换） | 100-300ms | <100ms |
| 卫星到 UAV | 异构协议适配 | 300-800ms | <500ms |
| 多层协同切换 | 全局最优选择 | 复杂 | 场景依赖 |

### 预测性切换

LEO 卫星的轨道是确定性的（可预测），这为切换提供了独特优势：

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

由于轨道可预测，可以提前数十秒开始切换准备，实现"零中断切换"。

## IoT 应用场景

### 场景 1：远洋船舶监控

- 全球约 90,000 艘商船需要持续通信
- 传统 VSAT 成本高（$3,000-10,000/月）
- LEO IoT 方案：$10-50/月/设备，覆盖全球海域
- 数据类型：位置报告、发动机状态、货物温度、安全警报

### 场景 2：全球资产追踪

- 集装箱、铁路车厢、航空货运的全球追踪
- 需求：每 15-60 分钟报告一次位置 + 状态
- 卫星 IoT 完美匹配：低频次、低数据量、全球覆盖
- 市场规模：2025 年预计 2000 万连接

### 场景 3：精准农业

- 偏远农田无地面网络覆盖
- 需监测：土壤湿度、气象站、灌溉控制、作物健康
- 卫星 IoT + LoRa 网关组合方案：
  - 田间传感器 --(LoRa)--> 网关 --(卫星)--> 云平台
  
### 场景 4：灾害应急

- 地震/洪水后地面网络瘫痪
- UAV 快速部署临时基站（分钟级）
- HAP 提供区域持续覆盖（小时级）
- 卫星保障全球回传不中断

### 场景 5：极地/深海科考

- 南极/北极科考站、深海探测器
- 唯一通信方式：卫星链路
- 数据上传：环境监测数据、设备遥测
- 下行：远程控制指令、软件更新

## 关键技术挑战

### 1. 频谱共享与干扰管理

卫星与地面网络使用相邻或相同频段时，相互干扰严重。解决方案：

| 方法 | 原理 | 效果 | 复杂度 |
|------|------|------|--------|
| 频率分离 | 不同层用不同频段 | 无干扰 | 低（但浪费频谱） |
| 动态频谱共享 | 按需分配频率 | 高效 | 高 |
| 波束零陷 | 卫星波束避开地面热点 | 中等 | 中 |
| 认知无线电 | 检测并避免已占用频段 | 中等 | 中 |
| NOMA | 非正交多址区分信号 | 高效 | 高 |

### 2. 传播延迟补偿

LEO 卫星的往返延迟 5-40ms，与 5G 的 1ms 目标差距明显。3GPP NTN 的适配措施：

- HARQ 时序调整（禁用或延长反馈窗口）
- 定时提前（TA）预补偿
- 传播延迟预测（基于星历表）
- 自适应调度间隔

### 3. 多普勒频移

LEO 卫星相对地面移动速度 7.8km/s，产生显著多普勒频移：

- S 频段（2GHz）：最大约 48kHz
- Ka 频段（26GHz）：最大约 624kHz

必须在接收端进行频率预补偿，否则正交性被破坏。

### 4. 能量受限

卫星 IoT 终端通常由电池供电，需要极低功耗通信：

| 省电技术 | 原理 | 功耗降低 |
|---------|------|---------|
| eDRX（扩展非连续接收） | 延长休眠周期到数分钟 | 80-90% |
| PSM（省电模式） | 完全休眠直到有数据发送 | 95%+ |
| 预调度唤醒 | 仅在卫星过顶时唤醒 | 90%+ |
| 自适应调制 | 信道好时用高阶调制缩短传输时间 | 20-40% |

## 标准化进展

### 3GPP NTN 演进

| Release | 完成时间 | NTN 相关内容 |
|---------|---------|------------|
| Rel-17 | 2022 | 首版 NR-NTN/IoT-NTN，透明卫星中继 |
| Rel-18 | 2024 | 增强 NTN：移动性、覆盖增强、功耗优化 |
| Rel-19 | 2025 | NTN-NTN 卫星间链接、多层协同、MIMO |
| Rel-20 | 2026-2027 | 再生卫星、星上计算、AI-native NTN |

### ITU WRC-23 决议

2023 年世界无线电通信大会（WRC-23）的关键决定：
- 为卫星直连终端（D2D）识别新频谱
- 允许 IMT 频段用于 NTN（与地面共享）
- 推动全球频谱协调

## 天地一体化 IoT 系统设计考量

### 协议栈适配

| 协议层 | 地面方案 | SAGIN 适配 |
|--------|---------|-----------|
| 应用层 | MQTT/CoAP | DTN（延迟容忍网络）+ Store-and-Forward |
| 传输层 | TCP | QUIC/PEP（性能增强代理） |
| 网络层 | IP | 段路由（SRv6） + 多路径 |
| 链路层 | 4G/5G NR | NTN 定制帧结构 |
| 物理层 | OFDM | 大 subcarrier spacing + 预补偿 |

### 路由策略

```
IoT 数据包路由决策树：
1. 地面网络可用且满足 QoS？ -> 走地面（最低延迟）
2. 地面不可用，UAV 在覆盖范围？ -> 走 UAV 中继
3. 都不可用，等待 LEO 卫星过顶？
   - 数据紧急（告警） -> 走 GEO（即时但贵/慢）
   - 数据非紧急 -> 存储等待 LEO 过顶（Store-and-Forward）
```

## 参考文献

1. J. Liu et al., "Space-Air-Ground Integrated Network: A Survey," IEEE Communications Surveys & Tutorials, vol. 26, no. 2, pp. 1298-1345, 2024.
2. 3GPP TR 38.821, "Solutions for NR to Support Non-Terrestrial Networks," v17.2.0, 2024.
3. X. Lin et al., "5G-Advanced and 6G NTN: Toward Ubiquitous 3D Connectivity," IEEE Communications Magazine, vol. 62, no. 6, pp. 42-49, 2024.
4. M. Giordani et al., "Non-Terrestrial Networks in the 6G Era: Challenges and Opportunities," IEEE Network, vol. 38, no. 3, pp. 88-96, 2024.
5. Y. Su et al., "LEO Satellite IoT: Architecture, Protocols, and Performance Analysis," IEEE Internet of Things Journal, vol. 11, no. 16, pp. 27890-27908, 2024.
6. Z. Qu et al., "Handover Management in LEO Satellite Networks: A Machine Learning Approach," IEEE Transactions on Wireless Communications, vol. 23, no. 8, pp. 8901-8917, 2024.
7. AST SpaceMobile, "Commercial Direct-to-Device Broadband from Space: First Results," White Paper, 2024.
8. K. An et al., "UAV-Satellite Cooperative Communication for IoT: Resource Optimization and Protocol Design," IEEE Transactions on Vehicular Technology, vol. 73, no. 7, pp. 9876-9892, 2024.
9. ITU-R, "WRC-23 Final Acts: Decisions on Non-Terrestrial IMT," International Telecommunication Union, 2023.
10. H. Chen et al., "Integrated LEO Satellite and Terrestrial 6G Networks: Architecture and Key Technologies," Science China Information Sciences, vol. 67, no. 4, pp. 1-25, 2024.
11. R. Rinaldo et al., "Non-Geostationary Satellite IoT Systems: Technology Evolution and Market Outlook," IEEE Aerospace and Electronic Systems Magazine, vol. 39, no. 3, pp. 34-48, 2024.
