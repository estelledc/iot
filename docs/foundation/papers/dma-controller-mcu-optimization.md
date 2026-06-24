# DMA控制器在MCU数据搬运中的优化策略
> **难度**：🟡 中级 | **领域**：嵌入式数据传输 | **阅读时间**：约 20 分钟

## 引言

想象一家餐厅：厨师(CPU)本来要自己把菜从厨房端到每桌客人面前，每次端菜都占用了他做菜的时间。DMA 就像雇了一个专门的传菜员，厨师只需要告诉传菜员"把第 1 号到第 8 号菜端到 A 区"，然后继续做菜，传菜员会自动完成搬运，端完再通知厨师。

在 MCU 系统中，大量数据搬运任务(ADC 采样、UART 接收、SPI 收发)如果全靠 CPU 逐字节处理，不仅浪费算力，还会因中断频繁导致实时性下降。DMA(Direct Memory Access)控制器正是解决这一问题的硬件模块：它独立于 CPU 执行数据搬运，让 CPU 专注于控制逻辑与算法运算。

本文从 DMA 基础原理出发，逐步深入传输模式、通道仲裁、高级特性(FIFO/burst/linked-list)，并结合 ADC/UART/SPI 典型场景给出优化策略，最后讨论 Cortex-M7 上 DMA 与 cache 一致性这一容易踩坑的问题。

## 1. DMA 基础：为什么要卸载 CPU

### 1.1 CPU 搬运的开销

以 115200 baud UART 为例，每秒约 11520 字节。若用中断逐字节接收：

- 每字节触发一次中断，约需 30-50 个时钟周期(入栈/出栈/状态判断)
- 在 72 MHz 主频下，中断开销约占 4.6%-7.7% CPU 时间
- 若同时运行多个外设，中断嵌套导致抖动(jitter)加剧

用 DMA 后，CPU 只需在传输完成时处理一次中断，开销降至可忽略。

### 1.2 DMA 核心能力对比

| 特性 | CPU 搬运 | DMA 搬运 |
|------|----------|----------|
| 搬运执行者 | ALU | DMA 独立总线 |
| 每字节开销 | 取指+译码+执行 | 单周期总线传输 |
| CPU 占用 | 100% | 约 0%(仅配置时) |
| 实时性 | 受中断延迟影响 | 硬件级确定性 |
| 适用场景 | 少量/不规则数据 | 大块/连续数据流 |

### 1.3 何时该用 DMA

- 数据量 > 16 字节且地址连续 --> 推荐 DMA
- 数据量 < 4 字节或极低频率 --> 中断/轮询即可
- 数据不规则(如变长协议帧) --> DMA + 辅助机制(见第 5 节)

## 2. DMA 传输模式

### 2.1 三种基本传输方向

```
(1) Memory-to-Memory (M2M)   : Flash/SRAM --> SRAM, 用途: 缓冲区复制、查表
(2) Peripheral-to-Memory (P2M): ADC/UART/SPI --> SRAM, 用途: 采样、接收
(3) Memory-to-Peripheral (M2P): SRAM --> UART/SPI/DAC, 用途: 发送、输出
```

M2M 模式通常只在特定通道上可用(如 STM32F4 的 DMA2 Stream0)，且不能与外设请求同时使用。

### 2.2 Normal 模式 vs Circular 模式

**Normal 模式**：传输指定数量(N)后自动停止，需软件重新启动。

```c
// Normal 模式配置 (STM32 HAL)
hdma_uart_rx.Init.Mode = DMA_NORMAL;
hdma_uart_rx.Init.MemInc = DMA_MINC_ENABLE;
HAL_DMA_Start(&hdma_uart_rx, SRC_ADDR, DST_ADDR, BUFFER_SIZE);
// 传输完成后触发中断，需手动重启
```

**Circular 模式**：传输完 N 个数据后自动回绕到起始地址，持续运行。

