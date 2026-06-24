# ADC+DMA连续采样实时数据采集系统设计
> **难度**：🟡 中级 | **领域**：数据采集系统 | **阅读时间**：约 20 分钟

## 引言

想象一条流水线：原料(模拟信号)进入机器(ADC)变成半成品(数字采样值)，传送带(DMA)自动把半成品送到仓库(内存缓冲区)，质检员(CPU)定期取出一批成品检测。整条流水线自动运转，质检员只需在每批到货时工作。这就是ADC+DMA连续采样的核心：硬件自动完成"转换+搬运"，CPU只在处理阶段介入，既保证采样率精度，又最大化CPU利用率。

## 1. ADC基础回顾

### 1.1 ADC核心参数

| 参数 | 含义 | 典型值 |
|------|------|--------|
| 分辨率 | 数字输出位数 | 12位(STM32)/16位(专用) |
| 采样率 | 每秒转换次数 | 1kSPS - 1MSPS |
| 参考电压 | 满量程电压 | 3.3V(VDDA) |
| 精度(ENOB) | 实际有效位数 | 比分辨率少1-2位 |

12位ADC的量化阶梯：LSB = 3.3V / 4096 = 0.806mV

### 1.2 采样率与带宽

奈奎斯特定理要求采样率 > 2倍信号最高频率。工程上通常取5-10倍：f_sample >= 10 * f_signal_max

## 2. 为什么需要连续采样

### 2.1 单次转换的局限

```c
HAL_ADC_Start(&hadc1);
HAL_ADC_PollForConversion(&hadc1, 100);
uint32_t value = HAL_ADC_GetValue(&hadc1);
```

问题：每次转换有软件开销；采样间隔不均匀；高采样率时CPU被完全占用；无法持续波形采集。

### 2.2 连续采样的需求场景

| 应用 | 采样率 | 通道数 | 特点 |
|------|--------|--------|------|
| 振动监测 | 1-10kSPS | 3轴 | 持续频谱分析 |
| 音频采集 | 8-48kSPS | 1-2 | 实时流式传输 |
| 电能质量 | 10-100kSPS | 3相 | 同步谐波计算 |
| 心电信号 | 250-500SPS | 1-12 | 低速持续不间断 |

## 3. DMA基础

### 3.1 DMA是什么

DMA(Direct Memory Access)在无CPU介入下直接在内存和外设间传输数据。

```
传统: ADC --> CPU读 --> CPU写 --> 内存 (耗时, 需CPU)
DMA:  ADC --> DMA控制器 --> 内存       (CPU空闲!)
```

### 3.2 DMA关键参数

| 参数 | 说明 |
|------|------|
| 源地址 | 外设数据寄存器(如ADC1->DR) |
| 目的地址 | 内存缓冲区首地址 |
| 传输宽度 | 每次传输位宽(8/16/32位) |
| 模式 | Normal(单次) / Circular(循环) |

**Circular模式**：传输到缓冲区末尾后自动回到开头继续，是实现连续采样的关键。

## 4. ADC+DMA架构

### 4.1 基本架构

```
模拟信号 --> ADC(连续转换) --> DMA(Circular) --> RAM环形缓冲区
                                                         |
                                                    CPU处理(半满/全满时)
```

流程：ADC不停转换 -> 每次完成DMA自动搬运 -> 缓冲区满后绕回 -> 半传输/全传输中断通知CPU

### 4.2 STM32配置步骤

```c
// 1. ADC连续转换
hadc1.Init.ContinuousConvMode = ENABLE;
hadc1.Init.DMAContinuousRequests = ENABLE;
HAL_ADC_Init(&hadc1);

// 2. DMA Circular模式
hdma_adc1.Init.Mode = DMA_CIRCULAR;
HAL_DMA_Init(&hdma_adc1);

// 3. 关联并启动
__HAL_LINKDMA(&hadc1, DMA_Handle, hdma_adc1);
HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_buffer, BUFFER_SIZE);
```

## 5. 双缓冲技术

### 5.1 为什么需要双缓冲

Circular模式下DMA持续写入，如果CPU正在处理前半部分而DMA绕回到前半部分写入，就会覆盖数据 -- 数据损坏！

双缓冲(Ping-Pong)利用半传输和全传输中断避免这个问题。

### 5.2 工作原理

```
DMA写入:  [====前半====][====后半====][====前半====]...
                |              |              |
           半传输中断    全传输中断    半传输中断
CPU处理:     处理前半     处理后半     处理前半
           (后半正在被写) (前半正在被写)
```

CPU始终处理"刚写完"的那半，DMA正在写另半，互不干扰。

### 5.3 代码实现

```c
#define BUF_SIZE  200
#define HALF_BUF  (BUF_SIZE / 2)

uint16_t adc_buffer[BUF_SIZE];
volatile uint8_t data_ready = 0;
volatile uint16_t *data_ptr = NULL;

void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef *hadc) {
    data_ready = 1;
    data_ptr = &adc_buffer[0];       // 前半就绪
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc) {
    data_ready = 1;
    data_ptr = &adc_buffer[HALF_BUF]; // 后半就绪
}

while (1) {
    if (data_ready) {
        data_ready = 0;
        process_samples((uint16_t*)data_ptr, HALF_BUF);
    }
}
```

