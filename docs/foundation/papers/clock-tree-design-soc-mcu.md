# SoC/MCU时钟树设计与PLL/FLL配置
> **难度**：🟡 中级 | **领域**：时钟系统设计 | **阅读时间**：约 20 分钟

## 引言

时钟就像乐团的指挥——每个乐手（外设模块）需要按照统一的节拍工作，但不同乐手可能需要不同的速度：小提琴手（CPU）需要快节拍，定音鼓手（RTC）需要慢节拍。时钟树就是这个"指挥系统"：从几个源头（晶振、内部 RC）出发，经过倍频（PLL）、分频（预分频器），把不同频率的时钟信号分发给各个模块。理解时钟树，就是理解 MCU 的"脉搏"是如何产生和分配的。

## 1. 时钟树的角色

### 1.1 时钟的功能

在同步数字电路中，时钟信号协调所有时序逻辑的状态更新：

- 每个 D 触发器在时钟上升沿采样输入
- 组合逻辑在两个时钟沿之间完成计算
- 时钟频率决定处理速度

### 1.2 为什么需要不同的时钟频率

| 模块 | 典型频率 | 原因 |
|------|----------|------|
| CPU | 48-480MHz | 高性能计算 |
| AHB 总线 | 48-240MHz | 与 CPU 同步或半频 |
| APB 外设 | 10-80MHz | UART/SPI/I2C 不需要太快 |
| ADC | 1-20MHz | 采样率限制 |
| RTC | 32.768kHz | 精确计时，低功耗 |
| USB | 48MHz | 协议要求精确 |
| BLE Radio | 16MHz | 射频协议要求 |

一个时钟源无法同时满足所有需求，因此需要时钟树进行分发和变换。

## 2. 时钟源

### 2.1 四种时钟源

**高速外部振荡器(HSE)：** 外接晶体，4-48MHz，精度 10-50ppm，启动 1-10ms，功耗 0.5-2mA。系统主时钟源，USB/BLE 等精度要求高的场景必须使用。

**高速内部 RC(HSI)：** 芯片内部 RC，8-64MHz，精度 1-3%（受温压影响），启动 1-5us（极快），功耗 0.2-0.5mA。上电默认时钟、快速启动场景。

**低速外部振荡器(LSE)：** 外接 32.768kHz 晶体，精度 10-20ppm，启动 100-1000ms，功耗 0.5-2uA。RTC 时钟源，BLE 睡眠定时器。

**低速内部 RC(LSI)：** 内部 RC，约 32-40kHz，精度 5-10%（很差），启动约 10us，功耗 0.2-0.5uA。独立看门狗(IWDG)。

### 2.2 时钟源对比

| 参数 | HSE | HSI | LSE | LSI |
|------|-----|-----|-----|-----|
| 频率 | 4-48MHz | 8-64MHz | 32.768kHz | 32-40kHz |
| 精度 | 10-50ppm | 1-3% | 10-20ppm | 5-10% |
| 启动时间 | 1-10ms | 1-5us | 100-1000ms | ~10us |
| 功耗 | 0.5-2mA | 0.2-0.5mA | 0.5-2uA | 0.2-0.5uA |
| 外部元件 | 晶体+电容 | 无 | 晶体+电容 | 无 |

## 3. PLL（锁相环）

### 3.1 原理

PLL 将输入频率倍频到更高频率，是时钟树的核心"加速器"。

日常类比：你骑自行车跟在一辆汽车后面，你要保持和汽车同速。你盯着汽车（相位检测器），如果你慢了就加速（VCO 提高），如果快了就减速，最终锁定在汽车速度。如果你齿轮比调高（倍频系数 N），你每蹬一圈相当于汽车转 N 圈。

### 3.2 PLL 结构

