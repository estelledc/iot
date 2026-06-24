# 传感器节点占空比策略与寿命估算

> **难度**：🟡 中级 | **领域**：IoT功耗优化 | **阅读时间**：约 18 分钟

## 引言

想象你值夜班守仓库：不是整夜瞪着监控屏幕，而是每半小时巡一圈、其余时间趴桌上打盹。巡一次花2分钟，打盹28分钟——你的"工作占空比"就是 2/30 = 6.7%。只要闹钟够准、醒得够快，仓库安全不受影响，但你的精力消耗降了一个数量级。

传感器节点的占空比 (Duty Cycling) 就是同样的逻辑。一个靠 CR2032 跑 10 年的温度记录器，99.95% 的时间都在微安级深度睡眠，只在采集和发射的那几十毫秒"醒"过来。**占空比是多少、每个阶段的电流多大、醒来的频率多高——这三件事直接决定了电池寿命是 1 年还是 10 年。** 本文从平均电流公式出发，逐阶段拆解功耗优化策略，并用真实计算案例和测量方法帮你避开估算中最常见的坑。

## 1. 占空比的基本概念

### 1.1 定义与直觉

占空比 (Duty Cycle, DC) 指设备在活跃状态下占总周期时间的比例：

```
DC = T_active / T_cycle
T_active = T_wake + T_sense + T_process + T_transmit + T_shutdown
T_cycle  = T_active + T_sleep
```

典型 IoT 传感器节点的占空比极低：

| 应用场景 | 采样间隔 | 活跃时间 | 占空比 |
|---------|---------|---------|-------|
| 室内温湿度 | 5 min | 80 ms | 0.027% |
| 户外气象站 | 15 min | 120 ms | 0.013% |
| 智能水表 | 30 min | 200 ms | 0.011% |
| 可穿戴心率 | 1 s | 5 ms | 0.5% |

优化重点永远是**减少活跃时间和次数**，而不是降低活跃电流本身。

### 1.2 平均电流公式

整个周期的平均电流是各阶段电流的时间加权平均：

```
I_avg = (I_sleep * T_sleep + I_wake * T_wake + I_sense * T_sense
       + I_process * T_process + I_transmit * T_transmit
       + I_shutdown * T_shutdown) / T_cycle
```

当 DC 远小于 1 时 (典型 IoT 场景)，公式近似为：

```
I_avg = I_sleep + I_active * DC
```

**睡眠电流是地板，活跃电流乘以占空比是增量**。两个要同时压低。

## 2. 传感器节点的功耗剖析

### 2.1 单次工作周期的五个阶段

```
  ___       _____         ____          _______          ____
_|   |_____|     |_______|    |________|       |________|    |__
  Wake    Sensor     Process    Transmit       Shutdown   Sleep
  Setup   Warmup     Reading    + Rx ACK       Cool-down  (dominant)
```

各阶段典型参数 (以 STM32L4 + SHT40 + SX1276 LoRa 为例)：

| 阶段 | 时长 | 电流 | 电量消耗 | 备注 |
|------|------|------|---------|------|
| Wake + Setup | 3 ms | 5 mA | 4.2 nAh | MCU 从 Stop 2 恢复 |
| Sensor Warmup + Read | 12 ms | 0.4 mA | 1.3 nAh | SHT40 加热+读取 |
| Process | 5 ms | 4 mA | 5.6 nAh | CRC校验、数据打包 |
| Transmit (LoRa 20dBm) | 50 ms | 120 mA | 1667 nAh | 最大电流尖峰 |
| Rx ACK Window | 100 ms | 11 mA | 306 nAh | LoRaWAN Class A 接收窗 |
| Shutdown | 2 ms | 3 mA | 1.7 nAh | 配置RTC、进入Stop 2 |
| Sleep (Stop 2) | - | 0.3 uA | - | 占据绝大部分时间 |

核心发现：**发射阶段只占总时间的 50ms，但消耗了 83% 的活跃电量。** 优化发射是最大的杠杆点。

