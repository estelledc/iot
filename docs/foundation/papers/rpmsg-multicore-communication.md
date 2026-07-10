---
schema_version: '1.0'
id: rpmsg-multicore-communication
title: RPMsg多核异构通信在IoT SoC中的应用
layer: 1
content_type: UNKNOWN
difficulty: advanced
reading_time: 22
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# RPMsg多核异构通信在IoT SoC中的应用
> **难度**：🔴 高级 | **领域**：多核通信架构 | **阅读时间**：约 22 分钟

## 引言

想象一栋大楼里有两个人：一个擅长写报告但反应慢(应用核跑Linux)，另一个擅长处理突发事件但不会写长文(实时核跑RTOS)。他们需要交换信息，怎么办？在桌上放一本共享笔记本，写完便条后按一下对方的门铃 -- 这就是RPMsg的核心思路。两个核各司其职，通过共享内存和中断通知完成协作。

在IoT SoC中，"应用核+实时核"的异构架构越来越普遍。Linux处理网络和云端事务，RTOS负责毫秒级传感器采样和电机控制，两者需要高效、可靠地交换数据。RPMsg正是Linux内核提供的标准化多核通信框架，本文将系统讲解其架构与实战要点。

## 1. 异构多核架构概述

### 1.1 什么是不对称多处理(AMP)

对称多处理(SMP)中多个核运行同一操作系统，共享同一套调度器。不对称多处理(AMP)则不同：

- 每个核运行独立的操作系统或裸机程序
- 核之间通过消息传递而非共享变量通信
- 各自有独立的地址空间和中断配置

在IoT SoC中，AMP的典型配置：

| 核心 | 操作系统 | 职责 |
|------|----------|------|
| 应用核(A核) | Linux | 网络连接、云端通信、用户界面、文件系统 |
| 实时核(M核) | RTOS/裸机 | 传感器采样、电机PWM、实时控制环路 |

这种分工让"大核"可以在低功耗休眠时，"小核"仍然保持实时响应。

### 1.2 为什么需要标准化的核间通信

不同核之间通信看似简单 -- 共享一块内存就行。但实际开发中问题很多：

- 内存区域怎么划分？谁管理缓冲区？
- 数据写完怎么通知对方？轮询还是中断？
- 多个服务能否复用同一链路？
- 一方崩溃了另一方怎么知道？

RPMsg框架正是为了解决这些问题而诞生，提供了一套标准化的通信接口。

## 2. RPMsg框架架构

### 2.1 整体分层

RPMsg的架构分为三层：

```
+---------------------------+
|  RPMsg Channel / Endpoint |  <-- 用户接口(命名通道)
+---------------------------+
|     virtio (VRing)        |  <-- 传输抽象(环形缓冲区描述)
+---------------------------+
|  Shared Memory + Mailbox  |  <-- 物理层(共享内存+中断)
+---------------------------+
```

- **RPMsg层**：提供命名端点(endpoint)，类似网络端口号，多个服务可复用同一链路
- **virtio层**：源自虚拟化领域的标准化I/O框架，提供环形缓冲区管理
- **物理层**：共享内存存放实际数据，mailbox中断负责通知

### 2.2 共享内存布局

两个核共享一块物理内存区域，核心数据结构是vring：

```
+--------------------+  <-- 共享内存起始地址
|   vring0 (TX方向)   |  核A发往核B的环形描述符表
|   - Descriptor Table|  存放缓冲区指针和长度
|   - Available Ring  |  发送方写入: "有新数据"
|   - Used Ring       |  接收方写入: "已处理完毕"
+--------------------+
|   vring1 (RX方向)   |  核B发往核A的环形描述符表
|   - Descriptor Table|
|   - Available Ring  |
|   - Used Ring       |
+--------------------+
|   Buffer Pool       |  实际数据缓冲区(共享RAM区域)
|   (多个固定大小buffer)|
+--------------------+
```

