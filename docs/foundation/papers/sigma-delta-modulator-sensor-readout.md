---
schema_version: '1.0'
id: sigma-delta-modulator-sensor-readout
title: Sigma-Delta调制器在高精度传感器读出中的应用
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
# Sigma-Delta调制器在高精度传感器读出中的应用
> **难度**：🔴 高级 | **领域**：精密数据转换 | **阅读时间**：约 22 分钟

## 引言

用一把只有厘米刻度的尺子量头发丝的直径,显然不行。Sigma-Delta ADC就像一把"电子千分尺",它不靠精密的刻度,而是靠反复比较和统计,用时间换精度。它每秒做几百万次粗略比较,然后通过数字滤波把精度提炼出来。这种"笨功夫换高精度"的思路,正好适合传感器信号:变化慢,但需要极高分辨率。

## 1 Sigma-Delta ADC基本原理

### 1.1 三大支柱

Sigma-Delta ADC的精度来自三个机制协同:

```
输入信号 --> [过采样] --> [噪声整形] --> [数字抽取滤波] --> 高精度输出
              扩散噪声    推走噪声       提取信号频带
```

1. **过采样**: 以远高于奈奎斯特的速率采样,将量化噪声分散到更宽频带
2. **噪声整形**: 反馈环路将量化噪声推向高频,信号频带内噪声大幅降低
3. **数字抽取滤波**: 低通滤波滤除高频噪声,降采样到目标数据率

### 1.2 与SAR ADC对比

| 特性 | SAR ADC | Sigma-Delta ADC |
|------|---------|----------------|
| 分辨率 | 8-18 bit | 16-32 bit |
| 采样率 | 高(MSPS级) | 低(Hz到kSPS级) |
| 精度元件需求 | 需要精密电容匹配 | 不需要(1位量化器) |
| 抗混叠 | 需要陡峭模拟滤波器 | 自带(过采样+数字滤波) |
| 延迟 | 低(1个转换周期) | 高(滤波器建立时间) |
| 典型应用 | 音频,高速采集 | 传感器,称重,温度 |

## 2 过采样

### 2.1 奈奎斯特与过采样

```
奈奎斯特采样: fs = 2 * fsignal
  量化噪声均匀分布在 [0, fs/2]

过采样: fs = OSR * 2 * fsignal  (OSR = 过采样率)
  量化噪声分布在 [0, fs/2], 频带更宽
  信号频带 [0, fsignal] 内的噪声降低
```

### 2.2 过采样增益

每过采样4倍(2倍OSR),等效增加1位分辨率:

| OSR | 理论ENOB提升 | SNR提升(dB) |
|-----|-------------|------------|
| 1 | 0 | 0 |
| 4 | 1 bit | 6 |
| 16 | 2 bit | 12 |
| 64 | 3 bit | 18 |
| 256 | 4 bit | 24 |

单独过采样提升太慢,需要噪声整形配合。

## 3 噪声整形

### 3.1 一阶Sigma-Delta调制器

```
一阶Sigma-Delta调制器框图:

  X(z) -->(+)-->[积分器]-->[1位量化器]--> Y(z) (1位输出)
           ^                         |
           |        -1               |
           +<------[D(z)]<----------+
              (反馈: 延迟一拍)
```

### 3.2 噪声传递函数

对一阶调制器进行z域分析:

```
Y(z) = STF(z) * X(z) + NTF(z) * E(z)

STF(z) = 1            (信号直接传递)
NTF(z) = (1 - z^-1)   (噪声被一阶差分整形)

|NTF(f)|^2 = 4 * sin^2(pi*f/fs)
  低频: 噪声被极大抑制
  高频: 噪声被推向高频
```

### 3.3 不同阶数的噪声整形

| 阶数 | NTF | 信号频带噪声衰减 | 理论SNR(OSR=64) |
|------|-----|-----------------|----------------|
| 0(纯过采样) | 1 | 无衰减 | 72 dB |
| 1阶 | (1-z^-1) | 20dB/dec下降 | ~96 dB |
| 2阶 | (1-z^-1)^2 | 40dB/dec下降 | ~120 dB |
| 3阶 | (1-z^-1)^3 | 60dB/dec下降 | ~144 dB |

### 3.4 MASH结构

3阶以上单环调制器存在稳定性问题,MASH通过级联解决:

```
2-1 MASH (3阶等效):
  第1级: 2阶 -> 输出Y1, 量化误差E1
  第2级: 1阶, 输入E1 -> 输出Y2
  数字组合: Y = Y1*H1(z) - Y2*H2(z)
  每级低阶保证稳定,整体3阶噪声整形
```

## 4 数字抽取滤波器

### 4.1 功能

1位高速数据流变为多位低速高精度数据:

```
[1位高速流, 几MHz] --> [CIC滤波器] --> [FIR滤波器] --> [24位低速数据]
                       (梳状,降采样)   (修正幅度响应)
```

### 4.2 CIC滤波器

```
CIC = 积分器(高速时钟) + 降采样(R倍) + 梳状(低速时钟)

优点: 不需要乘法器(只有加法和延迟)
缺点: 通带衰减(低频也有一定下降)
阶数: 通常等于调制器阶数+1
```

### 4.3 sinc滤波器

许多集成ADC使用sinc3或sinc4滤波器:

```
sinc3: H(z) = [(1 - z^-N) / (1 - z^-1)]^3
建立时间: 3个数据周期(sinc3), 4个(sinc4)

sinc滤波器在50/60Hz处提供陷波:
  f_data = 50SPS -> 50Hz陷波(工频抑制)
  f_data = 10SPS -> 10,20,30,40,50,60Hz都有陷波
```

## 5 关键规格