### 5.4 缓冲区大小选择

缓冲区至少能容纳CPU最长处理时间内的采样数据：BUFFER_MIN = f_sample * t_process_max

## 6. 定时器触发ADC

### 6.1 为什么要用定时器触发

ADC连续模式的采样率不够精确。定时器触发可实现精确稳定采样率、多通道严格时间间隔、与其他定时事件同步。

### 6.2 配置方法

```
定时器(TIM) --> TRGO --> ADC外部触发 --> 转换 --> DMA搬运
```

```c
// 定时器1kHz采样率
htim3.Init.Prescaler = 99;       // 84MHz/100 = 840kHz
htim3.Init.Period    = 839;      // 840kHz/840 = 1kHz
HAL_TIM_Base_Init(&htim3);

TIM_MasterConfigTypeDef sMasterConfig = {0};
sMasterConfig.MasterOutputTrigger = TIM_TRGO_UPDATE;
HAL_TIMEx_MasterConfigSynchronization(&htim3, &sMasterConfig);

// ADC定时器触发(非连续)
hadc1.Init.ContinuousConvMode = DISABLE;
hadc1.Init.ExternalTrigConv   = ADC_EXTERNALTRIGCONV_T3_TRGO;
hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_RISING;
```

### 6.3 采样率精度对比

| 触发方式 | 精度 | 适用场景 |
|----------|------|----------|
| ADC连续模式 | +-5% | 低精度要求 |
| 定时器触发 | +-0.01% | 信号分析、频谱计算 |
| 软件触发 | 不确定 | 单次采样 |

## 7. 多通道扫描

### 7.1 扫描模式原理

扫描模式让ADC按顺序转换多个通道，DMA依次存入缓冲区。

```
通道序列: CH0 -> CH3 -> CH7 -> CH2
DMA缓冲: [CH0, CH3, CH7, CH2, CH0, CH3, ...]
```

### 7.2 配置示例

```c
ADC_ChannelConfTypeDef sConfig = {0};
sConfig.SamplingTime = ADC_SAMPLETIME_84CYCLES;

sConfig.Channel = ADC_CHANNEL_0; sConfig.Rank = 1;
HAL_ADC_ConfigChannel(&hadc1, &sConfig);
sConfig.Channel = ADC_CHANNEL_3; sConfig.Rank = 2;
HAL_ADC_ConfigChannel(&hadc1, &sConfig);
sConfig.Channel = ADC_CHANNEL_7; sConfig.Rank = 3;
HAL_ADC_ConfigChannel(&hadc1, &sConfig);
sConfig.Channel = ADC_CHANNEL_2; sConfig.Rank = 4;
HAL_ADC_ConfigChannel(&hadc1, &sConfig);
```

### 7.3 数据解交织

```c
#define NUM_CH  4
void deinterleave(uint16_t *buf, uint16_t len) {
    uint16_t n = len / NUM_CH;
    for (uint16_t i = 0; i < n; i++) {
        ch0_data[i] = buf[i * NUM_CH + 0];
        ch3_data[i] = buf[i * NUM_CH + 1];
        ch7_data[i] = buf[i * NUM_CH + 2];
        ch2_data[i] = buf[i * NUM_CH + 3];
    }
}
```

## 8. 完整系统示例

4通道传感器采样：每通道1kSPS，定时器触发，DMA Circular双缓冲，主循环滤波传输。

```c
#define NUM_CH    4
#define SMP_PER_CH 100
#define BUF_SIZE  (NUM_CH * SMP_PER_CH)
#define HALF_BUF (BUF_SIZE / 2)

uint16_t adc_buf[BUF_SIZE];
volatile uint8_t half_ready = 0;

void sampling_init(void) {
    __HAL_RCC_ADC1_CLK_ENABLE();
    __HAL_RCC_DMA2_CLK_ENABLE();
    __HAL_RCC_TIM3_CLK_ENABLE();

    // 定时器4kHz(1kHz*4通道)
    htim3.Init.Prescaler = 20; htim3.Init.Period = 999;
    HAL_TIM_Base_Init(&htim3);

    // ADC: 定时器触发, 4通道扫描
    hadc1.Init.ScanConvMode = ENABLE;
    hadc1.Init.NbrOfConversion = NUM_CH;
    hadc1.Init.ExternalTrigConv = ADC_EXTERNALTRIGCONV_T3_TRGO;
    HAL_ADC_Init(&hadc1);

    // DMA Circular
    hdma.Init.Mode = DMA_CIRCULAR;
    HAL_DMA_Init(&hdma);

    HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_buf, BUF_SIZE);
    HAL_TIM_Base_Start(&htim3);
}

void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef *h) { half_ready = 1; }
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *h) { half_ready = 2; }

void main_loop(void) {
    while (1) {
        if (half_ready == 1) { half_ready = 0; process_half(&adc_buf[0], HALF_BUF); }
        else if (half_ready == 2) { half_ready = 0; process_half(&adc_buf[HALF_BUF], HALF_BUF); }
    }
}
```

