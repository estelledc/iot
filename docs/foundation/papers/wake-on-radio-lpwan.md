---
schema_version: '1.0'
id: wake-on-radio-lpwan
title: 无线唤醒Wake-on-Radio在LPWAN中的实现
layer: 1
content_type: UNKNOWN
difficulty: advanced
reading_time: 22
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 无线唤醒Wake-on-Radio在LPWAN中的实现

> **难度**：🔴 高级 | **领域**：低功耗无线通信 | **阅读时间**：约 22 分钟

## 引言

想象你是一个夜班保安，有两种工作方式。第一种是整夜盯着监控屏幕不眨眼（always-on 接收机），虽然不会错过任何事件，但你会精疲力竭，很快撑不住。第二种是定个闹钟，每隔 5 分钟醒来扫一眼屏幕（duty-cycled 监听），省力很多，但如果事件刚好发生在你睡觉的那 5 分钟里，你就会错过。有没有第三种方案？有——给监控屏幕装一个动作感应器，平时你安心睡觉，只有屏幕检测到画面变化时才响铃叫醒你。这个动作感应器就是 Wake-on-Radio (WoR)：一个几乎不耗电的监听机制，只在空中真的有给你的信号时才唤醒主接收机。

LPWAN (Low-Power Wide-Area Network) 设备靠电池运行数年，传统 always-on 接收机的电流在毫安级，几天就能耗尽电池。WoR 通过让射频前端绝大部分时间处于极低功耗状态，仅在检测到有效唤醒信号时才激活主收发器，从根本上解决了"随时可达"与"超低功耗"之间的矛盾。本文将深入分析 WoR 的核心机制、主流实现方案、以及从 preamble sampling 到专用 WuRx 的完整技术谱系。

## 1. 问题根源：Always-On 接收机为什么不可持续

### 1.1 接收机功耗的构成

典型 Sub-GHz 超外差接收机的功耗分布：

| 模块 | 功能 | 典型电流 | 占比 |
|------|------|---------|------|
| LNA | 低噪声放大 | 2-5 mA | 15% |
| Mixer | 下变频 | 1-3 mA | 10% |
| PLL/Synthesizer | 频率合成 | 3-8 mA | 30% |
| ADC + DSP | 数字解调 | 2-5 mA | 20% |
| 协议栈 MCU | MAC 层处理 | 3-10 mA | 25% |
| **总计** | | **11-31 mA** | 100% |

一个 CR2032 纽扣电池容量约 225 mAh。以 15 mA 持续接收计算：

```
电池寿命 = 225 mAh / 15 mA = 15 小时
```

15 小时 vs 5 年目标，差距超过 3000 倍。这就是 always-on 接收机在 LPWAN 中不可行的根本原因。

### 1.2 能量预算分析

假设一个 LPWAN 节点每天发送 1 次数据包，每次发射耗时 100 ms，发射电流 45 mA：

```
发射能量/天 = 45 mA x 0.1 s = 4.5 mAs = 1.25 uAh
5 年总发射能量 = 1.25 uAh x 365 x 5 = 2.28 mAh

接收能量/天 (always-on) = 15 mA x 86400 s = 1296 As = 360 mAh/天
5 年总接收能量 = 360 mAh x 365 x 5 = 657,000 mAh
```

接收能耗是发射能耗的近 30 万倍。问题的核心不是"怎么省发射功耗"，而是"怎么省接收功耗"。

## 2. Duty-Cycled 监听：最朴素的省电方案

### 2.1 Low Duty Cycle (LDC) 原理

LDC 的核心思想是让接收机周期性地开启和关闭，用极低的占空比换取平均功耗的下降：

```
平均电流 = I_rx x duty_cycle + I_sleep x (1 - duty_cycle)

如果 duty_cycle = 1% (每 10 秒监听 100 ms):
平均电流 = 15 mA x 0.01 + 2 uA x 0.99 = 0.152 mA
5 年电池 = 225 mAh / 0.152 mA = 1480 小时 = 61 天
```

1% 的占空比仍然不够。要把 5 年寿命做到，需要：

```
225 mAh / (5 x 365 x 24 h) = 5.14 uA 平均电流
5.14 uA = 15 mA x duty_cycle + 2 uA x (1 - duty_cycle)
duty_cycle = 0.00021 = 0.021%
```

