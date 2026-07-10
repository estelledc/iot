---
schema_version: '1.0'
id: spi-protocol-modes-timing
title: SPI协议四种模式与时序参数详解
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
# SPI协议四种模式与时序参数详解

> **难度**：🟢 初级 | **领域**：嵌入式通信协议 | **阅读时间**：约 18 分钟

## 引言

想象一个快递分拣中心：主管(主机)站在中央传送带旁，对每个分拣员(从机)喊"你来处理这个包裹"。传送带一直转(时钟线)，包裹放上去(数据线)，谁被点名谁就干活(片选线)。SPI总线就是这个分拣中心的电子版——一个主机控制时钟节奏，通过四根线与一个或多个从机高速交换数据。

SPI(Serial Peripheral Interface)是嵌入式世界中最常用的同步串行通信协议之一。相比I2C，它牺牲了引脚数量，换来了更高的速度和更简单的时序。理解SPI的四种模式(CPOL/CPHA组合)和时序参数，是调试任何SPI外设的第一步。

## 1. SPI总线概述

### 1.1 四根信号线

| 信号线 | 全称 | 方向(相对主机) | 作用 |
|--------|------|-----------------|------|
| MOSI | Master Out Slave In | 主机->从机 | 主机发送数据 |
| MISO | Master In Slave Out | 从机->主机 | 主机接收数据 |
| SCK | Serial Clock | 主机->从机 | 同步时钟 |
| CS/SS | Chip Select/Slave Select | 主机->从机 | 选中从机(低有效) |

四根线的命名很容易混淆。记忆方法：**MOSI的O表示Out(从主机角度)**，MISO的I表示In(从主机角度)。有些数据手册用SDO/SDI命名，此时要看是谁的视角——从机的SDO就是主机的MISO。

### 1.2 主从架构

SPI是**单主多从**架构：

- 主机(Master)：生成SCK时钟，发起通信，控制CS
- 从机(Slave)：被动响应，按SCK节拍采样/输出数据
- 从机不能主动发起通信，也不能控制时钟频率

这意味着如果两个SPI设备需要互相发起通信，要么轮流切换主从角色，要么换用其他协议(如UART)。

### 1.3 全双工通信

SPI的一大优势是**全双工**：MOSI和MISO同时传输数据。主机发送一个字节的同时，也收到从机返回的一个字节。这不像I2C那样需要切换方向，时序更简洁，吞吐更高。

实际通信流程：

1. 主机拉低CS，选中从机
2. 主机在SCK驱动下，MOSI逐位发出数据
3. 从机在同一SCK驱动下，MISO逐位返回数据
4. 8/16个时钟周期后，双方各收/发一个字节
5. 主机拉高CS，释放从机

## 2. CPOL与CPHA：四种模式的根源

### 2.1 什么是CPOL和CPHA

SPI的四种模式由两个参数决定：

- **CPOL**(Clock POLarity)：时钟空闲电平
  - CPOL=0：SCK空闲时为低电平
  - CPOL=1：SCK空闲时为高电平

- **CPHA**(Clock PHAse)：数据采样边沿
  - CPHA=0：第一个边沿(SCK跳变沿)采样数据
  - CPHA=1：第二个边沿采样数据

这两个参数决定了时钟的初始状态和数据在哪个跳变沿被读取。**主机和从机的CPOL/CPHA必须一致，否则数据全错。**

### 2.2 四种模式一览

| 模式 | CPOL | CPHA | 空闲电平 | 采样边沿 | 输出边沿 | 常用外设 |
|------|------|------|----------|----------|----------|----------|
| Mode 0 | 0 | 0 | 低 | 上升沿 | 下降沿 | 多数ADC/DAC/传感器 |
| Mode 1 | 0 | 1 | 低 | 下降沿 | 上升沿 | 部分Flash |
| Mode 2 | 1 | 0 | 高 | 下降沿 | 上升沿 | 较少见 |
| Mode 3 | 1 | 1 | 高 | 上升沿 | 下降沿 | 多数SD卡/显示驱动 |