每个vring包含三部分：描述符表记录缓冲区位置，available环由发送方更新，used环由接收方更新。这种设计避免了锁 -- 发送方只写available，接收方只写used。

### 2.3 通信流程详解

一次完整的RPMsg消息发送过程：

1. 发送方从buffer pool获取一个空闲缓冲区
2. 将数据写入缓冲区
3. 更新vring描述符(指向该缓冲区，记录长度)
4. 更新available环，表示有新描述符可用
5. 触发mailbox中断，通知接收方
6. 接收方读取available环，获取描述符
7. 根据描述符从共享内存读取数据
8. 处理完毕后更新used环，归还缓冲区
9. 可选：触发反向中断通知发送方缓冲区已释放

```
核A(发送)                          核B(接收)
   |                                  |
   |--- 1.获取空闲buffer -----------> |
   |--- 2.写入数据到buffer ---------> |
   |--- 3.更新vring descriptor -----> |
   |--- 4.更新available ring -------> |
   |--- 5.Mailbox中断 --------------->|
   |                                  |--- 6.读取available ring
   |                                  |--- 7.从共享内存读数据
   |                                  |--- 8.更新used ring
   |<-- 9.(可选)Mailbox中断 ----------|
```

## 3. remoteproc框架

### 3.1 生命周期管理

remoteproc是Linux内核中管理远程处理器生命周期的框架，职责包括：

| 阶段 | 操作 | 说明 |
|------|------|------|
| 加载 | 解析固件(ELF格式) | 将代码段、数据段加载到对应物理地址 |
| 启动 | 释放复位信号 | 远程核开始执行 |
| 运行 | 监控心跳 | 可选watchdog监控 |
| 停止 | 发送停止信号 | 优雅关机或强制复位 |
| 崩溃恢复 | 检测崩溃 | 清理资源，重新加载固件 |

### 3.2 设备树配置

在Linux设备树中描述远程核的配置：

```dts
/* 设备树示例: STM32MP1的M4核 */
m4_rproc: m4@10000000 {
    compatible = "st,stm32mp1-m4";
    reg = <0x10000000 0x40000>,    /* 代码区 */
          <0x10040000 0x10000>;     /* 数据区 */
    resets = <&rcc MCU_R>;
    st,syscfg-holdboot = <&rcc 0x0 0x1>;
    memory-region = <&m4_sysram>;  /* 共享内存区域 */
    mboxes = <&ipcc 0>, <&ipcc 1>; /* mailbox通道 */
    mbox-names = "vq0", "vq1";
};
```

### 3.3 崩溃恢复机制

远程核崩溃后，remoteproc框架的处理流程：

1. 检测崩溃(watchdog超时或硬件异常中断)
2. 通知RPMsg层断开所有端点
3. 清理共享内存中的残留数据
4. 重新加载远程核固件
5. 重新建立RPMsg链路

这个过程对应用层透明 -- 上层服务只需处理连接断开和重建事件。

## 4. RPMsg端点与服务复用

### 4.1 命名端点机制

RPMsg端点类似网络端口号，每个端点有一个字符串名称：

```
RPMsg Link (一条物理连接)
  |
  +-- endpoint "rpmsg-sensor"   --> 传感器数据服务
  +-- endpoint "rpmsg-control"   --> 控制指令服务
  +-- endpoint "rpmsg-debug"     --> 调试日志服务
```

好处是多个服务复用同一条RPMsg链路，互不干扰。每个端点有独立的回调函数，收到消息后由对应的处理函数响应。

### 4.2 端点创建与通信

Linux端的端点创建流程：

