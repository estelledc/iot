---
schema_version: '1.0'
id: load-cell-hx711-interface
title: 称重传感器与HX711 ADC接口设计
layer: 1
content_type: UNKNOWN
difficulty: beginner
reading_time: 15
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 称重传感器与HX711 ADC接口设计

> **难度**：🟢 初级 | **领域**：力传感、称重系统、嵌入式接口 | **阅读时间**：约 15 分钟

## 日常类比

你站在商场电子秤上，屏幕跳出体重数字。背后是一套精密的力-电转换链：你踩下去，秤台下方的金属梁微微弯曲，贴在梁上的应变片跟着变形，电阻发生微小变化，惠斯通电桥把电阻变化转成毫伏级电压，最后 HX711 芯片把这个微弱信号放大 128 倍并转换成 24 位数字——MCU 读到的就是你能理解的"公斤数"。

整个过程像一个翻译链：力 → 形变 → 电阻变化 → 电压变化 → 数字。每一环都有精度损失，好的设计就是让每一环都足够可靠。

---

## 1. 称重传感器类型

称重传感器（Load Cell）将力/重量转换为电信号，核心原理是电阻应变效应。

### 1.1 悬臂梁式（Beam）

金属梁一端固定，另一端受力，上下表面分别产生拉伸和压缩应变。最常用的结构。

- 量程：1 kg ~ 500 kg，精度 0.02% ~ 0.05% FS
- 安装简单（四颗螺丝），输出信号大（2 mV/V 典型值）

日常类比：一端夹在桌沿的长条木板，另一端挂重物——挂得越重，弯得越厉害。传感器就是精确测量这根"木板"弯了多少。

### 1.2 S 型（S-Type）

外形像字母"S"，受力时中间段产生剪切变形。可测拉力和压力（双向），抗偏载能力强。

- 量程：5 kg ~ 20 t，精度 0.02% ~ 0.03% FS

### 1.3 轮辐式 / 饼式（Pancake）

外形扁平如圆饼，内部像车轮辐条，受力时辐条产生剪切应变。抗偏载和侧向力极强，高度低。

- 量程：100 kg ~ 500 t，精度 0.03% ~ 0.05% FS

### 1.4 类型对比

| 特性 | 悬臂梁式 | S 型 | 轮辐式 |
|------|----------|------|--------|
| 量程范围 | 1 kg ~ 500 kg | 5 kg ~ 20 t | 100 kg ~ 500 t |
| 精度 | 0.02% ~ 0.05% | 0.02% ~ 0.03% | 0.03% ~ 0.05% |
| 灵敏度（典型） | 2 mV/V | 2 mV/V | 1.5 mV/V |
| 抗偏载 | 中 | 强 | 极强 |
| 成本 | 低 | 中 | 高 |
| 典型应用 | 电子秤、料斗 | 吊秤、测力机 | 汽车衡、大吨位 |

---

## 2. 称重传感器内部的应变片电桥

### 2.1 四片全桥结构

传感器内部贴有 4 枚应变片，组成惠斯通全桥。两片贴在受拉区，两片贴在受压区，四个臂的电阻变化叠加输出。

```
    Vex (+)
     |
    [R1: 拉]     [R2: 压]
     |              |
     +---- Vo+ ----+
     |              |
    [R3: 压]     [R4: 拉]
     |              |
    GND            GND
```

受力时 R1、R4 被拉伸（电阻增大），R2、R3 被压缩（电阻减小）。简化后输出电压：

$$
V_o \approx V_{ex} \cdot GF \cdot \varepsilon
$$

### 2.2 灵敏度参数

灵敏度（额定输出）单位 mV/V——满量程载荷下，每 1V 激励电压产生的输出电压：

- 典型值：1 mV/V ~ 3 mV/V，最常见 2 mV/V
- 示例：5V 激励、2 mV/V → 满量程输出仅 10 mV

10 mV 有多小？AA 电池 1.5V 的 1/150。这就是为什么需要专用高精度 ADC。

### 2.3 四线 vs 六线接线

| 接线方式 | 线数 | 特点 | 适用场景 |
|----------|------|------|----------|
| 四线制 | 4（E+, E-, S+, S-） | 简单，导线电阻影响激励电压 | 短距离、低成本 |
| 六线制 | 6（+Sense, -Sense 额外两根） | 反馈远端实际电压，补偿线损 | 远距离、高精度 |

日常类比：四线制像给远处送外卖，路上消耗不知道多少；六线制多派一个人报告"到地方还剩多少"，据此补偿。

---

## 3. HX711 24 位 ADC 架构

### 3.1 为什么需要专用 ADC？

| 参数 | MCU 内置 10 位 ADC | HX711 |
|------|-------------------|-------|
| 分辨率 | 10 位（1024 级） | 24 位（16M 级） |
| 有效位数 | ~9 bit | ~20 bit |
| 输入范围 | 0 ~ Vref | ±20 mV（增益 128） |
| 内置 PGA | 无 | 有（128/64/32） |