```c
// Circular 模式配置
hdma_adc.Init.Mode = DMA_CIRCULAR;
hdma_adc.Init.MemInc = DMA_MINC_ENABLE;
HAL_DMA_Start(&hdma_adc, ADC_DR_ADDR, (uint32_t)adc_buffer, BUFFER_SIZE);
// 永不停止，配合半传输/全传输中断使用
```

| 对比项 | Normal | Circular |
|--------|--------|----------|
| 传输结束 | 停止，需重启 | 自动回绕，持续运行 |
| 适用场景 | 一次性传输(发一批数据) | 连续数据流(ADC 采样) |
| 溢出风险 | 低(停止即安全) | 需及时消费，否则数据被覆盖 |

### 2.3 Double-Buffer 模式

STM32F4/F7/H7 的部分 DMA Stream 支持双缓冲：当前缓冲区传输时，CPU 可处理另一缓冲区的数据，硬件自动切换，零延迟。

```c
// STM32F4 双缓冲配置
DMA2_Stream3->M0AR = (uint32_t)buffer_a;
DMA2_Stream3->M1AR = (uint32_t)buffer_b;
DMA2_Stream3->CR |= DMA_SxCR_DBM;  // 使能双缓冲
```

时序示意：

```
时间轴: |--- buffer_a 传输 ---|--- buffer_b 传输 ---|--- buffer_a 传输 ---|
CPU:          处理 buffer_b        处理 buffer_a        处理 buffer_b
```

## 3. DMA 通道、流与仲裁

### 3.1 STM32 DMA1/DMA2 架构

以 STM32F407 为例：DMA1/DMA2 各 8 个 Stream，每个 Stream 可选 1 个 Channel(4 选 1)，每个 Stream 有固定的外设映射(参考数据手册 DMA request mapping 表)。

> 关键：同一 Stream 同一时刻只能服务一个外设请求，需查阅映射表避免冲突。

### 3.2 优先级与仲裁

当多个 DMA 请求同时到达，仲裁器按以下规则裁决：

1. **软件优先级**：Very High > High > Medium > Low(4 级)
2. **硬件优先级**：同优先级时，Stream 编号小的优先(Stream0 > Stream1 > ...)

```c
hdma_adc.Init.Priority = DMA_PRIORITY_HIGH;       // ADC 采样优先
hdma_uart_rx.Init.Priority = DMA_PRIORITY_MEDIUM;  // UART 次之
```

设计原则：实时性要求高的(ADC)设 High/Very High；吞吐大的(SPI)设 Medium；低速(UART)设 Low；避免所有通道同优先级。

### 3.3 总线仲裁：DMA vs CPU

DMA 与 CPU 共享 AHB 总线矩阵。DMA 在事务间隙插入传输，不会长时间阻塞 CPU。若两者访问同一 SRAM bank 则产生等待周期；多 SRAM bank 的 MCU(如 STM32H7)可将 DMA 缓冲区放在不同 bank 消除竞争。

## 4. 高级特性：FIFO、Burst 与链表 DMA

### 4.1 FIFO 阈值

STM32F4/F7/H7 的 DMA 每个 Stream 内置 16 字节深度 FIFO：

| 阈值 | 触发传输字节数 | 适用场景 |
|------|---------------|----------|
| 1/4 Full | 4 字节 | 低延迟，小包数据 |
| 1/2 Full | 8 字节 | 平衡模式 |
| 3/4 Full | 12 字节 | 减少总线占用 |
| Full | 16 字节 | 最大吞吐，大块传输 |

FIFO 核心作用是**合并窄带宽外设访问为宽总线传输**：

```
无 FIFO:  外设(8bit) -> AHB(8bit 传输 x 4 次) -> 内存(32bit)
有 FIFO:  外设(8bit) -> FIFO(累积4字节) -> AHB(32bit 传输 x 1 次) -> 内存
```

### 4.2 Burst 传输

Burst 模式允许单次请求传输 4/8/16 个数据节拍，减少总线仲裁次数：

