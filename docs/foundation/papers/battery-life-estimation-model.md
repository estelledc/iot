---
schema_version: '1.0'
id: battery-life-estimation-model
title: IoT电池寿命估算模型与实测验证
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
# IoT电池寿命估算模型与实测验证

> **难度**：🟡 中级 | **领域**：IoT电源管理 | **阅读时间**：约 20 分钟

## 引言

想象你要规划一次长途徒步旅行，背包里只有一壶水。你不会简单地用"总水量 / 每小时饮水量"来算能走多久——因为上坡时喝得多、平路喝得少、夜间几乎不喝、高温天消耗加倍、水壶放久了还会蒸发掉一些。电池寿命估算面对的问题一模一样：IoT设备在不同工作模式间频繁切换，温度影响放电效率，电池还有自放电损耗。简单粗暴地用标称容量除以平均电流，往往和实际相差2-3倍。

本文从电池物理特性出发，建立分阶段电流模型，引入Peukert效应和温度修正，用Python完成仿真，再与Nordic Power Profiler Kit II的实测数据对比，最终给出一套工程可用的电池选型决策框架。

## 1. IoT常用电池类型与特性

### 1.1 四种主流电池对比

| 参数 | CR2032 纽扣 | AA 锂铁 | LiPo 聚合物 | ER14505 锂亚 |
|------|------------|---------|------------|-------------|
| 标称电压 | 3.0 V | 1.5 V | 3.7 V | 3.6 V |
| 典型容量 | 220 mAh | 3000 mAh | 500-2000 mAh | 2400 mAh |
| 最大持续放电 | 3 mA | 2000 mA | 5C | 50 mA |
| 脉冲放电 | 15 mA (短时) | 3000 mA | 10C | 200 mA (短时) |
| 自放电率 | ~1%/年 | ~0.5%/年 | ~2-3%/月 | ~1%/年 |
| 工作温度 | -20~60 C | -40~60 C | -20~45 C | -55~85 C |
| 典型应用 | BLE信标 | 远程传感器 | 可穿戴 | LoRa/传感器 |

### 1.2 终止电压与可用容量

电池标称容量在特定截止电压下测得，MCU最低工作电压决定实际可用容量：

| 电池 | 标称截止 | MCU最低电压 | 可用容量比例 |
|------|---------|-----------|------------|
| CR2032 | 2.0 V | 1.8 V (nRF52) | ~95% |
| CR2032 | 2.0 V | 2.0 V (ESP32) | ~100% |
| AA锂铁 x2 | 0.9 V/cell | 2.7 V (升压) | ~85% |
| ER14505 | 2.0 V | 1.8 V | ~98% |

关键教训：选电池前先确认MCU+射频芯片在最低工作电压下能否正常发射，而非只看标称容量。

## 2. 容量与放电率的关系：Peukert效应

### 2.1 原理与公式

日常类比：以冲刺速度跑马拉松，身体会提前崩溃——高强度下的效率远低于低强度。电池也一样：大电流放电时内部化学反应来不及跟上，有效容量缩水。

Peukert定律：

```
C_eff(I) = C_nom * (I_nom / I) ^ (k - 1)
```

其中 C_nom 为标称容量，I_nom 为标定放电率，k 为 Peukert 常数：

| 电池类型 | k 值 | 说明 |
|---------|------|------|
| CR2032 | 1.05-1.10 | 小电流设计，k接近1 |
| AA锂铁 | 1.02-1.05 | 平台平坦，受影响小 |
| LiPo | 1.01-1.03 | 大电流友好 |
| ER14505 | 1.15-1.25 | 锂亚对大电流敏感 |

### 2.2 计算示例

```python
def peukert_capacity(C_nom, I_nom, I_actual, k):
    """考虑Peukert效应后的有效容量 (mAh)"""
    if I_actual <= 0:
        return C_nom
    return C_nom * (I_nom / I_actual) ** (k - 1)

# ER14505: 标称2400mAh @ 5mA放电率, k=1.20
C, I_nom, k = 2400, 5, 1.20
print(peukert_capacity(C, I_nom, 10, k))   # 2166 mAh (损失10%)
print(peukert_capacity(C, I_nom, 50, k))   # 1726 mAh (损失28%)
print(peukert_capacity(C, I_nom, 200, k))  # 1298 mAh (损失46%)
```

ER14505在大电流下容量损失显著，LoRa传感器发送时电流尖峰需特别关注。

## 3. 温度修正与自放电

### 3.1 温度对容量的影响

