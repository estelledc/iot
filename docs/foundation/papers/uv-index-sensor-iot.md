# 紫外线指数传感器UV检测技术与校准

> **难度**：🟡 中级 | **领域**：光电传感、光谱加权、IoT 环境监测 | **阅读时间**：约 18 分钟

## 日常类比

你去海边玩，出门前打开天气 App 看到一个数字——"紫外线指数 8，建议涂防晒霜"。这个数字不是简单量"阳光有多强"，而是把不同波长的紫外光按"对皮肤伤害有多大"加权算出来的——就像考试不是每道题一样值分，难题分高、简单题分低，最终得到一个加权总分。

紫外线传感器就是那个"阅卷老师"：先把紫外光按波长分开，再按皮肤敏感度打分，最后加总输出指数。只不过现实中的传感器做不到完美加权，需要硬件滤波 + 软件修正 + 出厂校准三管齐下，才能让那个数字足够靠谱。

## 1. 紫外辐射波段与物理基础

### 1.1 UV 辐射的三段划分

太阳辐射中波长 100–400 nm 的部分称为紫外（UV）波段，按波长细分为三段：

| 波段 | 波长范围 | 到达地表比例 | 主要特征 |
|------|----------|-------------|---------|
| UVA | 315–400 nm | ~95% | 穿透力强，直达真皮层，致皮肤老化与间接 DNA 损伤 |
| UVB | 280–315 nm | ~5% | 能量密度高，直接损伤 DNA，晒伤与皮肤癌主因 |
| UVC | 100–280 nm | ≈0% | 被臭氧层完全吸收，人工源（汞灯、电焊弧）才产生 |

关键点：UVA 占地表紫外辐射的绝大多数，但 UVB 单位能量的生物危害远高于 UVA。UV 指数不是"测总能量"，而是按皮肤红斑反应的光谱敏感度加权。

### 1.2 大气衰减

- **臭氧层**：吸收几乎全部 UVC 和大部分 UVB；臭氧浓度下降 1%，地表 UVB 约增加 2%
- **瑞利散射**：UVB 比 UVA 散射率高约 (400/300)⁴ ≈ 3.2 倍
- **气溶胶与云**：薄云可增加散射 UV（漫射增强），厚云衰减 50–90%

```
E_surface = E_TOA × exp(-τ_ozone × AM) × T_aerosol × T_cloud
AM ≈ 1/cos(θ), τ_ozone ~ 0.3–1.0
```

### 1.3 UV 对人体的影响

| 效应 | 主要波段 | 机制 | 剂量关系 |
|------|---------|------|---------|
| 红斑（晒伤） | UVB > UVA | DNA 光产物 → 细胞凋亡 → 炎症 | S-shaped |
| 皮肤老化 | UVA | ROS → 胶原降解 | 累积性 |
| 黑色素瘤 | UVB + UVA | DNA 突变积累 | 与累积剂量正相关 |
| 维生素 D 合成 | UVB (295–300 nm) | 7-脱氢胆固醇光解 | 极低剂量即可 |
| 白内障 | UVA + UVB | 晶状体蛋白交联 | 累积性 |

## 2. 紫外线指数定义与健康意义

### 2.1 UV Index 的国际定义

UV Index（UVI）由 WHO/WMO/ICNIRP 联合定义：

```
UVI = 40 × ∫ E(λ) × S_er(λ) × dλ

E(λ): 太阳紫外光谱辐照度 (W/m²/nm)
S_er(λ): 红斑作用光谱（CIE 修订版，1998）
积分范围: 250–400 nm
系数 40: 将典型晴天中午值映射到 0–15 范围
```

| UVI 范围 | 等级 | 防护建议 |
|----------|------|---------|
| 0–2 | 低 | 无需特别防护 |
| 3–5 | 中等 | 戴帽、涂 SPF 30+ |
| 6–7 | 高 | 减少户外暴露时间 |
| 8–10 | 很高 | 避免正午外出，SPF 50+ |
| 11+ | 极端 | 户外活动必须有全面防护 |

### 2.2 红斑作用光谱

CIE 红斑作用光谱 S_er(λ) 是 UVI 计算的核心权重函数：

