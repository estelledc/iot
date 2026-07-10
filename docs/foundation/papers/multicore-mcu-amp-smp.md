---
schema_version: '1.0'
id: multicore-mcu-amp-smp
title: 多核MCU的AMP与SMP运行模式分析
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
# 多核MCU的AMP与SMP运行模式分析

> **难度**：🔴 高级 | **领域**：多核嵌入式系统 | **阅读时间**：约 22 分钟

## 引言

想象你经营一家餐厅。如果两个厨师共享同一本菜谱、同一口锅、同一个灶台，谁先用谁后用得商量着来，这就是 SMP (Symmetric Multi-Processing) -- 对称多处理，所有核心对等，共享一切资源，由一个"大厨长"(操作系统)统一调度。如果两个厨师各管各的灶台，一个专做凉菜一个专炒热菜，偶尔通过传菜窗口递个消息，这就是 AMP (Asymmetric Multi-Processing) -- 非对称多处理，各核心独立运行，各司其职，通过明确接口协作。

单核 MCU 的时代正在结束。IoT 设备同时要做实时控制、网络通信、AI 推理，一个核心已经力不从心。但"多核"远不止"把核心数加一"那么简单 -- 两个核心怎么共享内存、怎么通信、怎么避免踩彼此的脚，才是真正的硬骨头。本文从 AMP 和 SMP 两种多核范式入手，结合 STM32H7、RP2040、ESP32 三款典型芯片，拆解多核 MCU 的设计全貌。

## 1. 多核基础：为什么单片机也需要"多核"

### 1.1 单核的瓶颈

单核 MCU 提升性能的传统手段是拉高主频，但这带来三个问题：

- **功耗墙**：动态功耗与主频近似线性关系，Cortex-M7 在 600 MHz 时功耗已达 mW 级别
- **实时性冲突**：Wi-Fi 协议栈长时间关中断会让电机控制抖动
- **功能安全**：IEC 61508 要求 ASIL-D 级别的系统需要硬件冗余

### 1.2 AMP 与 SMP 的本质区别

| 维度 | AMP | SMP |
|------|-----|-----|
| 核心关系 | 不对等，各运行独立 OS/裸机 | 对等，共享一个 OS 实例 |
| 内存视图 | 各核心有私有区域，共享区需显式管理 | 统一地址空间，OS 统一管理 |
| 调度策略 | 各核心自行调度，无全局调度器 | 全局调度器均衡负载 |
| 通信方式 | 显式 IPC (共享内存/邮箱/信号量) | 原子操作/自旋锁/互斥锁 |
| 典型场景 | 实时核 + 通信核 | 通用计算加速 |

## 2. AMP 模式详解

### 2.1 AMP 的核心思想

AMP 的设计哲学是"分而治之"：每个核心有自己的职责、自己的固件、自己的内存区域。核心之间通过明确定义的接口通信，而不是共享操作系统状态。凉菜厨师不需要知道热菜厨师在用什么锅，只需要在传菜窗口看到"3 号桌凉菜已上"的纸条就够了。

### 2.2 资源划分 (Resource Partitioning)

AMP 系统最关键的设计决策是资源划分。以 STM32H747 为例：

```
STM32H747 资源划分方案:

  Cortex-M7 (Core 0)              Cortex-M4 (Core 1)
  +-------------------------+     +-------------------------+
  | DTCM: 128 KB (私有)     |     | SRAM1: 128 KB (私有)    |
  | ITCM: 64 KB (私有)      |     | SRAM2: 128 KB (私有)    |
  +-------------------------+     +-------------------------+
  | AXI SRAM: 256 KB (共享)                             |
  |   Core 0 写命令, Core 1 写状态                      |
  +-----------------------------------------------------+
  | 外设: TIM1/TIM2/ADC (Core0)  USART1/SPI3/ETH (Core1) |
  +-----------------------------------------------------+
```

资源划分黄金原则：私有优先、共享最小化、外设独占。

### 2.3 核间通信机制

#### 共享内存 (Shared Memory)

最基础也最灵活的方式，两个核心通过双方均可访问的 SRAM 交换数据。

```c
// 共享内存环形缓冲区 (位于共享 SRAM)
#define SHM_BASE  0x24000000

typedef struct {
    volatile uint32_t head;       // Core 0 写入位置
    volatile uint32_t tail;       // Core 1 读取位置
    uint32_t         size;
    uint8_t          data[4096];
} RingBuffer;

RingBuffer* g_tx_buf = (RingBuffer*)SHM_BASE;

// Core 0 (生产者)
int send_to_core1(const uint8_t* payload, uint32_t len) {
    uint32_t next = (g_tx_buf->head + len) % g_tx_buf->size;
    if (next == g_tx_buf->tail) return -1;  // 满
    for (uint32_t i = 0; i < len; i++) {
        g_tx_buf->data[g_tx_buf->head] = payload[i];
        g_tx_buf->head = (g_tx_buf->head + 1) % g_tx_buf->size;
    }
    HAL_HSEM_FastTake(HSEM_ID_0);  // 通知 Core 1
    HAL_HSEM_Release(HSEM_ID_0);
    return len;
}
```

