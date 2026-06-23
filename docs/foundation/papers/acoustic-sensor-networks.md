# 声学传感网络：从 MEMS 麦克风阵列到边缘音频智能

> **难度**：🟡 中级 | **领域**：声学传感、信号处理、边缘 AI | **阅读时间**：约 19 分钟

## 日常类比

你一定有过这样的体验：在嘈杂的聚会里，即使周围人声鼎沸，你依然能听清对面朋友说的话。这就是"鸡尾酒会效应"——人耳利用双耳时间差定位声源，大脑过滤掉不感兴趣的方向的噪声。

声学传感网络做的是同样的事情，只不过"耳朵"换成了 MEMS 麦克风阵列，"大脑"换成了 DSP 芯片。通过多个麦克风之间的信号时间差和强度差，系统可以精确定位声源方向、增强目标声音、识别异常事件（如玻璃破碎、枪声、机器异响）。

这项技术正从消费电子（智能音箱的远场拾音）扩展到工业 IoT——工厂里通过"听"机器运转的声音来判断设备健康状态，比装振动传感器更便宜、更灵活。

## 1. MEMS 麦克风技术基础

### 1.1 工作原理

MEMS 麦克风的核心是一个微型电容器：一块固定背板 + 一片可动振膜。声波引起振膜振动，改变两板间距，从而改变电容值。内置的 ASIC 将电容变化转换为电信号。

### 1.2 关键参数对比

| 参数 | 入门级 (SPH0645) | 中端 (ICS-43434) | 高端 (IM69D130) |
|------|-----------------|-----------------|-----------------|
| 制造商 | Knowles | TDK InvenSense | Infineon |
| SNR | 65 dB(A) | 70 dB(A) | 69 dB(A) |
| AOP (声学过载点) | 120 dB SPL | 126 dB SPL | 130 dB SPL |
| 灵敏度 | -26 dBFS | -26 dBFS | -36 dBFS |
| 动态范围 | 87 dB | 96 dB | 105 dB |
| 接口 | I2S | I2S/TDM | I2S/TDM/PDM |
| 频率响应 | 50-15k Hz | 20-20k Hz | 28-20k Hz |
| 功耗 | 600 μA | 850 μA | 980 μA |
| 封装 | 3.5×2.65 mm | 3.5×2.65 mm | 4.0×3.0 mm |
| 单价 (1k) | ¥3 | ¥8 | ¥15 |

### 1.3 PDM vs I2S 接口选择

```c
// PDM (Pulse Density Modulation) 接口配置
// 优点: 只需 CLK + DATA 两根线，多麦共享时钟
// 缺点: 需要额外 decimation 滤波器

// I2S 配置示例 (ESP32-S3)
#include "driver/i2s_std.h"

i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(
    I2S_NUM_0, I2S_ROLE_MASTER
);

i2s_std_config_t std_cfg = {
    .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(48000),  // 48kHz 采样率
    .slot_cfg = I2S_STD_MSB_SLOT_DEFAULT_CONFIG(
        I2S_DATA_BIT_WIDTH_24BIT,    // 24位精度
        I2S_SLOT_MODE_STEREO         // 双声道(L/R选择)
    ),
    .gpio_cfg = {
        .mclk = GPIO_NUM_0,
        .bclk = GPIO_NUM_4,
        .ws = GPIO_NUM_5,
        .dout = I2S_GPIO_UNUSED,
        .din = GPIO_NUM_6,
    },
};

// 多麦克风 TDM 配置 (4路复用同一数据线)
// TDM 帧格式: [CH0_24bit | CH1_24bit | CH2_24bit | CH3_24bit]
// BCLK = 48000 * 24 * 4 = 4.608 MHz
```

## 2. 波束成形（Beamforming）

### 2.1 延迟-求和波束成形 (DSB)

最基本的波束成形算法：根据目标方向计算各麦克风的时延差，对齐后求和。目标方向的信号相干叠加增强，其他方向的信号非相干叠加抵消。

