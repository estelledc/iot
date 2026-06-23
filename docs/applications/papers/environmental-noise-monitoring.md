# 环境噪声监测物联网

> **难度**：🟡 中级 | **领域**：环境监测、智慧城市 | **阅读时间**：约 25 分钟

## 日常类比

你住的小区旁边开始修地铁了，每天早上六点准时被打桩机吵醒。你想投诉，但环保局说"需要提供噪声超标的证据"。你拿手机下了个分贝计 APP 测了一下——86 dB，确实很吵。但环保局又说"手机测的不算数，要用专业设备在规定测点连续监测"。

这就是传统噪声监测的困境：**设备贵、测点少、数据断**。一台专业声级计要几万块，一个城市可能只有十几个固定测点，数据只在检测时段有效。实际上噪声污染是动态的——交通噪声早晚高峰最严重，施工噪声白天最吵，夜间娱乐场所又是另一个高峰。

环境噪声监测物联网要做的就是：用低成本的 MEMS 麦克风阵列取代昂贵的专业设备，在城市中大规模布点（从十几个到几千个），实时采集、传输、分析噪声数据，生成动态噪声地图，自动识别噪声来源，并在超标时触发告警。这不仅帮市民维权，更为城市规划（道路设计、绿化带布局、建筑隔声设计）提供数据支撑。

## 1 噪声测量基础

### 1.1 分贝与加权

声压级（SPL）用分贝（dB）表示：SPL = 20×log₁₀(p/p₀)，其中 p₀ = 20 μPa（人耳听阈）。人耳对不同频率的灵敏度不同——对 1-4 kHz 最敏感，对低频和极高频不太敏感。为了让测量值反映人的主观感受，使用 A 加权（dBA）：

| 频率 (Hz) | A 加权修正 (dB) |
|-----------|----------------|
| 63 | -26.2 |
| 125 | -16.1 |
| 250 | -8.6 |
| 500 | -3.2 |
| 1000 | 0 |
| 2000 | +1.2 |
| 4000 | +1.0 |
| 8000 | -1.1 |

低频噪声（如变压器嗡嗡声、空调外机）被 A 加权大幅衰减，这也是为什么有些"听起来很吵"的低频噪声在 dBA 测量上不超标——这是 A 加权的局限性。

### 1.2 关键指标

环境噪声不是一个瞬时值，而是一个时间段的统计量：

```python
import numpy as np

def calculate_noise_metrics(dba_samples, sample_rate_hz, duration_s):
    """
    从连续 dBA 采样计算各类噪声指标
    dba_samples: 每个采样点的 A 加权声压级 (dBA)
    """
    # Leq: 等效连续声压级 (能量平均)
    # 这是最核心的指标, 表示"把起伏的噪声压平成一个恒定值"
    leq = 10 * np.log10(np.mean(10 ** (dba_samples / 10)))
    
    # Lmax / Lmin
    lmax = np.max(dba_samples)
    lmin = np.min(dba_samples)
    
    # 统计声级: LN 表示 N% 时间内超过的声压级
    l10 = np.percentile(dba_samples, 90)   # 10% 时间超过, 代表噪声峰值
    l50 = np.percentile(dba_samples, 50)   # 中位数, 代表背景水平
    l90 = np.percentile(dba_samples, 10)   # 90% 时间超过, 代表背景噪声
    
    # Lden: 日-晚-夜等效声级 (EU 指令核心指标)
    # 晚间(19-23h) +5dB 惩罚, 夜间(23-7h) +10dB 惩罚
    # 需要分时段计算, 此处简化示意
    
    return {
        'Leq': round(leq, 1),
        'Lmax': round(lmax, 1),
        'Lmin': round(lmin, 1),
        'L10': round(l10, 1),
        'L50': round(l50, 1),
        'L90': round(l90, 1),
    }
```

### 1.3 典型噪声水平参考

