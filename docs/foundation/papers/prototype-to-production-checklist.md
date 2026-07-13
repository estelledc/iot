---
schema_version: '1.0'
id: prototype-to-production-checklist
title: IoT硬件原型到量产的设计检查清单
layer: 1
content_type: tutorial
difficulty: intermediate
reading_time: 15
prerequisites:
  - bom-cost-optimization-iot
  - testability-design-iot-hardware
  - ce-fcc-certification-iot
tags:
  - 量产
  - DFM
  - DFT
  - 认证
  - BOM
  - 检查清单
  - NPI
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# IoT硬件原型到量产的设计检查清单

> **难度**：🟡 中级 | **领域**：产品工程 | **关键词**：NPI, DFM, DFT, 认证, BOM | **阅读时间**：约 15 分钟

## 日常类比

家里做菜好吃，不等于能上餐厅菜单：要稳定采购、份量一致、高峰仍能出餐、冷链后口感仍在。原型到量产就是这段距离——功能“能跑”只是起点，制造与现场可靠才是目标[1]。

## 摘要

按电气/结构/固件/供应链/认证/测试列出可执行检查项，强调可制造性设计（Design for Manufacturability, DFM）与可测试性设计（Design for Testability, DFT）。清单需按产品风险裁剪，非一次性填完[2]。

## 1. 原型与量产差距

| 原型常见 | 量产要求 |
|----------|----------|
| 飞线/手工焊 | 可 SMT 的完整工艺 |
| 散件电商货 | 可追溯、双供、生命周期 |
| 室温演示 | 全温、湿热、振动 |
| 调试口常开 | 关闭或鉴权、量产固件 |
| 未认证天线 | 模组/天线组合合规 |

## 2. 硬件与 DFM/DFT

| 类别 | 检查要点 |
|------|----------|
| 原理图 | 上下拉默认态、复位、看门狗、欠压、防反接 |
| PCB | 阻抗/回流、散热、拼板、丝印极性、测试点 |
| BOM | 生命周期、交期、替代料、成本阶梯 |
| 结构 | 公差、防水、静电放电（ESD）路径、天线净空 |
| DFT | 夹具点、边界扫描/烧录夹具、光学检测标记 |

## 3. 固件、工厂与认证

固件：安全启动、加密、校准数据分区、工厂模式、版本与序列号写入、掉电安全。工厂：烧录夹具节拍、校准限值、失败码、包装防潮。认证：电磁兼容（EMC）、射频、安规、电池运输——改天线/时钟/外壳常触发重测[3][4]。

| 阶段 | 出口准则示例 |
|------|----------------|
| EVT | 功能闭环、已知问题列表 |
| DVT | 环境/EMC 预合规、DFM 关闭项 |
| PVT | 良率达标、工艺文件冻结 |
| MP | 变更控制、持续可靠性抽测 |

## 4. 局限、挑战与可改进方向

### 1. 清单过长无法落地

**局限**：百项全勾导致形式主义。
**改进**：按安全/合规/成本风险分级；每阶段强制项≤可执行数量[2]。

### 2. 工程样与产线物料不一致

**局限**：替代料导致射频/时序回归。
**改进**：PVT 必须用产线 BOM；替代料走变更评审[5]。

### 3. 认证与设计并行不足

**局限**：冻结后才测，改板代价高。
**改进**：DVT 前预扫描；保留认证模组与布局约束[3]。

### 4. 现场失效未回流到清单

**局限**：同样坑在下一代重复。
**改进**：失效模式与影响分析（FMEA）更新检查项；售后编码闭环[1]。

## 总结

把原型当“菜谱草稿”，用分阶段出口准则与 DFM/DFT/认证检查把产品推到可重复制造；清单服务于风险，而不是堆砌条目。

## 参考文献

[1] New product introduction (NPI) stage-gate practices for electronics.
[2] Design for Manufacturability / Design for Testability handbooks (IPC-related).
[3] CE/FCC IoT device certification process overviews.
[4] Battery UN38.3 / transport compliance notes for IoT products.
[5] Engineering change order (ECO) and second-source qualification.
[6] SMT panelization, fiducial, and test-point guidelines.
[7] Secure manufacturing: provisioning, key injection, factory modes.
[8] Environmental test suites (temperature, humidity, vibration) for IoT.
[9] EMC pre-compliance scanning in development labs.
[10] BOM lifecycle and PCN monitoring practices.
[11] Yield ramp metrics from PVT to mass production.
[12] Field failure feedback into FMEA and checklists.