| 波长 (nm) | S_er(λ) | 说明 |
|-----------|---------|------|
| 250–298 | 1.0 | UVB 峰值，归一化为 1 |
| 300 | 0.65 | 快速下降起始 |
| 310 | 0.045 | UVA/UVB 边界 |
| 320 | 0.008 | UVA 开始 |
| 340 | 0.003 | UVA 权重极低 |
| 400 | 0.0001 | 截止 |

核心结论：UVB 对 UVI 的贡献占 80–85%，尽管 UVA 能量远高于 UVB。传感器如果 UVA 泄漏过多，UVI 读数会严重偏高——光谱选择性是 UV 传感器的第一指标。

### 2.3 健康暴露时间估算

`暴露时间(min) = 200 / UVI`（II 型皮肤，UVI=1 对应 0.025 W/m² 红斑加权辐照度）

| UVI | MED 时间 | 建议防护 |
|-----|---------|---------|
| 3 | ~67 min | SPF 15 |
| 6 | ~33 min | SPF 30 + 帽 |
| 9 | ~22 min | SPF 50 + 遮阳 |
| 12 | ~17 min | 避免户外 |

## 3. UV 传感器技术原理

### 3.1 碳化硅（SiC）光电二极管

SiC 宽禁带（Eg = 3.26 eV），天然对可见光不响应：

- **光谱范围**：200–380 nm（峰值 ~280 nm），可见光截止优于 10⁻⁴
- **暗电流**：fA 级（宽禁带使本征载流子浓度极小）
- **温度系数**：< 0.1%/°C，远优于 Si 基方案
- **耐辐射性**：抗 UV 退化，适合长期户外部署

典型器件：Infineon SI-CQD 系列、Roithner Laser SiC-UV。

### 3.2 氮化镓（GaN）光电二极管

GaN 禁带宽度 3.4 eV，"天然盲紫"：光谱 250–365 nm，峰值 ~350 nm；AlGaN 可裁剪截止波长（Al₀.₃Ga₀.₇N 截止 ~310 nm）。量子效率 50–70%，响应纳秒级。挑战：外延成本高，AlGaN 高 Al 含量时缺陷密度上升。

### 3.3 滤波硅光电二极管

硅响应 200–1100 nm，叠层介电干涉滤光片实现 UV 选择性。优势：成熟工艺、低成本。劣势：角度依赖性（入射角 > 30° 通带蓝移，UVI 偏差 20%）、可见光泄漏（带外抑制 10⁻³–10⁻⁴）、温度系数 0.1–0.3%/°C。

### 3.4 三种技术路线对比

| 指标 | SiC PD | GaN PD | 滤波 Si PD |
|------|--------|--------|-----------|
| 光谱范围 | 200–380 nm | 250–365 nm | 280–400 nm |
| 可见光抑制 | 10⁻⁴ | 10⁻³ | 10⁻³–10⁻⁴ |
| 暗电流 | fA 级 | pA 级 | pA–nA 级 |
| 温度系数 | < 0.1%/°C | ~0.1%/°C | 0.1–0.3%/°C |
| 成本 | 高 | 中高 | 低 |
| 耐久性 | 优秀 | 良好 | 滤光片可能退化 |
| 典型应用 | 基准仪器 | 工业/科研 | 消费级 IoT |

## 4. 主流 UV 传感器芯片对比

### 4.1 综合对比表

- **VEML6075**：双通道 Si PD + 滤光片，分别测 UVA/UVB，I2C，16 位 ADC
- **SI1145**：单 Si PD + 光窗，UV 模式输出内部估算 UVI，附加 ALS + PS
- **GUVA-S12SD**：SiC 肖特基 PD，模拟电压输出 0–1.1 V，峰值 ~300 nm 接近红斑光谱
- **LTR-390UV**：Si PD + UV 滤光片 + 16 位 ADC，UV + ALS 双通道

