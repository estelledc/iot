# GPIO配置模式：推挽/开漏/复用功能详解
> **难度**：🟢 初级 | **领域**：MCU外设基础 | **阅读时间**：约 18 分钟

## 引言

想象你有一排电灯开关，每个开关不仅可以开灯关灯，还能切换成"门铃模式"(输入)或"调光器模式"(模拟)。GPIO(通用输入输出)就是MCU上这样的可编程引脚 -- 软件决定每个引脚的角色和行为模式。选对模式，外设才能正常工作；选错模式，轻则信号异常，重则烧毁芯片。本文系统梳理GPIO的8种配置模式，给出选型依据和典型代码示例。

## 1. GPIO基本概念

### 1.1 什么是GPIO

GPIO(General Purpose Input/Output)是微控制器上最基础的外设。每个引脚可由软件配置为：

- **输入**：读取外部信号的高低电平
- **输出**：驱动外部负载为高或低电平
- **复用功能**：将引脚交给片上外设(UART/SPI/TIM等)控制
- **模拟**：断开数字缓冲，连接到ADC或DAC

### 1.2 GPIO内部结构

| 组件 | 功能 |
|------|------|
| 保护二极管 | 钳位电压到VDD和VSS，防止ESD损坏 |
| 上拉/下拉电阻 | 为输入提供默认电平，阻值约30-50k |
| 输入施密特触发器 | 对输入信号整形，消除噪声抖动 |
| 输出MOSFET对 | P-MOS(上管)和N-MOS(下管)驱动输出 |
| 复用功能选择器 | 多路开关，选择哪个外设控制该引脚 |
| 模拟开关 | 断开数字通路，连接模拟外设 |

## 2. 输出模式

### 2.1 推挽输出(Push-Pull)

推挽输出是最常用的输出模式。名字来源于两个MOSFET"一推一挽"地工作。

**工作原理**：
- 输出高电平：P-MOS(上管)导通，N-MOS(下管)关断，引脚连VDD
- 输出低电平：P-MOS关断，N-MOS导通，引脚连VSS

```
VDD
 |
[P-MOS] <-- 控制信号(反相)
 |---------引脚
[N-MOS] <-- 控制信号
 |
VSS
```

**特性**：驱动能力对称；切换速度快；不能线与(多推挽不可短接)；典型驱动4-25mA。

**适用场景**：LED驱动、数字信号输出、SPI时钟/数据线、UART TX

### 2.2 开漏输出(Open-Drain)

开漏输出只有下管(N-MOS)，上管断开。

**工作原理**：
- 输出低电平：N-MOS导通，引脚拉到VSS
- 输出高电平：N-MOS关断，引脚浮空(不是主动拉高!)
- 需要外部上拉电阻才能输出高电平

```
VDD
 |
[外部上拉R] -- 需要外接!
 |
 |---------引脚
[N-MOS] <-- 控制信号
 |
VSS
```

**特性**：只能主动拉低；支持线与(Wired-OR)；可实现电平转换。

**适用场景**：I2C总线(SDA/SCL)、单总线(1-Wire)、电平转换、多主机总线

### 2.3 上拉电阻选择

| 上拉电阻 | 上升时间 | 功耗 | 适用场景 |
|----------|----------|------|----------|
| 1k | 快(~100ns) | 高(3.3mA) | 高速I2C(400kHz+) |
| 4.7k | 中(~500ns) | 中(0.7mA) | 标准I2C(100kHz) |
| 10k | 慢(~1us) | 低(0.33mA) | 低速总线、按钮 |

计算公式：上升时间约等于 0.35 x R x C_bus

## 3. 输入模式

### 3.1 浮空输入(Floating Input)

引脚内部既无上拉也无下拉，呈现高阻抗。悬空时输入值不确定(随机跳变)。适用于外部信号已有明确驱动的场景(如另一个MCU的推挽输出)。

### 3.2 上拉输入(Pull-Up Input)

内部约30-50k电阻连到VDD，悬空时读到高电平。

**典型应用**：按钮接在引脚和GND之间。未按下读到1，按下读到0(低有效)。

### 3.3 下拉输入(Pull-Down Input)

内部电阻连到VSS，悬空时读到低电平。

**典型应用**：按钮接在引脚和VDD之间。未按下读到0，按下读到1(高有效)。

### 3.4 输入模式选择指南

| 场景 | 推荐模式 | 理由 |
|------|----------|------|
| 按钮对地 | 上拉 | 低有效，按下读到0 |
| 按钮对VDD | 下拉 | 高有效，按下读到1 |
| 传感器推挽输出 | 浮空 | 信号已有驱动 |
| I2C从机SDA | 外部上拉 | 开漏总线标准 |
| 未连接引脚 | 上拉或下拉 | 避免浮空跳变耗电 |

## 4. 模拟模式

### 4.1 何时使用模拟模式

当引脚连接到ADC或DAC时，必须配置为模拟模式。

**模拟模式做了什么**：断开施密特触发器(避免数字开关噪声)；断开输出驱动器；直接连到模拟多路开关。

