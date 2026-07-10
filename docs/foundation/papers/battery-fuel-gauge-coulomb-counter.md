---
schema_version: '1.0'
id: battery-fuel-gauge-coulomb-counter
title: 电池电量计库仑计法与电压法对比
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
# 电池电量计库仑计法与电压法对比
> **难度**：🟡 中级 | **领域**：电池管理系统 | **阅读时间**：约 20 分钟

## 引言

想象你的汽车油表: 一种方式是看油箱上的刻度(电压法), 另一种方式是在加油口装一个流量计, 记录每次加了多少油、发动机用了多少油(库仑计法). 前者简单但抖动大, 后者精确但需要校准. 在物联网设备中, 电池电量(SOC)的准确估计直接决定设备能跑多久、什么时候该省电、什么时候该报警. 本文从两种基本方法出发, 讲到融合方案和实际芯片选型, 帮助你在项目中做出合理选择.

## 1 为什么SOC准确性对IoT至关重要

### 1.1 SOC误差的实际后果

SOC(State of Charge)即电池剩余电量的百分比. 在IoT场景中, SOC不准会导致三类问题:

- **过早关机**: SOC显示还剩30%, 实际电量已接近0, 设备突然掉电, 数据丢失
- **过度保守**: SOC显示0%, 实际还有20%, 用户提前更换电池或充电, 浪费能量
- **调度错误**: 固件根据SOC决定是否启动高功耗操作(如LoRA发射), 误判导致通信失败或错过窗口

### 1.2 IoT设备的特殊挑战

与手机不同, IoT设备通常:

- 放电电流极小(休眠时几微安), 偶尔大电流脉冲(发射时几十到几百毫安)
- 工作温度范围宽(-40 到 85 摄氏度)
- 电池容量小(100mAh 到 3000mAh), 小误差就是大百分比
- 电池寿命要求长(3 到 10 年)

这些特征使得传统手机电量计方案不能直接照搬.

## 2 电压法估算SOC

### 2.1 基本原理

锂电池的开路电压(OCV)与SOC之间存在单调关系. 测量电池端电压, 查OCV-SOC曲线, 即可得到SOC估算值.

```
V_batt ---> [OCV-SOC查找表] ---> SOC%
```

典型锂电池OCV-SOC曲线特征:

| SOC (%) | OCV (V) | 区间特点 |
|---------|---------|---------|
| 0-10    | 3.0-3.3 | 陡峭, 变化快 |
| 10-80   | 3.3-3.9 | 平坦, 变化慢 |
| 80-100  | 3.9-4.2 | 陡峭, 变化快 |

### 2.2 OCV曲线的获取

OCV曲线必须在静置状态下获取. 具体步骤:

1. 以恒定电流放电, 每放出10%容量后暂停
2. 静置1到2小时, 让电压恢复到平衡态
3. 记录此时的OCV值
4. 重复直到SOC为0%

不同化学体系的OCV曲线形状不同. LiFePO4的曲线特别平坦(3.2V附近几乎不变), 这使得电压法对其几乎失效.

### 2.3 电压法的三大误差源

**负载效应**: 有电流流过时, 端电压偏离OCV:

```
V_terminal = OCV - I * R_internal
```

其中R_internal包括欧姆内阻和极化内阻. 一个100mA的发射脉冲, 如果内阻100毫欧, 电压就低了10mV, 对应SOC误差可能达到5%.

**温度依赖**: 低温下内阻增大, OCV本身也略有偏移. 0摄氏度时的OCV比25摄氏度时低约20到40mV.

**滞后效应**: 充电后和放电后的OCV不同, 即使SOC相同. 这种滞后(hysteresis)可达10到30mV, 对应SOC误差3到8%.

### 2.4 电压法的适用场景

尽管精度有限, 电压法在某些场景仍有价值:

- 极低成本的消费品(玩具、一次性设备)
- 休眠时间远大于工作时间, 电压基本稳定
- 只需要粗略的"满/半/空"三档指示

## 3 库仑计法

### 3.1 基本原理

库仑计法(Coulomb Counting)通过积分电流来追踪电量的变化:

```
SOC(t) = SOC(t0) + (1/Q_max) * Integral(I(t), t0, t)
```

其中Q_max是电池满充容量, I(t)是实时电流(充电为正, 放电为负).

类比: 就像水表, 记录流进和流出的水量, 需要知道水箱总容量和起始水位.

### 3.2 电流检测方式

**检流电阻(Shunt Resistor)**: 在充放电路径上串联一个小阻值精密电阻, 测量其两端压降:

```
I = V_sense / R_sense
```

典型参数:
- 阻值: 10到100毫欧
- 精度: 1%或更好
- 功耗: I^2 * R_sense