```c
/* Linux端: 创建RPMsg端点 */
static int rpmsg_sensor_cb(struct rpmsg_device *rpdev,
    void *data, int len, void *priv, u32 src)
{
    struct sensor_data *sdata = data;
    /* 处理传感器数据 */
    return 0;
}

static int rpmsg_probe(struct rpmsg_device *rpdev)
{
    /* 端点已在设备树中声明，probe时自动创建 */
    dev_info(&rpdev->dev, "endpoint: %s\n",
             rpdev->id.name);
    return 0;
}

static struct rpmsg_driver rpmsg_sensor_driver = {
    .drv.name = "rpmsg-sensor",
    .callback = rpmsg_sensor_cb,
    .id_table = rpmsg_sensor_id,
};
```

## 5. 典型平台与实战

### 5.1 常见异构SoC平台

| 平台 | 应用核 | 实时核 | 典型应用 |
|------|--------|--------|----------|
| STM32MP1 | Cortex-A7 (Linux) | Cortex-M4 (RTOS) | 工业网关、智能仪表 |
| i.MX8M | Cortex-A53 (Linux) | Cortex-M4/M7 | 智能家居网关 |
| NXP LPC55S69 | 双Cortex-M33 | 一个跑安全固件 | 安全IoT设备 |
| TI AM62x | Cortex-A53 (Linux) | Cortex-R5F | 工业控制 |

### 5.2 STM32MP1实战示例

以STM32MP1为例，Linux核与M4核通过RPMsg交换数据：

**场景描述**：Linux发送配置参数给M4，M4以1kHz频率回传传感器数据。

```
M4核(RTOS)                         Linux核
   |                                  |
   |<-- rpmsg-sensor端点建立 --------|
   |<-- 配置:采样率=1000Hz ----------|
   |                                  |
   |--- 传感器数据(1kHz) ----------->|
   |--- 传感器数据(1kHz) ----------->|
   |--- 传感器数据(1kHz) ----------->|
   |   ...持续发送...                 |
   |                                  |
   |<-- 配置:采样率=100Hz -----------|  (动态调整)
   |--- 传感器数据(100Hz) ---------->|
```

M4端使用RPMsg-lite(轻量级RPMsg实现)：

```c
/* M4端(RTOS): RPMsg-lite初始化 */
#define SHM_BASE  0x10040000  /* 共享内存基地址 */
#define SHM_SIZE  0x10000     /* 共享内存大小 */

struct rpmsg_lite_instance *inst;
inst = rpmsg_lite_master(SHM_BASE, SHM_SIZE,
                          RPMSG_LITE_LINK_ID,
                          VIRIGNUM, &env_ctx);
/* 创建端点 */
struct rpmsg_lite_endpoint *ept;
ept = rpmsg_lite_create_ept(inst, SENSOR_EPT_ADDR,
                              sensor_data_cb, NULL);
/* 发送数据 */
rpmsg_lite_send(inst, ept, REMOTE_EPT_ADDR,
                &sensor_buf, sizeof(sensor_buf));
```

### 5.3 i.MX8M平台要点

i.MX8M的M4核在Linux启动前就已经运行(早期启动)，需要注意：

- M4固件由U-Boot加载或Linux remoteproc加载
- 共享内存区域必须在设备树中预留，防止Linux占用
- MU(Message Unit)硬件提供核间中断机制
- 资源分区(Resource Domain Controller)控制外设归属

## 6. 开发流程与调试

### 6.1 完整开发步骤

1. **硬件准备**：确认SoC支持异构多核，确认共享内存区域
2. **设备树配置**：定义remoteproc节点、共享内存保留区、mailbox通道
3. **Linux端开发**：编写RPMsg驱动，定义端点名称和回调
4. **RTOS端开发**：使用RPMsg-lite，实现对应端点和数据格式
5. **联调测试**：先测基本通信，再测压力场景(高频、大数据量)
6. **异常处理**：测试崩溃恢复、通信超时、缓冲区溢出

### 6.2 调试技巧

| 问题 | 调试方法 |
|------|----------|
| 消息未收到 | 跟踪mailbox中断计数: `/proc/interrupts` |
| 数据错误 | dump共享内存内容，检查buffer是否被覆盖 |
| 性能不足 | 测量端到端延迟: 发送方打时间戳，接收方计算差值 |
| 崩溃重启循环 | 检查remoteproc日志: `dmesg / grep remoteproc` |
| 内存一致性问题 | 确认共享内存区域标记为non-cacheable |

