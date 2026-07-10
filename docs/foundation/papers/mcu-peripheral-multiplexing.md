---
schema_version: '1.0'
id: mcu-peripheral-multiplexing
title: MCU外设引脚复用与引脚分配策略
layer: 1
content_type: UNKNOWN
difficulty: beginner
reading_time: 18
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# MCU外设引脚复用与引脚分配策略
> **难度**：初级 | **领域**：MCU系统设计 | **阅读时间**：约 18 分钟

## 引言

一个MCU就像一栋多功能活动中心，同一个房间可以当会议室、教室或者健身房，但不能同时使用。MCU的引脚复用也是这个道理：每个引脚可以承担多种功能，但在同一时刻只能选一种。引脚分配策略就是规划"哪个房间干什么"的过程 -- 规划得好，各功能互不冲突；规划得差，到了PCB阶段才发现引脚不够用或者功能打架，那就麻烦了。

## 1 引脚复用概念

### 1.1 什么是引脚复用

MCU内部集成了大量外设(UART、SPI、I2C、ADC、Timer等)，但封装引脚数量有限。引脚复用(Multiplexing)让一个物理引脚可以在多种外设功能之间切换选择。

```
         MCU内部
+------------------+
| UART0_TX  -------+---> PIN_10 (选择UART0_TX)
| SPI1_MOSI -------+      或
| TIM2_CH1  -------+      SPI1_MOSI
| GPIO_B2   -------+      或 TIM2_CH1
+------------------+      或 GPIO_B2
```

### 1.2 为什么需要复用

- **成本**：引脚数越少，封装越小，芯片和PCB越便宜
- **灵活性**：不同应用使用不同外设组合，用户按需分配
- **面积**：MCU封装尺寸直接受引脚数影响

### 1.3 复用的代价

- 同一引脚上的外设功能互斥，不能同时使用
- 需要仔细规划避免冲突
- 增加了硬件设计的复杂度

## 2 替代功能映射

### 2.1 STM32的AF映射

STM32每个引脚有AF0到AF15共16种替代功能选择：

```c
// STM32 HAL库设置替代功能
// 将PA9配置为USART1_TX (AF7)
GPIO_InitTypeDef GPIO_InitStruct = {0};
GPIO_InitStruct.Pin = GPIO_PIN_9;
GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
GPIO_InitStruct.Pull = GPIO_NOPULL;
GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
GPIO_InitStruct.Alternate = GPIO_AF7_USART1;  // AF7 = USART1
HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
```

### 2.2 数据手册中的引脚表

数据手册的引脚表是引脚分配的核心参考资料：

```
Pin  | Name   | AF0      | AF1      | AF2      | AF3
-----|--------|----------|----------|----------|----------
1    | PA0    | GPIO     | TIM2_CH1 | UART4_TX | ...
2    | PA1    | GPIO     | TIM2_CH2 | UART4_RX | ...
3    | PA2    | GPIO     | TIM2_CH3 | USART2_TX| ...
4    | PA3    | GPIO     | TIM2_CH4 | USART2_RX| ...
```

必须仔细查阅此表，确认所需外设功能在目标引脚上可用。

## 3 引脚分配策略

### 3.1 优先级排序

引脚分配按优先级从高到低进行：

**第一优先级：固定功能引脚**

这些引脚不能更改，必须首先预留：

- 晶振引脚(OSC_IN/OSC_OUT)
- SWD调试引脚(SWDIO/SWCLK)
- USB引脚(D+/D-)
- BOOT引脚(BOOT0/BOOT1)
- 复位引脚(NRST)

**第二优先级：关键外设**

引脚选择受限的外设优先分配：

- 高速SPI(Flash/Display)：引脚通常固定
- ADC模拟输入：只有特定引脚有ADC功能
- USB：只有特定引脚支持USB

**第三优先级：灵活外设**

引脚选择余地大的外设最后分配：

- UART：多数引脚都有UART AF
- I2C：有多个I2C实例可选
- 普通GPIO：任何引脚都能做

### 3.2 分配检查清单

```
[ ] 1. 列出所有需要的外设及其引脚需求
[ ] 2. 标记每个外设的可用引脚范围
[ ] 3. 预留固定功能引脚
[ ] 4. 从约束最多的外设开始分配
[ ] 5. 检查已分配引脚之间是否有冲突
[ ] 6. 记录最终分配结果
```