### 2.2 用 PPK2 看到的真实波形

```
电流 (mA)
120 |                    ___________
    |                   /           \
 11 |          ________/             \_______
  5 |  __   /                                \___
0.3 |                                            \___________
    |__________________________________________________________ 时间 (ms)
    |3|12| 5|        50|           100|   2|       ~900000|
    Wake Sense Proc    Transmit       Rx    Shutdown    Sleep
```

注意：Wake 阶段有 PLL 启动脉冲；Transmit 前 5ms 电流较低 (PA 预热)；Rx 窗口切换时有瞬态尖峰。

## 3. 电池容量与寿命估算

### 3.1 电池的有效容量

标称容量不等于可用容量：

```
C_eff = C_nom * f_temp * f_self_discharge * f_cutoff
```

| 电池 | 标称容量 | 10年自放电损失 | 截止电压可用比 | 10年有效容量 |
|------|---------|-------------|-------------|------------|
| CR2032 | 225 mAh | ~5% | ~90% (截止2.0V) | ~192 mAh |
| CR2450 | 620 mAh | ~5% | ~90% | ~531 mAh |
| ER14250 | 1200 mAh | ~10% | ~95% (截止2.5V) | ~1026 mAh |

### 3.2 寿命计算核心公式

```
寿命 (年) = C_eff (mAh) / (I_avg (mA) * 8760)
```

### 3.3 实战计算：CR2032 跑 10 年的目标拆解

**目标**：用一颗 CR2032 (有效容量 192 mAh) 让温度传感器运行 10 年。

Step 1: 反推允许的平均电流

```
I_avg_max = 192 / (10 * 8760) = 2.19 uA
```

Step 2: 计算每次活跃电量

```
Q_active = 5*3 + 0.4*12 + 4*5 + 120*50 + 11*100 + 3*2  (mA*ms)
         = 15 + 4.8 + 20 + 6000 + 1100 + 6
         = 7145.8 mA*ms = 0.001985 mAh
```

Step 3: 反推采样间隔

```
I_avg = I_sleep + Q_active / T_cycle
2.19 >= 0.0003 + 0.001985 / T_cycle
T_cycle >= 0.001985 / 2.1897 = 0.000907 小时 = 3.27 秒
```

不同采样间隔的预估寿命：

| 采样间隔 | I_avg (uA) | 预估寿命 (年) |
|---------|-----------|-------------|
| 10 s | 20.15 | 1.09 |
| 60 s | 3.61 | 6.07 |
| 5 min | 0.96 | 22.8 |
| 15 min | 0.52 | 42.1 |

15 分钟间隔寿命远超 10 年，为自放电和漏电流留出充足裕量。

## 4. 逐阶段优化策略

### 4.1 睡眠阶段

| 优化手段 | 效果 | 代价 |
|---------|------|------|
| 用最深睡眠模式 (Stop 2 / Standby) | 0.3 uA -> 30 nA | Standby 丢失 RAM |
| 关闭 BOR 检测 | 节省约 200 nA | 失去欠压保护 |
| GPIO 配置为模拟输入 | 防止悬空引脚漏电 | 需逐一审查引脚 |

```c
// STM32L4 进入 Stop 2 前的引脚配置
void configure_gpio_for_low_power(void) {
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Mode = GPIO_MODE_ANALOG;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Pin = GPIO_PIN_All;
    GPIO_InitStruct.Pin &= ~(UART_TX_PIN | I2C_SDA_PIN | I2C_SCL_PIN);
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
}
```

### 4.2 唤醒与启动阶段

| 优化手段 | 节省时间 | 说明 |
|---------|---------|------|
| Stop 模式而非 Standby | 2-5 ms | RAM 保持，无需重初始化 |
| 按需初始化外设 | 0.5-2 ms | 只初始化本次需要的 |
| 用 MSI 而非 PLL 启动 | 1-2 ms | MSI 可直接作系统时钟 |

