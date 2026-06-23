# IoT 设备电池管理系统 BMS

> **难度**：🟡 中级 | **领域**：电源管理、嵌入式系统、电化学 | **阅读时间**：约 20 分钟

## 日常类比

手机电量显示"20%"——这个数字是怎么来的？电池没有"油量表"，不能像水箱一样直接看水位。电池的"剩余电量"是通过 BMS 芯片**估算**出来的：它同时跟踪充放电电流（像记流水账）、监测电压曲线（像根据水压推水量）、再用数学模型修正误差。

BMS 就像电池的"私人医生"：实时监测体温（防过热）、限制运动强度（防过流）、定期体检（估算健康度）、平衡营养摄入（均衡各节电池）。对于 IoT 设备，BMS 还多了一个特殊使命——让设备在野外无人维护地运行数年，这对功耗和寿命预测提出了极高要求。

## 1. 锂离子电池化学基础

### 1.1 工作原理

锂离子电池通过锂离子在正负极之间的往返迁移存储/释放能量：

```
充电方向 -->
正极 (LiCoO2)                    负极 (石墨 C6)
LiCoO2 -> Li(1-x)CoO2 + xLi+ + xe-  -->  xLi+ + xe- + C6 -> LixC6
                                <--
                          放电方向
                  电解液 (LiPF6 有机溶剂)
```

### 1.2 主流正极材料对比

| 材料 | 缩写 | 能量密度 | 寿命 | 安全性 | 成本 | IoT 适用度 |
|------|------|---------|------|--------|------|-----------|
| 钴酸锂 | LCO | 高 (200 Wh/kg) | 500-1000 次 | 中 | 高 | 小型可穿戴 |
| 磷酸铁锂 | LFP | 中 (170 Wh/kg) | 2000-5000 次 | 高 | 低 | 户外长寿命节点 |
| 三元锂 | NCM/NCA | 高 (250 Wh/kg) | 800-2000 次 | 中 | 中 | 无人机/机器人 |
| 锰酸锂 | LMO | 中 (150 Wh/kg) | 500-1000 次 | 高 | 低 | 低成本IoT |

### 1.3 关键电气参数

```python
# 锂离子电池基本参数（以 18650 NCM 电池为例）
cell_params = {
    "nominal_voltage": 3.7,        # V 标称电压
    "charge_cutoff": 4.2,          # V 充电截止
    "discharge_cutoff": 2.5,       # V 放电截止（LFP: 2.0V）
    "capacity_mAh": 3000,          # 典型容量
    "max_charge_rate": 1.0,        # C 最大充电倍率 (= 3A)
    "max_discharge_rate": 2.0,     # C 最大放电倍率 (= 6A)
    "internal_resistance_mOhm": 50,# 内阻
    "self_discharge_pct_month": 2, # %/月 自放电率
    "temp_range_charge": (0, 45),  # 充电温度范围 C
    "temp_range_discharge": (-20, 60),  # 放电温度范围 C
}
```

### 1.4 OCV-SoC 曲线

开路电压（OCV）与荷电状态（SoC）之间存在相对稳定的对应关系，这是 SoC 估算的基础：

```python
import numpy as np

def ocv_ncm(soc):
    """
    NCM 电池 OCV-SoC 经验模型（6阶多项式拟合）
    输入: soc (0-1)
    输出: 开路电压 (V)
    """
    # 实测数据拟合的多项式系数
    coeffs = [-11.52, 36.37, -45.30, 28.63, -9.56, 1.92, 3.43]
    ocv = np.polyval(coeffs, soc)
    return np.clip(ocv, 2.5, 4.2)

# SoC 从 0% 到 100% 的 OCV 变化
soc_range = np.linspace(0, 1, 101)
ocv_values = [ocv_ncm(s) for s in soc_range]
# 特征: 两端陡峭（0-10%, 90-100%）中间平坦（20-80%约3.5-3.9V）
# 平坦区是SoC估算最困难的区域——电压变化太小
```

## 2. SoC 估算方法

### 2.1 库仑计数法（Coulomb Counting）

最直观的方法：积分充放电电流。