```python
import numpy as np
from scipy.signal import fftconvolve

class DelayAndSumBeamformer:
    """
    延迟-求和波束成形器
    适用于均匀线阵 (ULA) 和环形阵列
    """
    def __init__(self, mic_positions, sample_rate=48000, c=343.0):
        """
        mic_positions: (N, 3) 麦克风坐标 (米)
        sample_rate: 采样率 (Hz)
        c: 声速 (m/s)
        """
        self.mic_pos = np.array(mic_positions)
        self.n_mics = len(mic_positions)
        self.fs = sample_rate
        self.c = c
    
    def compute_delays(self, doa_deg):
        """
        计算各麦克风相对于参考点的时延
        doa_deg: 目标方向 (方位角, 度)
        """
        theta = np.radians(doa_deg)
        # 远场假设: 平面波到达
        direction = np.array([np.cos(theta), np.sin(theta), 0])
        
        # 各麦克风相对延迟 (秒)
        delays = self.mic_pos @ direction / self.c
        delays -= delays.min()  # 归一化到非负
        
        return delays
    
    def beamform(self, signals, doa_deg):
        """
        执行波束成形
        signals: (N_mics, N_samples) 多通道音频
        doa_deg: 目标方向
        returns: (N_samples,) 增强后信号
        """
        delays = self.compute_delays(doa_deg)
        delay_samples = (delays * self.fs).astype(int)
        
        n_samples = signals.shape[1]
        max_delay = delay_samples.max()
        output = np.zeros(n_samples + max_delay)
        
        for i in range(self.n_mics):
            d = delay_samples[i]
            output[max_delay - d:max_delay - d + n_samples] += signals[i]
        
        # 归一化
        output /= self.n_mics
        return output[:n_samples]
    
    def steering_response(self, signals, angles=np.arange(-90, 91, 1)):
        """
        扫描所有方向的功率，生成空间谱
        用于声源定位 (SRP-PHAT)
        """
        powers = []
        for angle in angles:
            beam_out = self.beamform(signals, angle)
            power = np.mean(beam_out**2)
            powers.append(power)
        
        return angles, np.array(powers)

# 使用示例: 4 麦克风线阵，间距 4cm
mic_spacing = 0.04  # 4cm (适合 4kHz 以下)
mic_positions = [[i * mic_spacing, 0, 0] for i in range(4)]
bf = DelayAndSumBeamformer(mic_positions)
```

### 2.2 阵列设计要点

| 设计参数 | 计算公式 | 典型值 | 约束 |
|---------|---------|--------|------|
| 最大无栅瓣间距 | d ≤ λ_min/2 = c/(2·f_max) | 4.3 cm @4kHz | 频率上限 |
| 阵列孔径 | D = (N-1)·d | 12.9 cm (4麦@4cm) | 角分辨率 |
| 半功率波束宽度 | θ_3dB ≈ 0.89·λ/D | 22° @2kHz, 4麦 | 定位精度 |
| 波束增益 | 10·log10(N) | 6 dB (4麦) | SNR 提升 |
| 白噪声增益 | 同上 (DSB) | 6 dB (4麦) | 抗噪能力 |

## 3. 声源定位算法

### 3.1 TDOA 与 GCC-PHAT

GCC-PHAT（广义互相关-相位变换）是工业界最常用的时延估计算法，对混响鲁棒性强：