`volatile` 关键字不可省略：它阻止编译器优化掉对共享变量的访问。

#### 邮箱 (Mailbox)

硬件级消息传递，一个核心写入寄存器，另一个核心收到中断。通知开销极低，但消息长度受限(通常几个字节)，大数据仍需共享内存。

#### 硬件信号量 (Hardware Semaphore)

MCU 缺少 cache 一致性协议，软件自旋锁不可靠，必须依赖硬件信号量互斥。

```c
#define HSEM_ID_SHARED_BUF  8

void core0_access_shared(void) {
    while (HAL_HSEM_Take(HSEM_ID_SHARED_BUF, 0) != HAL_OK);  // 阻塞获取
    shared_data->sensor_value = read_sensor();
    HAL_HSEM_Release(HSEM_ID_SHARED_BUF, 0);  // 释放, 0 = Core 0 ID
}
```

### 2.4 OpenAMP 框架

OpenAMP 提供标准化的 AMP 通信接口，核心抽象是 RPMsg (Remote Processor Messaging)。

```
OpenAMP 软件栈:

  +-----------------------------------+
  |  应用层 (Core 0: 控制 / Core 1: 通信) |
  +-----------------------------------+
  |  RPMsg (消息传递, 多通道 endpoint)   |
  +-----------------------------------+
  |  VirtIO (环形缓冲区 + 信号通知)      |
  +-----------------------------------+
  |  Metal (硬件抽象: 共享内存/中断)     |
  +-----------------------------------+
  |  硬件 (共享 SRAM + 邮箱 + HSEM)     |
  +-----------------------------------+
```

```c
// OpenAMP RPMsg 使用示例 (Core 0 端)
static struct rpmsg_endpoint ept;

static int rpmsg_recv_cb(struct rpmsg_endpoint *ept,
                          void *data, size_t len,
                          uint32_t src, void *priv) {
    process_response((uint8_t*)data, len);
    return 0;
}

void amp_comm_init(void) {
    rpmsg_create_ept(&ept, rpdev, "comm-channel",
                      RPMSG_ADDR_ANY, RPMSG_ADDR_ANY,
                      rpmsg_recv_cb, NULL);
    const char *cmd = "START_SAMPLING:1000";
    rpmsg_send(&ept, cmd, strlen(cmd));
}
```

OpenAMP 的价值在于**标准化**：不同厂商 MCU 用同一套 API 做核间通信，应用代码可移植。

## 3. SMP 模式详解

### 3.1 SMP 的核心思想

SMP 让所有核心运行同一个 OS 实例，调度器自动分配任务到空闲核心。对应用开发者来说，多核是透明的 -- 你创建任务，OS 决定在哪个核上跑。

### 3.2 Cache 一致性问题

SMP 的最大技术挑战。Cortex-M 没有硬件一致性协议(不像 Cortex-A 的 ACE/CHI)，必须软件解决。

```
Core 0 D-Cache: val=42 (本地缓存)
Core 1 D-Cache: val=0  (过期缓存!)
主存 SRAM:      val=42 (Core 0 已写回)

问题: Core 1 读到的是过期值 0
```

| 策略 | 原理 | 适用场景 |
|------|------|----------|
| Non-Cacheable | 不缓存，每次直接访问主存 | 高频共享数据量小 |
| clean/invalidate | 写入后 clean，读取前 invalidate | 数据量大但更新频率低 |
| HSEM + cache 操作 | 获取锁 invalidate，释放锁 clean | 通用场景 |
| TCM 共享 | TCM 不经过 cache，天然一致 | 延迟敏感的共享数据 |

```c
// FreeRTOS SMP 手动维护 cache 一致性
void task_on_core0(void *pv) {
    while (1) {
        xSemaphoreTake(g_shared_mutex, portMAX_DELAY);
        SCB_InvalidateDCache_by_Addr((uint32_t*)&g_shared, sizeof(g_shared));
        g_shared.sensor_count++;
        SCB_CleanDCache_by_Addr((uint32_t*)&g_shared, sizeof(g_shared));
        xSemaphoreGive(g_shared_mutex);
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}
```

### 3.3 FreeRTOS SMP 移植

FreeRTOS V11.0 起提供官方 SMP 移植，支持多核 Cortex-M 和 RISC-V。

