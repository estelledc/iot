---
schema_version: '1.0'
id: ultrasonic-distance-measurement
title: 超声波测距传感器原理与盲区优化
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
# 超声波测距传感器原理与盲区优化

> **难度**：🟢 初级 | **领域**：距离测量、声学传感、机器人避障 | **阅读时间**：约 15 分钟

## 日常类比

想象你站在一个空旷的山谷里，对着远处的山崖大喊一声，然后开始计时。过了大约 2 秒，你听到了回声。你知道声音在空气中的传播速度大约是每秒 340 米，那么 2 秒的来回时间意味着声音走了 680 米，除以 2 就是 340 米——这就是你到山崖的距离。超声波测距传感器做的就是同一件事：发出一个"喊声"（超声波脉冲），等回声回来，用时间差算出距离。

再想一个场景：你在一个很小的房间里喊话，墙壁离你太近，回声几乎和你的声音同时回来，你根本分不清哪个是原声、哪个是回声。这就是超声波传感器的"盲区"——目标太近时，发射脉冲还没完全结束，回声就已经回来了，接收电路无法区分两者。就像你必须等嘴巴闭上，耳朵才能听清别人说话一样，传感器也必须等发射脉冲"说完"，才能开始"听"回声。

最后，想象一个停车场里几十辆车同时在按喇叭——你很难分辨哪个声音是你的回声。多个超声波传感器同时工作时也会遇到同样的问题：一个传感器发出的声波被另一个传感器接收到，产生"串扰"。解决这类干扰就像让每辆车轮流按喇叭，或者给每辆车分配不同的音调——这也是多传感器协作时的核心设计考量。

## 1. 超声波基础

### 1.1 什么是超声波

超声波是指频率高于人类听觉上限（约 20 kHz）的声波。在测距应用中，常用频率范围为 40 kHz～200 kHz，其中 40 kHz 最为普遍。超声波本质上是机械振动在弹性介质中的传播，遵循声波的基本物理规律：

- 在空气中以纵波形式传播（介质质点振动方向与传播方向平行）
- 传播速度受温度影响显著（约 0.6 m/s 每 °C）
- 遇到不同声阻抗的界面会发生反射

### 1.2 为什么选超声波而不是光

| 特性 | 超声波测距 | 红外测距 | 激光测距 |
|------|-----------|---------|---------|
| 工作原理 | 飞行时间（声速） | 三角测距 / 反射强度 | 飞行时间（光速） |
| 典型量程 | 2 cm ～ 4 m | 10 cm ～ 80 cm | 0.1 m ～ 100+ m |
| 表面适应性 | 对颜色/透明度不敏感 | 深色/透明表面失效 | 对漫反射表面较弱 |
| 成本 | 极低（HC-SR04 约 5 元） | 低 | 较高 |
| 响应速度 | 毫秒级（声速限制） | 毫秒级 | 微秒级 |
| 环境光干扰 | 无影响 | 严重受影响 | 较小 |

超声波对目标表面颜色和透明度不敏感——它能轻松检测玻璃杯或黑色物体，而红外传感器在这些场景下几乎失效。这是超声波在智能垃圾桶、自动泊车等场景中不可替代的优势。

### 1.3 声速与温度的关系

空气中声速的经验公式：

```
c = 331.4 + 0.6 × T
```

其中 $T$ 为摄氏温度，$c$ 为声速（m/s）。常见温度下的声速：

| 温度 (°C) | 声速 (m/s) | 1 ms 对应距离 (cm) |
|-----------|-----------|-------------------|
| -10 | 325.4 | 16.27 |
| 0 | 331.4 | 16.57 |
| 20 | 343.4 | 17.17 |
| 40 | 355.4 | 17.77 |

温度每变化 10°C，声速变化约 6 m/s，对应距离误差约 1.7%。在精度要求高于 1% 的场合，必须加入温度补偿。