| Burst 大小 | 节拍数 | 适用场景 |
|------------|-------|----------|
| Single | 1 | 通用场景 |
| INCR4 | 4 | 中等吞吐 |
| INCR8 | 8 | 高吞吐 |
| INCR16 | 16 | 超高吞吐(视频/音频) |

```c
hdma.Init.MemBurst = DMA_MBURST_INC4;      // 内存侧 Burst4
hdma.Init.PeriphBurst = DMA_PBURST_SINGLE;   // 外设侧单次
```

> 注意：Burst 传输期间不可被打断，实时性要求高的系统 Burst 不宜超过 INCR4。

### 4.3 链表 DMA：STM32H7 MDMA

STM32H7 引入 MDMA(Master DMA)，支持链表(Linked List)传输：一次配置可执行多段不连续传输，节点间自动跳转，无需 CPU 介入。

```c
// MDMA 链表节点结构 (简化)
typedef struct {
    uint32_t sar;    // 源地址
    uint32_t dar;    // 目的地址
    uint32_t bndtr;  // 传输长度
    uint32_t lar;    // 下一节点地址(链表指针)
} MDMA_LinkNodeTypeDef;

MDMA_LinkNodeTypeDef node1 = {
    .sar = ADC_BUFFER_ADDR, .dar = PROCESS_BUF_A,
    .bndtr = 256, .lar = (uint32_t)&node2,
};
MDMA_LinkNodeTypeDef node2 = {
    .sar = ADC_BUFFER_ADDR + 256*2, .dar = PROCESS_BUF_B,
    .bndtr = 256, .lar = 0,  // 链表结束
};
```

MDMA 适用场景：图像处理(分发摄像头数据)、多通道 ADC 分别存储、大块内存初始化。

## 5. 典型场景优化

### 5.1 DMA + ADC：连续采样

ADC 连续转换 + DMA Circular 模式是最常见的组合：

```c
#define ADC_BUF_SIZE 256
uint16_t adc_buffer[ADC_BUF_SIZE];

// 配置 ADC 连续转换 + DMA Circular
hadc1.Init.ContinuousConvMode = ENABLE;
hadc1.Init.DMAContinuousRequests = ENABLE;
hdma_adc.Init.Mode = DMA_CIRCULAR;
HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_buffer, ADC_BUF_SIZE);

// 半传输中断 -- 处理前半段
void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef* hadc) {
    Process_ADC_Data(&adc_buffer[0], ADC_BUF_SIZE / 2);
}
// 全传输中断 -- 处理后半段
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc) {
    Process_ADC_Data(&adc_buffer[ADC_BUF_SIZE / 2], ADC_BUF_SIZE / 2);
}
```

时序分析：

```
ADC 转换: [0][1][2]...[127][128]...[255][0][1]...
DMA 写入: [======= 前半 =======][======= 后半 =======]
                                 ^ HT中断          ^ TC中断
CPU 处理:        处理前半(0-127)       处理后半(128-255)
```

优化要点：缓冲区大小 >= 采样率 x 处理周期 x 2；使能 HT 中断避免数据覆盖；多通道注意对齐。

### 5.2 DMA + UART：空闲线检测

UART 接收变长帧的核心思路：DMA Circular 持续接收 + UART IDLE 中断判断帧结束。

```c
#define UART_RX_BUF_SIZE 256
uint8_t uart_rx_buf[UART_RX_BUF_SIZE];

void UART_DMA_Init(void) {
    HAL_UART_Receive_DMA(&huart1, uart_rx_buf, UART_RX_BUF_SIZE);
    __HAL_UART_ENABLE_IT(&huart1, UART_IT_IDLE);  // 使能 IDLE 中断
}

void USART1_IRQHandler(void) {
    if (__HAL_UART_GET_FLAG(&huart1, UART_FLAG_IDLE)) {
        __HAL_UART_CLEAR_IDLEFLAG(&huart1);
        uint32_t remain = __HAL_DMA_GET_COUNTER(&hdma_usart1_rx);
        uint32_t recv_len = UART_RX_BUF_SIZE - remain;
        Process_UART_Frame(uart_rx_buf, recv_len);
    }
}
```

