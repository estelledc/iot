---
schema_version: '1.0'
id: tinyml-keyword-spotting-mcu
title: TinyML关键词检测在MCU上的部署实践
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
# TinyML关键词检测在MCU上的部署实践
> **难度**：🟡 中级 | **领域**：嵌入式语音AI | **阅读时间**：约 20 分钟

## 引言

想象你对智能音箱说"嘿，Siri"——在它回答你之前，必须先"听到"这两个字。关键词检测(Keyword Spotting, KWS)就是让设备在本地持续"监听"特定唤醒词的技术。传统方案把音频送到云端识别，但TinyML让MCU(微控制器)自己就能完成——不需要联网，不需要等服务器响应，一毫秒级别就能做出判断。这篇文章讲的就是怎么把KWS模型塞进只有几十KB内存的MCU里。

## 1. 关键词检测(KWS)概述

### 1.1 什么是KWS

关键词检测是在连续音频流中识别预设关键词(如唤醒词)的技术：

- **始终在线(Always-on)**：设备持续监听，等待关键词出现
- **低功耗**：24小时运行，毫瓦级功耗
- **本地推理**：音频不出设备，隐私有保障
- **快速响应**：检测延迟在百毫秒以内

### 1.2 KWS vs ASR

| 对比项 | KWS | ASR(自动语音识别) |
|--------|-----|------------------|
| 词汇量 | 1-35个关键词 | 无限(自由文本) |
| 模型大小 | 20-200KB | 数百MB |
| 计算量 | 低(MCU可运行) | 高(需服务器或NPU) |
| 延迟 | <100ms | 300ms+ |
| 功耗 | mW级 | W级 |
| 典型用途 | 唤醒词检测 | 语音转文字 |

KWS是ASR的"前哨"——先用KWS唤醒设备，再启动ASR处理后续指令。

### 1.3 为什么在MCU上做KWS

- **隐私**：音频数据永远不离开设备，无窃听风险
- **延迟**：本地推理毫秒级响应，无需等网络往返
- **功耗**：始终在线仅需mW级，适合电池供电设备
- **成本**：无需Wi-Fi/蜂窝模块，一颗MCU+麦克风即可
- **离线可用**：断网场景照样工作

## 2. 音频处理流水线

### 2.1 从麦克风到推理结果

```
MEMS麦克风 --> PDM/I2S输出 --> PCM采样(16kHz/16bit)
    --> 分帧(30ms帧/10ms步长) --> 特征提取 --> 模型推理 --> 后处理 --> 检测结果
```

### 2.2 音频采样参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 采样率 | 16kHz | 语音有效带宽8kHz内，Nyquist定理 |
| 量化位数 | 16bit | 动态范围约96dB |
| 帧长 | 25-30ms | 约一个音素时长 |
| 帧移 | 10ms | 帧间重叠保证连续性 |
| 窗函数 | 汉宁窗(Hanning) | 减少频谱泄漏 |

### 2.3 音频环形缓冲区

MCU上通常用环形缓冲区(Ring Buffer)存储最近的音频帧：

```c
#define FRAME_SIZE  480   // 30ms x 16kHz
#define NUM_FRAMES  7     // 约1秒历史

int16_t audio_ring[NUM_FRAMES * FRAME_SIZE];
volatile uint32_t write_idx = 0;

// DMA中断中写入新帧
void audio_dma_callback(void) {
    memcpy(&audio_ring[write_idx * FRAME_SIZE],
           new_frame, FRAME_SIZE * sizeof(int16_t));
    write_idx = (write_idx + 1) % NUM_FRAMES;
}
```

DMA负责音频采集，CPU只做推理，不参与搬运。

## 3. 特征提取

### 3.1 MFCC与Log-Mel频谱

| 特征 | MFCC | Log-Mel频谱图 |
|------|------|---------------|
| 计算步骤 | FFT -> Mel滤波 -> 对数 -> DCT | FFT -> Mel滤波 -> 对数 |
| 输出维度 | 10-13个系数 | 40个Mel频带 |
| 计算量 | 较高(含DCT) | 较低 |
| 模型效果 | 略低 | 略高(端到端学习) |
| MCU推荐 | 传统方案 | 主流方案 |

### 3.2 Log-Mel特征提取流程

