---
schema_version: '1.0'
id: rtd-pt100-signal-conditioning
title: RTD/PT100温度传感器信号调理电路设计
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
# RTD/PT100温度传感器信号调理电路设计

> **难度**：🟡 中级 | **领域**：模拟电路设计、传感器接口、工业测温 | **阅读时间**：约 20 分钟

## 日常类比

想象你有一根金属丝，天冷时它"僵硬"（电阻低），天热时它"松弛"（电阻高）。PT100就是这样一根精心制作的铂金丝——在0C时电阻恰好是100 ohm，温度每升高1C，电阻大约增加0.385 ohm。这就像一把"电阻温度计"，通过测量电阻的变化来推算温度。

但问题来了：这根铂金丝的电阻变化非常微小。从0C到100C，电阻只从100 ohm变到138.5 ohm——变化量不到40 ohm。如果你用一把只能量到"公斤"的秤去称一粒米的重量变化，显然是不够的。信号调理电路就是那把精密的"电子秤"，它把微小的电阻变化放大、转换成ADC能识别的电压信号，同时还要滤除各种干扰噪声。

再打个比方：PT100输出的原始信号就像耳语声，周围环境噪声（工频干扰、热噪声）就像嘈杂的市场。信号调理电路的工作就是给耳语者戴上麦克风和音箱（放大），同时给旁边的噪音源套上隔音罩（滤波），最终让你清楚听到耳语的内容（精确的温度值）。

## 1. RTD/PT100基础原理

### 1.1 电阻-温度关系

铂电阻温度计（RTD, Resistance Temperature Detector）利用金属铂的电阻随温度线性变化的特性来测量温度。其数学模型由Callendar-Van Dusen方程描述：

对于 0C <= T <= 850C：

```
R(T) = R0 * (1 + A*T + B*T^2)
```

对于 -200C <= T < 0C：

```
R(T) = R0 * (1 + A*T + B*T^2 + C*(T-100)*T^3)
```

其中标准系数为：
- R0 = 100 ohm（0C时的电阻值）
- A = 3.9083e-3 /C
- B = -5.775e-7 /C^2
- C = -4.183e-12 /C^4

### 1.2 PT100与其他温度传感器对比

| 特性 | PT100 (RTD) | 热电偶 (K型) | 热敏电阻 (NTC) | 数字传感器 (DS18B20) |
|------|-------------|-------------|----------------|---------------------|
| 测温范围 | -200C ~ +850C | -200C ~ +1370C | -40C ~ +300C | -55C ~ +125C |
| 精度 | +/-0.1C (A级) | +/-1.5C | +/-0.2C | +/-0.5C |
| 线性度 | 优秀 | 良好 | 差（指数关系） | N/A（数字输出） |
| 响应时间 | 1~10s | 0.1~1s | 0.5~5s | 0.75s |
| 长期稳定性 | 极好 | 一般 | 差 | 良好 |
| 自热效应 | 有（需控制激励电流） | 无 | 有 | 无 |
| 成本 | 中高 | 低 | 低 | 低 |
| 典型应用 | 工业过程控制 | 高温测量 | 家电温控 | 环境监测 |

### 1.3 PT100精度等级

| 等级 | 标准 | 0C时容差 | 100C时容差 | 适用场景 |
|------|------|-----------|-------------|----------|
| AA (1/3 DIN) | IEC 60751 | +/-0.1C | +/-0.17C | 精密实验室 |
| A | IEC 60751 | +/-0.15C | +/-0.35C | 工业精密测量 |
| B | IEC 60751 | +/-0.3C | +/-0.8C | 通用工业 |
| C (1/3 B) | IEC 60751 | +/-0.6C | +/-1.6C | 一般监测 |

## 2. 接线方式与引线补偿

### 2.1 二线制、三线制、四线制

PT100的引线电阻会引入测量误差。一根10m长的铜导线，在20C时电阻约0.33 ohm，对应约0.86C的温度误差。不同接线方式对此有不同的补偿策略：

**二线制**：最简单，但引线电阻直接叠加在PT100电阻上，适合引线短、精度要求低的场景。