## 2. 飞行时间测距原理

### 2.1 基本公式

超声波测距的核心是飞行时间（Time of Flight, ToF）法：

```
d = (c × t) / 2
```

- $d$：传感器到目标的距离
- $c$：声速（m/s）
- $t$：从发射到接收到回声的时间间隔
- 除以 2 是因为声波走了一个来回

### 2.2 测距精度分析

精度由时间分辨率决定。假设系统时钟为 1 MHz（周期 1 μs），则：

- 时间分辨率：1 μs
- 距离分辨率：$c \times 1\mu s / 2 \approx 0.17$ mm（理论值）

但实际精度受以下因素制约：

1. **发射脉冲宽度**：40 kHz 超声波的一个周期为 25 μs，通常发射 8 个脉冲（200 μs），距离分辨率受脉宽限制
2. **回波阈值判定**：接收信号的包络上升沿并非理想阶跃，阈值选取引入误差
3. **声速不确定性**：未做温度补偿时，20°C 偏差可导致约 3% 的距离误差
4. **空气扰动**：风、气流不均匀会导致声速局部变化

### 2.3 测距流程时序

典型的单次测距时序如下：

```
        ┌───┐                           ┌──────────────┐
TRIG ───┘   └───────────────────────────┘              └───
        │10μs│                           │   Echo脉宽   │
        │    │    等待回波...             │  ∝ 距离      │
        ▼    ▼                           ▼              ▼
      发射脉冲 ────────────────────── 接收回波
        │◄──────── t (飞行时间) ────────►│
```

## 3. HC-SR04 模块内部解析

### 3.1 模块架构

HC-SR04 是最常用的低成本超声波测距模块，其内部结构：

```
         ┌──────────────────────────────────┐
TRIG ───►│  控制逻辑   压电发射器 (T)       │───► 超声波
         │    │                            │
         │    ▼                            │
         │  脉冲发生器                      │
         │  (8 pulses @ 40kHz)             │
         │    │                            │
         │    ▼                            │
         │  放大 + 比较器 ── 压电接收器 (R) │◄─── 回波
ECHO ───►│                                │
         └──────────────────────────────────┘
```

### 3.2 引脚定义与电气参数

| 引脚 | 方向 | 功能 | 电气特性 |
|------|------|------|---------|
| VCC | 输入 | 电源 | 5 V DC（工作电流约 15 mA） |
| TRIG | 输入 | 触发信号 | ≥ 10 μs 高电平触发一次测量 |
| ECHO | 输出 | 回波信号 | 高电平宽度 = 飞行时间（μs） |
| GND | — | 地 | — |

### 3.3 工作时序详解

1. MCU 向 TRIG 引脚发送 ≥ 10 μs 的高电平脉冲
2. 模块内部自动发射 8 个 40 kHz 超声波脉冲
3. 发射完成后，ECHO 引脚拉高
4. 接收到回波时，ECHO 引脚拉低
5. ECHO 高电平持续时间即为飞行时间 $t$
6. 若未收到回波，ECHO 在约 200 ms 后自动拉低（超时保护）

### 3.4 距离计算示例

假设 ECHO 脉冲宽度为 1160 μs，环境温度 20°C：

```
d = (343.4 m/s × 1160 μs) / 2
  = (343.4 × 0.001160) / 2
  = 0.3984 / 2
  ≈ 0.199 m ≈ 20 cm
```

工程上常使用简化公式（假设 20°C 标准声速）：

```
d(cm) = t(μs) / 58
```

## 4. 盲区成因与优化

### 4.1 盲区是什么

盲区（Blind Zone / Dead Zone）是指传感器无法有效检测目标的最近距离范围。HC-SR04 的标称盲区约为 2～3 cm，实际使用中可能更大。

### 4.2 盲区产生的三大原因

**原因一：发射余振**

