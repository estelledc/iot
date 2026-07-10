---
schema_version: '1.0'
id: optical-sensors-iot
title: 光电传感器在 IoT 中的应用
layer: 1
content_type: UNKNOWN
difficulty: intermediate
reading_time: 19
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 光电传感器在 IoT 中的应用

> **难度**：🟡 中级 | **领域**：光电子、信号处理、智能感知 | **阅读时间**：约 19 分钟

## 日常类比

手机屏幕在阳光下自动调亮——这背后是一颗环境光传感器在工作。它本质上就是一个"数光子的计数器"：光子打到半导体材料上激发电子-空穴对，电流大小正比于光照强度。

再想想高速公路的自动收费闸机：红外对射传感器就像一条"看不见的绊线"，物体经过时切断光路，触发计数。从原理上看，所有光电传感器都在做同一件事——把光信号转换成电信号，只是灵敏度、速度、光谱范围各有侧重。

当我们把光电传感器接入 IoT 系统，就能实现远程环境感知（农业光照监测）、健康监测（光电容积脉搏波 PPG）、3D 空间测量（LiDAR）等智能场景。

## 1. 光电探测器基础

### 1.1 三种核心器件对比

| 器件 | 结构 | 增益 | 带宽 | 暗电流 | 典型应用 |
|------|------|------|------|--------|---------|
| 光电二极管 (PD) | PN/PIN 结 | 1× | DC–GHz | pA–nA | 光通信、光度计 |
| 光电晶体管 (PT) | BJT 无基极引线 | 100–1000× | DC–kHz | nA–μA | 开关检测、编码器 |
| 雪崩光电二极管 (APD) | 高反偏 PN 结 | 10–1000× | MHz–GHz | nA | LiDAR、单光子计数 |

### 1.2 光电转换物理

核心方程：光电流 I_ph = R × P_opt

其中 R 是响应度（A/W），P_opt 是入射光功率。响应度取决于量子效率 η：

```
R = η × q × λ / (h × c)

η: 量子效率 (0-1)，每个入射光子产生电子-空穴对的概率
q: 电子电荷 1.6×10⁻¹⁹ C
λ: 波长 (m)
h: 普朗克常数 6.63×10⁻³⁴ J·s
c: 光速 3×10⁸ m/s
```

**硅光电二极管**在 900 nm 处响应度最高（~0.6 A/W），可见光范围 400–700 nm 典型 0.2–0.5 A/W。

### 1.3 关键性能指标

```python
import numpy as np

def calculate_nep(dark_current_A, responsivity_AW, bandwidth_Hz):
    """
    计算噪声等效功率 NEP (W/√Hz)
    NEP = 光探测器刚好能检测到的最小光功率
    """
    # 散粒噪声电流（暗电流主导）
    q = 1.6e-19
    shot_noise = np.sqrt(2 * q * dark_current_A * bandwidth_Hz)
    
    # NEP = 噪声电流 / 响应度
    nep = shot_noise / responsivity_AW
    
    # 比探测率 D* (越大越好)
    # D* = √A / NEP，A 为探测器面积
    return nep

# 示例：PIN 光电二极管
nep = calculate_nep(
    dark_current_A=1e-9,     # 1 nA 暗电流
    responsivity_AW=0.5,     # 0.5 A/W @ 850nm
    bandwidth_Hz=1e6         # 1 MHz 带宽
)
print(f"NEP = {nep:.2e} W")  # ~3.6×10⁻¹⁴ W，非常灵敏
```

## 2. LiDAR 与飞行时间（ToF）

### 2.1 ToF 测距原理

LiDAR 发射激光脉冲，测量往返时间 Δt，距离 d = c·Δt/2。

两种主流方案：

| 方案 | 原理 | 精度 | 距离 | 成本 |
|------|------|------|------|------|
| dToF（直接 ToF） | 测脉冲往返时间 | ±1 cm | 0.1–200 m | 高 |
| iToF（间接 ToF） | 测调制光相位差 | ±1% | 0.1–10 m | 低 |

iToF 更适合 IoT（低成本、低功耗）。VL53L1X（ST 出品）是典型代表：

