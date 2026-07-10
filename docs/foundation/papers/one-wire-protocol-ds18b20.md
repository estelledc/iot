---
schema_version: '1.0'
id: one-wire-protocol-ds18b20
title: 1-Wire协议与DS18B20温度传感器实战
layer: 1
content_type: UNKNOWN
difficulty: beginner
reading_time: 15
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 1-Wire协议与DS18B20温度传感器实战

> **难度**：🟢 初级 | **领域**：单总线通信 | **阅读时间**：约 15 分钟

## 引言

想象你在一个教室里，老师只用一根麦克风线就能逐个点名、让每个学生回答问题——不需要每个学生单独一根线，也不需要额外的电源线，因为麦克风线本身就能提供微弱的电力。这就是 1-Wire 协议的精髓：一根数据线加一根地线，就能完成供电、寻址和通信三件事。

在 IoT 温度采集场景中，DS18B20 是最经典的 1-Wire 器件。它只需要三根线就能工作，甚至可以省掉电源线靠数据线"寄生供电"。这种极简接线让它在冷链物流、温室大棚、机房监控等场景中广受欢迎。本文将从协议原理到代码实现，完整拆解 1-Wire 通信和 DS18B20 的实战要点。

## 1. 1-Wire 协议概述

### 1.1 单总线架构

1-Wire 是 Dallas Semiconductor(现 Maxim Integrated)开发的半双工通信协议，物理层只需一根数据线和一根地线：

```
Master (MCU)                        Slave (DS18B20)
    VCC ----+                            +---- VDD(可选)
           |                            |
    GPIO ---+---- 4.7K 上拉 ---总线-----+---- DQ
           |                            |
    GND ----+----------------------------+---- GND
```

关键特征：只有一根数据线(DQ)，所有设备共享；开漏输出需要外部上拉电阻(通常 4.7k)；线空闲时为高电平；通信由 Master 完全控制。

### 1.2 寄生供电模式

1-Wire 最巧妙的设计之一是寄生供电(Parasitic Power Mode)：VDD 接地，DQ 同时负责供电和通信。总线高电平时 Slave 内部电容充电储能，低电平时靠电容维持工作。温度转换期间电流较大(约 1mA)，需要额外强上拉(MOSFET 拉高)。寄生供电的限制：转换期间必须提供强上拉，通信速度受电容影响，长线缆时更明显。

### 1.3 64位ROM ID

每个 1-Wire 器件出厂时烧录了唯一的 64 位 ROM ID：

```
| 8-bit CRC | 48-bit 序列号 | 8-bit 家族码 |
|   (MSB)   |               |   (LSB)      |

家族码: 标识器件类型 (DS18B20 = 0x28)
序列号: 全球唯一标识
CRC-8: 校验前 56 位数据的完整性
```

同一总线上可以挂载多个同类器件，通过 ROM ID 逐一寻址。ROM ID 的唯一性保证了即使同型号器件也能被区分。

## 2. 1-Wire 通信时序

### 2.1 复位与存在脉冲

所有 1-Wire 通信以复位脉冲开始：

```
Master 发复位脉冲:      拉低 480us 以上，释放
Slave 回存在脉冲:       拉低 60-240us

DQ: ‾‾‾\________________________________/‾‾‾\____________/‾‾‾‾‾‾
         |<--- 480us 最小 --->|         |<-- 60-240us -->|
         Master 拉低                Slave 拉低(存在脉冲)
```

Master 在释放后 60us 内采样，低电平表示有器件响应。

### 2.2 读写时隙

写操作通过拉低时间长短区分 0 和 1：

```
写 0: 拉低 60us 以上，释放
写 1: 拉低 1-15us，释放(让上拉电阻拉高)

DQ 写 0: \________________/‾‾‾‾‾   (拉低 >= 60us)
DQ 写 1: \_/‾‾‾‾‾‾‾‾‾‾‾‾‾/‾‾‾‾‾   (拉低 1-15us，然后释放)
```

读操作由 Master 拉低 1us 以上后释放，在 15us 内采样总线电平——Slave 发 0 则持续拉低，发 1 则释放总线。每个时隙 120us 内完成，时隙间至少 1us 恢复。