**三线制**：工业最常用。三根引线中两根接PT100两端，第三根用于补偿引线电阻。前提是三根引线材质、长度、线径完全一致。

**四线制**：最高精度。两根引线通激励电流，另两根引线测量PT100两端电压。由于电压测量回路几乎无电流流过，引线电阻的影响被完全消除。

### 2.2 接线方式选择决策

- 引线 < 1m，精度要求 +/-1C -> 二线制
- 引线 1~50m，精度要求 +/-0.5C -> 三线制
- 引线任意长度，精度要求 +/-0.1C -> 四线制

## 3. 激励电流源设计

### 3.1 为什么需要恒流激励

测量电阻最直观的方法是施加已知电流，测量其两端电压，由欧姆定律 R = V/I 得到电阻值。恒流源的优势在于：即使引线电阻变化（温度漂移），流过PT100的电流不变，配合四线制测量可以完全消除引线影响。

### 3.2 激励电流的选择

激励电流太大会导致自热效应（焦耳热使PT100温度升高），太小则信号幅度不够。典型选择：

- 1mA：最常用，自热约0.1C（薄膜型），信号范围100~385mV（0~850C）
- 0.5mA：低自热应用，信号减半
- 0.1mA：极低自热要求，需更高增益放大

自热功耗计算：P = I^2 * R = (1mA)^2 * 100 ohm = 0.1mW

### 3.3 恒流源电路实现

使用运放+基准电压的经典恒流源设计：

```
        Vref (2.5V)
          |
          R_set (2.5k ohm -> I = 1mA)
          |
     +----|----+
     |   Op   |--- Vout -> 经过PT100
     +----|----+
          |
         GND (反馈点)
```

关键设计要点：
- 基准电压源选择低温漂型（如REF3025，温漂3ppm/C）
- 设定电阻使用精密电阻（0.1%容差，25ppm/C温漂）
- 运放选择低偏置电流型（如OPA277，偏置电流1nA）

## 4. 信号调理电路设计

### 4.1 惠斯通电桥方案

惠斯通电桥是传统的RTD测量电路。将PT100作为电桥的一个臂，当温度变化时电桥失衡，差分电压与温度成正比（近似）。

电桥输出电压：
```
Vout = Vexc * (R_pt100/(R_pt100 + R3) - R2/(R2 + R1))
```

平衡条件（0C）：R1 = R2 = R3 = 100 ohm

优点：抑制共模干扰，输出差分信号。
缺点：非线性、需要匹配电阻、不适合宽温度范围。

### 4.2 恒流源+仪表放大器方案（推荐）

这是现代工业测温的主流方案，由三个核心模块组成：

**模块1：精密恒流源** -> 提供稳定的1mA激励电流

**模块2：仪表放大器（INA）** -> 放大PT100两端的差分电压
- 输入电压范围：100mV ~ 385mV（对应0C ~ 850C）
- 目标输出范围：0 ~ 3.3V（匹配ADC输入）
- 所需增益：G = 3.3V / 0.285V 约 11.6（取G = 10，加后级调整）

**模块3：低通滤波器** -> 滤除高频噪声和50/60Hz工频干扰

### 4.3 推荐芯片选型

| 功能模块 | 推荐芯片 | 关键参数 | 备选方案 |
|----------|----------|----------|----------|
| 恒流源运放 | OPA277 | 偏置电流1nA，失调10uV | AD8551 |
| 仪表放大器 | INA128 | CMRR 120dB，增益误差0.02% | AD620 |
| 基准电压 | REF3025 | 2.5V，温漂3ppm/C | LM4040 |
| ADC | ADS1220 | 24bit，2kSPS，内置PGA | ADS1115 |
| 集成方案 | ADS1248 | 内置恒流源+PGA+ADC | MAX31865 |

### 4.4 使用MAX31865的集成方案

MAX31865是专为PT100设计的SPI接口RTD数字转换器，内部集成了：
- 可配置的恒流源（100uA~1.6mA）
- 15位ADC
- 自动三线制/四线制补偿
- 过/欠温故障检测