### 6.3 内存一致性问题

这是最容易踩的坑。如果共享内存被配置为cacheable：

- 发送方写入数据可能还在cache中，未刷到物理内存
- 接收方读到的是旧数据(stale data)
- 导致数据不一致、通信失败

解决方案：

```dts
/* 在设备树中标记共享内存为non-cacheable */
reserved-memory {
    m4_sysram: m4_sysram@10040000 {
        reg = <0x10040000 0x10000>;
        no-map;          /* 不映射到Linux虚拟地址空间 */
        /* ARMv7-M侧天然non-cacheable(Strongly Ordered) */
    };
};
```

或者在代码中手动维护cache一致性：

```c
/* 发送方: 写入后刷cache */
memcpy(buffer, &data, sizeof(data));
/* ARM: 清理D-cache，将数据写入物理内存 */
flush_dcache_range(buffer, buffer + sizeof(data));
/* 然后触发中断通知接收方 */
```

## 7. 性能考量

### 7.1 延迟分析

RPMsg消息的端到端延迟组成：

```
总延迟 = buffer分配 + 数据拷贝 + vring更新
       + 中断传递 + 中断处理 + 数据读取
```

典型数据(STM32MP1 @ 650MHz A7 / 209MHz M4)：

| 消息大小 | 单次延迟 | 吞吐量 |
|----------|----------|--------|
| 64 字节 | 30-50 us | ~1.2 MB/s |
| 256 字节 | 40-70 us | ~3.5 MB/s |
| 512 字节 | 50-90 us | ~5.0 MB/s |

### 7.2 缓冲区调优

关键参数与取舍：

| 参数 | 增大的影响 |
|------|-----------|
| vring descriptor数量 | 更多并发消息，但占用更多共享内存 |
| 单个buffer大小 | 支持更大的消息，但小消息浪费空间 |
| buffer pool总量 | 减少分配失败概率，但增加内存占用 |

建议根据实际业务调整。传感器数据通常是小消息(16-64字节)，可以用小buffer多描述符的配置；图像传输则需要大buffer。

### 7.3 零拷贝优化

标准RPMsg需要两次拷贝(用户空间到内核，内核到共享内存)。对性能敏感的场景，可以考虑：

- 使用DMA将数据直接搬到共享内存
- 在RPMsg buffer中直接构造数据(避免中间拷贝)
- 使用RPMsg byte buffer模式(部分平台支持)

## 总结

RPMsg为IoT SoC中的异构多核通信提供了标准化框架。核心要点回顾：

1. **架构三层**：RPMsg端点 -> virtio vring -> 共享内存+mailbox中断，每层职责清晰
2. **无锁设计**：vring的available/used双环机制让收发双方各写各的，避免锁竞争
3. **生命周期管理**：remoteproc负责远程核的加载、启动、监控和崩溃恢复
4. **服务复用**：命名端点让多个服务共享一条物理链路，互不干扰
5. **实战关键**：共享内存必须non-cacheable或手动维护cache一致性，这是最常见的坑

在IoT场景中，RPMsg让"Linux管云端、RTOS管实时"的分工成为可能，两者通过高效的消息传递协作，各取所长。

## 参考文献

1. Linux Kernel Documentation, "Remote Processor Framework (remoteproc)", kernel.org
2. OpenAMP Project, "librpmsg and RPMsg-lite Implementation Guide", openamp.github.io
3. STMicroelectronics, "STM32MP1 RPMsg usage and Inter-Processor Communication", AN5604
4. NXP, "i.MX Linux User's Guide: RPMsg and Inter-Processor Communication", NXP Documentation
5. Virtio Specification v1.1, "Virtqueues and Used/Available Rings", oasis-open.org
