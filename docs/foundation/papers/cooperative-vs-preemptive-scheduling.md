# 协作式与抢占式调度在资源受限设备中的权衡
> **难度**：🟡 中级 | **领域**：嵌入式调度策略 | **阅读时间**：约 20 分钟

## 引言

想象一条单车道的乡间小路：只有一辆车能在路上开，其他车必须在路口等。如果每个司机都自觉 -- 开到路口主动靠边让下一位走，这就是协作式调度；如果路边有个交警，定时按红绿灯强制换车，那就是抢占式调度。前者靠自觉，简单高效但可能被一个"霸路司机"堵死；后者靠强制，公平可控但每次换车都要搬上搬下货物 (上下文切换开销)。

在资源受限的 IoT 设备上，这个选择决定了 RAM 预算、最坏响应时间、代码复杂度乃至调试难度。本文从栈开销、响应时间、共享资源安全、实时保证四个维度系统对比，并给出 IoT 场景选择建议。

## 1. 调度模型基础

### 1.1 协作式调度 (Cooperative Scheduling)

核心思想：任务获得 CPU 后一直运行，直到主动让出 (yield)。没有外部机制能打断正在执行的任务。

```c
// protothreads 协作式示例
#include "pt.h"
static struct pt pt_sensor, pt_comm;

static PT_THREAD(sensor_thread(struct pt *pt)) {
    PT_BEGIN(pt);
    while (1) {
        read_sensor();
        PT_YIELD(pt);           // 主动让出, 下次从这里恢复
        process_data();
        PT_YIELD(pt);
    }
    PT_END(pt);
}
```

关键特征：切换只发生在 yield 点，位置完全可预测；不需要定时器中断驱动调度；protothreads 仅 2 字节/任务 RAM。

### 1.2 抢占式调度 (Preemptive Scheduling)

核心思想：内核通过 tick 中断强制暂停当前任务，切换到更高优先级就绪任务。

```c
// FreeRTOS 抢占式示例
void sensor_task(void *pv) {
    while (1) {
        read_sensor();       // 随时可能被抢占
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}
void comm_task(void *pv) {   // 高优先级, 可抢占 sensor_task
    while (1) {
        check_radio();
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}
```

关键特征：tick 中断 (通常 1ms) 定期触发调度判断；高优先级可随时抢占低优先级；需完整的上下文保存/恢复。

### 1.3 直观时序对比

```
协作式 (无抢占):                      抢占式 (tick=5ms):
Time: 0---5---10--15--20--25--30      Time: 0---5---10--15--20--25--30
TaskA: [====]       [====]            TaskA: [=]    [=]   [=]  [===]
TaskB:      [====]       [====]       TaskB:    [===]  [===]   [=]
       ^yield  ^yield                    ^preempt ^preempt
```

## 2. 栈开销对比

### 2.1 为什么抢占式需要更多栈

抢占式中每个任务必须有独立且足够大的栈，因为 tick 中断随时发生，栈须容纳寄存器保存区 + 嵌套中断预留 + 安全裕量。协作式不需要这些。

```
协作式任务栈:               抢占式任务栈:
+------------------+       +------------------+
| 局部变量         |       | 局部变量         |
+------------------+       +------------------+
| 函数调用链       |       | 函数调用链       |
+------------------+       +------------------+
| (无中断帧)       |       | 中断帧 (16-64B)  | <-- Cortex-M4: 64B
+------------------+       +------------------+
                           | 安全裕量 (~20%)  |
                           +------------------+
```

### 2.2 量化对比 (ARM Cortex-M4)

| 项目 | 协作式 | 抢占式 |
|------|--------|--------|
| 中断帧大小 | 0 B | 64 B (含 FPU) |
| 每任务栈推荐 | 128-256 B | 256-512 B |
| 4 任务总栈 | 512 B - 1 KB | 1 KB - 2 KB |
| 共享栈 | 可以 (protothreads) | 不可以 |

8 KB RAM 的 MCU 上，4 个抢占式任务吃掉 25% RAM 仅用于栈；协作式仅 6-12%。

### 2.3 协作式的栈共享技巧

