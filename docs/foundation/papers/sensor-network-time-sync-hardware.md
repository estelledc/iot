# 传感器网络硬件级时间同步PPS/PTP
> **难度**：高级 | **领域**：精密时间同步 | **阅读时间**：约 22 分钟

## 引言

乐队演奏时，所有乐手必须看同一个指挥的拍子才能合拍。传感器网络也一样：如果10个振动传感器各自记录自己的时间，事后想把数据对齐就像让10个各自看不同手表的人描述同一瞬间发生了什么 -- 毫无意义。时间同步就是让所有传感器共享同一个"指挥的拍子"，硬件级同步(PPS/PTP)能把对齐精度从软件方案的毫秒级推到微秒甚至纳秒级。

## 1 为什么需要精密时间同步

### 1.1 传感器网络中的同步需求

分布式传感器网络中，精密时间同步是以下应用的前提：

- **事件关联**：确定不同传感器检测到的事件的先后顺序
- **TDOA定位**：到达时间差(Time Difference of Arrival)定位，需要纳秒级精度
- **同步采样**：多个传感器在同一时刻采样，保证数据相位一致
- **模态分析**：结构振动分析需要所有通道时间对齐

### 1.2 精度需求对比

| 应用 | 所需同步精度 | 说明 |
|------|-------------|------|
| 数据日志时间戳 | 1-10ms | 知道大概何时采集即可 |
| 事件排序 | 100us-1ms | 区分事件先后 |
| 波束成形 | 1-10us | 信号相干叠加 |
| TDOA定位 | <1us | 光速下1us = 300m误差 |
| 同步采样/模态分析 | <100ns | 采样相位精确对齐 |

## 2 软件时间同步的局限

### 2.1 NTP原理与精度

NTP(Network Time Protocol)是最常见的网络时间同步协议：

```
客户端                        服务器
  |--- T1: 发送请求 --------->|
  |                           |  T2: 收到请求
  |                           |  T3: 发送回复
  |<--- T4: 收到回复 ---------|

往返延迟 = (T4-T1) - (T3-T2)
时钟偏移 = ((T2-T1) + (T3-T4)) / 2
```

### 2.2 NTP的精度瓶颈

NTP在局域网中最好也只能做到1-10ms精度，原因包括：

- **网络抖动**：数据包排队延迟不确定
- **OS调度延迟**：从网卡中断到应用层的时间不确定
- **协议栈延迟**：TCP/IP栈处理时间变化
- **时钟频率漂移**：本地晶振频率偏差(典型20-50ppm)

### 2.3 为什么软件同步不够

```
软件同步误差来源(堆叠):
  网络抖动:       0.1 - 10ms
  + OS调度:       10us - 1ms
  + 协议栈:       1us - 100us
  + 中断延迟:     1us - 50us
  ---------------------------
  总误差:         ~1ms - 10ms
```

对于需要微秒级同步的应用，软件方案的根本问题是时间戳在软件层打，此时已经经过了不确定的延迟。

## 3 PPS：GPS秒脉冲

### 3.1 PPS原理

GPS模块每秒输出一个与UTC秒沿对齐的硬件脉冲：

```
UTC秒沿:  |          |          |          |
PPS脉冲:  _|^^^^^^^^^|__________|^^^^^^^^^|____
          <-- 1us -->           <-- 1us -->
```

- 脉冲上升沿与UTC秒沿的偏差 < 100ns
- 脉冲宽度通常100ms-900ms(可配置)
- 3.3V或5V CMOS电平

### 3.2 PPS时间戳捕获

MCU通过GPIO中断捕获PPS上升沿的精确时刻：

```c
// STM32 PPS捕获(使用定时器输入捕获)
void HAL_TIM_IC_CaptureCallback(TIM_HandleTypeDef *htim) {
    static uint32_t last_pps_tick = 0;

    if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1) {
        uint32_t current_tick = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1);
        uint32_t interval = current_tick - last_pps_tick;

        // 1秒 = timer_clock_hz 个tick
        // 用interval与理论值的偏差来校准本地时钟
        int32_t offset_ticks = interval - timer_clock_hz;
        float offset_us = (float)offset_ticks / timer_clock_hz * 1e6;

        // 校准本地时钟
        adjust_local_clock(offset_us);

        last_pps_tick = current_tick;
    }
}
```

### 3.3 GPS驯服本地振荡器

GPS PPS提供长期稳定的1Hz参考，本地TCXO/OCXO提供短期稳定性。两者结合：

```
GPS PPS ----->[鉴相器]----->[PID滤波器]----->[VCXO控制]
                  ^                                     |
                  |                                     v
               本地振荡器 <-------------------------- 输出时钟
```

GPS驯服时钟(GPSDO)可达到优于1ppb(十亿分之一)的频率稳定度。

### 3.4 PPS的优势与局限

