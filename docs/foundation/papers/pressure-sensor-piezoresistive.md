---
schema_version: '1.0'
id: pressure-sensor-piezoresistive
title: 压阻式压力传感器工作原理与MEMS制造
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
# 压阻式压力传感器工作原理与MEMS制造

> **难度**：🟡 中级 | **领域**：压力传感、MEMS工艺、工业IoT | **阅读时间**：约 20 分钟

## 日常类比

想象你站在一块薄木板上，木板会微微弯曲。你的体重越重，弯曲越明显。压阻式压力传感器里的"木板"就是一片极薄的硅膜片（diaphragm），而"弯曲"就是膜片受力后产生的应变。只不过，传感器不是用肉眼观察弯曲程度，而是利用硅材料的一个奇妙特性——受力后电阻率会发生变化，这就是**压阻效应**。

再想一个例子：四个人手拉手围成一圈，每个人代表一个电阻。如果其中两人被"拉伸"（阻力增大），另外两人被"压缩"（阻力减小），整个圆圈的力量平衡就被打破了。传感器里的四个压敏电阻正是这样排列在硅膜片上，组成惠斯通电桥。压力一旦变化，电桥就输出电压信号——就像天平两端的砝码发生偏移，指针立刻偏转。

这种"力 → 形变 → 电阻变化 → 电压输出"的转换链路，就是压阻式压力传感器的核心逻辑。它的灵敏度远高于金属应变片，且可以通过 MEMS 工艺在硅片上批量制造，因此成为工业 IoT 中最主流的压力传感方案之一。

## 1. 压阻效应基础

### 1.1 物理机制

压阻效应（piezoresistive effect）指材料在机械应力作用下电阻率发生改变的现象。1856 年，开尔文勋爵首次在金属中观察到该效应，但金属的压阻系数极低（约 \(G \approx 1\text{–}2\)）。直到 1954 年，Smith 在硅和锗中发现了显著的压阻效应——单晶硅的压阻系数比金属高 1–2 个数量级，纵向压阻系数 \(π_l\) 可达 \(10^{-10}\ \text{Pa}^{-1}\) 量级。

其微观机制是：应力改变了硅晶格中载流子（电子与空穴）的迁移率。对于 p 型硅，沿 \([110]\) 晶向施加应力时，价带空穴的有效质量与散射概率发生改变，宏观表现为电阻率变化。

### 1.2 压阻系数与灵敏度

压阻效应是各向异性的。对于 (100) 硅片上沿 \([110]\) 和 \([\bar{1}10]\) 晶向布置的压敏电阻，电阻变化率可表示为纵向与横向应力分量的线性组合：

\[
\frac{\Delta R}{R} = π_l \sigma_l + π_t \sigma_t
\]

其中纵向压阻系数 \(π_l = \frac{1}{2}(π_{11} + π_{12} + π_{44})\)，横向压阻系数 \(π_t = \frac{1}{2}(π_{11} + π_{12} - π_{44})\)。p 型硅的 \(π_{44}\) 远大于 \(π_{11}\) 和 \(π_{12}\)，因此纵向和横向系数差异显著，这也是惠斯通电桥中电阻两两"拉压交替"布局的理论依据。

灵敏度公式为 \(S = V_{out}/V_{in}\)，全桥时 \(S = \Delta R / R\)，半桥时 \(S = \Delta R / (2R)\)。典型 MEMS 压阻式压力传感器的灵敏度为 10–100 mV/V/FS，远高于金属应变片的 1–3 mV/V/FS。

## 2. MEMS 压力传感器结构

### 2.1 硅膜片

硅膜片是传感器的力敏元件，通常为圆形或方形薄板结构。其厚度决定了量程：

| 量程范围 | 典型膜片厚度 | 典型边长/直径 |
|----------|-------------|---------------|
| 0–1 kPa（微压） | 5–10 μm | 1–2 mm |
| 0–100 kPa（低压） | 15–30 μm | 0.5–1 mm |
| 0–1 MPa（中压） | 50–100 μm | 0.3–0.5 mm |
| 0–10 MPa（高压） | 150–300 μm | 0.2–0.3 mm |

膜片在小挠度条件下（挠度 < 厚度/5），中心挠度与压力近似线性关系：

\[
w_0 = \frac{3(1-\nu^2) p a^4}{16 E h^3}
\]

其中 \(p\) 为压力，\(a\) 为边长，\(h\) 为厚度，\(E\) 为弹性模量，\(\nu\) 为泊松比。