| 参数 | 含义 | 典型值 |
|------|------|--------|
| 标称分辨率 | ADC位数 | 24-32 bit |
| 有效分辨率(ENOB) | 实际可用位数 | 16-24 bit |
| 峰峰值分辨率 | 无闪烁位数 | ENOB - 2.7 bit |
| 无噪声分辨率 | rms噪声对应位数 | ENOB - 0.5 bit |

数据率与分辨率权衡: 数据率每降低2倍,有效分辨率增加约0.5bit。

## 6 传感器应用

### 6.1 热电偶

```
K型热电偶: 41uV/度C
  测量0.1度C -> 需分辨4.1uV
  24位ADC, Vref=2.048V -> LSB=0.12uV, 足够
```

### 6.2 称重传感器

```
灵敏度 2mV/V, 激励5V -> 满量程10mV
  需1/10000分辨率 -> 分辨1uV
  24位ADC + PGA(GAIN=128) -> 轻松实现
```

### 6.3 RTD温度测量

```
PT100: 0.385 ohm/度C, 1mA激励
  0度C: 100mV, 100度C: 138.5mV
  0.1度C = 38.5uV变化, 24位ADC可分辨
```

### 6.4 pH电极

pH电极输出约59mV/pH单位,需高输入阻抗(>10^12 ohm) + 24位ADC。

## 7 常用Sigma-Delta ADC芯片

| 型号 | 分辨率 | 最高速率 | PGA | 特点 |
|------|--------|---------|-----|------|
| ADS1220 | 24bit | 2kSPS | 1-128x | 低功耗,内置激励电流源 |
| ADS1256 | 24bit | 30kSPS | 1-64x | 极低噪声(19nVrms@60SPS) |
| AD7124 | 24bit | 9.6kSPS | 1-128x | 内置诊断,符合IEC61298 |

## 8 实例: 称重传感器读出

### 8.1 硬件连接

```
        +Vexc (5V)
          |
    [R1]--[R2]      惠斯通电桥
     |      |        (Load Cell)
    [R3]--[R4]
          |
         GND

  AIN0 ---- R1/R2中点 (信号+)
  AIN1 ---- R2/R4中点 (信号-)
  ADS1220 内部PGA=128, 参考Vref=2.048V
```

### 8.2 配置代码

```python
# ADS1220 称重读出配置(伪代码)
class LoadCellReadout:
    def __init__(self, spi):
        self.adc = ADS1220(spi)

    def configure(self):
        self.adc.write_register(0x00,
            mux=0x00,     # AIN0-AIN1差分
            gain=0x05,    # PGA=128
            pga_bypass=0  # 启用PGA
        )
        self.adc.write_register(0x01,
            data_rate=0x02,  # 20SPS(50Hz陷波)
            mode=0x00,       # 正常模式
            ref_sel=0x00     # 内部2.048V参考
        )

    def read_weight(self):
        raw = self.adc.read_data()  # 24位有符号
        voltage_uV = raw * 8e6 / (2**23)
        weight_frac = voltage_uV / 10000
        return weight_frac * self.full_capacity
```

### 8.3 有效分辨率

```
ADS1220, PGA=128, 20SPS:
  输入噪声: 0.23uV rms -> 峰峰值1.5uV (6.6sigma)
  满量程: +/- 8mV = 16mV
  峰峰值分辨率 = log2(16mV/1.5uV) = 13.4位
  100kg量程 -> 分辨率9.4g
```

## 9 配置注意事项

### 9.1 数据率选择

| 场景 | 推荐数据率 | 理由 |
|------|-----------|------|
| 静态称重 | 5-20 SPS | 高分辨率,50/60Hz抑制 |
| 过程监测 | 20-100 SPS | 平衡速度和精度 |
| 快速采集 | 200-2000 SPS | 牺牲分辨率换速度 |

### 9.2 输入阻抗

低数据率时输入阻抗高(几十M ohm级),高数据率时降低(几百k ohm级)。高源阻抗传感器需加输入缓冲器。

### 9.3 参考电压

- 内部参考: 方便但精度有限(约0.1%)
- 外部精密参考: 如REF5025(0.05%)
- 比例测量: 同一参考驱动激励和ADC,消除参考误差

## 10 常见问题

### 10.1 通道切换建立时间

多路复用时,切换通道后必须等待滤波器重新建立:

```
sinc3: 等待3个数据周期
错误做法: 切换后立即读数 -> 混合新旧通道
正确做法: 丢弃前N-1个数据 -> 读第N个
```

### 10.2 布局要点

```
1. 模拟输入走线对称(差分对)
2. 参考电容紧贴ADC引脚
3. 数字和模拟地单点连接
4. 远离开关电源(噪声耦合)
5. 输入保护: 限流电阻 + 钳位二极管
```

## 总结

Sigma-Delta ADC通过过采样、噪声整形和数字滤波三个机制,用速度换精度,是高精度传感器读出的首选方案。其24位以上分辨率非常适合热电偶、称重传感器、RTD等微弱信号测量。设计时需特别注意数据率与分辨率的权衡、数字滤波器的建立时间、工频抑制数据率的选择,以及参考电压的稳定性。理解噪声传递函数和sinc滤波器特性,是正确使用Sigma-Delta ADC的关键。

## 参考文献

1. Texas Instruments, "ADS1220 24-Bit 2-kSPS Low-Power ADC Datasheet", 2023
2. Analog Devices, "AD7124 24-Bit Low Power Sigma-Delta ADC Datasheet", 2022
3. Norsworthy SR, Schreier R, Temes GC, "Delta-Sigma Data Converters: Theory, Design, and Simulation", IEEE Press, 1997
4. Kester W, "Which ADC Architecture Is Right for Your Application?", Analog Dialogue, 2005
5. Texas Instruments, "Precision ADC Noise Analysis Application Note", SLAA635, 2018