**集成检流电阻**: 部分fuel gauge IC将检流电阻集成在芯片内部, 省去外部元件, 但精度和灵活性受限.

### 3.3 ADC与积分实现

库仑计法的核心是高精度ADC:

```
// 伪代码: 库仑计法的离散化实现
float soc = soc_initial;       // 初始SOC
float q_max = 1500.0;         // 满充容量, mAh
float r_sense = 0.050;        // 检流电阻, 欧姆
float dt = 1.0;               // 采样间隔, 秒

void coulomb_count_update(void) {
    float v_sense = adc_read(SENSE_PIN);  // 读取检流电压
    float current_ma = (v_sense / r_sense) * 1000.0;  // 转换为mA
    float delta_mah = current_ma * (dt / 3600.0);     // mAh增量
    soc += (delta_mah / q_max) * 100.0;               // SOC百分比更新
    soc = clamp(soc, 0.0, 100.0);
}
```

关键参数:
- ADC分辨率: 12到16位
- 采样率: 1到100Hz(根据负载变化率选择)
- 积分时间步长: 越短越精确, 但功耗越高

### 3.4 漂移累积问题

库仑计法的根本缺陷是漂移(drift):

- **初始SOC未知**: 上电时不知道当前SOC, 只能从电压法估算一个起始值
- **电流测量误差**: ADC偏移、增益误差、检流电阻温漂, 都会随时间累积
- **积分是开环的**: 没有外部参考来校正累积误差

假设电流测量误差0.5%, 一个1000mAh的电池持续放电, 10小时后误差可达5mAh, 对应SOC误差0.5%. 看似不大, 但如果设备运行数月, 误差会持续增长.

## 4 融合方法: 电压+库仑+卡尔曼滤波

### 4.1 为什么需要融合

电压法在低电流时准确, 库仑计法在大电流时准确, 两者互补. 卡尔曼滤波器(EKF)将两种测量融合:

```
// 简化的EKF融合框架
// 状态向量: x = [SOC, R_internal]
// 观测: V_measured
// 预测步骤(库仑计)
x_pred = x_prev + (I * dt / Q_max);
// 更新步骤(电压法校正)
V_expected = OCV(SOC_pred) - I * R_pred;
K = P * H / (H * P * H' + R);  // 卡尔曼增益
x_update = x_pred + K * (V_measured - V_expected);
```

### 4.2 融合效果

| 指标 | 纯电压法 | 纯库仑计法 | 融合方法 |
|------|---------|-----------|---------|
| 静态精度 | +/-5% | +/-3% | +/-2% |
| 动态精度 | +/-15% | +/-3% | +/-3% |
| 长期漂移 | 无 | 有 | 无(电压法校正) |
| 算法复杂度 | 低 | 低 | 高 |
| 计算资源 | 极少 | 少 | 中等(需要乘法/矩阵运算) |

### 4.3 实际实现考量

在MCU上实现EKF需要注意:

- 32位浮点运算足够, 不需要双精度
- 状态向量2到3维(SOC, 内阻, 也许温度), 计算量可控
- OCV-SOC查找表需要针对具体电池型号标定
- 滤波器参数(R, Q矩阵)需要实测调优

## 5 Fuel Gauge IC选型

### 5.1 三款常用芯片对比

**BQ27441 (TI)**:
- 方法: Impedance Track(融合法)
- 精度: +/-1%
- 接口: I2C (400kHz)
- 电流检测: 外部7到20毫欧检流电阻
- 特点: 自动学习电池特性, 内置温度补偿

**MAX17048 (Maxim/ADI)**:
- 方法: ModelGauge(改进电压法)
- 精度: +/-1%(稳定状态)
- 接口: I2C (400kHz)
- 电流检测: 无需外部检流电阻
- 特点: 超小封装(1.5x1.9mm), 无检流电阻, 适合空间受限设计

**LC709203F (ON Semi)**:
- 方法: 改进电压法 + 温度补偿
- 精度: +/-2.5%
- 接口: I2C (100kHz)
- 电流检测: 无需外部检流电阻
- 特点: 低成本, 支持多种电池类型

| 特性 | BQ27441 | MAX17048 | LC709203F |
|------|---------|----------|-----------|
| 方法 | 融合法 | 改进电压法 | 改进电压法 |
| 精度 | +/-1% | +/-1%(稳态) | +/-2.5% |
| 外部检流电阻 | 需要 | 不需要 | 不需要 |
| I2C地址 | 0x55 | 0x36 | 0x0B |
| 工作电流 | 60uA | 25uA | 5到8uA |
| 封装 | 2.5x2.5mm | 1.5x1.9mm | 2.9x2.8mm |
| 价格(参考) | $1.5 | $1.2 | $0.6 |

### 5.2 I2C接口与关键寄存器