### 3.2 内部结构

```
称重传感器 ──→ [多路复用器] ──→ [PGA] ──→ [Σ-Δ ADC] ──→ [输出寄存器]
               Ch_A / Ch_B     ×128/64/32   24-bit         SDA/SCK
```

集成了模拟多路复用器、可编程增益放大器、24 位 Σ-Δ ADC、片上振荡器和两线制串行接口。

### 3.3 增益选择

| 通道 | 增益 | 输入范围 | 噪声 | 典型用途 |
|------|------|----------|------|----------|
| A | 128 | ±20 mV | 0.5 LSB rms | **称重主通道**（最常用） |
| A | 64 | ±40 mV | 1.0 LSB rms | 大信号场景 |
| B | 32 | ±80 mV | 2.0 LSB rms | 温度补偿（接热敏电阻） |

日常类比：增益像显微镜倍数。128 倍看细菌——最微小变化也能看到，但视野只有 ±20 mV。32 倍像普通放大镜，视野大但细节少。

数据速率：10 Hz（默认，静态称重）或 80 Hz（动态称重），通过 RATE 引脚选择。

---

## 4. 时序协议：非标准串行通信

### 4.1 为什么不用 I2C 或 SPI？

HX711 使用自定义两线制协议，不是 I2C 也不是 SPI。原因：只需两根 GPIO、不需要地址、低速足够（10~80 Hz）、省去协议栈降低成本。

### 4.2 通信时序

```
          ┌───┐   ┌───┐   ┌───┐       ┌───┐   ┌───┐
PD_SCK ───┘   └───┘   └───┘   └─ ... └───┘   └───┘─── 25~27 pulses
          ↑   ↑   ↑   ↑   ↑   ↑       ↑   ↑   ↑   ↑
DOUT  ────┘   └───┘   └───┘   └─ ... └───┘   └───┘   Data bits
         b23  b22  b21  b20      b2   b1   b0  gain
```

**读取流程**：

1. 等待 DOUT 拉低（数据就绪）
2. 发 25 个脉冲 → 读 24 位数据（通道 A 增益 128）
3. 发 26 个脉冲 → 读 24 位数据（通道 A 增益 64）
4. 发 27 个脉冲 → 读 24 位数据（通道 B 增益 32）

每个 SCK 上升沿输出一位数据，MSB 在先。注意：SCK 高电平不宜超过 60 μs，否则进入掉电模式。

---

## 5. 校准流程

### 5.1 为什么需要校准？

HX711 输出原始 ADC 值，不是重量。不同传感器灵敏度有差异，校准就是找原始值到真实重量的映射。

日常类比：买了新体温计，得先用标准温度点标定刻度。校准就是在秤上放已知砝码，让系统记住"这个 ADC 值 = 这个重量"。

### 5.2 两点校准法

$$
W = \frac{Raw - Tare}{ScaleFactor}
$$

- `Tare`：空载 ADC 读数（去皮值）
- `ScaleFactor`：每单位重量对应的 ADC 计数

**操作步骤**：

1. 空载读 ADC 值，记为 `Tare`
2. 放已知重量 `W_cal` 的砝码，读 ADC 值 `Raw_cal`
3. 计算：`ScaleFactor = (Raw_cal - Tare) / W_cal`

示例：空载 `Tare = 85000`，放 1 kg 砝码后 `Raw_cal = 180000`，则 `ScaleFactor = 95.0` ADC 计数/克。

### 5.3 校准注意

- 砝码精度至少是目标精度的 3 倍
- 预热 10~15 分钟后再校准
- 多次采样取平均；ScaleFactor 存 EEPROM 断电不丢
- 温度变化大的环境建议每周复校

---

## 6. 代码示例：Arduino 称重测量

基于 `bogde/HX711` 库。

### 6.1 接线

```
Arduino    HX711 模块    称重传感器
  D2  ────  DOUT
  D3  ────  PD_SCK
  5V  ────  VCC
  GND ────  GND
              E+  ────  红 (激励+)
              E-  ────  黑 (激励-)
              A-  ────  白 (信号-)
              A+  ────  绿 (信号+)
```

### 6.2 称重代码

```cpp
#include <HX711.h>

const int DOUT_PIN = 2;
const int SCK_PIN  = 3;
const long TARE_OFFSET   = 85000;   // 校准后填入
const float SCALE_FACTOR  = 95.0;   // ADC 计数 / 克

HX711 scale;

void setup() {
  Serial.begin(9600);
  scale.begin(DOUT_PIN, SCK_PIN);
  scale.set_gain(128);               // 通道 A，增益 128
  scale.set_offset(TARE_OFFSET);
  scale.set_scale(SCALE_FACTOR);
  delay(2000);                       // 等待传感器稳定
  scale.tare(10);                    // 10 次采样去皮
  Serial.println("去皮完成，可以称重！");
}

void loop() {
  if (scale.is_ready()) {
    float weight_g = scale.get_units(5);  // 5 次平均
    Serial.print("重量: ");
    Serial.print(weight_g, 1);
    Serial.println(" g");
    delay(500);
  }
}
```

