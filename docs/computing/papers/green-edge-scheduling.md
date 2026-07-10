---
schema_version: '1.0'
id: green-edge-scheduling
title: 绿色边缘调度策略
layer: 4
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - resource-management-heterogeneous
  - mec-5g-integration
tags:
- 绿色计算
- 碳感知调度
- DVFS
- 能量比例
- 碳强度
- 边缘调度
- 太阳能边缘
- PUE
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 绿色边缘调度策略

> **难度**：🟡 中级 | **领域**：绿色计算、调度优化、边缘计算 | **阅读时间**：约 22 分钟

## 日常类比

家用光伏 + 储能：白天“免费且更清洁”的电适合跑洗衣机、充电桩；晚上或阴天多用电网电。绿色边缘调度把同一逻辑用到计算任务——不紧急的模型更新、日志归档，可等到本地低碳窗口，或迁到当前电网更清洁的节点；告警与实时推理则不能为省碳而拖延[2][4]。

## 摘要

覆盖运营碳与内嵌碳、碳强度（carbon intensity）数据源、时间/空间迁移、能量比例与合并、动态电压频率调节（Dynamic Voltage and Frequency Scaling, DVFS）、温度感知与太阳能-电池节点调度。减排与功耗数字来自公开报告与典型硬件量级，跨地区电网与机型差异大，须本地测量验收[1][6][7]。

## 1 碳感知基础

### 1.1 两类碳

| 类型 | 定义 | 优化空间 |
|------|------|----------|
| 运营碳（Operational） | 用电产生的排放 | 调度与能效可显著影响 |
| 内嵌碳（Embodied） | 制造硬件的排放 | 主要靠延寿与提高利用率 |

边缘设备常利用率偏低、寿命偏短，内嵌碳占比相对云服务器更突出——具体吨级数字依赖供应链与电网，不宜套用单一常数[9][10]。

### 1.2 碳强度

单位：gCO₂eq/kWh。地区与时刻差异大：水电/核电主导区域可低至数十量级，煤电主导区域可达数百量级；同一天内可再生出力变化可带来数十百分点波动（量级示意）[3][5]。数据源包括 Electricity Maps、WattTime 等 API；无外网时用时段启发式降级[2][3]。

### 1.3 获取强度（示意）

```python
# Electricity Maps 等：GET latest carbon-intensity by zone
# 无网降级：白天有光伏则下调估计，夜间用区域基线
```

## 2 工作负载调度

### 2.1 时间迁移（Temporal Shifting）

在最大可延迟窗口内选择预测碳强度更低的时段执行批任务。Google 等超大规模数据中心报告过通过灵活负载获得约一成量级的碳减排（方法与边界见其公开材料，不可直接外推到边缘）[1][6]。边缘若叠加本地光伏，可延迟窗口的收益可能更大，也更受天气预测误差影响。

优先级建议三分：`realtime`（立即）、`best-effort`（窗口内选低谷）、`batch`（可等阈值以下，否则到期强制跑）。

### 2.2 空间迁移（Spatial Shifting）

| 约束 | 说明 |
|------|------|
| 传输成本 | 搬数据的带宽与延迟可能抵消碳收益 |
| 数据主权 | 跨境/跨域法规 |
| 容量 | 目标节点是否有空闲 |
| 可靠性 | 弱网下迁移失败 |

示意：同功率任务在高碳区与低碳区电网下，运营排放可差数倍；须把网络能耗与 SLA 一并计入目标函数[6][10]。

## 3 能量比例与合并

现实服务器空闲仍耗峰值功耗的相当比例（常见约四成量级，机型相关），低利用率等于“空转烧碳”[9]。

| 手段 | 做法 | 边缘注意 |
|------|------|----------|
| 合并（Consolidation） | 任务集中到少数节点，闲置关机/休眠 | 关节点会拉高用户延迟 |
| 右尺寸 | 选更小 TDP 平台 | 留突发余量 |
| 功率封顶 | CPU/GPU power cap | 先测 QPS/延迟曲线 |

## 4 DVFS 与 GPU 功耗

近似关系：动态功耗与 \(V^2 f\) 相关；降频并降压可超线性省电，但延迟上升[8]。Linux `cpufreq` 的 `schedutil`/`powersave`、Jetson `nvpmodel`、`nvidia-smi -pl` 功率上限是常用旋钮。功率上限往往以较小性能损失换明显功耗下降——**比例视负载是否算力瓶颈而定**，须 profiler 验证[8]。