这大大简化了硬件设计，适合IoT应用中的快速原型开发。

## 5. 滤波与抗干扰设计

### 5.1 噪声来源分析

工业环境中的主要干扰源：
- 50/60Hz工频干扰：来自电力线的电磁耦合
- 射频干扰（RFI）：来自变频器、电机驱动器
- 热噪声：PT100自身的约翰逊噪声（4kTRB）
- 1/f噪声：运放的低频闪烁噪声

### 5.2 滤波器设计

**一阶RC低通（传感器端）**：截止频率设在10Hz
```
R = 15.9k ohm, C = 1uF -> fc = 1/(2*pi*R*C) = 10Hz
```

**二阶有源Sallen-Key低通（ADC前）**：截止频率设在5Hz，巴特沃斯响应
```
增益 = 1 (电压跟随器配置)
R1 = R2 = 22k ohm
C1 = 1uF, C2 = 470nF
fc 约 1/(2*pi * 22k * sqrt(1u * 470n)) 约 4.7Hz
```

### 5.3 PCB布局要点

- 激励电流走线与电压检测走线分开布线
- 模拟地与数字地单点连接
- PT100连接器附近放置TVS管（防浪涌）和旁路电容
- 信号调理电路用地平面屏蔽

## 6. 软件线性化与温度计算

### 6.1 查表法+线性插值（C语言实现）

```c
#include <stdint.h>

// PT100电阻-温度查找表（每10C一个点）
// 索引: 0=-200C, 1=-190C, ..., 20=0C, ..., 105=850C
static const float pt100_table[] = {
    18.52,  22.83,  27.10,  31.34,  35.54,  // -200 ~ -160C
    39.72,  43.88,  48.00,  52.11,  56.19,  // -160 ~ -120C
    60.26,  64.30,  68.33,  72.33,  76.33,  // -120 ~ -80C
    80.31,  84.27,  88.22,  92.16,  96.09,  // -80 ~ -40C
    100.00, 103.90, 107.79, 111.67, 115.54, // 0 ~ 40C
    119.40, 123.24, 127.07, 130.89, 134.70, // 40 ~ 80C
    138.50, 142.29, 146.06, 149.82, 153.58, // 80 ~ 120C
    157.31, 161.04, 164.76, 168.46, 172.16, // 120 ~ 160C
    175.84, 179.51, 183.17, 186.82, 190.45  // 160 ~ 200C
};

// 通过电阻值查表计算温度（线性插值）
// resistance: PT100当前电阻值（ohm）
// 返回: 温度值（C），范围 -200 ~ 200C
float pt100_resistance_to_temp(float resistance) {
    // 查找区间
    int idx = 0;
    int table_size = sizeof(pt100_table) / sizeof(pt100_table[0]);

    for (idx = 0; idx < table_size - 1; idx++) {
        if (resistance < pt100_table[idx + 1]) break;
    }

    // 边界检查
    if (idx >= table_size - 1) return 200.0f;  // 超上限
    if (resistance < pt100_table[0]) return -200.0f;  // 超下限

    // 线性插值: T = T_low + (R - R_low)/(R_high - R_low) * 10C
    float r_low = pt100_table[idx];
    float r_high = pt100_table[idx + 1];
    float t_low = -200.0f + idx * 10.0f;

    return t_low + (resistance - r_low) / (r_high - r_low) * 10.0f;
}
```

### 6.2 Callendar-Van Dusen直接计算（Python实现）