关键时序参数：

| 操作 | 最小时间 | 典型时间 |
|------|----------|----------|
| 复位脉冲拉低 | 480 us | 500 us |
| 存在脉冲检测窗口 | 60 us | 70 us |
| 写 0 拉低 | 60 us | 65 us |
| 写 1 拉低 | 1 us | 10 us |
| 读采样窗口 | 1 us | 10 us |

1-Wire 没有独立时钟线，所有时序依赖精确延时控制，这是实现中最容易出问题的环节。

## 3. ROM 命令与功能命令

### 3.1 ROM 命令

| 命令 | 代码 | 功能 | 典型场景 |
|------|------|------|----------|
| Search ROM | 0xF0 | 搜索总线上所有 ROM ID | 枚举总线设备 |
| Read ROM | 0x33 | 读取唯一器件的 ROM ID | 总线仅 1 个器件 |
| Match ROM | 0x55 | 匹配指定 ROM ID | 定点操作某器件 |
| Skip ROM | 0xCC | 跳过 ROM 匹配 | 总线仅 1 个器件 |
| Alarm Search | 0xEC | 搜索报警器件 | 温度超限巡检 |

Search ROM 的原理是二叉树遍历：每个 Slave 先发某位原值再发反码，Master 据此判断一致性或冲突点，通过 64 次交互确定一个 ROM ID，再在冲突位选另一分支继续搜索。

### 3.2 DS18B20 功能命令

| 命令 | 代码 | 功能 |
|------|------|------|
| Convert T | 0x44 | 启动温度转换 |
| Write Scratchpad | 0x4E | 写暂存器(TH/TL/配置) |
| Read Scratchpad | 0xBE | 读暂存器(9字节) |
| Copy Scratchpad | 0x48 | 暂存器复制到 EEPROM |
| Read Power Supply | 0xB4 | 读取供电模式 |

### 3.3 典型通信流程

单器件温度读取：Reset -> Skip ROM -> Convert T -> 等待转换 -> Reset -> Skip ROM -> Read Scratchpad -> 读取9字节 -> CRC校验。

多器件效率优化：Skip ROM + Convert T 广播启动所有器件转换，等待后逐一 Match ROM + Read Scratchpad 读取结果。这种方式利用了 Convert T 命令在 Skip ROM 模式下的广播特性，所有器件同时执行温度转换，总等待时间仅需一次 750ms(12-bit)而非 N x 750ms。

## 4. DS18B20 温度传感器详解

### 4.1 基本参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 测量范围 | -55 ~ +125 C | 涵盖绝大多数场景 |
| 精度 | +/-0.5 C | -10 ~ +85 C 范围内 |
| 分辨率 | 9/10/11/12-bit 可选 | 默认 12-bit |
| 转换时间 | 93.75ms(9-bit) ~ 750ms(12-bit) | 分辨率越高越慢 |
| 供电电压 | 3.0 ~ 5.5 V | 兼容 3.3V 和 5V |

### 4.2 温度数据格式

16 位温度寄存器采用补码格式，高 5 位为符号位：

```
| S S S S S S B10 B9 | B8 B7 B6 B5 B4 B3 B2 B1 |

S = 符号位(0=正, 1=负)
B10-B1 = 温度值(2 的补码)
12-bit: 0.0625 C / LSB, 11-bit: 0.125 C / LSB
10-bit: 0.25 C / LSB, 9-bit: 0.5 C / LSB
```

正温度示例：0x0191 = 401，401 x 0.0625 = 25.0625 C。负温度取补码计算：0xFF5E 取补码得 0x00A2 = 162，-162 x 0.0625 = -10.125 C。

### 4.3 暂存器与分辨率配置

9 字节暂存器：Byte 0-1 温度值，Byte 2-3 报警阈值，Byte 4 配置字节，Byte 5-7 保留，Byte 8 CRC-8。配置字节的 R1/R0 位决定分辨率：00=9-bit(93.75ms)，01=10-bit(187.5ms)，10=11-bit(375ms)，11=12-bit(750ms)。