### 4.3 传感器采集阶段

| 优化手段 | 效果 |
|---------|------|
| 选低功耗传感器 | SHT40: 0.4mA vs DHT22: 1.5mA |
| 低精度模式 | SHT40: 高精度12ms, 低精度2ms |
| 批量读多传感器 | 一次唤醒读多个，减少唤醒次数 |

### 4.4 无线发射阶段 (最大杠杆点)

| 优化手段 | 节省电量 | 代价 |
|---------|---------|------|
| 降低发射功率 20->14dBm | 电流降约 50% | 通信距离缩短 |
| 批量上报 (攒数据) | 10次采集发1次 | 实时性下降 |
| 压缩载荷 | 20字节 -> 8字节 | 额外处理时间 |
| 跳过 Rx 窗口 | 节省 100ms * 11mA | 不确认是否送达 |

## 5. 自适应占空比策略

### 5.1 周期性 vs 事件驱动

| 维度 | 周期性 | 事件驱动 |
|------|-------|---------|
| 平均电流可预测性 | 高 | 低 (依赖事件频率) |
| 最坏情况寿命 | 可精确计算 | 需假设事件频率上限 |
| 典型应用 | 温湿度记录、水表 | 烟雾报警、入侵检测 |

### 5.2 混合策略：自适应占空比

根据环境变化动态调整采样频率：

```c
// 自适应占空比：温度变化快时加密采样
typedef struct {
    uint32_t interval_fast;    // 快速模式 (如 30s)
    uint32_t interval_normal;  // 正常模式 (如 300s)
    uint32_t interval_slow;    // 慢速模式 (如 1800s)
    float    delta_threshold;  // 变化阈值 (如 0.5 C)
} adaptive_config_t;

uint32_t compute_next_interval(float current, float previous,
                                adaptive_config_t *cfg) {
    float delta = fabs(current - previous);
    if (delta > cfg->delta_threshold)
        return cfg->interval_fast;
    else if (delta > cfg->delta_threshold * 0.2f)
        return cfg->interval_normal;
    else
        return cfg->interval_slow;
}
```

关键教训：**自适应策略省电的前提是 slow 模式的时间占比足够高**。如果事件频繁发生，自适应反而比固定间隔更费电。

### 5.3 RTC 定时唤醒机制

几乎所有低功耗 MCU 都依赖 RTC 实现定时唤醒：

```
1. MCU 配置 RTC 闹钟值 -> 进入深度睡眠
2. RTC 计数器到达设定值 -> 产生中断
3. 中断触发 MCU 唤醒 -> 执行采集任务
4. 重新配置 RTC，回到睡眠
```

```c
// STM32L4 RTC 唤醒定时器配置
void configure_rtc_wakeup(uint32_t interval_ms) {
    __HAL_RCC_PWR_CLK_ENABLE();
    HAL_PWR_EnableBkUpAccess();
    __HAL_RCC_RTC_CONFIG(RCC_RTCCLKSOURCE_LSE);
    __HAL_RCC_RTC_ENABLE();

    RTC_HandleTypeDef hrtc = {0};
    hrtc.Instance = RTC;
    // prescaler=16, 唤醒周期 = (auto_reload+1)*16/32768 秒
    uint32_t auto_reload = (interval_ms * 32768) / (16 * 1000) - 1;
    HAL_RTCEx_SetWakeUpTimer_IT(&hrtc, auto_reload,
                                 RTC_WAKEUPCLOCK_RTCCLK_DIV16);
    HAL_NVIC_SetPriority(RTC_WKUP_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(RTC_WKUP_IRQn);
}
```

RTC 时钟源选择：

| RTC 时钟源 | 典型电流 | 精度 |
|-----------|---------|------|
| LSE (32.768kHz 晶振) | 0.1 - 0.3 uA | +/- 20 ppm |
| LSI (内部 RC) | 0.1 uA | +/- 5% (温漂大) |
| 外部 TCXO | 1 - 3 uA | +/- 2 ppm |