```python
class CoulombCounter:
    """
    库仑计数法 SoC 估算
    优点：实现简单、动态响应快
    缺点：电流测量误差会累积、需要准确初始值
    """
    
    def __init__(self, capacity_mAh, initial_soc=1.0):
        self.capacity_As = capacity_mAh * 3.6  # mAh -> As (库仑)
        self.soc = initial_soc
        self.coulomb_efficiency = 0.995  # 库仑效率（充电时略低）
    
    def update(self, current_A, dt_s):
        """
        更新 SoC
        current_A: 正=充电, 负=放电
        dt_s: 时间步长 (秒)
        """
        # 充电时考虑库仑效率损失
        if current_A > 0:
            effective_current = current_A * self.coulomb_efficiency
        else:
            effective_current = current_A
        
        # 积分: dSoC = I*dt / Q_total
        delta_soc = effective_current * dt_s / self.capacity_As
        self.soc += delta_soc
        self.soc = np.clip(self.soc, 0.0, 1.0)
        
        return self.soc
    
    def get_remaining_mAh(self):
        return self.soc * self.capacity_As / 3.6

# 误差分析：
# 假设电流传感器精度 +-0.5%，容量 3000mAh
# 一个完整充放循环累积误差: 3000 * 0.005 * 2 = 30 mAh (1%)
# 10个循环不校正: 误差可达 10%
```

### 2.2 OCV 校正法

利用电池静置后电压逼近 OCV 的特性，修正库仑计数的累积误差：

```python
def ocv_correction(terminal_voltage, current_A, r_internal,
                   ocv_soc_table, rest_time_s):
    """
    OCV 法修正 SoC
    仅在电池"近似静置"时有效（电流 < 0.02C 且持续 > 30min）
    """
    # 补偿内阻压降，估算 OCV
    estimated_ocv = terminal_voltage - current_A * r_internal
    
    # 如果静置时间足够，直接查表
    if abs(current_A) < 0.01 and rest_time_s > 1800:
        # 在 OCV-SoC 表中反查 SoC
        soc = np.interp(estimated_ocv, 
                        ocv_soc_table['voltage'],
                        ocv_soc_table['soc'])
        confidence = 0.95  # 高置信度
    else:
        # 动态情况下 OCV 估算不可靠
        soc = None
        confidence = 0.0
    
    return soc, confidence
```

### 2.3 扩展卡尔曼滤波器（EKF）

EKF 是工业 BMS 的标准方法——融合库仑计数（预测）和电压测量（观测），实时估算 SoC 和内阻。

```python
import numpy as np

class BatteryEKF:
    """
    电池 SoC 估算 EKF
    状态: x = [SoC, R_internal]
    观测: z = terminal_voltage
    """
    
    def __init__(self, capacity_Ah, initial_soc=0.5):
        # 状态 [SoC, R_internal(Ohm)]
        self.x = np.array([initial_soc, 0.05])
        
        # 状态协方差
        self.P = np.diag([0.01, 0.001])
        
        # 过程噪声
        self.Q = np.diag([1e-6, 1e-8])  # SoC过程噪声很小
        
        # 观测噪声（电压测量噪声）
        self.R = np.array([[0.001]])  # 1 mV std
        
        self.capacity_As = capacity_Ah * 3600
    
    def predict(self, current_A, dt_s):
        """预测步骤：库仑计数"""
        soc, r_int = self.x
        
        # 状态转移: SoC(k+1) = SoC(k) + I*dt/Q
        new_soc = soc + current_A * dt_s / self.capacity_As
        
        # 内阻缓慢变化（近似不变）
        # F = 状态转移雅可比
        F = np.array([
            [1, 0],
            [0, 1]
        ])
        
        self.x = np.array([new_soc, r_int])
        self.P = F @ self.P @ F.T + self.Q
    
    def update(self, measured_voltage, current_A):
        """更新步骤：电压观测"""
        soc, r_int = self.x
        
        # 预测电压: V = OCV(SoC) + I*R
        predicted_voltage = ocv_ncm(soc) + current_A * r_int
        
        # 观测雅可比 H = [dV/dSoC, dV/dR]
        d_ocv = (ocv_ncm(soc + 0.001) - ocv_ncm(soc - 0.001)) / 0.002
        H = np.array([[d_ocv, current_A]])
        
        # 新息
        y = measured_voltage - predicted_voltage
        
        # 卡尔曼增益
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ np.linalg.inv(S)
        
        # 更新
        self.x = self.x + (K @ np.array([y])).flatten()
        self.P = (np.eye(2) - K @ H) @ self.P
        
        # 限幅
        self.x[0] = np.clip(self.x[0], 0, 1)
        self.x[1] = np.clip(self.x[1], 0.01, 0.5)
    
    def get_soc(self):
        return self.x[0]
    
    def get_resistance(self):
        return self.x[1]
```

