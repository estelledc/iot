# ADC校准：失调误差与增益误差补偿

> **难度**：🟡 中级 | **领域**：ADC精度优化 | **阅读时间**：约 18 分钟

## 引言

想象你用一把尺子量东西。如果尺子的零刻度没对齐物体边缘，量出来的长度总是偏大或偏小一个固定值——这就是**失调误差**(Offset Error)。如果尺子本身被拉长或缩短了，量出来的结果会按比例偏大或偏小——这就是**增益误差**(Gain Error)。

ADC就像一把把模拟电压"量"成数字的尺子。校准的过程，就是找到偏移量和缩放比例，把读数修正回来。本文从误差来源出发，逐步讲解两点校准、多点拟合、自校准、温度补偿和端到端校准等工程实践。

## 1. ADC误差来源

### 1.1 四类主要误差

| 误差类型 | 英文 | 特征 | 影响 |
|----------|------|------|------|
| 失调误差 | Offset Error | 整体平移 | 所有码值偏移固定量 |
| 增益误差 | Gain Error | 斜率偏差 | 误差随输入线性增大 |
| 积分非线性 | INL | 传递曲线弯曲 | 中间区域偏差最大 |
| 微分非线性 | DNL | 码宽不均匀 | 某些码偏宽/偏窄 |

物理根因：失调源于比较器失调电压和开关电荷注入；增益源于基准电压精度和电阻匹配；INL/DNL源于电容失配和码宽不均匀。12位ADC在Vref=3.3V时1LSB约0.8mV，10LSB失调即8mV偏差——位数越高，校准收益越大。

## 2. 失调误差：定义与测量

失调误差是ADC传递函数在零输入时的输出码偏移：

```
D_ideal  = Vin / Vref * (2^N - 1)
D_actual = D_ideal + Offset_Code
```

**测量方法**：

- **短路输入法**：将ADC输入接地，采集N>=256个样本取均值即为失调码
- **零点交叉法**：用精密电压源缓慢扫过零点，记录输出跳变对应的电压偏差

单极性ADC中，正失调导致量程缩短(底部码丢失)，负失调导致零点附近出现死区。

## 3. 增益误差：定义与测量

增益误差是实际斜率与理想斜率的偏差。消除失调后，满量程输入时输出码与理想码之差即为增益误差：

```
Gain_Error_LSB = D_corrected(Vref) - (2^N - 1)
Gain_Error_percent = Gain_Error_LSB / (2^N - 1) * 100%
```

**测量方法**：输入0V和Vref，分别记录D0和Dfull，计算G_actual = (Dfull - D0) / (2^N - 1)，G_error = G_actual - 1.0。

主要来源是基准电压偏差——1%的Vref精度偏差直接导致约1%增益误差，在12位ADC上相当于41LSB。

## 4. 两点校准法

### 4.1 原理

用两个已知输入点建立线性修正模型：

```
D_calibrated = G * D_raw + B

G = (D_ideal_high - D_ideal_low) / (D_measured_high - D_measured_low)
B = D_ideal_low - G * D_measured_low
```

类比：给歪斜的尺子做"零点校准"加"刻度缩放"——先对齐零点，再按比例修正刻度。

### 4.2 校准点选择

| 方案 | 优点 | 缺点 |
|------|------|------|
| 0V + Vref | 覆盖全量程 | 需两个精密电压源 |
| Vref*25% + Vref*75% | 避开端部非线性 | 两端精度稍差 |

12位及以下ADC选0V+Vref即可；16位以上建议考虑多点校准。

### 4.3 C语言实现

```c
#include <stdint.h>

typedef struct {
    float gain;
    float offset;
} adc_calib_t;

void adc_calib_two_point(adc_calib_t *cal,
                         int32_t d_low, int32_t d_high,
                         int32_t ideal_low, int32_t ideal_high)
{
    int32_t delta = d_high - d_low;
    if (delta == 0) { cal->gain = 1.0f; cal->offset = 0.0f; return; }
    cal->gain   = (float)(ideal_high - ideal_low) / delta;
    cal->offset = (float)ideal_low - cal->gain * d_low;
}

int32_t adc_calib_apply(const adc_calib_t *cal, int32_t raw)
{
    float result = cal->gain * raw + cal->offset;
    if (result < 0) return 0;
    if (result > 4095) return 4095;     // 12位ADC
    return (int32_t)(result + 0.5f);    // 四舍五入
}

// 使用: 实测0V->码15, Vref->码4070; 理想0V->0, Vref->4095
// adc_calib_two_point(&cal, 15, 4070, 0, 4095);
```

## 5. 多点校准与多项式拟合

两点校准只能消除线性误差。当INL较大时，需多点校准弥补非线性弯曲。

### 5.1 分段线性插值