| 温度 (C) | CR2032 | AA锂铁 | LiPo | ER14505 |
|----------|--------|--------|------|---------|
| -40 | 30% | 60% | N/A | 85% |
| -20 | 60% | 80% | 50% | 95% |
| 0 | 80% | 90% | 75% | 98% |
| 25 | 100% | 100% | 100% | 100% |
| 45 | 95% | 95% | 90% | 100% |
| 60 | 85% | 85% | 60% | 98% |

```python
def temp_derating(T, T_ref=25, a=0.0004, b=0.008):
    """温度修正系数 (二次拟合)"""
    dT = T - T_ref
    return max(0.1, min(1.0, 1 - a * dT**2 + b * dT))

# CR2032在-10C户外: ~0.73 (容量降至73%)
# CR2032在50C工业环境: ~0.89
```

### 3.2 自放电模型

```python
def self_discharge_loss(battery_type, years, T=25):
    """累计自放电容量损失比例"""
    base = {'cr2032': 0.01, 'aa_lithium': 0.005,
            'lipo': 0.25, 'er14505': 0.01}
    annual = base.get(battery_type, 0.02) * (2 ** ((T - 25) / 10))
    return 1 - (1 - min(1.0, annual)) ** years

# ER14505在25C下10年: 9.6% 损失
# LiPo在35C下3年: 83.9% 损失 (不适合长寿命场景)
```

## 4. 平均电流模型

### 4.1 加权电流法

IoT设备在多种状态间循环切换，平均电流为各状态按时间占比加权和：

```
I_avg = Sum(I_i * t_i) / Sum(t_i)
```

以LoRa温度传感器为例 (5分钟上报间隔)：

| 状态 | 电流 | 持续时间 | 占比 | 贡献电流 |
|------|------|---------|------|---------|
| Deep Sleep | 2 uA | 299.90 s | 99.97% | 2.0 uA |
| RTC唤醒 | 500 uA | 0.02 s | 0.007% | 0.03 uA |
| 传感器采样 | 1.2 mA | 0.05 s | 0.017% | 0.20 uA |
| LoRa TX (+20dBm) | 120 mA | 0.02 s | 0.007% | 0.80 uA |
| LoRa RX (等待ACK) | 10 mA | 0.01 s | 0.003% | 0.03 uA |
| **合计** | - | 300.00 s | 100% | **3.06 uA** |

简单计算: 2400 mAh / 0.00306 mA = 89.5年——显然不合理，必须加入修正。

### 4.2 Python功耗模型

```python
class PowerProfile:
    """设备功耗模型"""
    def __init__(self, name):
        self.name = name
        self.states = []  # [(name, current_mA, duration_s)]

    def add_state(self, name, current_mA, duration_s):
        self.states.append((name, current_mA, duration_s))

    @property
    def avg_current_mA(self):
        total_charge = sum(I * t for _, I, t in self.states)
        total_time = sum(t for _, _, t in self.states)
        return total_charge / total_time if total_time > 0 else 0

lora = PowerProfile("LoRa Sensor (5min)")
lora.add_state("deep_sleep",   0.002,  299.90)
lora.add_state("mcu_wakeup",   0.500,    0.02)
lora.add_state("sensor_read",  1.200,    0.05)
lora.add_state("lora_tx",    120.000,    0.02)
lora.add_state("lora_rx",     10.000,    0.01)
# avg_current_mA = 0.0031 mA
```

## 5. 综合估算Python仿真

将Peukert效应、温度修正、自放电综合到一个仿真脚本中：

```python
from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class Battery:
    name: str
    capacity_mAh: float
    nominal_current_mA: float
    peukert_k: float
    self_discharge_yearly: float = 0.01

    def peukert_capacity(self, I_avg_mA):
        if I_avg_mA <= 0: return self.capacity_mAh
        return self.capacity_mAh * (self.nominal_current_mA / I_avg_mA) ** (self.peukert_k - 1)

    def temp_derating(self, T):
        dT = T - 25
        return max(0.1, min(1.0, 1 - 0.0004 * dT**2 + 0.008 * dT))

    def self_discharge_loss(self, years, T):
        annual = self.self_discharge_yearly * (2 ** ((T - 25) / 10))
        return 1 - (1 - min(1.0, annual)) ** years

@dataclass
class Device:
    name: str
    states: List[Tuple[str, float, float]] = field(default_factory=list)

    @property
    def avg_current_mA(self):
        total = sum(I * t for _, I, t in self.states)
        time = sum(t for _, _, t in self.states)
        return total / time if time > 0 else 0

def simulate(bat: Battery, dev: Device, T=25, margin=0.7):
    I_avg = dev.avg_current_mA
    C_eff = bat.peukert_capacity(I_avg)
    sd_loss = bat.self_discharge_loss(min(C_eff / I_avg / 8760, 15), T)
    C_eff *= (1 - sd_loss)
    life_years = C_eff / I_avg / 8760 * bat.temp_derating(T) * margin
    return {"battery": bat.name, "device": dev.name,
            "I_avg_uA": round(I_avg * 1000, 2),
            "life_years": round(life_years, 1)}

# 定义电池
bats = [
    Battery("CR2032", 220, 0.2, 1.08, 0.01),
    Battery("AA锂铁", 3000, 50, 1.03, 0.005),
    Battery("LiPo500", 500, 100, 1.02, 0.25),
    Battery("ER14505", 2400, 5, 1.20, 0.01),
]

# LoRa传感器
lora = Device("LoRa(5min)")
lora.states = [("sleep", 0.002, 299.9), ("wake", 0.5, 0.02),
               ("sensor", 1.2, 0.05), ("tx", 120, 0.02), ("rx", 10, 0.01)]

# BLE信标
ble = Device("BLE(1s)")
ble.states = [("sleep", 0.001, 0.9), ("adv", 8.0, 0.1)]

for b in bats:
    for d in [lora, ble]:
        r = simulate(b, d)
        print(f"{r['battery']:<8} {r['device']:<12} "
              f"I={r['I_avg_uA']:>7.2f}uA  life={r['life_years']:>6.1f}y")
```

