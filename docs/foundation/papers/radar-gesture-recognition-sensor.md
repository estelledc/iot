# 雷达手势识别传感器硬件与算法概述
> **难度**：🔴 高级 | **领域**：雷达感知技术 | **阅读时间**：约 22 分钟

## 引言

想象一下：你在漆黑的卧室里挥挥手，灯就亮了。不需要碰开关，不需要摄像头"看"你，甚至毯子盖住手也能识别动作。这不是科幻电影，而是 60GHz 毫米波雷达在手势识别上的真实能力。雷达感知就像蝙蝠的回声定位——发射一段电磁波，听回声，从回声中判断距离、速度和方向。本文从雷达硬件原理出发，沿信号处理流水线一路走到手势分类算法，帮助理解这项技术为什么能在 IoT 领域替代摄像头做近距离交互。

## 1. 雷达感知基础

### 1.1 FMCW 雷达原理

FMCW (Frequency Modulated Continuous Wave) 雷达是手势识别的主流方案。它发射频率线性变化的"啁啾"信号(Chirp)，接收反射信号，两者混频后产生差频(Beat Frequency)。

```
发射信号: f(t) = f0 + S * t        (S = 带宽/啁啾时长)
接收信号: f(t) = f0 + S * (t - td)  (td = 2R/c)
差频:     fb = S * td = 2 * S * R / c
```

- R: 目标距离，c: 光速，S: 调频斜率
- 差频 fb 与距离 R 成正比——对差频做 FFT 就得到距离信息

### 1.2 距离分辨率

距离分辨率由带宽决定：

```
dR = c / (2 * B)
```

60GHz ISM 频段可用带宽约 7GHz，理论距离分辨率约 2cm，足以分辨手指的微动作。

### 1.3 速度测量与多普勒效应

运动目标反射信号会产生多普勒频移：

```
fd = 2 * v * f0 / c
```

- v: 目标径向速度，f0: 中心频率
- 60GHz 雷达对速度非常敏感：1m/s 手部运动可产生约 400Hz 多普勒频移

多个 Chirp 之间对同一距离单元做 FFT（多普勒-FFT），就能提取速度信息。

### 1.4 角度估计

使用多根接收天线构成阵列，利用目标反射信号到达不同天线的相位差估计角度：

```
相位差: d_phi = 2 * pi * d * sin(theta) / lambda
```

- d: 天线间距，lambda: 波长，theta: 到达角
- 60GHz 波长约 5mm，天线间距可做得非常紧凑
- 天线数越多，角度分辨率越高（典型 3-4 根接收天线）

## 2. 硬件平台

### 2.1 Google Soli

Soli 是手势识别雷达的里程碑项目，核心特点：

| 参数 | 值 |
|------|-----|
| 频段 | 60GHz ISM |
| 带宽 | 7GHz |
| 帧率 | 10000 fps |
| 天线 | 1Tx + 4Rx |
| 芯片面积 | 约 5mm x 5mm |
| 功耗 | 约 50-100mW |

Soli 证明了雷达手势识别可集成到手机/手表级别设备，后被 Pixel 4 采用。

### 2.2 Infineon BGT60TR13C

目前最广泛使用的 60GHz 手势识别雷达芯片：

- 1 发 3 收天线阵列
- 集成 VCO、PLL、ADC
- SPI 接口输出原始数据
- 扫描帧率可配置（典型 10-100fps）
- 功耗约 50-200mW（取决于配置）
- 配合 XENSIV DK 开发板可快速验证

### 2.3 TI IWR1443 / AWR1642

77GHz 汽车雷达家族，也适用于手势识别：

- IWR1443: 3 发 4 收，适合高精度
- AWR1642: 2 发 4 收，集成 DSP/HWA 加速器
- 优势：SDK 成熟，算法库丰富
- 劣势：77GHz 非全球 ISM，功耗偏高

### 2.4 Acconeer A121

采用脉冲相干雷达(Pulsed Coherent Radar)而非 FMCW：

- 60GHz，单天线收发
- 超低功耗：平均约 1-10mW
- 精密距离测量可达亚毫米级
- 适合存在检测、接近感测，手势识别能力有限

## 3. 信号处理流水线

### 3.1 整体流程

```
原始ADC数据
  |
  v
[Range-FFT]  ----> 距离维信息
  |
  v
[Doppler-FFT] ----> 速度维信息
  |
  v
[CFAR检测]   ----> 目标点提取
  |
  v
[点云生成]   ----> (距离, 速度, 角度) 元组
  |
  v
[特征提取]   ----> 手势特征向量
  |
  v
[分类器]     ----> 手势标签
```

### 3.2 Range-FFT

对每个 Chirp 的采样数据做 FFT：

- 采样率通常 1-5 Msps
- FFT 点数 256-1024
- 输出：距离-幅度谱
- 窗函数（Hamming/Hanning）抑制旁瓣

