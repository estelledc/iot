# MCU睡眠模式层级：Sleep/Stop/Standby功耗对比

> **难度**：🟢 初级 | **领域**：低功耗设计 | **阅读时间**：约 18 分钟

## 引言

想象你的手机有四种"省电方式"：只关屏幕(CPU暂停但系统还在跑)、关屏幕再关Wi-Fi和蓝牙(大部分外设断电)、只留闹钟和来电振子(几乎全关但还能叫醒你)、以及完全关机只剩一个物理按键能开机(彻底断电，醒来要从头启动)。每种方式省的电越来越多，但"醒来"能做的事越来越少、恢复速度也越来越慢。

MCU的睡眠模式就是同样的逻辑。一个靠CR2032纽扣电池跑5年的IoT温度传感器，99.9%的时间都在"睡觉"，只在采集和发送数据的那几毫秒才"醒来"。选对睡眠模式，直接决定电池能用1年还是10年。本文以STM32为主线，系统对比Sleep/Stop/Standby各模式的功耗、唤醒源和适用场景，并横向对比nRF52和ESP32。

## 1. 为什么低功耗对IoT至关重要

### 1.1 电池寿命的数学

IoT设备最常见的供电是纽扣电池或一次性锂亚电池：

| 电池类型 | 标称容量 | 标称电压 | 最大脉冲电流 | 典型应用 |
|---------|---------|---------|------------|---------|
| CR2032 | 225 mAh | 3.0V | ~15 mA | 传感器节点、遥控器 |
| CR2450 | 620 mAh | 3.0V | ~15 mA | 空气质量监测 |
| ER14250 (锂亚) | 1200 mAh | 3.6V | ~50 mA | 智能水表、燃气表 |

核心公式：`电池寿命(小时) = 电池容量(mAh) / 平均电流(mA)`

MCU一直以10mA运行，CR2032只能撑约22小时。但如果99.9%时间在1uA深度睡眠，平均电流降到微安级，电池寿命就能延长到数年。

### 1.2 IoT节点的真实功耗分布

典型LoRa温度传感器节点，15分钟采集一次：

```
时间段              电流        时长      时间占比   能耗占比
深度睡眠(Stop 2)   0.3 uA     899.7s   99.97%    0.3%
传感器采集          0.35 mA    5 ms     0.0006%   0.2%
LoRa发送            45 mA      50 ms    0.0056%   28%
等待ACK             10 mA      200 ms   0.022%    27%
MCU处理             8 mA       45 ms    0.005%    4.5%
```

核心洞察：睡眠占99.97%的时间但能耗只占0.3%。但如果选错模式(用Sleep而不是Stop)，睡眠电流从0.3uA变成1.1mA，睡眠能耗就变成总能耗的90%以上。模式选择至关重要。

## 2. STM32睡眠模式全解析

### 2.1 模式层级概览

STM32L4系列提供6种电源模式，从浅到深：

```
Run -> Sleep -> Stop 0 -> Stop 1 -> Stop 2 -> Standby -> Shutdown
       CPU暂停  时钟停止  低功耗    更多断电   核心断电   几乎全断电
       外设全跑  RAM保持  稳压器    RAM保持   RAM丢失   RAM丢失
```

### 2.2 各模式详细对比

| 特性 | Sleep | Stop 0 | Stop 1 | Stop 2 | Standby | Shutdown |
|------|-------|--------|--------|--------|---------|----------|
| CPU | 暂停 | 停止 | 停止 | 停止 | 断电 | 断电 |
| RAM | 保持 | 保持 | 保持 | 保持 | 丢失 | 丢失 |
| 寄存器 | 保持 | 保持 | 保持 | 保持 | 丢失 | 丢失 |
| 主时钟 | 保持 | 停止 | 停止 | 停止 | 停止 | 停止 |
| 外设 | 全部可用 | 冻结 | 冻结 | 冻结 | 断电 | 断电 |
| 稳压器 | 主稳压器 | 主稳压器 | 低功耗 | 低功耗 | 断电 | 断电 |

### 2.3 电流消耗实测 (STM32L476, 3.0V, 25度C)