即每 500 秒只能监听约 100 ms，这意味着平均延迟高达 250 秒。

### 2.2 LDC 的时序图

```
时间轴 (s)  0    1    2    3    4    5    6    7    8    9   10
            |    |    |    |    |    |    |    |    |    |    |
接收机      [SLP][SLP][SLP][SLP][SLP][SLP][SLP][SLP][SLP][SLP][RX]
            |<-------------- 睡眠 9.9 s ------------->|<-0.1s->|

发送方      [PREAMBLE......(持续发送，等待接收方醒来).............][DATA]
            |<----------------- 长前导 ------------------------->|

SLP = 睡眠  RX = 接收窗口
```

问题很明显：发送方必须用极长的前导码 (preamble) 覆盖接收方的整个睡眠周期，这极大地浪费了发送方能量和信道占用时间。

### 2.3 LDC 的致命缺陷

| 缺陷 | 说明 |
|------|------|
| 发送方功耗高 | 前导长度 = 接收方睡眠周期，发送方需持续发射数百毫秒到数秒 |
| 信道占用 | 长前导占用信道，影响其他节点通信 |
| 延迟不确定 | 发送方必须等到接收方恰好醒来才能传输数据 |
| 时钟漂移 | 晶振偏差导致窗口偏移，需加大监听窗口补偿，进一步增加功耗 |

## 3. Preamble Sampling：从盲目监听到事件驱动

### 3.1 核心思想

Preamble Sampling (也叫 framed preamble 或 channel sampling) 翻转了 LDC 的逻辑：不再是"接收方周期性醒来等发送方"，而是"接收方极短间隔地采样信道，检测是否有前导信号"。

```
接收方采样模式:
时间  0  50ms  100ms  150ms  200ms  250ms  300ms  350ms  400ms
      |    |     |      |      |      |      |      |      |
采样  [S]       [S]           [S]           [S]           [S]
      |<-2ms->|  (每次采样仅需 2 ms)

S = 信道能量采样 (RSSI 检测)
```

每次采样仅需 1-2 ms，采样间隔 50-100 ms。采样电流仍为 15 mA，但因为每次仅持续 2 ms：

```
平均电流 = 15 mA x (2 ms / 100 ms) + 2 uA x (98 ms / 100 ms)
         = 0.3 mA + 1.96 uA
         = 0.302 mA
```

仍然较高，因为采样时 PLL 启动和 RSSI 检测都需要完整接收机工作。

### 3.2 快速 PLL 启动：降低采样开销的关键

传统 PLL 锁定需要 200-500 us，这是采样窗口无法进一步缩短的主要瓶颈。现代 Sub-GHz 芯片采用了多种快速启动技术：

| 技术 | 原理 | 锁定时间 | 代表芯片 |
|------|------|---------|---------|
| 直接加载频率字 | 启动前预先计算 PLL 配置寄存器 | 50-80 us | CC1310 |
| 保留 PLL 偏置 | 睡眠时维持 VCO 偏置电流 | 20-40 us | SX1261 |
| 环形振荡器粗调 | 先用粗调快速逼近，再精调 | 40-60 us | nRF52840 (2.4G) |

CC1310 的 RFC (Radio Core) 可以在 50 us 内从 IDLE 进入 RX，单次采样能耗降到约 0.75 uJ。

### 3.3 Preamble Sampling 的时序协议

```
发送方:
[PREAMBLE: 重复唤醒信号] [SYNC WORD] [HEADER] [PAYLOAD] [CRC]
|<------- 可变长度 ----->|<---------- 固定长度 ------------->|

接收方:
[S][S][S]...[S] -- 检测到能量 --> [连续RX] [解码SYNC] [接收数据]
                                      |
                               确认是有效信号，保持接收
                               如果是噪声，立即回到采样

S = 短采样 (2 ms), 连续RX = 完整接收机激活
```

关键优化：采样不是解码，只检测信道能量 (RSSI)。只有检测到高于噪声底的能量时，才激活完整接收机去解码 SYNC word，确认是否为有效信号。这种两级检测大幅减少了无效唤醒。

## 4. 长前导 vs 短前导重复唤醒信号

### 4.1 传统长前导方案

传统方案发送一个与接收方采样间隔匹配的长前导。如果接收方每 100 ms 采样一次，前导至少需要 100 ms + 采样窗口宽度：

