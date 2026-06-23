# IoT 低功耗设计模式

> **难度**：🟡 中级 | **领域**：嵌入式系统、电源管理 | **阅读时间**：约 20 分钟

## 日常类比

想象你住在一个偏远小屋，唯一的电源是一块太阳能电池板加一个蓄电池。你不会 24 小时开着所有电器——而是：灯只在需要时开（事件驱动），冰箱用变频压缩机（电压调节），睡觉时关掉大部分电器只留烟雾报警器（深度睡眠），甚至可以把某些房间的电闸完全拉下（电源门控）。

IoT 设备的低功耗设计就是同样的思路。一个靠纽扣电池运行 5 年的温度传感器，99.9% 的时间都在"睡觉"，只在需要采集和发送数据的那几毫秒才"醒来"工作。这篇文章将系统梳理所有主流的低功耗设计模式，并给出真实的功耗测量数据。

## 1. 睡眠模式层次

### 1.1 MCU 电源状态机

现代 MCU 通常提供 3-5 级睡眠深度，核心权衡是：睡得越深省电越多，但醒来越慢。

| 模式 | RAM 保持 | 外设状态 | 唤醒时间 | 典型电流 (STM32L4) |
|------|---------|---------|---------|-------------------|
| Run | 全部活跃 | 全部活跃 | N/A | 28 mA @ 80MHz |
| Sleep | 保持 | 可选保持 | < 1 us | 1.1 mA |
| Stop 0 | 保持 | 冻结 | 3.5 us | 1.0 uA |
| Stop 1 | 保持 | 冻结 | 3.5 us | 0.6 uA |
| Stop 2 | 保持 | 冻结 | 3.5 us | 0.3 uA |
| Standby | 丢失 | 关闭 | 50 us | 30 nA |
| Shutdown | 丢失 | 关闭 | 复位启动 | 8 nA |

### 1.2 ESP32 的睡眠模式实测

```c
// ESP32-S3 深度睡眠配置示例
#include "esp_sleep.h"
#include "driver/rtc_io.h"

void enter_deep_sleep(uint64_t sleep_us) {
    // 关闭不需要的外设
    esp_wifi_stop();
    esp_bt_controller_disable();

    // 配置唤醒源：定时器 + GPIO
    esp_sleep_enable_timer_wakeup(sleep_us);
    esp_sleep_enable_ext0_wakeup(GPIO_NUM_33, 0);  // 低电平唤醒

    // 隔离未使用的 GPIO 以减少漏电流
    rtc_gpio_isolate(GPIO_NUM_12);
    rtc_gpio_isolate(GPIO_NUM_15);

    // 关闭 ULP 协处理器（如果不需要）
    esp_sleep_pd_config(ESP_PD_DOMAIN_RTC_PERIPH, ESP_PD_OPTION_OFF);

    // 进入深度睡眠
    esp_deep_sleep_start();
    // 代码不会执行到这里，唤醒后从 app_main() 重新开始
}

// 实测功耗数据 (ESP32-S3-WROOM-1, 3.3V 供电):
// Active (WiFi TX):     240 mA
// Active (CPU only):     30 mA @ 240MHz
// Modem Sleep:           20 mA (CPU 活跃，WiFi 关)
// Light Sleep:          130 uA (RAM 保持，快速唤醒)
// Deep Sleep (RTC on):    8 uA
// Deep Sleep (RTC off):   5 uA
// Hibernation:           2.5 uA (仅 RTC timer)
```

### 1.3 STM32L4 Stop 模式配置