设置分辨率：Write Scratchpad(0x4E) 写入 TH/TL/配置字节后，Copy Scratchpad(0x48) 保存到 EEPROM。

## 5. CRC 校验

1-Wire 使用 CRC-8 多项式 x^8 + x^5 + x^4 + 1。读取 Scratchpad 前 8 字节计算 CRC 与第 9 字节比较，一致则数据有效。

```c
// CRC-8 查表法
static const uint8_t crc8_table[256] = {
    0x00, 0x5E, 0xBC, 0xE2, 0x61, 0x3F, 0xDD, 0x83,
    0xC2, 0x9C, 0x7E, 0x20, 0xA3, 0xFD, 0x1F, 0x41,
    // ... 完整 256 项 ...
};

uint8_t ow_crc8(const uint8_t *data, uint8_t len) {
    uint8_t crc = 0;
    for (uint8_t i = 0; i < len; i++)
        crc = crc8_table[crc ^ data[i]];
    return crc;
}
```

## 6. 多传感器单总线操作

### 6.1 总线挂载能力

总线挂载能力受线缆电容、寄生供电电流、通信时间等制约：

| 限制因素 | 影响 | 典型上限 |
|----------|------|----------|
| 总线电容 | 上升沿变慢，时序裕量减少 | 线缆 < 30m 时约 20 个 |
| 寄生供电电流 | 转换时总电流超过上拉能力 | 寄生模式约 10 个 |
| 通信时间 | Search ROM 和逐个读取耗时 | 数量多时实时性下降 |
| 上拉电阻 | 阻值影响上升时间和驱动能力 | 4.7k 为典型值 |

### 6.2 多传感器读取策略

推荐策略：广播启动所有器件转换，等待后逐一读取，兼顾效率和简单性。

```
策略一: 广播启动 + 逐一读取 (推荐)
  Skip ROM -> Convert T  (所有器件同时转换)
  等待 750ms
  for each sensor:
    Match ROM -> Read Scratchpad

策略二: 分组启动 (兼顾功耗和速度)
  将传感器分组，每组同时转换
  适合寄生供电场景，控制每组电流
```

## 7. STM32 GPIO Bit-banging 实现

### 7.1 底层时序

```c
// DWT 精确延时 (Cortex-M)
void dwt_init(void) {
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
}
void delay_us(uint32_t us) {
    uint32_t start = DWT->CYCCNT;
    uint32_t ticks = us * (SystemCoreClock / 1000000);
    while ((DWT->CYCCNT - start) < ticks);
}

// 复位 + 存在脉冲检测
uint8_t ow_reset(void) {
    OW_LOW(); delay_us(480);  // 拉低 480us
    OW_HIGH(); delay_us(70);
    uint8_t presence = OW_READ(); // 0=有器件
    delay_us(410);
    return presence;
}

// 写字节 (LSB first)
void ow_write_byte(uint8_t byte) {
    for (uint8_t i = 0; i < 8; i++) {
        if (byte & 0x01) {
            OW_LOW(); delay_us(6); OW_HIGH(); delay_us(64);
        } else {
            OW_LOW(); delay_us(60); OW_HIGH(); delay_us(10);
        }
        byte >>= 1;
    }
}

// 读字节 (LSB first)
uint8_t ow_read_byte(void) {
    uint8_t byte = 0;
    for (uint8_t i = 0; i < 8; i++) {
        OW_LOW(); delay_us(6); OW_HIGH(); delay_us(9);
        if (OW_READ()) byte |= (1 << i);
        delay_us(55);
    }
    return byte;
}
```

### 7.2 DS18B20 温度读取

```c
float ds18b20_read_temp(void) {
    uint8_t buf[9];
    // 启动转换
    ow_reset(); ow_write_byte(0xCC); ow_write_byte(0x44);
    HAL_Delay(750); // 12-bit 转换时间
    // 读取结果
    ow_reset(); ow_write_byte(0xCC); ow_write_byte(0xBE);
    for (uint8_t i = 0; i < 9; i++) buf[i] = ow_read_byte();
    // CRC 校验
    if (ow_crc8(buf, 8) != buf[8]) return -999.0f;
    // 计算温度
    int16_t raw = (buf[1] << 8) | buf[0];
    return (float)raw * 0.0625f;
}
```