| 优势 | 局限 |
|------|------|
| 精度高(<100ns) | 需要GPS信号(室内不可用) |
| 实现简单(GPIO捕获) | 每个节点需要GPS模块 |
| 全球统一(UTC) | 成本增加 |
| 无需网络 | 仅1Hz参考频率 |

## 4 PTP/IEEE 1588精密时间协议

### 4.1 PTP概述

PTP(Precision Time Protocol)是IEEE 1588定义的精密时间同步协议：

- 在局域网内实现亚微秒级同步
- 核心区别：硬件时间戳(hardware timestamping)
- 主从层次架构：Grandmaster -> Boundary Clock -> Ordinary Clock

### 4.2 PTP消息类型与同步流程

PTP通过4步消息交换计算时钟偏移和路径延迟：

```
主时钟(Master)                    从时钟(Slave)
  |                                 |
  |--- Sync(t1) ------------------>|  t1: 主时钟发送时间
  |                                 |
  |--- Follow_Up(t1精确值) -------->|  (携带t1的精确值)
  |                                 |  t2: 从时钟接收时间
  |<-- Delay_Req ------------------|  t3: 从时钟发送时间
  |                                 |
  |--- Delay_Resp(t4) ------------>|  t4: 主时钟接收时间

计算:
  时钟偏移 offset = ((t2-t1) + (t3-t4)) / 2
  路径延迟 delay  = ((t2-t1) - (t3-t4)) / 2
```

### 4.3 硬件时间戳的关键作用

PTP精度远超NTP的根本原因是时间戳在物理层打：

```
NTP时间戳:  应用层打标 --> 包含协议栈+OS延迟
PTP时间戳:  MAC/PHY层打标 --> 仅包含线缆延迟

|<-- 协议栈延迟(不确定) -->|<-- 硬件延迟(确定) -->|
应用层                  MAC层              PHY层    网线
  |                      |                  |        |
  v                      v                  v        v
NTP时间戳            PTP时间戳(精确)
```

硬件时间戳在帧起始定界符(SFD)通过PHY的时刻捕获，消除所有软件栈延迟。

## 5 硬件时间戳实现

### 5.1 以太网PHY/MAC时间戳

支持PTP的以太网控制器在发送/接收帧时自动记录时间戳：

```c
// PTP时间戳捕获(STM32以太网PTP示例)
typedef struct {
    uint32_t seconds;      // 秒
    uint32_t nanoseconds;  // 纳秒
} ptp_timestamp_t;

// 发送帧时捕获时间戳
void eth_send_with_timestamp(uint8_t *frame, uint16_t len,
                             ptp_timestamp_t *tx_ts) {
    // 启用发送时间戳捕获
    ETH_PTP_TxTimestampConfig(ENABLE);

    // 发送帧
    ETH_WriteFrame(frame, len);

    // 等待时间戳就绪
    while (!ETH_PTP_TxTimestampAvailable());
    ETH_PTP_GetTxTimestamp(tx_ts);
}

// 接收帧时获取时间戳
void eth_receive_handler(uint8_t *frame, uint16_t len,
                         ptp_timestamp_t *rx_ts) {
    // 接收帧时硬件自动打时间戳
    ETH_PTP_GetRxTimestamp(rx_ts);
    // 处理PTP消息...
}
```

### 5.2 精度修正

PTP实现中需要考虑的延迟修正：

- **PHY内部延迟**：从MII/GMII接口到线缆的固定延迟(可从PHY数据手册查到)
- **MAC内部延迟**：从时间戳点到MAC发送FIFO的延迟
- **线缆延迟**：约5ns/米(光速在铜缆中约为2x10^8 m/s)

这些延迟是固定值，可在初始化时从硬件数据手册读取并配置到PTP协议栈中。

## 6 PTP硬件支持

### 6.1 支持PTP的硬件平台

| 平台 | PTP功能 | 说明 |
|------|---------|------|
| STM32H7/F7 | IEEE 1588 MAC | 内置PTP时间戳单元 |
| TI DP83640 | PTP PHY | PHY层时间戳，高精度 |
| Intel i210 | 硬件时间戳 | 服务器/网关卡 |
| LAN7430 | PTP支持 | 工业以太网 |
| KSZ9477 | PTP交换 | 边界时钟功能 |

### 6.2 边界时钟与透明时钟

**边界时钟(Boundary Clock)**：
- 交换机的每个端口维护独立PTP时钟
- 终止一个域的PTP消息，用本地时钟重新生成
- 阻止抖动累积

**透明时钟(Transparent Clock)**：
- 不同步时钟，只测量帧在交换机内的驻留时间
- 将驻留时间写入PTP帧的校正字段
- 主时钟用校正后的值计算偏移

```
普通时钟 --[交换机]-- 普通时钟
            |
     边界时钟: 同步后重新发送
     透明时钟: 只修正驻留时间
```

## 7 无线网络时间同步挑战