| 场景 | 声压级 (dBA) | 主观感受 |
|------|-------------|---------|
| 安静的图书馆 | 30-40 | 很安静 |
| 普通办公室 | 45-55 | 正常 |
| 城市主干道旁 | 70-80 | 吵闹，需要提高嗓门说话 |
| 建筑施工（10m） | 85-95 | 很吵，长期暴露损伤听力 |
| 飞机起飞（100m） | 110-130 | 疼痛感，瞬间损伤 |

WHO 建议：住宅区夜间 Lnight < 40 dBA，白天 Leq < 55 dBA。EU 环境噪声指令（2002/49/EC）要求主要城市绘制噪声地图，每 5 年更新一次。

## 2 传感器硬件

### 2.1 MEMS 麦克风 vs 传统声级计

传统 I 类精密声级计（如 B&K 2250）售价 3-5 万元，精度 ±0.7 dB，但体积大、需要手动操作。MEMS 麦克风（如 InvenSense ICS-43434）单价 < 10 元，可以做成小型化节点。

| 参数 | I 类声级计 | MEMS 节点 |
|------|-----------|-----------|
| 价格 | 3-5 万元 | 500-2000 元（含板卡） |
| 精度 | ±0.7 dB | ±1.5-3 dB |
| 频响 | 10 Hz - 20 kHz | 50 Hz - 20 kHz |
| 动态范围 | 20-140 dBA | 35-120 dBA |
| 自噪声 | <15 dBA | 26-33 dBA |
| 防水 | 需外壳 | 需外壳 |
| 校准 | NIST 可溯源 | 出厂校准 + 现场校准 |

MEMS 的精度能满足监测需求吗？对于噪声地图绘制（精度要求 ±3 dB），MEMS 完全够用。对于执法取证（精度要求 ±1 dB），则需要 II 类以上声级计或经过溯源校准的 MEMS 阵列。

### 2.2 节点硬件设计

```
典型噪声监测节点硬件组成:

MEMS 麦克风 (ICS-43434) ×2  (冗余 + 对比校准)
    ↓ I2S 数字音频接口
MCU (STM32L4 或 ESP32-S3)
    ↓
信号处理: A 加权滤波 → FFT → Leq 计算
    ↓
通信模块: LoRaWAN (SX1262) 或 NB-IoT (BC95)
    ↓
供电: 太阳能板 (5W) + 18650 锂电池 (×2)
    ↓
外壳: IP65 防水 + 防风罩 (减少风噪)
```

防风罩至关重要——风速 > 5 m/s 时，气流冲击麦克风会产生严重低频噪声（风噪），在 A 加权下可能叠加 5-15 dB 的误差。标准做法是用 90mm 直径的多孔泡沫球包裹麦克风。

## 3 噪声源识别

### 3.1 边缘 AI 分类

仅仅知道"噪声是 75 dBA"不够，管理部门需要知道"是交通噪声、施工噪声还是娱乐噪声"——不同来源的管理权限和标准不同。

基于音频频谱特征的分类方法：

```python
import librosa
import numpy as np
from tensorflow.keras.models import load_model

class NoiseSourceClassifier:
    """基于 Mel 频谱图 + CNN 的噪声源分类"""
    
    CLASSES = [
        'traffic',        # 交通噪声
        'construction',   # 施工噪声
        'aircraft',       # 飞机噪声
        'rail',           # 铁路噪声
        'entertainment',  # 娱乐噪声 (广场舞/KTV)
        'industrial',     # 工业噪声
        'nature',         # 自然声 (鸟叫/风声)
        'human_voice',    # 人声
    ]
    
    def __init__(self, model_path):
        self.model = load_model(model_path)
    
    def classify(self, audio_segment, sr=16000):
        """
        audio_segment: 5 秒音频片段
        返回: (类别, 置信度)
        """
        # 提取 Mel 频谱图 (128 个 Mel 频带)
        mel_spec = librosa.feature.melspectrogram(
            y=audio_segment, sr=sr,
            n_mels=128, fmax=8000
        )
        mel_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # 归一化到 [0, 1]
        mel_norm = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min())
        
        # CNN 推理
        input_tensor = mel_norm[np.newaxis, ..., np.newaxis]
        probs = self.model.predict(input_tensor)[0]
        
        class_idx = np.argmax(probs)
        return self.CLASSES[class_idx], float(probs[class_idx])
```

