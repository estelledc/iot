---
schema_version: '1.0'
id: tinyml-anomaly-detection-vibration
title: TinyML振动异常检测在工业IoT中的应用
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
# TinyML振动异常检测在工业IoT中的应用
> **难度**：中级 | **领域**：工业预测维护 | **阅读时间**：约 20 分钟

## 引言

想象一位老司机听发动机声音就能判断哪里出了问题 -- 他不需要把发动机拆下来送到实验室分析，耳朵在现场就能完成诊断。TinyML振动异常检测做的事情类似：把"听觉"装到机器旁边的微控制器上，让它实时听机器的振动，一旦声音不对就立刻报警，而不需要把振动数据传到云端再做分析。

## 1 振动监测与预测维护

### 1.1 为什么监测振动

旋转机械(电机、泵、风机、压缩机)在出现故障前，振动模式会率先发生变化。常见的故障类型及其振动特征：

- **轴承磨损**：高频冲击脉冲，外圈/内圈/滚动体各有特征频率
- **转子不平衡**：1倍转速频率分量增大
- **轴不对中**：2倍转速频率分量突出
- **机械松动**：多阶谐波成分

### 1.2 预测维护的价值

传统维护策略对比：

| 策略 | 方式 | 缺点 |
|------|------|------|
| 事后维护 | 坏了再修 | 停机损失大 |
| 定期维护 | 按时间更换 | 过度维修或不足 |
| 预测维护 | 根据状态决策 | 需要持续监测 |

预测维护能在故障早期发出预警，计划性停机远比紧急停机代价小。

## 2 为什么在设备端做TinyML

### 2.1 云端方案的问题

传统方案是持续采集振动数据上传到云端分析，但这有几个实际问题：

- **数据量大**：3轴加速度计以1kHz采样，每秒生成6KB原始数据，24小时超过500MB
- **延迟高**：从采集到云端返回结果，秒级甚至分钟级
- **依赖网络**：工厂环境网络可能不稳定
- **隐私顾虑**：生产数据不愿外传

### 2.2 边缘端推理的优势

TinyML将模型部署到MCU上，直接在传感器旁边做推理：

- **减少传输**：只发送异常分数或告警，带宽需求降低几个数量级
- **实时检测**：毫秒级响应，故障发生时立即告警
- **离线运行**：不依赖云连接，断网也能正常工作
- **数据隐私**：原始数据不出设备

## 3 数据流水线

### 3.1 从传感器到异常分数

完整的数据处理链路：

```
MEMS加速度计 -> ADC采样 -> 预处理 -> 特征提取 -> ML模型推理 -> 异常分数
```

### 3.2 信号采集

MEMS加速度计(如ADXL345/ADXL362)输出模拟或数字信号。数字输出通过SPI/I2C直接读取，省去外部ADC。

采样参数：
- 采样率：1kHz - 10kHz(视目标频率而定)
- 采样位数：12-16 bit
- 采样窗口：0.1s - 1s(即每窗口100-10000个采样点)

### 3.3 预处理

采集后的原始信号需要预处理才能提取有效特征：

- **去均值**：消除直流偏移
- **加窗**：对采样窗口施加汉宁窗，减少频谱泄漏
- **重采样**：如果采样率不匹配模型输入要求

## 4 特征工程

### 4.1 时域特征

直接从时域波形计算，计算量小：

| 特征 | 含义 | 计算方式 |
|------|------|----------|
| RMS | 有效值，反映振动能量 | sqrt(mean(x^2)) |
| 峰值 | 最大振幅 | max(abs(x)) |
| 峭度 | 信号冲击性 | 四阶中心矩/方差平方 |
| 波峰因子 | 峰值/RMS | 反映冲击脉冲 |

### 4.2 频域特征

对信号做FFT后提取频率信息：

- **FFT峰值频率**：主振动频率，对应转速或故障特征频率
- **频谱质心**：频谱能量分布的"重心"
- **频带能量比**：不同频段的能量占比

### 4.3 时频特征

用STFT(短时傅里叶变换)生成时频谱图，兼顾时间和频率分辨率。将谱图当作图像输入CNN，可自动学习特征。

