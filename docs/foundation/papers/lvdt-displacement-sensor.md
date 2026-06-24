# LVDT差动变压器位移传感器原理与应用

> **难度**：🟡 中级 | **领域**：位移测量、电磁感应、工业自动化 | **阅读时间**：约 18 分钟

## 日常类比

想象你站在一条走廊正中间，左右两边各有一个音箱播放同样大小的声音。当你站在正中时，两只耳朵听到的声音完全一样——左右声压抵消，你感觉"静"。当你往左偏一步，左耳声音变大、右耳声音变小，差值立刻告诉你偏了多远、往哪边偏。LVDT（Linear Variable Differential Transformer，线性可变差动变压器）的工作方式几乎一模一样：中间的铁芯就是"你"，两个次级线圈就是"两个音箱"，输出电压的差值精准反映了位移的大小和方向。

再换一个类比：老式天平秤。左右两个托盘各放一个砝码，天平平衡时读数为零；往左加 1 克，指针偏转的幅度正比于多出来的重量。LVDT 的"差动"二字正是这个意思——两个次级线圈像天平的两端，铁芯移动打破平衡，差值就是位移信号。这种差动结构天然抵消了温度漂移、电源波动等共模干扰，就像天平两侧同时受震动时指针并不偏。

最后再想一个场景：变压器大家不陌生，初级线圈通电产生磁场，次级线圈感应出电压。但普通变压器的铁芯是固定的，输出也是固定的。如果把铁芯做成可以滑动的，次级电压就随铁芯位置而变——这就是 LVDT 的本质：一个铁芯可移动的差动变压器。

---

## 1. LVDT的结构组成

### 1.1 总体结构

LVDT由三个部分组成，沿同一轴线排列在圆柱形外壳内：

- **初级线圈**：位于中间，由交流激励源驱动，产生交变磁场
- **两个次级线圈**：对称分布在初级两侧（S₁ 和 S₂），感应初级磁场
- **可移动铁芯**：高导磁率圆柱体，可沿轴向自由滑动

```
  S₁    Primary    S₂
 ═════ ══════════ ═════   ← 线圈骨架
       ████████████        ← 可移动铁芯
          ← d →
```

### 1.2 关键结构参数

| 参数 | 典型值 | 说明 |
|------|--------|------|
| 铁芯材料 | Ni-Fe合金（坡莫合金） | 高导磁率、低磁滞 |
| 铁芯直径 | 3~12 mm | 需与线圈骨架内径配合 |
| 线圈骨架 | PEEK / PPS / 陶瓷 | 低热膨胀系数、绝缘 |
| 线径 | 0.05~0.15 mm 漆包线 | 匝数决定灵敏度 |
| 外壳 | 不锈钢 316 / 304 | 防护等级 IP65~IP68 |
| 行程范围 | ±0.5 mm ~ ±500 mm | 不同型号覆盖不同量程 |

铁芯与线圈骨架之间留有微小气隙（约 0.2~0.5 mm），确保运动顺畅同时尽量减小磁路磁阻。铁芯长度通常略大于初级线圈长度，保证整个行程内磁路耦合连续变化。

### 1.3 为什么是"差动"

两个次级线圈反向串联（同名端对接），S₁ 和 S₂ 的感应电动势相减输出。铁芯位于正中时，两侧耦合磁通相等，输出为零；铁芯偏移时，一侧增强另一侧减弱，差值不再为零——这就是"差动"的核心。

---

## 2. 工作原理

### 2.1 电磁感应过程

初级线圈通入交流激励信号（典型频率 1~10 kHz，幅值 1~10 V），在铁芯中建立交变磁通。磁通耦合到两个次级线圈，分别感应出电动势：

\[
e_1 = -N_1 \frac{d\Phi_1}{dt}, \quad e_2 = -N_2 \frac{d\Phi_2}{dt}
\]

其中 \(N_1 = N_2\)，\(\Phi_1\)、\(\Phi_2\) 分别为穿过 S₁ 和 S₂ 的磁通量。

### 2.2 差动输出

输出电压为两个次级线圈感应电动势之差：

\[
V_{out} = e_1 - e_2 = k \cdot x
\]

其中 \(k\) 为灵敏度系数（V/mm），\(x\) 为铁芯偏离零位的位移量。在理想线性区内，输出电压幅值与位移成正比。