```
              +--------+     +------+     +-----+
  F_ref ----->| 相位   |---->| 环路 |---->| VCO |----+---> F_out
              | 检测器 |     | 滤波器|     |     |    |
              +--------+     +------+     +-----+    |
                  ^                                    |
                  |          +-----+    +-----+        |
                  +----------| / M |<---| / N |<-------+
                             +-----+    +-----+
                             输入分频    反馈分频

F_out = F_ref * N / M
```

### 3.3 PLL 配置参数

| 参数 | 含义 | 典型范围 |
|------|------|----------|
| M (输入分频) | 将输入频率分到PD可接受范围 | 1-16 |
| N (倍频系数) | VCO 倍频倍数 | 8-400 |
| P (主输出分频) | 产生系统时钟 | 1-8 (2的幂次) |
| Q (辅助输出1) | USB/外设时钟 | 1-16 |
| R (辅助输出2) | I2S/SAI 时钟 | 1-16 |

### 3.4 配置计算示例

STM32H743 配置 480MHz 系统时钟：

```
输入: HSE = 8MHz, 目标: SYSCLK = 480MHz

步骤1: M = 1 -> PLL1_IN = 8MHz
步骤2: VCO 范围 128-560MHz
        N = 60 -> VCO = 8MHz * 60 = 480MHz (在范围内)
步骤3: P = 1 -> SYSCLK = 480MHz / 1 = 480MHz
步骤4: 验证 F_ref * N / M = 8 * 60 / 1 = 480MHz (OK)
```

### 3.5 PLL 锁定时间

PLL 启动后需等待锁定（频率和相位稳定），典型 100-500us。锁定前不能作为系统时钟。

```
启动序列:
  1. 使能 PLL
  2. 等待 PLL_LOCK 标志置位 (100-500us)
  3. 切换系统时钟源到 PLL
```

## 4. FLL（锁频环）

### 4.1 原理

FLL 比 PLL 简单，只锁定频率不锁定相位：使用低频参考校准高频 RC 振荡器，精度约 1-2%，但功耗和面积更小。

### 4.2 nRF52 中的 FLL

```
nRF52 时钟系统:
  HFXO (32MHz 晶体)  ---> 64MHz (FLL 倍频)
  LFXO (32.768kHz)   ---> RTC 时钟源
  HFINT (64MHz RC)   ---> 启动默认, 精度约 5%
  LFINT (32kHz RC)   ---> 看门狗

FLL: HFXO 32MHz 作参考 -> 倍频到 64MHz
     HFXO 未启动时用 HFINT RC
```

### 4.3 PLL vs FLL

| 特性 | PLL | FLL |
|------|-----|-----|
| 相位锁定 | 是 | 否 |
| 频率精度 | 极高(<0.01%) | 较高(1-2%) |
| 功耗 | 较高(1-5mA) | 较低(0.1-0.5mA) |
| 面积 | 大 | 小 |
| 锁定时间 | 100-500us | 10-50us |
| 适用场景 | 精确时钟(USB/BLE) | 低功耗MCU |

## 5. 时钟树结构

### 5.1 典型时钟树

```
                    +-------+
          +-------->| PLL   |-------+---------> SYSCLK (80MHz)
          |         +-------+       |
          |              ^          +---> AHB Prescaler (/1) -> 80MHz
+-----+   |    +-----+   |          +---> APB1 Prescaler (/1) -> 80MHz
| HSE |---+    | HSI |---+         +---> APB2 Prescaler (/1) -> 80MHz
| 8MHz|        |16MHz|              +---> 48MHz (USB)
+-----+        +-----+            |
+-------+                         |
| LSE   |-----> RTC (32.768kHz)   |
|32.768k|                          |
+-------+         +-----+         |
                   | LSI |-----> IWDG
                   |32kHz|
                   +-----+
```

### 5.2 总线时钟关系

```
SYSCLK (系统时钟)
  +---> AHB: 预分频 /1~/512, 连接 CPU, DMA, Flash, SRAM
  +---> APB1: 预分频 /1~/16, 连接 UART2-5, I2C, SPI2-3, TIM2-7
  +---> APB2: 预分频 /1~/16, 连接 UART1, SPI1, ADC, TIM1
```