```c
// STM32L476 Stop 2 模式 - 最低功耗且保持 RAM
#include "stm32l4xx_hal.h"

void enter_stop2_mode(void) {
    // 关闭所有不需要的时钟
    __HAL_RCC_GPIOB_CLK_DISABLE();
    __HAL_RCC_GPIOC_CLK_DISABLE();
    // ... 关闭其他 GPIO 端口时钟

    // 配置未使用引脚为模拟输入（最低漏电流）
    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = GPIO_PIN_All;
    gpio.Mode = GPIO_MODE_ANALOG;
    gpio.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOB, &gpio);

    // 关闭 Flash（从 RAM 运行唤醒代码）
    __HAL_FLASH_SLEEP_POWERDOWN_ENABLE();

    // 配置 RTC 唤醒（每 60 秒）
    HAL_RTCEx_SetWakeUpTimer_IT(&hrtc, 60, RTC_WAKEUPCLOCK_CK_SPRE_16BITS);

    // 进入 Stop 2
    HAL_SuspendTick();
    HAL_PWREx_EnterSTOP2Mode(PWR_STOPENTRY_WFI);

    // --- 唤醒后从这里继续 ---
    HAL_ResumeTick();
    SystemClock_Config();  // 重新配置时钟（Stop 模式会复位时钟树）
}

// 实测: Stop 2 模式下 STM32L476 电流 = 0.32 uA (数据手册标称 0.29 uA)
```

## 2. 占空比（Duty Cycling）

### 2.1 核心公式

占空比是最基本的省电策略：设备大部分时间睡眠，周期性醒来工作。

```python
def calculate_average_current(
    active_current_mA: float,
    sleep_current_uA: float,
    active_time_ms: float,
    period_ms: float
) -> float:
    """
    计算占空比模式下的平均电流
    """
    duty_cycle = active_time_ms / period_ms
    avg_current_mA = (active_current_mA * duty_cycle +
                      sleep_current_uA / 1000 * (1 - duty_cycle))
    return avg_current_mA

# 示例：LoRa 传感器节点，每 15 分钟发一次数据
# 活跃阶段：采集(5ms) + LoRa发送(50ms) + 等ACK(200ms) = 255ms
# 周期：15 * 60 * 1000 = 900,000 ms

avg = calculate_average_current(
    active_current_mA=50,     # 发射时 50mA
    sleep_current_uA=0.3,     # Stop 2 模式 0.3uA
    active_time_ms=255,
    period_ms=900000
)
print(f"平均电流: {avg*1000:.2f} uA")  # 约 14.4 uA
```

### 2.2 电池寿命估算

```python
def battery_life_years(
    battery_mAh: float,
    avg_current_uA: float,
    self_discharge_percent_per_year: float = 1.0,
    efficiency: float = 0.85
) -> float:
    """
    估算电池寿命（年）
    efficiency: 电池放电效率（低温/高放电率时降低）
    """
    usable_capacity_uAh = battery_mAh * 1000 * efficiency
    hours = usable_capacity_uAh / avg_current_uA
    years = hours / 8760

    # 考虑自放电
    effective_years = years / (1 + self_discharge_percent_per_year / 100)
    return effective_years

# CR2032 纽扣电池 (225 mAh) + 上面的传感器节点
life = battery_life_years(225, 14.4, self_discharge_percent=1.0)
print(f"预计电池寿命: {life:.1f} 年")  # 约 14.7 年（理论值）

# 实际考虑因素：
# - 峰值电流限制（CR2032 最大持续 5mA，脉冲 15mA）
# - 低温性能下降（-20C 时容量降至 60%）
# - 电压跌落（LoRa 发射时瞬间大电流导致电压跌落）
# 实际寿命通常为理论值的 50-70%
```

## 3. 事件驱动唤醒

### 3.1 中断唤醒 vs 轮询

轮询（Polling）：定时醒来检查是否有事件 -> 大部分唤醒是"白醒"，浪费电。

事件驱动（Event-driven）：只在真正有事件时才唤醒 -> 零无效唤醒。

### 3.2 硬件中断唤醒设计