| 参数 | VEML6075 | SI1145 | GUVA-S12SD | LTR-390UV |
|------|----------|--------|-----------|-----------|
| 探测器 | Si + 滤光片 | Si + 光窗 | SiC 肖特基 | Si + 滤光片 |
| 通道数 | 2(UVA+UVB) | 1(UV+ALS+PS) | 1(UV) | 2(UV+ALS) |
| 接口 | I2C | I2C | 模拟电压 | I2C |
| 峰值波长 | 365/315 nm | ~350 nm | ~300 nm | ~330 nm |
| 可见光抑制 | 10⁻³ | 10⁻² | 10⁻⁴ | 10⁻³ |
| 工作电流 | 550 μA | ~500 μA | ~0.3 mA | 400 μA |
| 典型价格 | $2–3 | $3–4 | $1–2 | $2–3 |
| 适用场景 | 可穿戴/气象站 | 手环/便携 | 低成本 IoT | 智能家居/气象 |

## 5. 光谱加权与 UVI 计算

### 5.1 从原始传感器值到 UVI

传感器原始输出不等于 UVI，需要光谱加权修正。以 VEML6075 为例：

```
UVA_comp = UVA_raw - UVB_raw × 2.22 - VIS_comp × 1.67
UVB_comp = UVB_raw - UVA_raw × 1.0 - VIS_comp × 0.78
UVI = UVA_comp × α + UVB_comp × β

α, β: 出厂校准系数，与积分时间相关
```

GUVA-S12SD 简化计算：`UVI = V_out / V_per_UVI`，V_per_UVI（典型 ~0.1 V/UVI）需标准光源校准。

### 5.2 余弦校正

传感器对斜射光的响应须遵循朗伯余弦定律 R(θ) = cos(θ)。大多数传感器在 θ > 60° 时偏离，需软件修正：

```python
import math

def cosine_correction(raw_uvi, zenith_deg):
    """斜射 UV 余弦校正"""
    theta = math.radians(zenith_deg)
    ideal = math.cos(theta)
    if ideal <= 0: return 0.0
    # 传感器角度响应二次修正模型
    actual = ideal * (1.0 + 0.05 * theta**2 / (math.pi/2)**2)
    return max(0.0, raw_uvi * ideal / actual)

print(f"校正后 UVI: {cosine_correction(6.5, 45):.1f}")  # ≈ 5.9
```

### 5.3 温度补偿

UV 传感器输出随温度漂移，典型系数 0.1–0.3%/°C：

```python
def temp_compensate(raw_uvi, temp_C, ref=25):
    """温度补偿 UVI"""
    COEFF = 0.002  # 0.2%/°C
    return max(0.0, raw_uvi / (1 + COEFF * (temp_C - ref)))

print(f"补偿后 UVI: {temp_compensate(8.0, 35):.1f}")  # ≈ 7.8
```

## 6. 校准方法与标准溯源

### 6.1 校准层级

| 层级 | 仪器 | 不确定度 | 用途 |
|------|------|---------|------|
| 一级标准 | NIST 双单色仪光谱辐射计 | ±1–2% | 国家基准 |
| 二级标准 | 已校准光谱辐射计 | ±3–5% | 传递标准 |
| 工作标准 | 已校准宽带 UV 表 | ±5–10% | 生产线校准 |
| 现场 | 待校准 IoT 传感器 | ±10–20% | 实际部署 |

### 6.2 实验室校准流程

1. 光谱响应度校准：单色仪逐波长扫描，获得 R(λ)
2. UVI 校准：太阳模拟器下与参考仪器同时测量
3. 角度响应校准：旋转 0–85°，记录偏差
4. 温度校准：温控箱 0–50°C 测量系数

### 6.3 现场校准——太阳参考法

对已部署的 IoT 传感器网络，利用晴空辐射模型进行现场校准：

```python
def solar_calibration(sensor_uvis, times, lat, lon):
    """利用太阳辐射模型对传感器进行现场校准"""
    import numpy as np
    ref_uvis = []
    for t in times:
        sza = calculate_solar_zenith(t, lat, lon)
        if sza > 85:
            continue
        # 简化晴空模型：UVI ≈ 12 × cos(SZA) × ozone × alt
        ref_uvi = 12.0 * np.cos(np.radians(sza))
        ref_uvis.append(ref_uvi)
    # 线性回归求校准系数
    sensor_arr = np.array(sensor_uvis[:len(ref_uvis)])
    ref_arr = np.array(ref_uvis)
    slope, intercept = np.polyfit(sensor_arr, ref_arr, 1)
    r2 = np.corrcoef(sensor_arr, ref_arr)[0,1]**2
    print(f"校准系数: slope={slope:.3f}, intercept={intercept:.3f}, R²={r2:.3f}")
    return slope, intercept
```

