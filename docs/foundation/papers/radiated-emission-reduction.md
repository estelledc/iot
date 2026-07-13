---
schema_version: '1.0'
id: radiated-emission-reduction
title: 辐射发射降低：走线/接地/屏蔽综合策略
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - emc-fundamentals-iot-device
  - conducted-emi-filter-design
tags:
  - 辐射发射
  - EMC
  - 屏蔽
  - 接地
  - PCB布局
  - 回流路径
  - CISPR
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 辐射发射降低：走线/接地/屏蔽综合策略

> **难度**：🔴 高级 | **领域**：EMC 设计 | **关键词**：辐射发射, 回流, 屏蔽, 接地 | **阅读时间**：约 16 分钟

## 日常类比

印制板（PCB）上的电流回路像一把隐形的弓：电流越大、回路面积越大、频率越高，向外“射”的电磁能量越强。降辐射要同时减张力（电流/边沿）、缩短弓身（回路面积）、加隔音罩（屏蔽）——缺一不可[1][2]。

## 摘要

从环路天线机理出发，给出布线、叠层接地、电缆与屏蔽的组合策略，以及预合规思路。场强公式为定性指导，限值以适用标准为准[3]。

## 1. 机理

远场辐射与电流、环路面积、频率相关；共模电流经电缆也可成高效天线。差模靠减小环路；共模靠抑制对地不平衡与铁氧体/滤波[1][4]。

| 路径 | 典型来源 | 优先手段 |
|------|----------|----------|
| 差模环路 | 时钟、开关电源热环 | 紧耦合回流、短环 |
| 共模电缆 | 连接器、外壳缝 | 共模扼流、360°搭接 |
| 缝隙泄漏 | 屏蔽体开口 | 波导截止、导电衬垫 |

## 2. 布线与接地

高速线紧贴地平面，避免跨槽；时钟远离板边与连接器。开关电源热环（输入电容-开关-电感/二极管）最小化。地：提供完整回流；单点/多点按频率分段，避免“天线地线”[2][5]。

| 做法 | 目的 |
|------|------|
| 四层以上优先完整地 | 低阻抗回流 |
| 控制边沿/串阻 | 降高频谐波 |
| 晶振壳接地 | 减辐射与敏感 |
| 去耦近放 | 减电源环路 |

## 3. 屏蔽与线缆

金属壳需导电连续；漆面绝缘会破坏搭接。线缆屏蔽两端策略按是否防辐射/防敏感权衡；I/O 处滤波与壳体搭接常比“多贴铜皮”更有效[6]。

## 4. 局限、挑战与可改进方向

### 1. 晚阶段靠堆屏蔽

**局限**：成本高且可能仍失败。
**改进**：原理图/布局阶段控环路与时钟；预扫描迭代[3]。

### 2. 地槽与“隔离”误用

**局限**：切开地平面制造更大天线。
**改进**：用桥接与分区滤波代替长槽[5]。

### 3. 塑料壳产品

**局限**：无法拉第笼。
**改进**：关键回路自屏蔽、内部小板屏蔽罩、线缆共模抑制[6]。

### 4. 标准与限值混淆

**局限**：用错 Class/距离导致误判。
**改进**：明确目标市场标准（如 CISPR 32）再设设计裕量[3]。

## 总结

辐射控制是系统工程：先减小源与环路，再接地与线缆，最后屏蔽补强；用预合规数据驱动改板，而不是一次过认证赌运气。

## 参考文献

[1] Ott / Paul style EMC textbooks: loop radiation basics.
[2] PCB layout guidelines for EMI reduction (industry ANs).
[3] CISPR 32 / FCC Part 15 radiated emission overview.
[4] Common-mode vs differential-mode emission separation.
[5] Ground plane slots and return path discontinuities.
[6] Cable shield termination and enclosure bonding practices.
[7] Switch-mode power supply hot-loop layout notes.
[8] Ferrite bead/clamp selection for I/O cables.
[9] Shielding effectiveness and aperture leakage theory.
[10] Pre-compliance near-field probe scanning methods.
[11] Clock harmonic control: slew rate and spread spectrum.
[12] IoT module antenna keep-out vs EMC trade-offs.