### 4.2 为什么不能只用浮空输入

浮空输入模式下施密特触发器仍在工作，模拟信号在阈值附近会触发频繁翻转，产生额外噪声。模拟模式彻底断开数字通路，是最干净的选择。

## 5. 复用功能模式

### 5.1 引脚复用概念

MCU引脚数量有限但片上外设很多。引脚复用让同一物理引脚在不同时刻承担不同功能。例如STM32F4的PA9：

| AF编号 | 功能 | 外设 |
|--------|------|------|
| AF0 | MCO | 系统时钟输出 |
| AF1 | TIM1_CH2 | 定时器1通道2 |
| AF7 | USART1_TX | 串口1发送 |
| AF9 | I2C3_SCL | I2C3时钟 |

### 5.2 复用功能配置要点

1. 先使能对应外设时钟(RCC)
2. 将GPIO配置为复用功能模式(AF Mode)
3. 在AFR寄存器中选择正确的AF编号
4. 根据外设需求选择推挽或开漏

**重要**：AF编号在不同芯片上可能不同，必须查数据手册！

### 5.3 常见复用功能输出类型

| 外设 | 推荐输出类型 | 原因 |
|------|--------------|------|
| UART TX | 推挽 | 单主机点对点 |
| SPI SCK/MOSI | 推挽 | 单主机总线 |
| I2C SCL/SDA | 开漏 | 多主机线与总线 |
| TIM PWM | 推挽 | 主动驱动负载 |

## 6. 输出速度(摆率)控制

### 6.1 什么是输出速度

输出速度控制信号边沿变化率(Slew Rate)。STM32提供4档：

| 速度等级 | 典型值 | 边沿时间 | 适用频率 |
|----------|--------|----------|----------|
| Low | 2MHz | ~100ns | < 1MHz |
| Medium | 10MHz | ~30ns | 1-10MHz |
| High | 50MHz | ~10ns | 10-50MHz |
| Very High | 100MHz | ~5ns | > 50MHz |

### 6.2 速度选择权衡

速度越高边沿越陡峭但EMI辐射更强。**原则**：在满足时序前提下选最低速度。

| 场景 | 推荐速度 | 理由 |
|------|----------|------|
| LED控制 | Low | 低频信号，无需快速边沿 |
| I2C(100kHz) | Low/Medium | 上升沿由上拉电阻决定 |
| SPI(1MHz) | Medium | 满足时序即可 |
| SPI(10MHz+) | High | 需要陡峭边沿 |

## 7. STM32 GPIO寄存器与配置

### 7.1 关键寄存器

| 寄存器 | 功能 | 位宽/引脚 |
|--------|------|-----------|
| MODER | 模式选择(输入/输出/AF/模拟) | 2位 |
| OTYPER | 输出类型(推挽/开漏) | 1位 |
| OSPEEDR | 输出速度 | 2位 |
| PUPDR | 上下拉(无/上/下/保留) | 2位 |
| AFR[2] | 复用功能选择(0-15) | 4位 |

### 7.2 HAL库配置示例

```c
// 配置PA5为推挽输出(LED)
GPIO_InitTypeDef GPIO_InitStruct = {0};
GPIO_InitStruct.Pin   = GPIO_PIN_5;
GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_PP;
GPIO_InitStruct.Pull  = GPIO_NOPULL;
GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

// 配置PB6为开漏复用(I2C1 SCL)
GPIO_InitStruct.Pin       = GPIO_PIN_6;
GPIO_InitStruct.Mode      = GPIO_MODE_AF_OD;
GPIO_InitStruct.Pull      = GPIO_PULLUP;
GPIO_InitStruct.Speed     = GPIO_SPEED_FREQ_MEDIUM;
GPIO_InitStruct.Alternate = GPIO_AF4_I2C1;
HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

// 配置PA0为模拟输入(ADC)
GPIO_InitStruct.Pin   = GPIO_PIN_0;
GPIO_InitStruct.Mode  = GPIO_MODE_ANALOG;
GPIO_InitStruct.Pull  = GPIO_NOPULL;
HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
```

### 7.3 不要忘记使能GPIO时钟

```c
__HAL_RCC_GPIOA_CLK_ENABLE();  // 必须在配置之前!
```

不使能时钟则寄存器写入无效，这是最常见的初学者错误之一。

## 8. GPIO中断 -- EXTI

### 8.1 外部中断概念

GPIO引脚可配置为外部中断源(EXTI)，在上升沿、下降沿或双沿时触发中断。

### 8.2 EXTI配置步骤

```c
// 配置PC13为下降沿中断(按钮按下)
GPIO_InitTypeDef GPIO_InitStruct = {0};
GPIO_InitStruct.Pin  = GPIO_PIN_13;
GPIO_InitStruct.Mode = GPIO_MODE_IT_FALLING;
GPIO_InitStruct.Pull = GPIO_PULLUP;
HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

HAL_NVIC_SetPriority(EXTI15_10_IRQn, 0, 0);
HAL_NVIC_EnableIRQ(EXTI15_10_IRQn);

// 中断服务函数
void EXTI15_10_IRQHandler(void)
{
    if (__HAL_GPIO_EXTI_GET_IT(GPIO_PIN_13) != RESET)
    {
        __HAL_GPIO_EXTI_CLEAR_IT(GPIO_PIN_13);
        // 处理按钮按下事件
    }
}
```

