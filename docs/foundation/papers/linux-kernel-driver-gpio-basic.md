---
schema_version: '1.0'
id: linux-kernel-driver-gpio-basic
title: Linux内核GPIO驱动开发基础
layer: 1
content_type: tutorial
difficulty: intermediate
reading_time: 16
prerequisites:
  - device-tree-embedded-linux
tags:
  - Linux驱动
  - GPIO
  - libgpiod
  - 设备树
  - 平台驱动
  - 嵌入式Linux
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# Linux内核GPIO驱动开发基础

> **难度**：🟡 中级 | **领域**：嵌入式 Linux | **关键词**：gpiod, 设备树, IRQ | **阅读时间**：约 16 分钟

## 日常类比

用户空间拨开关像请前台代按电灯；内核驱动则是直接进配电间改接线。现代 Linux 用描述符型 GPIO（gpiod）API 与设备树（Device Tree）说明“哪根针干什么”，旧 sysfs GPIO 接口已走向淘汰[1][4]。

## 摘要

覆盖用户空间 libgpiod、内核 `gpiod_*` API、中断、平台驱动与设备树绑定。内核版本差异大，以目标 LTS 文档为准[1][2]。

## 1. 用户空间与内核空间

| 路径 | 适用 |
|------|------|
| libgpiod / `gpioget` | 脚本、应用快速控灯 |
| 字符设备 `/dev/gpiochip*` | 取代旧 sysfs |
| 内核驱动 | 需中断线程、与总线外设绑定 |

| 内核概念 | 作用 |
|----------|------|
| gpio_chip | 控制器 |
| gpio_desc | 线路描述符 |
| 设备树 `gpios` 属性 | 连接外设与引脚 |

请求 GPIO 时应指定方向与标志（开漏、低有效等）；中断用 `gpiod_to_irq` 或 fwnode IRQ API，上半部短、下半部/线程处理[1]。

## 2. 平台驱动要点

`probe` 中：解析设备树 → `devm_gpiod_get` → 注册 IRQ/字符设备。用 `devm_` 托管资源防泄漏。调试：`/sys/kernel/debug/gpio`、`gpioinfo`、动态调试打印[2][5]。

## 3. 局限、挑战与可改进方向

### 1. 沿用已弃用 sysfs

**局限**：新内核移除后应用崩溃。
**改进**：迁移 libgpiod[2][4]。

### 2. 设备树引脚冲突

**局限**：pinctrl 与另一外设复用打架。
**改进**：统一 pinctrl 组；启动日志查 busy[3]。

### 3. 用户空间轮询实时性差

**局限**：延迟与抖动大。
**改进**：内核 IRQ + 字符设备/事件通知[1]。

### 4. 睡眠与唤醒脚

**局限**：系统挂起后边沿丢失。
**改进**：配置唤醒源与电源域；测试 suspend[5]。

## 总结

新代码用 gpiod + 设备树；应用优先 libgpiod，要实时与集成再写平台驱动。先搞清引脚归属，再写 `probe`。

## 参考文献

[1] Kernel.org, GPIO Descriptor Driver Interface 文档.
[2] libgpiod 项目文档与工具说明.
[3] Bootlin, Embedded Linux 驱动培训材料.
[4] L. Walleij, GPIO character device API 介绍.
[5] Kernel.org, Platform drivers / Driver model 文档.
[6] Device Tree Specification / GPIO 绑定文档.
[7] Linux IRQ 线程化中断说明.
[8] pinctrl 子系统文档.
[9] Yocto/Buildroot 中启用 gpio 工具的配方说明.
[10] sysfs GPIO 弃用说明（内核邮件列表/文档）.
[11] `devm_` 资源管理最佳实践文章.
[12] 嵌入式 Linux GPIO 硬件防抖与中断风暴处理笔记.