LSE 是大多数场景的最佳选择。只有对时间精度要求极高时才考虑 TCXO。

## 6. 功耗测量技术

### 6.1 PPK2 测量步骤

Nordic Power Profiler Kit II 是 IoT 功耗测量的事实标准：

1. 断开节点电池，PPK2 连接到电池焊盘
2. Source 模式设电压 3.0V (模拟 CR2032)
3. 开始采样，触发一次完整采集-上报周期
4. 导出波形数据，分析各阶段电流

### 6.2 波形分析要点

```
1. 睡眠电流: 平直段均值 (确认无周期性漏电尖峰)
2. 峰值电流: 发射阶段最高点 (确认不超过电池脉冲能力)
3. 各阶段时长: 用电流跳变沿标记起止
4. 活跃总电量: 对活跃段积分 (mA*ms -> mAh)
5. 睡眠漏电尖峰: 周期性微安级尖峰 = 看门狗/RTC 短暂唤醒
```

### 6.3 替代方案

| 方法 | 精度 | 成本 |
|------|------|------|
| PPK2 | 1 uA | ~$800 |
| Joulescope | 1 uA | ~$400 |
| uCurrent + 示波器 | ~1 uA | ~$150 + 示波器 |
| 串联电阻 + 示波器 | ~0.1 mA | 示波器成本 |

uCurrent 原理：将电流转换为电压 (1mV/uA 档位)，示波器观察电压波形间接得电流。

## 7. 寿命估算中的常见错误

### 7.1 忽略峰值电流对电池的影响

**错误认知**：CR2032 标称 225mAh，只要平均电流算对就行。

**正确理解**：CR2032 内阻约 20-40 欧姆，120mA 脉冲时：

```
电压跌落 = 120mA * 30 = 3.6V  -> MCU 可能复位!
CR2032 只能提供约 15mA 脉冲电流
```

解决方案：并联 100uF 钽电容提供脉冲电流，或换锂亚电池 (ER14250, 内阻约 5 欧姆)。

### 7.2 忘记 LDO 的静态电流

**错误认知**：LDO 睡眠时几乎不耗电。

**正确理解**：LDO 静态电流 (Iq) 一直存在：

| LDO 型号 | 静态电流 |
|----------|---------|
| HT7333 | 4 uA |
| ME6211 | 3.5 uA |
| TLV73333 | 35 uA |
| TPS7A02 | 25 nA |

HT7333 的 4uA Iq 是 MCU 睡眠电流 (0.3uA) 的 **13 倍**，系统实际睡眠电流变成 4.3uA。选超低 Iq LDO 或用负载开关断电。

### 7.3 低估 PCB 漏电流

潮湿环境下 PCB 表面漏电流可达 0.1-1 uA，来源：助焊剂残留、表面导电、丝印吸湿。预防：负载开关断开电源轨、加保形涂层、生产后严格清洗。

### 7.4 忽略自放电与误用标称容量

| 电池化学 | 年自放电率 | 10年损失 |
|---------|-----------|---------|
| 锂锰 (CR2032) | ~0.5% | ~5% |
| 锂亚 (ER14250) | ~1% | ~10% |
| 碱性 (AA) | ~3% | ~26% |

标称容量是特定放电条件下的值。截止电压、温度、脉冲特性都会降低可用容量。**建议按 C_eff = C_nom * 0.7 计算留 30% 裕量。**

## 8. 实际案例分析

### 8.1 案例：户外温湿度传感器节点

需求：5分钟上报、LoRaWAN Class A、目标5年、CR2450 (620mAh)。