```c
// VL53L1X ToF 测距传感器 I2C 读取（STM32 HAL）
#include "vl53l1_api.h"

VL53L1_Dev_t dev;
VL53L1_RangingMeasurementData_t data;

void tof_init() {
    VL53L1_WaitDeviceBooted(&dev);
    VL53L1_DataInit(&dev);
    VL53L1_StaticInit(&dev);
    
    // 设置测距模式：短距（1.3m）/中距（3m）/长距（4m）
    VL53L1_SetDistanceMode(&dev, VL53L1_DISTANCEMODE_MEDIUM);
    // 设置测量周期 100ms
    VL53L1_SetMeasurementTimingBudgetMicroSeconds(&dev, 100000);
    VL53L1_StartMeasurement(&dev);
}

uint16_t tof_read_mm() {
    VL53L1_WaitMeasurementDataReady(&dev);
    VL53L1_GetRangingMeasurementData(&dev, &data);
    VL53L1_ClearInterruptAndStartMeasurement(&dev);
    
    if (data.RangeStatus == 0) {  // 有效测量
        return data.RangeMilliMeter;
    }
    return 0xFFFF;  // 无效
}
```

### 2.2 IoT LiDAR 应用

| 场景 | 传感器 | 分辨率 | 刷新率 | 功耗 |
|------|--------|--------|--------|------|
| 智能垃圾桶满溢检测 | VL53L0X | 单点 | 10 Hz | 20 mW |
| 人流计数 | VL53L5CX (8×8) | 64 区域 | 15 Hz | 60 mW |
| 仓储库位管理 | VL53L8 | 64 区域 | 30 Hz | 80 mW |
| 扫地机器人 | LDS-01 旋转雷达 | 360° / 1° | 5 Hz | 2.5 W |

### 2.3 多区域 ToF 的优势

VL53L5CX 提供 8×8 = 64 个测距区域，相当于低分辨率深度相机：

```python
import numpy as np

# 模拟 VL53L5CX 8×8 深度图处理
# 场景：检测是否有人经过门口

def detect_person(depth_frame_8x8, background_mm, threshold_mm=200):
    """
    基于深度变化检测人体通过
    depth_frame_8x8: 当前帧 8×8 深度值 (mm)
    background_mm: 背景参考帧
    threshold_mm: 判定有物体的深度差阈值
    """
    diff = background_mm - depth_frame_8x8  # 有物体则距离变近
    mask = diff > threshold_mm
    
    # 连通区域面积 > 4 个zone 判定为人
    object_pixels = np.sum(mask)
    
    if object_pixels >= 4:
        # 计算质心位置（追踪方向）
        rows, cols = np.where(mask)
        centroid_x = np.mean(cols) / 7.0  # 归一化到 0-1
        return True, centroid_x
    return False, None

# 双区域方向判定：通过质心在左→右移动判断进/出
```

## 3. 环境光传感（ALS）

### 3.1 人眼响应匹配

理想的 ALS 应该模拟人眼的光谱响应（明视觉函数 V(λ)，峰值 555 nm）。实际硅光电二极管的响应峰在 ~900 nm（红外），需要滤光片修正。

现代 ALS 芯片（如 VEML7700、TSL2591）内置双通道：

- 可见光通道（加绿色滤光片匹配 V(λ)）
- 全谱通道（含红外）

```python
# VEML7700 环境光传感器数据处理
# 输出单位: Lux

def veml7700_to_lux(als_raw, gain, integration_time_ms):
    """
    将原始计数转换为勒克斯
    resolution 取决于增益和积分时间
    """
    # 分辨率表 (lux/count)
    resolution_table = {
        (1, 100): 0.0576,
        (2, 100): 0.0288,
        (1, 200): 0.0288,
        (2, 200): 0.0144,
        (1, 400): 0.0144,
        (1, 800): 0.0072,
    }
    
    resolution = resolution_table.get((gain, integration_time_ms), 0.0576)
    lux = als_raw * resolution
    
    # 高亮度修正（>1000 lux 非线性）
    if lux > 1000:
        lux = 6.0135e-13 * lux**4 - 9.3924e-9 * lux**3 + \
              8.1488e-5 * lux**2 + 1.0023 * lux
    
    return lux

# 典型照度参考
# 月光: 0.5 lux | 办公室: 300-500 lux | 阴天户外: 10000 lux | 直射阳光: 100000 lux
```

### 3.2 自动增益切换

IoT 场景需要覆盖从 0.01 lux（星光）到 120,000 lux（烈日）的范围——动态范围超过 7 个数量级。解决方案是自动增益+积分时间切换：