### 3.3 Doppler-FFT

对同一距离单元在多个 Chirp 上的数据做第二次 FFT：

- Chirp 数量（慢时间维度）通常 16-128
- 输出：距离-多普勒图（Range-Doppler Map, RDM）
- RDM 是后续处理的核心数据结构

### 3.4 CFAR 检测

恒虚警率(CFAR)算法从 RDM 中提取目标点：

- CA-CFAR (Cell Averaging)：取周围单元均值作为阈值
- OS-CFAR (Ordered Statistic)：排序取中间值，抗干扰目标
- 检测结果：目标点列表 (range_bin, doppler_bin, amplitude)

### 3.5 点云生成

对检测到的目标点进行角度估计，生成 3D 点云：

```python
# 伪代码：点云生成
point_cloud = []
for target in cfar_detections:
    r = target.range_bin * range_resolution
    v = target.doppler_bin * velocity_resolution
    theta = angle_estimation(target.rx_phases)  # 利用多天线相位差
    x = r * cos(theta)
    y = r * sin(theta)
    point_cloud.append((x, y, v, target.amplitude))
```

## 4. 手势分类方法

### 4.1 传统机器学习方法

手工设计特征 + 分类器：

**常用特征：**

| 特征类型 | 示例 |
|----------|------|
| 距离特征 | 目标距离均值/方差、距离变化率 |
| 速度特征 | 多普勒均值/峰值、速度持续时间 |
| 角度特征 | 方位角变化范围、角速度 |
| 统计特征 | RDM 直方图、能量分布矩 |

**常用分类器：** SVM、Random Forest、k-NN

优势：计算量小，可在 Cortex-M4 上实时运行
劣势：特征工程耗时，泛化能力有限

### 4.2 深度学习方法

#### 4.2.1 CNN on Range-Doppler Map

将 RDM 视为二维图像，输入 CNN：

```
输入: T帧 x H距离 x W速度 的 RDM 序列
模型: 3D-CNN 或 2D-CNN + 时间聚合
输出: 手势类别概率
```

- 优点：自动特征提取，精度高
- 缺点：需要大量标注数据，计算资源需求大

#### 4.2.2 RNN/LSTM on Time Series

将点云序列或特征序列输入 RNN：

```python
# 简化 LSTM 手势分类
class GestureLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        out, _ = self.lstm(x)         # x: (batch, seq_len, features)
        return self.fc(out[:, -1, :])  # 取最后时刻输出
```

#### 4.2.3 点云网络

直接处理雷达点云，类似 PointNet 思路：

- 对每帧点云做 PointNet 提取帧特征
- 帧特征序列输入 LSTM 做时序建模
- 适合稀疏点云场景

### 4.3 方法对比

| 方法 | 精度 | 计算量 | 数据需求 | 可部署性 |
|------|------|--------|----------|----------|
| SVM + 手工特征 | 中 | 低 | 少(100s) | Cortex-M 可用 |
| CNN on RDM | 高 | 高 | 多(1000s) | 需要 DSP/NPU |
| LSTM on 序列 | 高 | 中 | 多(1000s) | 需要 DSP |
| PointCloud Net | 中高 | 中 | 中 | 需要 DSP |

## 5. 雷达 vs 摄像头

### 5.1 雷达优势

- **暗光可用**：不依赖环境光，完全黑暗中正常工作
- **穿透材料**：可穿透塑料、织物、玻璃——设备可完全封闭
- **隐私保护**：不生成图像，无隐私泄露风险
- **小尺寸**：芯片级封装，适合空间受限设备
- **低功耗**：50-200mW，远低于摄像头模组

### 5.2 雷达劣势

- **无纹理信息**：无法识别手势之外的身份、表情
- **空间分辨率有限**：2cm 级别，不如摄像头的亚毫米级
- **环境干扰**：金属反射、多径效应影响检测

## 6. 功耗与探测范围

### 6.1 60GHz 雷达的典型参数

| 参数 | 典型值 |
|------|--------|
| 探测距离 | 0-2m（手势识别） |
| 距离分辨率 | 2-4cm |
| 速度分辨率 | 5-20 cm/s |
| 角度分辨率 | 15-30 度（3Rx） |
| 发射功率 | 0-10 dBm EIRP |
| 功耗 | 50-200mW（工作态） |
| 待机功耗 | <1mW |

### 6.2 功耗优化策略

- 降低帧率：非交互时降至 1fps 做存在检测
- 减少 Chirp 数量：牺牲速度分辨率换功耗
- 占空比控制：脉冲式工作，间歇采样
- 使用硬件加速器替代软件 FFT

## 7. IoT 应用场景

### 7.1 智能家居无触控

- 挥手开关灯/电器
- 手指捏合调节音量
- 存在检测自动开/关空调

### 7.2 睡眠监测