## 5 模型方法

### 5.1 自编码器

自编码器是最常用的异常检测方案，原理直观：

1. 只用正常运行数据训练
2. 编码器将输入压缩到低维潜在空间
3. 解码器从潜在空间重建输入
4. 正常数据重建误差小，异常数据重建误差大
5. 设定阈值，超过阈值判定异常

```c
// 简化的自编码器推理伪代码
float anomaly_score = 0;
for (int i = 0; i < INPUT_SIZE; i++) {
    float diff = input[i] - reconstructed[i];
    anomaly_score += diff * diff;
}
anomaly_score /= INPUT_SIZE;
if (anomaly_score > THRESHOLD) {
    trigger_alert();
}
```

### 5.2 单类SVM

在特征空间中找到包含正常数据的紧凑边界，边界外的数据判定为异常。适合低维特征输入。

### 5.3 孤立森林

通过随机划分特征空间来"孤立"数据点，异常点更容易被孤立(需要更少的划分次数)。适合多维度特征输入。

### 5.4 CNN频谱图分类

将STFT频谱图作为图像输入CNN，利用卷积层自动提取频域特征。需要更多计算资源，但特征提取能力强。

## 6 训练工作流

### 6.1 数据收集

```
步骤1: 在正常运行状态下持续采集振动数据(至少数天)
步骤2: 手动筛选确认无异常的片段作为训练集
步骤3: 可选: 收集部分异常数据用于验证阈值
```

### 6.2 模型训练

以自编码器为例的训练流程：

1. 数据预处理：去均值、标准化
2. 特征提取：计算时域/频域特征，或直接使用原始窗口
3. 构建自编码器：编码器逐步压缩，解码器逐步恢复
4. 训练：最小化重建误差(MSE损失)
5. 验证：用正常数据集的重建误差分布设定阈值(如99百分位)

### 6.3 阈值选择

阈值直接影响误报率和漏报率的平衡：

- 阈值过低：正常波动也被标记为异常，误报多
- 阈值过高：真正的故障被漏掉，漏报多
- 常用方法：正常数据重建误差的均值 + 3倍标准差

## 7 MCU部署

### 7.1 TensorFlow Lite Micro

TFLite Micro是Google推出的轻量级推理框架，专为MCU设计：

- 纯C++实现，不依赖操作系统
- 支持ARM Cortex-M的CMSIS-NN加速
- 模型大小通常10-50KB
- 推理周期1-10秒(取决于模型复杂度)

### 7.2 部署优化

```c
// CMSIS-DSP加速FFT计算
#include "arm_math.h"

arm_rfft_fast_instance_f32 fft_instance;
arm_rfft_fast_init_f32(&fft_instance, FFT_SIZE);

float32_t input_buf[FFT_SIZE];
float32_t output_buf[FFT_SIZE];

// 执行FFT
arm_rfft_fast_f32(&fft_instance, input_buf, output_buf, 0);

// 计算幅度谱
for (int i = 0; i < FFT_SIZE / 2; i++) {
    float real = output_buf[2 * i];
    float imag = output_buf[2 * i + 1];
    magnitude[i] = sqrtf(real * real + imag * imag);
}
```

### 7.3 资源预算

典型资源配置：

| 资源 | 预算 |
|------|------|
| Flash(模型+代码) | 50-100KB |
| RAM(推理缓冲) | 10-30KB |
| 推理时间 | 10-100ms |
| 功耗 | < 5mA(间歇推理) |

## 8 实践案例：电机轴承监测

### 8.1 硬件方案

- **加速度计**：ADXL345(3轴, SPI接口, 量程16g)
- **MCU**：STM32L476(Cortex-M4, 128KB RAM, 1MB Flash)
- **通信**：BLE(nRF52832模块)或LoRa(SX1276)

### 8.2 软件架构

```
[ADXL345 SPI采样 1kHz]
        |
        v
[CMSIS-DSP FFT 256点]
        |
        v
[特征提取: RMS + 频带能量]
        |
        v
[TFLite Micro 自编码器推理]
        |
        v
[异常分数 -> 阈值判断]
        |
    +---+---+
    |       |
  正常     异常
    |       |
  空闲    LED/蜂鸣器 + BLE告警
```