以BQ27441为例:

```
// I2C读SOC寄存器
// 设备地址: 0x55
// SOC寄存器: 0x1C (2字节, 无符号整数)
uint16_t read_soc_bq27441(void) {
    uint8_t buf[2];
    i2c_write(0x55, 0x1C, 1);    // 写入寄存器地址
    i2c_read(0x55, buf, 2);       // 读取2字节
    return (buf[1] << 8) | buf[0]; // 小端序
    // 返回值就是SOC百分比, 如 85 表示 85%
}
```

MAX17048的关键寄存器:

```
// SOC寄存器: 0x04 (2字节)
// VCELL寄存器: 0x02 (2字节, 电压值, 单位78.125uV)
uint16_t read_soc_max17048(void) {
    uint8_t buf[2];
    i2c_write(0x36, 0x04, 1);
    i2c_read(0x36, buf, 2);
    return (buf[0] << 8) | buf[1]; // 大端序
    // 返回值 / 256.0 得到百分比, 如 0x5600 = 86%
}
```

### 5.3 学习周期(Learning Cycle)

BQ27441等融合法芯片需要执行学习周期来校准电池模型:

1. 将电池充至满充(4.2V, 截止电流C/10)
2. 静置2小时
3. 以典型负载电流放电至空(3.0V)
4. 静置2小时
5. 芯片记录满充容量和空电电压, 更新内部模型

首次使用或更换电池后必须执行一次学习周期. 之后芯片可以在正常运行中持续微调.

## 6 温度补偿

### 6.1 温度对电池参数的影响

| 参数 | 25摄氏度 | 0摄氏度 | -20摄氏度 | 影响 |
|------|---------|--------|-----------|------|
| 内阻 | 80毫欧 | 150毫欧 | 300毫欧 | 压降增大 |
| 容量 | 100% | 90% | 75% | 可用能量减少 |
| OCV | 基准 | -15mV | -35mV | SOC估算偏移 |
| 自放电率 | 2%/月 | 0.5%/月 | 0.2%/月 | 长期漂移 |

### 6.2 补偿策略

**硬件补偿**: 使用NTC热敏电阻测量电池温度, 通过ADC读数查表获取温度值, 传给fuel gauge IC.

```
// NTC温度读取(简化)
float read_battery_temp(void) {
    float v_ntc = adc_read_voltage(NTC_CH);
    float r_ntc = (v_ntc / V_REF) * R_PULLUP / (1.0 - v_ntc / V_REF);
    // Steinhart-Hart方程或查表
    float temp = steinhart_hart(r_ntc, A, B, C);
    return temp;
}
```

**软件补偿**: 在MCU侧维护温度-SOC偏移表, 根据当前温度校正SOC读数. 大部分fuel gauge IC已经内置了温度补偿算法, 只需正确配置温度参数.

## 7 自放电建模

### 7.1 自放电率

锂电池在开路存放时也会缓慢损失电量:

- 室温: 约1到3%/月
- 高温(45摄氏度): 约5到10%/月
- 低温(-20摄氏度): 约0.2到0.5%/月

对于长期运行的IoT设备(如每年只工作几次的传感器), 自放电是SOC漂移的重要来源.

### 7.2 在电量计中的处理

高级fuel gauge(如BQ27441)内置自放电模型, 但大多数简单芯片不处理. 需要在MCU侧实现:

```
// 简单的自放电补偿
// 假设自放电率为 2%/月 = 0.000093%/小时
void apply_self_discharge(void) {
    static uint32_t last_time = 0;
    uint32_t now = get_rtc_timestamp();
    if (last_time == 0) { last_time = now; return; }
    uint32_t elapsed_hours = (now - last_time) / 3600;
    float self_discharge = elapsed_hours * 0.000093;  // %
    soc -= self_discharge;
    last_time = now;
}
```

## 8 方法对比总结

| 维度 | 电压法 | 库仑计法 | 融合法 |
|------|--------|---------|--------|
| 精度(稳态) | +/-5到10% | +/-3到5% | +/-1到2% |
| 精度(动态) | +/-10到20% | +/-3到5% | +/-2到3% |
| 成本 | 极低(仅ADC) | 低(ADC+电阻) | 中(IC成本$0.6到2) |
| 外部元件 | 无 | 检流电阻 | 检流电阻(部分IC不需要) |
| 算法复杂度 | 极低 | 低 | 中到高 |
| 初始SOC | 有(上电即知) | 无(需要初始化) | 有(电压法辅助) |
| 长期漂移 | 无 | 有(累积) | 无(电压法校正) |
| 适用化学体系 | 受限(LiFePO4差) | 不受限 | 不受限 |
| 适合IoT场景 | 低成本/粗略指示 | 中等精度需求 | 高精度/长寿命需求 |