优化要点：Circular 模式下无需重启 DMA；需记录上次接收位置计算增量；帧间间隔极短时考虑 Normal 模式逐帧处理。

### 5.3 DMA + SPI：全双工收发

SPI 全双工通信中，DMA 同时驱动 TX 和 RX：

```c
#define SPI_BUF_SIZE 128
uint8_t spi_tx_buf[SPI_BUF_SIZE];
uint8_t spi_rx_buf[SPI_BUF_SIZE];

void SPI_FullDuplex_Transfer(void) {
    Prepare_TX_Data(spi_tx_buf, SPI_BUF_SIZE);
    HAL_SPI_TransmitReceive_DMA(&hspi1, spi_tx_buf, spi_rx_buf, SPI_BUF_SIZE);
}
```

优化要点：TX/RX 使用不同 DMA Stream 避免冲突；高速 SPI 必须用 DMA；只接收时 TX 仍需发 dummy 字节产生时钟。

## 6. Cortex-M7 上的 Cache 一致性问题

### 6.1 问题根源

Cortex-M7 的 D-Cache 会在 CPU 侧缓存内存数据。当 DMA 直接操作内存时：

- **DMA 读内存**(P2M)：CPU 写的数据可能还在 D-Cache，尚未写回主存 --> DMA 读到旧数据
- **DMA 写内存**(M2P)：DMA 写入的数据在主存，但 D-Cache 持有旧副本 --> CPU 读到旧数据

```
场景1: DMA 读到过时数据
  CPU 写 buffer -> 数据留在 D-Cache (未写回 SRAM) -> DMA 从 SRAM 读到旧数据
场景2: CPU 读到过时数据
  DMA 写 buffer -> 数据更新到 SRAM -> CPU 读 buffer 时 D-Cache 命中旧数据
```

### 6.2 解决方案

**方案一：关闭 D-Cache**(简单但性能损失大)

```c
SCB_DisableDCache();  // 不推荐：所有内存访问都变慢
```

**方案二：将 DMA 缓冲区放在 Non-Cacheable 区域**(推荐)

```c
// STM32H7 MPU 配置
MPU_Region_InitTypeDef MPU_InitStruct = {0};
MPU_InitStruct.Enable = MPU_REGION_ENABLE;
MPU_InitStruct.BaseAddress = 0x24000000;
MPU_InitStruct.Size = MPU_REGION_SIZE_256KB;
MPU_InitStruct.TypeExtField = MPU_TEX_LEVEL0;  // Non-Cacheable
MPU_InitStruct.AccessPermission = MPU_REGION_FULL_ACCESS;
MPU_InitStruct.IsCacheable = MPU_ACCESS_NOT_CACHEABLE;
MPU_InitStruct.IsBufferable = MPU_ACCESS_BUFFERABLE;
HAL_MPU_ConfigRegion(&MPU_InitStruct);
```

**方案三：手动维护 Cache 一致性**(灵活但易出错)

```c
// DMA 读取前：写回 D-Cache
void DMA_Start_Transmit(uint8_t* buf, uint32_t len) {
    SCB_CleanDCache_by_Addr((uint32_t*)buf, len);
    HAL_DMA_Start(&hdma, (uint32_t)buf, PERIPH_ADDR, len);
}
// DMA 写入后：无效化 D-Cache 对应行
void DMA_Receive_Complete(uint8_t* buf, uint32_t len) {
    SCB_InvalidateDCache_by_Addr((uint32_t*)buf, len);
    Process_Data(buf, len);
}
```

| 方案 | 性能 | 复杂度 | 适用场景 |
|------|------|--------|----------|
| 关闭 D-Cache | 低 | 最低 | 简单原型/调试 |
| Non-Cacheable 区域 | 中 | 中 | 生产环境(推荐) |
| 手动 Cache 维护 | 高 | 高 | 性能要求极高 |