```
长前导方案时序:

发送方:  [PREAMBLE (>=102ms) ][SYNC][DATA]
                        ^
                        |
接收方:        [S]      |     [S]  检测到能量 -> [连续RX][SYNC][DATA]
               100ms前   |    100ms后
                         |
              这个采样点恰好在两次采样之间
              需要前导覆盖至少一个完整采样间隔
```

长前导的问题：

- 前导越长，发送方能耗越大
- 前导占用信道时间越长，碰撞概率增加
- 对时钟精度要求高，需要留裕量

### 4.2 短前导重复唤醒信号方案

改进方案：不发送一个连续长前导，而是发送一系列短脉冲组成的唤醒信号 (Wake-Up Signal, WUS)。每个短脉冲的长度恰好覆盖一个采样窗口，脉冲之间间隔略小于采样间隔：

```
短前导重复唤醒方案时序:

发送方:  [WUS1]  gap  [WUS2]  gap  [WUS3] [SYNC][DATA]
         |<100ms->|   |<100ms->|
         20ms脉冲    20ms脉冲    20ms脉冲

接收方:       [S]          [S]          [S]
               |            |            |
               v            v            v
           检测到WUS1   检测到WUS2   检测到WUS3
           (可能错过)    (命中)        (确认)
```

对比：

| 指标 | 长前导 | 短前导重复WUS |
|------|--------|-------------|
| 发送方空中时间 | 100+ ms 连续 | 3 x 20 ms = 60 ms |
| 发送方能耗 | 高 (连续发射) | 低 40% |
| 信道占用 | 长时间连续占用 | 短脉冲间可被其他节点使用 |
| 检测可靠性 | 取决于采样是否落在前导内 | 多次机会，更可靠 |
| 实现复杂度 | 低 | 需要精确的 WUS 时序控制 |

### 4.3 WUS 中的地址编码

为了让只有目标节点被唤醒，WUS 中可以嵌入接收方地址。常见的编码方式：

```
WUS 帧结构:
[载波唤醒 (2 ms)] [地址位 (8-16 bits, OOK调制)] [CRC (4 bits)]

地址位编码示例 (8-bit 地址, OOK):
bit 1 = 1: [载波 500us] [静默 500us]
bit 0 = 0: [静默 500us] [载波 500us]

每个 bit 持续 1 ms, 8 bits = 8 ms
总 WUS 长度 = 2 + 8 + 0.5 = 10.5 ms
```

接收方在检测到载波后，继续解码地址位。如果地址不匹配，立即回到睡眠，不激活主接收机。这一步完全由低功耗监听电路完成，主 MCU 始终未唤醒。

## 5. Sub-GHz 芯片中的 WoR 实现

### 5.1 TI CC1310: RAT 触发的 WoR

CC1310 内置一个独立的 Radio CPU (ARM Cortex-M0)，可以在主 MCU 睡眠时自主执行 WoR 协议。核心机制是 RAT (Radio Timer) 触发的周期性信道采样。

```c
// CC1310 WoR 配置 (基于 rfWorrisone 例程)
// 关键参数配置
worParams.worMode = WOR_MODE_SINGLE;   // 单次唤醒模式
worParams.worEventTime = 100000;        // 采样间隔 100 ms (单位: RAT ticks)
worParams.worRxWindow = 2000;           // 采样窗口 2 ms
worParams.rssiThreshold = -90;          // RSSI 阈值 dBm

// Radio CPU 执行流程:
// 1. 主 MCU 进入 Deep Sleep
// 2. RAT 定时器到期 -> 触发 RFC 进入 RX
// 3. RFC 检测 RSSI 是否超过阈值
//    - 超过: 保持 RX, 等待 SYNC word 解码
//    - 未超过: 关闭 RX, 等待下一个 RAT 中断
// 4. SYNC 解码成功 -> 唤醒主 MCU
// 5. 主 MCU 读取数据包, 处理后重新进入 Deep Sleep
```

CC1310 各状态功耗：

| 状态 | 电流 | 持续时间 | 能耗/次 |
|------|------|---------|---------|
| Deep Sleep | 1 uA | 98 ms | 0.098 uAs |
| RX 采样 (含PLL) | 5.9 mA | 2 ms | 11.8 uAs |
| RX 完整接收 | 5.9 mA | 50 ms | 295 uAs |
| **每100ms平均** | | | **~1.2 uA** |