```
30ms PCM帧(480点) --> 预加重 --> 汉宁窗 --> 256点FFT
    --> 功率谱 --> 40通道Mel滤波器组 --> 取对数 --> 40维特征向量
```

每10ms生成一个40维特征向量，一帧音频对应的特征图尺寸约为 40(频率) x 49(时间)。

### 3.3 MCU上的FFT优化

- 使用CMSIS-DSP库的`arm_rfft_fast_f32`函数
- 输入256点，输出128个频率bin
- STM32L4上单次FFT约100us
- Mel滤波器组可预计算为查找表，避免运行时三角函数计算

## 4. 适用于MCU的模型架构

### 4.1 主流模型对比

| 模型 | 参数量 | 模型大小 | 准确率(GSC) | 推理时间 | 特点 |
|------|--------|----------|-------------|----------|------|
| DS-CNN(S) | 24K | 24KB | 93% | 6ms | 深度可分离卷积，Google参考 |
| DS-CNN(M) | 42K | 42KB | 94.5% | 10ms | 中等规模，性价比高 |
| TC-ResNet8 | 60K | 60KB | 94% | 8ms | 时间卷积，适合流式处理 |
| GRU | 50K | 50KB | 93% | 12ms | 序列建模，内存开销大 |
| MLP | 20K | 20KB | 88% | 2ms | 最简单，基线方案 |

准确率基于Google Speech Commands v2 12类任务。

### 4.2 深度可分离卷积(DS-CNN)

DS-CNN是KWS的主流架构，将标准卷积拆分为两步：

```
标准卷积:  输入 x 卷积核 = 输出   (参数量 = Cin x Cout x K x K)
深度卷积:  每通道独立卷积          (参数量 = Cin x K x K)
逐点卷积:  1x1卷积通道混合         (参数量 = Cin x Cout x 1 x 1)
```

参数量减少约8-9倍，准确率损失不到1%。

### 4.3 模型架构示例(DS-CNN-S)

```
输入: 40x49 Log-Mel特征图
    --> Conv2D(1->64, 10x4)     # 首层标准卷积
    --> DS-Conv2D(64->64, 3x3)  # 深度可分离块1
    --> DS-Conv2D(64->64, 3x3)  # 深度可分离块2
    --> DS-Conv2D(64->64, 3x3)  # 深度可分离块3
    --> DS-Conv2D(64->128, 3x3) # 深度可分离块4
    --> Global Average Pooling
    --> Dense(128->12)           # 12类输出
```

## 5. 训练工作流

### 5.1 数据集

**Google Speech Commands(GSC)**：

- 版本v2：35个关键词，105,829条录音
- 每条1秒长，16kHz采样
- 常用12类子集："yes"/"no"/"up"/"down"/"left"/"right"/"on"/"off"/"stop"/"go"/"silence"/"unknown"

### 5.2 数据增强

| 增强方法 | 目的 | 参数范围 |
|----------|------|----------|
| 背景噪声叠加 | 提升噪声鲁棒性 | SNR 5-20dB |
| 时间偏移 | 对抗时间抖动 | +/-100ms |
| 速度扰动 | 模拟语速变化 | 0.9-1.1x |
| 音量变化 | 模拟远近场 | +/-6dB |
| 频谱掩蔽 | SpecAugment | 频率/时间掩蔽 |

### 5.3 训练流程

```
GSC数据集 --> 预处理(特征提取) --> 数据增强
    --> 训练(TensorFlow/Keras, 20-50 epochs)
    --> 评估(测试集准确率)
    --> 量化(INT8)
    --> 转换(TFLite Micro格式)
    --> 部署到MCU
```

### 5.4 INT8量化

将浮点模型转为INT8，模型体积缩小4倍，推理速度提升2-3倍：

- 训练后量化(Post-Training Quantization)：简单但有精度损失(1-2%)
- 量化感知训练(QAT)：训练时模拟量化，精度损失更小(<0.5%)

```python
# TensorFlow训练后量化示例
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset_gen
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
tflite_model = converter.convert()
```

## 6. MCU部署

### 6.1 TFLite Micro架构

