---
schema_version: '1.0'
id: timer-counter-pwm-capture
title: 定时器/计数器PWM输出与输入捕获应用
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
# 定时器/计数器PWM输出与输入捕获应用
> **难度**：🟢 初级 | **领域**：MCU定时器应用 | **阅读时间**：约 18 分钟

## 引言

想象厨房的烹饪定时器：你设定倒计时，时间到了就响铃。MCU定时器也一样 -- 硬件计数器按时钟递增，到设定值产生中断或事件。但它远不止"闹钟"：能输出PWM控制电机和LED亮度，能捕获外部信号时间戳测量频率和脉宽，还能读取编码器方向和位置。一个定时器，三种角色，这是嵌入式最versatile的外设。

## 1. 定时器/计数器基础

### 1.1 核心工作原理

定时器是硬件计数器，每个时钟周期递增1(经预分频后)。达到自动重载值(ARR)时清零并产生更新事件。

```
时钟源 --> 预分频器(PSC) --> 计数器(CNT) --> 比较器(CCR) --> 输出/中断
              |                  |
              +-- 分频=PSC+1    +-- 达到ARR溢出清零
```

### 1.2 关键参数

| 参数 | 寄存器 | 含义 |
|------|--------|------|
| 预分频值 | PSC | 分频系数 = PSC + 1 |
| 自动重载值 | ARR | 计数器周期 = ARR + 1 |
| 比较值 | CCR | PWM占空比/比较阈值 |

### 1.3 定时周期计算

```
f_overflow = f_timer_clock / ((PSC + 1) * (ARR + 1))
```

PSC和ARR都是"值+1"关系，这是初学者常犯的off-by-one错误。

## 2. 定时器类型

### 2.1 基本定时器(Basic Timer)

以TIM6/TIM7为例：16位向上计数器、预分频器、自动重载、更新中断、可触发DAC。

**适用场景**：简单时间基准、周期性中断、DAC触发源。

### 2.2 通用定时器(General-Purpose Timer)

以TIM2-TIM5为例：16/32位计数器(向上/向下/中心对齐)、4个捕获/比较通道、PWM输出、输入捕获、输出比较、编码器接口、从模式。

**适用场景**：PWM控制、脉冲测量、编码器读取、事件定时。

### 2.3 高级定时器(Advanced Timer)

以TIM1/TIM8为例，面向电机控制：通用定时器全部功能 + 互补输出(CHx/CHxN) + 死区时间 + 刹车输入 + 重复计数器。

### 2.4 定时器类型对比

| 特性 | 基本定时器 | 通用定时器 | 高级定时器 |
|------|-----------|-----------|-----------|
| 通道数 | 0 | 4 | 4 |
| PWM输出 | 否 | 是 | 是(含互补) |
| 输入捕获 | 否 | 是 | 是 |
| 编码器模式 | 否 | 是 | 是 |
| 死区/刹车 | 否 | 否 | 是 |

## 3. PWM输出模式

### 3.1 PWM工作原理

PWM通过改变脉冲宽度控制平均电压或功率。

**向上计数PWM模式1**：CNT<CCR时输出高，CNT>=CCR时输出低，占空比=CCR/(ARR+1)。

```
CCR=3, ARR=7, 占空比=3/8=37.5%
CNT:  0  1  2  3  4  5  6  7  0  1  2  3
OUT:  H  H  H  L  L  L  L  L  H  H  H  L
```

### 3.2 PWM频率与占空比

```
f_PWM = f_timer_clock / ((PSC + 1) * (ARR + 1))
占空比 = CCR / (ARR + 1)          (PWM模式1)
```

**设计步骤**：1)确定目标频率 2)选ARR(决定分辨率) 3)算PSC

### 3.3 PWM分辨率

| ARR值 | 占空比分辨率 | 步进 |
|-------|-------------|------|
| 99 | 1% | 1% |
| 255 | 8位 | 0.39% |
| 999 | 0.1% | 0.1% |