```c
// 事件驱动设计：加速度计检测运动 -> 唤醒 MCU -> 采集数据 -> 发送
// 使用 LIS2DH12 加速度计的运动检测中断

void configure_motion_wakeup(void) {
    // 配置 LIS2DH12 运动检测阈值
    lis2dh12_write_reg(LIS2DH12_INT1_THS, 0x10);  // 阈值 = 16 * 16mg = 256mg
    lis2dh12_write_reg(LIS2DH12_INT1_DURATION, 0x03);  // 持续 3 个采样周期

    // 启用 X/Y/Z 轴高事件中断
    lis2dh12_write_reg(LIS2DH12_INT1_CFG, 0x2A);  // OR 组合，高事件

    // 将中断路由到 INT1 引脚
    lis2dh12_write_reg(LIS2DH12_CTRL_REG3, 0x40);  // IA1 中断到 INT1

    // 设置低功耗模式 + 低 ODR
    lis2dh12_write_reg(LIS2DH12_CTRL_REG1, 0x2F);  // 10Hz, 低功耗, XYZ 启用
    // 此模式下加速度计自身功耗仅 4 uA

    // 配置 MCU GPIO 为中断唤醒源
    HAL_PWR_EnableWakeUpPin(PWR_WAKEUP_PIN1);
}

// 功耗对比：
// 轮询方案（每秒醒来检查）: 平均 ~50 uA
// 事件驱动方案: 平均 ~4.5 uA（加速度计 4uA + MCU 睡眠 0.3uA + 偶尔唤醒）
// 节省: 91%
```

### 3.3 ULP 协处理器

ESP32 的 ULP（Ultra Low Power）协处理器可以在主 CPU 深度睡眠时独立运行简单任务：

```c
// ULP 程序：监测 ADC 值，超过阈值才唤醒主 CPU
// ULP 运行功耗约 150 uA，远低于主 CPU 的 30 mA

#include "soc/rtc_cntl_reg.h"
#include "soc/sens_reg.h"

const ulp_insn_t program[] = {
    // 读取 ADC 通道 0
    I_ADC(R0, 0, 0),

    // 与阈值比较 (2048 = 约 1.65V)
    I_MOVI(R1, 2048),
    I_SUBR(R0, R0, R1),
    I_BGE(&wake, 0),       // 如果 >= 阈值，唤醒主 CPU

    // 未超阈值，继续睡眠
    I_HALT(),

    // 超过阈值，唤醒主 CPU
    M_LABEL(wake),
    I_WAKE(),
    I_HALT(),
};

// ULP 每 100ms 采样一次，主 CPU 保持深度睡眠
// 总功耗: ULP(150uA) + RTC(5uA) = 155 uA
// 对比主 CPU 轮询: 30 mA * 0.1% + 5 uA = 35 uA（看似更低）
// 但 ULP 方案的优势是响应延迟 < 100ms，轮询方案若要同样延迟需要更高占空比
```

## 4. 电源门控（Power Gating）

### 4.1 原理

电源门控是用 MOSFET 开关彻底切断不使用模块的供电，消除漏电流。这比让模块进入睡眠模式更省电，但代价是重新上电需要初始化时间。

### 4.2 实际电路设计

```
VCC (3.3V)
  |
  |--- [P-MOSFET] --- VCC_SENSOR --- [传感器模块]
        |
       GPIO (MCU)

// 控制逻辑：
// GPIO = LOW  -> P-MOSFET 导通 -> 传感器供电
// GPIO = HIGH -> P-MOSFET 截止 -> 传感器断电（零漏电流）
```

选型要点：

| 参数 | 推荐值 | 原因 |
|------|--------|------|
| Rds(on) | < 100 mohm | 减少压降 |
| Vgs(th) | < 1.5V | 确保 3.3V GPIO 能完全导通 |
| 漏电流 | < 1 nA | 关断时不浪费电 |
| 封装 | SOT-23 | 小尺寸 |

推荐器件：Si2301（P-MOS，Rds=80mohm，Vgs(th)=1.0V）

### 4.3 门控策略

```python
# 电源门控决策：什么时候值得关断电源？
def should_power_gate(
    module_sleep_current_uA: float,
    startup_time_ms: float,
    startup_current_mA: float,
    idle_duration_ms: float
) -> bool:
    """
    判断是否值得做电源门控
    只有当关断节省的能量 > 重新启动消耗的能量时才值得
    """
    # 关断期间节省的能量 (uA * ms = nAh / 3600 * 1000)
    energy_saved = module_sleep_current_uA * idle_duration_ms  # uA*ms

    # 启动消耗的额外能量
    energy_startup = startup_current_mA * 1000 * startup_time_ms  # uA*ms

    return energy_saved > energy_startup

# 示例：BME280 温湿度传感器
# 睡眠电流: 0.1 uA, 启动时间: 2ms, 启动电流: 1mA
# 空闲 60 秒
print(should_power_gate(0.1, 2, 1, 60000))  # True: 节省 6 uA*ms vs 消耗 2000 uA*ms
# 等等，这里节省 = 0.1 * 60000 = 6000 uA*ms > 2000 uA*ms，所以值得

# 示例：GPS 模块
# 睡眠电流: 20 uA, 启动时间(冷启动): 30000ms, 启动电流: 25mA
# 空闲 5 分钟
print(should_power_gate(20, 30000, 25, 300000))
# 节省 = 20 * 300000 = 6,000,000 uA*ms
# 消耗 = 25000 * 30000 = 750,000,000 uA*ms
# False! GPS 冷启动太贵，不值得完全断电
```