## 3. 电池均衡

### 3.1 为什么需要均衡

多节串联电池组中，由于制造差异和老化速度不同，各节 SoC 会逐渐失衡：

- 最弱电池决定整组容量（木桶效应）
- 不均衡加速老化（弱电池过充/过放）
- 10% 的不均衡可导致整组可用容量下降 20-30%

### 3.2 被动均衡（Passive Balancing）

最简单的方案：通过电阻放掉高 SoC 电池的多余电荷。

```c
// 被动均衡控制逻辑（BQ76952 示例）
// 原理：SoC 高的电池通过旁路电阻放电，直到与最低电池对齐

#define NUM_CELLS       4
#define BALANCE_THRESH  50    // mV，启动均衡的电压差阈值
#define BALANCE_CURRENT 50    // mA，均衡电流（= V_cell / R_balance）

typedef struct {
    float voltage[NUM_CELLS];
    bool balancing[NUM_CELLS];
} BMS_State;

void passive_balance(BMS_State *state) {
    // 找到最低电压
    float v_min = state->voltage[0];
    for (int i = 1; i < NUM_CELLS; i++) {
        if (state->voltage[i] < v_min)
            v_min = state->voltage[i];
    }
    
    // 对电压高于 (v_min + threshold) 的电池启动均衡
    for (int i = 0; i < NUM_CELLS; i++) {
        if (state->voltage[i] - v_min > BALANCE_THRESH / 1000.0f) {
            state->balancing[i] = true;   // 使能旁路 MOSFET
        } else {
            state->balancing[i] = false;
        }
    }
}

// 被动均衡缺点：
// - 能量以热量形式浪费
// - 均衡速度慢（50mA 均衡 100mAh 差异需要 2 小时）
// - 均衡电流受限于散热（电阻发热）
```

### 3.3 主动均衡（Active Balancing）

通过 DC-DC 转换器将高 SoC 电池的能量转移到低 SoC 电池，效率 > 90%。

| 拓扑 | 效率 | 复杂度 | 均衡速度 | 成本 |
|------|------|--------|---------|------|
| 电阻旁路（被动） | 0% | 最低 | 慢 (50mA) | ¥0.5/节 |
| 电容切换 | 85% | 中 | 中 (200mA) | ¥3/节 |
| 电感飞渡 | 90% | 高 | 快 (1A) | ¥8/节 |
| 变压器多绕组 | 92% | 最高 | 最快 | ¥15/节 |

IoT 设备通常只用 2-4 节电池，被动均衡已够用。主动均衡主要用于电动车（90+ 节串联）。

## 4. 保护电路

### 4.1 必须保护的故障场景

| 故障 | 阈值 | 后果 | 保护动作 |
|------|------|------|---------|
| 过充 | > 4.25V | 电解液分解、热失控 | 断开充电 MOSFET |
| 过放 | < 2.5V | 铜溶解、不可逆损伤 | 断开放电 MOSFET |
| 过流（放电） | > 3C | 内部温升、析锂 | 短暂延时后断开 |
| 短路 | > 10C | 瞬间高温、爆炸风险 | 微秒级断开 |
| 过温 | > 60C | 隔膜收缩、热失控 | 断开所有 MOSFET |
| 低温充电 | < 0C | 析锂（不可逆） | 禁止充电 |

### 4.2 典型保护电路架构