| 模式 | 数据手册标称 | 实测典型值 | 说明 |
|------|------------|----------|------|
| Run @ 80MHz | 7.0 mA | 7.2 mA | 全速运行 |
| Low Power Run @ 100kHz | 30 uA | 32 uA | 低频运行 |
| Sleep @ 80MHz | 1.1 mA | 1.15 mA | CPU暂停 |
| Stop 0 | 1.0 uA | 1.1 uA | 主稳压器保持 |
| Stop 1 | 0.6 uA | 0.65 uA | 低功耗稳压器 |
| Stop 2 | 0.29 uA | 0.32 uA | 更多外设断电 |
| Standby (RTC on) | 30 nA | 35 nA | RAM丢失 |
| Shutdown | 8 nA | 9 nA | 几乎完全断电 |

Stop 2是"保持RAM"模式中最低功耗的选择，也是IoT传感器节点最常用的模式。

## 3. 唤醒源与延迟

### 3.1 唤醒源对比

| 唤醒源 | Sleep | Stop | Standby | Shutdown |
|--------|-------|------|---------|----------|
| 任何中断 (NVIC) | 支持 | 不支持 | 不支持 | 不支持 |
| 外部中断 (EXTI) | 支持 | 支持 | 支持(WKUP) | 支持(WKUP) |
| RTC闹钟/唤醒 | 支持 | 支持 | 支持 | 可选 |
| USART/I2C/SPI | 支持 | 不支持 | 不支持 | 不支持 |
| WKUP引脚 | N/A | 支持 | 支持 | 支持 |

### 3.2 唤醒延迟与恢复代价

| 从模式 | 唤醒延迟 | 唤醒后状态 | 恢复操作 |
|--------|---------|----------|---------|
| Sleep | < 1 us | 完整保持 | 无需恢复 |
| Stop 0/1/2 | ~3.5 us | 寄存器保持 | 重配时钟树 |
| Standby | ~50 us | 复位状态 | 完整初始化 |
| Shutdown | ~1 ms | 复位状态 | 完整初始化 + 备份寄存器恢复 |

关键区别：Sleep/Stop唤醒后从WFI下一条指令继续执行；Standby/Shutdown唤醒后等同于复位，程序从main()重新开始。

```
模式深度 -->       浅                                    深
            Sleep    Stop 0   Stop 1   Stop 2   Standby   Shutdown
延迟:       <1us     3.5us    3.5us    3.5us    50us      ~1ms
功耗:       1.1mA    1.0uA    0.6uA    0.3uA    30nA      8nA
状态保持:   完整     完整     完整     完整     丢失      丢失
唤醒灵活度: 最高     中等     中等     中等     有限      最少
```

## 4. 进入各模式的代码示例

### 4.1 Sleep模式

Sleep是最浅的睡眠，CPU暂停但时钟和外设继续运行，任何中断都能唤醒。

```c
// STM32L4 进入 Sleep 模式
void enter_sleep_mode(void) {
    HAL_PWR_EnableSleepOnExit();  // 中断返回后自动回Sleep
    HAL_PWR_EnterSLEEPMode(PWR_MAINREGULATOR_ON, PWR_SLEEPENTRY_WFI);
}
// 功耗: ~1.1 mA | 适用: 等待USART/ADC/Timer中断
```

### 4.2 Stop 2模式

Stop模式停止所有时钟，但RAM和寄存器内容保持。Stop 2是最常用的深度睡眠模式。

```c
// STM32L4 进入 Stop 2 模式
void enter_stop2_mode(void) {
    // 关闭不需要的GPIO时钟
    __HAL_RCC_GPIOB_CLK_DISABLE();
    __HAL_RCC_GPIOC_CLK_DISABLE();

    // 未使用引脚配为模拟输入 (最小漏电流)
    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = GPIO_PIN_All;
    gpio.Mode = GPIO_MODE_ANALOG;
    gpio.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOB, &gpio);

    // Flash低功耗 + RTC唤醒(每60秒)
    __HAL_FLASH_SLEEP_POWERDOWN_ENABLE();
    HAL_RTCEx_SetWakeUpTimer_IT(&hrtc, 60,
        RTC_WAKEUPCLOCK_CK_SPRE_16BITS);

    HAL_SuspendTick();
    HAL_PWREx_EnterSTOP2Mode(PWR_STOPENTRY_WFI);

    // --- 唤醒后从这里继续 ---
    HAL_ResumeTick();
    SystemClock_Config();  // 必须重配时钟!
}
// 功耗: ~0.3 uA | 适用: 周期性采集、事件驱动唤醒
```