```python
import math

# Callendar-Van Dusen系数（IEC 60751标准）
A = 3.9083e-3   # /C
B = -5.775e-7   # /C^2
C = -4.183e-12  # /C^4（仅T<0C时使用）
R0 = 100.0      # 0C时的标称电阻（ohm）


def pt100_to_temperature(resistance: float) -> float:
    """
    将PT100电阻值转换为温度值。
    使用Callendar-Van Dusen方程的逆运算。

    Args:
        resistance: PT100当前电阻值（ohm）

    Returns:
        温度值（C）

    Note:
        T >= 0C时使用二次方程求解
        T < 0C时使用迭代法（牛顿法）
    """
    if resistance >= R0:
        # T >= 0C: R = R0*(1 + A*T + B*T^2)
        # 解二次方程: B*T^2 + A*T + (1 - R/R0) = 0
        discriminant = A**2 - 4 * B * (1 - resistance / R0)
        if discriminant < 0:
            raise ValueError(f"电阻值 {resistance} ohm 超出有效范围")
        temperature = (-A + math.sqrt(discriminant)) / (2 * B)
    else:
        # T < 0C: 使用牛顿迭代法求解
        # R = R0*(1 + A*T + B*T^2 + C*(T-100)*T^3)
        t = (resistance / R0 - 1) / A  # 初始猜测（线性近似）
        for _ in range(20):  # 最多迭代20次
            r_calc = R0 * (1 + A*t + B*t**2 + C*(t - 100)*t**3)
            dr_dt = R0 * (A + 2*B*t + C*(4*t**3 - 300*t**2))
            dt = (resistance - r_calc) / dr_dt
            t += dt
            if abs(dt) < 1e-6:
                break
        temperature = t

    return round(temperature, 3)


# 使用示例
if __name__ == "__main__":
    test_resistances = [80.31, 100.00, 119.40, 138.50, 175.84]
    for r in test_resistances:
        t = pt100_to_temperature(r)
        print(f"R = {r:7.2f} ohm -> T = {t:8.3f} C")
```

## 7. MAX31865驱动实现（Arduino/ESP32）

### 7.1 硬件连接

```
ESP32         MAX31865
-----         --------
GPIO5  --->   CS
GPIO18 --->   CLK (SCK)
GPIO23 --->   SDI (MOSI)
GPIO19 <---   SDO (MISO)
3.3V   --->   VDD
GND    --->   GND

MAX31865      PT100 (四线制)
--------      --------------
FORCE+  --->  PT100引脚1 (电流+)
RTDIN+  --->  PT100引脚2 (电压+)
RTDIN-  --->  PT100引脚3 (电压-)
FORCE-  --->  PT100引脚4 (电流-)
```

### 7.2 驱动代码

```c
#include <SPI.h>

#define MAX31865_CS     5
#define MAX31865_RREF   430.0  // 参考电阻值（ohm），四线制用430 ohm
#define MAX31865_RNOMINAL 100.0  // PT100标称电阻

// 寄存器地址
#define REG_CONFIG      0x00
#define REG_RTD_MSB     0x01
#define REG_RTD_LSB     0x02
#define REG_FAULT       0x07

// 配置位
#define CONFIG_BIAS     0x80  // 偏置电压使能
#define CONFIG_AUTO     0x40  // 自动转换模式
#define CONFIG_1SHOT    0x20  // 单次转换
#define CONFIG_3WIRE    0x10  // 三线制模式
#define CONFIG_FILT50   0x01  // 50Hz滤波

void max31865_init() {
    pinMode(MAX31865_CS, OUTPUT);
    digitalWrite(MAX31865_CS, HIGH);
    SPI.begin();

    // 配置: 偏置使能 + 自动转换 + 四线制 + 50Hz滤波
    uint8_t config = CONFIG_BIAS | CONFIG_AUTO | CONFIG_FILT50;
    max31865_write_reg(REG_CONFIG, config);
    delay(10);  // 等待偏置电压稳定
}

void max31865_write_reg(uint8_t reg, uint8_t val) {
    digitalWrite(MAX31865_CS, LOW);
    SPI.transfer(reg | 0x80);  // 写操作：地址最高位置1
    SPI.transfer(val);
    digitalWrite(MAX31865_CS, HIGH);
}

uint8_t max31865_read_reg(uint8_t reg) {
    digitalWrite(MAX31865_CS, LOW);
    SPI.transfer(reg & 0x7F);  // 读操作：地址最高位置0
    uint8_t val = SPI.transfer(0xFF);
    digitalWrite(MAX31865_CS, HIGH);
    return val;
}

float max31865_read_temperature() {
    // 读取RTD寄存器（15位ADC值）
    uint8_t msb = max31865_read_reg(REG_RTD_MSB);
    uint8_t lsb = max31865_read_reg(REG_RTD_LSB);

    uint16_t rtd_raw = ((uint16_t)msb << 8) | lsb;
    rtd_raw >>= 1;  // 去掉最低位（故障位）

    // 检查故障位
    if (lsb & 0x01) {
        uint8_t fault = max31865_read_reg(REG_FAULT);
        Serial.printf("MAX31865 fault: 0x%02X\n", fault);
        max31865_write_reg(REG_FAULT, 0x02);  // 清除故障
        return -999.0;  // 返回错误值
    }

    // 计算电阻值: R_rtd = (ADC_raw / 2^15) * R_ref
    float resistance = (float)rtd_raw * MAX31865_RREF / 32768.0;

    // 使用简化公式计算温度（0~850C范围，误差<0.1C）
    float temp = (resistance / MAX31865_RNOMINAL - 1.0) / 3.9083e-3;

    // 二次修正（提高精度）
    temp -= (temp * temp * 5.775e-7 * MAX31865_RNOMINAL) /
            (resistance * 3.9083e-3);

    return temp;
}
```