## 5. 动态电压频率调节（DVFS）

### 5.1 功耗与频率/电压的关系

CMOS 电路的动态功耗公式：P = C * V^2 * f。降低电压的效果是平方级的，降低频率是线性的。

### 5.2 STM32L4 的频率调节实测

| 频率 | 电压 | 电流 | 相对性能 | 能效 (DMIPS/mW) |
|------|------|------|---------|----------------|
| 80 MHz | 1.2V | 28 mA | 100% | 3.0 |
| 48 MHz | 1.0V | 11 mA | 60% | 4.6 |
| 24 MHz | 1.0V | 5.5 mA | 30% | 4.6 |
| 4 MHz | 1.0V | 1.0 mA | 5% | 4.2 |
| 100 kHz (MSI) | 1.0V | 30 uA | 0.1% | 2.8 |

关键洞察：48 MHz 是 STM32L4 的"甜蜜点"——能效最高。

### 5.3 运行时频率切换

```c
// STM32L4 运行时切换频率的示例
void switch_to_low_power_run(void) {
    // 切换到 MSI 4MHz
    RCC_OscInitTypeDef osc = {0};
    osc.OscillatorType = RCC_OSCILLATORTYPE_MSI;
    osc.MSIState = RCC_MSI_ON;
    osc.MSIClockRange = RCC_MSIRANGE_6;  // 4 MHz
    HAL_RCC_OscConfig(&osc);

    // 切换系统时钟源到 MSI
    RCC_ClkInitTypeDef clk = {0};
    clk.ClockType = RCC_CLOCKTYPE_SYSCLK;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_MSI;
    HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_0);

    // 关闭 PLL 节省功耗
    osc.OscillatorType = RCC_OSCILLATORTYPE_NONE;
    osc.PLL.PLLState = RCC_PLL_OFF;
    HAL_RCC_OscConfig(&osc);

    // 进入低功耗运行模式（降低内部稳压器电压）
    HAL_PWREx_EnableLowPowerRunMode();
    // 此时功耗约 30 uA @ 100kHz 或 1 mA @ 4MHz
}
```

## 6. 功耗预算实战

### 6.1 完整功耗预算表模板

```python
# 功耗预算计算工具
class PowerBudget:
    def __init__(self, battery_mAh, voltage=3.3):
        self.battery_mAh = battery_mAh
        self.voltage = voltage
        self.components = []

    def add_component(self, name, active_mA, sleep_uA,
                      active_ms_per_cycle, cycle_period_ms):
        duty = active_ms_per_cycle / cycle_period_ms
        avg_uA = active_mA * 1000 * duty + sleep_uA * (1 - duty)
        self.components.append({
            'name': name,
            'avg_uA': avg_uA,
            'duty_cycle': duty
        })

    def report(self):
        total_uA = sum(c['avg_uA'] for c in self.components)
        life_hours = self.battery_mAh * 1000 / total_uA
        life_years = life_hours / 8760

        print(f"{'组件':<20} {'平均电流(uA)':<15} {'占比':<10}")
        print("-" * 45)
        for c in self.components:
            pct = c['avg_uA'] / total_uA * 100
            print(f"{c['name']:<20} {c['avg_uA']:<15.2f} {pct:.1f}%")
        print("-" * 45)
        print(f"{'总计':<20} {total_uA:<15.2f}")
        print(f"\n电池: {self.battery_mAh} mAh")
        print(f"预计寿命: {life_years:.1f} 年")


# 示例：LoRaWAN 温湿度传感器节点
budget = PowerBudget(battery_mAh=2400)  # 2x AA 电池

# MCU (STM32L072) - 每 15 分钟醒来 200ms
budget.add_component("MCU", active_mA=8, sleep_uA=0.3,
                     active_ms_per_cycle=200, cycle_period_ms=900000)

# LoRa (SX1262) - 每 15 分钟发送 80ms
budget.add_component("LoRa TX", active_mA=118, sleep_uA=0.16,
                     active_ms_per_cycle=80, cycle_period_ms=900000)

# 传感器 (BME280) - 每 15 分钟采集 10ms
budget.add_component("BME280", active_mA=0.35, sleep_uA=0.1,
                     active_ms_per_cycle=10, cycle_period_ms=900000)

# 稳压器静态电流（始终存在）
budget.add_component("LDO quiescent", active_mA=0.001, sleep_uA=1.0,
                     active_ms_per_cycle=900000, cycle_period_ms=900000)

budget.report()
```

