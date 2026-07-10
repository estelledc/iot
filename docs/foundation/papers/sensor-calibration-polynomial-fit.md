---
schema_version: '1.0'
id: sensor-calibration-polynomial-fit
title: 传感器校准：多项式拟合与查找表方法
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
# 传感器校准：多项式拟合与查找表方法
> **难度**：🟡 中级 | **领域**：传感器校准 | **阅读时间**：约 20 分钟

## 引言

买一把新尺子，刻度不一定准——可能是厂家压模偏了零点几毫米。传感器也一样：出厂时的制造公差让它读出来的值和真实值之间总有偏差。校准就像给尺子贴一张"修正表"：你读到 5mm，查表发现实际应该是 4.8mm，于是你就知道该减去 0.2mm。

本文讲解两种最常用的校准数学方法——多项式拟合与查找表，并给出 MCU 上的高效实现。

## 1 为什么传感器需要校准

### 1.1 制造公差

同一批次生产的传感器，其灵敏度和偏移量存在离散性：

- 压力传感器灵敏度公差可达 +/-10%
- 热敏电阻 B 值公差 +/-1%~3%
- 模拟输出传感器的零点偏移可达满量程的 5%

### 1.2 非线性误差

许多传感器的输出与被测物理量之间不是线性关系：

- NTC 热敏电阻的 R-T 曲线是指数型
- 热电偶的 mV-T 关系高阶非线性
- 压力传感器的非线性随量程增大而加剧

### 1.3 偏移误差与增益误差

传感器误差可分解为两类：

- **偏移误差**：零输入时输出不为零，相当于尺子的零刻度偏了
- **增益误差**：灵敏度偏离标称值，相当于尺子的每格比实际大或小

```
理想:  y = a * x + b
实际:  y = (a + da) * x + (b + db)
       增益误差 da     偏移误差 db
```

## 2 校准工作流程

### 2.1 参考标准

校准的前提是有一个比被校传感器精度更高的参考：

- 温度：标准铂电阻温度计（精度 +/-0.01 度C）
- 压力：活塞式压力计（精度 +/-0.005%）
- 电压：标准电压源（6 位半数字表验证）

### 2.2 多点测量

在量程内选取多个校准点，记录传感器原始输出与参考真值：

```
点1: (x1, y1) = (0度C,   3270)
点2: (x2, y2) = (25度C,  2890)
点3: (x3, y3) = (50度C,  2410)
...
```

校准点数量和分布原则：
- 不少于拟合阶数加 1（3 阶拟合至少 4 个点）
- 在量程端点和中间均匀分布
- 非线性严重处加密采样

### 2.3 曲线拟合

根据测量数据，选择数学模型拟合校准曲线：
- 线性关系：两点校准即可
- 轻微非线性：2-3 阶多项式
- 强非线性：查找表或专用方程

## 3 多项式拟合

### 3.1 最小二乘法原理

给定 N 个数据点 (xi, yi)，寻找 n 阶多项式：

```
P(x) = a0 + a1*x + a2*x^2 + ... + an*x^n
```

使残差平方和最小：

```
minimize: S = sum((yi - P(xi))^2, i=1..N)
```

对每个系数求偏导并令其为零，得到法方程组，求解即得系数。

### 3.2 阶数选择

| 阶数 | 适用场景 | 风险 |
|------|----------|------|
| 1 | 线性传感器 | 欠拟合非线性 |
| 2-3 | 轻微非线性 | 平衡精度与计算量 |
| 4+ | 强非线性 | 过拟合、边缘震荡 |

### 3.3 过拟合风险

阶数过高时，多项式在校准点之间产生剧烈震荡：

```
// 过拟合的判断标准
// 1. 增加阶数后，校准点处的误差已不再显著降低
// 2. 校准点之间的插值出现不合理波动
// 3. 交叉验证：用 80% 点拟合，20% 点验证，验证误差反而增大
```

经验法则：校准点数至少为阶数的 3 倍，以抑制过拟合。

## 4 查找表方法

### 4.1 查找表基本结构

将校准数据按输入排序存储为表：

```c
// 查找表结构定义
typedef struct {
    int16_t raw;       // 传感器原始输出(ADC值)
    int16_t calibrated; // 校准后的物理量(0.1度C)
} lut_entry_t;

// 示例：NTC热敏电阻查找表
const lut_entry_t temp_lut[] = {
    {4095, -40},   // ADC满量程 -> -40度C
    {3850, -20},
    {3500,   0},
    {3000,  25},
    {2400,  50},
    {1800,  75},
    {1200, 100},
    { 600, 125},
    { 200, 150},
};
#define LUT_SIZE (sizeof(temp_lut) / sizeof(temp_lut[0]))
```

### 4.2 线性插值

在相邻两个表项之间做线性插值：