### 2.2 压敏电阻布局

在方形膜片上，四个压敏电阻布置在膜片边缘的应力集中区域：

- **R1、R3**：沿 \([\bar{1}10]\) 晶向，受纵向压应力 → 电阻减小
- **R2、R4**：沿 \([110]\) 晶向，受横向拉应力 → 电阻增大

这种布局使四个电阻的 \(\Delta R\) 符号两两相反，在惠斯通电桥中实现推挽（push-pull）工作，灵敏度比半桥提高一倍，且共模误差（如温度漂移）被抵消。

### 2.3 惠斯通电桥

```
        V_in (+)
         │
    ┌────┤────┐
    │    │    │
   R1    │   R2
    │    │    │
    ├────┼────┤ ── V_out (+)
    │    │    │
   R3    │   R4
    │    │    │
    └────┤────┘ ── V_out (-)
         │
        GND
```

电桥输出电压：

\[
V_{out} = V_{in} \cdot \frac{R_1 R_4 - R_2 R_3}{(R_1 + R_2)(R_3 + R_4)}
\]

初始状态 \(R_1 = R_2 = R_3 = R_4\) 时，\(V_{out} = 0\)；受压后 \(R_1, R_4\) 减小而 \(R_2, R_3\) 增大，电桥失平衡，输出与压力成正比的差分电压。

### 2.4 封装结构

典型封装包含：感压芯片（硅膜片 + 压敏电阻 + 参考真空腔/通气管）、玻璃基座（阳极键合密封）、金属/陶瓷外壳（TO-5/DIP）、导压管孔。

## 3. MEMS 制造工艺

### 3.1 体微加工与面微加工

MEMS 压力传感器的制造主要采用两种工艺路线：

| 特征 | 体微加工（Bulk Micromachining） | 面微加工（Surface Micromachining） |
|------|-------------------------------|----------------------------------|
| 加工对象 | 硅衬底本身 | 沉积在衬底上的薄膜层 |
| 结构厚度 | 50–500 μm | 0.5–5 μm |
| 典型工艺 | KOH/TMAH 各向异性湿法腐蚀 | 牺牲层释放（如 PSG/SiO₂） |
| 膜片形成 | 从背面腐蚀出腔体 | 正面沉积薄膜 + 下方牺牲层去除 |
| 优势 | 结构厚、机械强度高 | 与 CMOS 工艺兼容性好 |
| 劣势 | 尺寸较大、双面对准 | 薄膜应力控制困难 |

工业级压力传感器主流采用体微加工工艺，因其膜片厚度可控、机械可靠性高。

### 3.2 典型工艺流程

以体微加工绝压型传感器为例，主要步骤如下：

1. **衬底准备**：选用 (100) 晶向 n 型硅片，厚度 400–500 μm
2. **氧化**：热生长 1 μm SiO₂ 作为掩膜和钝化层
3. **光刻**：在正面定义压敏电阻区域，背面定义腐蚀窗口
4. **离子注入**：硼离子注入形成 p 型压敏电阻，剂量 \(10^{14}\text{–}10^{15}\ \text{cm}^{-2}\)
5. **退火**：1050°C 快速热退火激活掺杂、修复晶格损伤
6. **接触孔光刻与金属化**：刻蚀接触孔，溅射 Al/Si 形成互连
7. **背面腐蚀**：KOH 溶液（浓度 30–40%，温度 80°C）各向异性腐蚀，形成方形膜片
8. **硅-玻璃键合**：与 #7740 Pyrex 玻璃阳极键合（400°C、1000V），密封参考真空腔
9. **划片与封装**：激光划片，芯片粘接与引线键合

### 3.3 关键工艺参数与 CMOS 集成

- **腐蚀速率控制**：KOH 腐蚀 (100) 面约 1 μm/min，(111) 面速率低 100–400 倍，可自停止形成精确腔体
- **掺杂浓度**：需权衡灵敏度与温度系数——低掺杂灵敏度高但 TCR 大，典型表面浓度 \(10^{19}\ \text{cm}^{-3}\)
- **膜片厚度均匀性**：决定量程一致性，要求片内 ±2% 以内

先进工艺将传感单元与信号调理电路集成在同一芯片上（CMOS-MEMS 单片集成）：

- **前置方案**：先做 CMOS 电路，再从背面腐蚀出膜片
- **后置方案**：先腐蚀膜片，再沉积薄膜电路
- **混合信号方案**：模拟前端 + ADC + 数字校准在同一管芯