ARR越大分辨率越高，但在给定频率下需更高时钟。

## 4. 输入捕获模式

### 4.1 捕获工作原理

输入捕获在检测到外部信号边沿时，锁存当前计数器值到CCR。

```
外部信号:  ___/----\___/----\___
              ^         ^
           捕获CCR1   捕获CCR2
周期 T = (CCR2 - CCR1) * t_tick
```

### 4.2 脉宽测量

捕获上升沿和下降沿：脉宽 = (CCR_下降 - CCR_上升) * t_tick

### 4.3 频率测量方法

| 方法 | 原理 | 适用范围 |
|------|------|----------|
| 直接测频 | 计N个周期用时T，f=N/T | 高频信号 |
| 测周法 | 测一个周期T，f=1/T | 低频信号 |
| 等精度测频 | 同时计数被测信号和参考时钟 | 全频段恒精度 |

## 5. 输出比较模式

计数器值等于CCR时对输出执行动作：Frozen(无动作)、Toggle(翻转)、Active/Inactive(设高/低)、Force Active/Inactive(强制)。

**典型应用**：Toggle产生精确方波；中断模式实现精确事件调度。

## 6. 编码器接口模式

### 6.1 正交编码器原理

旋转编码器输出A/B两路正交信号(相差90度)，通过相位关系判断方向：

```
顺时针: A超前B    逆时针: B超前A
```

### 6.2 编码器模式配置

| 模式 | 计数信号 | 方向检测 |
|------|----------|----------|
| TI1 | 仅A边沿 | A边沿看B电平 |
| TI2 | 仅B边沿 | B边沿看A电平 |
| TI1+TI2 | A和B边沿 | 4倍频 |

4倍频原理：A/B各有上升和下降沿，每周期4个边沿。1000线编码器4倍频后每转4000个计数。

### 6.3 位置和速度计算

```c
int32_t position = __HAL_TIM_GET_COUNTER(&htim3);
int32_t delta = pos_now - pos_prev;
float speed_rpm = (delta * 60.0f) / (PPR * dt_seconds);
```

## 7. 实际应用示例

### 7.1 LED调光(PWM 1kHz)

```c
// TIM2 CH1, f_timer=84MHz, PSC=99, ARR=839 -> 1kHz
TIM_OC_InitTypeDef sConfigOC = {0};
htim2.Init.Prescaler   = 99;
htim2.Init.Period      = 839;
htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
HAL_TIM_PWM_Init(&htim2);

sConfigOC.OCMode     = TIM_OCMODE_PWM1;
sConfigOC.Pulse      = 420;  // 50%占空比
sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
HAL_TIM_PWM_ConfigChannel(&htim2, &sConfigOC, TIM_CHANNEL_1);
HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_1);

void set_brightness(uint8_t percent) {
    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, (percent * 840) / 100);
}
```

### 7.2 舵机控制(PWM 50Hz)

```c
// PSC=99, ARR=16799 -> 50Hz
// 0.5ms=840counts, 2.5ms=4200counts
void servo_set_angle(uint8_t angle) {
    uint32_t ccr = 840 + (angle * (4200 - 840)) / 180;
    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, ccr);
}
```

### 7.3 超声波测距(输入捕获)

```c
volatile uint32_t cap_rise = 0, cap_fall = 0;
volatile uint8_t cap_done = 0;

void HAL_TIM_IC_CaptureCallback(TIM_HandleTypeDef *htim) {
    if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1)
        cap_rise = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1);
    if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_2) {
        cap_fall = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_2);
        cap_done = 1;
    }
}

float get_distance_cm(void) {
    if (!cap_done) return -1.0f;
    uint32_t ticks = cap_fall - cap_rise;
    float us = ticks * (1000000.0f / f_timer_hz);
    return us / 58.0f;  // 58us/cm
}
```

## 8. 定时器与DMA

### 8.1 DMA触发模式