```
y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
```

精度取决于表的密度：表项越密，插值误差越小。

### 4.3 样条插值

用三次样条曲线在表项之间做光滑过渡：

- 比线性插值更光滑
- 避免在表项处的斜率突变
- 计算量大于线性插值，MCU 上需权衡

## 5 多项式与查找表对比

| 维度 | 多项式拟合 | 查找表 |
|------|-----------|--------|
| 代码体积 | 小(存n+1个系数) | 大(存N个表项) |
| 计算速度 | 中(需n次乘法) | 快(查表+1次插值) |
| 任意曲线适应 | 受限(阶数高则震荡) | 强(表项密即可) |
| 校准数据修改 | 重新拟合 | 修改单点即可 |
| 内存需求 | RAM几字节 | Flash/ROM数百字节 |

选择建议：
- RAM/Flash 充足、曲线复杂 → 查找表
- 资源紧张、曲线可用低阶近似 → 多项式

## 6 MCU 上的高效实现

### 6.1 Horner 法则求多项式

将多项式改写为嵌套形式，减少乘法次数：

```
// 原始: P(x) = a0 + a1*x + a2*x^2 + a3*x^3
// Horner: P(x) = a0 + x*(a1 + x*(a2 + x*a3))
```

定点数实现：

```c
#include <stdint.h>

// Q16.16 定点数多项式求值 (Horner法)
// coeffs[]: 系数数组, a0在[0], a1在[1], ...
// n: 阶数
// x_q16: 自变量, Q16.16格式
int32_t poly_eval_q16(const int32_t coeffs[], int n, int32_t x_q16) {
    int32_t result = coeffs[n]; // 从最高阶开始
    for (int i = n - 1; i >= 0; i--) {
        // result = result * x + coeffs[i]
        // Q16.16乘法: (a*b) >> 16
        result = ((int64_t)result * x_q16) >> 16;
        result += coeffs[i];
    }
    return result;
}

// 使用示例: y = 25.0 + 0.05*x - 0.0001*x^2
// Q16.16: 25.0=1638400, 0.05=3277, -0.0001=-7
const int32_t coeffs[] = {1638400, 3277, -7};
int32_t y = poly_eval_q16(coeffs, 2, x_adc_q16);
```

### 6.2 查找表二分搜索

```c
// 在排序查找表中二分搜索并线性插值
int16_t lut_interpolate(const lut_entry_t *lut, int size, int16_t raw) {
    int lo = 0, hi = size - 1;

    // 二分搜索找到raw所在的区间
    while (lo < hi - 1) {
        int mid = (lo + hi) / 2;
        if (lut[mid].raw > raw)
            lo = mid;
        else
            hi = mid;
    }

    // 线性插值
    int32_t dy = lut[lo].calibrated - lut[hi].calibrated;
    int32_t dx = lut[lo].raw - lut[hi].raw;
    int32_t offset = (int32_t)(raw - lut[hi].raw) * dy / dx;
    return lut[hi].calibrated + (int16_t)offset;
}
```

## 7 校准数据存储

### 7.1 EEPROM 存储

校准系数存储在 MCU 内部或外部 EEPROM 中：

- 上电时读取校准系数，写入 RAM
- 支持现场重新校准并更新
- 典型容量：256B-4KB

```c
// EEPROM校准数据结构
typedef struct __attribute__((packed)) {
    uint16_t magic;        // 校验标识 0xCA5E
    uint8_t  order;        // 多项式阶数
    uint8_t  reserved;
    int32_t  coeffs[6];    // 最多6阶, Q16.16
    int16_t  checksum;     // CRC16
} cal_data_t;
```

### 7.2 OTP 存储

部分 MCU 提供 OTP（一次可编程）存储区：

- 写入后不可修改——适合出厂校准
- 安全性高，不会被意外擦除
- 校准后无法重新校准

### 7.3 存储可靠性

- 添加 CRC 校验防止数据损坏
- 双备份存储：两个区域互为校验
- 上电检查 magic number + CRC，失败则使用默认参数

## 8 温度交叉校准

### 8.1 温度对校准的影响

许多传感器的偏移和增益随温度变化：

- 压力传感器零点温度系数：0.01%/度C
- 称重传感器灵敏度温度系数：0.005%/度C

### 8.2 二维校准矩阵

在不同温度下分别校准，构建二维查找表：

```c
// 二维校准表: [温度区间][压力区间]
typedef struct {
    int16_t temp_min;   // 温度区间下限(0.1度C)
    int16_t temp_max;   // 温度区间上限
    const lut_entry_t *pressure_lut;  // 该温度下的压力校准表
    int lut_size;
} temp_compensated_lut_t;
```

### 8.3 温度补偿多项式

用含温度变量的二元多项式：

