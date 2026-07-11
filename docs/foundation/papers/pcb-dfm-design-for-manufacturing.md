---
schema_version: '1.0'
id: pcb-dfm-design-for-manufacturing
title: PCB可制造性设计DFM检查清单
layer: 1
content_type: tutorial
difficulty: beginner
reading_time: 16
prerequisites:
  - pcb-design-basics-iot
  - bom-cost-optimization-iot
  - testability-design-iot-hardware
tags:
  - DFM
  - 可制造性
  - 线宽间距
  - 钢网
  - 拼板
  - IPC
  - 良率
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# PCB可制造性设计DFM检查清单

> **难度**：🟢 初级 | **领域**：制造与工艺 | **关键词**：DFM, 线宽, 环宽, 钢网 | **阅读时间**：约 16 分钟

## 日常类比

木匠图纸上的椅子弧度再美，工厂刀具够不着、胶水枪伸不进、螺丝边距不够一拧就裂——问题在“没为制造而设计”。印刷电路板（Printed Circuit Board, PCB）可制造性设计（Design for Manufacturing, DFM）同理：电气正确仍可能无法高良率量产[1][3]。

## 摘要

整理线宽间距、钻孔厚径比、阻焊丝印、焊盘环宽、拼板、表面处理、钢网与测试点等检查项。具体 mil/µm 极限以目标板厂能力表为准[1][5]。

## 1. DFM 维度

| 维度 | 关注 | 失败表现 |
|------|------|----------|
| 蚀刻 | 线宽/间距 | 开短路 |
| 钻孔 | 孔径、厚径比、孔环 | 断钻、破盘 |
| 焊接 | 焊盘、钢网、热不平衡 | 虚焊、立碑 |
| 测试 | 测点可达 | 漏测 |
| 拼板 | 工艺边、分板 | 翘曲、伤板 |

## 2. 关键规则（量级）

| 项目 | 稳妥做法倾向 |
|------|----------------|
| 线宽/间距 | 能 6/6 mil 不用极限 3/3 |
| 最小孔与环宽 | 满足 IPC 与厂规，避免孤岛环 |
| 铜到板边 | 留足安全距，金手指另规 |
| 阻焊桥 | 细间距封装按厂能力 |
| 丝印 | 不压焊盘，字高可读 |

表面处理：HASL/ENIG/OSP 等按焊盘密度、保质期、成本选；BGA/细间距常偏向 ENIG 等[1][5]。钢网：开孔与释放比例影响锡量；非对称焊盘易立碑，应热平衡设计[2]。

| 拼板 | 要点 |
|------|------|
| 工艺边 | 定位孔、光学点 |
| 分板 | V-cut/邮票孔强度与毛刺 |
| 利用率 | 与翘曲风险折中 |

## 3. 交付与成本

Gerber/钻孔/叠层/阻抗说明/BOM 封装一致；缺阻焊层或镜像错误是常见返工。成本：放宽线宽、减少特殊孔、标准板厚与表面处理，往往比砍器件更能降报价[3][5]。

## 4. 局限、挑战与可改进方向

### 1. 设计规则与工厂能力脱节

**局限**：EDA 默认通过，板厂拒单。
**改进**：项目启动导入该厂 DFM 约束文件[5]。

### 2. 过度追求高密度

**局限**：良率崩、交期飘。
**改进**：只在必要网络用极限规则，其余留裕量[1]。

### 3. 忽略组装 DFM

**局限**：PCB 能做但 SMT 立碑/连锡。
**改进**：按 IPC-7351 焊盘；钢网与回流曲线联调[2]。

### 4. 测试点不足

**局限**：量产无法 ICT/飞针覆盖。
**改进**：早期加 DFT 测点与夹具方案[3]。

## 总结

DFM 是把工厂教训写成约束：先对厂能力、再留裕量、再用清单。电气仿真替代不了可制造性审查。

## 参考文献

[1] IPC-2221B, Printed Board Design.
[2] IPC-7351B, SMD Land Pattern.
[3] Happy Holden, PCB Design for Manufacturing 相关著作.
[4] Robertson, Printed Circuit Board Designer's Reference.
[5] Sierra Circuits 等, DFM Guidelines Handbook.
[6] IPC-A-600/A-610 验收标准（质量背景）.
[7] 钢网设计与 IPC-7525 相关实践.
[8] ENIG/OSP/HASL 比较应用笔记.
[9] 拼板与分板工艺指南（板厂）.
[10] BGA 逃逸与孔环可靠性文献.
[11] 立碑机理与焊盘对称设计笔记.
[12] Gerber 与制造数据包检查清单.