## 4 常见冲突

### 4.1 I2C与SPI共享引脚

某些引脚同时支持I2C和SPI功能，两者不能同时使用：

```
Pin PA4: SPI1_NSS / I2C1_SCL  <-- 冲突!
Pin PA5: SPI1_SCK / I2C1_SDA  <-- 冲突!
```

解决方案：选择其他引脚的I2C或SPI实例。

### 4.2 ADC与通信外设冲突

ADC模拟输入引脚通常也支持数字功能：

```
Pin PA0: ADC_IN0 / TIM2_CH1 / UART4_TX
```

如果PA0用作ADC输入，就不能同时用作定时器或串口。

### 4.3 定时器PWM通道受限

定时器的PWM输出通道固定在特定引脚上：

```
TIM2_CH1: PA0 或 PA15 (二选一)
TIM2_CH2: PA1 或 PB3  (二选一)
TIM2_CH3: PA2 或 PB10 (二选一)
```

如果需要3个PWM通道同时输出，必须确保它们不与其他功能冲突。

## 5 引脚规划工具

### 5.1 STM32CubeMX

ST官方的图形化配置工具：

- 可视化引脚分配，冲突自动标红
- 一键生成初始化代码
- 支持引脚导出为表格

使用步骤：
1. 选择MCU型号
2. 在Pinout视图中配置外设
3. 检查冲突(红色标记)
4. 调整引脚分配直到无冲突
5. 生成代码

### 5.2 ESP-IDF menuconfig

ESP32系列的配置方式：

- 通过Kconfig菜单选择外设和引脚
- GPIO矩阵几乎允许任何外设映射到任何引脚

### 5.3 Nordic nRF Device Tree

Zephyr RTOS下nRF系列通过设备树配置引脚：

```dts
&i2c0 {
    compatible = "nordic,nrf-twi";
    sda-pin = <26>;
    scl-pin = <27>;
    status = "okay";
};

&spi1 {
    compatible = "nordic,nrf-spi";
    sck-pin = <31>;
    mosi-pin = <29>;
    miso-pin = <30>;
    cs-gpios = <&gpio0 28 GPIO_ACTIVE_LOW>;
    status = "okay";
};
```

## 6 引脚重映射

### 6.1 STM32 AFIO重映射

部分STM32支持通过AFIO寄存器将外设映射到另一组引脚：

```c
// STM32F1系列：将USART1从PA9/PA10重映射到PB6/PB7
__HAL_RCC_AFIO_CLK_ENABLE();
__HAL_AFIO_REMAP_USART1_ENABLE();
```

### 6.2 ESP32 GPIO矩阵

ESP32的GPIO矩阵几乎允许将任何外设信号映射到任何GPIO：

```c
// ESP32: 任意引脚分配
#define I2C_SDA_PIN  21
#define I2C_SCL_PIN  22
#define SPI_MOSI_PIN 23
#define SPI_MISO_PIN 19
#define SPI_SCLK_PIN 18
// 这些引脚号可以自由更改(少数除外)
```

ESP32 GPIO矩阵是引脚分配最灵活的方案，大大降低了冲突概率。

## 7 实践案例：IoT传感器节点

### 7.1 需求列表

| 外设 | 用途 | 引脚需求 |
|------|------|----------|
| SWD | 调试 | 2脚(SWDIO/SWCLK) |
| I2C1 | 温湿度传感器 | 2脚(SCL/SDA) |
| SPI1 | 外部Flash | 4脚(SCK/MOSI/MISO/CS) |
| UART1 | GPS模块 | 2脚(TX/RX) |
| ADC1 | 电池电压 | 1脚 |
| TIM2_CH1 | 状态LED PWM | 1脚 |
| GPIO | 按键 | 1脚 |

总计：13个引脚。

### 7.2 分配过程

```
步骤1: 固定引脚
  SWDIO -> PA13, SWCLK -> PA14 (固定,不可更改)

步骤2: ADC引脚(只有特定引脚支持)
  ADC_IN0 -> PA0 (电池电压分压后输入)

步骤3: SPI1(高速,选固定引脚)
  SCK -> PA5, MOSI -> PA7, MISO -> PA6, CS -> PA4

步骤4: I2C1
  SCL -> PB6, SDA -> PB7

步骤5: UART1
  TX -> PA9, RX -> PA10

步骤6: PWM和GPIO(灵活分配)
  TIM2_CH1 -> PA1 (LED PWM)
  GPIO -> PB0 (按键,外部中断)
```