**Mode 0和Mode 3最常见**。Mode 0是很多传感器的默认模式，Mode 3常用于SD卡和某些LCD控制器。Mode 1和Mode 2相对少见。

## 3. 四种模式的时序图详解

### 3.1 Mode 0 (CPOL=0, CPHA=0)

```
SCK:  __|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__
          1      2      3      4      5      6      7      8
MOSI: ___D7____D6____D5____D4____D3____D2____D1____D0___
          ^      ^      ^      ^      ^      ^      ^      ^
        采样    采样   采样   采样   采样   采样   采样   采样
CS:  ‾‾‾__________________________________________‾‾‾‾‾‾
```

- SCK空闲为低
- 数据在**上升沿**被从机采样
- 数据在**下降沿**由发送方切换
- 第一个数据位在CS拉低后、第一个上升沿之前就已就绪

### 3.2 Mode 1 (CPOL=0, CPHA=1)

```
SCK:  __|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__
          1      2      3      4      5      6      7      8
MOSI: ______D7____D6____D5____D4____D3____D2____D1____D0_
                ^      ^      ^      ^      ^      ^      ^      ^
              采样    采样   采样   采样   采样   采样   采样   采样
CS:  ‾‾‾__________________________________________‾‾‾‾‾‾
```

- SCK空闲为低
- 数据在**下降沿**被从机采样
- 数据在**上升沿**由发送方切换
- 第一个数据位在第一个上升沿之后才切换

### 3.3 Mode 2 (CPOL=1, CPHA=0)

```
SCK:  ‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾
          1      2      3      4      5      6      7      8
MOSI: ___D7____D6____D5____D4____D3____D2____D1____D0___
          ^      ^      ^      ^      ^      ^      ^      ^
        采样    采样   采样   采样   采样   采样   采样   采样
CS:  ‾‾‾__________________________________________‾‾‾‾‾‾
```

- SCK空闲为高
- 数据在**下降沿**被从机采样(CPOL=1时第一个跳变是下降沿)
- 数据在**上升沿**由发送方切换

### 3.4 Mode 3 (CPOL=1, CPHA=1)

```
SCK:  ‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾|__|‾‾
          1      2      3      4      5      6      7      8
MOSI: ______D7____D6____D5____D4____D3____D2____D1____D0_
                ^      ^      ^      ^      ^      ^      ^      ^
              采样    采样   采样   采样   采样   采样   采样   采样
CS:  ‾‾‾__________________________________________‾‾‾‾‾‾
```

- SCK空闲为高
- 数据在**上升沿**被从机采样
- 数据在**下降沿**由发送方切换
- 注意：Mode 3的采样/输出边沿与Mode 0相同，只是空闲电平不同

### 3.5 模式选择的实用判断方法

如果数据手册只写了"SPI Mode 0"或"CPOL=0, CPHA=0"，直接对应即可。如果只写了"数据在SCK上升沿采样"，则：

- 上升沿采样 + SCK空闲低 = Mode 0
- 上升沿采样 + SCK空闲高 = Mode 3
- 下降沿采样 + SCK空闲低 = Mode 1
- 下降沿采样 + SCK空闲高 = Mode 2

## 4. 片选管理

### 4.1 硬件CS vs 软件CS

| 方式 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 硬件CS | SPI控制器自动管理CS引脚 | 时序精确，无抖动 | 灵活性差，从机数量受限于控制器CS数 |
| 软件CS | GPIO手动拉低/拉高 | 灵活，从机数量不限 | CS与SCK之间的时序需手动保证 |

软件CS的典型代码：

```c
// 软件CS：手动控制
HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);  // 选中从机
HAL_SPI_TransmitReceive(&hspi1, tx_buf, rx_buf, len, timeout);
HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);    // 释放从机
```

### 4.2 CS时序要求

CS信号不是随便拉低就行，有两个关键时序参数：

