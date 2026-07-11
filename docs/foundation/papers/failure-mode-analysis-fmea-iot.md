---
schema_version: '1.0'
id: failure-mode-analysis-fmea-iot
title: IoT硬件失效模式分析FMEA方法
layer: 1
content_type: tutorial
difficulty: intermediate
reading_time: 18
prerequisites:
  - accelerated-life-testing-iot
  - derating-component-reliability
tags:
  - FMEA
  - DFMEA
  - RPN
  - 可靠性
  - 失效模式
  - IoT硬件
  - FTA
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT硬件失效模式分析FMEA方法

> **难度**：🟡 中级 | **领域**：可靠性分析 | **关键词**：FMEA, DFMEA, RPN, 失效模式 | **阅读时间**：约 18 分钟

## 日常类比

体检不是等生病才做，而是提前筛风险。失效模式与影响分析（Failure Mode and Effects Analysis, FMEA）就是硬件设计的“体检”：在出货前穷举可能怎么坏、坏了有多严重、现有测试能不能抓到，再按风险优先数（Risk Priority Number, RPN）排改进顺序[1][2]。

## 摘要

梳理设计 FMEA（Design FMEA, DFMEA）与过程 FMEA（Process FMEA, PFMEA）分工、七步流程、严重度/发生度/探测度（Severity / Occurrence / Detection, S/O/D）评分与 IoT 节点案例。评分阈值与失效率为工程常用量级，**以项目标准与现场数据为准**[2][3]。

## 1. 类型与时机

| 类型 | 关注点 | IoT 典型用途 |
|------|--------|--------------|
| DFMEA | 原理图、结构、环境适应性 | 设计评审 |
| PFMEA | 焊接、装配、测试、包装 | 产线与工艺 |

概念设计即可出初版，详细设计与原型验证后更新；量产前才做往往改不动。与故障树分析（Fault Tree Analysis, FTA）互补：FMEA 自底向上扫面，高严重度项再用 FTA 深挖[2][4]。

## 2. 七步与 RPN

范围建议按子系统（电源、传感、通信）拆分。对每项功能列出失效模式 → 影响(S) → 原因(O) → 现有控制(D) → `RPN = S × O × D`（各项通常 1–10）[1][3]。

| 常见失效类别 | 示例 |
|--------------|------|
| 功能丧失/降级 | 无输出、精度超差 |
| 间歇/非预期 | 偶发复位、GPIO 误触发 |
| 超时 | 启动过长、OTA 失败 |

| 评分维度 | 低分含义 | 高分含义 |
|----------|----------|----------|
| S | 几乎无感 | 停机或人身安全风险 |
| O | 极罕见 | 几乎必然 |
| D | 交付前几乎必检出 | 几乎无法检出 |

**注意**：D 越低越好。任何 S 很高的项，即使 RPN 不高也应单列关注。RPN 行动阈值由项目自定，常见做法是高分段强制措施、中分段评估[3]。

## 3. IoT 特有失效面

除元器件与焊接外，节点常需覆盖：空中下载（Over-The-Air, OTA）变砖、电池老化与低温、网关/射频丢失、内存泄漏与看门狗失效等——传统消费电子 FMEA 表里往往缺失[5][6]。

| 功能示例 | 高风险方向 | 典型措施方向 |
|----------|------------|--------------|
| 温度采集 | 漂移难检出 | 交叉校验、现场校准 |
| 射频 | 温漂频偏、天线接触 | TCXO/补偿、固定胶与驻波检 |
| OTA | 掉电半更新 | 双区 + 校验 + 回滚 |

## 4. 局限、挑战与可改进方向

### 1. 评分主观与“走过场”

**局限**：无现场数据时 O/D 靠拍脑袋，表格填完不驱动设计。
**改进**：用同类产品故障率校准 O；把高 RPN 绑到设计评审与测试用例[3]。

### 2. 探测度虚低

**局限**：把“用户能发现”当成“产线能探测”。
**改进**：D 只评交付前控制；环境相关失效用加速试验补覆盖[6]。

### 3. 措施不闭环

**局限**：写“加强质量”无法执行，设计变更后表不更新。
**改进**：措施写到器件/代码/测试；变更触发 FMEA 增量评审[1]。

### 4. 范围过大

**局限**：整机一张表导致粒度过粗。
**改进**：按模块拆分；S 高项再配 FTA[4]。

## 总结

FMEA 把事后救火变成事前排序：尽早、按子系统、措施可验证并持续更新。IoT 务必把 OTA、电池与连接失效写进表，用 RPN 集中资源改最高风险项。

## 参考文献

[1] SAE J1739, Potential Failure Mode and Effects Analysis in Design (Design FMEA).
[2] IEC 60812, Failure modes and effects analysis (FMEA and FMECA).
[3] AIAG & VDA, FMEA Handbook, 1st Edition.
[4] D. H. Stamatis, Failure Mode and Effect Analysis: FMEA from Theory to Execution, ASQ.
[5] GJB 1391, 故障模式、影响及危害性分析程序（对照参考）.
[6] IEC 60068 / 加速寿命与环境试验相关标准（探测与验证语境）.
[7] ISO 26262 功能安全中的系统失效分析实践（汽车交叉参考）.
[8] NASA, Fault Tree Handbook with Aerospace Applications（与 FTA 配合）.
[9] IPC / 电子组装可靠性与工艺 FMEA 应用笔记.
[10] IEEE Reliability Society, FMEA 在嵌入式与物联网系统中的应用综述.
[11] MIL-STD-1629A, Procedures for Performing a FMECA（历史方法对照）.
[12] 现场退货与 FRACAS 闭环实践文献（用数据校准 O）.