| 照度范围 | 增益 | 积分时间 | 分辨率 |
|----------|------|----------|--------|
| 0–100 lux | ×2 | 800 ms | 0.0036 lux |
| 100–1,000 lux | ×1 | 100 ms | 0.0576 lux |
| 1,000–10,000 lux | ×1/4 | 25 ms | 0.9216 lux |
| > 10,000 lux | ×1/8 | 25 ms | 1.8432 lux |

## 4. 光电容积脉搏波（PPG）

### 4.1 原理

PPG 利用血液对绿光（~530 nm）吸收随心跳搏动而周期性变化的特性，测量脉搏波形。

```
LED (绿光 530nm)
    ↓ 照射皮肤
    ↓
    ├── 稳定分量 (DC): 骨骼、肌肉、静脉血 → 基线
    └── 搏动分量 (AC): 动脉血体积变化 → 脉搏波
         ↓
    光电二极管接收反射光
    AC/DC 比值 → 灌注指数 (PI)
```

### 4.2 IoT PPG 实现

```python
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

def process_ppg(raw_signal, fs=100):
    """
    PPG 信号处理：原始光电流 → 心率
    raw_signal: ADC 原始采样序列
    fs: 采样率 (Hz)
    """
    # 1. 带通滤波 (0.5-5 Hz，对应 30-300 BPM)
    b, a = butter(3, [0.5/(fs/2), 5.0/(fs/2)], btype='band')
    filtered = filtfilt(b, a, raw_signal)
    
    # 2. 归一化
    filtered = (filtered - np.mean(filtered)) / np.std(filtered)
    
    # 3. 峰值检测
    peaks, properties = find_peaks(
        filtered,
        distance=int(fs * 0.4),  # 最小峰间距 0.4s (= 150 BPM上限)
        height=0.3,              # 最小峰高
        prominence=0.5           # 最小突出度
    )
    
    # 4. 计算心率
    if len(peaks) >= 2:
        ibi = np.diff(peaks) / fs  # 搏动间期 (s)
        heart_rate = 60.0 / np.mean(ibi)
        hrv_sdnn = np.std(ibi) * 1000  # HRV-SDNN (ms)
    else:
        heart_rate = 0
        hrv_sdnn = 0
    
    return heart_rate, hrv_sdnn, peaks

# MAX30102 传感器配置要点：
# - 绿色 LED 电流: 6-20 mA (功耗主要来源)
# - 采样率: 100 Hz (心率) 或 400 Hz (SpO2)
# - ADC 分辨率: 18 位
# - 平均功耗: ~1 mW (低功耗模式)
```

### 4.3 运动伪影消除

佩戴者运动时，PPG 信号混入大量运动伪影（motion artifact）。解决方案：

- **加速度计参考**：同步采集 IMU 数据，用自适应滤波（LMS/RLS）消除
- **多波长方法**：绿光+红光+红外三通道，运动伪影相关但 PPG 分量不同
- **深度学习**：1D U-Net 端到端去噪，2024 年 benchmark 显示信噪比提升 8–12 dB

## 5. 光纤传感器

### 5.1 光纤布拉格光栅（FBG）

FBG 在光纤纤芯上刻写周期性折射率调制，反射特定波长（布拉格波长 λ_B = 2nΛ）。温度或应变改变 Λ，λ_B 随之漂移。

| 参数 | 典型值 |
|------|--------|
| 温度灵敏度 | ~10 pm/°C |
| 应变灵敏度 | ~1.2 pm/με |
| 波长精度 | ±1 pm |
| 单根光纤可串联 | 10–100 个 FBG |
| 传输距离 | 可达 100 km |

**IoT 应用**：桥梁结构健康监测、油气管道温度分布式感知、高压电缆温度监测。

### 5.2 分布式光纤传感（DFOS）

不需要特殊光栅——普通光纤本身就是传感器：

- **OTDR（瑞利散射）**：定位光纤断点/弯折，空间分辨率 ~1 m
- **布里渊散射**：测温度和应变，50 km 范围，分辨率 1 m
- **拉曼散射**：测温度，10 km 范围，精度 ±1°C

## 6. 光谱传感在农业中的应用

### 6.1 NDVI 植被指数