- **t_css**(CS Setup Time)：CS拉低到SCK第一个边沿的最小间隔
- **t_csh**(CS Hold Time)：SCK最后一个边沿到CS拉高的最小间隔

如果CS拉低后立即开始时钟，从机可能还没准备好，导致第一个bit出错。大多数从机要求t_css至少几十纳秒。

## 5. 多从机配置

### 5.1 独立CS方式(最常用)

每个从机分配一根独立的CS线，主机同一时刻只拉低一根CS：

```
主机 MOSI ─────┬─── 从机1 MOSI
               └─── 从机2 MOSI

主机 MISO ─────┬─── 从机1 MISO
               └─── 从机2 MISO

主机 SCK  ─────┬─── 从机1 SCK
               └─── 从机2 SCK

主机 CS0  ───────── 从机1 CS
主机 CS1  ───────── 从机2 CS
```

优点：每个从机可独立工作，甚至可以使用不同的SPI模式(通过切换CPOL/CPHA)。缺点：每加一个从机多占一根GPIO。

### 5.2 菊花链方式(Daisy-chain)

从机的MISO连到下一个从机的MOSI，数据像穿珠子一样依次移位通过所有从机：

```
主机 MOSI ──> 从机1 MOSI
从机1 MISO ──> 从机2 MOSI
从机2 MISO ──> 主机 MISO
主机 SCK  ──> 所有从机 SCK
主机 CS   ──> 所有从机 CS
```

优点：只用一根CS。缺点：所有从机必须同时移位，不能单独访问；所有从机的数据宽度必须已知；延迟随从机数量线性增长。菊花链在实际项目中较少见，常见于多片ADC级联。

## 6. 时钟速度考量

### 6.1 SPI时钟频率范围

SPI没有协议规定的固定速率，时钟频率完全由主机决定，这是SPI比I2C快得多的根本原因。典型范围：

| 场景 | 典型频率 |
|------|----------|
| 低速传感器(温度/湿度) | 1 - 5 MHz |
| Flash存储器 | 10 - 80 MHz |
| 高速ADC/DAC | 20 - 50 MHz |
| STM32F4 SPI最高 | 42 MHz(APB2/2) |
| STM32H7 SPI最高 | 150 MHz |

### 6.2 频率选择原则

1. **不超从机最高频率**：查数据手册的f_SCK(max)
2. **不超MCU SPI外设最高频率**：取决于APB总线分频
3. **留余量**：长走线、高负载电容时降低频率
4. **EMI考虑**：高速SPI信号可能成为辐射源，必要时降频或加匹配电阻

## 7. DMA与SPI：高吞吐的搭档

### 7.1 为什么需要DMA

不用DMA时，每收/发一个字节都需要CPU干预(中断或轮询)。以1 MHz SPI为例，每秒125 KB数据，每8 us一次中断——CPU大量时间花在中断上下文切换上。

DMA(Direct Memory Access)让SPI控制器直接读写内存，CPU只需在传输完成后处理数据：

```c
// DMA方式：CPU几乎不参与数据搬运
HAL_SPI_TransmitReceive_DMA(&hspi1, tx_buf, rx_buf, len);

// 传输完成回调
void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *hspi)
{
    // 数据已在rx_buf中，开始处理
    process_data(rx_buf, len);
}
```

### 7.2 DMA注意事项

- **缓冲区对齐**：某些MCU的DMA要求缓冲区地址对齐到4字节(或cache line大小)
- **Cache一致性**：如果MCU有D-Cache，DMA读内存前需清cache(stale数据)，DMA写内存后需invalidate cache(让CPU看到新数据)
- **双缓冲**：部分STM32的DMA支持Circular模式，配合半传输完成中断可实现乒乓缓冲

## 8. STM32 SPI HAL实例

### 8.1 初始化配置

