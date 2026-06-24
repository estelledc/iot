# DAC在IoT音频输出与执行器控制中的应用

> **难度**：🟢 初级 | **领域**：数模转换应用 | **阅读时间**：约 18 分钟

## 引言

想象你在调音量旋钮。旋钮是连续转动的，可以停在任意位置，但手机里存的音乐只是一串数字(0和1)。DAC(数模转换器)就是那个"旋钮的替身" -- 把离散的数字变成连续的模拟电压，让扬声器震动、让灯光渐变、让阀门停在半开的位置。没有DAC，数字世界永远只能"开"或"关"，没法"开一点点"。

在IoT设备中，DAC的身影无处不在:门铃播放提示音、智能家居语音播报、工业阀门定位、电机速度给定、LED呼吸灯。本文从DAC基本原理出发，覆盖主流架构、MCU内置DAC、I2S音频DAC、DMA播放、PWM等效DAC、执行器控制和关键规格，帮你建立完整的选型与应用框架。

## 1. DAC基本原理

### 1.1 数字到模拟的转换过程

DAC的核心任务:将N位数字码字转换为对应的模拟电压(或电流)。

```
数字输入 (N bit)          模拟输出
  D[N-1] ... D[1] D[0]  ──>  Vout = Vref x (D / 2^N)

例: 8位DAC, Vref = 3.3V
  输入 0   -> Vout = 0.000 V
  输入 128 -> Vout = 1.650 V
  输入 255 -> Vout = 3.290 V
```

| 要素 | 说明 | 典型值 |
|------|------|--------|
| 分辨率 | 数字位宽，决定最小步进 | 8/10/12/16 bit |
| 参考电压 | 满量程对应的电压 | 3.3V / 5V / 2.5V |
| 输出范围 | 单极性或双极性 | 0~Vref / -Vref~+Vref |
| 更新速率 | 每秒可输出的样点数 | 1KSPS ~ 1MSPS |

### 1.2 量化台阶与LSB

LSB(Least Significant Bit)是DAC最小电压步进:

```
LSB = Vref / 2^N
8位:  3.3/256   = 12.89 mV
12位: 3.3/4096  = 0.806 mV
16位: 3.3/65536 = 0.0503 mV
```

分辨率越高台阶越细，但分辨率不等于精度 -- INL/DNL误差可能让实际输出偏离理想值。

## 2. DAC架构分类

### 2.1 三种主流架构

| 架构 | 原理 | 速度 | 精度 | 面积 | 典型应用 |
|------|------|------|------|------|----------|
| R-2R梯形 | 电阻网络分压 | 中 | 中高 | 中 | 通用MCU内置DAC |
| 电流舵 | 电流源并行切换 | 高 | 中 | 大 | 高速通信、视频 |
| PWM型 | 占空比+低通滤波 | 低 | 中 | 极小 | 低成本执行器、LED调光 |

### 2.2 R-2R梯形DAC

R-2R梯形网络只用两种阻值(R和2R)，不管多少位都一样，工艺一致性容易保证。

```
           2R    2R    2R    2R
    Vref ─┤├──┤├──┤├──┤├── GND
           │     │     │     │
          2R    2R    2R    2R
           │     │     │     │
          D3    D2    D1    D0   (开关接Vref或GND)
           └─────┴─────┴─────┴── Vout
```

第k位对输出的贡献恰好是Vref x 2^k / 2^N。优点:两种阻值匹配性好、位数扩展方便。缺点:电阻数量随位数线性增长、开关导通电阻影响精度。

### 2.3 电流舵DAC

电流舵DAC用并行电流源实现转换，每个电流源由数字位控制:

```
  I     2I     4I     8I    ...  2^(N-1) x I
 [S0]   [S1]   [S2]   [S3]  ...  [S(N-1)]
  └──────┴──────┴──────┴───── ... ┴── Iout -> Vout
```

优点:速度极快(电流源直接切换)、差分输出抑制共模噪声。缺点:电流源匹配要求高面积大、功耗较高、不适合低功耗IoT。

### 2.4 PWM型DAC

PWM配合RC低通滤波器等效DAC，是IoT中最常用的"穷人DAC"方案:

```
  PWM波形               RC低通后
  Vcc ┌┐  ┌┐  ┌┐      ┌──────────┐
      ││  ││  ││      │ 平滑直流  │
  0   └┘──┘┘──┘┘ ──> └──────────┘
       <-Ton->     Vout = Vcc x (Ton/T) = Vcc x DutyCycle
```

等效分辨率取决于PWM计数器位宽:8位PWM等效8位DAC，16位PWM等效16位DAC。优点:几乎零成本、驱动能力强。缺点:纹波大、带宽低、响应慢。