将量程分成若干段，每段独立线性修正。简单稳定，是最常用的多点方法。

### 5.2 多项式拟合

```
D_calibrated = a0 + a1*D_raw + a2*D_raw^2 + ... + an*D_raw^n
```

通常n=2或3即可满足12-16位ADC精度。注意：阶数不宜超过3，否则过拟合；高阶多项式在边界可能振荡(Runge现象)；分段线性插值比高阶多项式更稳定。

```c
typedef struct { float a0, a1, a2; } adc_calib_poly_t;

int32_t adc_calib_apply_poly(const adc_calib_poly_t *cal, int32_t raw)
{
    float r = (float)raw;
    float result = cal->a0 + cal->a1 * r + cal->a2 * r * r;
    if (result < 0) return 0;
    if (result > 4095) return 4095;
    return (int32_t)(result + 0.5f);
}
```

## 6. 自校准：内部参考短路

许多MCU内置ADC自校准：内部将输入短接到VSSA测失调、接VREFINT测增益，自动写入校准因子。

```
流程: ADC断开外部输入 -> 接VSSA测失调 -> 接VREFINT测增益
    -> 写入校准寄存器 -> 后续转换自动应用
```

**优势**：无需外部精密源，上电即执行，自动补偿芯片间差异。
**局限**：只校准ADC本身，不含外部信号链；内部参考精度有限(典型1-3%)。

自校准是第一步，不能替代系统级端到端校准。

## 7. 工厂校准与现场校准

| 维度 | 工厂校准 | 现场校准 |
|------|----------|----------|
| 精度 | 高(受限于测试设备) | 中(受限于现场条件) |
| 成本 | 高(产线设备+时间) | 低(软件实现) |
| 补偿范围 | 出厂时误差 | 长期漂移+温漂 |
| 存储 | OTP/Flash | EEPROM/Flash |
| 频率 | 一次 | 周期性 |

工厂校准在产线施加精密电压、计算系数、写入非易失性存储器；现场校准利用板载基准源或已知物理量(如0度冰水混合物)更新参数。

## 8. 校准数据存储

| 介质 | 写入次数 | 掉电保持 | 适用场景 |
|------|----------|----------|----------|
| OTP | 1次 | 永久 | 工厂校准，不可更改 |
| EEPROM | 10万-100万次 | 10-100年 | 现场校准，频繁更新 |
| Flash | 1万-10万次 | 20-100年 | 兼顾容量和耐久性 |
| FRAM | 10^14次以上 | 10-100年 | 高频更新，成本较高 |

数据组织建议：

```c
typedef struct {
    uint32_t magic;        // 魔数, 验证有效性
    int32_t  offset_code;  // 失调校准码
    float    gain;         // 增益系数
    float    temp_ref;     // 校准时温度
    uint32_t crc32;        // CRC32校验
} adc_calib_data_t;
```

完整性保护：CRC32校验(上电验证) + 双份冗余存储 + 默认值回退。

## 9. 温度相关校准

### 9.1 温漂来源

- 失调温漂：比较器失调电压温度系数，典型1-50uV/C
- 增益温漂：基准电压温度系数，典型10-100ppm/C

### 9.2 补偿策略

**策略一**：单温度点校准 + 数据手册温漂系数做软件修正。

**策略二**：多温度点校准，运行时按当前温度插值：

```c
typedef struct {
    float temp;
    adc_calib_t calib;
} temp_calib_entry_t;

#define TEMP_CALIB_POINTS 5
temp_calib_entry_t temp_table[TEMP_CALIB_POINTS] = {
    { -20.0f, {0.9985f, -12.3f} },
    {   0.0f, {0.9992f,  -5.1f} },
    {  25.0f, {1.0000f,   0.0f} },
    {  50.0f, {1.0011f,   6.8f} },
    {  85.0f, {1.0028f,  15.4f} },
};

adc_calib_t get_calib_at_temp(float temp)
{
    int i;
    for (i = 0; i < TEMP_CALIB_POINTS - 1; i++)
        if (temp <= temp_table[i+1].temp) break;
    if (i >= TEMP_CALIB_POINTS - 1) i = TEMP_CALIB_POINTS - 2;
    float t0 = temp_table[i].temp, t1 = temp_table[i+1].temp;
    float r = (temp - t0) / (t1 - t0);
    adc_calib_t res;
    res.gain   = temp_table[i].calib.gain
               + r * (temp_table[i+1].calib.gain - temp_table[i].calib.gain);
    res.offset = temp_table[i].calib.offset
               + r * (temp_table[i+1].calib.offset - temp_table[i].calib.offset);
    return res;
}
```

注意：精密应用需外接温度传感器紧贴ADC芯片；MCU内部温度传感器仅适合粗略补偿；需关注自热效应。

## 10. STM32 ADC校准寄存器