### 6.4 校准不确定度分析

| 不确定度来源 | 典型贡献 | 说明 |
|-------------|---------|------|
| 光谱失配 | 3–8% | 传感器光谱响应与红斑光谱偏差 |
| 角度响应 | 2–5% | 偏离余弦定律 |
| 温度漂移 | 1–3% | 未经补偿时 |
| 参考仪器 | 1–5% | 取决于校准链溯源 |
| 合成不确定度 (k=2) | 5–15% | 取决于传感器品质和校准等级 |

## 7. 代码实例：ESP32 读取 UVI

### 7.1 VEML6075 完整驱动（Arduino/C++）

```cpp
#include <Wire.h>
#define VEML6075_ADDR 0x10
#define REG_UVA    0x07
#define REG_UVB    0x09
#define REG_COMP1  0x0A
#define REG_COMP2  0x0B
#define REG_CONF   0x02

// UVI 计算系数
#define UVA_UVI  0.001461
#define UVB_UVI  0.002591

uint16_t readReg(uint8_t reg) {
    Wire.beginTransmission(VEML6075_ADDR);
    Wire.write(reg);
    Wire.endTransmission(false);
    Wire.requestFrom(VEML6075_ADDR, (uint8_t)2);
    uint16_t val = Wire.read();
    val |= (uint16_t)Wire.read() << 8;
    return val;
}

void setup() {
    Serial.begin(115200);
    Wire.begin();
    // 配置：积分时间 100ms
    Wire.beginTransmission(VEML6075_ADDR);
    Wire.write(REG_CONF); Wire.write(0x02); Wire.write(0x00);
    Wire.endTransmission();
    delay(50);
}

void loop() {
    uint16_t uva = readReg(REG_UVA);
    uint16_t uvb = readReg(REG_UVB);
    uint16_t c1  = readReg(REG_COMP1);
    uint16_t c2  = readReg(REG_COMP2);
    // 可见光补偿后计算 UVI
    float uva_c = uva - 2.22 * uvb - 1.67 * c1;
    float uvb_c = uvb - 1.0  * uva - 0.78 * c1;
    float uvi = max(0.0f, uva_c * UVA_UVI + uvb_c * UVB_UVI);
    Serial.printf("UVI: %.1f\n", uvi);
    delay(2000);
}
```

### 7.2 GUVA-S12SD 模拟读取 + MQTT 上报（MicroPython）

```python
import machine, time, json
from umqtt.simple import MQTTClient

adc = machine.ADC(machine.Pin(34))
adc.atten(machine.ADC.ATTN_11DB)
CAL_FACTOR = 0.1  # V/UVI，需实测校准

def read_uvi():
    samples = [adc.read() for _ in range(16)]
    voltage = (sum(samples) / len(samples)) * 3.3 / 4095
    return max(0.0, round(voltage / CAL_FACTOR, 1))

def level(uvi):
    if uvi <= 2:   return "low"
    if uvi <= 5:   return "moderate"
    if uvi <= 7:   return "high"
    if uvi <= 10:  return "very_high"
    return "extreme"

client = MQTTClient("uv_01", "192.168.1.100")
client.connect()

while True:
    uvi = read_uvi()
    payload = json.dumps({"uvi": uvi, "level": level(uvi), "ts": time.time()})
    client.publish(b"iot/uv/data", payload)
    print(f"Published UVI={uvi}")
    time.sleep(60)
```

## 8. IoT 应用场景

### 8.1 可穿戴设备

- **需求**：极低功耗（间歇采样，平均 < 10 μA）、小封装（< 3×3 mm）
- **典型方案**：SI1145（集成 ALS + PS + UV）或 VEML6075
- **挑战**：佩戴角度不确定导致余弦校正困难；手腕 UVI 与面部有差异