## 3. MCU内置DAC

### 3.1 STM32 DAC外设

| 参数 | STM32F4 DAC | 说明 |
|------|-------------|------|
| 分辨率 | 12 bit | 可配置8/12位 |
| 通道数 | 2 | 可独立或同步输出 |
| 参考电压 | VREF+ | 通常接3.3V |
| 更新速率 | 最高1 MSPS | 受APB1时钟限制 |
| 输出缓冲 | 可使能 | 增加驱动能力 |
| DMA支持 | 有 | 定时器触发自动更新 |

### 3.2 STM32 DAC基础配置

```c
// STM32 HAL: DAC通道1基础输出
DAC_HandleTypeDef hdac;

void DAC_Init(void) {
    DAC_ChannelConfTypeDef sConfig = {0};
    hdac.Instance = DAC;
    HAL_DAC_Init(&hdac);
    sConfig.DAC_Trigger = DAC_TRIGGER_NONE;
    sConfig.DAC_OutputBuffer = DAC_OUTPUTBUFFER_ENABLE;
    HAL_DAC_ConfigChannel(&hdac, &sConfig, DAC_CHANNEL_1);
}

void DAC_SetVoltage(uint16_t value) {
    if (value > 4095) value = 4095;
    HAL_DAC_SetValue(&hdac, DAC_CHANNEL_1, DAC_ALIGN_12B_R, value);
    HAL_DAC_Start(&hdac, DAC_CHANNEL_1);
}

// 辅助: 目标电压(mV) -> DAC码字
uint16_t VoltageToCode(uint32_t target_mV) {
    return (uint16_t)((target_mV * 4095UL) / 3300UL);
}
```

### 3.3 ESP32 DAC

ESP32提供两个8位DAC通道(GPIO25/26)，LSB约13mV，适合粗略控制(LED调光、偏置)，高精度场景需外接DAC芯片。

## 4. I2S音频DAC

### 4.1 为什么需要专用音频DAC

MCU内置DAC用于音频时短板明显:分辨率不够(12位=72dB SNR，CD需16位=96dB)、无去毛刺(产生click/pop噪声)、缺数字滤波。专用I2S音频DAC通过I2S接口接收PCM数据，内部高精度转换后直接输出模拟音频。

### 4.2 常用I2S DAC芯片对比

| 型号 | 分辨率 | SNR | 采样率 | 输出类型 | 价格 |
|------|--------|-----|--------|----------|------|
| PCM5102 | 32 bit | 112 dB | 384 kHz | 立体声线出 | 中 |
| MAX98357 | 16 bit | 92 dB | 96 kHz | 单声道D类功放 | 低 |
| ES8316 | 16 bit | 90 dB | 96 kHz | ADC+DAC codec | 低 |
| CS43L22 | 24 bit | 98 dB | 192 kHz | 立体声耳机 | 中 |

### 4.3 PCM5102与MAX98357

PCM5102A(TI): 32位DAC内核，112dB SNR，无需MCLK(仅BCLK+LRCK+DIN三线)，3.3V单电源，适合高品质音频。

```
MCU (I2S Master)        PCM5102A
  I2S_BCLK ────────────> BCLK
  I2S_LRCK ────────────> LRCK
  I2S_DOUT ────────────> DIN
                         LOUT ──> 左声道
                         ROUT ──> 右声道
```

MAX98357A: I2S输入直接驱动扬声器，内置3W D类功放，IoT最简音频方案。

```c
// ESP32 I2S驱动MAX98357
#include "driver/i2s.h"

void I2S_MAX98357_Init(void) {
    i2s_config_t cfg = {
        .mode = I2S_MODE_MASTER | I2S_MODE_TX,
        .sample_rate = 16000,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .tx_desc_auto_clear = true,
        .dma_buf_count = 8, .dma_buf_len = 256,
    };
    i2s_pin_config_t pin = {
        .bck_io_num = 26, .ws_io_num = 25,
        .data_out_num = 22, .data_in_num = -1,
    };
    i2s_driver_install(I2S_NUM_0, &cfg, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin);
}
```

## 5. DMA驱动的音频播放

### 5.1 为什么需要DMA

CPU逐样点写DAC则100%占用;DMA自动搬运数据，CPU只需配置一次即可解放。

### 5.2 STM32 DMA + DAC + Timer波形输出

利用"定时器触发DMA、DMA更新DAC"链路，零CPU占用输出任意波形:

```c
#define WAVE_POINTS 256
uint16_t sine_table[WAVE_POINTS];

void GenerateSineTable(void) {
    for (int i = 0; i < WAVE_POINTS; i++)
        sine_table[i] = 2048 + 2047 * sin(2.0*3.14159*i/WAVE_POINTS);
}

void StartWaveOutput(uint32_t freq_hz) {
    uint32_t timer_freq = freq_hz * WAVE_POINTS;
    TIM6_Config(timer_freq);
    HAL_DAC_Start_DMA(&hdac, DAC_CHANNEL_1,
        (uint32_t*)sine_table, WAVE_POINTS, DAC_ALIGN_12B_R);
}
```

数据流: `sine_table[] ──DMA──> DAC ──> 模拟输出`，Timer6触发DMA，循环回绕。

### 5.3 I2S DMA播放音频片段

```c
void PlayVoicePrompt(const int16_t *pcm, uint32_t count) {
    size_t written = 0;
    i2s_write(I2S_NUM_0, pcm, count*sizeof(int16_t),
              &written, portMAX_DELAY);
}
```

优化: 长音频用ADPCM压缩(4:1)实时解压; 多段提示音拼大表偏移索引; SPI Flash XIP省RAM。

## 6. PWM作为低成本DAC

### 6.1 RC滤波设计

截止频率在"滤除PWM载频"和"保留信号带宽"间折中: `fsignal < fc < fpwm/10`，其中 `fc = 1/(2*pi*R*C)`。

例: fpwm=10kHz, fsignal=100Hz, fc选339Hz -> R=4.7kOhm, C=100nF。

### 6.2 纹波与二阶滤波

单级RC纹波: `Vripple ≈ Vcc x (fc/fpwm)`。例: Vcc=3.3V, fc=339Hz, fpwm=10kHz -> 约0.11V。二阶RC: `Vripple ≈ Vcc x (fc/fpwm)^2` -> 约1.1mV，显著改善。

```c
// STM32: PWM + 二阶RC等效12位DAC
void PWM_DAC_Init(void) { /* PWM 84MHz/4096=20.5kHz, 等效12位 */ }
void PWM_DAC_SetValue(uint16_t val) {
    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, val);
}
```

## 7. DAC用于执行器控制

### 7.1 阀门位置控制

DAC给阀门定位器提供0~10V位置设定信号:

```c
void Valve_SetPosition(uint8_t percent) {
    DAC_SetVoltage((uint16_t)(percent * 4095UL / 100UL));
}
```

### 7.2 电机速度参考

变频器常用0~10V模拟输入作为速度给定:

```c
// 额定3000RPM对应DAC满量程
void Motor_SetSpeed(uint16_t rpm) {
    if (rpm > 3000) rpm = 3000;
    DAC_SetVoltage((uint16_t)(rpm * 4095UL / 3000UL));
}
```

注意: DAC输出驱动能力有限(几mA)，长线传输需加运放跟随器。

### 7.3 LED调光(模拟方式)

EMI敏感场景(医疗、精密测量)需模拟调光而非PWM调光:

| 特性 | 模拟调光(DAC) | PWM调光 |
|------|---------------|---------|
| EMI | 极低 | 高(方波谐波) |
| 效率 | 较低(线性损耗) | 高(开关损耗小) |
| 电路 | 需V-to-I电路 | 直接驱动 |
| 线性度 | 受晶体管非线性影响 | 天然线性 |

## 8. DAC关键规格参数

### 8.1 静态参数

| 参数 | 定义 | 典型IoT要求 |
|------|------|-------------|
| 分辨率 | 位数N | 8~12 bit |
| INL | 积分非线性:输出与理想直线最大偏差 | < 2 LSB |
| DNL | 微分非线性:相邻步进与1LSB偏差 | < 0.5 LSB(保单调) |
| 增益误差 | 实际满量程与理想值偏差 | < 1% |
| 偏移误差 | 输入0时输出不为0 | < 5 mV |

DNL > 1 LSB意味着丢码 -- 某数字输入不产生新步进，输出倒退，控制应用中可能导致振荡。

### 8.2 动态参数

| 参数 | 定义 | 典型IoT音频要求 |
|------|------|-----------------|
| 建立时间 | 输出跳变到稳定在+-1/2LSB内的时间 | < 10us |
| 毛刺能量 | 码字切换瞬间尖峰能量 | < 100 pV-s |
| 更新率 | 单位时间可刷新样点数 | > 2 x fsignal |
| SFDR | 无杂散动态范围 | > 60 dB |

### 8.3 毛刺抑制

DAC码字切换瞬间因开关时间不一致产生尖峰，音频中表现为"咔嗒"噪声。抑制方法:选低毛刺DAC(电流舵);外加采样保持;音频DAC内置去毛刺(PCM5102);软件避免大步进跳变。