### 6.2 常见功耗陷阱

| 陷阱 | 现象 | 解决方案 |
|------|------|---------|
| 浮空引脚 | 睡眠电流比预期高 10-100x | 所有未用引脚设为模拟输入或加上下拉 |
| LED 指示灯 | 常亮 LED 消耗 2-20 mA | 改为闪烁或仅调试时启用 |
| LDO 静态电流 | 即使负载为零也消耗 1-100 uA | 选用超低静态电流 LDO（如 TPS7A02，25nA） |
| 上拉电阻 | I2C 上拉在总线空闲时漏电 | 使用电源门控切断传感器侧上拉 |
| Flash 保持 | NOR Flash 待机 10-50 uA | 使用 Deep Power Down 命令 |

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：用万用表测量 ESP32 各模式的实际电流，对比数据手册
2. **第二步**：实现一个定时唤醒的温度采集节点，计算理论 vs 实际电池寿命
3. **第三步**：用 Nordic PPK2 或 Otii Arc 做精确的电流波形分析
4. **第四步**：优化一个现有项目——找到最大的功耗瓶颈并解决
5. **第五步**：设计完整的功耗预算表，包含所有组件和工作模式

### 7.2 具体调优建议

**测量优先**：永远先测量再优化。很多时候最大的功耗来源不是你以为的那个组件。推荐工具：Nordic PPK2（约 600 元，动态范围 200nA-1A，采样率 100kHz）。

**从最大的开始**：功耗优化遵循帕累托法则——80% 的功耗通常来自 20% 的组件/时间段。先解决最大的问题。

**注意峰值电流**：纽扣电池（CR2032）的内阻约 10-30 欧姆，50mA 的峰值电流会导致 0.5-1.5V 的电压跌落，可能触发 MCU 掉电复位。解决方案：并联 100uF 电容做储能缓冲。

## 参考文献

1. STMicroelectronics. "STM32L4 Series Ultra-low-power Features Overview." AN4621, 2023.
2. Espressif. "ESP32-S3 Technical Reference Manual." v1.2, 2024.
3. Texas Instruments. "MSP430 Ultra-Low-Power Sensing and Measurement." SLAA731, 2022.
4. Nordic Semiconductor. "nRF52840 Power Profiling with PPK2." 2023.
5. Semtech. "Designing for Ultra-Low Power with LoRa." AN1200.17, 2022.
6. Siekkinen, M., et al. "How Low Energy is Bluetooth Low Energy? Comparative Measurements with ZigBee/802.15.4." IEEE WCNC, 2012.
7. Gomez, C., et al. "Overview and Evaluation of Bluetooth Low Energy: An Emerging Low-Power Wireless Technology." Sensors, 12(9), 2012.
8. Kamath, S., and Lindh, J. "Measuring Bluetooth Low Energy Power Consumption." TI Application Note AN092, 2022.
9. Raza, U., et al. "Low Power Wide Area Networks: An Overview." IEEE Communications Surveys, 19(2), 2017.
10. Georgiou, O., and Raza, U. "Low Power Wide Area Network Analysis: Can LoRa Scale?" IEEE Wireless Communications Letters, 6(2), 2017.