### 2.3 相位信息

差动输出还包含相位信息：铁芯偏向 S₁ 时输出与激励同相，偏向 S₂ 时反相（180°），零位时输出为零。相位信息用于判断位移方向，这是 LVDT 优于简单变压器的关键。

### 2.4 线性区与非线性区

| 区域 | 铁芯位置 | 输出特性 |
|------|----------|----------|
| 线性区 | 初级线圈覆盖范围内 | \(V_{out} \propto x\)，线性度优于 0.1% FS |
| 过渡区 | 铁芯边缘接近初级线圈端部 | 非线性增大，曲线弯曲 |
| 饱和区 | 铁芯完全偏离一侧 | 输出不再随位移增大 |

实际使用中，将工作行程限制在线性区内，这是 LVDT 设计选型的基本原则。

---

## 3. 信号解调

### 3.1 为什么需要解调

LVDT 原始输出是调幅交流信号——频率等于激励频率、幅值正比于位移。需解决两个问题：

1. **幅值提取**：将交流信号转换为正比于位移的直流电压
2. **方向判别**：根据相位信息判断铁芯偏移方向

### 3.2 同步解调（Synchronous Demodulation）

将 LVDT 输出与激励信号相乘后低通滤波：

\[
V_{demod} = \text{LPF}\left[ V_{out}(t) \times V_{exc}(t) \right]
\]

同相时乘积直流分量为正，反相时为负。低通滤波后同时包含幅值和方向信息。

### 3.3 相敏检波（Phase-Sensitive Detection）

相敏检波是同步解调的具体电路实现：

1. 用激励信号生成参考方波（同频同相）
2. 参考方波控制开关，分别在正负半周采样 LVDT 输出
3. 正半周采样值减去负半周采样值，得到含方向的直流输出

### 3.4 专用集成电路

现代应用中，通常使用专用 LVDT 信号调理芯片来简化设计：

| 芯片型号 | 供电电压 | 激励频率 | 特点 |
|----------|----------|----------|------|
| AD698 | ±15 V | 20 Hz~20 kHz | 经典方案，外置元件多 |
| AD598 | ±15 V | 1~10 kHz | 内置振荡器，同步解调 |
| NXP NE5521 | 5 V | 固定 | 低功耗，汽车级 |
| TI PGA300 | 3.3 V | 外部提供 | 可编程增益，数字接口 |

---

## 4. 性能指标

### 4.1 主要性能参数表

| 参数 | 典型范围 | 高精度型号 | 说明 |
|------|----------|------------|------|
| 量程 | ±0.5 ~ ±500 mm | ±1 ~ ±50 mm | 线性区有效行程 |
| 线性度 | 0.1% ~ 0.5% FS | 0.05% FS | 非线性误差占满量程比 |
| 分辨率 | 0.1 ~ 1 μm | 0.01 μm | 理论上无摩擦、无限分辨 |
| 灵敏度 | 10 ~ 200 mV/V/mm | 50 ~ 100 mV/V/mm | 每毫米位移每伏激励的输出 |
| 重复性 | 0.01% ~ 0.1% FS | 0.005% FS | 同方向重复测量的一致性 |
| 频率响应 | 0 ~ 500 Hz | 0 ~ 1 kHz | 取决于激励频率（约 1/10） |
| 工作温度 | -55 ~ +175 °C | -40 ~ +85 °C | 航空级可达更宽范围 |
| 迟滞 | < 0.1% FS | < 0.02% FS | 正反行程差值 |
| 输出阻抗 | 1 ~ 10 kΩ | — | 影响后级电路设计 |

### 4.2 灵敏度与激励频率的关系

激励频率 \(f_{exc}\) 需在灵敏度和频率响应间权衡：过低（< 1 kHz）灵敏度低；适中（1~10 kHz）线性度好；过高（> 50 kHz）涡流损耗增大、灵敏度反而降低。经验法则：激励频率取铁芯最大运动频率的 8~10 倍。

---

## 5. 与其他位移传感器的比较

### 5.1 对比表