压电陶瓷换能器在发射完 8 个脉冲后，不会立刻停止振动——存在机械余振（ringing）。余振信号幅度远大于远处目标的回波，接收电路无法在余振期间检测到回波。余振持续时间通常为 1～3 ms，对应的盲区：

```
盲区 ≈ (c × 余振时间) / 2 = (343.4 × 0.002) / 2 ≈ 34 cm（理论最坏情况）
```

模块内部通过增益控制和比较器阈值抑制部分余振，将盲区压缩到 2～3 cm。

**原因二：发射-接收串扰**

在收发一体式传感器中，发射信号直接耦合到接收电路。即使采用分体式设计（HC-SR04 的 T 和 R 分开），近距离目标的回波仍可能在发射脉冲尚未结束时到达，产生信号重叠。

**原因三：声场近场效应**

超声波换能器的声场分为近场（Fresnel 区）和远场（Fraunhofer 区）。近场中声压分布不均匀，存在多个极大值和极小值，导致接收信号幅度与距离的关系不规则，难以可靠判定。

### 4.3 盲区优化方案

#### 硬件层面

| 方案 | 原理 | 效果 | 代价 |
|------|------|------|------|
| 收发分体设计 | 物理隔离发射与接收路径 | 减少直接串扰 | 体积增大 |
| 声学吸收层 | 在换能器周围填充吸音材料 | 减少余振和侧面回波 | 增加模块厚度 |
| 发射阻尼电路 | 发射后主动对换能器施加阻尼 | 缩短余振时间 | 电路复杂度增加 |
| 独立收发换能器 | 分别使用发射和接收专用换能器 | 余振最小化 | 成本增加 |

#### 软件层面

```cpp
// 盲区补偿策略：使用红外传感器补充近距离检测
// 当超声波报告距离 < 盲区阈值时，切换到红外传感器数据

#define ULTRASONIC_BLIND_ZONE_CM  3.0
#define IR_VALID_MAX_CM           30.0

float getReliableDistance() {
    float usDist = readUltrasonic();   // 读取超声波距离
    float irDist = readInfrared();     // 读取红外距离

    if (usDist <= ULTRASONIC_BLIND_ZONE_CM) {
        // 超声波进入盲区，信任红外数据
        return (irDist <= IR_VALID_MAX_CM) ? irDist : ULTRASONIC_BLIND_ZONE_CM;
    }
    // 超声波有效范围内，优先使用超声波（不受颜色影响）
    return usDist;
}
```

#### 时序优化

```cpp
// 利用发射后的固定延迟跳过余振期
// 在延迟结束后才开始检测回波

#define RINGING_DELAY_US  500  // 跳过余振的延迟（对应约 8.6 cm）

float measureWithBlindZoneSkip() {
    sendTriggerPulse();                       // 发送触发信号
    delayMicroseconds(RINGING_DELAY_US);      // 跳过余振期
    unsigned long duration = pulseIn(ECHO_PIN, HIGH);  // 测量回波脉宽
    float distance = duration / 58.0;         // 转换为 cm
    return distance;
}
```

## 5. 常见超声波模块对比

| 参数 | HC-SR04 | JSN-SR04T | A02YYUW | DYP-A02 | MB1040 (MaxSonar) |
|------|---------|-----------|---------|---------|-------------------|
| 工作电压 | 5 V | 5 V | 3.3～5 V | 5 V | 3.3～5 V |
| 量程 | 2～400 cm | 20～600 cm | 3～450 cm | 3～450 cm | 0～765 cm |
| 盲区 | 2 cm | 20 cm | 3 cm | 3 cm | 0 cm（特别设计） |
| 精度 | ~3 mm | ~10 mm | ~3 mm | ~3 mm | ~10 mm |
| 波束角 | ~15° | ~15° | ~15° | ~15° | ~20° |
| 接口 | TRIG/ECHO | TRIG/ECHO | 串口 | 串口 | 模拟/串口/PWM |
| 防水 | 否 | 是（IP67） | 是 | 否 | 否 |
| 参考价格 | ¥5 | ¥15 | ¥25 | ¥30 | ¥80 |