```c
SPI_HandleTypeDef hspi1;

void MX_SPI1_Init(void)
{
    hspi1.Instance               = SPI1;
    hspi1.Init.Mode              = SPI_MODE_MASTER;     // 主机模式
    hspi1.Init.Direction         = SPI_DIRECTION_2LINES; // 全双工
    hspi1.Init.DataSize          = SPI_DATASIZE_8BIT;   // 8位帧
    hspi1.Init.CLKPolarity       = SPI_POLARITY_LOW;    // CPOL=0
    hspi1.Init.CLKPhase          = SPI_PHASE_1EDGE;     // CPHA=0 -> Mode 0
    hspi1.Init.NSS               = SPI_NSS_SOFT;        // 软件CS
    hspi1.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_8; // APB2/8
    hspi1.Init.FirstBit          = SPI_FIRSTBIT_MSB;    // 高位在前
    hspi1.Init.TIMode            = SPI_TIMODE_DISABLE;  // 不用TI模式
    hspi1.Init.CRCCalculation    = SPI_CRCCALCULATION_DISABLE;
    hspi1.Init.CRCPolynomial     = 7;
    HAL_SPI_Init(&hspi1);
}
```

### 8.2 阻塞式收发

```c
uint8_t tx_data[4] = {0x03, 0x00, 0x00, 0x00};  // Flash读命令+地址
uint8_t rx_data[4] = {0};

HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
HAL_SPI_TransmitReceive(&hspi1, tx_data, rx_data, 4, 100);  // 100ms超时
HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
```

### 8.3 中断式收发

```c
HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
HAL_SPI_TransmitReceive_IT(&hspi1, tx_data, rx_data, 4);
// 传输完成后进入 HAL_SPI_TxRxCpltCallback
```

### 8.4 只发不收(如驱动DAC)

```c
HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
HAL_SPI_Transmit(&hspi1, &dac_value, 1, 100);
HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
```

## 9. Quad-SPI(QSPI)：Flash的加速通道

### 9.1 标准SPI的瓶颈

标准SPI一个时钟周期传1 bit。读一个256 KB的Flash扇区，在50 MHz下需要：

```
256 * 1024 * 8 / 50,000,000 = 41.9 ms
```

对启动时间或实时图形缓冲区来说，这太慢了。

### 9.2 QSPI原理

QSPI在数据阶段同时使用4根信号线(SIO0-SIO3)，一个时钟周期传4 bit，理论吞吐是标准SPI的4倍：

| 信号 | 标准SPI | QSPI |
|------|---------|------|
| 数据线 | MOSI + MISO (2根) | SIO0 + SIO1 + SIO2 + SIO3 (4根) |
| 每周期bit数 | 1 | 4 |
| 256 KB读取(50MHz) | 41.9 ms | 10.5 ms |

QSPI常用于MCU连接外部Flash存储XIP(eXecute In Place)——直接从外部Flash取指令执行，无需先拷贝到内部RAM。

### 9.3 QSPI命令序列

一次QSPI操作由若干阶段组成：

```c
// STM32 HAL QSPI读Flash ID示例
QSPI_CommandTypeDef cmd;
cmd.InstructionMode    = QSPI_INSTRUCTION_1_LINE;  // 命令阶段：1线
cmd.Instruction        = 0x9F;                     // Read ID命令
cmd.AddressMode        = QSPI_ADDRESS_NONE;        // 无地址阶段
cmd.AlternateByteMode  = QSPI_ALTERNATE_BYTES_NONE;
cmd.DataMode           = QSPI_DATA_4_LINES;        // 数据阶段：4线
cmd.NbData             = 3;                        // 读3字节
cmd.DummyCycles        = 0;                        // 无dummy周期
HAL_QSPI_Command(&hqspi, &cmd, 100);
```

## 10. 常见问题与排查

### 10.1 模式不匹配

**现象**：收到的数据全是0xFF或0x00，或者数据错位。

**原因**：主机和从机的CPOL/CPHA不一致。

**排查**：

1. 查从机数据手册，确认其SPI模式
2. 用示波器或逻辑分析仪看SCK空闲电平和采样边沿
3. 对比主机配置中的CPOL/CPHA