### 10.1 关键寄存器

| 寄存器 | 功能 | 说明 |
|--------|------|------|
| ADC_CR.ADCAL | 启动校准 | 写1启动，硬件自动清零 |
| ADC_CR.ADDIS | 禁用ADC | 校准前需先禁用 |
| ADC_CALFACT | 校准因子 | 校准完成后硬件自动写入 |

### 10.2 HAL库校准流程

```c
void stm32_adc_calibrate(ADC_HandleTypeDef *hadc)
{
    HAL_ADC_DeInit(hadc);
    HAL_ADC_Init(hadc);
    // 单端输入校准
    HAL_ADCEx_Calibration_Start(hadc, ADC_SINGLE_ENDED);
    HAL_ADC_PollForCalibrationEvent(hadc, HAL_MAX_DELAY);
    // 可选: 读取校准因子调试
    uint32_t factor = HAL_ADCEx_Calibration_GetValue(
                          hadc, ADC_SINGLE_ENDED);
}
```

注意事项：校准前ADC必须禁用(ADCAL=1时ADEN=0)；校准期间不能启动转换；每次上电需重新校准(掉电丢失)。

## 11. 系统级端到端校准

ADC校准只补偿了芯片内部误差。信号从传感器到ADC经过完整链路：

```
传感器 -> 运放 -> 滤波器 -> 多路复用器 -> ADC
```

每个环节都引入误差。端到端校准在传感器输入端施加已知物理量，直接建立物理量到ADC码的映射：

```c
// 压力传感器端到端校准
typedef struct {
    float pressure_zero, pressure_full;  // 已知压力值(kPa)
    int32_t code_zero, code_full;        // 对应ADC码
} sys_calib_t;

float pressure_from_adc(const sys_calib_t *cal, int32_t raw)
{
    if (cal->code_full == cal->code_zero) return 0.0f;
    float ratio = (float)(raw - cal->code_zero)
                / (cal->code_full - cal->code_zero);
    return cal->pressure_zero
         + ratio * (cal->pressure_full - cal->pressure_zero);
}
```

优势：补偿全部信号链误差，软件无需分别处理各环节。注意：校准条件应接近实际使用条件，多通道需每通道单独校准。

## 12. 校准间隔建议

### 12.1 推荐间隔

| 应用场景 | 精度要求 | 推荐间隔 |
|----------|----------|----------|
| 消费电子 | 5-10% | 出厂一次 |
| 工业监控 | 1-5% | 每年或每次维护 |
| 精密测量 | 0.1-1% | 每月或每次开机 |
| 计量仪表 | <0.1% | 每次测量前 |

### 12.2 自适应重新校准

```c
typedef struct {
    uint32_t last_tick;       // 上次校准tick
    uint32_t interval_ms;     // 时间间隔
    float    last_temp;       // 上次温度
    float    temp_threshold;  // 温度变化阈值
} calib_scheduler_t;

int should_recalibrate(calib_scheduler_t *s,
                       uint32_t tick, float temp)
{
    if ((tick - s->last_tick) >= s->interval_ms) return 1;
    float delta = temp - s->last_temp;
    if (delta < 0) delta = -delta;
    if (delta > s->temp_threshold) return 1;
    return 0;
}
```

在线校准(利用冗余通道/采样间隙)适合7x24系统；离线校准(进入维护模式)适合可中断应用。

## 总结

1. **两类线性误差**：失调(平移)和增益(缩放)，两点校准可完全消除
2. **非线性误差(INL/DNL)**：需多点校准或多项式拟合，多数应用残余INL可接受
3. **自校准**：MCU内部功能，补偿ADC自身误差，方便但不能替代系统级校准
4. **端到端校准**：覆盖传感器到ADC完整链路，追求精度的最终方案
5. **温度补偿**：高精度应用必须考虑温漂，多温度点+插值是实用策略
6. **数据存储**：OTP存工厂参数，EEPROM/Flash存现场更新，务必CRC保护
7. **校准间隔**：取决于精度和环境变化，关键系统应实施自适应重新校准

校准的本质是**用已知的参照修正未知的偏差**——参照点的数量、精度和更新频率，决定了精度与成本的平衡。

## 参考文献

1. Kester W. Data Conversion Handbook. Analog Devices, 2005. Chapter 2: ADC Error Analysis.
2. STM32F4 Reference Manual RM0090. STMicroelectronics, 2023. Section 13: ADC.
3. Texas Instruments. Understanding ADC Error Sources and Calibration. Application Note SLAA013, 2019.
4. Maxim Integrated. ADC Calibration Techniques for Precision Measurements. Application Note 5693, 2018.
5. Jespers JG. Integrated Converters: D to A and A to D Architectures. Springer, 2001. Chapter 4: Error Correction and Calibration.