单片集成的优势是寄生电容小、信噪比高、可片上温度补偿；劣势是工艺复杂度增加、良率下降。

## 4. 压力传感器类型对比

| 特性 | 压阻式 | 电容式 | 压电式 | 光纤式 |
|------|--------|--------|--------|--------|
| **原理** | 压阻效应（电阻变化） | 极板间距变化（电容变化） | 正压电效应（电荷产生） | 光纤布拉格光栅波长偏移 |
| **量程** | 0.1 kPa–100 MPa | 0.01 kPa–10 MPa | 0.1 kPa–500 MPa | 0.1 MPa–100 MPa |
| **精度** | 0.05%–1% FS | 0.01%–0.5% FS | 0.5%–2% FS | 0.01%–0.1% FS |
| **频率响应** | DC–100 kHz | DC–1 MHz | 0.1 Hz–1 MHz | DC–100 kHz |
| **功耗** | 中（1–10 mW） | 低（0.1–1 mW） | 极低（自发电） | 中（光源功耗） |
| **温度范围** | -40°C–125°C | -40°C–175°C | -55°C–300°C | -40°C–300°C |
| **抗电磁干扰** | 弱 | 中 | 弱 | 极强 |
| **MEMS 兼容性** | 优 | 优 | 中 | 差 |
| **成本** | 低 | 中 | 中 | 高 |
| **典型应用** | 工业过程控制、血压计 | 触摸屏、高度计 | 爆炸压力、声学 | 油井监测、电力 |

**选择建议**：

- 低成本、批量生产、精度要求中等 → 压阻式
- 超低功耗、微小压力变化 → 电容式
- 动态/冲击压力测量 → 压电式
- 强电磁干扰环境 → 光纤式

## 5. 信号调理与温度补偿

### 5.1 信号调理电路

压阻式传感器的原始输出通常为 50–200 mV 满量程，需要放大到 ADC 可用的 0–3.3V 或 0–5V 范围：

1. **仪表放大器**：高共模抑制比（CMRR > 80 dB），如 INA333、AD8421
2. **低通滤波**：RC 滤波（截止频率 100 Hz–10 kHz）或数字滤波，抑制高频噪声
3. **ADC 采样**：16–24 位 Σ-Δ ADC（如 ADS1220、HX711），分辨率可达 0.01% FS

### 5.2 温度补偿

压阻式传感器的主要温度误差来源：

- **零位温度漂移（TCO）**：0.01%–0.05% FS/°C
- **灵敏度温度漂移（TCS）**：-0.15%–-0.25% FS/°C（p 型硅灵敏度随温度升高而降低）

**模拟补偿方法**：

- 零位补偿：在电桥输出端串联热敏电阻网络
- 灵敏度补偿：用 PTC 电阻与恒流源串联，温度升高时激励电流增大，补偿灵敏度下降

**数字补偿方法**：

现代传感器多采用数字补偿，在芯片内嵌入温度传感器和校准 EEPROM：

1. 在多个温度点（如 -40°C、25°C、85°C、125°C）和压力点测量输出
2. 拟合二维多项式：\(P = f(V_{bridge}, V_{temp})\)
3. 将多项式系数存入 EEPROM
4. 运行时实时读温度，插值计算补偿后压力值

BMP280、MS5837 等集成传感器即采用此方案，校准系数出厂时逐片写入。

## 6. 代码示例：I2C 读取压阻式压力传感器

以下以 BMP280（集成压阻式压力传感器 + 温度传感器）为例，通过 I2C 接口读取校准后的压力值：

