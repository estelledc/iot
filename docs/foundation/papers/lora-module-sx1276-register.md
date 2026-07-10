---
schema_version: '1.0'
id: lora-module-sx1276-register
title: LoRa模组SX1276寄存器配置与扩频参数
layer: 1
content_type: UNKNOWN
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# LoRa模组SX1276寄存器配置与扩频参数

> **难度**：🟡 中级 | **领域**：LoRa射频配置 | **阅读时间**：约 20 分钟

## 引言

想象你在调一台老式收音机:拧频率旋钮找到电台,拧音量旋钮调声音大小。SX1276就是LoRa世界的"收音机",只不过它的"旋钮"是一组寄存器--通过SPI往特定地址写不同的值,就能切换频率、调节功率、改变扩频参数。如果你只停留在用别人的库函数而不知道底层寄存器在干什么,那就像只会按收音机预设键而不会手动搜台--遇到干扰换频段时就无从下手。

本文从SX1276/SX1278的寄存器地图出发,逐组拆解扩频参数(SF/BW/CR)的含义和配置方法,覆盖模式切换、FIFO管理、中断映射、频率与功率设置,最后给出一份可直接运行的配置代码和速率-距离权衡表。

## 1. SX1276/SX1278芯片概述

### 1.1 芯片定位

SX1276是Semtech推出的Sub-GHz远距离扩频收发器,覆盖137MHz~1020MHz频段。SX1278是其高频版本(覆盖2.4GHz以外的Sub-GHz频段,引脚和寄存器完全兼容)。两者共享同一套寄存器地图,固件可互换。

### 1.2 核心特性

| 参数 | SX1276 | SX1278 |
|------|--------|--------|
| 频率范围 | 137-1020 MHz | 137-1020 MHz |
| 调制方式 | LoRa / FSK/OOK | LoRa / FSK/OOK |
| 最大发射功率 | +20 dBm (PA_BOOST) | +20 dBm (PA_BOOST) |
| 接收灵敏度 | -148 dBm (SF12, BW125) | -148 dBm (SF12, BW125) |
| 接口 | SPI (最高10MHz) | SPI (最高10MHz) |
| 工作电压 | 1.8-3.7 V | 1.8-3.7 V |
| 接收电流 | 10.8 mA (LoRa模式) | 10.8 mA (LoRa模式) |

### 1.3 内部功能框图

```
  SPI接口 --> 寄存器组 --> 调制器 --> PA --> 天线
                ^                             |
                |          LNA <-- 射频前端 <--|
                +---- 解调器 <-- ADC <--------+
```

芯片内部集成了完整的射频前端:调制器、功率放大器(PA)、低噪声放大器(LNA)、混频器、PLL和ADC。MCU只需通过SPI读写寄存器即可控制全部功能。

## 2. LoRa调制基础:CSS啁啾扩频

### 2.1 CSS原理

CSS(Chirp Spread Spectrum)的核心是将数据编码为频率随时间线性变化的"啁啾"信号:

- 上啁啾(Up-Chirp):频率从低到高线性扫描,表示默认基线
- 下啁啾(Down-Chirp):频率从高到低,用于同步
- 数据啁啾:通过起始频率偏移编码不同数据值

每个啁啾信号覆盖整个带宽B,持续时间为 T_symbol = 2^SF / B。接收端通过FFT或匹配滤波检测啁啾的起始频率偏移,还原出数据。

### 2.2 扩频因子(SF)

扩频因子SF7~SF12决定了每个符号的码片数:

```
码片数 = 2^SF
符号速率 = BW / 2^SF
每符号比特数 = SF
```

| SF | 码片/符号 | 符号时间(ms) @125kHz | 比特率(bps) @125kHz | 灵敏度(dBm) |
|----|----------|---------------------|--------------------|----|
| 7  | 128      | 1.0                 | 5469               | -123 |
| 8  | 256      | 2.0                 | 3125               | -126 |
| 9  | 512      | 4.1                 | 1758               | -129 |
| 10 | 1024     | 8.2                 | 977                | -132 |
| 11 | 2048     | 16.4                | 537                | -134.5 |
| 12 | 4096     | 32.8                | 293                | -137 |

SF越大,灵敏度越高(可接收更弱信号),但速率越低。这就是LoRa最核心的速率-距离权衡。

### 2.3 带宽(BW)与编码率(CR)

**带宽**:LoRa支持125/250/500kHz三种标准带宽。更宽的带宽意味着更高的数据速率,但噪声功率也按比例增加,灵敏度降低约3dB每倍带宽。