- 检测呼吸频率（胸腔微动约 0.5mm）
- 体动检测判断睡眠阶段
- 无需佩戴设备

### 7.3 生命体征监测

- 雷达可检测心跳引起的胸腔微动
- 精度可达 1-2 bpm（比PPG略低但无需接触）
- 适合老人看护、婴儿监测

### 7.4 车内交互

- 识别驾驶员手势控制导航/音乐
- 座椅占用检测（安全气囊策略）
- 后排儿童遗留提醒

## 8. 实践示例：BGT60TR13C 手势检测

### 8.1 硬件配置

```
[Infineon BGT60TR13C] --SPI--> [STM32F4 / Cortex-M4]
                                |
                                +---> 手势分类算法
                                |
                                +---> UART 输出结果
```

### 8.2 配置参数

```c
// BGT60TR13C 典型手势识别配置
radar_config_t config = {
    .start_freq_Hz    = 58000000000ULL,  // 58GHz 起始频率
    .end_freq_Hz      = 62500000000ULL,  // 62.5GHz 结束频率
    .num_chirps       = 32,             // 每帧 32 个 Chirp
    .num_samples      = 64,             // 每个 Chirp 64 采样
    .sample_rate       = 2000000,        // 2Msps
    .frame_rate        = 20,             // 20fps
    .rx_antennas       = 3,             // 使用全部 3 个接收天线
};
```

### 8.3 信号处理流程

```c
// 简化处理流程
void process_frame(uint16_t *adc_data) {
    // 1. Range-FFT (每根天线每chirp)
    arm_cfft_f32(&fft_instance, fft_input, 0, 1);

    // 2. Doppler-FFT (同一距离bin跨chirps)
    arm_cfft_f32(&doppler_fft, doppler_input, 0, 1);

    // 3. CFAR 检测
    cfar_detect(range_doppler_map, &targets, &num_targets);

    // 4. 提取特征
    extract_features(&targets, &feature_vector);

    // 5. SVM 分类
    gesture_id = svm_predict(&feature_vector);
}
```

### 8.4 可识别手势

| 手势 | 运动特征 | 典型应用 |
|------|----------|----------|
| 左右滑动 | 距离变化 + 速度方向 | 切换歌曲 |
| 前推 | 距离减小 + 速度正 | 确认/开灯 |
| 后拉 | 距离增大 + 速度负 | 取消/关灯 |
| 点击 | 距离快速变化 | 选择 |
| 旋转 | 角度变化 | 调节音量 |

## 9. 挑战与局限

### 9.1 手势词表有限

- 当前可稳定识别的手势约 5-10 种
- 精细手势（如不同手指）难以区分
- 连续手势的分割是开放问题

### 9.2 用户差异

- 不同人手势速度、幅度差异大
- 同一人每次手势不完全一致
- 需要用户自适应或大量训练数据

### 9.3 多用户干扰

- 多人同时在雷达前做手势
- 需要目标跟踪区分不同用户
- 当前方案多假设单用户场景

## 10. 集成注意事项

### 10.1 天线设计

- 60GHz 波长约 5mm，天线尺寸极小
- 需要精确控制天线间距（lambda/2 约 2.5mm）
- 微带贴片天线或缝隙天线常见选择
- 天线增益影响探测距离和角度分辨率

### 10.2 天线罩(Radome)材料

- 罩体材料需对 60GHz 电磁波低损耗
- 常用材料：工程塑料(ABS/PC)，厚度需避开半波长整数倍
- 金属装饰件会严重干扰雷达——设计时需预留非金属窗口

### 10.3 法规合规

- 60GHz ISM 频段：全球大部分地区可用
- 发射功率限制：FCC Part 15 / ETSI EN 302 265
- EIRP 通常限制在 10-40dBm 以内
- 需关注各国具体法规差异

## 总结

雷达手势识别用 FMCW 或脉冲相干技术捕捉手部微动，通过 Range-FFT -> Doppler-FFT -> CFAR -> 点云 -> 特征提取 -> 分类的流水线完成手势识别。相比摄像头，它在暗光、隐私保护和小型化上有独特优势，但手势词表和用户泛化仍是挑战。对于 IoT 设备，BGT60TR13C 等芯片配合 Cortex-M4 已能实现基本手势交互，是触摸和语音之外的有力补充。

## 参考文献

1. Lien J, et al. "Soli: Ubiquitous Gesture Sensing with Millimeter Wave Radar." ACM SIGGRAPH 2016.
2. Infineon Technologies. "XENSIV BGT60TR13C Radar Sensor Datasheet." 2023.
3. Texas Instruments. "IWR1443 Single-Chip 77GHz FMCW Radar Sensor Reference Design." 2019.
4. Acconeer. "A121 Pulsed Coherent Radar Product Guide." 2023.
5. Sun H, et al. "Micro-Doppler Signatures for Intelligent Human Activity Recognition Using Radar." IEEE Radar Conference, 2019.