protothreads 所有协程共享调用栈，每个只保存一个 `unsigned short` (2 字节) 作为恢复点：

```c
static struct pt pt1, pt2, pt3; // 3 个任务仅占 6 字节!
void scheduler(void) {
    while (1) {
        PT_SCHEDULE(protothread1(&pt1));
        PT_SCHEDULE(protothread2(&pt2));
        PT_SCHEDULE(protothread3(&pt3));
    }
}
```

这让 protothreads 在 MSP430 (仅 512 B RAM) 上也能跑多任务。

## 3. 响应时间分析

### 3.1 协作式：受制于最长任务段

```
                    事件发生
                       |
TaskA: [===========长任务段===========] yield
                                       |
TaskB:                             [响应] <-- 延迟 = TaskA 段执行时间
```

最坏响应时间 = max(任务段执行时间)。如果任务段没有 yield，系统"卡住"。

### 3.2 抢占式：中断延迟 + 临界区

```
                    事件发生
                       |<-中断延迟->|<-调度开销->|
TaskA (低): [====临界区====]..........|
TaskB (高):                             [立即响应]

R_preemptive = t_interrupt + t_scheduler + t_critical_max
```

### 3.3 对比总结

| 指标 | 协作式 | 抢占式 |
|------|--------|--------|
| 典型响应 | 1-50 ms | 5-50 us |
| 最坏响应 | 最长任务段时间 | 中断延迟 + 临界区 |
| 可预测性 | 取决于代码质量 | 取决于临界区设计 |
| 硬实时可行 | 通常不可行 | 可行 (需仔细分析) |

STM32L476 (80 MHz) 实测：协作式 max 9.8 ms vs 抢占式 max 42.7 us，差距约 200 倍。

## 4. 共享资源安全性

### 4.1 协作式：天然安全

一个任务执行时其他任务不可能运行，就像单车道路口，不存在撞车风险：

```c
// 协作式: 无需任何保护
static sensor_data_t g_data;
void sensor_task(void) {
    g_data.temperature = read_temp();
    g_data.humidity = read_humidity();
    g_data.valid = true;    // yield 前写完, 其他任务看到一致状态
    yield();
}
```

### 4.2 抢占式：竞态风险 + 互斥锁

高优先级任务可能抢占低优先级任务，读到半更新状态。必须用互斥锁：

```c
static SemaphoreHandle_t xDataMutex;
void sensor_task(void) {
    xSemaphoreTake(xDataMutex, portMAX_DELAY);
    g_data.temperature = read_temp();
    g_data.humidity = read_humidity();
    g_data.valid = true;
    xSemaphoreGive(xDataMutex);
    vTaskDelay(pdMS_TO_TICKS(100));
}
```

### 4.3 同步机制开销对比

| 同步需求 | 协作式 | 抢占式 |
|---------|--------|--------|
| 简单变量 | 无需保护 | 关中断或原子操作 |
| 结构体 | 无需保护 | 互斥锁 |
| 队列/缓冲区 | 无锁实现 | 互斥锁或环形缓冲区 + 关中断 |
| 互斥锁 RAM | 0 B | ~80 B/个 (FreeRTOS) |
| 优先级反转 | 不存在 | 存在 (需优先级继承) |

优先级反转是抢占式特有的经典问题：低优先级持锁 -> 中优先级抢占低 -> 高优先级间接被中阻塞。协作式不存在此问题。

## 5. 实时性保证

### 5.1 硬实时 vs 软实时

- **硬实时**：错过截止时间 = 灾难 (安全气囊、电机控制)
- **软实时**：偶尔错过可接受 (温度上报、UI 刷新)

| 系统类型 | 适合协作式 | 适合抢占式 |
|---------|-----------|-----------|
| 硬实时控制 (< 100us) | 不适合 | 适合 |
| 硬实时通信 (< 1ms) | 不适合 | 适合 |
| 软实时传感 (100ms 级) | 适合 | 适合但过度 |
| 后台数据处理 | 适合 | 适合但过度 |

### 5.2 可调度性分析

抢占式有经典 RMA (速率单调分析)：高频任务分配高优先级，可调度性充分条件 Σ(Ui) <= n(2^(1/n) - 1)。