## 8. IoT应用中的实践考量

### 8.1 低功耗设计

在电池供电的IoT节点中，PT100信号调理电路的功耗是关键挑战：

**间歇式激励**：不需要测温时关闭恒流源。典型工作周期：
- 唤醒 -> 开启恒流源 -> 等待稳定(50ms) -> ADC采样 -> 关闭恒流源 -> 睡眠
- 平均功耗可从持续的5mA降至 < 50uA（1次/分钟采样）

**选择集成方案**：MAX31865的待机电流仅20uA，配合ESP32深度睡眠(10uA)，整个测温节点平均功耗可控制在100uA以内。

### 8.2 数据处理与上报策略

```python
import time
from collections import deque


class PT100DataProcessor:
    """PT100温度数据处理器，适用于IoT边缘节点"""

    def __init__(self, window_size=10, deadband=0.1):
        """
        Args:
            window_size: 滑动窗口大小（用于平均滤波）
            deadband: 死区阈值（C），变化小于此值不上报
        """
        self.window = deque(maxlen=window_size)
        self.deadband = deadband
        self.last_reported = None
        self.fault_count = 0

    def add_reading(self, temperature: float) -> dict:
        """
        添加一次温度读数，返回处理结果。

        Returns:
            dict: {
                'valid': bool,      # 数据是否有效
                'filtered': float,  # 滤波后的温度值
                'should_report': bool,  # 是否需要上报
                'alarm': str|None   # 告警信息
            }
        """
        result = {'valid': True, 'filtered': 0.0,
                  'should_report': False, 'alarm': None}

        # 异常值检测（范围检查 + 跳变检查）
        if temperature < -200 or temperature > 850:
            self.fault_count += 1
            result['valid'] = False
            if self.fault_count >= 3:
                result['alarm'] = 'sensor out of range 3 times, possible open/short'
            return result

        if self.window and abs(temperature - self.window[-1]) > 50:
            result['valid'] = False
            result['alarm'] = f'temperature jump too large: {self.window[-1]:.1f} -> {temperature:.1f} C'
            return result

        self.fault_count = 0
        self.window.append(temperature)

        # 滑动平均滤波
        filtered = sum(self.window) / len(self.window)
        result['filtered'] = round(filtered, 2)

        # 死区判断：只有变化超过阈值才上报
        if self.last_reported is None:
            result['should_report'] = True
        elif abs(filtered - self.last_reported) >= self.deadband:
            result['should_report'] = True

        if result['should_report']:
            self.last_reported = filtered

        return result
```

### 8.3 工业现场常见部署架构

```
[PT100传感器] --(屏蔽电缆)--> [信号调理板] --(SPI/I2C)--> [MCU]
                                                              |
                                                         [WiFi/LoRa]
                                                              |
                                                         [云平台/SCADA]
```