```c
// FreeRTOS SMP 配置
#define configNUMBER_OF_CORES       2    // 核心数
#define configUSE_CORE_AFFINITY     1    // 启用核心亲和性

void app_main(void) {
    // 电机控制: 绑定 Core 0
    xTaskCreateAffinitySet(motor_control_task, "Motor",
        1024, NULL, configMAX_PRIORITIES-1, (1 << 0), NULL);
    // 通信: 绑定 Core 1
    xTaskCreateAffinitySet(wifi_comm_task, "WiFi",
        2048, NULL, tskIDLE_PRIORITY + 2, (1 << 1), NULL);
    vTaskStartScheduler();
}
```

SMP 下锁的选择：互斥锁适合长临界区(阻塞让出 CPU)，自旋锁适合极短临界区(忙等，ISR 中唯一选择)。

## 4. 三款芯片实战对比

### 4.1 STM32H747: M7 + M4 (AMP 典范)

异构双核，天生为 AMP 设计。

| 特性 | Cortex-M7 (Core 0) | Cortex-M4 (Core 1) |
|------|---------------------|---------------------|
| 主频 | 480 MHz | 240 MHz |
| 私有 RAM | DTCM 128KB + ITCM 64KB | SRAM2 128KB |
| 浮点 | 双精度 FPU | 单精度 FPU |

典型分工：M7 做电机 FOC 控制和传感器融合，M4 跑 Wi-Fi/BLE 协议栈和 MQTT。启动流程：Core 0 先启动 -> 初始化共享资源 -> `HAL_PWREx_ReleaseCore1()` 释放 Core 1 -> 两侧各初始化 OpenAMP。

### 4.2 RP2040: 双核 M0+ (轻量 AMP)

不到 $1 的双核 MCU，核间通信用硬件 FIFO (每个方向 4 个 32 位字)。

```c
// RP2040 双核 (Pico SDK)
#include "pico/multicore.h"

void core1_entry(void) {
    while (1) {
        uint32_t cmd = multicore_fifo_pop_blocking();
        if (cmd == CMD_READ_SENSOR)
            multicore_fifo_push_blocking(read_adc());
    }
}

int main(void) {
    stdio_init_all();
    multicore_launch_core1(core1_entry);
    while (1) {
        multicore_fifo_push_blocking(CMD_READ_SENSOR);
        uint32_t val = multicore_fifo_pop_blocking();
        printf("Sensor: %lu\n", val);
        sleep_ms(100);
    }
}
```

设计哲学"够用就好"：两个 M0+ 各跑裸机，用 FIFO 传命令和结果。

### 4.3 ESP32: 双核 LX6 (混合模式)

最"模糊"AMP/SMP 边界的芯片：默认 SMP (FreeRTOS 统一调度)，但通过核心亲和性实现类 AMP 分工。

```c
// ESP32: SMP 调度 + 核心绑定
void app_main(void) {
    xTaskCreatePinnedToCore(wifi_task,    "WiFi",   4096, NULL, 2, NULL, 0);  // Core 0
    xTaskCreatePinnedToCore(control_task, "Control", 2048, NULL, 5, NULL, 1);  // Core 1
}
```

ESP32 特殊处理：Core 0 负责 Wi-Fi/BLE 协议栈(底层中断绑定)，用户实时任务绑 Core 1 避免干扰。这是"AMP 思维在 SMP 框架内"的典型案例。

### 4.4 综合对比

| 维度 | STM32H747 | RP2040 | ESP32 |
|------|-----------|--------|-------|
| 核心组合 | M7+M4 (异构) | M0+x2 (同构) | LX6x2 (同构) |
| 默认模式 | AMP | AMP (裸机) | SMP |
| 核间通信 | OpenAMP/HSEM | 硬件 FIFO | FreeRTOS 原语 |
| Cache | 需软件维护 | 无 cache | 需软件维护 |
| 价格 | $12-18 | $0.7 | $2.5 |

## 5. IoT 场景选型与性能

### 5.1 实时核 + 通信核模式

IoT 领域最常见的 AMP 模式：一个核心做硬实时控制，另一个跑网络协议栈。核心价值：Wi-Fi 重连导致 Core 1 卡 200 ms，电机控制环路仍稳定运行。

```
选型决策树:

需要硬实时控制?
├── 是 → 抖动 < 50 us?
│   ├── 是 → AMP (电机控制/PLC/机器人)
│   └── 否 → SMP + 核心亲和性 (智能家居)
└── 否 → 计算密集?
    ├── 是 → SMP (边缘 AI/信号处理)
    └── 否 → 单核够了 (简单传感器上报)
```

### 5.2 性能考量

多核不等于双倍性能，三个因素制约加速比：