**选型建议**：

- **教学 / 原型验证**：HC-SR04，成本最低、资料最多
- **户外 / 潮湿环境**：JSN-SR04T，防水但盲区大（20 cm）
- **近距离 + 小盲区**：MB1040，盲区几乎为零，但价格高
- **串口通信需求**：A02YYUW，3.3 V 兼容，适合 ESP32 等平台

## 6. Arduino 完整测距程序

### 6.1 基础版本

```cpp
/*
 * 超声波测距 - 基础版
 * 硬件: Arduino Uno + HC-SR04
 * 接线: TRIG->D9, ECHO->D10, VCC->5V, GND->GND
 */

#define TRIG_PIN  9
#define ECHO_PIN  10
#define SOUND_SPEED_CM_US  0.0343  // 20°C 时声速 (cm/μs)

void setup() {
    Serial.begin(9600);
    pinMode(TRIG_PIN, OUTPUT);
    pinMode(ECHO_PIN, INPUT);
    // 确保触发引脚初始为低电平
    digitalWrite(TRIG_PIN, LOW);
    delay(100);  // 等待模块稳定
}

float measureDistance() {
    // 1. 发送触发脉冲 (≥10μs 高电平)
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);

    // 2. 测量 ECHO 脉冲宽度（超时 30ms ≈ 5m 上限）
    unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000);

    // 3. 超时处理
    if (duration == 0) {
        return -1.0;  // 无回波
    }

    // 4. 计算距离 (cm)
    float distance = (duration * SOUND_SPEED_CM_US) / 2.0;
    return distance;
}

void loop() {
    float dist = measureDistance();

    if (dist < 0) {
        Serial.println("超出量程或无回波");
    } else if (dist < 2.0) {
        Serial.println("进入盲区，数据不可靠");
    } else {
        Serial.print("距离: ");
        Serial.print(dist, 1);
        Serial.println(" cm");
    }

    delay(100);  // 测量间隔 ≥60ms，避免回波干扰
}
```

### 6.2 带温度补偿的增强版本

```cpp
/*
 * 超声波测距 - 温度补偿版
 * 硬件: Arduino Uno + HC-SR04 + LM35 温度传感器
 * 接线: TRIG->D9, ECHO->D10, LM35->A0
 */

#define TRIG_PIN  9
#define ECHO_PIN  10
#define TEMP_PIN  A0
#define BLIND_ZONE_CM  2.0
#define MAX_RANGE_CM   400.0
#define NUM_SAMPLES    5          // 滑动平均滤波采样数

float samples[NUM_SAMPLES];      // 滑动窗口缓冲区
int sampleIndex = 0;

// 根据温度计算声速 (cm/μs)
float getSoundSpeed() {
    // LM35 输出 10 mV/°C，ADC 5V/1024 → 每单位 4.88 mV
    float voltage = analogRead(TEMP_PIN) * 5.0 / 1024.0;
    float tempC = voltage * 100.0;  // 转换为摄氏度

    // 声速公式: c = 331.4 + 0.6 × T (m/s)
    float speedMps = 331.4 + 0.6 * tempC;
    return speedMps / 10000.0;  // 转换为 cm/μs
}

float measureOnce() {
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);

    unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000);
    if (duration == 0) return -1.0;

    float soundSpeed = getSoundSpeed();
    float distance = (duration * soundSpeed) / 2.0;

    // 范围校验
    if (distance < BLIND_ZONE_CM || distance > MAX_RANGE_CM) {
        return -1.0;
    }
    return distance;
}

// 滑动平均滤波，抑制偶然跳变
float getFilteredDistance() {
    samples[sampleIndex] = measureOnce();
    sampleIndex = (sampleIndex + 1) % NUM_SAMPLES;

    float sum = 0;
    int validCount = 0;
    for (int i = 0; i < NUM_SAMPLES; i++) {
        if (samples[i] > 0) {
            sum += samples[i];
            validCount++;
        }
    }

    if (validCount == 0) return -1.0;
    return sum / validCount;
}

void setup() {
    Serial.begin(9600);
    pinMode(TRIG_PIN, OUTPUT);
    pinMode(ECHO_PIN, INPUT);
    digitalWrite(TRIG_PIN, LOW);

    // 初始化滤波缓冲区
    for (int i = 0; i < NUM_SAMPLES; i++) {
        samples[i] = -1.0;
    }
    delay(100);
}

void loop() {
    float dist = getFilteredDistance();

    if (dist < 0) {
        Serial.println("[!] 无有效回波");
    } else {
        Serial.print("距离: ");
        Serial.print(dist, 1);
        Serial.println(" cm");
    }
    delay(60);  // 间隔 ≥60ms 防止回波串扰
}
```