**编码率**:CR=4/(4+n),n=1~4,对应4/5、4/6、4/7、4/8。更高的编码率提供更强的抗突发干扰能力,但有效载荷速率降低:

| CR | 编码率 | 开销 | 抗干扰能力 |
|----|--------|------|-----------|
| 1  | 4/5    | 20%  | 最低      |
| 2  | 4/6    | 33%  | 较低      |
| 3  | 4/7    | 43%  | 中等      |
| 4  | 4/8    | 50%  | 最高      |

一般应用选CR=1(4/5),强干扰环境选CR=4(4/8)。

### 2.4 链路预算计算

链路预算决定了最远通信距离:

```
链路预算(dB) = 发射功率(dBm) - 接收灵敏度(dBm)
```

例如:发射+14dBm,接收灵敏度-137dBm(SF12,BW125):

```
链路预算 = 14 - (-137) = 151 dB
```

自由空间路径损耗(FSPL)估算:

```
FSPL(dB) = 20*log10(d) + 20*log10(f) + 32.44
```

其中d为距离(km),f为频率(MHz)。470MHz下10km的FSPL约105dB,加上裕量后151dB的链路预算可支持10~15km视距通信。

## 3. 寄存器地图概览

### 3.1 地址空间分布

SX1276的寄存器地址从0x00到0x7F,按功能分组:

| 地址范围 | 功能 | 备注 |
|----------|------|------|
| 0x00-0x07 | FIFO与基本控制 | LoRa/FSK共用 |
| 0x08-0x0F | 中断与标志 | DIO映射、中断标志 |
| 0x10-0x1F | LoRa调制参数 | SF、BW、CR、CRC |
| 0x20-0x27 | 频率与信道 | 载波频率设置 |
| 0x28-0x2B | 发射功率与PA | 输出功率、PA选择 |
| 0x2C-0x2F | 接收配置 | LNA增益、AGC |
| 0x30-0x37 | 数据包格式 | 前导码、头模式 |
| 0x38-0x3F | FIFO地址 | 读写指针 |
| 0x40-0x4F | IRQ标志与掩码 | 中断状态 |
| 0x50-0x6F | 校准与测试 | 生产用,一般不改 |

### 3.2 SPI访问协议

SX1276的SPI时序:CS拉低后,第一个字节的最高位决定读/写,低7位为寄存器地址:

```
写: [0x80 | addr][data]     -- bit7=1 表示写
读: [0x00 | addr][dummy]    -- bit7=0 表示读,第二个字节为dummy(0xFF)
```

SPI模式:CPOL=0,CPHA=0(即Mode 0),最高10MHz。

```c
// SPI读写示例 (STM32 HAL)
uint8_t SX1276_ReadReg(uint8_t addr) {
    uint8_t tx = addr & 0x7F;  // bit7=0, 读操作
    uint8_t rx = 0;
    HAL_GPIO_WritePin(NSS_GPIO, NSS_PIN, GPIO_PIN_RESET);
    HAL_SPI_TransmitReceive(&hspi1, &tx, &rx, 1, 100);
    HAL_SPI_TransmitReceive(&hspi1, &(uint8_t){0xFF}, &rx, 1, 100);
    HAL_GPIO_WritePin(NSS_GPIO, NSS_PIN, GPIO_PIN_SET);
    return rx;
}

void SX1276_WriteReg(uint8_t addr, uint8_t data) {
    uint8_t tx = addr | 0x80;  // bit7=1, 写操作
    HAL_GPIO_WritePin(NSS_GPIO, NSS_PIN, GPIO_PIN_RESET);
    HAL_SPI_Transmit(&hspi1, &tx, 1, 100);
    HAL_SPI_Transmit(&hspi1, &data, 1, 100);
    HAL_GPIO_WritePin(NSS_GPIO, NSS_PIN, GPIO_PIN_SET);
}
```

## 4. 模式切换

### 4.1 工作模式

SX1276有6种工作模式,通过RegOpMode(0x01)寄存器配置:

| 模式 | Mode位[2:0] | 电流 | 用途 |
|------|-------------|------|------|
| Sleep | 000 | 0.2uA | 最低功耗,可改寄存器 |
| Standby | 001 | 1.5mA | 可配置所有寄存器 |
| FS-TX | 010 | 11mA | 频率合成器打开(发送准备) |
| TX | 011 | 29~120mA | 发射中 |
| FS-RX | 100 | 11mA | 频率合成器打开(接收准备) |
| RX | 101 | 10.8mA | 接收中 |

### 4.2 模式切换流程

必须经过Standby模式中转:

```
Sleep --> Standby --> TX/RX
  (改配置)   (配参数)  (开始工作)
```