| 特性 | LVDT | 电位器 | 光电编码器 | 电容式传感器 |
|------|------|--------|------------|--------------|
| 测量原理 | 电磁感应 | 电阻分压 | 光学计数 | 电容变化 |
| 接触/非接触 | 非接触 | 接触 | 非接触 | 非接触 |
| 分辨率 | 极高（理论无限） | 中等 | 高（取决于码盘） | 极高 |
| 线性度 | 0.05~0.5% FS | 0.1~1% FS | N/A（数字输出） | 0.05~0.5% FS |
| 耐久性 | 极好（无摩擦） | 一般（电刷磨损） | 好 | 好 |
| 环境适应性 | 优（耐温、耐振、密封） | 差 | 差（怕灰尘） | 中（怕湿气） |
| 量程 | ±0.5 mm ~ ±500 mm | 10 mm ~ 500 mm | 无限制 | 0.01 mm ~ 10 mm |
| 成本 | 中高 | 低 | 中 | 中 |
| 输出信号 | 交流调幅 | 直流电压 | 数字脉冲 | 交流/频率 |
| 动态响应 | 0~1 kHz | 0~100 Hz | 0~数百 kHz | 0~10 kHz |

### 5.2 LVDT 的独特优势

1. **无摩擦、无限分辨率**：铁芯与线圈无机械接触，理论上不存在摩擦和磨损，分辨率仅受后续电路噪声限制
2. **坚固耐用**：全密封不锈钢外壳，耐高温、耐高压、耐腐蚀，可在恶劣工业环境中长期工作
3. **零位输出为零**：差动结构使得零位时输出真正为零，便于信号处理和误差控制
4. **抗辐射**：无半导体器件在传感头内，适合核电站等强辐射环境

### 5.3 LVDT 的局限

1. **需要交流激励和解调电路**：系统复杂度高于电位器
2. **体积较大**：线圈骨架和铁芯需要一定长度，微型化受限
3. **非线性区限制行程**：超出线性区后精度急剧下降
4. **电磁干扰敏感**：强磁场环境需考虑屏蔽

---

## 6. 接口电路设计

### 6.1 专用信号调理芯片

AD698 是 Analog Devices 推出的 LVDT 专用信号调理芯片，内部集成正弦波振荡器、同步解调器和输出放大器，外围只需少量阻容元件。

### 6.2 基于微控制器的数字接口方案

以下代码展示 STM32 通过 ADC 采集 LVDT 信号并进行同步解调：

```c
/** LVDT 同步解调 — STM32 HAL 实现
 *  PA0 → LVDT 输出 | PA1 → 激励参考 | PA8 → 激励 PWM (5kHz)
 *  原理：LVDT 输出 × 激励符号函数 → 低通滤波 → 位移值 */

#include "stm32f4xx_hal.h"
#include <math.h>

#define SAMPLE_RATE       50000   // 采样率 50kHz
#define EXCITATION_FREQ   5000    // 激励频率 5kHz
#define SAMPLES_PER_CYC   (SAMPLE_RATE / EXCITATION_FREQ)  // 每周期10点
#define NUM_CYCLES        4       // 积分4个周期
#define ADC_RESOLUTION    4096.0f // 12-bit ADC
#define ADC_VREF          3.3f
#define LVDT_SENSITIVITY  50.0f   // mV/V/mm
#define LVDT_EXC_VOLTAGE  5.0f    // 激励电压

static uint16_t adc_buffer_lvdt[SAMPLES_PER_CYC * NUM_CYCLES];
static uint16_t adc_buffer_ref[SAMPLES_PER_CYC * NUM_CYCLES];

float lvdt_compute_displacement(void) {
    float sum = 0.0f;
    int n = SAMPLES_PER_CYC * NUM_CYCLES;
    for (int i = 0; i < n; i++) {
        float v_lvdt = (float)adc_buffer_lvdt[i] / ADC_RESOLUTION * ADC_VREF;
        float v_ref  = (float)adc_buffer_ref[i]  / ADC_RESOLUTION * ADC_VREF;
        // 参考过零 → +1/-1 符号函数（相敏检波核心）
        float sign = (v_ref > ADC_VREF / 2.0f) ? 1.0f : -1.0f;
        sum += v_lvdt * sign;  // 乘积累加
    }
    float demod = sum / (float)n;  // 均值=低通滤波
    return demod / (LVDT_SENSITIVITY * LVDT_EXC_VOLTAGE / 1000.0f);  // → mm
}

// 一阶低通滤波器: alpha 越小越平滑（典型 0.05~0.2）
float low_pass_filter(float in, float prev, float alpha) {
    return alpha * in + (1.0f - alpha) * prev;
}
```