协作式没有等价理论，但有工程准则：

```
1. 所有任务段执行时间 < 系统最短截止时间
2. 总 CPU 利用率 < 70% (留足裕量)
3. yield 点之间无无限循环
4. ISR 尽可能短, 只设标志位
```

### 5.3 中断与调度配合

协作式中 ISR 只设标志，任务轮询标志处理：

```c
volatile bool g_radio_irq = false;
void RADIO_IRQHandler(void) { g_radio_irq = true; }  // 极短 ISR
void comm_task(void) {
    while (1) {
        if (g_radio_irq) { process_radio_event(); g_radio_irq = false; }
        yield();
    }
}
```

抢占式中 ISR 直接唤醒高优先级任务，延迟更低：

```c
void RADIO_IRQHandler(void) {
    BaseType_t xWoken = pdFALSE;
    xSemaphoreGiveFromISR(xRadioSem, &xWoken);
    portYIELD_FROM_ISR(xWoken);  // 退出 ISR 后立即切换到高优先级任务
}
```

## 6. 典型实现对比

### 6.1 Contiki (协作式)

IoT 领域最著名的协作式 OS，用于无线传感器网络。所有进程共享栈，每进程仅占 ~20 B，事件驱动，天然协作式。

### 6.2 FreeRTOS (抢占式)

默认抢占式，也支持协作模式 (`configUSE_PREEMPTION = 0`)。可在抢占环境中用 `taskYIELD()` 实现协作式任务，形成混合模式。

### 6.3 protothreads (极简协作式)

Adam Dunkels 设计，仅 ~50 行代码，每任务 2 B RAM。局限：不能用 switch-case，局部变量 yield 后丢失，无阻塞 I/O。

### 6.4 实现复杂度对比

| 指标 | protothreads | Contiki | FreeRTOS (抢占) |
|------|-------------|---------|----------------|
| 内核代码量 | ~50 行 | ~2000 行 | ~5000 行 |
| 最小 RAM/任务 | 2 B | ~20 B | ~200 B |
| 最小 ROM | ~100 B | ~10 KB | ~6 KB |
| 学习曲线 | 极低 | 中等 | 中等 |
| 调试难度 | 低 | 低 | 中-高 |

## 7. 混合策略

### 7.1 抢占 + 协作分层模型

```
+-------------------------------------------+
| 抢占层: ISR + 高优先级实时任务             |
|   (通信接收, 安全监控, 硬件控制)           |
+-------------------------------------------+
| 协作层: 低优先级任务循环                   |
|   (数据处理, 日志记录, UI 更新)            |
+-------------------------------------------+
| 空闲层: 低功耗休眠                         |
+-------------------------------------------+
```

```c
// FreeRTOS 混合策略
void radio_irq_task(void *pv) {     // 优先级 3: 抢占式, 实时响应
    while (1) { ulTaskNotifyTake(pdTRUE, portMAX_DELAY); process_radio_isr(); }
}
void comm_task(void *pv) {          // 优先级 2: 抢占式
    while (1) { xQueueReceive(xTxQueue, &pkt, portMAX_DELAY); transmit_packet(&pkt); }
}
void data_task(void *pv) {          // 优先级 1: 协作式, 分块处理
    while (1) { process_data_chunk(); vTaskDelay(1); aggregate_stats(); vTaskDelay(1); }
}
```

### 7.2 Zephyr 的逐任务调度策略

```c
// Zephyr: 可逐任务设置 K_COOPERATIVE 或 K_PREEMPT
K_THREAD_DEFINE(sensor_tid, 256, sensor_entry, NULL, NULL, NULL, -5, K_COOPERATIVE, 0);
K_THREAD_DEFINE(comm_tid,   512, comm_entry,   NULL, NULL, NULL, -10, K_PREEMPT, 0);
// 协作式任务不会被同/低优先级抢占, 但高优先级抢占式任务仍可抢占它
```

## 8. 调试差异

### 8.1 协作式：确定性带来的便利

- 可复现：相同输入永远产生相同执行顺序
- yield 点可预测：上下文切换只在已知位置
- 无竞态条件，无死锁可能
- 栈溢出少见 (共享栈 + 浅调用链)