### 5.3 外设时钟使能

```c
// STM32 外设时钟使能 (RCC: Reset and Clock Control)
RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;   // 使能 GPIOA
RCC->APB2ENR |= RCC_APB2ENR_USART1EN;   // 使能 USART1
RCC->APB1ENR |= RCC_APB1ENR_TIM2EN;     // 使能 TIM2
RCC->APB2ENR &= ~RCC_APB2ENR_ADC1EN;   // 关闭 ADC1 (省功耗)
```

## 6. 时钟门控

关闭不使用的外设时钟，消除其动态功耗：

```
P = alpha * C * V^2 * f
典型外设空转约 50-200uW (80MHz, 1.2V)
10个外设只用3个: 节省约 700uW
```

| 策略 | 描述 | 适用场景 |
|------|------|----------|
| 软件门控 | 初始化时关闭不用的外设时钟 | 所有场景 |
| 自动门控 | 外设空闲时硬件自动关闭时钟 | 高级 MCU |
| 时钟请求 | 外设驱动申请/释放时钟 | OS 驱动模型 |

## 7. 动态时钟切换

### 7.1 运行时切换

根据负载切换系统时钟：高性能(PLL 80MHz) -> 低功耗(HSI 8MHz) -> 超低功耗(LSI 32kHz)

### 7.2 切换流程

```c
void switch_system_clock(clock_source_t new_src) {
    wait_clock_ready(new_src);           // 确保新时钟源就绪
    if (new_freq > current_freq)
        set_flash_latency(new_freq);      // 升频先调Flash等待
    RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_SW) | new_src;
    while ((RCC->CFGR & RCC_CFGR_SWS) != (new_src << 2));
    if (new_freq < current_freq)
        set_flash_latency(new_freq);      // 降频后降Flash等待
    SystemCoreClock = new_freq;
}
```

注意：切换时不能有正在进行的外设传输，Flash等待周期必须与频率匹配。

## 8. 实例：STM32 时钟配置

### 8.1 STM32G4 时钟树

```
HSE 8MHz --+--> PLL
           |     +-- M=1 -> PD = 8MHz
           |     +-- N=40 -> VCO = 320MHz
           |     +-- P=2 -> PLL_P = 160MHz (SYSCLK)
           |     +-- Q=4 -> PLL_Q = 80MHz (USB)
HSI 16MHz -+--> (备用)

SYSCLK = 160MHz -> AHB /1 = APB1 /1 = APB2 /1 = 160MHz
```

### 8.2 CubeMX 配置等效代码

```c
void SystemClock_Config(void) {
    RCC->CR |= RCC_CR_HSEON;
    while (!(RCC->CR & RCC_CR_HSERDY));

    RCC->PLLCFGR = (1 << RCC_PLLCFGR_PLLM_Pos)    // M = 1
                  | (40 << RCC_PLLCFGR_PLLN_Pos)    // N = 40
                  | (0 << RCC_PLLCFGR_PLLP_Pos)    // P = 2
                  | (4 << RCC_PLLCFGR_PLLQ_Pos)     // Q = 4
                  | (0 << RCC_PLLCFGR_PLLR_Pos);    // R = 2

    RCC->CR |= RCC_CR_PLLON;
    while (!(RCC->CR & RCC_CR_PLLRDY));

    FLASH->ACR = FLASH_ACR_LATENCY_4WS;  // 160MHz需要4WS
    RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_SW) | RCC_CFGR_SW_PLL;
    while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL);
}
```

## 9. 实例：nRF52 时钟配置

### 9.1 时钟源与启动序列

```
nRF52832:
  HFXO:  32MHz 外部晶体 (BLE射频必须)
  HFINT: 64MHz 内部 RC (启动默认)
  LFXO:  32.768kHz 外部晶体 (RTC)
  LFRC:  32.768kHz 内部 RC (替代LFXO)
```