### 6.3 基于 ESP32 的 IoT 采集节点

以下代码展示如何通过 ESP32 将 LVDT 数据接入 MQTT 物联网平台：

```python
"""lvdt_iot_node.py — ESP32 MicroPython: ADC采集→滑动平均→MQTT上云"""
import machine, time, json
from umqtt.simple import MQTTClient

# 硬件 & LVDT 参数
adc = machine.ADC(machine.Pin(34))
adc.atten(machine.ADC.ATTN_11DB)   # 0~3.3V
adc.width(machine.ADC.WIDTH_12BIT)
LVDT_RANGE_MM = 50.0              # 量程 ±25mm
LVDT_VOFFSET  = 1.65              # 零位电压中点
LVDT_SCALE    = LVDT_RANGE_MM / 3.3  # mm/V

WINDOW_SIZE = 16                   # 滑动平均窗口
adc_buffer = []

# MQTT 配置
MQTT_BROKER = "192.168.1.100"
MQTT_TOPIC  = b"factory/lvdt/displacement"
CLIENT_ID   = b"lvdt-node-001"

def read_displacement():
    """ADC → 电压 → 滑动平均 → 位移(mm)"""
    voltage = adc.read() / 4095.0 * 3.3
    adc_buffer.append(voltage)
    if len(adc_buffer) > WINDOW_SIZE:
        adc_buffer.pop(0)
    avg = sum(adc_buffer) / len(adc_buffer)
    return round((avg - LVDT_VOFFSET) * LVDT_SCALE, 3)

def main():
    client = MQTTClient(CLIENT_ID, MQTT_BROKER, port=1883)
    client.connect()
    last_report = 0
    while True:
        t = time.time()
        d = read_displacement()
        if t - last_report >= 1.0:  # 1Hz 上报
            payload = json.dumps({
                "node_id": "lvdt-001", "displacement_mm": d,
                "timestamp": t, "unit": "mm",
                "status": "normal" if abs(d) < 24 else "alarm"
            })
            client.publish(MQTT_TOPIC, payload)
            last_report = t
        time.sleep(0.05)  # 20Hz 采样

if __name__ == "__main__":
    main()
```

---

## 7. 工业 IoT 应用场景

### 7.1 数控机床刀具磨损监测

将 LVDT 安装在刀架或主轴附近，实时监测刀具的轴向和径向位移：

- **在线监测**：每次换刀后测量刀具实际伸出长度，与设定值比较判断磨损量
- **补偿控制**：根据位移偏差自动调整刀具补偿值
- **预警停机**：磨损量超过阈值时触发报警

典型安装：外壳固定在刀架基座，铁芯弹簧预紧贴在刀柄端面，量程 ±2 mm，分辨率 0.1 μm。

### 7.2 液压系统位移控制

液压缸行程控制是 LVDT 的经典应用：

- **伺服液压缸**：LVDT 内置在活塞杆中心孔内，形成闭环位置控制
- **比例阀反馈**：检测阀芯位移，实现精确流量控制
- **同步控制**：多缸同步系统中各缸 LVDT 反馈用于误差校正

液压环境要求耐高压（最高 350 bar）、耐振动、耐油液浸泡，LVDT 的全密封无摩擦特性使其成为首选。

### 7.3 结构健康监测

在桥梁、大坝、高层建筑中，LVDT 用于长期监测位移和变形：

- **裂缝扩展**：跨裂缝安装，持续记录宽度变化
- **支座位移**：监测桥梁支座水平位移和沉降
- **风振响应**：高层建筑层间位移监测

这些场景要求无人值守连续工作数年至数十年，LVDT 的高可靠性和零漂移特性使其特别适合。

### 7.4 其他应用

| 应用领域 | 测量对象 | 典型量程 | 特殊要求 |
|----------|----------|----------|----------|
| 汽车试验台 | 减震器行程 | ±100 mm | 高频响应 |
| 航空航天 | 执行器位置 | ±25 mm | 宽温、抗辐射 |
| 核电站 | 控制棒位置 | 0~300 mm | 耐辐射、耐高温 |
| 材料试验机 | 试件变形 | ±10 mm | 高分辨率 |
| 纺织机械 | 纱线张力辊位移 | ±5 mm | 防尘、防纤维缠绕 |