关键步骤:
1. 写RegOpMode进入Standby
2. 配置频率、功率、调制参数
3. 写RegOpMode进入TX或RX
4. 等待DIO中断或轮询RegIrqFlags

```c
void SX1276_SetMode(uint8_t mode) {
    uint8_t reg = SX1276_ReadReg(0x01);
    reg = (reg & 0xF8) | (mode & 0x07);  // 保留高位,改低3位
    SX1276_WriteReg(0x01, reg);
}
```

## 5. 频率配置寄存器

### 5.1 载波频率计算

载波频率由三个寄存器RegFrfMsb/Mid/Lsb(0x06-0x08)设置:

```
Frf = (Frf_23_16 << 16 | Frf_15_8 << 8 | Frf_7_0) * Fstep
Fstep = Fxosc / 2^19 = 32MHz / 524288 = 61.03515625 Hz
```

以470MHz为例:

```
470000000 / 61.03515625 = 7700480 = 0x757480
RegFrfMsb = 0x75
RegFrfMid = 0x74
RegFrfLsb = 0x80
```

```c
void SX1276_SetFrequency(uint32_t freq_hz) {
    uint32_t frf = (freq_hz << 19) / 32000000;
    SX1276_WriteReg(0x06, (frf >> 16) & 0xFF);
    SX1276_WriteReg(0x07, (frf >> 8) & 0xFF);
    SX1276_WriteReg(0x08, frf & 0xFF);
}
```

## 6. 功率放大器与发射功率

### 6.1 PA_BOOST vs RFO

SX1276有两个射频输出引脚:

| 输出 | 最大功率 | 引脚 | 适用场景 |
|------|---------|------|---------|
| RFO_HF | +14 dBm | RFO_HF | 低功率,直连天线 |
| PA_BOOST | +20 dBm | PA_BOOST | 远距离,加外部PA |

RegPaConfig(0x09)控制PA选择:

```
bit7: PaSelect  -- 0=RFO, 1=PA_BOOST
bit6-4: (PaSelect=1时) MaxPower, 输出功率上限
bit3-0: OutputPower, 功率步进
```

### 6.2 功率计算

PA_BOOST模式下的输出功率:

```
Pout = 17 - (15 - OutputPower)  (dBm)
```

例如OutputPower=0xF时,Pout=17dBm;OutputPower=0x0时,Pout=2dBm。

若需要+20dBm,还需设置RegPaDac(0x4D)=0x87(高功率模式)。

```c
void SX1276_SetPower(int8_t power_dbm) {
    if (power_dbm > 20) power_dbm = 20;
    if (power_dbm > 17) {
        // 高功率模式
        SX1276_WriteReg(0x4D, 0x87);          // RegPaDac = +20dBm模式
        SX1276_WriteReg(0x09, 0xFF);           // PA_BOOST, MaxPower, OutputPower=15
    } else {
        SX1276_WriteReg(0x4D, 0x84);           // RegPaDac = 默认
        uint8_t pa_config = 0x80;              // PA_BOOST
        pa_config |= (power_dbm - 2) & 0x0F;
        SX1276_WriteReg(0x09, pa_config);
    }
}
```

### 6.3 OCP过流保护

RegOcp(0x0B)设置过流保护阈值:

```
bit5: OcpOn -- 0=关闭, 1=开启
bit4-0: OcpTrim -- Imax = 45 + 5*OcpTrim (mA), 范围45~240mA
```

PA_BOOST +20dBm时需确保OcpTrim >= 27(Imax=180mA),否则功率会被限幅。

## 7. LNA配置

### 7.1 LNA增益设置

RegLna(0x0C)控制低噪声放大器:

```
bit7-5: LnaGain -- 000=最大增益(G1), 001=G2, ..., 111=最小增益(G6)
bit4-3: LnaBoostLf -- 00=默认, 11=LNA电流提升(提高灵敏度)
bit2-0: LnaBoostHf -- 同上,高频段
```

一般接收时设置LnaGain=G1(最大增益),LnaBoost=11:

```c
void SX1276_SetLnaRx(void) {
    SX1276_WriteReg(0x0C, 0x23);  // G1最大增益, LNA Boost LF开启
}
```

### 7.2 AGC自动增益

RegModemConfig3(0x26)的bit2可启用AGC,芯片自动调节LNA增益。弱信号环境下建议手动设最大增益;信号强弱变化大的场景可启用AGC。

## 8. 扩频参数寄存器配置

### 8.1 RegModemConfig1 (0x1D)