## 8. 常见问题与调试

### 8.1 时序敏感性问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 延时不精确 | HAL_Delay 精度仅 1ms | 使用 DWT 或 TIM 做 us 延时 |
| 中断干扰 | 1-Wire 时隙被打断 | 关键段内 __disable_irq() |
| RTOS 切换 | 任务切换破坏时序 | 互斥锁保护或提高优先级 |

### 8.2 85 C 默认值问题

最常见的新手坑：读到温度永远是 85.0 C。85.0 C(0x0550)是上电默认值，说明温度转换未成功。排查步骤：(1) 检查复位和存在脉冲；(2) 确认转换等待时间足够；(3) 寄生供电检查强上拉；(4) 打印 Scratchpad 全部 9 字节验证 CRC。

### 8.3 长线缆布线

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 通信失败 | 线缆电容过大，上升沿变慢 | 降低上拉电阻(至 2.2k) |
| 读数跳变 | 反射信号干扰 | 线缆末端加 100R 终端电阻 |
| 器件丢失 | 电压降过大 | 使用更粗线缆或星形拓扑 |
| 串扰 | 平行走线耦合 | 双绞线或远离干扰源 |

线缆 < 30m 通常无需特殊处理；超过 30m 用屏蔽双绞线，DQ 和 GND 绞合，上拉电阻降至 2.2k；超过 100m 考虑 DS2480B 中继器。避免星形拓扑，优先线性拓扑，最远端加 100R 终端电阻。

实用建议：使用 CAT5 网线时，一对双绞线给 DQ + GND，另一对给 VCC + GND(外部供电模式)，屏蔽层单端接 GND。

## 9. 实际应用接线方案

### 9.1 基础三线制接线

```
最简方案(外部供电):
  DS18B20 pin1 (GND) --> GND
  DS18B20 pin2 (DQ)  --> MCU GPIO + 4.7k 上拉到 VCC
  DS18B20 pin3 (VDD) --> VCC (3.3V 或 5V)
```

### 9.2 寄生供电接线

```
寄生供电方案:
  DS18B20 pin1 (GND) --> GND
  DS18B20 pin2 (DQ)  --> MCU GPIO + 4.7k 上拉
  DS18B20 pin3 (VDD) --> GND

  温度转换时需额外强上拉:
  MCU 另一 GPIO --> MOSFET Gate
  MOSFET: VCC --> Drain, Source --> DQ 总线
```

### 9.3 长线缆多点测温

长线缆方案(> 30m)建议使用 CAT5 网线：一对双绞线接 DQ + GND，另一对接 VCC + GND(外部供电模式)，屏蔽层单端接地。最远端 DS18B20 的 DQ 与 GND 间加 100R 电阻，上拉电阻改为 2.2k 增强驱动。

## 总结

1-Wire 协议用极简的硬件设计实现了完整的寻址、供电和通信。DS18B20 核心要点：(1) 时序是生命线，DWT 或 TIM 是必须的延时工具；(2) 寄生供电省线但增加强上拉复杂度；(3) CRC 校验不可省，长线缆下数据出错概率不低；(4) 85 C 默认值是调试风向标；(5) 多传感器广播启动加逐一读取最实用。掌握 1-Wire 和 DS18B20，就掌握了单总线通信的基本范式，后续接触其他 1-Wire 器件(如 DS2431 EEPROM、DS2406 开关)会非常容易上手。

## 参考文献

1. Maxim Integrated. DS18B20 Digital Thermometer Datasheet. Rev. 19-7262, 2019.
2. Maxim Integrated. 1-Wire Communication Protocol Application Note 937. 2008.
3. Maxim Integrated. Guidelines for Reliable Long Line 1-Wire Networks Application Note 148. 2012.
4. Dallas Semiconductor. Book of iButton Standards. 2002.
5. STMicroelectronics. STM32 HAL Driver User Manual. UM1850, 2023.