```python
def gcc_phat(sig1, sig2, fs, max_delay_samples=None):
    """
    GCC-PHAT 时延估计
    比普通互相关更抗混响：只保留相位信息，忽略幅度
    """
    n = len(sig1) + len(sig2) - 1
    n_fft = 2**int(np.ceil(np.log2(n)))
    
    # FFT
    S1 = np.fft.rfft(sig1, n=n_fft)
    S2 = np.fft.rfft(sig2, n=n_fft)
    
    # 互功率谱
    cross_spectrum = S1 * np.conj(S2)
    
    # PHAT 加权: 只保留相位
    magnitude = np.abs(cross_spectrum)
    magnitude[magnitude < 1e-10] = 1e-10  # 避免除零
    gcc = np.fft.irfft(cross_spectrum / magnitude)
    
    # 寻找峰值
    if max_delay_samples is None:
        max_delay_samples = n_fft // 2
    
    # 循环移位对齐
    gcc = np.concatenate([gcc[-max_delay_samples:], gcc[:max_delay_samples+1]])
    
    peak_idx = np.argmax(np.abs(gcc))
    delay_samples = peak_idx - max_delay_samples
    delay_seconds = delay_samples / fs
    
    return delay_seconds, gcc

# 示例: 两个麦克风间距 10cm，声源在 30° 方向
# 理论时延 = d*sin(θ)/c = 0.1*sin(30°)/343 = 0.146 ms = 7 samples @48kHz
```

### 3.2 三维定位 (多麦克风对)

```python
def localize_3d(mic_positions, tdoa_pairs, tdoa_values, c=343.0):
    """
    最小二乘法三维声源定位
    mic_positions: (N, 3) 麦克风坐标
    tdoa_pairs: [(i, j), ...] 麦克风对索引
    tdoa_values: 对应时延差 (秒)
    """
    # 转换为距离差
    range_diffs = np.array(tdoa_values) * c
    
    # 线性化: 以 mic[0] 为参考
    # |r - mi| - |r - m0| = d_i0
    # 展开后线性化 (Taylor/Chan算法简化版)
    
    N = len(tdoa_pairs)
    A = np.zeros((N, 3))
    b = np.zeros(N)
    
    m0 = mic_positions[0]
    for idx, ((i, j), rd) in enumerate(zip(tdoa_pairs, range_diffs)):
        mi = mic_positions[i]
        mj = mic_positions[j]
        A[idx] = 2 * (mj - mi)
        b[idx] = (rd**2 - np.sum(mj**2) + np.sum(mi**2))
    
    # 最小二乘解
    source_pos, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    return source_pos
```

## 4. 声学事件检测

### 4.1 边缘端音频分类流水线

```
┌───────────────────────────────────────────────────┐
│          边缘声学事件检测流水线                       │
├───────────────────────────────────────────────────┤
│                                                   │
│  [麦克风] → [PDM→PCM] → [VAD 静音检测]            │
│                              ↓ (有声段)            │
│                    [Mel频谱图提取]                  │
│                    64 Mel bins, 25ms帧             │
│                              ↓                    │
│                    [CNN 分类模型]                   │
│                    MobileNetV2-tiny               │
│                    ~100K 参数                     │
│                              ↓                    │
│              ┌───────────────┴──────────┐         │
│              │ 事件类型 + 置信度 + 方向角 │         │
│              └───────────────┬──────────┘         │
│                              ↓                    │
│                    [阈值过滤 + 去重]               │
│                              ↓                    │
│                    [MQTT 上报 / 本地告警]           │
└───────────────────────────────────────────────────┘
```

### 4.2 边缘推理性能对比

| 平台 | 模型 | 参数量 | 推理时间 | 功耗 | 准确率 | 适用场景 |
|------|------|--------|---------|------|--------|---------|
| ESP32-S3 | tiny-CNN | 50K | 80 ms | 100 mW | 85% | 简单分类(3-5类) |
| STM32H7 | MobileNet-tiny | 100K | 45 ms | 200 mW | 89% | 中等复杂度 |
| MAX78000 | CNN (硬件加速) | 200K | 2 ms | 5 mW | 91% | 超低功耗连续监测 |
| RPi Zero 2W | YAMNet-lite | 500K | 120 ms | 500 mW | 94% | 多类别高精度 |
| Coral Edge TPU | EfficientNet-B0 | 4M | 8 ms | 2W | 96% | 实时多路 |

