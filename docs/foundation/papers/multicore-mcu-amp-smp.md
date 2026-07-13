---
schema_version: '1.0'
id: multicore-mcu-amp-smp
title: 多核MCU的AMP与SMP运行模式分析
layer: 1
content_type: comparison
difficulty: intermediate
reading_time: 16
prerequisites:
  - freertos-task-scheduling-deep-dive
  - rpmsg-multicore-communication
tags:
  - 多核MCU
  - AMP
  - SMP
  - OpenAMP
  - FreeRTOS
  - 核间通信
  - 实时性
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 多核MCU的AMP与SMP运行模式分析

> **难度**：🟡 中级 | **领域**：嵌入式多核 | **关键词**：AMP, SMP, RPMsg, 缓存一致性 | **阅读时间**：约 16 分钟

## 日常类比

单核像一个厨师既炒菜又收银，忙不过来。**AMP**（Asymmetric Multi-Processing）像前后厨分工：一核专做实时控制，一核跑通信/UI。**SMP**（Symmetric Multi-Processing）像两个同等厨师抢同一本菜单（同一操作系统调度）——灵活，但要解决抢灶台（缓存与锁）问题[1][2]。

## 摘要

对比 AMP/SMP 资源划分、核间通信与缓存一致性，并以 STM32H7 双核、RP2040、ESP32 为例说明选型。延迟与加速比为场景量级，以共享总线与内存争用实测为准[3]。

## 1. 为何多核、两种模型

单核在无线协议栈 + 控制环 + 加密同压时抖动大。AMP：每核独立镜像/OS，资源静态划分；SMP：单 OS 调度多对称核。

| 维度 | AMP | SMP |
|------|-----|-----|
| OS | 每核可不同 | 通常同一 RTOS/Linux |
| 隔离 | 好（实时/安全） | 依赖锁与分区 |
| 负载均衡 | 手工 | 调度器 |
| 复杂度 | 通信与生命周期 | 并发与一致性 |

## 2. AMP 通信与 SMP 一致性

AMP 常用共享内存 + 环形缓冲、邮箱、硬件信号量；OpenAMP/RPMsg 提供标准化消息通道与生命周期管理[4]。

SMP 必须处理缓存一致性（硬件监听或软件维护）与临界区；错误表现为“偶发数据腐蚀”。FreeRTOS SMP 等需确认移植是否启用多核调度与自旋锁[5]。

| 芯片倾向 | 模式 | 备注 |
|----------|------|------|
| STM32H747 M7+M4 | AMP 典范 | 实时 + 通用 |
| RP2040 双 M0+ | 轻量 AMP/协作 | 无复杂 cache 层次 |
| ESP32 双核 | 协议栈绑核 + 应用 | 偏混合 |

## 3. IoT 选型

| 场景 | 建议 |
|------|------|
| 硬实时控制 + 云连接 | AMP：实时核隔离 |
| 同质并行计算 | SMP 或多任务单核先评估 |
| 安全世界隔离 | AMP + 内存保护 |

性能不是 ×N：共享 Flash/外设与同步开销会吃掉加速比[3]。

## 4. 局限、挑战与可改进方向

### 1. 共享资源争用

**局限**：双核同时打 Flash/DMA 导致实时核超时。
**改进**：关键代码放 ITCM/SRAM；总线带宽预算与优先级[3]。

### 2. 核间协议无版本

**局限**：一端 OTA 后消息布局变化致死锁。
**改进**：RPMsg 契约测试、版本字段、握手兼容矩阵[4]。

### 3. SMP 调试困难

**局限**：竞态只在高负载出现。
**改进**：线程消毒剂/硬件跟踪；减少共享可变状态[5]。

### 4. 过度多核化

**局限**：任务本可单核周期调度，却引入双镜像成本。
**改进**：先剖析 CPU；不够再拆核[2]。

## 总结

AMP 换隔离与可证明的实时边界，SMP 换调度灵活；IoT 网关/电机控制更常 AMP。先定谁必须不被抢，再定通信契约，最后才谈“跑满双核”。

## 参考文献

[1] ARM, 多核与 AMP/SMP 系统软件指南公开材料.
[2] FreeRTOS SMP 文档与移植说明.
[3] ST, STM32H7 双核应用笔记.
[4] OpenAMP / RPMsg 规范与文档.
[5] ESP-IDF 双核调度与核绑定文档.
[6] Raspberry Pi RP2040 Datasheet（双核与 FIFO）.
[7] 缓存一致性协议教材章节（MESI 等）.
[8] 多核嵌入式调试与跟踪（ETM/SWO）应用笔记.
[9] 核间共享内存无锁环形缓冲实践.
[10] 功能安全中的多核分区讨论公开材料.
[11] Linux remoteproc/rpmsg 框架文档（对照 MCU）.
[12] 多核启动顺序与复位策略应用笔记.