**示例**：W25Q16 Flash默认Mode 0，但某STM32例程配成了Mode 3——读出的ID全是0xFF。改成Mode 0后正常。

### 10.2 CS时序问题

**现象**：第一个字节总是错的，后续字节正确。

**原因**：CS拉低到SCK起始之间没有足够的setup time。

**排查**：

1. 在CS拉低后加一小段延时，或在两次传输间确保CS有过拉高
2. 检查是否在连续传输时CS一直保持低——有些从机要求每次传输都重新拉高CS(如W25Q的Read Status Reg)

### 10.3 时钟过快

**现象**：近距离短走线正常，加长线后数据出错。

**原因**：长走线的RC延迟导致信号边沿变缓，采样时刻信号未稳定。

**排查**：降低SCK频率，或使用更短的PCB走线，必要时加缓冲器。

### 10.4 MISO浮空

**现象**：不通信时MISO线上有毛刺，或读到随机数据。

**原因**：未被选中的从机MISO应输出高阻态，但有些从机实现不佳，或缺少上拉电阻。

**排查**：在MISO线上加10K-47K上拉电阻，确保无从机选中时MISO为确定电平。

## 11. SPI vs I2C快速对比

| 特性 | SPI | I2C |
|------|-----|-----|
| 信号线 | 4根(MOSI/MISO/SCK/CS) | 2根(SDA/SCL) |
| 通信方式 | 全双工 | 半双工 |
| 速度 | 高(几MHz~几十MHz) | 低(100K/400K/3.4M) |
| 寻址方式 | 硬件CS(引脚) | 软件地址(7/10位) |
| 多从机 | 每加一个从机多一根CS | 不额外占引脚 |
| 协议开销 | 几乎无(无地址帧) | 有起始位/地址/ACK |
| 时钟 | 主机完全控制 | 主机控制，但从机可clock stretching |
| 适用场景 | 高速、短距离、引脚充裕 | 低速、引脚紧张、多设备 |

**选择建议**：

- 需要速度(如Flash、高速ADC) -> SPI
- 引脚紧张或设备多(如多个低速传感器) -> I2C
- 需要全双工 -> SPI
- 需要一条总线挂很多设备 -> I2C

## 总结

SPI的四种模式本质上就是两个二选一的组合：时钟空闲电平选高还是低(CPOL)，数据在第一个跳变沿还是第二个跳变沿采样(CPHA)。掌握这个核心逻辑，配合数据手册的时序图，就能正确配置任何SPI外设。

关键要点回顾：

1. **四线结构**：MOSI/MISO/SCK/CS，全双工同步传输
2. **四种模式**：CPOL和CPHA各0/1，Mode 0和Mode 3最常用
3. **匹配是硬要求**：主机和从机的模式必须一致，否则数据全错
4. **CS不是摆设**：注意setup/hold time，尤其是连续传输时
5. **多从机用独立CS**：菊花链在少数场景有用，但调试难度大
6. **DMA是标配**：超过1 MHz的SPI应该用DMA，避免CPU被中断淹没
7. **QSPI是加速版**：4线并行，Flash读取的标配

下一步学习建议：用逻辑分析仪抓一次真实的SPI波形，对照四种模式的时序图逐一确认，这比看十遍文章都有效。

## 参考文献

1. Motorola. *MC68HC11 Reference Manual* - SPI协议的原始定义来源
2. Texas Instruments. *SPI — Serial Peripheral Interface* (SLAU208), 2022 - 四种模式的权威时序说明
3. STMicroelectronics. *STM32F4 Reference Manual (RM0090)*, Chapter 28: SPI - STM32 SPI外设寄存器与配置详解
4. JEDEC. *JESD216: Serial Flash Discoverable Parameters (SFDP)* - QSPI Flash标准规范
5. W25Q16JV Data Sheet, Winbond - 典型SPI Flash的时序参数与模式要求