## 9. DAC输出缓冲

### 9.1 为什么需要缓冲

MCU内置DAC无缓冲时输出阻抗约15kOhm，直接驱动负载电压跌落严重: `Vactual = Vdac x Rload/(Rdac+Rload)`，Rdac=15k, Rload=10k时Vactual仅为Vdac的40%。

### 9.2 运放跟随器

用运放接成电压跟随器(增益=1)，输出阻抗接近0:

```
              ┌──────────┐
DAC输出 ─────>│+        │
              │  Op-Amp ├──> 低阻抗输出
         ┌───>│-        │
         │    └──────────┘
         └────────────────┘
```

| 要求 | 推荐 | 说明 |
|------|------|------|
| 通用低成本 | LM358 | 双运放，单电源 |
| 精密低偏移 | OPA333 | 零漂移，<10uV偏移 |
| 轨到轨3.3V | MCP6001 | 单电源系统首选 |
| 高速音频 | OPA1662 | 低噪声，音频缓冲 |

### 9.3 单转双电源(双极性输出)

用运放差分放大配置: `Vout = (Vdac - Vref/2) x 2`，使Vdac=0时Vout=-Vref，Vdac=Vref/2时Vout=0。双向电机等执行器需要双极性给定。

## 10. 实际应用案例

### 10.1 IoT门铃音频播放

智能门铃按下后播放音效，MAX98357A+ESP32方案:

```
按键 ──> ESP32 ──I2S──> MAX98357A ──> 扬声器
           │
         Flash(PCM, 16kHz/16bit, ~64KB/2s)
```

```c
const int16_t doorbell_pcm[] = { /* PCM数据 */ };
void Doorbell_Play(void) {
    PlayVoicePrompt(doorbell_pcm, sizeof(doorbell_pcm)/2);
}
```

### 10.2 智能家居语音播报

温度超阈值时播报警告语音，片段拼接省存储:

```c
typedef struct { const int16_t *data; uint32_t length; } VoiceClip;

const VoiceClip voice_table[] = {
    { clip_temp_high, sizeof(clip_temp_high)/2 },
    { clip_humi_high, sizeof(clip_humi_high)/2 },
    { clip_close_win, sizeof(clip_close_win)/2 },
};

void PlayClip(uint8_t idx) {
    if (idx < sizeof(voice_table)/sizeof(VoiceClip))
        PlayVoicePrompt(voice_table[idx].data, voice_table[idx].length);
}
```

"温度"+"三十五"+"度"拼成完整播报，片段复用大幅省存储。

### 10.3 PID控制器DAC输出

温度PID控制，运算结果(0~100%)通过DAC驱动加热器:

```c
void PID_UpdateOutput(float pid_out) {
    if (pid_out < 0.0f) pid_out = 0.0f;
    if (pid_out > 100.0f) pid_out = 100.0f;
    DAC_SetVoltage((uint16_t)(pid_out * 40.95f));
}
```

控制链路: `传感器 ──ADC──> MCU ──PID──> DAC ──运放──> SSR ──> 加热器`，形成闭环。

## 总结

DAC是数字世界控制模拟世界的核心接口。IoT应用核心要点:

1. **选型决策**: 精度>=12位用MCU内置或外部DAC; 纯开关/调光用PWM; 音频用I2S专用DAC
2. **音频路径**: MCU I2S -> MAX98357(低成本) / PCM5102(高品质)，DMA搬运零CPU占用
3. **PWM等效DAC**: 加RC滤波，注意截止频率设计，二阶滤波大幅降纹波
4. **执行器控制**: DAC输出必须加运放缓冲，注意输出阻抗和驱动能力
5. **关键参数**: 分辨率决定步进细度，建立时间决定更新速率，DNL>1LSB会丢码

选型速查:

```
需要音频输出? ──是──> I2S DAC (MAX98357/PCM5102)
              └──否──> 精度>=12bit? ──是──> MCU内置DAC或外部SPI DAC
                                └──否──> PWM+RC (最低成本)
```

## 参考文献

1. Texas Instruments, "DAC Essentials: What You Need to Know About Digital-to-Analog Converters", SLAA567, 2013.
2. STMicroelectronics, "STM32F4 Reference Manual - DAC Chapter", RM0090 Rev.19, 2022.
3. Maxim Integrated, "MAX98357A Class D Speaker Amplifier with I2S Input", Datasheet Rev.2, 2020.
4. Kester W., "Data Conversion Handbook", Analog Devices, 2005. Chapter 3: DAC Architectures.
5. Cao Y. et al., "A Survey of DAC-Based Actuator Control in IoT Systems", IEEE IoT Journal, vol.11, 2024.