### 8.2 气象站与环境监测

- **精度**：±10% UVI，需定期校准
- **防护**：IP65+ 外壳 + 石英光学窗口（UV 透过率远优于普通玻璃）
- **传输**：MQTT/CoAP + LoRa/NB-IoT
- **部署**：高度 1.5–2 m，无遮挡；定期清洁光学窗口（灰尘可衰减 UV 信号 20–50%）

### 8.3 工业 UV 固化监测

- **需求**：实时检测 UV 固化灯输出强度，确保固化质量一致
- **挑战**：高强度（1–10 W/cm²，需衰减片）、高温（> 60°C，需散热）
- **方案**：SiC PD + 衰减片 + 温度补偿；灯管老化衰减 > 15% 时自动报警

### 8.4 智能农业与公共健康

- **农业**：温室 UV 补光控制、大棚膜老化透过率监测、UV 应激预警
- **公共健康**：城市级 UV 传感器网络 → 实时 LED 屏显示 UVI → UVI > 8 自动推送告警 → 与卫星遥感交叉验证提升预报精度

## 9. 总结与展望

### 9.1 核心要点回顾

1. **UV 辐射分段**：UVA 占能量主体，UVB 是健康危害核心，UVC 被大气完全吸收
2. **UVI 不是能量**：UVI 是红斑加权指数，UVB 权重远高于 UVA，传感器须具备光谱选择性
3. **传感器选型**：SiC 天然盲紫但昂贵，滤波 Si 成本低但串扰和角度响应受限，GaN 介于两者之间
4. **校准不可或缺**：原始值到 UVI 需光谱加权、余弦校正、温度补偿，不确定度 5–15%

### 9.2 技术趋势

| 方向 | 现状 | 展望 |
|------|------|------|
| 宽禁带半导体 | SiC/GaN 已商用 | AlGaN 全固态 UVC 探测 |
| 片上光谱仪 | 滤光片阵列 | 纳米超表面滤波，微型 UV 光谱仪 |
| AI 校准 | 线性补偿 | 机器学习多传感器融合，不确定度降至 5% |
| 超低功耗 | μA 级工作电流 | 能量收集驱动，免维护部署 |
| 标准化 | CIE 1998 版 | 纳入 UVA1 和蓝光损伤权重 |
| 集成化 | UV + ALS 分立 | UV/ALS/IR 三合一单芯片 |

### 9.3 给 IoT 开发者的建议

- 选型优先关注可见光抑制比，而非绝对灵敏度
- 务必做余弦校正，否则斜射光下 UVI 误差 > 20%
- 石英窗口 > 玻璃窗口（普通玻璃 300 nm 以下透过率 < 1%）
- 户外部署每月清洁光学窗口；滤波 Si PD 年衰减 1–3%，1–2 年重校准
- 预算允许时双通道（UVA + UVB）远优于单通道

## 参考资料

1. WHO. (2002). Global Solar UV Index: A Practical Guide. World Health Organization.
2. CIE. (1998). Erythema Reference Action Spectrum and Standard Erythema Dose. CIE S 007/E.
3. Vishay. (2024). VEML6075 Datasheet: UVA and UVB Light Sensor. Rev 1.8.
4. Silicon Labs. (2023). SI1145/46/47 Datasheet. Rev 1.4.
5. Lite-On. (2023). LTR-390UV Datasheet. Rev 1.0.
6. Seckmeyer, G. et al. (2001). Instruments to measure solar UV radiation. WMO/GAW Report No. 126.
7. McKenzie, R. L. et al. (2003). Changes in biologically active UV radiation. Photochem. Photobiol. Sci., 2(1), 5–15.
8. Köhler, M. et al. (2023). Wide-bandgap semiconductor UV photodetectors. Adv. Mater., 35(22), 2209425.
9. Zaimi, I. et al. (2024). ML-based calibration of low-cost UV sensors for IoT. Sensors, 24(3), 892.
10. Diffey, B. L. (2002). Sources and measurement of ultraviolet radiation. Methods, 28(1), 4–13.