### 4.3 常见声学事件识别准确率 (AudioSet 测试集)

| 事件类别 | 传统 MFCC+SVM | 深度学习 CNN | 工业部署精度 |
|---------|--------------|-------------|------------|
| 玻璃破碎 | 82% | 96% | 93% (实际) |
| 烟雾报警 | 95% | 99% | 97% |
| 犬吠 | 78% | 94% | 88% |
| 枪声 | 85% | 97% | 91% |
| 机器异响 | 70% | 88% | 82% |
| 人声检测 | 90% | 98% | 95% |

## 5. 水下声学传感

### 5.1 水下声学 vs 空气声学

| 参数 | 空气中 | 水中 | 影响 |
|------|--------|------|------|
| 声速 | 343 m/s | 1500 m/s | 时延估计精度变化 |
| 吸收系数 @10kHz | 0.1 dB/km | 1 dB/km | 传播距离受限 |
| 吸收系数 @100kHz | 3 dB/km | 40 dB/km | 高频衰减严重 |
| 阻抗 | 415 Pa·s/m | 1.5×10⁶ Pa·s/m | 换能器设计不同 |
| 多径效应 | 轻微 | 严重 (海面/海底反射) | 需要复杂均衡 |
| 背景噪声 | 可控 | 航运/生物/湍流 | SNR 挑战 |

### 5.2 IoT 水下声学应用

主要应用场景包括：水下管线泄漏检测（通过声学特征变化识别泄漏点，精度可达 ±2 米）、渔业资源监测（利用鱼群游动产生的特征频率估计密度）、海洋环境监测（利用声学层析成像测量大范围水温分布）。

## 6. 结构健康监测 (SHM) 中的声学方法

### 6.1 声发射 (AE) 监测

```python
class AcousticEmissionMonitor:
    """
    声发射监测系统
    用于检测结构裂纹扩展、腐蚀、松动等损伤
    """
    def __init__(self, sensor_positions, sample_rate=1000000):
        """
        AE 传感器典型工作频率: 100kHz - 1MHz
        远高于音频范围，使用压电传感器
        """
        self.sensor_pos = np.array(sensor_positions)
        self.fs = sample_rate
        self.threshold_db = 40  # 触发阈值 (dB_AE)
        self.event_buffer = []
    
    def detect_event(self, signal, channel):
        """AE 事件检测 - 阈值触发"""
        # 计算包络 (Hilbert 变换)
        analytic = np.abs(self._hilbert(signal))
        
        # dB 转换 (参考 1μV)
        db_signal = 20 * np.log10(analytic / 1e-6 + 1e-10)
        
        # 阈值交叉检测
        above_threshold = db_signal > self.threshold_db
        
        # 提取 AE 参数
        if np.any(above_threshold):
            start = np.argmax(above_threshold)
            end = len(above_threshold) - np.argmax(above_threshold[::-1])
            
            event = {
                'channel': channel,
                'amplitude_db': np.max(db_signal),
                'duration_us': (end - start) / self.fs * 1e6,
                'rise_time_us': (np.argmax(db_signal) - start) / self.fs * 1e6,
                'energy': np.sum(signal[start:end]**2),
                'counts': self._count_threshold_crossings(
                    signal[start:end], self.threshold_db
                ),
            }
            self.event_buffer.append(event)
            return event
        return None
    
    def classify_damage(self, event):
        """
        基于 AE 参数的损伤分类
        经验规则 (实际部署需要训练数据)
        """
        if event['rise_time_us'] < 50 and event['amplitude_db'] > 70:
            return 'crack_initiation'
        elif event['duration_us'] > 1000 and event['amplitude_db'] < 55:
            return 'friction_rubbing'
        elif event['counts'] > 20 and event['energy'] > 1e-6:
            return 'crack_propagation'
        else:
            return 'unknown'
```

### 6.2 超声导波检测

