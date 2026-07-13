---
schema_version: '1.0'
id: cooperative-vs-preemptive-scheduling
title: 协作式与抢占式调度在资源受限设备中的权衡
layer: 1
content_type: comparison
difficulty: intermediate
reading_time: 15
prerequisites: UNKNOWN
tags:
  - 协作式调度
  - 抢占式调度
  - FreeRTOS
  - protothreads
  - 实时性
  - 栈开销
  - IoT
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 协作式与抢占式调度在资源受限设备中的权衡

> **难度**：🟡 中级 | **领域**：嵌入式调度策略 | **阅读时间**：约 15 分钟

## 日常类比

单车道小路：司机到路口自觉让行 = 协作式（Cooperative）；交警按灯强制换车 = 抢占式（Preemptive）。前者省事但怕“霸路”；后者可控但每次换车要搬货——上下文切换（Context Switch）开销[1][2]。

## 摘要

从栈 RAM、响应时间、共享资源安全与实时保证对比协作/抢占及混合策略，并映射 Contiki/protothreads 与 FreeRTOS/Zephyr。延迟与栈字节为工程量级，**随 MCU、编译器与任务深度变化**[1][3]。

## 1. 模型

协作：任务跑到主动 `yield` 才切换，切换点可预期，可无 tick 驱动。抢占：tick/事件让内核暂停当前任务，高优先级就绪即可抢占，需保存完整上下文[1][2]。

| 维度 | 协作式 | 抢占式 |
|------|--------|--------|
| 切换时机 | yield 点 | 中断/优先级 |
| 每任务栈 | 可共享（如 protothreads） | 独立且更大 |
| 共享数据 | yield 前写完则常天然一致 | 需锁/原子 |
| 硬实时 | 难（取决于最长段） | 更可行（仍要分析） |

## 2. 栈、响应与同步

抢占栈须覆盖寄存器帧、嵌套中断与裕量；协作可极省（protothreads 每任务数字节级叙事）[1][4]。

最坏响应：协作 ≈ 最长不可抢占段；抢占 ≈ 中断延迟 + 调度 + 最长临界区。硬实时（安全气囊级）通常要抢占 + 可调度性分析（如 RMA 叙事）；软实时传感可用协作[3][5]。

| 同步 | 协作 | 抢占 |
|------|------|------|
| 简单变量 | 常无需 | 原子/关中断 |
| 结构体 | 段内写完 | 互斥锁 |
| 优先级反转 | 无 | 有（需继承等） |

## 3. 实现与混合

| 实现 | 模型 | 备注 |
|------|------|------|
| protothreads | 极简协作 | 局部变量跨 yield 限制 |
| Contiki 系 | 事件+协作 | WSN 经典叙事 |
| FreeRTOS | 默认可抢占 | 可关抢占或分层 |
| Zephyr | 可逐任务协作/抢占 | 灵活混合 |

混合：通信/安全路径高优先级抢占；日志/聚合低优先级协作分块。ISR 宜短：协作侧置标志；抢占侧可 FromISR 给信号量并请求切换[2][6]。

## 4. 场景选择

| 场景 | 倾向 |
|------|------|
| RAM 极紧、秒级采集 | 协作 |
| 工业网关、亚毫秒通信 | 抢占 |
| 两者兼需 | 混合分层 |

原则：用能满足截止时间的最简机制，避免为“可能需要”引入锁与时序 bug[3][7]。

## 5. 局限、挑战与可改进方向

### 1. 协作被长段堵死

**局限**：漏写 yield 或阻塞调用 → 整系统假死。
**改进**：编码规范强制短段；静态检查最长路径；看门狗。

### 2. 抢占竞态与死锁

**局限**：半更新数据、锁顺序错误、优先级反转。
**改进**：最小临界区；优先级继承；超时拿锁；追踪工具。

### 3. 栈溢出难估

**局限**：独立栈低估 → 静默破坏。
**改进**：栈水位着色/钩子；按最坏调用链测算裕量。

### 4. 过度选型

**局限**：软实时小节点上满配抢占 RTOS，RAM/复杂度浪费。
**改进**：先证明截止时间需求；能协作则协作。

## 6. 实践要点

1. 列出任务截止时间与 RAM 预算再选模型。
2. 抢占系统默认打开栈溢出检测与断言。
3. 混合时明确“谁可抢谁”，文档化优先级表。

## 参考文献

[1] Dunkels A. et al., Protothreads: simplifying event-driven programming of memory-constrained embedded systems, ACM SenSys.
[2] Barry R., FreeRTOS practical guides / kernel documentation.
[3] Buttazzo G., *Hard Real-Time Computing Systems*, Springer.
[4] Contiki / Contiki-NG kernel and process model documentation.
[5] Rate-monotonic scheduling theory summaries (Liu & Layland lineage).
[6] Zephyr Project, Kernel scheduling documentation (cooperative vs preemptive threads).
[7] Embedded race condition and priority inversion case studies (industry notes).
[8] Cortex-M context switch and stack frame size references (ARM TRM).
[9] ISR design patterns: flag vs semaphore-from-ISR.
[10] Memory footprint comparisons of lightweight IoT OS schedulers.
[11] Watchdog and progress-metric techniques for cooperative loops.