无线信道的传播延迟高度可变：CSMA/CA退避时间不确定、重传导致额外延迟、射频前端没有硬件时间戳能力。

IEEE 802.15.4e的TSCH(Time-Slotted Channel Hopping)是无线场景的主要方案：所有节点共享时间槽调度表，每个时间槽约10ms，通道跳频减少干扰，精度通常1-10us。

## 8 实践案例：分布式振动监测

### 8.1 系统需求

- 10个振动传感器节点分布在大型结构上
- 同步采样率1kHz，采样时刻对齐精度 < 1us
- 数据通过以太网传回中心服务器

### 8.2 同步方案

```
GPS天线
   |
   v
GPS模块 ----PPS----> PTP Grandmaster (STM32H7 + DP83640)
                         |
                    以太网PTP交换机(边界时钟)
                    /    |    \     \
               节点1  节点2  节点3 ... 节点10
               (从时钟, 硬件时间戳)
```

### 8.3 节点同步采样实现

```c
// 从时钟节点：同步采样
void sync_sampling_task(void) {
    ptp_timestamp_t current_time;
    ptp_timestamp_t next_sample_time;

    while (1) {
        // 获取当前PTP时间
        ptp_get_time(&current_time);

        // 计算下一个采样时刻(1ms间隔, 对齐到整数毫秒)
        next_sample_time = current_time;
        next_sample_time.nanoseconds = 0;
        next_sample_time.milliseconds += 1;

        // 等待到采样时刻
        while (ptp_compare(ptp_get_time_now(), next_sample_time) < 0) {
            // 短暂等待,避免忙等
            NOP();
        }

        // 精确时刻采样
        adc_trigger_conversion();
        sample_buffer[sample_idx++] = adc_read();

        // 存储带时间戳的采样数据
        store_sample(&sample_buffer[sample_idx-1], &next_sample_time);
    }
}
```

## 9 同步精度对比

| 方法 | 典型精度 | 硬件需求 | 适用场景 |
|------|----------|----------|----------|
| NTP | 1-10ms | 无特殊硬件 | 数据日志 |
| PTP软件时间戳 | 10-100us | 普通网卡 | 低精度同步 |
| PTP硬件时间戳 | <1us | PTP PHY/MAC | 工业测量 |
| GPS PPS | <100ns | GPS模块 | 室外精密同步 |
| 有线触发 | <10ns | 同轴电缆 | 实验室级 |

## 10 实现考量

### 10.1 网络拓扑选择

```
星型拓扑:  所有节点直连Grandmaster
  - 优点: 延迟最小,精度最高
  - 缺点: 需要多口交换机

级联拓扑:  Grandmaster -> BC -> BC -> OC
  - 优点: 扩展性好
  - 缺点: 每级BC引入额外抖动

推荐: 使用边界时钟交换机,级联不超过3级
```

### 10.2 非对称延迟补偿

PTP假设主到从和从到主的路径延迟相同。如果非对称：

- 正向和反向走不同物理路径
- 光纤收发延迟不同

补偿方法：
- 测量已知非对称量并配置修正值
- 使用透明时钟避免累积误差
- 校准线缆长度确保对称

### 10.3 GPS信号丢失时的守时

GPS PPS不可用时的保持策略(holdover)：使用本地振荡器维持时间，守时精度取决于振荡器质量：

| 振荡器类型 | 守时1小时误差 | 成本 |
|-----------|--------------|------|
| 普通晶振(XO) | 3.6ms | $1 |
| 温补晶振(TCXO) | 360us | $5 |
| 恒温晶振(OCXO) | 3.6us | $50 |
| 铷原子钟 | 36ns | $500 |

守时算法需跟踪频率偏差和漂移率，在GPS恢复后重新校准。

## 总结

传感器网络的精密时间同步是分布式测量的基础。NTP的毫秒级精度对于大多数IoT数据记录够用，但需要微秒级或更高精度时必须依赖硬件方案。GPS PPS提供纳秒级精度的绝对时间参考，但需要卫星信号和每节点GPS模块；PTP/IEEE 1588通过硬件时间戳在局域网内实现亚微秒同步，是工业以太网场景的标准方案。关键实现考量包括网络拓扑设计(边界时钟 vs 透明时钟)、非对称延迟补偿、以及GPS信号丢失时的守时策略。

## 参考文献

1. IEEE Std 1588-2019: Precision Clock Synchronization Protocol, IEEE, 2019.
2. Eidson J. Measurement, Control, and Communication Using IEEE 1588. Springer, 2006.
3. STM32 Ethernet PTP Time Stamp Unit Application Note AN3415, STMicroelectronics.
4. TI DP83640 Precision PHYTER IEEE 1588 Datasheet, Texas Instruments.
5. LMIC. TSCH: Time-Slotted Channel Hopping for IoT, IEEE 802.15.4e Standard, 2012.
