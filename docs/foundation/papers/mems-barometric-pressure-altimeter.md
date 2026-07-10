---
schema_version: '1.0'
id: mems-barometric-pressure-altimeter
title: MEMS气压计高度测量原理与温度补偿
layer: 1
content_type: UNKNOWN
difficulty: UNKNOWN
reading_time: UNKNOWN
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# MEMS气压计高度测量原理与温度补偿

> 技术分析 | 难度：🟡 中级 | 气压测量 · 高度计算 · 导航定位

---

## 引言

假设你站在一栋30层大楼的底层，想知道自己具体在几楼。GPS在室内几乎废掉，WiFi指纹又不够精确——但有一个物理量始终随高度规律变化：**大气压**。每升高约8.5米，气压下降约1 hPa。MEMS气压计正是利用这一规律，把看不见的气压变化变成看得见的高度数字。

---

## 大气压与高度的关系

### 日常类比：叠被子与气压

想象大气层是一叠棉被。最底层承受了上面所有棉被的重量，压得最实（气压最高）；越往上压着的越少，越蓬松（气压越低）。

### 气压公式（Barometric Formula）

对流层内（0\~11 km），标准大气模型（ISA）下：

$$
P(h) = P_0 \cdot \left(1 - \frac{L \cdot h}{T_0}\right)^{\frac{g \cdot M}{R \cdot L}}
$$

| 符号 | 含义 | 标准值 |
|------|------|--------|
| \(P_0\) | 海平面标准气压 | 101325 Pa |
| \(T_0\) | 海平面标准温度 | 288.15 K (15°C) |
| \(L\) | 温度递减率 | 0.0065 K/m |
| \(g\) | 重力加速度 | 9.80665 m/s² |
| \(M\) | 干空气摩尔质量 | 0.0289644 kg/mol |
| \(R\) | 通用气体常数 | 8.31447 J/(mol·K) |

代入标准值后指数部分 \(\approx 5.255\)，简化为：

$$
P(h) = P_0 \cdot \left(1 - \frac{h}{44330}\right)^{5.255}
$$

**经验法则**：低海拔区域，**1 hPa 气压变化 ≈ 8.5 m 高度变化**。

---

## MEMS气压传感原理

### 日常类比：鼓面与气压

把传感器核心想象成一面小鼓。鼓面（薄膜）一侧暴露在环境气压中，另一侧密封为真空参考腔。气压变大，鼓面往里凹；气压变小，往外鼓。检测鼓面形变即检测气压。

### 压阻式（Piezoresistive）

在硅薄膜上嵌入压敏电阻（惠斯通电桥）。薄膜弯曲时电阻值因压阻效应改变，电桥输出与气压成正比。结构简单、线性度好，但**温度敏感性高**——硅的压阻系数随温度变化显著。代表：Bosch BMP280、BMP390。

### 电容式（Capacitive）

薄膜与固定电极构成平行板电容器。薄膜位移导致极板间距变化，电容值随之改变。温度稳定性优于压阻式（电容值对温度不敏感），噪声更低，但电路更复杂。代表：Infineon DPS310。

### 两种原理对比

| 特性 | 压阻式 | 电容式 |
|------|--------|--------|
| 温度敏感性 | 高（需强补偿） | 低（天然优势） |
| 噪声水平 | 中等 | 更低 |
| 电路复杂度 | 低 | 较高 |
| 功耗 | 低 | 中等 |
| 长期稳定性 | 中等 | 较好 |
| 代表芯片 | BMP280/BMP390 | DPS310 |

---

## 主流MEMS气压芯片对比