```python
# bmp280_reader.py
# 通过 I2C 读取 BMP280 压阻式压力传感器
# 适用平台：Raspberry Pi / Linux SBC

import smbus2  # I2C 通信库
import time

# ---- BMP280 寄存器地址 ----
BMP280_ADDR        = 0x76   # I2C 地址（SDO 接 GND 时为 0x76，接 VDD 时为 0x77）
REG_CHIP_ID       = 0xD0   # 芯片 ID 寄存器，应返回 0x58
REG_RESET         = 0xE0   # 软复位寄存器
REG_CTRL_MEAS     = 0xF4   # 测量控制寄存器（压力/温度过采样 + 工作模式）
REG_CONFIG        = 0xF5   # 配置寄存器（待机时间 + 滤波系数）
REG_PRESS_MSB     = 0xF7   # 压力数据 MSB
REG_TEMP_MSB      = 0xFA   # 温度数据 MSB
REG_DIG_T1        = 0x88   # 温度校准参数起始地址

class BMP280:
    """BMP280 压阻式压力传感器驱动"""

    def __init__(self, bus_id=1, address=BMP280_ADDR):
        self.bus = smbus2.SMBus(bus_id)
        self.addr = address
        chip_id = self._read_byte(REG_CHIP_ID)
        if chip_id != 0x58:
            raise RuntimeError(f"芯片 ID 不匹配：读取 0x{chip_id:02X}，期望 0x58")
        self._load_calibration()          # 加载出厂校准系数
        self._soft_reset()                # 软复位确保已知状态
        # 设置：压力过采样 x4，温度过采样 x1，正常工作模式
        self._write_byte(REG_CTRL_MEAS, 0x2B)  # osrs_t=001, osrs_p=100, mode=11
        # 设置：待机 125ms，IIR 滤波系数 4
        self._write_byte(REG_CONFIG, 0x5C)     # t_sb=100, filter=100, spi3w=0

    def _read_byte(self, reg):
        """读取单个寄存器"""
        return self.bus.read_byte_data(self.addr, reg)

    def _write_byte(self, reg, value):
        """写入单个寄存器"""
        self.bus.write_byte_data(self.addr, reg, value)

    def _read_word_signed(self, reg, is_signed=True):
        """读取 16 位校准参数（小端序）"""
        lsb = self._read_byte(reg)
        msb = self._read_byte(reg + 1)
        val = (msb << 8) | lsb
        if is_signed and val >= 0x8000:
            val -= 0x10000  # 二进制补码转换
        return val

    def _load_calibration(self):
        """从 EEPROM 加载出厂校准系数（数字温度补偿核心）"""
        self.dig_T1 = self._read_word_signed(REG_DIG_T1, is_signed=False)
        self.dig_T2 = self._read_word_signed(REG_DIG_T1 + 2)
        self.dig_T3 = self._read_word_signed(REG_DIG_T1 + 4)
        self.dig_P1 = self._read_word_signed(REG_DIG_T1 + 6, is_signed=False)
        self.dig_P2 = self._read_word_signed(REG_DIG_T1 + 8)
        self.dig_P3 = self._read_word_signed(REG_DIG_T1 + 10)
        self.dig_P4 = self._read_word_signed(REG_DIG_T1 + 12)
        self.dig_P5 = self._read_word_signed(REG_DIG_T1 + 14)
        self.dig_P6 = self._read_word_signed(REG_DIG_T1 + 16)
        self.dig_P7 = self._read_word_signed(REG_DIG_T1 + 18)
        self.dig_P8 = self._read_word_signed(REG_DIG_T1 + 20)
        self.dig_P9 = self._read_word_signed(REG_DIG_T1 + 22)

    def _soft_reset(self):
        """写入 0xB6 触发软复位"""
        self._write_byte(REG_RESET, 0xB6)
        time.sleep(0.1)  # 等待复位完成

    def _read_raw_temp(self):
        """读取 20 位原始温度数据"""
        msb = self._read_byte(REG_TEMP_MSB)
        lsb = self._read_byte(REG_TEMP_MSB + 1)
        xlsb = self._read_byte(REG_TEMP_MSB + 2)
        return (msb << 12) | (lsb << 4) | (xlsb >> 4)

    def _read_raw_pressure(self):
        """读取 20 位原始压力数据"""
        msb = self._read_byte(REG_PRESS_MSB)
        lsb = self._read_byte(REG_PRESS_MSB + 1)
        xlsb = self._read_byte(REG_PRESS_MSB + 2)
        return (msb << 12) | (lsb << 4) | (xlsb >> 4)

    def compensate_temp(self, raw_t):
        """温度补偿算法（Bosch 官方文档公式）"""
        var1 = ((raw_t / 16384.0) - (self.dig_T1 / 1024.0)) * self.dig_T2
        var2 = ((raw_t / 131072.0) - (self.dig_T1 / 8192.0)) ** 2 * self.dig_T3
        self.t_fine = var1 + var2  # 保存 t_fine 供压力补偿使用
        return (var1 + var2) / 5120.0

    def compensate_pressure(self, raw_p):
        """压力补偿算法（含温度修正）"""
        var1 = self.t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = var2 / 4.0 + self.dig_P4 * 65536.0
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        if var1 == 0:
            return 0  # 避免除零
        p = 1048576.0 - raw_p
        p = (p - var2 / 4096.0) * 6250.0 / var1
        var1 = self.dig_P9 * p * p / 2147483648.0
        var2 = p * self.dig_P8 / 32768.0
        p = p + (var1 + var2 + self.dig_P7) / 16.0
        return p  # 单位：Pa

    def read(self):
        """读取补偿后的温度和压力"""
        raw_t = self._read_raw_temp()
        raw_p = self._read_raw_pressure()
        temp = self.compensate_temp(raw_t)
        pressure = self.compensate_pressure(raw_p)
        return temp, pressure


# ---- 使用示例 ----
if __name__ == "__main__":
    sensor = BMP280(bus_id=1)
    while True:
        temp, pressure = sensor.read()
        altitude = 44330.0 * (1.0 - (pressure / 101325.0) ** (1.0 / 5.255))
        print(f"温度: {temp:.2f} °C | 气压: {pressure:.0f} Pa "
              f"| 估算海拔: {altitude:.1f} m")
        time.sleep(1)
```