```
                    PACK+
                      |
     ┌───────────────┤
     |                |
  [Cell 4] 4.2V     |
     |              ┌┴┐
  [Cell 3] 4.2V    │ │ Charge MOSFET (P-CH)
     |              └┬┘
  [Cell 2] 4.2V     |
     |              ┌┴┐
  [Cell 1] 4.2V    │ │ Discharge MOSFET (N-CH)
     |              └┬┘
     |                |
     └───────BMS IC───┤
      (监测所有电压)    |
                    PACK-
```

### 4.3 BMS IC 选型对比

| 芯片 | 厂商 | 节数 | SoC 估算 | 均衡 | 接口 | 精度 | 适用 |
|------|------|------|---------|------|------|------|------|
| BQ76952 | TI | 3-16S | 内置库仑计 | 被动 | I2C/SPI | ±1mV | 中大型电池组 |
| MAX17261 | ADI | 1S | ModelGauge m5 | - | I2C | ±1% SoC | 小型IoT设备 |
| BQ27427 | TI | 1S | Impedance Track | - | I2C | ±1% SoC | 可穿戴 |
| ISL94203 | Renesas | 3-8S | 外部MCU | 被动 | SPI | ±1.5mV | 工业IoT |
| nPM1300 | Nordic | 1S | 内置充电+量计 | - | I2C | ±3% SoC | BLE IoT |

### 4.4 MAX17261 单节 BMS 实战

对于大多数 IoT 设备（单节锂电池），MAX17261 是性价比最优选择：

```python
# MAX17261 I2C 寄存器读取（MicroPython）
from machine import I2C, Pin
import struct

class MAX17261:
    """MAX17261 单节电量计驱动"""
    
    ADDR = 0x36
    
    # 关键寄存器
    REG_STATUS = 0x00
    REG_VCELL = 0x09      # 电压
    REG_CURRENT = 0x0A    # 电流
    REG_SOC = 0x06        # SoC (%)
    REG_TTE = 0x11        # 剩余时间 (秒)
    REG_TEMP = 0x08       # 温度
    REG_CYCLES = 0x17     # 循环次数
    REG_SOH = 0xB3        # 健康度 (%)
    
    def __init__(self, i2c):
        self.i2c = i2c
    
    def read_reg(self, reg):
        data = self.i2c.readfrom_mem(self.ADDR, reg, 2)
        return struct.unpack('<H', data)[0]
    
    def get_voltage_V(self):
        """电压，分辨率 78.125 uV/LSB"""
        raw = self.read_reg(self.REG_VCELL)
        return raw * 78.125e-6
    
    def get_current_mA(self):
        """电流，分辨率取决于检测电阻 (假设 10 mOhm)"""
        raw = self.read_reg(self.REG_CURRENT)
        # 有符号数处理
        if raw > 0x7FFF:
            raw -= 0x10000
        return raw * 1.5625 / 10  # 10 mOhm sense resistor
    
    def get_soc_pct(self):
        """SoC 百分比，分辨率 1/256 %"""
        raw = self.read_reg(self.REG_SOC)
        return raw / 256.0
    
    def get_time_to_empty_min(self):
        """剩余使用时间 (分钟)"""
        raw = self.read_reg(self.REG_TTE)
        return raw * 5.625 / 60  # 5.625 s/LSB -> min
    
    def get_soh_pct(self):
        """电池健康度 SOH (%)"""
        raw = self.read_reg(self.REG_SOH)
        return raw / 256.0

# 使用示例
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
gauge = MAX17261(i2c)
print(f"电压: {gauge.get_voltage_V():.3f} V")
print(f"电流: {gauge.get_current_mA():.1f} mA")
print(f"SoC: {gauge.get_soc_pct():.1f} %")
print(f"剩余: {gauge.get_time_to_empty_min():.0f} 分钟")
```

## 5. 热管理

### 5.1 温度对电池的影响

```
          容量保持率 vs 温度
100% |         ●●●●●
     |       ●       ●
 80% |     ●           ●
     |   ●               ●
 60% |  ●                 ●
     | ●                   ●
 40% |●                     ●
     +--+--+--+--+--+--+--+--
    -20 -10  0  10 20 30 40 50  (C)
    
最佳工作温度: 20-30C
低温: 容量骤降 + 禁止充电 (析锂)
高温: 容量短期增加但加速老化
```