| 参数 | BMP280 | BMP390 | DPS310 |
|------|--------|--------|--------|
| 厂商 | Bosch | Bosch | Infineon |
| 传感原理 | 压阻式 | 压阻式 | 电容式 |
| 量程 | 300\~1100 hPa | 300\~1250 hPa | 300\~1200 hPa |
| 相对精度 | ±0.12 hPa | ±0.08 hPa | ±0.06 hPa |
| 绝对精度 | ±1 hPa | ±0.5 hPa | ±1 hPa |
| 分辨率 | 0.01 hPa | 0.01 hPa | 0.001 hPa |
| 等效高度精度 | ±1 m | ±0.5 m | ±0.5 m |
| TCO | ±1.5 Pa/K | ±0.7 Pa/K | ±0.5 Pa/K |
| 封装 | 2.0×2.5 mm | 2.0×2.0 mm | 2.0×2.5 mm |
| 电流（1Hz） | 2.7 μA | 3.4 μA | 3 μA |
| FIFO | 无 | 512 字节 | 32 帧 |
| 参考价格 | ¥6\~8 | ¥12\~15 | ¥8\~12 |

**选型**：低成本天气站选BMP280；无人机高度计选BMP390（TCO优、有FIFO）；室内楼层检测选DPS310（分辨率最高、温漂最小）；可穿戴选BMP390（封装最小2×2 mm）。

---

## 从气压计算高度

### 压高公式（Hypsometric Equation）

气压公式的逆运算——从气压反推高度：

$$
h = 44330 \cdot \left[1 - \left(\frac{P}{P_0}\right)^{0.1903}\right]
$$

### 考虑实际温度的修正

标准模型假设温度递减率为常数，实际有偏差。引入实测温度 \(T\)：

$$
\Delta h = \frac{T \cdot R}{g \cdot M} \cdot \ln\left(\frac{P_1}{P_2}\right)
$$

这是**相对高度测量**的基础——不依赖海平面气压绝对值，只看两个位置的气压差。

### 海平面气压校准

绝对高度依赖 \(P_0\)，而 \(P_0\) 随天气变化。常见校准方法：已知高度点反算、在线气象数据获取、差分双传感器消除天气影响。

---

## 温度补偿方法

### 日常类比：钢卷尺的热胀冷缩

一把钢卷尺在夏天和冬天长度不同。MEMS传感器的硅薄膜和压敏电阻同样"热胀冷缩"——温度变化导致的信号偏移，可能远大于实际气压变化。BMP280的TCO为±1.5 Pa/K，温度变化30°C可偏移±45 Pa，等效高度误差约±3.8 m，远超传感器本身的±1 m精度。

### 芯片内置补偿

每颗芯片出厂逐个校准，补偿系数写入NVM。BMP280含6个系数（T1\~T3, P1\~P9），BMP390扩展到11个，用户按厂商库调用即可。

### 外部二次补偿

| 方法 | 原理 | 适用场景 |
|------|------|----------|
| 查表法 | 不同温度点实测偏移，建查找表 | 温度范围小、批量大 |
| 多项式拟合 | 温度-偏移数据做最小二乘拟合 | 有足够校准样本 |
| 差分双传感器 | 两颗同型号取差值，抵消共模温漂 | 高精度仪表 |
| Kalman滤波 | 温度漂移建模为状态量，与气压联合估计 | 动态场景 |

---

## 噪声与分辨率提升

噪声来源：热机械噪声（硅薄膜布朗运动）、ADC量化噪声、环境扰动（风、气流）。

### 过采样（Oversampling）

多次采样取平均，噪声降低 \(\sqrt{N}\) 倍：

| 设置 | 倍数 | 推荐应用 |
|------|------|----------|
| Ultra-low power | ×1 | 天气趋势 |
| Standard | ×4 | 通用 |
| High | ×8 | 导航 |
| Ultra-high | ×16 | 精密高度计 |

### IIR低通滤波器

对连续采样做指数加权平均：\(y[n] = \alpha \cdot x[n] + (1 - \alpha) \cdot y[n-1]\)

| 系数 | 等效时间常数 | 效果 |
|------|-------------|------|
| 0 | — | 无滤波，响应最快 |
| 4 | ~5周期 | 中度平滑 |
| 16 | ~23周期 | 强平滑，适合静态场景 |