## 7. 多传感器干扰与规避

### 7.1 串扰问题

当两个或多个超声波传感器同时工作时，传感器 A 发出的声波可能被传感器 B 的接收器捕获，导致 B 测出错误距离。这种现象称为交叉串扰（crosstalk）。

串扰在以下场景尤其严重：

- 机器人上安装多个超声波传感器形成阵列
- 多台设备在同一空间内工作（如停车场多车位同时检测）
- 传感器安装间距小于声束覆盖范围

### 7.2 时分复用方案

最简单有效的抗干扰策略是时分复用（TDMA）：让多个传感器轮流工作，同一时刻只有一个传感器在发射。

```cpp
/*
 * 多超声波传感器时分复用示例
 * 3 个 HC-SR04 分时工作，避免串扰
 */

const int NUM_SENSORS = 3;
const int TRIG_PINS[NUM_SENSORS] = {9, 11, 13};
const int ECHO_PINS[NUM_SENSORS] = {10, 12, A1};
const int MEASURE_INTERVAL_MS = 60;  // 每个传感器间隔

float distances[NUM_SENSORS];

float measureOneSensor(int idx) {
    digitalWrite(TRIG_PINS[idx], LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PINS[idx], HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PINS[idx], LOW);

    unsigned long duration = pulseIn(ECHO_PINS[idx], HIGH, 30000);
    if (duration == 0) return -1.0;
    return duration / 58.0;
}

void setup() {
    Serial.begin(9600);
    for (int i = 0; i < NUM_SENSORS; i++) {
        pinMode(TRIG_PINS[i], OUTPUT);
        pinMode(ECHO_PINS[i], INPUT);
        digitalWrite(TRIG_PINS[i], LOW);
        distances[i] = -1.0;
    }
    delay(100);
}

void loop() {
    for (int i = 0; i < NUM_SENSORS; i++) {
        distances[i] = measureOneSensor(i);

        Serial.print("S");
        Serial.print(i);
        Serial.print(": ");
        if (distances[i] > 0) {
            Serial.print(distances[i], 1);
            Serial.print("cm");
        } else {
            Serial.print("---");
        }
        Serial.print("  ");

        delay(MEASURE_INTERVAL_MS);  // 等待余波消散
    }
    Serial.println();
}
```

### 7.3 其他抗干扰策略

| 策略 | 原理 | 适用场景 |
|------|------|---------|
| 时分复用 (TDMA) | 轮流发射，同时只有 1 个传感器工作 | 传感器数量少（≤6） |
| 编码发射 | 每个传感器使用不同的发射编码（如 Chirp） | 中等规模阵列 |
| 物理遮挡 | 在传感器间加装吸音隔板 | 固定安装场景 |
| 随机退避 | 每次测量前随机等待一段空闲时间 | 分布式多设备场景 |
| 码分多址 (CDMA) | 用正交编码区分不同传感器的信号 | 高端工业应用 |