> 注意：`SCB_CleanDCache_by_Addr` 要求地址对齐到 cache line(通常 32 字节)，缓冲区应用 `__ALIGNED(32)` 修饰。

## 7. 性能基准对比

### 7.1 测试场景

MCU: STM32F407 @ 168 MHz，传输 1024 字节内存到内存。

| 方法 | 传输耗时(us) | CPU 占用 | 代码复杂度 |
|------|-------------|----------|-----------|
| CPU 轮询(memcpy) | ~18 | 100% | 低 |
| CPU 中断(逐字节) | ~450 | ~35% | 中 |
| DMA Normal | ~6 | <1% | 中 |
| DMA Burst4 | ~3 | <1% | 中高 |

### 7.2 不同外设的 DMA 效果

| 外设 | 速率 | CPU 轮询占用 | CPU 中断占用 | DMA 占用 |
|------|------|-------------|-------------|---------|
| UART 115200 | 11.5 KB/s | ~1.6% | ~4.6% | <0.1% |
| SPI 10 MHz | 1.25 MB/s | ~17.6% | ~44% | <0.5% |
| ADC 1 MSPS | 2 MB/s | N/A | ~28% | <0.2% |
| UART 921600 | 92 KB/s | ~13% | ~36% | <0.2% |

> 数据为估算值，实际取决于 MCU 主频、总线架构和编译优化级别。

### 7.3 优化选型决策树

```
数据量是否 > 16 字节?
  |-- 否 --> CPU 轮询或中断
  |-- 是 --> 数据是否连续/规则?
              |-- 否 --> DMA + IDLE 检测(UART 变长帧)
              |-- 是 --> 是否需要持续运行?
                          |-- 否 --> DMA Normal 模式
                          |-- 是 --> DMA Circular + HT/TC 双中断
                                      是否需要零延迟切换? --> Double-Buffer
                          是否 Cortex-M7? --> 处理 Cache 一致性
                          是否 STM32H7? --> 考虑 MDMA 链表传输
```

## 总结

DMA 控制器是 MCU 数据搬运优化的核心手段。本文核心要点：

1. **基本判断**：数据量 > 16 字节且地址连续，优先用 DMA；小数据/低频场景用中断即可
2. **模式选择**：一次性传输用 Normal，连续数据流用 Circular + HT/TC 双中断，零延迟切换用 Double-Buffer
3. **通道规划**：查阅 DMA request mapping 避免通道冲突，按实时性设置优先级
4. **高级特性**：FIFO 合并窄带传输减少总线占用；Burst 提升吞吐但注意实时性影响；MDMA 链表适合多段不连续传输
5. **典型场景**：ADC 用 Circular + 半传输中断；UART 用 IDLE 线检测；SPI 全双工需同时配 TX/RX 两个 Stream
6. **Cache 一致性**：Cortex-M7 上 DMA 缓冲区必须处理 D-Cache，生产环境推荐 Non-Cacheable 区域方案

DMA 的本质是用硬件确定性替代软件不确定性。理解了这一点，就能在具体项目中做出正确的架构选择。

## 参考文献

1. STMicroelectronics. RM0090 Reference Manual: STM32F405/415, STM32F407/417, STM32F427/437 and STM32F429/439. Section 9: Direct memory access controller (DMA).
2. STMicroelectronics. RM0433 Reference Manual: STM32H742, STM32H743/753 and STM32H750/750. Section 14: MDMA - Master DMA controller.
3. Arm. Armv7-M Architecture Reference Manual. Section B3: Memory model and cache architecture.
4. Joseph Yiu. The Definitive Guide to ARM Cortex-M7 Processors. Arm Ltd, 2016. Chapter 7: Memory System and Cache.
5. STMicroelectronics. AN4839 Application Note: DMA controller guidelines for STM32 MCU and MPU.