### 6.1 关键代码说明

- **校准系数加载**（`_load_calibration`）：BMP280 出厂时在内部 EEPROM 中写入了 12 个校准参数，这些参数用于补偿压阻传感器的零位漂移和灵敏度温度漂移，是数字补偿方案的核心
- **温度先行补偿**：`compensate_temp` 先计算 `t_fine`，`compensate_pressure` 再利用 `t_fine` 完成温度修正后的压力计算——这体现了"先测温、后补偿"的两步补偿策略
- **IIR 滤波**：`REG_CONFIG` 中设置滤波系数为 4，相当于对连续 5 次采样做加权平均，有效抑制高频噪声

## 7. IoT 应用场景

### 7.1 工业过程控制

在化工、石油、制药等行业，压阻式压力传感器用于管道压力监测、液位测量、泄漏检测：

- **量程选择**：根据工艺压力范围选择 0.1%–0.5% FS 精度等级
- **介质兼容性**：腐蚀性介质需采用 316L 不锈钢隔离膜片 + 硅油传压结构
- **防爆认证**：易燃易爆环境需 ATEX/IECEx 认证的本安型传感器
- **通信协议**：4–20 mA 电流环、HART、Modbus RTU、IO-Link

### 7.2 气象站与高度测量

大气压力是气象观测的基本参数之一：

- 绝压型压阻传感器测量 300–1100 hPa 大气压
- 结合温度和湿度数据，可估算海拔高度（精度 ±1 m）
- 自动气象站通常每 1–10 秒采样一次，需低功耗待机模式
- BMP280/388 等传感器支持 1 Hz 采样下低于 2.7 μA 的平均功耗

### 7.3 可穿戴设备

智能手表、运动手环中的气压计用于楼层检测和海拔追踪：

- **微型封装**：LGA 封装 2.0 × 2.0 × 0.75 mm（如 BMP388）
- **超低功耗**：1 Hz 采样下平均功耗 < 3 μA
- **动态分辨率**：通过过采样实现 0.01 hPa 分辨率（约 8 cm 海拔变化）
- **运动伪影抑制**：加速度计辅助剔除运动引起的压力波动

### 7.4 医疗与生物

血压计（0–300 mmHg，±1 mmHg）、呼吸机微压监测（0–100 cmH₂O）、眼压计（0–60 mmHg）等场景均采用压阻方案，追求高精度与低力接触。

## 8. 常见失效模式与可靠性

### 8.1 失效模式分类

| 失效模式 | 机理 | 预防措施 |
|----------|------|----------|
| 过载破裂 | 压力超过膜片屈服强度 | 机械限位结构 + 软件超压报警 |
| 蠕变漂移 | 长期恒压下硅膜片位错滑移 | 控制工作压力 < 75% FS，定期校准 |
| 湿气侵入 | 封装密封失效致参考腔污染 | 气密性封装（金属-玻璃封接）|
| 热冲击 | 快速温变致膜片热应力开裂 | 限定温度变化率 < 10°C/min |
| 电磁干扰 | 输出线拾取共模噪声 | 屏蔽电缆 + 差分走线 + 滤波电容 |
| 离子污染 | 腐蚀性介质渗入芯片表面 | 隔离膜片 + 硅油传压结构 |
| 疲劳失效 | 压力循环致膜片微裂纹累积 | 控制压力循环幅值，加速寿命测试验证 |

### 8.2 可靠性指标与加速测试