### 5.2 Semtech SX1276: CAD 触发的 WoR

SX1276 (LoRa 调制) 提供了一种独特的信道检测方式：CAD (Channel Activity Detection)。CAD 不需要完整解码前导，而是检测 LoRa 啁啾信号的存在：

```c
// SX1276 CAD 模式配置
void sx1276_cad_config(void) {
    // 设置 CAD 参数
    write_reg(REG_LR_CADCONFIG, 
              CAD_DETECT_ON |       // CAD 开启
              CAD_SYMBOL_NUM_2);    // 检测 2 个符号

    // 进入 CAD 模式
    set_opmode(MODE_CAD);

    // CAD 完成后中断:
    // - CAD_Detected: 信道有 LoRa 信号 -> 切换到 RX 接收
    // - CAD_Done: 信道空闲 -> 回到睡眠
}

// CAD 模式功耗优势:
// CAD 持续时间 = 2 个符号时间 (SF10: ~16 ms)
// CAD 电流 = 10.8 mA
// 但只需检测 2 个符号 vs 完整前导 8+ 符号
// 且只在检测到信号时才进入完整 RX
```

CAD 的时序图：

```
SX1276 WoR 时序:

[RX/CAD]    [SLEEP]  [RX/CAD]   [SLEEP]  [RX/CAD]
[  16ms ]  [  984ms ] [  16ms ] [  984ms ] [  16ms ]
    |                                    |
    v                                    v
 CAD_Done (空闲)                   CAD_Detected (有信号)
    |                                    |
    v                                    v
 回到睡眠                          [连续RX, 接收完整数据包]
                                   [   100-500 ms          ]
```

### 5.3 两种实现的对比

| 特性 | CC1310 (FSK) | SX1276 (LoRa CAD) |
|------|-------------|-------------------|
| 调制方式 | 2-FSK / GFSK | LoRa CSS |
| 检测方式 | RSSI 能量检测 | CAD 符号检测 |
| 采样时间 | 2 ms | 16 ms (SF10) |
| 检测灵敏度 | -90 to -100 dBm | -130 dBm |
| 抗干扰性 | 一般 (能量检测易误触发) | 强 (符号级检测) |
| 平均待机电流 | ~1.2 uA | ~0.2 uA (采样间隔更长) |
| 适用场景 | 近距离高频唤醒 | 远距离低频唤醒 |

## 6. LoRaWAN Class B: 信标同步唤醒

### 6.1 Class B 的设计目标

LoRaWAN 默认的 Class A 是纯上行触发 (uplink-only receive window)，下行延迟不可控。Class B 通过信标 (beacon) 同步，让节点在固定时隙打开额外的接收窗口 (ping slot)，实现可预测的下行可达性。

### 6.2 信标时序结构

```
Beacon 周期 (128 秒):

|<----------- 128 s ------------>|
[BEACON]  [PS][PS]...[PS]        [BEACON]
| 2.4s  | |  |  |   |  |         |
         |<-- ping slots ------->|

BEACON = 网关广播的信标帧
PS = Ping Slot (节点专属接收窗口)

信标帧结构:
[RFU][CRC][Time][Param][GwSpecific]
 2B   2B    4B    7B      variable
```

### 6.3 Ping Slot 的计算

每个节点根据 DevAddr 计算 ping slot 的偏移量，确保不同节点的窗口错开：

```c
// LoRaWAN Class B ping slot 计算 (简化)
uint32_t calc_ping_slot_offset(uint32_t dev_addr, uint16_t slot_idx) {
    // 用 AES-ECB 加密 dev_addr 生成伪随机偏移
    uint8_t key[16] = {0}; // AppKey
    aes_encrypt(key, (uint8_t*)&dev_addr, enc_buf);
    
    // 取加密结果的一部分作为偏移量
    uint16_t rand_val = (enc_buf[0] << 8) | enc_buf[1];
    uint32_t ping_period = 128000 / ping_nb;  // ms
    uint32_t offset = (rand_val % ping_period);
    
    return BEACON_TIME + offset;
}

// Ping slot 数量与功耗关系:
// ping_nb = 1:  每 128s 开 1 个窗口, 额外功耗 ~0.14 uA
// ping_nb = 2:  每 128s 开 2 个窗口, 额外功耗 ~0.28 uA
// ping_nb = 8:  每 128s 开 8 个窗口, 额外功耗 ~1.12 uA
// ping_nb = 64: 每 128s 开 64 个窗口, 额外功耗 ~8.96 uA
```