### 8.3 关键代码片段

```c
// 主循环：采样 -> FFT -> 特征 -> 推理 -> 判断
void monitor_loop(void) {
    while (1) {
        // 1. 采集一个窗口的振动数据
        acquire_vibration_buffer(accel_buf, WINDOW_SIZE);

        // 2. FFT变换
        compute_fft_magnitude(accel_buf, freq_buf, WINDOW_SIZE);

        // 3. 提取特征
        features[0] = compute_rms(accel_buf, WINDOW_SIZE);
        features[1] = compute_kurtosis(accel_buf, WINDOW_SIZE);
        extract_band_energy(freq_buf, &features[2], NUM_BANDS);

        // 4. 模型推理
        float score = model_inference(features, FEATURE_DIM);

        // 5. 异常判断
        if (score > ALERT_THRESHOLD) {
            alert_buzzer_on();
            send_ble_alert(score);
        }

        // 6. 等待下一个推理周期
        delay_ms(INFERENCE_INTERVAL_MS);
    }
}
```

## 9 告警与上报

### 9.1 本地告警

检测到异常后的即时响应：

- **LED指示**：红色闪烁表示告警等级
- **蜂鸣器**：不同频率对应不同严重程度
- **显示屏**：显示异常分数趋势(如果有屏幕)

### 9.2 远程上报

通过无线方式将状态报告发送到网关：

- **LoRa**：远距离(公里级)、低带宽，适合周期性状态报告
- **BLE**：近距离、中等带宽，适合连接手机/网关实时查看
- **上报内容**：设备ID、时间戳、异常分数、特征值、电池电压

## 10 Edge Impulse平台

### 10.1 一站式开发流程

Edge Impulse为TinyML提供了完整的云端开发平台：

1. **数据采集**：通过手机或开发板采集并上传数据
2. **信号处理**：可视化配置FFT/滤波/特征提取
3. **模型训练**：选择神经网络架构，自动调参
4. **模型评估**：查看准确率、混淆矩阵、推理延迟
5. **部署导出**：生成TFLite Micro C++库或Arduino库

### 10.2 适用场景

- 快速原型验证
- 不熟悉ML的嵌入式工程师
- 需要快速迭代的实验项目

## 11 挑战与对策

### 11.1 概念漂移

机器老化会改变"正常"振动模式，导致原本训练好的模型产生误报：

- 对策：定期用最近数据重新训练(在线学习)
- 对策：动态调整阈值，跟踪误差分布的缓慢变化

### 11.2 多种工作模式

同一台机器可能在不同工况下运行(不同转速、不同负载)，每种工况的"正常"不同：

- 对策：为每种工况训练单独的模型或阈值
- 对策：将工况参数(转速)作为模型输入条件

### 11.3 训练数据不足

只有正常运行数据，异常数据稀少：

- 对策：用自编码器/单类SVM等只需要正常数据的方法
- 对策：数据增强：添加模拟噪声、人为注入轻微异常

## 总结

TinyML振动异常检测将预测维护的能力下沉到传感器节点，在微控制器上完成从信号采集到异常判断的全流程。核心技术路线是：MEMS加速度计采集 -> FFT/时域特征提取 -> 轻量级模型(通常是自编码器)推理 -> 阈值判断。关键挑战在于概念漂移、多工况适应和有限的训练数据。随着TFLite Micro和Edge Impulse等工具的成熟，在MCU上部署振动监测模型已不再是高门槛任务。

## 参考文献

1. Elmquist C, Niazi M. TinyML for Anomaly Detection in Industrial IoT: A Survey. IEEE IoT Journal, 2023.
2. Google. TensorFlow Lite for Microcontrollers Official Documentation, 2024.
3. Randall R B, Antoni J. Rolling Element Bearing Diagnostics - A Tutorial. Mechanical Systems and Signal Processing, 2011.
4. Edge Impulse. Continuous Anomaly Detection with Spectral Analysis, 2023.
5. Sharma A, et al. Vibration-based Fault Diagnosis of Rotating Machinery: A Review. Journal of Sound and Vibration, 2022.