工业级传感器的典型可靠性参数：MTBF > 100 万小时、压力循环寿命 > 1 亿次、长期稳定性 < 0.1% FS/年。

加速寿命测试常采用 Arrhenius 模型：

常见加速测试方法：

```c
// 加速寿命测试配置示例（伪代码）
typedef struct {
    float pressure_min;      // 最小循环压力 (kPa)
    float pressure_max;      // 最大循环压力 (kPa)
    float cycle_freq;        // 循环频率 (Hz)
    float temp_low;          // 低温端 (°C)
    float temp_high;         // 高温端 (°C)
    int   total_cycles;      // 总循环次数
    int   read_interval;     // 读数间隔（每 N 次循环读一次）
} AltLifeTestConfig;

AltLifeTestConfig industrial_test = {
    .pressure_min  = 0.0f,
    .pressure_max  = 500.0f,      // 50% FS for 1 MPa sensor
    .cycle_freq    = 5.0f,        // 5 Hz 循环
    .temp_low      = -40.0f,
    .temp_high     = 125.0f,
    .total_cycles  = 100000000,   // 1 亿次
    .read_interval = 10000,       // 每 1 万次采样一次
};

// Arrhenius 加速因子计算
// AF = exp[Ea/k * (1/T_use - 1/T_stress)]
// Ea = 0.7 eV（硅器件典型激活能）
// k = 8.617e-5 eV/K（玻尔兹曼常数）
float calc_acceleration_factor(float t_use, float t_stress) {
    const float Ea = 0.7f;            // 激活能 (eV)
    const float k  = 8.617e-5f;       // 玻尔兹曼常数 (eV/K)
    float t1 = 1.0f / (t_use + 273.15f);
    float t2 = 1.0f / (t_stress + 273.15f);
    return expf(Ea / k * (t1 - t2));  // AF > 1 表示加速
}
// 示例：使用温度 25°C，测试温度 125°C → AF ≈ 350
// 即 125°C 下测试 1 小时 ≈ 25°C 下使用 350 小时
```

## 总结与展望

压阻式压力传感器凭借硅压阻效应的高灵敏度、MEMS 工艺的批量制造能力以及与 CMOS 电路的良好兼容性，已成为 IoT 领域最主流的压力感知方案。从工业过程控制到可穿戴设备，它覆盖了从 0.1 kPa 到 100 MPa 的宽广量程。

当前技术发展趋势：

- **更高集成度**：传感器 + ADC + MCU + 无线通信 SoC 单芯片方案（如 nRF52833 + 压力传感前端）
- **AI 边缘推理**：在传感器节点部署 TinyML 模型，实现异常检测和预测性维护，减少数据传输量
- **新材料探索**：SiC 压阻传感器可在 600°C 以上工作，拓展高温应用场景；石墨烯膜片有望实现超高灵敏度微压测量
- **柔性封装**：可拉伸基板上的压力传感阵列，用于电子皮肤和健康监测
- **自供能传感**：结合压电能量收集与超低功耗设计，实现无需电池的无线压力传感节点

理解压阻式传感器的工作原理与制造工艺，是深入学习工业 IoT 感知层的重要基础。建议结合电容式和压电式传感器的对比学习，建立更完整的压力传感知识体系。

## 参考资料

1. Smith C S. Piezoresistance effect in germanium and silicon[J]. Physical Review, 1954, 94(1): 42-49.
2. Sze S M, Ng K K. Physics of Semiconductor Devices[M]. 3rd ed. Wiley, 2006. Chapter 14: Piezoresistive Sensors.
3. Senturia S D. Microsystem Design[M]. Springer, 2001. Chapters 6-8: MEMS Fabrication and Mechanical Design.
4. Beeby S, Ensell G, Kraft M, et al. MEMS Mechanical Sensors[M]. Artech House, 2004.
5. Bosch Sensortec. BMP280 Digital Pressure Sensor Data Sheet, 2018.
6. Eaton W P, Smith J H. Micromachined pressure sensors: review and recent developments[J]. Smart Materials and Structures, 1997, 6(5): 530-539.
7. Barlian A A, Park W T, Mallon J R, et al. Review: Semiconductor piezoresistance for microsystems[J]. Proceedings of the IEEE, 2009, 97(3): 513-552.
8. CN103 — MEMS 压力传感器设计与应用, 中国集成电路产业白皮书, 2023.
9. Telcordia Technologies. SR-332: Reliability Prediction Procedure for Electronic Equipment, 2016.