### 6.4 Class B 的局限

| 局限 | 说明 |
|------|------|
| 信标依赖 | 节点必须持续接收信标，错过信标则失同步 |
| 网关负担 | 网关必须在所有子信道上广播信标 |
| GPS 约束 | 信标时间基准来自 GPS，网关需 GPS 锁定 |
| 覆盖限制 | 信标用固定 SF 和功率，边缘节点可能收不到 |
| ping 粒度粗 | 最小粒度 128s / 4096 = 30 ms，不支持 ms 级唤醒 |

## 7. IEEE 802.15.4g WoR 机制

### 7.1 标准 MR-FSK 的 WoR

IEEE 802.15.4g 定义了多速率 FSK (MR-FSK) 物理层，其中包含对 Wake-Up Receiver 的支持。关键特性：

- 支持 50 kbps 到 300 kbps 多档速率
- 定义了专用的 Wake-Up Packet (WUP) 格式
- WUP 使用更低速率的调制 (如 12.5 kbps) 以提高检测灵敏度

WUP 帧结构：

```
WUP (Wake-Up Packet):
[前导 (32-64 bytes)] [SFD] [WUS Type] [Addr] [CRC]
                     2 bytes  1 byte   var    2 bytes

WUS Type:
0x01 = 广播唤醒 (所有节点)
0x02 = 单播唤醒 (指定地址)
0x03 = 组播唤醒 (组地址)

Addr:
广播: 无
单播: 64-bit IEEE 地址 或 16-bit 短地址
组播: 16-bit 组 ID
```

### 7.2 与 Wi-SUN 的关系

Wi-SUN 基于 802.15.4g，其 FAN (Field Area Network) profile 目前主要使用 Class A (非同步) 模式。但 Wi-SUN 的 Enhanced Mode 引入了类似 WoR 的机制：

- 节点使用非信标模式 (beacon-less) 但周期性监听
- 协调器发送 CSMA-CA 前导 + 数据
- 节点检测到前导后保持接收

## 8. 专用 Wake-Up Receiver (WuRx)：终极低功耗方案

### 8.1 WuRx 的架构

与 WoR (用主收发器做低占空比监听) 不同，WuRx 是一个独立的超低功耗射频前端，专门用于检测唤醒信号。主收发器完全关闭，只在 WuRx 检测到有效信号时才通过 GPIO 唤醒。

```
WuRx 系统架构:

                +-----------+
  天线 ---------| RF 开关   |-------> 主收发器 (SX1276/CC1310)
                |           |             |
                |    +------|-------> WuRx (独立芯片)
                |    |      |             |
                +-----------+             v
                                          GPIO 唤醒主 MCU
                                          |
                                          v
                                    +-----------+
                                    | 主 MCU    |
                                    | (STM32L4) |
                                    +-----------+

WuRx 内部:
天线 -> LNA(可选) -> 包络检波 -> 基带放大 -> 地址匹配 -> GPIO 中断
        ~100nA       无源器件     ~200nA     ~100nA      -> 主MCU
```

### 8.2 WuRx 的关键指标

| 指标 | 典型值 | 说明 |
|------|--------|------|
| 待机电流 | 100-500 nA | 不含地址匹配时的电流 |
| 地址匹配电流 | 300-1000 nA | 含地址解码电路 |
| 灵敏度 | -40 to -60 dBm | 远低于主接收机 |
| 数据速率 | 1-100 kbps (OOK) | 调制方式简单 |
| 唤醒延迟 | < 10 ms | 从信号到GPIO中断 |
| 频率 | Sub-GHz / 2.4 GHz | 取决于具体实现 |
| 面积 | 0.5-2 mm2 (IC) | 集成到 SoC 中的额外面积 |

### 8.3 代表性 WuRx 产品与研究