---

## 8. 安装与校准

### 8.1 安装要点

1. **对中安装**：铁芯轴线与运动方向严格共线，偏斜导致非线性和侧向力
2. **刚性固定**：外壳刚性固定在静止参考点，松动引入测量误差
3. **预紧力控制**：弹簧预紧保证贴合但不过大，避免磨损
4. **电缆走线**：远离动力线，双绞屏蔽电缆，屏蔽层单端接地
5. **环境密封**：户外用全密封型号，电缆出口防水接头

### 8.2 校准流程

```
LVDT 校准流程

1. 零位校准
   → 铁芯置于机械零位 → 记录 ADC 零位输出 → 调整偏移使输出为零

2. 增益校准
   → 铁芯移至 +FS 记录 V+FS → 移至 -FS 记录 V-FS
   → 计算灵敏度 k = (V+FS - V-FS) / (2 × FS)

3. 线性度校验
   → 量程内均匀取 10~20 个点 → 记录实际与理论值 → 计算最大非线性误差

4. 温度补偿（可选）
   → 在工作温度范围两端重复步骤 1~3 → 建立温度-偏差补偿表
```

### 8.3 常见故障与排查

| 故障现象 | 可能原因 | 排查方法 |
|----------|----------|----------|
| 零位漂移 | 温度变化、机械松动 | 检查固定螺栓、环境温度 |
| 灵敏度下降 | 激励电压异常、铁芯磨损 | 测量激励频率和幅值 |
| 输出噪声大 | 电磁干扰、接地不良 | 检查屏蔽层接地、远离干扰源 |
| 非线性增大 | 安装偏斜、铁芯超出线性区 | 重新对中、检查行程 |
| 输出卡死 | 铁芯卡滞、线圈断线 | 检查铁芯运动、测量线圈电阻 |

### 8.4 校准周期建议

- 一般工业应用：每 6~12 个月
- 高精度测量（优于 0.1% FS）：每 3~6 个月
- 恶劣环境（强振动、大温差）：每 1~3 个月
- 重大维护后：必须重新校准

---

## 总结与展望

LVDT 凭借其非接触测量、无限分辨率、坚固耐用和差动抗干扰等核心优势，在高可靠性位移测量领域占据不可替代的地位。在工业 IoT 时代，LVDT 正经历从纯模拟传感器到智能数字节点的演进：

1. **集成化**：AD698/AD598 等芯片将同步解调集成在单芯片内
2. **数字化**：内置 ADC+MCU 的智能 LVDT 直接输出 Modbus/CAN/SPI
3. **网络化**：IoT 网关接入云平台，实现远程监控与预测性维护
4. **微型化**：MEMS 技术缩小体积，拓展空间受限场景
5. **多参数融合**：与温度、振动传感器联合，提升故障诊断准确性

对于 IoT 系统开发者而言，理解 LVDT 的工作原理和信号处理方法，是正确选型、集成和调试的必要基础。建议在实际项目中从专用信号调理芯片入手，逐步过渡到基于 MCU 的数字解调方案。

---

## 参考资料

1. Analog Devices. *AD698: Universal LVDT Signal Conditioner Data Sheet*. Rev C, 2017.
2. Analog Devices. *AD598: LVDT Signal Conditioner Data Sheet*. Rev D, 2015.
3. Fraden J. *Handbook of Modern Sensors: Physics, Designs, and Applications*. 5th ed. Springer, 2016. Chapter 6: Displacement and Position Sensors.
4. Wilson J S. *Sensor Technology Handbook*. Newnes, 2005. Chapter 7: Position and Motion Sensing.
5. Nyce D S. *Linear Position Sensors: Theory and Application*. Wiley-IEEE Press, 2004.
6. Macro Sensors. *LVDT Technical Guide and Application Notes*. 2020.
7. TE Connectivity. *LVDT Basics: Principles, Selection, and Application*. Application Note AN-002, 2019.
8. 国家标准 GB/T 18459-2001. *传感器主要静态性能指标计算方法*.
9. Ricken W, et al. "Giant magnetoresistive LVDT for harsh environment applications." *Sensors and Actuators A: Physical*, 2020.
10. KUKA Robotics. *Industrial Sensor Integration for IoT: LVDT in Smart Manufacturing*. Technical White Paper, 2022.
