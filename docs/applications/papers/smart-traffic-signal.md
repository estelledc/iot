---
schema_version: '1.0'
id: smart-traffic-signal
title: 智慧城市交通信号优化
layer: 7
content_type: technical_analysis
difficulty: intermediate
reading_time: 28
prerequisites:
  - reinforcement-learning-edge
  - edge-ai-video-analytics
  - v2x-autonomous-driving
tags:
- 交通信号
- ATSC
- SCATS
- SCOOT
- 强化学习
- 绿波协调
- SUMO
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 智慧城市交通信号优化

> **难度**：🟡 中级 | **领域**：智慧城市、交通工程 | **阅读时间**：约 28 分钟

## 日常类比

固定配时信号灯像闭眼指挥的交警：按表切换，不管哪边车多。自适应信号控制（Adaptive Traffic Signal Control, ATSC）像看队伍长度的传菜口主管——哪边堆菜多就多给窗口时间。绿波则是整条街多家餐厅传菜节奏对齐：你按设计车速走，连续遇到绿灯。现实更难：四向冲突、左转专用、行人与公交/急救优先都要排进同一套相位。

## 一句话总结

用线圈/视频/雷达等检测车流，经 SCATS/SCOOT 或强化学习动态调周期、绿信比与相位差，降低延误与排队；实地收益取决于检测质量、协调范围与 sim-to-real 差距。[1][3][5]

## 摘要

传统固定配时无法感知实时排队。ATSC 目标是最小化路网延误。下文覆盖检测技术、SCATS/SCOOT、多智能体 RL、绿波、公交/急救优先、SUMO 评估与部署案例口径。

## 1 车辆检测技术

| 检测技术 | 精度（示意） | 能力 | 安装成本 | 维护 | 适用 |
|----------|--------------|------|----------|------|------|
| 感应线圈 | 高 | 存在/计数 | 中（开挖） | 高 | 传统改造 |
| 视频检测 | 中–高 | 计数/速度/分类/轨迹 | 中–高 | 中 | 多车道 |
| 微波雷达 | 高 | 存在/速度/计数 | 中 | 低 | 雨雪雾 |
| 激光雷达 | 很高 | 3D 多目标 | 高 | 中 | 高精度 |
| 地磁 | 中–高 | 存在/计数 | 低 | 低 | 低成本 |
| V2I | 联网车近乎精确 | 位置/速度/意图 | 高 | 中 | 渗透率提升后 |

深度学习检测 + 跟踪相对"虚拟线圈"更稳，但仍受光照、遮挡影响；边缘算力决定可接入路数。[1][8]

车对基础设施（Vehicle-to-Infrastructure, V2I）经 C-V2X/DSRC 上报意图最理想，但新车装配率仍有限，短期作辅助源。[12]

## 2 经典自适应系统

### 2.1 SCATS

悉尼协调自适应交通系统（Sydney Coordinated Adaptive Traffic System）：路口根据检测从方案库选配时，区域层做绿波协调。全球多城部署，路口规模以厂商/交通局披露为准。[3]

### 2.2 SCOOT

分段偏移优化技术（Split Cycle Offset Optimisation Technique）：每周期微调周期、绿信比与相位差，逼近最优；检测与通信需求通常高于 SCATS。[1]

### 2.3 对比

| 维度 | SCATS | SCOOT |
|------|-------|-------|
| 优化方式 | 方案选择 | 在线微调 |
| 检测器 | 停车线附近为主 | 上游进口等更密 |
| 通信 | 相对较低 | 较高（更实时） |
| 适应速度 | 分钟级常见 | 可到周期级 |
| 延误降低（文献常见） | 约 15–25% | 约 12–20% |

百分比相对固定配时或改造前，基线不同不可横比。[1][3]

## 3 强化学习方法

将单路口建成 MDP：状态含各进口排队与相位；动作保持/切换；奖励惩罚排队、奖励吞吐。

多智能体难点是上游放行改变下游到达。方法含独立 DQN、CTDE（QMIX/MAPPO）、图注意力（GAT）建模空间耦合。论文在特定路网相对 SCATS 可报约两成延误下降，换城需重训与约束。[5][4][8]

**Sim-to-Real**：SUMO 跟驰、无噪声检测、缺非机动车/行人会导致落差。域随机化与在线微调是常用缓解。

```python
# 概念：奖励 = -α·总排队 + β·吞吐
# 实地必须加最小绿、全红、行人相位等硬约束，不能让 RL 自由探索
```

## 4 绿波协调

相位差 ≈ 路口间距 / 设计车速。单向绿波较易；双向绿波受半周期几何约束，常保主方向、次方向折中。MAXBAND/MULTIBAND 等用混合整数规划最大化带宽。[9]

