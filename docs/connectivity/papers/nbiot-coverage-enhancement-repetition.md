---
schema_version: '1.0'
id: nbiot-coverage-enhancement-repetition
title: NB-IoT覆盖增强重复传输机制分析
layer: 2
content_type: UNKNOWN
difficulty: advanced
reading_time: 22
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# NB-IoT覆盖增强重复传输机制分析
> **难度**：🔴 高级 | **领域**：蜂窝IoT覆盖 | **阅读时间**：约 22 分钟

## 引言

想象你在一个嘈杂的工地上试图跟远处的工友说话。说一遍他听不清,你就再说一遍、两遍、三遍......直到他听懂为止。每多说一遍,他把几次听到的模糊信息拼在一起,就能还原出完整的句子。NB-IoT的覆盖增强机制就是这个原理: 同样的数据重复发送多次,接收端将多次接收到的微弱信号合并,累积足够的能量来正确解码。

本文深入分析NB-IoT的重复传输机制,包括各信道的重复配置、对延迟和吞吐量的影响,以及链路预算计算。

## 1. NB-IoT覆盖目标

### 1.1 MCL目标

NB-IoT的核心设计目标之一是比GPRS提升20dB的覆盖:

```
覆盖对比:
- GPRS:   MCL = 144dB
- LTE:    MCL = 142dB
- NB-IoT: MCL = 164dB  (+20dB vs GPRS)

MCL含义: 发射功率 - 最小可解调接收功率
MCL越大 = 允许更多路径损耗 = 覆盖更远/更深
```

### 1.2 20dB额外覆盖的意义

```
建筑穿透损耗参考:
- 普通住宅墙壁: 10-15dB
- 地下室: 20-30dB
- 深层地下(停车场B3): 30-40dB

20dB额外MCL可以补偿:
- 1-2层额外墙壁穿透
- 地下1层到地上覆盖的差距
```

### 1.3 覆盖增强的代价

额外覆盖通过时间换取可靠性: 更多重复意味着更长传输时间(更高延迟)、设备更多TX时间(更多功耗)、占用更多空口资源(系统容量下降)。

## 2. 重复传输基本原理

### 2.1 信号合并增益

```
单次传输:  接收SNR = -5dB (无法解码)
重复2次:   合并后SNR = -5dB + 3dB = -2dB
重复4次:   合并后SNR = -5dB + 6dB = +1dB
重复8次:   合并后SNR = -5dB + 9dB = +4dB (可解码!)

规律: 重复次数翻倍, SNR增益约+3dB
(假设各次传输独立, 噪声不相关)
```

### 2.2 Chase Combining原理

```
第1次接收: r1 = s + n1  (信号+噪声)
第2次接收: r2 = s + n2  (相同信号+不同噪声)
...
第N次接收: rN = s + nN

合并: R = r1+r2+...+rN = N*s + (n1+n2+...+nN)
信号增益: N倍 = 20*log10(N) dB
噪声功率增益: N倍 -> 幅度sqrt(N)倍
净SNR增益: 10*log10(N) dB
```

### 2.3 实际增益vs理论增益

| 重复次数 | 理论增益(dB) | 实际增益(dB) | 差异原因 |
|---------|-------------|-------------|---------|
| 2 | 3.0 | 2.5-2.8 | 信道估计误差 |
| 4 | 6.0 | 5.0-5.5 | 信道变化 |
| 16 | 12.0 | 10-11 | 频偏积累 |
| 64 | 18.0 | 15-16 | 时钟漂移 |
| 128 | 21.0 | 17-19 | 多种非理想因素 |

## 3. 覆盖等级(CE Level)

### 3.1 三级覆盖定义

```
CE Level 0 (正常覆盖):
- MCL: <144dB, RSRP: >-100dBm
- 重复: 0-1次
- 场景: 室外, 窗边

CE Level 1 (扩展覆盖):
- MCL: 144-154dB, RSRP: -100 to -110dBm
- 重复: 最多32次
- 场景: 室内深处, 地下1层

CE Level 2 (极端覆盖):
- MCL: 154-164dB, RSRP: <-110dBm
- 重复: 最多128/2048次
- 场景: 地下车库, 管道井, 偏远农村
```

### 3.2 CE Level选择机制