### 7.3 最终引脚分配表

```
引脚   | 功能      | 外设
-------|-----------|--------
PA0    | ADC_IN0   | 电池电压
PA1    | TIM2_CH1  | LED PWM
PA4    | SPI1_NSS  | Flash CS
PA5    | SPI1_SCK  | Flash 时钟
PA6    | SPI1_MISO | Flash 数据入
PA7    | SPI1_MOSI | Flash 数据出
PA9    | USART1_TX | GPS发送
PA10   | USART1_RX | GPS接收
PA13   | SWDIO     | 调试(固定)
PA14   | SWCLK     | 调试(固定)
PB0    | GPIO_EXTI | 按键
PB6    | I2C1_SCL  | 传感器时钟
PB7    | I2C1_SDA  | 传感器数据
```

## 8 常见错误

### 8.1 早期不检查AF兼容性

最常见也最昂贵的错误：PCB做出来才发现引脚功能冲突。

对策：原理图阶段就用CubeMX或引脚表逐一验证。

### 8.2 后期引脚不够用

功能需求增加时发现引脚已经分配完了。

对策：设计初期预留10-20%的引脚余量。

### 8.3 忘记预留调试引脚

SWD引脚被其他功能占用，导致无法烧录和调试。

对策：SWD引脚永远优先预留，即使看似"浪费"。

### 8.4 ADC引脚被数字信号干扰

数字开关信号耦合到ADC输入，降低采样精度。

对策：ADC引脚与高速数字信号引脚物理远离，PCB上模拟地和数字地分区。

## 9 文档化

### 9.1 引脚分配表

在原理图中建立完整的引脚分配表：

```c
// 在代码中也应维护一份引脚定义头文件
// pin_config.h

#pragma once

// SWD Debug (固定,勿修改)
#define PIN_SWDIO       GPIO_PIN_13
#define PIN_SWCLK       GPIO_PIN_14
#define PORT_SWD        GPIOA

// I2C1 - Environmental Sensor
#define PIN_I2C1_SCL    GPIO_PIN_6
#define PIN_I2C1_SDA    GPIO_PIN_7
#define PORT_I2C1       GPIOB

// SPI1 - External Flash
#define PIN_SPI1_SCK    GPIO_PIN_5
#define PIN_SPI1_MISO   GPIO_PIN_6
#define PIN_SPI1_MOSI   GPIO_PIN_7
#define PIN_SPI1_CS     GPIO_PIN_4
#define PORT_SPI1       GPIOA

// ADC - Battery Voltage
#define PIN_ADC_BATT    GPIO_PIN_0
#define PORT_ADC_BATT   GPIOA

// PWM LED
#define PIN_LED_PWM     GPIO_PIN_1
#define PORT_LED_PWM    GPIOA

// Button
#define PIN_BUTTON      GPIO_PIN_0
#define PORT_BUTTON     GPIOB
```

### 9.2 与PCB布局交叉引用

引脚分配表应与PCB布局互相参照：

- 标注每个引脚的信号方向(输入/输出/双向)
- 标注高速信号引脚(需要阻抗匹配)
- 标注模拟信号引脚(需要远离干扰源)

## 总结

MCU引脚复用是嵌入式硬件设计的基础课题。核心策略是按优先级分配：先固定功能引脚，再约束多的外设，最后灵活分配。关键工具是数据手册的引脚表和STM32CubeMX等配置软件。常见错误(冲突、不够用、忘留调试脚)都可以通过早期规划避免。最终，将引脚分配结果同时文档化到原理图和代码头文件中，确保硬件和软件团队保持一致。

## 参考文献

1. STM32 Reference Manual RM0008 - GPIO and AFIO Chapters, STMicroelectronics.
2. STM32CubeMX User Guide, STMicroelectronics, 2024.
3. ESP32 Technical Reference Manual - GPIO Matrix, Espressif Systems.
4. Zephyr Device Tree Documentation, 2024.
5. Amulet Technologies. Pin Multiplexing Best Practices for Embedded Design, 2022.