```python
def calculate_ndvi(nir_reflectance, red_reflectance):
    """
    归一化植被指数 NDVI = (NIR - Red) / (NIR + Red)
    健康绿叶: NDVI > 0.6
    枯萎/裸土: NDVI < 0.2
    """
    ndvi = (nir_reflectance - red_reflectance) / \
           (nir_reflectance + red_reflectance + 1e-10)
    return np.clip(ndvi, -1, 1)

# 多光谱传感器 AS7341 (AMS) — 11通道可见光+近红外
# 通道配置:
# F1(415nm), F2(445nm), F3(480nm), F4(515nm),
# F5(555nm), F6(590nm), F7(630nm), F8(680nm),
# Clear, NIR(910nm), Flicker
```

### 6.2 IoT 农业光谱方案

| 应用 | 传感器 | 关键波段 | 信息 |
|------|--------|---------|------|
| 叶绿素含量 | 双通道 PD + 滤光片 | 680nm, 740nm | 作物氮素状态 |
| 果实成熟度 | 微型近红外光谱仪 | 700–1100nm | 糖度 (Brix) |
| 土壤水分 | 1450nm LED + PD | 1450nm | 水分吸收峰 |
| 病害检测 | 高光谱相机 | 400–1000nm | 异常光谱特征 |

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：用 BH1750 数字环境光传感器（¥5）+ Arduino 做照度计，理解 lux 概念
2. **第二步**：MAX30102 模块（¥15）做心率检测，学习 PPG 信号处理
3. **第三步**：VL53L1X ToF 模块（¥25）做测距，体验 I2C 配置和时序预算
4. **第四步**：AS7341 多光谱传感器（¥40）做颜色/光谱分析
5. **进阶**：用光纤 + 耦合器搭建简易 OTDR 演示系统

### 7.2 具体调优建议

**提高信噪比（SNR）**：

- 增大积分时间（但降低了时间分辨率——需要权衡）
- 锁相放大：用调制光源 + 同频解调，抑制环境光干扰 > 60 dB
- 光学滤光：窄带干涉滤光片只通过目标波长，抑制背景
- 冷却探测器：每降 10°C 暗电流约减半（APD 场景）

**PPG 信号质量优化**：

- LED 与 PD 间距 4–8 mm（反射式最佳耦合距离）
- 绿光 LED 穿透深度 ~1 mm，适合手腕；红光/红外穿透更深，适合指尖
- 佩戴松紧影响大：太松漏光、太紧血流受阻——需要自适应 LED 电流调节
- 采样率 ≥ 25 Hz 才能分辨脉搏波形（推荐 100 Hz）

**LiDAR 精度优化**：

- 环境光干扰：加光学滤光片（940nm 窄带）+ 增大信号脉冲功率
- 多目标反射：使用直方图 ToF（统计多次测量分布）区分真实目标和杂散反射
- 温度补偿：SPAD 暗计数率随温度指数增长，需要修正

**功耗优化**：

- PPG：降低 LED 电流（低灌注时才需要高电流）
- ALS：低照度时增大积分时间（而非增益）更省电
- ToF：降低测量频率（人体检测 5 Hz 够用，不需要 30 Hz）

## 参考文献

1. Hamamatsu Photonics. (2024). Photodiode Technical Guide. 4th Edition.
2. STMicroelectronics. (2024). VL53L5CX Datasheet: Multizone ranging sensor. Rev 3.
3. Castaneda, D. et al. (2018). A review on wearable photoplethysmography sensors and their potential future applications. Sensors, 18(8), 2894.
4. AMS-OSRAM. (2024). AS7341 11-Channel Multi-Spectral Sensor Datasheet.
5. Measures, R. M. (2001). Structural Monitoring with Fiber Optic Technology. Academic Press.
6. Allen, J. (2007). Photoplethysmography and its application in clinical physiological measurement. Physiological Measurement, 28(3), R1.
7. Kim, J. et al. (2023). Motion artifact reduction in PPG using deep learning. IEEE J. Biomed. Health Informatics, 27(4), 1892–1903.
8. Raj, T. et al. (2020). A survey on LiDAR scanning mechanisms. Electronics, 9(5), 741.
9. Mulla, D. J. (2013). Twenty-five years of remote sensing in precision agriculture. Biosystems Engineering, 114(4), 358–371.
10. Bierman, A. et al. (2024). Ultra-low-power optical sensing for always-on IoT. Nature Electronics, 7(1), 45–53.