### 5.2 IoT 设备热管理策略

| 场景 | 温度范围 | 策略 |
|------|---------|------|
| 室内IoT | 15-35C | 无需主动热管理 |
| 户外节点 | -20-60C | 加保温层 + 低温时降功率 |
| 工业设备 | -40-85C | 加热膜 + 强制风冷 |
| 可穿戴 | 20-40C | 限制充电电流防体温升高 |

### 5.3 低温充电保护

```c
// 低温充电保护逻辑
// 0C 以下充电会导致锂枝晶生长，永久损伤电池

typedef enum {
    CHARGE_NORMAL,        // > 10C: 正常 1C 充电
    CHARGE_REDUCED,       // 0-10C: 降低到 0.3C
    CHARGE_PROHIBITED,    // < 0C: 禁止充电
    CHARGE_PREHEAT        // < 0C 且有加热器: 先预热
} ChargeMode;

ChargeMode get_charge_mode(float temp_c, bool has_heater) {
    if (temp_c > 10.0f) {
        return CHARGE_NORMAL;
    } else if (temp_c > 0.0f) {
        return CHARGE_REDUCED;
    } else {
        return has_heater ? CHARGE_PREHEAT : CHARGE_PROHIBITED;
    }
}

float get_max_charge_current_A(float temp_c, float capacity_Ah) {
    if (temp_c > 25.0f) return capacity_Ah * 1.0f;      // 1C
    if (temp_c > 10.0f) return capacity_Ah * 0.5f;      // 0.5C
    if (temp_c > 0.0f)  return capacity_Ah * 0.2f;      // 0.2C
    return 0.0f;                                          // 禁止
}
```

## 6. 退化建模与寿命预测

### 6.1 容量衰减模型

锂电池容量随循环次数和日历老化而下降。经验模型：

```python
import numpy as np

def capacity_fade_model(cycles, temperature_C, dod=0.8, c_rate=0.5):
    """
    半经验容量衰减模型
    输入: 循环次数, 温度, 放电深度, 倍率
    输出: 容量保持率 (0-1)
    
    基于 Arrhenius + 幂律模型
    """
    # Arrhenius 温度加速因子
    Ea = 31700  # 活化能 J/mol (NCM typical)
    R = 8.314   # 气体常数
    T_ref = 298.15  # 参考温度 25C
    T = temperature_C + 273.15
    
    temp_factor = np.exp(Ea / R * (1/T_ref - 1/T))
    
    # DoD 应力因子 (深度放电加速老化)
    dod_factor = (dod / 0.8) ** 1.5
    
    # C-rate 应力因子
    crate_factor = (c_rate / 0.5) ** 0.5
    
    # 幂律衰减: Q_loss = k * N^z
    k = 0.0005 * temp_factor * dod_factor * crate_factor
    z = 0.5  # 平方根依赖（SEI膜生长主导）
    
    q_loss = k * (cycles ** z)
    retention = 1.0 - q_loss
    
    return max(retention, 0.0)

# 寿命预测示例
# 条件: 25C, 每天1次完整循环, 0.5C
cycles_per_year = 365
for year in range(1, 11):
    retention = capacity_fade_model(cycles_per_year * year, 25)
    print(f"第{year}年: 容量保持 {retention*100:.1f}%")
# 约第3-4年降到80%（寿命终止 EOL 定义）
```

### 6.2 IoT 设备寿命优化策略

| 策略 | 效果 | 实现难度 |
|------|------|---------|
| 限制充电上限 4.1V (非 4.2V) | 寿命延长 2-3x | 低 |
| 限制放电下限 20% (非 0%) | 寿命延长 1.5x | 低 |
| 避免满电存储（存于 50%） | 日历老化减半 | 中 |
| 低温环境加保温 | 减缓 SEI 低温生长 | 中 |
| 小电流充放（< 0.5C） | 减少锂浓差极化 | 低 |
| 智能充电曲线（非 CC-CV） | 寿命延长 20-30% | 高 |