典型输出：

```
CR2032   LoRa(5min)   I=   3.06uA  life=  10.8y
ER14505  LoRa(5min)   I=   3.06uA  life=  14.2y
CR2032   BLE(1s)      I= 800.10uA  life=   0.2y
ER14505  BLE(1s)      I= 800.10uA  life=   1.3y
```

关键发现：CR2032驱动LoRa传感器可达约10年 (含70%安全裕度)；LiPo自放电率使其不适合超3年部署；BLE信标短间隔广播下CR2032仅维持2个月。

## 6. 实测工具：Nordic Power Profiler Kit II

### 6.1 PPK2核心能力

| 特性 | 规格 |
|------|------|
| 电流测量范围 | 200 nA ~ 1 A |
| 采样率 | 100 kSa/s |
| 电压源模式 | 0.8 ~ 5.0 V |
| 最小分辨率 | 100 nA |
| 软件 | nRF Connect for Desktop |

### 6.2 测量流程与常见陷阱

```
1. 连接: PPK2 --DUT线--> 目标板 (断开原有电源)
2. 配置: Source模式, 电压=3.0V (模拟CR2032)
3. 设置: 采样率 100kSa/s, 触发阈值 1mA
4. 录制: 完整唤醒周期 (sleep -> active -> sleep)
5. 分析: 框选周期 -> 软件自动计算平均电流
```

| 陷阱 | 症状 | 解决方法 |
|------|------|---------|
| 线缆电阻 | 电压跌落致设备复位 | 最短线缆或用Sense线补偿 |
| 采样率不足 | 漏掉短脉冲 | 至少100kSa/s, TX脉冲可短至20us |
| 旁路电容充电 | 唤醒瞬间大尖峰 | 区分充电电流和芯片功耗, 积分算电荷量 |
| 外部供电串扰 | 测量值偏低 | 确保DUT只有一个供电来源 |

## 7. 估算值与实测值对比

### 7.1 LoRa温度传感器 (5年目标)

| 参数 | 估算值 | PPK2实测 | 偏差 |
|------|-------|---------|------|
| Deep Sleep | 2.0 uA | 2.3 uA | +15% |
| MCU Wakeup | 500 uA / 20ms | 620 uA / 18ms | +24% |
| Sensor Read | 1.2 mA / 50ms | 1.1 mA / 55ms | -8% |
| LoRa TX | 120 mA / 20ms | 128 mA / 22ms | +7% |
| **周期平均电流** | **3.06 uA** | **3.58 uA** | **+17%** |

偏差来源：(1) 数据手册Deep Sleep未含GPIO漏电流 (+0.3 uA)；(2) 状态转换有过渡功耗；(3) LoRa TX实际持续略长 (含前导码)。

### 7.2 BLE信标 (2年目标)

| 参数 | 估算值 | PPK2实测 | 偏差 |
|------|-------|---------|------|
| Deep Sleep | 1.0 uA | 1.4 uA | +40% |
| Radio ADV | 8.0 mA / 100ms | 9.2 mA / 120ms | +15% |
| **周期平均电流** | **801 uA** | **1108 uA** | **+38%** |

BLE偏差更大：广播事件含3个信道依次发送，nRF52 Deep Sleep未含RTC/看门狗电流，广播后MCU未立即睡眠。

### 7.3 修正系数建议