### 4.3 Standby模式

核心完全断电，RAM和寄存器全部丢失。只有RTC、备份寄存器和WKUP引脚保持工作。

```c
// STM32L4 进入 Standby 模式
void enter_standby_mode(void) {
    HAL_PWR_EnableBkUpAccess();
    RTC->BKP0R = 0xA5A5;         // 魔术字标记
    RTC->BKP1R = sensor_count;   // 保存关键数据

    HAL_PWR_EnableWakeUpPin(PWR_WAKEUP_PIN1_HIGH);

    // 清除唤醒标志 (必须!)
    __HAL_PWR_CLEAR_FLAG(PWR_FLAG_WU);
    __HAL_PWR_CLEAR_FLAG(PWR_FLAG_SB);

    HAL_PWR_EnterSTANDBYMode();
    // 永远不会到这里, 唤醒后从main()重新开始
}

// main() 中判断是否从 Standby 唤醒:
if (__HAL_PWR_GET_FLAG(PWR_FLAG_SB) != RESET) {
    HAL_PWR_EnableBkUpAccess();
    if (RTC->BKP0R == 0xA5A5) sensor_count = RTC->BKP1R;
    __HAL_PWR_CLEAR_FLAG(PWR_FLAG_SB);
}
// 功耗: ~30 nA | 适用: 长时间休眠(小时/天级别)
```

### 4.4 Shutdown模式

Shutdown是最低功耗模式，仅STM32L4/L5/G4/G0等新系列才有。

```c
void enter_shutdown_mode(void) {
    HAL_PWR_EnableBkUpAccess();
    RTC->BKP0R = 0xA5A5;
    HAL_PWR_EnableWakeUpPin(PWR_WAKEUP_PIN1_HIGH);
    __HAL_PWR_CLEAR_FLAG(PWR_FLAG_WU);
    HAL_PWREx_EnterSHUTDOWNMode();  // 唤醒 = 完全复位
}
// 功耗: ~8 nA | 适用: 仓储/运输模式, 几年不工作
```

## 5. 外设行为与RAM保持

### 5.1 外设在睡眠中的状态

| 外设 | Sleep | Stop | Standby | Shutdown |
|------|-------|------|---------|----------|
| USART/SPI/I2C | 继续运行 | 停止(冻结) | 断电 | 断电 |
| ADC/Timer/DMA | 继续运行 | 停止(冻结) | 断电 | 断电 |
| RTC | 继续运行 | 可选保持 | 可选保持 | 可选保持 |
| GPIO | 保持 | 保持 | 保持(WKUP) | 保持(WKUP) |
| Flash | 保持 | 保持 | 断电 | 断电 |

Stop模式下外设"冻结"：计数器暂停、通信停止、ADC停止转换，唤醒后从暂停处继续，无需重新初始化。

### 5.2 RAM保持选项

| 模式 | SRAM1 (主RAM) | SRAM2 (保持RAM) | 备份寄存器 |
|------|--------------|----------------|-----------|
| Sleep/Stop | 保持 | 保持 | 保持 |
| Standby | 丢失 | 可选保持 | 保持 |
| Shutdown | 丢失 | 丢失 | 保持 |

Standby模式保持SRAM2会使电流从30nA增加到300nA(10倍增幅)。此时Stop 2也是300nA但唤醒更快，所以"需要保持RAM"场景优先选Stop 2。

保存数据策略：小于80字节用备份寄存器(RTC BKP)，80字节~32KB用SRAM2保持，更大则写Flash或外部EEPROM。

## 6. 电池寿命计算实例

### 6.1 CR2032 + 温度传感器节点

场景：每5分钟采集一次温度，通过BLE广播发送。