```c
void clock_init(void) {
    nrfx_clock_lfclk_start();              // 启动 LFXO
    while (!nrfx_clock_lfclk_is_running());
    nrfx_clock_hfclk_start();              // 启动 HFXO, FLL自动倍频到64MHz
    while (!nrfx_clock_hfclk_is_running());
}
```

### 9.2 BLE 事件驱动时钟管理

```c
void ble_evt_handler(ble_evt_t const * p_ble_evt) {
    switch (p_ble_evt->header.evt_id) {
        case BLE_GAP_EVT_CONNECTED:
            // HFXO 必须保持开启 (BLE协议要求, SoftDevice自动管理)
            break;
        case BLE_GAP_EVT_DISCONNECTED:
            // 断开后可关闭 HFXO, CPU切到HFINT (精度从~30ppm降到~5%)
            break;
    }
}
```

## 10. 时钟精度要求

### 10.1 各外设精度需求

| 外设 | 频率 | 精度要求 | 合适的时钟源 |
|------|------|----------|-------------|
| UART | 任意 | <2% | HSE + PLL, HSI可能不够 |
| SPI | 任意 | <5% | HSE 或 HSI |
| USB | 48MHz | <0.25% | HSE + PLL (必须) |
| BLE | 16MHz | <50ppm | HFXO (必须) |
| RTC | 32.768kHz | <50ppm | LSE (必须) |

### 10.2 UART 精度分析

```
8N1 格式: 最大误差约 5%, 收发双方各约 2.5%
HSI 精度 1-3%: 勉强可用，温度极端时可能出错
HSE 精度 50ppm: 完全满足
```

## 11. 常见问题

### 11.1 PLL 锁定时间与CSS

PLL 锁定是启动延迟主要来源（100-500us vs HSI 1-5us），优化：先切 HSI 快速启动，PLL 锁定后再切换。

时钟安全系统(CSS)检测 HSE 故障：

```c
RCC->CR |= RCC_CR_CSSON;          // 使能CSS
void NMI_Handler(void) {
    if (RCC->CIR & RCC_CIR_CSSF) {
        // HSE故障! 自动切换到HSI
        // 重新配置系统时钟, 清除CSS标志
        RCC->CIR |= RCC_CIR_CSSCLR;
    }
}
```

### 11.2 抖动对 ADC 的影响

```
SNR_jitter = -20 * log10(2 * pi * f_in * t_jitter)

f_in = 100kHz, t_jitter = 100ps -> SNR_jitter = 84 dB
12-bit ADC (理论74dB): 抖动影响不大
16-bit ADC (理论98dB): 抖动成为瓶颈
```

## 总结

时钟树是 SoC/MCU 的"脉搏系统"：从 HSE/HSI/LSE/LSI 四种源头出发，经过 PLL 倍频或 FLL 校准，再通过 AHB/APB 预分频器分配给各个外设。PLL 通过 M/N/P 三级分频器精确控制输出频率；FLL 更简单省电，适合 nRF52 等低功耗 MCU。时钟门控关闭不用的外设时钟以省功耗，动态切换在运行时根据负载调整频率。实际配置时，USB 需要 PLL 输出精确 48MHz，BLE 需要 HFXO 精度优于 50ppm，而 UART 在 HSI 下可能因精度不足导致通信错误——这些都是时钟设计中需要特别注意的。

## 参考文献

1. STMicroelectronics. "STM32G4xx Reference Manual (RM0440) - Clock Control." 2023.
2. Nordic Semiconductor. "nRF52832 Product Specification - Clock Management." 2022.
3. Razavi B. "Design of Analog CMOS Integrated Circuits, Chapter 15: PLLs." McGraw-Hill, 2017.
4. Espressif Systems. "ESP32 Technical Reference Manual - Reset and Clock." 2022.
5. Horowitz P, Hill W. "The Art of Electronics, 3rd Ed., Chapter 13: Digital meets Analog." Cambridge University Press, 2015.