| 产品/研究 | 频段 | 灵敏度 | 电流 | 调制 | 地址能力 |
|----------|------|--------|------|------|---------|
| AS3933 (ams) | 125/134 kHz (LF) | -90 dBm | 2.7 uA | OOK | 16-bit |
| AX5043 (ON Semi) | Sub-GHz | -105 dBm | 600 nA (WuRx mode) | OOK/FSK | 32-bit |
| [Pletcher 2009] (UC Berkeley) | 2.4 GHz | -72 dBm | 52 uW | OOK | 无 |
| [Roberts 2016] (UMich) | 915 MHz | -97 dBm | 22 nW | OOK | 8-bit |
| [Mazloum 2018] (Georgia Tech) | 433 MHz | -83 dBm | 4.5 nW | OOK | 16-bit |

研究级 WuRx 的功耗已降至纳瓦级别，但灵敏度和地址匹配能力仍然有限。

### 8.4 WuRx 的包络检波原理

WuRx 能做到纳瓦级的核心原因：用无源包络检波替代了有源混频+ADC 链路。

```
传统接收机 (超外差):
天线 -> LNA -> 混频器 -> IF滤波 -> ADC -> DSP -> 解码
         有源     有源      有源    有源   有源   有源
       (mA级)  (mA级)   (mA级) (mA级)(mA级)(mA级)

WuRx (包络检波):
天线 -> 阻抗匹配 -> 包络检波 -> 基带放大 -> 比较器 -> 地址匹配
         无源        无源        有源         有源      有源
                   (二极管)    (nW级)      (nW级)   (nW级)
```

包络检波用肖特基二极管或 MOS 管的平方律特性，直接从射频信号中提取幅度包络，无需本振 (LO) 和混频器。代价是灵敏度低（-40 到 -60 dBm vs -130 dBm），但作为"守夜人"只需要检测附近是否有唤醒信号，灵敏度要求远低于主接收机。

## 9. 能量对比：Always-On vs WoR vs WuRx

### 9.1 统一场景假设

- 供电：3V CR2032 (225 mAh)
- 唤醒频率：每小时 1 次 (即每天 24 次下行)
- 数据包长度：50 ms @ 50 kbps
- 采样间隔：100 ms (WoR)
- 主接收机电流：15 mA
- 睡眠电流：2 uA

### 9.2 三种方案的计算

```
方案 A: Always-On
平均电流 = 15 mA
电池寿命 = 225 mAh / 15 mA = 15 小时

方案 B: WoR (preamble sampling, 2ms采样/100ms间隔)
采样电流 = 15 mA x (2ms / 100ms) = 0.3 mA
睡眠电流 = 2 uA x (98ms / 100ms) = 1.96 uA
唤醒接收电流 = 15 mA x 50ms x 24次/天 / 86400s/天 = 0.208 uA等效
WoR 平均电流 = 0.3 mA + 1.96 uA + 0.208 uA = 302 uA
电池寿命 = 225 mAh / 0.302 mA = 745 小时 = 31 天

方案 C: WuRx (专用唤醒接收机)
WuRx 待机电流 = 500 nA = 0.5 uA (持续监听)
主 MCU 睡眠电流 = 2 uA
唤醒接收电流 = 15 mA x 50ms x 24次/天 / 86400s/天 = 0.208 uA等效
WuRx 平均电流 = 0.5 uA + 2 uA + 0.208 uA = 2.71 uA
电池寿命 = 225 mAh / 0.00271 mA = 83,026 小时 = 9.5 年
```

### 9.3 对比总表

| 方案 | 平均电流 | 电池寿命 | 下行延迟 | 实现复杂度 |
|------|---------|---------|---------|-----------|
| Always-On | 15 mA | 15 小时 | 0 ms | 低 |
| WoR (LDC 1%) | 152 uA | 61 天 | ~5 s | 中 |
| WoR (Preamble Sampling) | 302 uA | 31 天 | ~100 ms | 中 |
| WoR (CAD, LoRa) | 0.2 uA + | ~5 年+ | ~1 s | 中高 |
| WuRx (专用) | 2.7 uA | 9.5 年 | < 10 ms | 高 |

注意：WoR preamble sampling 的平均电流看似高于 LDC，但这是因为它每 100ms 就采样一次（延迟低 50 倍）。如果将采样间隔放宽到 LDC 的水平（如 5 秒），WoR 的平均电流会大幅下降。

## 10. 误唤醒处理：False Wake-Up 的来源与对策