在 ESP32-S3 上用 TFLite 模型推理一个 5 秒音频片段约需要 200ms，功耗增加约 50mW——可以接受。

### 3.2 声源定位（阵列方法）

如果一个节点装了多个麦克风（阵列），还可以估算噪声来源方向：

- **2 麦克风**：利用到达时间差（TDOA）估算一维角度
- **4 麦克风正方形阵列**：估算二维方位角
- **精度**：麦克风间距 10cm，在 3kHz 频率下角度分辨率约 ±10°

## 4 噪声地图

### 4.1 从稀疏测点到连续地图

城市中只有有限的监测节点（通常每平方公里 1-5 个），但噪声地图需要覆盖每一条街道。填充方法：

**物理模型插值**：基于 ISO 9613-2 声传播模型，考虑声源（道路、工厂）位置、建筑物遮挡、地面反射、气象条件，计算每个网格点的预测声压级。监测节点数据用于校准模型参数。

**数据驱动插值**：用克里金插值（Kriging）或深度学习（如 U-Net）从稀疏观测推断全局分布。这种方法不需要详细的建筑三维模型，但需要较密的测点。

### 4.2 可视化平台

```python
# 噪声地图可视化 (Folium + 热力图)
import folium
from folium.plugins import HeatMap

def create_noise_map(sensor_data, center_lat, center_lon):
    """
    sensor_data: list of (lat, lon, leq_dba)
    生成交互式噪声热力图
    """
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=14,
        tiles='CartoDB positron'
    )
    
    # 将 dBA 转换为热力图权重
    heat_data = []
    for lat, lon, leq in sensor_data:
        # 归一化: 40 dBA → 0, 85 dBA → 1
        weight = max(0, min(1, (leq - 40) / 45))
        heat_data.append([lat, lon, weight])
    
    HeatMap(
        heat_data,
        radius=25,
        blur=15,
        gradient={0.2: 'green', 0.5: 'yellow', 0.7: 'orange', 1.0: 'red'},
        min_opacity=0.3,
    ).add_to(m)
    
    # 添加传感器标记
    for lat, lon, leq in sensor_data:
        color = 'green' if leq < 55 else 'orange' if leq < 70 else 'red'
        folium.CircleMarker(
            [lat, lon], radius=6, color=color,
            popup=f'Leq: {leq} dBA'
        ).add_to(m)
    
    return m
```

## 5 法规标准与合规

### 5.1 中国标准

中国环境噪声标准 GB 3096-2008 将功能区分为 5 类：

| 类别 | 适用区域 | 昼间限值 | 夜间限值 |
|------|----------|----------|----------|
| 0 类 | 疗养区、高级住宅 | 50 dBA | 40 dBA |
| 1 类 | 居住、文教区 | 55 dBA | 45 dBA |
| 2 类 | 商住混合区 | 60 dBA | 50 dBA |
| 3 类 | 工业区 | 65 dBA | 55 dBA |
| 4a 类 | 交通干线两侧 | 70 dBA | 55 dBA |
| 4b 类 | 铁路干线两侧 | 70 dBA | 60 dBA |

昼间指 6:00-22:00，夜间指 22:00-6:00。施工噪声另行规定（GB 12523-2011）：夜间禁止施工（确需施工要审批）。

### 5.2 公众参与

"公民科学"模式让市民用自己的手机参与噪声监测，扩大数据覆盖面。欧盟的 NoiseCapture 项目是一个成功案例——APP 免费，采集的数据匿名上传到公共数据库。截至 2024 年已收集 200 万+ 测量记录，覆盖 180 个国家。

手机测噪声的精度问题：不同手机的麦克风灵敏度和频响差异很大。解决方案是让用户用一个已知声级（如用另一台校准设备播放 94 dB/1kHz 校准音）做一次校准，之后用校准系数修正。校准后精度可达 ±2-3 dBA。

## 6 智慧城市集成

### 6.1 噪声数据驱动的决策