```
应用层:  main_loop() { 音频采集 -> 特征提取 -> 推理 -> 后处理 }
    |
解释器层: tflite::MicroInterpreter
    |       - 加载模型Flatbuffer
    |       - 分配Tensor Arena
    |       - 执行算子(注册的OP)
    |
算子层:  全连接/卷积/深度卷积/Softmax
    |       - CMSIS-NN加速(ARM Cortex-M)
    |
平台层:  音频DMA / 定时器 / GPIO
```

### 6.2 内存分配

```c
// 典型内存分配
#define TENSOR_ARENA_SIZE  (50 * 1024)  // 50KB
uint8_t tensor_arena[TENSOR_ARENA_SIZE];

// 模型数据(Flash中)
const unsigned char g_model_data[] = {
    0x18, 0x00, 0x00, 0x00, 0x54, 0x46, 0x4c, 0x33,
    // ... 模型Flatbuffer二进制 ...
};

// 创建解释器
tflite::MicroInterpreter interpreter(
    model, resolver, tensor_arena, TENSOR_ARENA_SIZE);
interpreter.AllocateTensors();
```

### 6.3 滑动窗口推理

KWS不需要每帧都做推理，通常每100ms推理一次：

```
时间轴:  |----|----|----|----|----|
帧:      f1  f2  f3  f4  f5  f6
推理:         ^         ^
              每100ms推理一次(用最近1s的特征)
```

每次推理取最近约1秒的特征图输入模型，输出各类别概率。

## 7. 实际案例

### 7.1 硬件配置

| 组件 | 型号 | 说明 |
|------|------|------|
| MCU | STM32L476RG | Cortex-M4, 128KB RAM, 1MB Flash |
| 麦克风 | ICS-43434 | MEMS, I2S输出, SNR 65dB |
| 开发板 | STM32L476G-DISCO | 自带音频Codec |

### 7.2 资源占用

| 资源 | 使用量 | 可用量 | 占比 |
|------|--------|--------|------|
| Flash(模型+代码) | 90KB | 1MB | 9% |
| RAM(Tensor Arena+缓冲) | 64KB | 128KB | 50% |
| 推理时间 | 10ms | 100ms周期 | 10% |
| 平均电流 | 2mA | - | - |

### 7.3 性能指标

- 检测关键词："on"/"off"两个命令词 + "unknown" + "silence"
- 测试集准确率：92%
- 误触发率(False Accept)：每12小时<1次
- 漏触发率(False Reject)：<8%
- 检测延迟：120ms(含特征提取+推理+后处理)

## 8. 准确率与资源的权衡

### 8.1 模型规模vs准确率

| 配置 | 模型大小 | RAM占用 | 准确率(GSC 12类) |
|------|----------|---------|-------------------|
| MLP(2层) | 20KB | 30KB | 88% |
| DS-CNN-S | 24KB | 35KB | 93% |
| DS-CNN-M | 42KB | 50KB | 94.5% |
| DS-CNN-L | 80KB | 80KB | 95.2% |

经验法则：

- 90%准确率：20-30KB模型
- 93-95%准确率：30-80KB模型
- 95%+准确率：80KB+模型

### 8.2 量化对准确率的影响

| 量化方式 | 模型体积 | 准确率变化 |
|----------|----------|-----------|
| FP32(基准) | 4x | 0% |
| FP16 | 2x | -0.1% |
| INT8(训练后量化) | 1x | -1~2% |
| INT8(量化感知训练) | 1x | -0.3~0.5% |

## 9. 误触发管理

### 9.1 置信度阈值

模型输出各类别的Softmax概率，设置置信度阈值：

- 阈值高：漏触发多，误触发少
- 阈值低：漏触发少，误触发多
- 典型阈值：0.7-0.85(根据应用调整)

### 9.2 连续检测要求

要求连续N帧都检测到同一关键词才触发：

- N=1：最灵敏，误触发最多
- N=3：平衡点，误触发大幅减少
- N=5：保守，漏触发增加

```c
#define CONSECUTIVE_REQ  3
int keyword_count = 0;
int last_keyword = -1;

void post_process(float* probabilities, int num_classes) {
    int best = argmax(probabilities, num_classes);
    if (best != last_keyword) {
        keyword_count = 1;
        last_keyword = best;
    } else {
        keyword_count++;
    }
    if (keyword_count >= CONSECUTIVE_REQ && best < NUM_KEYWORDS) {
        trigger_keyword_event(best);
        keyword_count = 0;
    }
}
```