### 10.1 误唤醒的来源

| 来源 | 机制 | 频率 |
|------|------|------|
| 同频段干扰 | 其他设备发射的同频信号触发 RSSI 阈值 | 高 (ISM 频段拥挤) |
| 宽带噪声 | 脉冲噪声触发能量检测 | 中 |
| 邻信道泄露 | 强邻信道信号通过滤波器裙边泄露 | 中 |
| 目标地址错误 | 给其他节点的信号被误检测 | 低 (有地址过滤后) |
| 自然现象 | 闪电、ESD 等瞬态电磁脉冲 | 低 |

### 10.2 多级过滤策略

```
级联过滤流程:

信道能量检测 -> SYNC word 匹配 -> 地址过滤 -> CRC 校验 -> 唤醒主MCU
   (RSSI)        (硬件)          (硬件/固件)   (硬件)     (最后一步)
    |              |                |            |
   1-5 us        0.5-2 ms         1-5 ms      1-5 ms
   
   过滤掉:       过滤掉:          过滤掉:      过滤掉:
   大部分噪声    非本协议信号     非本节点信号  畸变帧
   
每一级都避免唤醒主MCU, 仅在最后一级通过时才唤醒。
```

### 10.3 误唤醒的能耗影响

假设误触发率 1 次/分钟，每次误触发导致主接收机额外开启 5 ms：

```
额外电流 = 15 mA x 5 ms x 60 次/小时 / 3600 s/小时 = 1.25 uA
```

对于目标 5 uA 的系统，1.25 uA 的误触发开销占 25%，非常显著。因此降低误触发率是 WoR 系统设计的关键。

常用策略：
1. 提高 RSSI 阈值 (牺牲灵敏度)
2. 要求连续 N 次采样检测到能量才触发 (增加延迟)
3. 使用特定 SYNC word (增加前导长度)
4. 在唤醒信号中嵌入地址 (增加 WUS 长度)

## 11. 延迟-功耗权衡分析

### 11.1 理论下界

WoR 的平均待机电流与最大检测延迟之间存在根本性的权衡。假设采样窗口固定为 T_s，采样间隔为 T_i：

```
平均待机电流 = I_rx x (T_s / T_i) + I_sleep x (1 - T_s / T_i)
最大检测延迟 = T_i (最坏情况下恰好在采样后发送方开始发射)
平均检测延迟 = T_i / 2

因此:
平均待机电流 x 平均检测延迟 = const (对于固定的 T_s 和 I_rx)
```

这是 WoR 的"测不准原理"：要降低延迟，必须缩短采样间隔，但平均功耗会线性增加。

### 11.2 各方案的延迟-功耗曲线

```
平均电流 (uA)
1000 |  A (Always-On)
     |  |
100  |  |
     |  |     B (WoR LDC)
 10  |  |    /  \
     |  |   /    \---------- C (WoR Preamble Sampling)
  1  |  |  /                \--------
     |  | /                          \-------- D (WuRx)
0.1  |  |/                                   \--------
     |__|____________________________________________
     1ms   10ms   100ms    1s      10s     100s
                  最大检测延迟 (s)

A: Always-On, 延迟=0, 电流=15000 uA
B: WoR LDC (1%), 延迟=5s, 电流=152 uA
C: WoR Preamble Sampling, 延迟=100ms, 电流=302 uA
D: WuRx, 延迟<10ms, 电流=0.5-3 uA

WuRx 打破了 WoR 的延迟-功耗权衡,
因为它不需要"采样-睡眠"的循环,
而是持续监听, 电流几乎为零。
```

### 11.3 选择决策树

```
需要下行可达性?
  |
  +-- 否 --> Class A (纯上行), 最省电
  |
  +-- 是 --> 可接受延迟?
             |
             +-- >30s --> Class A (上行后开窗口)
             |
             +-- 1-30s --> LoRaWAN Class B / WoR (LDC)
             |
             +-- <1s --> WoR (Preamble Sampling) 或 WuRx?
                          |
                          +-- 功耗预算 >100uA --> WoR
                          +-- 功耗预算 <10uA --> WuRx
                          +-- 需要远距离唤醒 --> WuRx + PA 方案
```

## 12. 实现建议与踩坑提醒

### 12.1 WoR 实现常见陷阱