```python
# CR2032 电池寿命计算
battery_mah = 225      # CR2032 标称容量
efficiency = 0.85      # 放电效率

period_s = 300         # 5分钟周期
active_time_s = 0.15   # 150ms活跃
active_current_ma = 8.0 # MCU + 传感器 + BLE
sleep_current_ua = 0.3  # Stop 2

duty_cycle = active_time_s / period_s
avg_ua = active_current_ma * 1000 * duty_cycle + sleep_current_ua * (1 - duty_cycle)
life_years = battery_mah * 1000 * efficiency / avg_ua / 8760

print(f"占空比: {duty_cycle*100:.3f}%")
print(f"平均电流: {avg_ua:.2f} uA")
print(f"电池寿命: {life_years:.1f} 年")
# 输出: 占空比 0.050%, 平均 4.30 uA, 寿命 5.1 年
```

### 6.2 不同睡眠模式的寿命对比

```python
modes = {
    "Sleep (1.1mA)": 1100,      # uA
    "Stop 0 (1.0uA)": 1.0,
    "Stop 2 (0.3uA)": 0.3,
    "Standby (30nA)": 0.03,
    "Shutdown (8nA)": 0.008,
}
for name, sleep_ua in modes.items():
    avg = 8000 * 0.15/300 + sleep_ua * (1 - 0.15/300)
    life = 225 * 850 / avg / 8760
    print(f"{name:25s} -> 平均 {avg:7.2f} uA -> 寿命 {life:5.1f} 年")
# Sleep(1.1mA) -> 1100 uA -> 0.06年(仅22天!)
# Stop 2(0.3uA)-> 4.30 uA -> 5.1年
# Standby(30nA)-> 4.00 uA -> 5.5年
```

关键发现：当活跃电流远大于睡眠电流时，睡眠模式的差异对总寿命影响很小。优化方向优先级：缩短活跃时间 > 降低活跃电流 > 追求更深睡眠。

## 7. 跨平台对比：STM32 vs nRF52 vs ESP32

### 7.1 睡眠模式与功耗横向对比

| 模式层级 | STM32L476 | nRF52840 | ESP32-S3 |
|---------|-----------|----------|----------|
| 浅睡眠 | Sleep (1.1mA) | ON Idle (1.2uA) | Light Sleep (130uA) |
| 深睡眠(RAM保持) | Stop 2 (0.3uA) | ON Idle (1.2uA) | Deep Sleep (8uA) |
| 深睡眠(RAM不保持) | Standby (30nA) | OFF (0.3uA) | Deep Sleep (8uA) |
| 最低功耗 | Shutdown (8nA) | OFF (0.3uA) | Deep Sleep (5uA) |

### 7.2 综合特性对比

| 特性 | STM32L4 | nRF52840 | ESP32-S3 |
|------|---------|----------|----------|
| Active 电流 | 7 mA @ 80MHz | 1.2 mA @ 64MHz | 30 mA @ 240MHz |
| 最低睡眠 | 8 nA | 300 nA | 5 uA |
| 集成射频 | 无 | BLE 5.0 | WiFi + BLE |
| 发射电流 | N/A | 5.3 mA (BLE) | 240 mA (WiFi) |
| RAM保持唤醒 | 3.5 us | ~2 us | ~10 us |
| RAM不保持唤醒 | 50 us | ~1 ms | ~5 ms |
| 典型电池寿命 | 数年(纽扣电池) | 数年(纽扣电池) | 数天-数周(锂电池) |

### 7.3 选型建议

| 场景 | 推荐 | 理由 |
|------|------|------|
| 纯传感器采集(无射频) | STM32L4 | 最低睡眠电流, 丰富外设 |
| BLE传感器 | nRF52 | 集成BLE, 综合功耗最优 |
| WiFi IoT网关 | ESP32 | WiFi必备, 开发便捷 |
| 10年寿命纽扣电池 | STM32L4 / MSP430 | 睡眠电流纳安级 |

## 8. 占空比IoT传感器的设计模式

### 8.1 经典采集-发送-睡眠循环

```c
void sensor_node_main_loop(void) {
    while (1) {
        SystemClock_Config();             // 恢复时钟
        float temp = read_temperature();  // 采集
        process_data(temp);               // 处理
        radio_send(packet, len);          // 发送
        enter_stop2_mode();               // RTC定时唤醒
    }
}
```