```
bit7-4: Bw -- 带宽
  0x0=7.8kHz, 0x1=10.4kHz, ..., 0x6=125kHz, 0x7=250kHz, 0x8=500kHz
bit3-1: CodingRate -- CR=4/(4+value), value=1~4
bit0:   ImplicitHeaderModeOn -- 0=显式头, 1=隐式头
```

常用配置:

| BW | Bw值 | CR | CodingRate值 | 组合寄存器值(显式头) |
|----|------|----|-------------|--------------------|
| 125kHz | 0x6 | 4/5 | 1 | 0x62 |
| 125kHz | 0x6 | 4/7 | 3 | 0x66 |
| 250kHz | 0x7 | 4/5 | 1 | 0x72 |
| 500kHz | 0x8 | 4/5 | 1 | 0x82 |

### 8.2 RegModemConfig2 (0x1E)

```
bit7-4: SpreadingFactor -- SF7=0x7, SF8=0x8, ..., SF12=0xC
bit3:   TxContinuousMode -- 0=单包, 1=连续发送(测试用)
bit2-0: SymbTimeout -- RX超时MSB(与0x1F组成10位超时值)
```

### 8.3 完整配置示例

```c
// 配置LoRa: SF10, BW125, CR4/5, 显式头
void SX1276_ConfigLoRa(void) {
    SX1276_SetMode(0x01);  // Standby

    // RegModemConfig1: BW125=0x6, CR4/5=1, 显式头=0
    SX1276_WriteReg(0x1D, 0x62);

    // RegModemConfig2: SF10=0xA, 单包模式, SymbTimeout MSB=0
    SX1276_WriteReg(0x1E, 0xA0);

    // RegModemConfig3: AGC Auto=0, LNA增益手动
    SX1276_WriteReg(0x26, 0x00);

    // RegSymbTimeoutLsb: 超时=0x64(100个符号)
    SX1276_WriteReg(0x1F, 0x64);

    // 前导码长度: 8个符号
    SX1276_WriteReg(0x20, 0x00);
    SX1276_WriteReg(0x21, 0x08);

    // 频率470MHz
    SX1276_SetFrequency(470000000);

    // 功率+14dBm
    SX1276_SetPower(14);

    // LNA最大增益
    SX1276_SetLnaRx();

    // 同步字(LoRaWAN: 0x34, 私有: 0x12)
    SX1276_WriteReg(0x39, 0x34);
}
```

## 9. 数据包格式与FIFO管理

### 9.1 显式头与隐式头

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| 显式头(Explicit) | 包头含长度、CR、CRC信息 | 变长数据包,通用 |
| 隐式头(Implicit) | 不含包头,接收端预知参数 | 固定长度,省时间 |

显式头占用约4个符号时间的开销。对于极短数据包,SF12下显式头的开销占比可达50%以上,此时隐式头更高效。

### 9.2 FIFO读写流程

发送流程:
1. 进入Standby模式
2. 设置RegFifoTxBaseAddr(0x0E)为FIFO起始地址
3. 设置RegFifoAddrPtr(0x0D)指向写入位置
4. 向RegFifo(0x00)逐字节写入数据
5. 设置RegPayloadLength(0x22)为数据长度
6. 进入TX模式,等待TxDone中断

接收流程:
1. 设置RegFifoRxBaseAddr(0x0F)
2. 进入RX模式
3. 等待RxDone中断
4. 读取RegRxNbBytes(0x13)获取接收字节数
5. 设置RegFifoAddrPtr = RegFifoRxCurrentAddr(0x10)
6. 从RegFifo(0x00)读取数据

```c
void SX1276_Send(uint8_t *data, uint8_t len) {
    SX1276_SetMode(0x01);  // Standby

    // 清FIFO
    SX1276_WriteReg(0x0E, 0x00);  // TxBaseAddr = 0
    SX1276_WriteReg(0x0D, 0x00);  // AddrPtr = 0

    // 写数据到FIFO
    for (uint8_t i = 0; i < len; i++) {
        SX1276_WriteReg(0x00, data[i]);  // RegFifo
    }

    // 设置长度
    SX1276_WriteReg(0x22, len);

    // 清中断标志
    SX1276_WriteReg(0x40, 0xFF);

    // 进入TX
    SX1276_SetMode(0x03);
}
```

## 10. DIO引脚映射与中断

### 10.1 DIO引脚配置

SX1276有6个DIO引脚(DIO0~DIO5),通过RegDioMapping1(0x40)和RegDioMapping2(0x41)映射到不同中断源:

**LoRa模式下DIO0~DIO5映射:**