设备基于测量的RSRP自主选择覆盖等级:

```
1. 设备测量服务小区RSRP
2. 对比网络广播的CE Level门限值(通过SIB2-NB)
3. 选择对应CE Level
4. 使用该Level的随机接入资源和重复配置

示例门限:
- RSRP > -100dBm -> CE Level 0
- -110 < RSRP < -100dBm -> CE Level 1
- RSRP < -110dBm -> CE Level 2
```

## 4. 各信道重复配置

### 4.1 NPRACH(随机接入信道)

```
NPRACH重复选项: 1, 2, 4, 8, 16, 32, 64, 128
基站通过SIB2-NB为每个CE Level配置

配置示例:
- CE Level 0: 重复=1, 时间=5.6ms
- CE Level 1: 重复=8, 时间=44.8ms
- CE Level 2: 重复=128, 时间=716.8ms
```

### 4.2 NPUSCH(上行数据信道)

```
NPUSCH重复配置:
- 单音模式: 最多128次重复
- 多音模式: 最多32次重复
- 重复选项: 1, 2, 4, 8, 16, 32, 64, 128

示例(TBS=256bits, 单音15kHz):
- 1个RU = 8ms, 需要10个RU = 80ms
- CE Level 2(128次重复): 80ms*128 = 10.24秒
- 仅发送32字节数据就需要10秒!
```

### 4.3 NPDSCH(下行数据信道)

```
NPDSCH重复选项:
1, 2, 4, 8, 16, 32, 64, 128, 192,
256, 384, 512, 768, 1024, 1536, 2048

单次子帧: 1ms
2048次重复: 2048ms = 2.048秒 (传输1个TB, 最大317字节)
```

### 4.4 NPDCCH(下行控制信道)

```
NPDCCH最大重复: 2048次
重要性: 设备必须先解码NPDCCH获取调度信息
然后才能接收/发送数据
NPDCCH重复次数决定了最低延迟下限
```

## 5. 延迟影响分析

### 5.1 各CE Level典型延迟

```
上行数据传输总延迟:

CE Level 0:
- NPRACH + RAR + Msg3 + CR + Data
- 总计: 约0.1-0.5秒

CE Level 1:
- NPRACH(8次) + RAR(含NPDCCH) + Msg3(8次) + CR + Data(16次)
- 总计: 约3-10秒

CE Level 2:
- NPRACH(128次) + RAR + Msg3(128次) + CR + Data(128次)
- 总计: 约30秒 - 数分钟
```

### 5.2 延迟可视化

```
延迟(对数刻度)
100s |                              ****  CE Level 2
     |                         ****
 10s |                    ****
     |               ****          ****  CE Level 1
  1s |          ****          ****
     |     ****          ****
0.1s | ****          ****               CE Level 0
     +---+---+---+---+---+---+---> 传输阶段
         NPRACH RAR  Msg3  CR  Data
```

## 6. 吞吐量影响

### 6.1 有效数据速率

```
峰值速率(无重复, CE Level 0):
- 下行: 26kbps(Cat-NB1), 上行: 62kbps(多音)

CE Level 1 (16次重复):
- 有效下行: 26000/16 = 1625 bps
- 有效上行: 62000/16 = 3875 bps

CE Level 2 (128次重复):
- 有效下行: 26000/128 = 约203 bps
- 有效上行: 单音约156 bps
```

### 6.2 数据量限制

```
地下水表(CE Level 2), 每次上报50字节:
- 50字节 = 400bits, TBS选择504bits
- 单音8个RU = 64ms, 128次重复: 8.192秒
- 加上随机接入和控制: 总计约30-60秒
- 固件升级(100KB)在CE Level 2下需要数小时
```

## 7. 功耗影响

### 7.1 重复传输的能量成本

```
上行50字节的能量消耗:

CE Level 0 (无重复):
- TX时间: 64ms, 电流220mA
- 能量: 14.08 mAs

CE Level 1 (16次重复):
- TX时间: 1024ms
- 能量: 225.28 mAs (16倍)

CE Level 2 (128次重复):
- TX时间: 8192ms
- 能量: 1802.24 mAs (128倍!)
```

### 7.2 覆盖vs电池寿命