```
y = a00 + a10*x + a01*T + a11*x*T + a20*x^2 + a02*T^2
```

系数在多点温度校准后用最小二乘法确定。

## 9 重新校准周期规划

### 9.1 制定重新校准周期的依据

1. 传感器厂家给出的稳定性指标
2. 应用场景的精度要求
3. 历史漂移数据

### 9.2 周期建议

| 传感器类型 | 典型漂移/年 | 建议校准周期 |
|-----------|------------|-------------|
| NTC热敏电阻 | <0.1度C | 2-3年 |
| 压力传感器 | 0.1-0.5%FS | 1年 |
| 电化学气体传感器 | 2-5% | 6个月 |
| 称重传感器 | 0.02%FS | 1年 |

## 10 实战：NTC 热敏电阻校准

### 10.1 Steinhart-Hart 方程

NTC 热敏电阻的电阻-温度关系：

```
1/T = A + B*ln(R) + C*(ln(R))^3
```

其中 T 为绝对温度(K)，R 为电阻值(Ohm)，A/B/C 为 Steinhart-Hart 系数。

### 10.2 系数标定

在三个已知温度点测量电阻，解三元一次方程组：

```c
// 三点标定求解Steinhart-Hart系数
void calc_steinhart_hart(float r1, float t1,
                          float r2, float t2,
                          float r3, float t3,
                          float *a, float *b, float *c) {
    float l1 = logf(r1), l2 = logf(r2), l3 = logf(r3);
    float y1 = 1.0f / t1, y2 = 1.0f / t2, y3 = 1.0f / t3;

    // 求解 1/T = A + B*ln(R) + C*(ln(R))^3
    // 用Cramer法则或矩阵求解(省略中间步骤)
    float gamma = (l1 - l2) * (l1 - l3) * (l2 - l3);
    *a = ((y1 * (l2 - l3)) + (y2 * (l3 - l1)) + (y3 * (l1 - l2))) / gamma;
    *b = ((y1 * (l3*l3 - l2*l2)) + (y2 * (l1*l1 - l3*l3)) + (y3 * (l2*l2 - l1*l1))) / gamma;
    *c = ((y1 * l2 * l3 * (l2 - l3)) + (y2 * l1 * l3 * (l3 - l1)) + (y3 * l1 * l2 * (l1 - l2))) / gamma;
}
```

### 10.3 电阻到温度转换

```c
// 使用Steinhart-Hart方程由电阻值计算温度
float ntc_r_to_t(float r_ohm, float a, float b, float c) {
    float ln_r = logf(r_ohm);
    float t_inv = a + b * ln_r + c * ln_r * ln_r * ln_r;
    return 1.0f / t_inv - 273.15f;  // 转换为度C
}
```

### 10.4 ADC 值到电阻转换

NTC 与固定电阻分压：

```c
// Vref ---[R_fixed]---+---[NTC]--- GND
//                     |
//                    ADC
//
// R_ntc = R_fixed * (Vref - V_adc) / V_adc
//       = R_fixed * (ADC_full - ADC_value) / ADC_value

#define R_FIXED      10000.0f   // 10kOhm
#define ADC_FULL     4095.0f    // 12-bit ADC

float adc_to_ntc_resistance(uint16_t adc_val) {
    if (adc_val == 0) return 1e6f;     // 防止除零
    if (adc_val >= ADC_FULL) return 0.0f;
    return R_FIXED * (ADC_FULL - (float)adc_val) / (float)adc_val;
}
```

## 总结

传感器校准是从原始数据到可靠测量的必经之路：

- 多项式拟合：代码紧凑，适合低阶近似的场景，Horner 法则在 MCU 上高效实现
- 查找表：适应任意曲线形状，二分搜索 + 线性插值是标配
- 温度交叉校准：环境温度变化大的应用必须考虑
- 校准数据存储：EEPROM 方案灵活，OTP 方案安全，两者都需要 CRC 保护
- NTC 校准：Steinhart-Hart 方程是行业标准，三点标定即可确定系数

校准不是一次性的工作——制定合理的重新校准周期，才能确保传感器在整个生命周期内的测量可靠性。

## 参考文献

1. Steinhart, J.S. and Hart, S.R., "Calibration curves for thermistors", Deep Sea Research and Oceanographic Abstracts, Vol.15, pp.497-503, 1968.
2. Honeywell, "Thermistor Calibration and the Steinhart-Hart Equation", Application Note, 2018.
3. Texas Instruments, "Sensor Calibration Techniques for Precision Measurement", SBAA282, 2019.
4. Kester, W., "Sensor Signal Conditioning: Calibration Techniques", Analog Devices Tutorial MT-004, 2009.
5. ISO/IEC 17025, "General requirements for the competence of testing and calibration laboratories", 2017.