| DIO | RegDioMapping1位 | 功能选项 |
|-----|-----------------|---------|
| DIO0 | bit7-6 | 00=RxDone, 01=TxDone, 10=CadDone |
| DIO1 | bit5-4 | 00=RxTimeout, 01=FhssChangeChannel, 10=CadDetected |
| DIO2 | bit3-2 | 00=FhssChangeChannel, 01=FhssChangeChannel |
| DIO3 | bit1-0 | 00=CadDone, 01=ValidHeader, 10=PayloadCrcError |
| DIO4 | RegDioMapping2 bit7-6 | -- |
| DIO5 | RegDioMapping2 bit5-4 | 00=ModeReady |

最常用的配置: DIO0=RxDone/TxDone, DIO1=RxTimeout。

### 10.2 中断标志寄存器

RegIrqFlags(0x12)包含所有中断标志:

```
bit7: RxDone       -- 接收完成
bit6: TxDone       -- 发送完成
bit5: CadDone      -- 信道活动检测完成
bit4: FhssChangeChannel -- 跳频
bit3: CadDetected  -- 检测到信号
bit2: ValidHeader  -- 检测到有效包头
bit1: CrcError     -- CRC校验失败
bit0: RxTimeout    -- 接收超时
```

中断处理流程:

```c
void SX1276_IRQHandler(void) {
    uint8_t flags = SX1276_ReadReg(0x12);

    if (flags & 0x40) {  // TxDone
        SX1276_SetMode(0x01);  // 回Standby
        tx_complete = 1;
    }

    if (flags & 0x80) {  // RxDone
        uint8_t len = SX1276_ReadReg(0x13);  // RxNbBytes
        uint8_t addr = SX1276_ReadReg(0x10); // RxCurrentAddr
        SX1276_WriteReg(0x0D, addr);          // FIFO指针
        for (uint8_t i = 0; i < len; i++) {
            rx_buf[i] = SX1276_ReadReg(0x00);
        }
        rx_len = len;
        rx_complete = 1;
    }

    if (flags & 0x01) {  // RxTimeout
        rx_timeout = 1;
    }

    // 清除所有标志
    SX1276_WriteReg(0x12, flags);
}
```

## 11. 速率与距离权衡表

### 11.1 常用配置组合

| SF | BW(kHz) | CR | 比特率(bps) | 灵敏度(dBm) | 空中时间(10B,ms) | 典型距离(km) |
|----|---------|----|-----------|-------------|-----------------|------------|
| 7  | 125     | 4/5| 5469      | -123        | 30              | 2~3        |
| 8  | 125     | 4/5| 3125      | -126        | 50              | 3~5        |
| 9  | 125     | 4/5| 1758      | -129        | 90              | 5~8        |
| 10 | 125     | 4/5| 977       | -132        | 165             | 8~12       |
| 11 | 125     | 4/5| 537       | -134.5      | 320             | 12~15      |
| 12 | 125     | 4/5| 293       | -137        | 620             | 15~20      |
| 7  | 500     | 4/5| 21875     | -117        | 10              | 0.5~1      |
| 10 | 250     | 4/5| 1953      | -129        | 80              | 5~10       |

### 11.2 选型建议

- 城市抄表:SF9/BW125,兼顾距离与实时性
- 农业监测:SF12/BW125,最远距离,数据量小
- 工厂车间:SF7/BW500,高速率,短距离
- LoRaWAN默认:SF10/BW125,欧洲标准配置

## 总结

SX1276的寄存器配置可归纳为四步:进Standby配参数、设频率和功率、填FIFO起收发、查中断读结果。核心参数SF/BW/CR三者的组合决定了速率-距离-抗干扰三角权衡。理解寄存器级配置的价值在于:当现成库函数不满足需求时(如非标频段、自定义同步字、优化空中时间),你能直接操作寄存器来精确控制射频行为。

关键要点:
- SF每增1级,灵敏度提升约2.5dB,速率减半
- PA_BOOST模式可达+20dBm,需配合RegPaDac和OCP
- FIFO必须先设地址指针再读写,不能漏
- 中断标志必须手动清除(写1清零)
- 频率计算注意32MHz基准和19位分数格式

## 参考文献

1. Semtech. SX1276/77/78/79 Datasheet Rev 6, 2017.
2. Semtech. SX1276 LoRa Modem Designer's Guide, AN1200.13, 2015.
3. LoRa Alliance. LoRaWAN Specification v1.0.4, 2020.
4. Reynders B, Pollin S. "Chirp Spread Spectrum as a Modulation Technique for Low Power Wide Area Networks," IEEE Commun. Surveys & Tutorials, 2019.
5. Augustin A, et al. "A Study of LoRa: Long Range & Low Power Networks for IoT," Sensors, 2016.