```
每天上报一次, AA电池3000mAh:

CE Level 0: 每次约20mAs
- 电池受自放电限制(约10年到期)

CE Level 1: 每次约350mAs
- 仍然可以10年

CE Level 2: 每次约2500mAs
- 理论12年, 实际约5-7年

结论: 低频上报(每天)在CE Level 2仍可多年寿命
     高频上报(每小时)在CE Level 2下寿命急剧缩短
```

## 8. 链路预算计算

### 8.1 完整链路预算

```
NB-IoT上行链路预算(CE Level 2, 164dB MCL):

发射端:
  设备TX功率:          +23 dBm
  设备天线增益:         +0 dBi
  EIRP:                +23 dBm

接收端:
  基站天线增益:         +18 dBi
  热噪声密度:          -174 dBm/Hz
  带宽(15kHz):         +41.8 dB
  噪声系数:            +3 dB
  接收灵敏度:          -129.2 dBm
  所需SNR(128次重复后): -12.6 dB
  所需接收功率:         -141.8 dBm

最大路径损耗 = 23 + 18 -(-141.8) = 182.8 dB
MCL = 182.8 - 18 = 164.8 dB (满足164dB目标)
```

### 8.2 覆盖距离估算

```
路径损耗模型(城区, 900MHz):
PL(dB) = 120.9 + 37.6*log10(d_km)

最大路径损耗164.8dB:
d = 10^((164.8-120.9)/37.6) = 14.7km (无穿透)

加上建筑穿透:
- 住宅15dB: d = 5.3km
- 地下室25dB: d = 1.9km
- 深地下35dB: d = 0.66km
```

## 9. 网络配置与动态调整

### 9.1 基站配置示例

```
SIB2-NB中NPRACH配置:
CE Level 0: numRepetitions=n1, periodicity=ms320
CE Level 1: numRepetitions=n8, periodicity=ms640
CE Level 2: numRepetitions=n128, periodicity=ms2560
```

### 9.2 动态CE Level变化

```
物流跟踪设备场景:
09:00 室外(RSRP=-85dBm) -> CE Level 0, 快速传输
09:30 进入仓库(-105dBm) -> CE Level 1, 较慢
10:00 仓库深处(-120dBm) -> CE Level 2, 很慢
10:30 回到入口(-95dBm)  -> CE Level 0, 恢复
设备自动适应, 无需人工干预
```

## 10. 实际部署案例

### 10.1 智能抄表(地下室)

```
- 穿透损耗: 约25dB, 距基站500m
- 实测RSRP: -118dBm, CE Level 2
- 每天上报20字节, 延迟约45秒
- 每次功耗约1800mAs, 电池寿命约8年
```

### 10.2 地下停车传感器

```
- B2停车场, 穿透约35dB, 距基站200m
- RSRP: -125dBm, CE Level 2(接近极限)
- 每天约10次状态变化, 延迟约60秒
- 电池寿命约1.5年
- 优化: 加装小型外置天线(+3-5dB)
```

### 10.3 农村偏远地区

```
- 室外水塘监测, 距基站15km
- RSRP: -128dBm, CE Level 2
- 传输成功率约85%(极端边缘)
- 建议增加应用层重传机制
```

## 总结

NB-IoT的重复传输机制是实现164dB MCL覆盖目标的核心手段。通过将相同数据重复发送最多2048次,接收端累积合并能量,可以在极低SNR条件下正确解码。这使得NB-IoT能够覆盖地下室、管道井等传统蜂窝网络难以触及的场景。

覆盖增强的代价明显: CE Level 2下延迟可达数十秒至数分钟,有效数据速率降至百bps级,功耗成倍增加。部署时需评估覆盖需求、延迟容忍度和电池寿命的权衡。

## 参考文献

1. 3GPP TR 45.820, "Cellular System Support for Ultra-Low Complexity and Low Throughput IoT", 2015
2. 3GPP TS 36.213 v14.0.0, "Physical layer procedures", 2017
3. Ratasuk, R. et al., "NB-IoT system for M2M communication", IEEE WCNC, 2016
4. Mangalvedhe, N. et al., "NB-IoT Deployment Study for Low Power Wide Area Cellular IoT", IEEE PIMRC, 2016
5. Xu, T. et al., "Coverage Enhancement Techniques for NB-IoT", IEEE Access, 2018