### 6.3 校准代码

```cpp
#include <HX711.h>
const int DOUT_PIN = 2, SCK_PIN = 3;
HX711 scale;

void setup() {
  Serial.begin(9600);
  scale.begin(DOUT_PIN, SCK_PIN);
  Serial.println("输入 't' 去皮 | 'c' 校准 | 'r' 读原始值");
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 't') {
      scale.tare(10);
      Serial.print("去皮完成, offset="); Serial.println(scale.get_offset());
    }
    else if (cmd == 'c') {
      Serial.println("输入砝码重量(克):");
      while (!Serial.available()) delay(100);
      float w = Serial.parseFloat();
      scale.calibrate_scale(w, 10);
      Serial.print("scale="); Serial.print(scale.get_scale(), 2);
      Serial.print(" offset="); Serial.println(scale.get_offset());
    }
    else if (cmd == 'r') {
      Serial.print("raw="); Serial.print(scale.read());
      Serial.print(" avg="); Serial.println(scale.read_average(10));
    }
  }
}
```

---

## 7. ADC 选项对比

| 特性 | HX711 | NAU7802 | ADS1232 |
|------|-------|---------|---------|
| 分辨率 | 24 bit | 24 bit | 24 bit |
| 通道数 | 2（A/B） | 2（差分） | 1 |
| PGA 增益 | 128/64/32 | 1~128 可编程 | 128/64 |
| 接口 | 自定义两线 | I2C | 自定义两线 |
| 数据速率 | 10/80 SPS | 10~320 SPS | 10/80 SPS |
| 工作电压 | 2.7~5.5V | 2.4~5.5V | 2.6~5.5V |
| 内置 LDO | 有 | 有 | 无 |
| 温度传感器 | 无 | 有（内置） | 无 |
| 参考价格 | ¥2~5 | ¥5~10 | ¥8~15 |

**选型建议**：

- **入门 / 低成本**：HX711 — 生态成熟，模块几元钱
- **需要 I2C 总线**：NAU7802 — 标准接口便于多设备共享，内置温度补偿
- **高精度 / 工业级**：ADS1232 — 更低噪声，适合 0.01% 级精度

---

## 8. IoT 应用场景

### 8.1 智能体重秤 / 厨房秤

ESP32 + HX711 + 称重传感器，Wi-Fi 上报健康数据。要点：HX711 掉电 < 1 μA；采样取平均过滤晃动；电池供电注意 LDO 压降。

### 8.2 仓储库存监测

货架底部装称重传感器，监测重量变化推算剩余件数。要点：S 型 / 轮辐式大量程；LoRa/NB-IoT 上报；六线制接线抵消长导线电阻；定期自动去皮。

### 8.3 蜂箱监测

传感器放在蜂箱下方，重量快速增加说明采蜜旺盛，突然减轻可能分蜂。要点：太阳能 + 电池供电；低采样率（每小时 1 次）；防水防潮；温度补偿（昼夜温差大）。

### 8.4 垃圾桶满溢监测

智慧城市场景，称重达阈值自动通知清运。要点：50 kg 级量程但防护等级 IP65+；NB-IoT 上报；成本和可靠性优先。

---

## 总结与展望

本文从称重传感器的三种主流结构出发，逐步深入到内部应变片电桥、HX711 ADC 架构、时序协议和校准流程，最后给出 Arduino 代码和 ADC 选型对比。

**核心要点**：

1. 称重传感器本质是惠斯通全桥，输出 mV 级信号，必须经高精度 ADC
2. HX711 以极低成本提供 24 位分辨率和 128 倍增益，是入门首选
3. 通信协议非 I2C/SPI 但时序极简，任何 GPIO 即可驱动
4. 校准不可省略——没有校准的 ADC 值毫无意义
5. IoT 场景需额外关注功耗、防护和温度补偿

**展望**：NAU7802 等 I2C 接口 ADC 更适合总线化 IoT 架构；内置温补和自校准 SoC 方案正在出现；边缘 AI 可用于动态称重信号滤波和异常检测；无线供电和能量收集将推动无电池称重节点落地。

---

## 参考资料

1. Avia Semiconductor. *HX711 24-Bit Analog-to-Digital Converter Datasheet*, 2012.
2. Nuvoton. *NAU7802 24-Bit ADC with I2C Interface Datasheet*, 2017.
3. Texas Instruments. *ADS1232 24-Bit ADC for Bridge Sensors Datasheet*, 2015.
4. Bogdan Necula. *HX711 Arduino Library*. GitHub: bogde/HX711.
5. K. Hoffmann. *An Introduction to Measurements using Strain Gages*. HBK, 1989.
6. 《应变片与惠斯通电桥测量电路》. IoT Reading Station, 2025.
7. Omega Engineering. *Load Cell Technical Guide*. omega.com.
8. SparkFun Electronics. *HX711 Load Cell Amplifier Hookup Guide*, 2023.