## 5 特殊场景

| 场景 | 策略 | 注意 |
|------|------|------|
| 公交优先（TSP） | 延长/提前绿灯；可设晚点条件 | 过度优先损害社会车 |
| 紧急车辆 | V2I/GPS 触发清场 | 冲突方向安全清空 |
| 自适应行人 | 检测等待人数/弱势群体 | 须满足最小行人绿 |

紧急车辆行程时间改善幅度来自特定城市系统报告，外推需本地验证。[2]

## 6 仿真与评估

SUMO + TraCI 可做微观闭环。核心指标：

| 指标 | 定义 | 目标 |
|------|------|------|
| 平均延误 | 实际行程 − 自由流 | 最小化 |
| 排队长度 | 进口道排队 | 最小化 |
| 停车次数 | 行程内停车 | 最小化 |
| 通行能力 | 单位时间通过量 | 最大化 |
| 绿灯利用率 | 实际/理论通行 | 最大化 |

## 7 部署效果（口径提示）

| 城市 | 系统 | 规模量级 | 报告延误降低 | 备注 |
|------|------|----------|--------------|------|
| 匹兹堡 | Surtrac | 数十路口 | 约两成余 | RL/自适应 [2] |
| 悉尼 | SCATS | 数千路口 | 约一至两成 | 长期运行 [3] |
| 伦敦 | SCOOT | 数千路口 | 约一成余 | 含排放相关报告 |
| 杭州 | 城市大脑 | 千余路口 | 约一成半 | 官方治理报告 [10] |
| 其他城市 | 多厂商 | 数百–数千 | 约一至两成 | 口径不一 |

## 8 局限、挑战与可改进方向

### 8.1 检测失效传导错误配时

**局限**：视频夜间误检、线圈损坏会让自适应"帮倒忙"。
**改进**：多源冗余；检测健康度降级到固定配时；运维 SLA。[8]

### 8.2 RL 安全与可认证性

**局限**：无约束探索可能过短绿灯或跳相，难通过交管验收。
**改进**：动作掩码（最小绿/全红/相序）；先影子再小范围 A/B；保留人工接管。[4][8]

### 8.3 绿波与支路公平

**局限**：干道绿波可能牺牲支路与行人。
**改进**：多目标（延误+等待公平）；分时段主方向；行人最小绿硬约束。[9]

### 8.4 案例数字营销化

**局限**：新闻稿"延误降 xx%"缺对照季节与边界。
**改进**：固定前后各数周同季节；报告延误、排队、事故率；开放聚合数据。

### 8.5 V2X 渗透不足

**局限**：低渗透时 V2I 优先可能不公平且不稳定。
**改进**：检测为主、V2I 为辅；渗透率阈值策略；与单车智能渐进融合。[12]

## 9 实践建议

1. 改造路口：保留可用线圈，加视频补分类与排队估计。
2. RL 必须在 SUMO 用本地流量标定后再试点，以 SCATS/SCOOT 为基线。
3. 先做主干单向绿波，设计车速取限速的八成左右作起点。
4. 全市数据汇聚与标准相位编号是智能化前提，先于算法炫技。

## 参考文献

[1] H. Wei et al., "A Survey on Traffic Signal Control Methods," arXiv:1904.08117, 2023 (updated).
[2] S. F. Smith et al., "Smart Urban Signal Networks: Initial Application of the Surtrac Adaptive Traffic Signal Control System," ICAPS, 2023.
[3] Roads and Maritime Services NSW, "SCATS Technical Reference," 2024.
[4] G. Zheng et al., "Diagnosing Reinforcement Learning for Traffic Signal Control," IEEE Transactions on Intelligent Transportation Systems, vol. 25, no. 3, 2024.
[5] X. Wang et al., "Multi-Agent Reinforcement Learning for Urban Traffic Signal Control Using Graph Attention Networks," Transportation Research Part C, vol. 158, 2024.
[6] 公安部交通管理局, "城市道路交通信号控制方式设置规范（GA/T 527-2023）," 2023.
[7] D. Krajzewicz et al., "SUMO – Simulation of Urban Mobility: An Overview," SIMUL, 相关版本说明.
[8] K. He et al., "Real-World Deployment of RL-based Traffic Signal Control: Challenges and Solutions," KDD, 2024.
[9] J. Gregoire et al., "Green Wave Optimization for Urban Traffic Networks: A Review," Transportation Research Record, 2024.
[10] 杭州城市大脑交通平台, "交通治理报告," 2024.
[11] TRL, "SCOOT Traffic Signal Control System: Technical Overview," 相关资料.
[12] 3GPP / C-V2X 相关规范与新车装配率行业统计（引用时注明年份）.