超声导波可在板状/管状结构中长距离传播（数十米），用少量传感器覆盖大面积。IoT 化的趋势是将导波激励/接收集成到低功耗节点中，实现自主巡检。

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：用 INMP441 MEMS 麦克风 + ESP32 搭建单麦录音系统，学习 I2S 接口配置和基本音频采集
2. **第二步**：扩展到 2 麦克风，实现 GCC-PHAT 时延估计，验证声源方向判断
3. **第三步**：在 ESP32-S3 上部署简单的 Mel 频谱 + CNN 分类模型（如区分"拍手/说话/静音"三类）
4. **第四步**：构建 4 麦环形阵列，实现 360° 声源定位 + 事件分类的完整流水线

### 7.2 具体调优建议

**硬件设计**：

- 麦克风间距决定频率范围上限：d_max = c/(2·f_max)。要覆盖 8kHz 以下需间距 ≤ 2.1cm，实际推荐 1.8-2.0cm
- 麦克风一致性很关键：同批次 MEMS 麦克风灵敏度差异通常 ±1-3 dB，部署前需要逐个校准或选配
- PCB 声孔设计影响频响：声孔直径推荐 0.8-1.0mm，前腔体积尽量小（< 1mm³），否则会引入 Helmholtz 共振
- 风噪防护：户外应用必须加防风罩，否则 > 1m/s 风速下低频噪声淹没信号

**算法优化**：

- GCC-PHAT 对宽带信号效果最好，窄带信号（如纯音报警）建议用 GCC-ML（最大似然）
- 实时波束成形推荐频域实现：overlap-save 方法，计算量仅为时域的 1/5
- 分类模型输入推荐 128 频点 Mel 频谱图 + 1 秒窗口（48 帧），在精度和计算量间平衡最优
- 对于工业监测场景，异常检测（autoencoder/one-class SVM）比分类更实用——不需要收集所有故障样本

**部署注意事项**：

- 采样率与存储/传输带宽的权衡：48kHz/16bit 单通道 = 768 kbps，4 通道需要 3 Mbps。边缘处理后只上报事件可将带宽降到 < 1 kbps
- 混响环境（工厂车间 RT60 > 0.5s）严重影响定位精度，需要去混响预处理或使用 SRP-PHAT 算法
- 温度变化影响声速（±0.6 m/s/°C），户外长基线阵列需要实时声速补偿

## 参考文献

1. J. Benesty et al., "Microphone Array Signal Processing," Springer, 2008.
2. C. Knapp and G. Carter, "The generalized correlation method for estimation of time delay," IEEE Trans. Acoustics, Speech, and Signal Processing, vol. 24, no. 4, pp. 320-327, 1976.
3. J. F. Gemmeke et al., "Audio Set: An ontology and human-labeled dataset for audio events," IEEE ICASSP, pp. 776-780, 2017.
4. S. Adavanne et al., "Sound event localization and detection of overlapping sources using convolutional recurrent neural networks," IEEE JSTSP, vol. 13, pp. 34-48, 2019.
5. Y. Kong et al., "PANNs: Large-scale pretrained audio neural networks for audio pattern recognition," IEEE Trans. Audio, Speech, Language Processing, vol. 28, pp. 2880-2894, 2020.
6. Infineon, "IM69D130 High Performance MEMS Microphone Datasheet," 2023.
7. C. Grosse and M. Ohtsu, "Acoustic Emission Testing: Basics for Research," Springer, 2022.
8. M. Xu et al., "Edge AI for acoustic sensing in industrial IoT: A comprehensive survey," IEEE Internet of Things Journal, vol. 11, no. 12, pp. 21456-21478, 2024.
9. A. Mesaros et al., "Sound event detection: A tutorial," IEEE Signal Processing Magazine, vol. 38, no. 5, pp. 67-83, 2021.
10. R. Chiariotti et al., "Acoustic beamforming for noise source localization: Reviews, methodology and applications," Mechanical Systems and Signal Processing, vol. 120, pp. 422-448, 2019.