1. **Amdahl 定律**：30% 串行代码时理论上限 1.54x
2. **通信开销**：共享内存每 1 KB 约 50-100 周期 cache 操作开销
3. **资源竞争**：双核实测加速往往只有 1.3-1.7x

```
STM32H747 Dhrystone 实测:
  单核 M7:          576 DMIPS
  双核理论:          726 DMIPS
  双核 (无竞争):     680 DMIPS (93.7%)
  双核 (共享 SRAM):  620 DMIPS (85.4%)
  双核 (共享 Flash): 550 DMIPS (75.8%)
  Flash 竞争是最大杀手! 关键代码放 ITCM
```

## 6. 多核调试

### 6.1 常见 Bug 模式

| Bug | 症状 | 根因 | 排查 |
|-----|------|------|------|
| Cache 一致性 | Core 1 读到旧值 | D-Cache 未维护 | 共享访问前后加 clean/invalidate |
| 资源竞争 | 外设行为随机 | 两核心同时操作 | 检查外设分配表 + HSEM |
| 死锁 | 双核同时卡住 | 信号量获取顺序不一致 | 画依赖图，统一顺序 |
| 启动时序 | Core 1 读到未初始化数据 | Core 1 先于 Core 0 启动 | Core 0 写就绪标志 |
| 优先级反转 | 实时任务抖动 | 低优先级持锁被中优先级抢占 | 用优先级继承 mutex |

### 6.2 调试实践

1. 共享变量加入 Watch 窗口，同时观察两个核心视角
2. 两核心日志用同一硬件定时器 (DWT_CYCCNT) 做时间戳

```c
// 多核日志同步
static inline uint32_t get_timestamp(void) {
    return DWT->CYCCNT;  // 两核心访问同一计数器
}
void core0_log(const char* msg) {
    printf("[%010lu][C0] %s\n", get_timestamp(), msg);
}
```

3. 先单核验证再双核集成
4. 死锁时读 HSEM "谁持有锁" 寄存器快速定位

## 7. 混合模式与未来趋势

实际项目中 AMP 和 SMP 并非非此即彼。混合模式：AMP 分域(两核心各跑独立 FreeRTOS)，域内用 SMP 调度，域间通过 OpenAMP 通信。

未来趋势：

- **三核/四核 MCU**：STM32H7Rx (M7+M7+M4)、ESP32-P4 (双核 RISC-V)，通信拓扑更复杂
- **硬件 cache 一致性**：CoreLink 控制器向 Cortex-M 渗透，MCU 也将自动维护一致性
- **RISC-V 多核**：P extension 和自定义指令让协作更灵活，但生态需时间
- **功能安全**：ISO 26262/IEC 61508 对多核认证趋严，锁步核和异构冗余成趋势

## 总结

AMP 和 SMP 代表多核设计的两种哲学：AMP 信奉"各管各的，明确接口"，SMP 信奉"统一调度，透明并行"。在 IoT 嵌入式领域，AMP 的"实时核 + 通信核"模式是最常见的实战选择。

关键要点：

1. **AMP 适合职责分明的场景**：核心间有清晰功能边界，通信频率和量可控
2. **SMP 适合计算密集型场景**：需负载均衡而非职责隔离
3. **Cache 一致性是 SMP 核心难题**：MCU 缺硬件一致性协议，必须软件方案
4. **OpenAMP 是 AMP 事实标准**：跨平台可移植的核间通信 API
5. **混合模式是实战最优解**：AMP 分域 + SMP 域内调度，兼得确定性和灵活性
6. **多核性能非线性增长**：通信开销、总线竞争和 Amdahl 定律限制加速比

选择 AMP 还是 SMP，不是技术信仰问题，而是看你能不能把"实时性"和"吞吐量"这对矛盾在架构层面拆开。

## 参考文献

1. ARM. *ARMv7-M Architecture Reference Manual (DDI 0403)*. ARM Ltd., 2020. -- Cortex-M 系列多核总线与内存模型定义
2. OpenAMP Project. *OpenAMP Library Documentation v0.3*. https://github.com/OpenAMP/open-amp, 2023. -- OpenAMP 框架 API 与实现细节
3. STMicroelectronics. *STM32H747/757 Reference Manual (RM0399)*. ST, 2023. -- STM32H7 双核寄存器、HSEM、邮箱详细定义
4. Raspberry Pi Foundation. *RP2040 Datasheet*. https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf, 2023. -- RP2040 双核 FIFO 与 SIO 模块描述
5. Espressif Systems. *ESP-IDF Programming Guide: FreeRTOS SMP*. https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/freertos.html, 2024. -- ESP32 FreeRTOS SMP 移植与核心绑定 API