### 推荐组合

| 场景 | 过采样 | IIR | 典型噪声 |
|------|--------|-----|---------|
| 天气监测 | ×1 | 关闭 | ±2.4 hPa |
| 户外导航 | ×4 | 4 | ±0.3 hPa |
| 无人机 | ×8 | 8 | ±0.15 hPa |
| 室内楼层 | ×16 | 16 | ±0.05 hPa |

---

## 代码示例：BMP280高度计算

基于ESP32 + Adafruit库，演示绝对高度和相对高度计算：

```cpp
#include <Wire.h>
#include <Adafruit_BMP280.h>

Adafruit_BMP280 bmp;
float seaLevelPressure = 1013.25;   // 海平面气压（hPa）
float referencePressure = 0.0;      // 启动时基准气压
bool  baselineSet = false;

void setup() {
    Serial.begin(115200);
    if (!bmp.begin(0x76)) {
        Serial.println("BMP280 未找到!");
        while (1) delay(10);
    }
    bmp.setSampling(
        Adafruit_BMP280::MODE_NORMAL,
        Adafruit_BMP280::SAMPLING_X16,   // 气压过采样 ×16
        Adafruit_BMP280::SAMPLING_X16,   // 温度过采样 ×16
        Adafruit_BMP280::FILTER_X16,     // IIR 系数 16
        Adafruit_BMP280::STANDBY_MS_1
    );
    delay(100);
}

void loop() {
    float temp = bmp.readTemperature();
    float pres = bmp.readPressure() / 100.0F;   // Pa → hPa
    float absAlt = bmp.readAltitude(seaLevelPressure);

    if (!baselineSet) { referencePressure = pres; baselineSet = true; }
    float relAlt = calcRelativeAltitude(referencePressure, pres, temp);

    Serial.printf("T:%.1fC P:%.2fhPa Abs:%.1fm Rel:%.2fm\n",
                  temp, pres, absAlt, relAlt);
    delay(500);
}

// 基于实际温度的相对高度（压高公式）
float calcRelativeAltitude(float p1, float p2, float tempC) {
    float T = tempC + 273.15;
    const float R = 8.31447, g = 9.80665, M = 0.0289644;
    return (T * R) / (g * M) * log(p1 / p2);
}
```

---

## 室内楼层检测算法

### 挑战

楼层高度不统一（住宅2.8 m，商业4\~6 m）；HVAC系统造成1\~3 hPa局部气压波动；电梯快速升降时气压滞后；天气漂移几小时可达5\~10 hPa。

### 基于差分气压的楼层检测

核心思想：**不依赖绝对气压，只看气压变化量是否超过一个楼层的阈值**。

```
#define FLOOR_HEIGHT_PA    4.0   // 每层约4 hPa（≈3.4m层高）
#define DEBOUNCE_SAMPLES   5     // 连续5次确认才判定换层
#define HYSTERESIS_PA      1.0   // 滞后窗口

class FloorDetector {
private:
    float groundPressure;
    int   currentFloor, pendingCount, pendingDirection;
    static const int BUF = 8;
    float pBuf[BUF]; int idx=0; bool full=false;

    float movingAvg(float p) {
        pBuf[idx] = p; idx = (idx+1) % BUF;
        full = full || (idx == 0);
        float s = 0; int n = full ? BUF : idx;
        for (int i=0; i<n; i++) s += pBuf[i];
        return s / n;
    }
public:
    void begin(float p0) {
        groundPressure = p0; currentFloor = 1;
        pendingCount = 0; pendingDirection = 0;
    }
    int update(float rawP) {
        float p = movingAvg(rawP);
        float delta = groundPressure - p;
        float est = 1.0 + delta / FLOOR_HEIGHT_PA;
        float err = est - currentFloor;
        int dir = 0;
        if (err >  0.5 + HYSTERESIS_PA/FLOOR_HEIGHT_PA) dir = +1;
        if (err < -0.5 - HYSTERESIS_PA/FLOOR_HEIGHT_PA) dir = -1;
        if (dir && dir == pendingDirection) pendingCount++;
        else { pendingDirection = dir; pendingCount = 1; }
        if (pendingCount >= DEBOUNCE_SAMPLES) {
            currentFloor += pendingDirection;
            groundPressure = p + (currentFloor-1) * FLOOR_HEIGHT_PA;
            pendingCount = 0; pendingDirection = 0;
        }
        return currentFloor;
    }
};
```