### 8.2 事件驱动唤醒模式

```c
// 门窗传感器: GPIO中断唤醒, 零无效唤醒
void door_sensor_setup(void) {
    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = DOOR_SENSOR_PIN;
    gpio.Mode = GPIO_MODE_IT_RISING_FALLING;
    gpio.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(DOOR_SENSOR_PORT, &gpio);

    HAL_NVIC_SetPriority(EXTI0_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(EXTI0_IRQn);
    HAL_PWREx_EnterSTOP2Mode(PWR_STOPENTRY_WFI);
}

void HAL_GPIO_EXTI_Callback(uint16_t pin) {
    if (pin == DOOR_SENSOR_PIN) {
        bool open = HAL_GPIO_ReadPin(DOOR_SENSOR_PORT, pin);
        radio_send_alert(open);
    }
}
```

### 8.3 设计模式选择指南

```
唤醒频率 < 1次/小时 且 不需要RAM? -> Standby / Shutdown
唤醒频率 < 1次/分钟 且 需要RAM?  -> Stop 2
唤醒频率 > 1次/秒?               -> Sleep 或 Low Power Run
事件不规律 (如门窗传感器)?       -> Stop 2 + EXTI中断
需要同时等待定时和事件?           -> Stop 2 + RTC + EXTI双唤醒源
```

## 9. 常见踩坑与调试

### 9.1 睡眠电流偏高的常见原因

| 问题 | 症状 | 解决方案 |
|------|------|---------|
| 浮空GPIO | 电流高10-100倍 | 未用引脚配为模拟输入 |
| SWD调试器连接 | 电流高几百uA | 调试完断开ST-Link |
| LDO静态电流 | 待机电流>1uA | 换低静态LDO (如TPS7A02, 25nA) |
| I2C上拉漏电 | 电流高几十uA | 电源门控上拉电阻 |
| 外部传感器待机 | 电流高几十uA | 断电不用的传感器 |
| HSE未关闭 | Stop模式电流高 | 进入Stop前关闭HSE |

### 9.2 功耗调试流程

```
1. 测 Run 电流 -> 确认基准
2. 进 Sleep -> 应为 ~1mA
3. 进 Stop 2 -> 应为 ~0.3uA (偏高则逐个断外设找漏电源)
4. 进 Standby -> 应为 ~30nA (偏高则检查GPIO和WKUP配置)
5. 跑完整工作循环 -> 测平均电流 -> 对比计算值
```

推荐工具：Nordic PPK2 (约600元, 动态范围200nA-1A, 采样率100kHz)。

## 总结

MCU睡眠模式的选择是IoT低功耗设计的核心决策，三个关键要点：

1. **模式选择看需求**：需要保持RAM选Stop 2(0.3uA)；不需要RAM且长时间休眠选Standby(30nA)；频繁唤醒用Sleep(1.1mA但唤醒最快)。不要无脑追求最深睡眠——唤醒和恢复的代价可能抵消省下的电。

2. **活跃阶段才是大头**：在典型的低占空比传感器中，活跃阶段的射频发送贡献了大部分能耗。优化方向优先级：缩短活跃时间 > 降低活跃电流 > 追求更深睡眠。

3. **实测比计算可靠**：数据手册的标称值是理想条件下的最小值。实际PCB布局、外部器件、GPIO配置都会影响睡眠电流。Nordic PPK2或Otii Arc这样的功耗分析工具是低功耗开发不可或缺的伙伴。

## 参考文献

1. STMicroelectronics. "STM32L4xxx Datasheet: Ultra-low-power ARM Cortex-M4 MCU." DS11451, 2023.
2. STMicroelectronics. "STM32L4 Series Ultra-low-power Features Overview." AN4621, 2023.
3. Nordic Semiconductor. "nRF52840 Product Specification v1.1." Nordic Semi, 2022.
4. Espressif Systems. "ESP32-S3 Technical Reference Manual." v1.2, 2024.
5. Yildirim, K.S., et al. "On the Lifetime of Wireless IoT Sensors with Sleep Mode." IEEE IoT Journal, 2021.