## 8. 物联网应用场景

### 8.1 智能停车场车位检测

在停车场每个车位上方安装一个超声波传感器（通常选用防水型 JSN-SR04T），定期测量到车顶的距离：

- 距离 > 阈值（如 150 cm）→ 车位空闲
- 距离 < 阈值 → 车位占用

数据通过 LoRa 或 Wi-Fi 上传至云平台，实现实时车位地图。关键设计要点：

1. 检测周期可设为 5～10 秒（车辆进出不频繁，降低功耗）
2. 多车位需采用时分复用避免串扰
3. 传感器需做防水防尘处理（IP65 以上）

### 8.2 液位监测

在储液罐顶部安装超声波传感器，向下测量到液面的距离，间接推算液位：

```
液位高度 = 罐体总高度 - 测量距离
```

注意事项：

- 液面波动需做滑动平均滤波
- 腐蚀性液体需选用防腐型传感器或采用非接触安装
- 温度变化大时必须加入温度补偿
- 罐壁回波可能干扰，需对准液面中心

### 8.3 机器人避障导航

移动机器人通常在前方和两侧安装多个超声波传感器，形成扇形探测区域：

```
          前方 (0°)
         ┌────────┐
    左前 /          \ 右前
   (-30°)            (+30°)
        │            │
   左侧 (-90°)    右侧 (+90°)
```

避障逻辑：

- 单侧距离 < 安全阈值 → 向反方向转向
- 正前方距离 < 紧急阈值 → 停车
- 所有方向安全 → 继续前进

超声波避障的局限性：

- 波束角较宽（约 15°），对细长物体（桌腿、椅子腿）检测能力弱
- 检测延迟较高（单次测量约 30～60 ms），高速运动时反应不及时
- 吸音材质表面（如海绵、毛毡）可能无回波

**实践建议**：在机器人应用中，超声波传感器常与红外传感器互补——红外负责近距离（< 30 cm）和细小障碍物检测，超声波负责中远距离范围检测。

## 总结与展望

超声波测距是一种成熟、低成本、对表面特性不敏感的距离测量技术。其核心原理——飞行时间法——简单直观，但在工程实践中需要重点关注三个问题：

1. **盲区**：由发射余振、串扰和近场效应共同导致，可通过硬件优化（收发分体、阻尼电路）和软件策略（多传感器融合、滤波）缓解
2. **精度**：温度对声速的影响不可忽视，高精度场景必须加入温度补偿
3. **多传感器干扰**：时分复用是最实用的抗串扰方案，大规模阵列需考虑编码发射

未来发展趋势：

- **MEMS 超声波**：将压电换能器集成到芯片级，大幅缩小体积、降低盲区
- **Chirp 编码**：用频率扫描信号替代固定频率脉冲，提高抗干扰能力和信噪比
- **AI 辅助信号处理**：用轻量级神经网络从回波信号中提取更多信息（如材质分类、多目标分辨）
- **与毫米波雷达融合**：超声波 + 毫米波互补，覆盖近距离到远距离的全量程高精度检测

## 参考资料

1. HC-SR04 Ultrasonic Module User Manual, Elecfreaks, 2013
2. Murata Manufacturing, "Piezoelectric Ceramic Transducers — Principle and Application", Application Note, 2020
3. MaxBotix, "LV-MaxSonar-EZ1 Datasheet & Operation Manual", 2021
4. B. Barshan, "Fast Processing Techniques for Accurate Ultrasonic Range Measurements", Mechatronics, Vol. 10, No. 5, 2000
5. 谭民, 徐德等, 《先进机器人控制》, 科学出版社, 2016
6. STMicroelectronics, "Ultrasonic Time-of-Flight Measurement AN5298", Application Note, 2020
7. JSN-SR04T Integrated Waterproof Ultrasonic Ranging Module Datasheet, 2019