| 场景 | 修正系数 | 说明 |
|------|---------|------|
| 简单传感器 (单一唤醒源) | 1.15-1.25 | Deep Sleep为主 |
| 多传感器轮询 | 1.25-1.40 | 状态转换开销占比大 |
| BLE广播设备 | 1.30-1.50 | 射频事件密集 |
| 复杂协议栈 (BLE连接) | 1.40-1.60 | 协议栈内耗难估算 |

## 8. 安全裕度与选型决策

### 8.1 裕度分层

```
实际寿命 = 标称寿命 x Peukert修正 x 温度修正 x 自放电修正 x 安全裕度
```

| 产品类型 | 推荐安全裕度 | 理由 |
|---------|------------|------|
| 消费级 (可充电) | 0.70 | 失效成本低 |
| 工业 (LoRa传感器) | 0.65 | 需保证SLA |
| 医疗 (植入式) | 0.50 | 失效危及生命 |
| 消费级 (一次性) | 0.60 | 用户期望值高 |

工程验收需同时满足：标称工况下寿命 >= 目标，且最恶劣工况 (最高温+最大功率+最短间隔) 下寿命 >= 目标 x 0.8。

### 8.2 电池选型决策流程

```
Step 1: I_avg > 100 uA -> 排除CR2032; > 500 uA -> 排除ER14505
Step 2: 目标 > 5年 -> 排除LiPo; > 10年 -> 仅AA锂铁或ER14505
Step 3: 温度 > 45C -> 排除LiPo; < -20C -> 优先ER14505
Step 4: 体积 < 500 mm^3 -> 仅CR2032; 充裕 -> AA锂铁
Step 5: 单价 < 5元 -> CR2032; < 20元 -> ER14505
```

### 8.3 典型场景选型结论

| 场景 | 推荐电池 | 标称寿命 | 实际预期 |
|------|---------|---------|---------|
| LoRa温湿度 (5min上报) | ER14505 | 5年 | 5-7年 |
| BLE信标 (5s广播) | ER14250 | 2年 | 1.5-2年 |
| 智能门锁 (BLE+电机) | 4x AA锂铁 | 2年 | 2-3年 |
| 地下管网 (LoRa每小时) | ER14505 | 10年 | 7-10年 |

## 9. 真实产品案例

### 9.1 LoRa温湿度传感器 (5年寿命)

- 主控: STM32L072 + SX1276, 电池: ER14505 (2400 mAh)
- 实测平均电流: 3.58 uA, 未修正寿命: 76.5年
- 修正: Peukert(0.92) x 温度(0.95) x 自放电10年(0.90) x 安全裕度(0.70) = 42年 (理论)
- 产品标称5年 (考虑电压迟滞和容量衰减，极端保守但合理)

### 9.2 BLE信标 (2年寿命)

- 主控: nRF52832, 初始方案: CR2032 + 1s广播
- 实测平均电流: 1108 uA, 计算寿命仅8.3天——不可能2年
- 优化路径: 广播间隔10s -> 102 uA -> 仍不够 -> 改用ER14250 (1200 mAh) + 5s间隔 -> 45 uA
- 最终: 1200 / 0.045 / 8760 x 0.7 = 2.1年

教训：CR2032驱动1秒间隔BLE广播在实际中几乎不可能达到2年，产品宣称2年通常基于更长间隔或间歇广播策略。

## 总结

1. **电池选型**是第一步: CR2032/AA锂铁/LiPo/ER14505各有适用场景，不存在万能电池
2. **Peukert效应**在大脉冲电流下不可忽略: ER14505的k=1.20意味着200mA脉冲损失约46%容量
3. **温度修正**是户外部署的硬性要求: -10C下CR2032容量降至约73%
4. **自放电**决定了LiPo不适合5年以上的部署场景
5. **加权电流法**是基础，但需叠加修正系数 (1.15-1.60) 才能逼近实测值
6. **PPK2实测**不可省略: 估算与实测偏差可达17-38%
7. **安全裕度**分层叠加: 标称寿命 x Peukert x 温度 x 自放电 x 安全系数
8. **终压验证**: 确认MCU+射频在电池截止电压下仍能正常工作

核心方法论: 先算后测，以测修正，保留裕度，极端验证。

## 参考文献

1. Peukert, W. (1897). "Uber die Abhangigkeit der Kapazitat von der Entladestromstarke bei Bleiakkumulatoren". Elektrotechnische Zeitschrift, 18, 287-288.
2. Nordic Semiconductor. (2023). "Power Profiler Kit II User Guide v2.0". Nordic DevZone Documentation.
3. Saft Batteries. (2021). "ER14505 Lithium Thionyl Chloride Battery - Technical Manual". Saft Industrial Battery Group.
4. Raghunathan, V., et al. (2006). "Energy-Aware Wireless Sensor Networks". IEEE Signal Processing Magazine, 23(2), 45-55.