## 5 温度感知

户外机柜高温触发降频（thermal throttling）、风扇功耗上升、可靠性恶化。策略：超温则降频、推迟批任务、必要时迁出；正常温区再吃满可再生窗口。

电源使用效率（Power Usage Effectiveness, PUE）= 设施总功耗 / IT 功耗。大型云数据中心可接近 1.1 量级；边缘微模块与户外节点常明显更高（散热差）——改善靠自然冷却、更好的机柜设计等，而非只调软件[7][9]。

## 6 太阳能-电池节点

架构：光伏 → 最大功率点跟踪（Maximum Power Point Tracking, MPPT）→ 电池 → 计算负载；能量管理系统（Energy Management System, EMS）把荷电状态（State of Charge, SoC）喂给调度器。

| 任务类 | 策略示意 |
|--------|----------|
| 传感与告警 | 最高优先级，几乎始终可跑 |
| 视觉推理 | 光伏功率充足时 |
| 日汇总/同步 | 固定低谷或 SoC 高时 |
| 模型下载 | SoC 高且链路好时 |

深度放电伤害电池寿命：SoC 低于约定阈值应砍非关键负载[10]。

## 7 落地顺序

1. 用 `powerstat` / `tegrastats` 等建立功耗基线
2. 试 DVFS / GPU power cap，画延迟-功耗帕累托
3. 接碳强度 API，先只调度可延迟批任务
4. Prometheus 等展示功耗、温度、估算排放，再谈自动迁移

## 8 局限、挑战与可改进方向

### 1. 碳数据粒度与误差

**局限**：区域平均强度不等于节点实际购电结构；预测误差会导致“以为在低碳窗口”实则不然。
**改进**：优先用本地电表 + 可再生仪表；API 作辅助；记录调度决策与事后强度，做回放评估[3][5]。

### 2. SLA 与碳目标冲突

**局限**：空间迁移增加尾延迟；合并关机伤害就近性。
**改进**：硬实时与安全链路移出碳优化集合；碳目标做成软约束或多目标（延迟分位数 + 碳）[6]。

### 3. 测量与归因困难

**局限**：共享节点上任务级能耗难拆；GPU/加速器功率域复杂。
**改进**：机柜级功率仪 + 利用率模型估算；关键作业独占时段标定；采用软件碳强度（Software Carbon Intensity, SCI）等规范做相对比较而非绝对审计[4]。

### 4. 边缘热与硬件寿命

**局限**：为吃光伏高峰而在高温时段满载，可能换来节碳却加速硬件老化。
**改进**：温度作硬约束，碳作软优化；高峰时优先能效比高的节点，而非盲目堆满[8][10]。

## 参考文献

[1] Google, "24/7 Carbon-Free Energy: Methodology and Results," https://sustainability.google/operating-sustainably/

[2] Green Software Foundation / Microsoft, "Carbon Aware SDK," https://github.com/Green-Software-Foundation/carbon-aware-sdk

[3] Electricity Maps, "Real-time Carbon Intensity API," https://www.electricitymaps.com/

[4] Green Software Foundation, "Software Carbon Intensity (SCI) Specification," https://sci.greensoftware.foundation/

[5] WattTime, "Marginal Emissions API Documentation," https://www.watttime.org/

[6] A. Radovanovic et al., "Carbon-Aware Computing for Datacenters," IEEE Transactions on Power Systems, 2022.

[7] IEA, "Data Centres and Data Transmission Networks," https://www.iea.org/energy-system/buildings/data-centres-and-data-transmission-networks

[8] NVIDIA, "Jetson Power Management Guide," https://docs.nvidia.com/jetson/

[9] B. Acun et al., "Carbon Explorer: A Holistic Framework for Designing Carbon Aware Datacenters," ACM ASPLOS, 2023.

[10] B. Li et al., "Sustainable Edge Computing: A Survey on Energy-Efficient and Carbon-Aware Approaches," ACM Computing Surveys, 2024.

[11] L. A. Barroso and U. Hölzle, "The Case for Energy-Proportional Computing," IEEE Computer, 2007.