| 触发源 | 用途 |
|--------|------|
| 更新事件 | 周期性搬运数据 |
| 比较匹配 | 动态更新CCR(动态PWM) |
| 捕获事件 | 自动存储捕获值到缓冲区 |

### 8.2 动态PWM波形

通过DMA循环更新CCR值，可产生任意波形(如正弦波PWM)：

```c
uint16_t sine_table[100];
for (int i = 0; i < 100; i++)
    sine_table[i] = (ARR/2) + (ARR/2) * sin(2 * 3.14159f * i / 100);
// DMA循环模式: sine_table --> TIM->CCR1
```

## 9. 单脉冲模式(OPM)

定时器在触发后产生一个脉冲然后自动停止。适合精确宽度触发脉冲、硬延时、一次性事件控制。

```c
htim2.Init.OnePulseMode = TIM_OPMODE_SINGLE;
```

## 10. 中心对齐模式

计数器先向上到ARR再向下到0。PWM边沿对称分布减少谐波，电机驱动减小电流纹波。代价：PWM频率减半。

## 11. 常见问题与排查

### 11.1 时钟源识别错误

**问题**：输出频率与计算不符。**原因**：不同定时器挂在不同总线上，且APB预分频不为1时定时器时钟自动x2。

### 11.2 预分频Off-By-One

```c
htim.Init.Prescaler = 100;     // 错误: 实际分频101
htim.Init.Prescaler = 100 - 1; // 正确: 实际分频100
```

### 11.3 输出引脚AF映射错误

PWM输出引脚必须配置为AF模式，AF编号必须对应正确的定时器通道。查数据手册AF映射表确认。

### 11.4 通道映射不匹配

```c
HAL_TIM_PWM_ConfigChannel(&htim, &sConfig, TIM_CHANNEL_1);
HAL_TIM_PWM_Start(&htim, TIM_CHANNEL_1);  // 通道必须一致!
```

## 12. 定时器应用速查

| 应用 | 定时器类型 | 模式 | 关键配置 |
|------|-----------|------|----------|
| 周期中断 | 任意 | 更新中断 | PSC, ARR |
| LED调光 | 通用 | PWM | f=1kHz |
| 舵机控制 | 通用 | PWM | f=50Hz, CCR=脉宽 |
| 电机驱动 | 高级 | PWM+互补+死区 | 中心对齐 |
| 频率测量 | 通用 | 输入捕获 | 边沿选择 |
| 编码器读取 | 通用 | 编码器 | TI1+TI2 4倍频 |
| 波形发生 | 通用 | PWM+DMA | 循环DMA到CCR |

## 总结

定时器是MCU上功能最丰富的外设之一，核心掌握要点：

1. **三类定时器**：基本(简单计时)、通用(PWM+捕获+编码器)、高级(电机控制+死区)
2. **PWM输出**：频率由PSC和ARR决定，占空比由CCR决定，分辨率与ARR成正比
3. **输入捕获**：锁存边沿时刻的计数器值，可测频率和脉宽
4. **编码器模式**：自动识别方向，4倍频提升分辨率
5. **DMA配合**：定时器触发DMA实现无CPU介入的精确定时
6. **Off-By-One**：PSC和ARR都是"值+1"关系，计算时务必注意

一个通用定时器可以同时输出PWM和进行输入捕获(不同通道)，善用组合可实现复杂的测量和控制方案。

## 参考文献

1. STMicroelectronics, *STM32F4 Reference Manual (RM0090)*, Timer chapters, 2023
2. STMicroelectronics, *AN4776: General-purpose timer cookbook for STM32*, 2022
3. Dr. Maged Ghoneima, *PWM Techniques for Motor Control*, ARM TechCon, 2019
4. Texas Instruments, *SPRUG10: ePWM Module Reference Guide*, 2021
5. Bogdan Raducanu, *STM32 Timer Encoder Mode*, STM32 Community, 2020