### 9.3 噪声鲁棒性

| 场景 | 挑战 | 对策 |
|------|------|------|
| 白噪声 | 频谱填满，特征模糊 | 训练时加白噪声增强 |
| 电视人声 | 与关键词混淆 | 增加负样本(hard negative) |
| 远场 | 信号弱，混响大 | 远场数据增强/AEC前处理 |
| 突发噪声 | 门关/拍手 | 短时能量检测+VAD预过滤 |

## 10. 工具与平台

### 10.1 开发平台对比

| 平台 | 门槛 | 灵活性 | 加速支持 | 适合人群 |
|------|------|--------|----------|----------|
| Edge Impulse | 低(可视化) | 中 | CMSIS-NN | 快速原型 |
| TFLite Micro | 中(需编码) | 高 | CMSIS-NN | 定制开发 |
| STM32 X-CUBE-AI | 中 | 中 | STM32 AI库 | STM32用户 |
| Arm ML Zoo | 低(预训练) | 低 | CMSIS-NN | 快速验证 |
| NNoM | 中 | 高 | 自定义 | 裸机偏好者 |

### 10.2 Edge Impulse工作流

```
数据采集 --> 标注 --> 特征提取(自动) --> 模型训练(自动调参)
    --> 量化(自动INT8) --> 部署(生成C++库) --> 烧录MCU
```

适合从零开始的开发者，全流程可视化，不需要写一行代码。

### 10.3 TFLite Micro工作流

```
本地训练(TF/Keras) --> 转换(.tflite) --> 集成到C++项目
    --> 配置Tensor Arena --> 适配平台(音频接口) --> 编译烧录
```

适合需要精确控制模型和推理过程的开发者。

## 11. 功耗优化

### 11.1 占空比推理

不是每个音频帧都需要推理：

```
全速推理:   |infer|infer|infer|infer|  功耗高
占空比推理: |infer|sleep|sleep|infer|  功耗降低50-75%
```

每100ms推理一次即可捕获关键词，其余时间MCU可进入低功耗模式。

### 11.2 硬件VAD预过滤

语音活动检测(VAD)在音频前端过滤静音段：

```
麦克风 --> 硬件VAD --> 有语音? --> 是 --> 唤醒MCU做KWS推理
                          --> 否 --> MCU保持睡眠
```

- 硬件VAD功耗仅数十uA
- 静音占实际环境的70-90%
- 平均功耗可从2mA降至0.5mA以下

### 11.3 功耗对比

| 方案 | 平均电流 | 唤醒延迟 | 实现复杂度 |
|------|----------|----------|-----------|
| 全速推理 | 2-5mA | 0ms | 低 |
| 占空比推理 | 0.5-1.5mA | <100ms | 中 |
| VAD预过滤 | 0.1-0.5mA | 100-300ms | 高 |
| 外部唤醒芯片 | <0.1mA | 200-500ms | 高(额外硬件) |

## 总结

TinyML关键词检测让MCU具备了"听觉"能力，无需联网即可在本地实时识别唤醒词。核心流水线是：麦克风采集16kHz音频 -> 分帧提取Log-Mel特征 -> DS-CNN等轻量模型推理 -> 后处理过滤误触发。模型量化到INT8后仅占20-80KB Flash，推理时间10ms以内，MCU平均功耗可控制在1mA以下。Edge Impulse提供低门槛的端到端方案，TFLite Micro适合需要灵活定制的场景。功耗优化的关键是用VAD预过滤和占空比推理，让MCU在静音时尽量睡眠。90%以上准确率在50-100KB模型中已经可以稳定实现。

## 参考文献

1. Y. Zhang et al., "Hello Edge: Keyword Spotting on Microcontrollers", arXiv:1711.07128, 2018
2. Google, "TensorFlow Lite for Microcontrollers", https://www.tensorflow.org/lite/microcontrollers
3. Arm, "CMSIS-NN: Efficient Neural Network Kernels for Cortex-M", 2022
4. Edge Impulse, "Keyword Spotting Tutorial", https://docs.edgeimpulse.com/docs/tutorials
5. P. Warden, D. Situnayake, "TinyML: Machine Learning with TensorFlow Lite on Arduino and Ultra-Low-Power Microcontrollers", O'Reilly, 2019