### 6.3 SoH 在线估算

```python
def estimate_soh(full_charge_capacity_mAh, design_capacity_mAh,
                 internal_resistance_now, internal_resistance_new):
    """
    SoH 双指标估算
    1. 容量型: SoH_Q = 当前满充容量 / 设计容量
    2. 功率型: SoH_R = (R_eol - R_now) / (R_eol - R_new)
    """
    # 容量健康度
    soh_capacity = full_charge_capacity_mAh / design_capacity_mAh
    
    # 内阻健康度 (内阻增大 = 老化)
    r_eol = internal_resistance_new * 2.0  # EOL定义: 内阻翻倍
    soh_resistance = (r_eol - internal_resistance_now) / \
                     (r_eol - internal_resistance_new)
    
    # 综合 (取较低值，保守估计)
    soh = min(soh_capacity, soh_resistance)
    return np.clip(soh, 0, 1)
```

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：TP4056 模块（¥1）+ 单节 18650，搭建最基本的充电电路，理解 CC-CV 充电曲线
2. **第二步**：MAX17261 评估板（¥50），用 I2C 读取 SoC/SoH，观察电量计行为
3. **第三步**：ESP32 + INA219 电流传感器，自己实现库仑计数，对比 MAX17261 结果
4. **第四步**：实现简化版 EKF，观察收敛过程
5. **进阶**：BQ76952 评估板，学习多节 BMS 配置（均衡、保护阈值设定）

### 7.2 具体调优建议

**SoC 精度优化**：

- 库仑计数必须有"校正锚点"——满充（SoC=100%）或静置 OCV 查表
- 电流检测用高精度分流器（< 0.1%）+ 24 bit ADC
- 温度补偿 OCV 曲线（不同温度 OCV-SoC 关系不同）
- EKF 的 Q/R 矩阵需要针对具体电池调参（不能照搬论文值）

**延长电池寿命**：

- 充电截止设为 4.1V 而非 4.2V（牺牲 10% 容量换 2-3 倍寿命）
- 深度学习优化充电曲线：2024 年 Nature Energy 报道的脉冲充电方案寿命提升 30%
- 不要长时间存储在满电或空电状态
- 高温是最大杀手——有条件就加温度传感器做热保护

**IoT 低功耗 BMS 设计**：

- 选用 nPM1300（Nordic）或 BQ25180（TI）等集成方案：充电 + 保护 + 量计一体
- BMS IC 自身静态功耗要低（< 5 uA），否则喧宾夺主
- 休眠模式下仅保留电压监测（不做库仑计数），唤醒后用 OCV 重新校正
- 考虑超级电容 + 电池混合方案：瞬时大电流由超级电容提供

## 参考文献

1. Plett, G. L. (2015). Battery Management Systems, Volume I: Battery Modeling. Artech House.
2. Texas Instruments. (2024). BQ76952 Technical Reference Manual. SLUSC05A.
3. Maxim Integrated (ADI). (2024). MAX17261 ModelGauge m5 Fuel Gauge Datasheet. Rev 4.
4. Barré, A. et al. (2013). A review on lithium-ion battery ageing mechanisms and estimations for automotive applications. Journal of Power Sources, 241, 680-689.
5. Severson, K. A. et al. (2019). Data-driven prediction of battery cycle life before capacity degradation. Nature Energy, 4(5), 383-391.
6. Nordic Semiconductor. (2024). nPM1300 Power Management IC Datasheet. v1.2.
7. Hu, X. et al. (2020). Battery Lifetime Prognostics. Joule, 4(2), 310-346.
8. Attia, P. M. et al. (2024). Pulse charging protocols for enhanced lithium-ion battery longevity. Nature Energy, 9(2), 134-143.
9. Rahimi-Eichi, H. et al. (2013). Battery management system: An overview of its application in the smart grid. IEEE Industrial Electronics Magazine, 7(2), 4-16.
10. Xiong, R. et al. (2018). Towards a smarter battery management system: A critical review on battery state of health monitoring methods. Journal of Power Sources, 405, 18-29.