关键要求：
- 传感器到调理板的电缆必须使用屏蔽双绞线
- 屏蔽层单端接地（调理板端）
- 电缆长度 < 100m（四线制）或 < 30m（三线制）
- 调理板本地需做数字滤波+异常检测，避免无效数据浪费带宽

## 9. 常见问题与故障排查

### 9.1 典型故障现象与原因

| 故障现象 | 可能原因 | 排查方法 |
|----------|----------|----------|
| 读数固定在最大值 | PT100断线 | 万用表量传感器电阻 |
| 读数固定在0或很小 | PT100短路 / 接线错误 | 检查接线，量引线间电阻 |
| 读数偏高（固定偏差） | 引线电阻未补偿（二线制） | 改用三/四线制 |
| 读数漂移不定 | 接触不良 / 干扰 | 检查连接器，加屏蔽 |
| 读数有50Hz纹波 | 工频干扰耦合 | 加滤波器，改善屏蔽 |
| 温度响应慢 | 传感器安装不当 | 确认探头与被测物热接触良好 |
| 精度随时间下降 | 传感器老化 / 受污染 | 定期校准或更换 |

### 9.2 自热效应的验证

用不同激励电流（如0.5mA和1mA）分别测量同一稳定温度点，如果读数差异超过预期，说明自热效应显著。解决方案：
- 降低激励电流
- 使用脉冲激励（占空比10%）
- 选择热耗散更好的传感器封装

### 9.3 校准流程

两点校准（冰水混合物0C + 沸水100C）是最简单的现场校准方法：

```
offset = R_measured_0C - 100.00  (零点偏差)
gain_error = (R_measured_100C - R_measured_0C) / 38.50 - 1.0  (灵敏度偏差)

R_corrected = (R_raw - offset) / (1 + gain_error)
```

## 10. 设计检查清单

在完成 PCB 布局前，逐项检查以下要点：

| 检查项 | 要求 | 通过 |
|--------|------|------|
| 激励电流源精度 | <=0.1% 漂移/C | [ ] |
| 三线/四线补偿 | 引线电阻误差 <0.1 Ohm | [ ] |
| ADC分辨率 | >=0.01C/LSB | [ ] |
| 滤波截止频率 | 低于采样率1/10 | [ ] |
| 自热误差 | <0.1C | [ ] |
| 两点校准 | 完成并记录 | [ ] |
| EMI防护 | 屏蔽线+差模滤波 | [ ] |
| 电源去耦 | 每个IC 100nF+10uF | [ ] |

## 总结与展望

PT100 信号调理电路设计的核心在于：精密激励、有效补偿、低噪声放大、高精度数字化四个环节的协同优化。从本文的分析可以得出几个关键结论：

第一，四线制接法配合恒流源激励是工业级精度的基础，三线制仅适合精度要求不高的场景。第二，专用芯片（MAX31865等）极大简化了设计复杂度，适合快速开发；但理解底层原理后的分立方案能获得更优的噪声性能和灵活性。第三，数字域的线性化和滤波算法同样重要，Callendar-Van Dusen方程的正确实现直接影响最终精度。

展望未来，PT100 调理电路的发展趋势包括：集成度更高的单芯片方案（片上激励+ADC+数字处理）、无线传感节点中的超低功耗设计（间歇采样+休眠）、以及基于机器学习的自适应校准算法。在工业物联网场景中，PT100 作为最可靠的温度传感方案，其信号调理技术将持续演进以满足更高精度和更低功耗的需求。

## 参考资料

1. IEC 60751:2022 - 工业铂电阻温度计和铂温度传感器标准
2. Maxim Integrated, "MAX31865 RTD-to-Digital Converter Datasheet"
3. Texas Instruments, "A Basic Guide to RTD Measurements" (SBAA275)
4. Analog Devices, "RTD Interfacing and Linearization Using Standard Analog Components" (AN-709)
5. 李刚等, 传感器原理及工程应用, 电子工业出版社
6. Callendar, H.L., "On the Practical Measurement of Temperature", Phil. Trans. Royal Society, 1887
7. OMEGA Engineering, "RTD Practical Guidelines" Technical Reference