## 9. 过采样与平均

### 9.1 硬件过采样

STM32部分ADC支持硬件过采样，累加并右移可提高有效分辨率：

| 过采样倍数 | 右移位数 | 增加ENOB | 等效分辨率 |
|-----------|---------|---------|-----------|
| 4x | 2 | 1位 | 13位 |
| 16x | 4 | 2位 | 14位 |
| 256x | 8 | 4位 | 16位 |

原理：过采样N倍，量化噪声分散到N倍带宽，滤波后噪声降sqrt(N)倍。

### 9.2 配置示例

```c
hadc1.Init.OversamplingMode = ENABLE;
hadc1.Init.Oversample.Ratio = ADC_OVERSAMPLING_RATIO_16;
hadc1.Init.Oversample.RightBitShift = ADC_RIGHTBITSHIFT_4;
```

代价：16倍过采样后1MSPS变成62.5kSPS。

## 10. 数据处理流水线

### 10.1 典型流水线

```
ADC+DMA --> 缓冲区 --> 解交织 --> 滤波 --> 特征提取 --> 打包 --> 传输(UART/BLE)
```

### 10.2 简单移动平均滤波

```c
#define MA_LEN  8
int32_t moving_average(int32_t *buf, int32_t new_sample) {
    static int32_t sum = 0;
    sum += new_sample - buf[0];
    memmove(buf, buf + 1, (MA_LEN - 1) * sizeof(int32_t));
    buf[MA_LEN - 1] = new_sample;
    return sum / MA_LEN;
}
```

### 10.3 数据打包传输

```c
typedef struct __attribute__((packed)) {
    uint8_t  header;        // 0xAA
    uint8_t  channel_count;
    uint16_t sample_rate;
    uint16_t timestamp_ms;
    int16_t  data[4];
    uint8_t  checksum;
} sensor_frame_t;

void send_frame(int16_t *ch_data) {
    sensor_frame_t frame = {0};
    frame.header = 0xAA;
    frame.channel_count = 4;
    frame.sample_rate = 1000;
    frame.timestamp_ms = (uint16_t)(HAL_GetTick() & 0xFFFF);
    memcpy(frame.data, ch_data, sizeof(frame.data));
    uint8_t *p = (uint8_t*)&frame;
    frame.checksum = 0;
    for (int i = 0; i < sizeof(frame) - 1; i++) frame.checksum ^= p[i];
    HAL_UART_Transmit(&huart1, (uint8_t*)&frame, sizeof(frame), 100);
}
```

## 11. 常见问题与排查

### 11.1 DMA优先级冲突

**现象**：ADC数据偶现异常值。**解决**：ADC DMA设高优先级。

### 11.2 数据对齐问题

**现象**：12位结果超4095或出现65535。**解决**：右对齐 + Half Word传输宽度。

```c
hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
hdma_adc.Init.MemDataAlignment = DMA_MDATAALIGN_HALFWORD;
```

### 11.3 Cortex-M7缓存一致性

**现象**：CPU读到DMA缓冲区旧值。**原因**：D-Cache。**解决**：处理前无效化D-Cache。

```c
SCB_InvalidateDCache_by_Addr((uint32_t*)adc_buf, BUF_SIZE * 2);
```

### 11.4 中断处理时间过长

**现象**：采样数据出现间隙。**解决**：回调只设标志，处理放主循环；增大缓冲区降低中断频率。

## 12. 系统设计清单

| 检查项 | 说明 |
|--------|------|
| ADC时钟不超限 | STM32F4: 36MHz, G4: 60MHz |
| 采样时间足够 | 高源阻抗需更长采样时间 |
| VDDA独立滤波 | 不与VDD共享 |
| DMA Circular | 连续采样必须 |
| 双缓冲回调 | 半传输处理前半，全传输处理后半 |
| 缓冲区大小 | >= 2倍最长处理时间对应样本数 |
| DMA优先级 | ADC DMA应高优先级 |
| Cache一致性 | Cortex-M7必须处理D-Cache |

## 总结

ADC+DMA连续采样系统设计的核心要点：

1. **架构选择**：ADC连续 + DMA Circular + 双缓冲，是实时采样的标准方案
2. **定时器触发**：需要精确采样率时，必须用定时器TRGO触发ADC
3. **双缓冲防冲突**：半传输和全传输中断配合，CPU和DMA互不干扰
4. **多通道解交织**：扫描模式DMA存储交错数据，处理前必须分离
5. **过采样提精度**：硬件过采样可免费获额外分辨率，代价是采样率降低
6. **注意Cache一致性**：Cortex-M7必须处理D-Cache问题

## 参考文献

1. STMicroelectronics, *STM32F4 Reference Manual (RM0090)*, ADC and DMA chapters, 2023
2. STMicroelectronics, *AN3116: STM32 ADC modes and their application*, 2022
3. STMicroelectronics, *AN4235: How to improve ADC accuracy*, 2021
4. ARM, *Cortex-M7 Technical Reference Manual*, D-Cache coherency section, 2020
5. Walt Kester, *Data Conversion Handbook*, Chapter 3, Analog Devices, 2005