## 9 实际MCU集成实践

### 9.1 与STM32的集成示例

```
// STM32 + BQ27441 初始化与SOC读取
#include "stm32l4xx_hal.h"

extern I2C_HandleTypeDef hi2c1;
#define BQ27441_ADDR  (0x55 << 1)  // HAL需要左移1位

HAL_StatusTypeDef bq27441_init(void) {
    uint8_t cmd = 0x00;  // 设备类型寄存器
    uint8_t buf[2];
    // 检查芯片是否响应
    HAL_StatusTypeDef ret = HAL_I2C_Mem_Read(&hi2c1,
        BQ27441_ADDR, 0x00, I2C_MEMADD_SIZE_8BIT,
        buf, 2, 100);
    return ret;
}

uint8_t bq27441_read_soc(void) {
    uint8_t buf[2];
    HAL_I2C_Mem_Read(&hi2c1,
        BQ27441_ADDR, 0x1C, I2C_MEMADD_SIZE_8BIT,
        buf, 2, 100);
    return buf[0];  // 低字节即SOC百分比
}
```

### 9.2 电池配置文件

Fuel gauge IC需要电池配置文件, 包含:

- 化学体系ID(化学标识符)
- 满充容量(Q_max)
- 设计容量
- 放电终止电压
- 充电终止电压
- 温度范围
- 内阻模型参数

这些参数通常由芯片厂商提供工具(如TI的bqStudio)生成, 以二进制格式写入IC的data flash.

### 9.3 低功耗策略

Fuel gauge IC本身也有功耗, 在超低功耗设计中需要考虑:

- BQ27441: 正常模式60uA, 休眠模式4uA
- MAX17048: 始终25uA, 无休眠模式
- LC709203F: 正常模式5到8uA, 休眠模式0.3uA

策略: 在MCU深度休眠时, 降低I2C读取频率(如每分钟一次), 或将fuel gauge设为低功耗模式.

## 10 常见问题与解决

### 10.1 掉电后初始SOC恢复

问题: 系统掉电重启后, 库仑计法的SOC丢失.

解决方案:
- 将SOC定期保存到非易失性存储器(如EEPROM或Flash)
- 重启后先读保存值, 再用电压法校验, 差异大则采用电压法值
- 在BQ27441中, 芯片内部有data flash, 掉电不丢失

```
// SOC掉电恢复策略
float soc_on_boot(void) {
    float soc_saved = eeprom_read_float(ADDR_SOC);
    float soc_voltage = voltage_to_soc(read_battery_voltage());
    // 如果两者差异小于10%, 用保存值(更准)
    // 否则用电压法值(更可靠)
    if (fabs(soc_saved - soc_voltage) < 10.0) {
        return soc_saved;
    } else {
        return soc_voltage;
    }
}
```

### 10.2 电池老化补偿

锂电池容量随循环次数衰减:

- 500个循环后容量约为初始的80%
- 1000个循环后容量约为初始的60%

高级fuel gauge通过学习周期自动跟踪容量衰减. 简单方案需要在MCU侧维护循环计数器, 定期调整Q_max.

### 10.3 多串电池组

本文主要讨论单节电池(3.7V标称). 多串电池组需要:
- 电池均衡电路
- 逐节电压监测
- 更复杂的SOC算法(各节电池SOC可能不同)

这属于BMS(Battery Management System)范畴, 超出本文范围.

## 总结

电压法简单但精度有限, 库仑计法精确但有漂移, 融合法取两者之长. 对于IoT设备:

- 成本敏感、精度要求不高: 电压法或MAX17048类改进电压法IC
- 需要较高精度且预算允许: BQ27441类融合法IC
- 超低功耗长期运行: LC709203F, 配合MCU侧自放电补偿

选型时优先考虑: 是否需要检流电阻(PCB面积)、精度要求、功耗预算、I2C地址冲突风险、以及是否需要学习周期(生产流程影响).

## 参考文献

1. TI, "BQ27441-G1 Single-Cell Nano Fuel Gauge Technical Reference Manual", SLUUAP5, 2015.
2. Maxim Integrated, "MAX17048/MAX17049 ModelGauge IC Data Sheet", Rev 3, 2018.
3. ON Semiconductor, "LC709203F Battery Fuel Gauge Data Sheet", Rev 7, 2019.
4. Plett G L, "Extended Kalman filtering for battery management systems of LiPB-based HEV battery packs", Journal of Power Sources, Vol 134, No 2, 2004, pp 252-261.
5. Rahimi-Eichi H, et al., "Battery management system: An overview of its application in the smart grid and electric vehicles", IEEE Industrial Electronics Magazine, Vol 7, No 2, 2013, pp 4-16.