```
初步计算:
  Q_active = 5*3 + 0.4*12 + 4*5 + 45*50 + 11*100*2 + 3*2 = 4495.8 mA*ms
  I_total  = Q_active/(5/60h) + 0.3 + 3.5(HT7333) = 18.78 uA
  Life     = 527 mAh / (18.78 * 8760/1000) = 0.37 年  -- 远不够!

优化: 换 TPS7A02 (25nA) + 跳过 Rx2 + 降 TX 功率到 10dBm:
  Q_active 降至 0.000666 mAh
  I_total = 0.000666/(5/60h) + 0.3 + 0.025 = 8.32 uA
  Life = 0.83 年  -- 还是不够!

延长到 30 分钟间隔 + 换 ER14250 电池:
  I_total = 1.66 uA
  Life = 1026 / (1.66 * 8760/1000) = 8.05 年  -- 满足!
```

设计结论：CR2450 + 5分钟间隔无法达5年。至少三选一：延长间隔、换锂亚电池、降低发射功耗。

### 8.2 案例：智能门磁传感器

需求：事件驱动 (门开/关) + 每小时心跳、BLE 5.0、nRF52832、CR2032 目标2年。

```
事件驱动: 每天20次, 每次 BLE TX 10mA*2ms = 0.204 mAh/年
心跳:     每小时一次 = 0.122 mAh/年
睡眠:     0.3 uA * 8760h = 2.628 mAh/年
总需求:   (0.204 + 0.122 + 2.628) * 2 = 5.908 mAh
CR2032 有效容量: 192 mAh, 利用率仅 3.1%
```

**BLE + 事件驱动 = 极长电池寿命**，睡眠电流反而是主要消耗。LoRa 的高发射电流 + 定时轮询才是电池寿命的真正挑战。

## 9. 寿命估算检查清单

```
[ ] 1. 睡眠电流: 实测值还是数据手册典型值?
[ ] 2. LDO / DCDC 静态电流: 是否包含在总电流中?
[ ] 3. 电池有效容量: 是否扣除截止电压、自放电、温度影响?
[ ] 4. 峰值电流: 电池能否提供足够脉冲电流?
[ ] 5. PCB 漏电流: 是否在目标温湿度下实测?
[ ] 6. 传感器预热: 是否计入 warmup 时间和电流?
[ ] 7. Rx 窗口: 确认模式是否计入接收窗口功耗?
[ ] 8. 重传: 是否预留重传的额外功耗?
[ ] 9. RTC 电流: 是否包含在睡眠电流中?
[ ] 10. 裕量: 是否留了至少 30% 的设计裕量?
```

## 总结

占空比策略是 IoT 传感器节点长寿命设计的核心杠杆：

1. **平均电流公式是出发点**：`I_avg = I_sleep + I_active * DC`
2. **发射阶段是最大瓶颈**：LoRa 发射占活跃电量 80%+，优化发射收益最大
3. **LDO 静态电流是隐形杀手**：4uA 的 Iq 是 MCU 睡眠电流的 10 倍
4. **电池容量不是标称值**：截止电压、自放电、脉冲特性都会降低有效容量
5. **自适应占空比不是万能药**：只有稳态时间占比足够高时才省电
6. **实测优于计算**：PPK2 实测比数据手册典型值可靠得多
7. **留足裕量**：30% 设计裕量是对现实不确定性的基本尊重

寿命估算的精髓不是得到一个精确数字，而是识别出哪些假设最脆弱、哪些参数对结果最敏感，然后针对性地验证。

## 参考文献

1. R. Piyare, et al., "Ultra Low Power Wake-Up Radios: A Hardware and Networking Survey," IEEE Communications Surveys & Tutorials, vol. 19, no. 4, pp. 2117-2157, 2017.
2. A. Bachir, et al., "MAC Protocols for Wireless Sensor Networks: A Survey," IEEE Communications Surveys & Tutorials, vol. 12, no. 1, pp. 92-115, 2010.
3. Nordic Semiconductor, "nRF52832 Product Specification v1.4," Section 6.2: Power Consumption, 2023.
4. Semtech, "SX1276/77/78/79 Datasheet Rev 7," Section 4.1: Power Consumption Profile, 2022.
5. J. Polastre, et al., "Telos: Enabling Ultra-Low Power Wireless Research," Proc. IPSN, pp. 364-369, 2005.