| 陷阱 | 正确做法 |
|------|---------|
| 采样间隔设为 2 的幂次 | 应根据延迟需求和电池容量精确计算 |
| RSSI 阈值用默认值 | 应在实际部署环境中测量噪声底后设定 |
| 忽略时钟漂移 | 采样窗口需覆盖晶振偏差，低温下偏差更大 |
| 地址匹配后直接唤醒主 MCU | 应先做 CRC 校验再唤醒，避免误触发 |
| WuRx 灵敏度与主收发器等同 | WuRx 灵敏度低 30-70 dB，发射方需加大功率或缩短距离 |

### 12.2 时钟漂移的补偿

```
假设晶振精度: +/- 20 ppm (工业级)
采样间隔: 1 s
温度范围: -20C 到 +60C

1 小时后的最大时钟偏差:
delta_t = 3600 s x 20 ppm = 72 ms

这意味着采样窗口需要额外增加 72 ms 的裕量:
实际采样窗口 = T_s + 2 x delta_t (双向偏差)
             = 2 ms + 144 ms = 146 ms (!)

显然不能这样补偿。正确做法:
1. 使用 TCXO (温度补偿晶振): 精度 +/- 2 ppm, 偏差仅 7.2 ms
2. 周期性同步: 用信标或接收数据包校准本地时钟
3. 渐进式窗口扩展: 随着距上次同步的时间增加, 逐步加大窗口
```

### 12.3 从零开始的设计清单

1. 确定最大可接受下行延迟
2. 确定电池容量和目标寿命，计算平均电流预算
3. 根据延迟和电流预算选择方案 (LDC / Preamble Sampling / WuRx)
4. 选择芯片 (CC1310 for FSK WoR, SX1276 for LoRa CAD, 外接 WuRx)
5. 在实际环境中测量噪声底，设定 RSSI/CAD 阈值
6. 实现多级误唤醒过滤
7. 测量真实平均电流，与预算对比
8. 做温度循环测试，验证时钟漂移补偿

## 总结

Wake-on-Radio 是 LPWAN 设备实现"随时可达"与"超低功耗"兼得的核心技术。从最朴素的 Low Duty Cycle 监听，到 Preamble Sampling 的两级检测，再到专用 Wake-Up Receiver 的纳瓦级持续监听，技术的演进本质上是在不断降低"守夜成本"——让设备花更少的电来等待可能永远不会到来的信号。

三种方案各有适用场景：

- **WoR (Preamble Sampling)**：最成熟的方案，CC1310/SX1276 等芯片原生支持，适合功耗预算在 10-500 uA、延迟要求 100 ms-1 s 的场景
- **LoRaWAN Class B**：标准化的信标同步方案，适合已有 LoRaWAN 网络的场景，但延迟粒度粗 (秒级)
- **WuRx (专用唤醒接收机)**：最终极的方案，纳瓦级功耗、毫秒级延迟，但灵敏度有限，适合短距离或发射方功率可控的场景

选择时需牢记延迟-功耗权衡的"测不准原理"：在 WoR 框架内，延迟和功耗不可同时优化。只有 WuRx 通过引入独立的超低功耗监听通道，才从根本上打破了这个约束。未来随着 WuRx 灵敏度的提升 (从 -60 dBm 向 -100 dBm 演进) 和集成度提高 (从独立芯片到 SoC 内部 IP)，WuRx 有望成为 LPWAN 设备的标配。

## 参考文献

1. Pletcher N, Gambini S, Rabaey J. "A 52 uW Wake-Up Receiver with -72 dBm Sensitivity Using an Uncertain-IF Architecture." IEEE Journal of Solid-State Circuits, 2009, 44(1): 269-280.
2. Roberts NE, Wentzloff DD. "A 98 nW Wake-Up Radio for Wireless Body Area Networks." IEEE Radio Frequency Integrated Circuits Symposium, 2012: 373-376.
3. Semtech Corporation. "SX1276/77/78/79 Datasheet: 137 MHz to 1020 MHz Low Power Long Range Transceiver." Rev 7, 2020.
4. Texas Instruments. "CC1310 SimpleLink Ultra-Low Power Sub-1 GHz Wireless MCU Datasheet." SWRS181, 2021.
5. LoRa Alliance. "LoRaWAN Specification v1.0.4." Class B Beacon Synchronization, 2020.