噪声监测数据不是孤立存在的，它和其他城市数据结合后能产生更大价值：

**交通管理**：噪声数据与交通流量数据关联——某条道路夜间 Leq > 55 dBA 且交通流量 > 500 辆/小时，建议设置限速或安装隔声屏障。深圳已经在 106 条道路安装了噪声监测与交通管控联动系统。

**城市规划**：新建住宅区选址时，噪声地图是重要参考——避免在高噪声区域（机场跑道延长线、高速公路两侧）建设住宅。

**健康研究**：长期噪声暴露与心血管疾病、睡眠障碍、认知能力下降的关联已被多项研究证实。WHO 2018 年指南指出：Lnight > 45 dBA 时心血管疾病风险显著增加。

### 6.2 与其他 IoT 系统联动

噪声数据可以与空气质量监测、气象站、摄像头等其他 IoT 系统打通。例如：噪声突增 + 空气颗粒物突增 → 可能是附近有违规施工；噪声突降 + 交通流量正常 → 可能是监测设备故障。多源数据融合提高了事件检测的准确性和可信度。

## 7 实践建议

### 7.1 初学者入门路径

1. **手机体验**：下载 NIOSH SLM APP（iOS）或 NoiseCapture（Android），实际测量不同环境的噪声水平，建立直觉
2. **硬件 DIY**：用 ESP32 + INMP441 MEMS 麦克风（约 15 元），写一个实时 dBA 显示器——关键是实现 A 加权滤波
3. **数据分析**：在一个固定地点连续采集 24 小时数据，画出噪声的日变化曲线，计算 Leq、L10、L90 等指标
4. **噪声地图**：在校园或小区布置 3-5 个节点，用 Folium 或 Google Maps API 做一张噪声热力图
5. **AI 分类**：用 ESC-50 或 UrbanSound8K 公开数据集训练一个噪声源分类模型，部署到 ESP32-S3

### 7.2 具体调优建议

**防风罩**：户外部署必须加防风罩。没有防风罩的裸麦克风在 5 m/s 风速下低频噪声可增加 20 dB+。推荐 Rycote 泡沫防风罩或自制开孔泡沫球。

**校准周期**：MEMS 麦克风每 6 个月用校准器（如 B&K 4231，94 dB/1kHz）做一次现场校准。不校准的话，精度会随温度和老化漂移 2-5 dB。

**采样率选择**：环境噪声频率范围主要在 20 Hz - 10 kHz，所以 20 kHz 采样率（奈奎斯特定理要求 2 倍最高频率）就够了。16 kHz 采样率覆盖到 8 kHz，对于多数交通/施工噪声已足够。

**数据传输优化**：不要传输原始音频——16kHz/16bit 音频数据率 = 256 kbps，LoRa 传不了。应该在节点本地计算 Leq、频谱、分类结果，每分钟上报一次结构化数据（约 100 字节）。

## 参考文献

1. WHO. Environmental Noise Guidelines for the European Region. WHO Regional Office for Europe, 2018.
2. European Commission. Directive 2002/49/EC relating to the Assessment and Management of Environmental Noise. 2002.
3. GB 3096-2008. 声环境质量标准. 中国国家标准, 2008.
4. Picaut J, et al. An Open-Science Crowdsourcing Approach for Producing Community Noise Maps Using Smartphones. Building and Environment, 2019.
5. Mydlarz C, et al. The Life of a New York City Noise Sensor Network. Sensors, 2019, 19(6): 1415.
6. InvenSense. ICS-43434 Multi-Mode Microphone with I2S Digital Output. Datasheet, 2023.
7. Bello JP, et al. SONYC: A System for Monitoring, Analyzing, and Mitigating Urban Noise Pollution. Communications of the ACM, 2019, 62(2): 68-77.
8. ISO 9613-2. Acoustics — Attenuation of Sound During Propagation Outdoors. 2024 revision.
9. Salamon J, et al. A Dataset and Taxonomy for Urban Sound Research. ACM Multimedia, 2014.
10. 深圳市生态环境局. 深圳市噪声监测与交通管控联动系统建设报告. 2024.