### 8.2 抢占式：非确定性带来的挑战

- 时序依赖 bug：只在特定调度顺序下触发，难以复现
- 优先级反转：偶发性长延迟，需专门工具检测
- 死锁：多个互斥锁获取顺序不当
- 栈溢出：独立栈难以精确预估

```c
// 抢占式调试辅助
#define configCHECK_FOR_STACK_OVERFLOW  2  // FreeRTOS 栈溢出检测
void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName) {
    printf("STACK OVERFLOW in %s\n", pcTaskName);
}
// 互斥锁超时检测 (不用 portMAX_DELAY)
if (xSemaphoreTake(xMutex, pdMS_TO_TICKS(100)) != pdTRUE)
    log_warning("Mutex timeout, possible deadlock");
```

| 调试维度 | 协作式 | 抢占式 |
|---------|--------|--------|
| 时序 bug | 极少 | 常见 |
| 竞态/死锁 | 不存在 | 需仔细排查 |
| 栈溢出 | 少见 | 常见 |
| 可复现性 | 高 | 低 |
| 需要工具 | 打印即可 | 逻辑分析仪 + 追踪 |

## 9. IoT 场景选择指南

### 9.1 适合协作式的场景

1. **无线传感器网络节点** -- RAM < 10 KB，功耗优先，采集间隔秒级，无硬实时
2. **简单家电控制** -- 任务 < 5 个，响应 100ms 级，成本极度敏感
3. **环境监测终端** -- 定时采集 + 周期上报，大部分时间休眠，数据丢失可容忍

### 9.2 适合抢占式的场景

1. **工业物联网网关** -- 多协议并行，通信 < 1ms，RAM > 64 KB
2. **可穿戴健康监测** -- 高频采样 + 蓝牙实时传输，异常告警需立即响应
3. **智能家居中枢** -- 多设备管理，语音交互低延迟，复杂优先级需求

### 9.3 决策流程

```
是否有硬实时要求 (< 1ms)?
  |-- 是 --> RAM > 32KB?
  |            |-- 是 --> 抢占式
  |            |-- 否 --> 混合策略 (关键路径抢占)
  |-- 否 --> 任务数 < 5 且无复杂优先级?
               |-- 是 --> 协作式 (简单可靠)
               |-- 否 --> 抢占式或混合
```

## 总结

协作式与抢占式调度不是非此即彼，而是资源受限设备上的工程权衡：

| 维度 | 协作式 | 抢占式 | 混合 |
|------|--------|--------|------|
| RAM 开销 | 极低 (2-20 B/任务) | 中等 (200-512 B/任务) | 中等 |
| 响应时间 | ms 级 | us 级 | 分层 |
| 资源安全 | 天然安全 | 需同步原语 | 分层 |
| 实时保证 | 软实时 | 硬实时 | 可达硬实时 |
| 代码复杂度 | 低 | 中-高 | 中 |
| 调试难度 | 低 | 高 | 中 |
| 典型应用 | WSN, 简单家电 | 工业网关, 可穿戴 | 复杂 IoT 设备 |

选择建议：
- 资源极度受限 + 软实时 -> 协作式 (Contiki/protothreads)
- 硬实时 + RAM 充裕 -> 抢占式 (FreeRTOS)
- 两者兼需 -> 混合策略 (Zephyr / FreeRTOS 分层)

核心原则：**用最简单的机制满足需求**。协作式够用时不引入抢占式复杂度；硬实时不可妥协时不在协作式上勉强。

## 参考文献

1. Dunkels A, et al. "Protothreads: Simplifying Event-Driven Programming of Memory-Constrained Embedded Systems." Proc. ACM SenSys, 2006.
2. Barry R. "Using the FreeRTOS Real Time Kernel: A Practical Guide." Real Time Engineers Ltd, 2016.
3. Buttazzo G. "Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications." Springer, 4th ed., 2011.
4. Levis P, et al. "The Trickle Algorithm." RFC 6206, IETF, 2011.
5. Zephyr Project. "Zephyr RTOS Kernel Documentation: Scheduling." https://docs.zephyrproject.org/latest/kernel/services/scheduling/