**设计要点**：8点滑动平均抑波动；滞后窗口防边界抖动；连续5次确认防电梯误判；换层后微调基准抗天气漂移。进阶可融合IMU检测电梯运动、Kalman联合估计、气压指纹库匹配、差分双气压计消除共模漂移。

---

## IoT应用场景

### 无人机高度计

BMP390凭±0.08 hPa相对精度和低TCO成为消费级无人机主流。典型：过采样×8 + IIR系数4，配合IMU做Kalman融合，高度精度±0.3 m。

### 运动手环/手表

BMP280低功耗模式（1Hz仅2.7 μA）首选。静态降采样率至0.5 Hz，运动时提升至4 Hz；相对高度即满足需求。

### 天气站

| 气压变化 | 趋势 | 天气预判 |
|----------|------|----------|
| >3 hPa/3h 下降 | 急降 | 暴风雨将至 |
| 1\~3 hPa/3h 下降 | 缓降 | 转阴或小雨 |
| 稳定 | 平稳 | 天气持续 |
| 1\~3 hPa/3h 上升 | 缓升 | 天气转好 |

天气站必须校准到海平面气压（QNH），不同海拔读数才可横向比较。

### 室内导航

气压计提供垂直维度，与WiFi/BLE指纹、IMU融合实现3D定位。每栋楼HVAC特性不同需单独校准；电梯井内气压波动需特殊处理；多设备协作时固定一台做参考站消除天气漂移。

---

## 总结与展望

1. **气压与高度**的关系是确定性物理规律，压高公式是从气压到高度的桥梁
2. **MEMS气压传感器**分压阻式和电容式，前者简单廉价，后者温漂更小
3. **温度补偿**是精度关键——内置补偿消主要误差，二次补偿满足高精度需求
4. **过采样+IIR**是提升分辨率的标配，代价是延迟和功耗
5. **相对高度**比绝对高度更可靠——差分测量天然消除天气漂移
6. **楼层检测**需防抖、滞后、基准校正等工程技巧，细节决定成败

**趋势**：BMP585已达0.01 hPa分辨率（等效8 cm），接近楼梯单级高度；气压+IMU+UWB紧耦合向厘米级推进；AI辅助校准自适应HVAC特性；新一代芯片功耗降至1 μA以下支持能量收集；SensorThings API等标准逐步纳入气压高度语义。

---

## 参考资料

1. Bosch Sensortec. *BMP280 Datasheet* (BST-BMP280-DS001). 2023.
2. Bosch Sensortec. *BMP390 Datasheet* (BST-BMP390-DS001). 2022.
3. Infineon Technologies. *DPS310 Data Sheet* (AB-000796). 2023.
4. ICAO. *Manual of the ICAO Standard Atmosphere*, Doc 7488. 1993.
5. Wallace & Hobbs. *Atmospheric Science*, 2nd ed. Academic Press, 2006.
6. Mok & Yuen. "Barometer for Floor Assignation in Indoor Positioning." *Sensors*, 23(1), 2023.
7. Parés et al. "Assessment of BMP388 Microbarometric MEMS Sensor." *Geofizicheskiy Zhurnal*, 2024.
8. 霍尼韦尔. *MEMS压力传感器设计与应用白皮书*. 2021.