### 8.3 EXTI限制与唤醒

EXTI线与引脚号对应(EXTI0对应Px0)，同一EXTI线只能映射到一个端口。EXTI中断还可将MCU从低功耗模式唤醒，实现"按键唤醒"。

## 9. 实际应用示例

### 9.1 按钮消抖(上拉输入 + EXTI)

```c
#define DEBOUNCE_MS  20
volatile uint32_t button_tick = 0;

void EXTI15_10_IRQHandler(void)
{
    if (__HAL_GPIO_EXTI_GET_IT(GPIO_PIN_13) != RESET)
    {
        __HAL_GPIO_EXTI_CLEAR_IT(GPIO_PIN_13);
        uint32_t now = HAL_GetTick();
        if (now - button_tick > DEBOUNCE_MS)
        {
            button_tick = now;
            // 有效的按钮按下事件
        }
    }
}
```

### 9.2 LED控制(推挽输出)

```c
HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_SET);    // 亮
HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_RESET);  // 灭
HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);                  // 翻转
```

### 9.3 I2C引脚(开漏复用)

```c
GPIO_InitStruct.Pin       = GPIO_PIN_6 | GPIO_PIN_7;
GPIO_InitStruct.Mode      = GPIO_MODE_AF_OD;
GPIO_InitStruct.Pull      = GPIO_PULLUP;
GPIO_InitStruct.Alternate = GPIO_AF4_I2C1;
HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
// 外部仍需4.7k上拉电阻!
```

### 9.4 电平转换(开漏 + 外部上拉到5V)

```c
GPIO_InitStruct.Pin   = GPIO_PIN_8;
GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_OD;
GPIO_InitStruct.Pull  = GPIO_NOPULL;  // 外部接10k上拉到5V
HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
// 输出低: 0V(MCU拉低)  输出高: 5V(外部上拉)
```

## 10. 常见错误与排查

### 10.1 忘记开GPIO时钟

**现象**：配置不报错但引脚无输出。**解决**：先调用`__HAL_RCC_GPIOx_CLK_ENABLE()`。

### 10.2 开漏模式忘记上拉

**现象**：输出"高电平"时引脚浮空。**解决**：I2C必须外部上拉。

### 10.3 复用功能编号错误

**现象**：外设配置正确但引脚无信号。**解决**：查参考手册AF映射表逐引脚核对。

### 10.4 引脚冲突

**现象**：某外设异常或MCU无响应。**解决**：画引脚分配表；PA13/PA14是SWD调试口，谨慎复用。

### 10.5 中断中未清除标志

**现象**：中断持续进入无法退出。**解决**：调用`__HAL_GPIO_EXTI_CLEAR_IT()`。

## 11. GPIO模式速查表

| 模式 | 驱动能力 | 典型应用 | 注意事项 |
|------|----------|----------|----------|
| 推挽输出 | 双向驱动 | LED/SPI/UART TX | 不能线与 |
| 开漏输出 | 只拉低 | I2C/电平转换 | 需外部上拉 |
| 浮空输入 | 高阻抗 | 已驱动信号 | 悬空时不稳定 |
| 上拉输入 | 默认高 | 按钮对地 | 内部R约40k |
| 下拉输入 | 默认低 | 按钮对VDD | 内部R约40k |
| 模拟 | 断开数字 | ADC/DAC | 噪声最低 |
| AF推挽 | 外设驱动 | UART/SPI/TIM | 查AF映射表 |
| AF开漏 | 外设驱动 | I2C | 需外部上拉 |

## 总结

GPIO配置模式的选择直接影响外设能否正常工作。核心要点：

1. **输出选类型**：需要双向驱动选推挽，需要线与或电平转换选开漏
2. **输入选偏置**：按钮用上拉/下拉，已有驱动的信号用浮空，ADC用模拟
3. **复用查映射**：AF编号必须查参考手册，不同引脚映射不同
4. **速度选最低**：满足时序前提下选最低速度，降低EMI
5. **时钟先使能**：不使能GPIO时钟，一切配置都无效
6. **中断清标志**：EXTI中断必须清除挂起标志，否则持续触发

## 参考文献

1. STMicroelectronics, *STM32F4 Reference Manual (RM0090)*, GPIO chapter, 2023
2. STMicroelectronics, *STM32F4 Datasheet - Pinout and AF Mapping*, 2022
3. Joseph Yiu, *The Definitive Guide to ARM Cortex-M4*, Chapter 5, Elsevier, 2021
4. Jack Ganssle, *A Guide to Debouncing*, ESD Journal, 2004
5. Texas Instruments, *Understanding I2C Pull-up Resistors*, SLVA689, 2015
