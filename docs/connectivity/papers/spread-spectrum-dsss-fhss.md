---
schema_version: '1.0'
id: spread-spectrum-dsss-fhss
title: 扩频技术DSSS与FHSS在IoT抗干扰中的原理
layer: 2
content_type: UNKNOWN
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 扩频技术DSSS与FHSS在IoT抗干扰中的原理
> **难度**: 中级 | **领域**: 扩频通信 | **阅读时间**: 约 20 分钟

## 引言

想象你在嘈杂的火车站,想跟对面的朋友说一句话。如果用正常音量,声音会被周围噪声淹没。但你有两种策略:

策略一(DSSS式): 把同一句话重复喊很多遍,对方把听到的所有片段"叠加"起来,你的声音就会从噪声中浮现——就像拍很多张模糊照片叠加后,清晰目标会越来越突出。

策略二(FHSS式): 你和朋友约定一个"位置表"——先在1号柱子旁说,再跑到3号检票口说,再到7号便利店。噪声来源固定在某些位置,你不断换位置说话,大部分时候都能避开噪声。

这就是扩频通信的两大流派: 直接序列扩频(DSSS)和跳频扩频(FHSS),IoT设备在拥挤ISM频段中可靠通信的核心武器。

## 1. 扩频通信基本概念

### 1.1 为什么要"扩频"

```
窄带通信: 用刚好够的带宽传数据(1kbps -> 1kHz带宽)
  优点: 频谱效率高
  缺点: 窄带干扰可轻易摧毁整个信号

扩频通信: 故意使用比必要更大的带宽(1kbps -> 1MHz带宽)
  优点: 抗干扰强(窄带干扰只影响一小部分)
  缺点: 占用更多频谱

核心: 用"冗余带宽"换取"抗干扰能力"
```

### 1.2 处理增益(Processing Gain)

处理增益量化扩频系统的抗干扰能力:

```
处理增益 Gp = 扩频带宽 / 数据带宽

例: 数据250kHz, 扩频后2MHz -> Gp = 8 (约9dB)
含义: 解扩后信噪比提升Gp倍, 干扰被"稀释"Gp倍

类比: 把一杯墨水(干扰)倒进水池
  小水池(窄带): 水变很黑 -> 信号淹没
  大水池(扩频): 水微微变色 -> 信号仍可辨识
```

### 1.3 扩频简史

1942年Hedy Lamarr获得跳频通信专利(鱼雷防干扰); 1950s军事广泛使用; 1985年FCC开放ISM频段给扩频设备(民用化起点); 1997年WiFi使用DSSS/FHSS; 2003年Zigbee使用DSSS; 2012年LoRa使用CSS。

## 2. 直接序列扩频(DSSS)

### 2.1 工作原理

DSSS用高速"扩频码"(PN序列)调制原始数据:

```
发送过程:
  数据bit 1: 乘以扩频码 [1 0 1 1 0 0 1 0 1 0 1] -> 得[1 0 1 1 0 0 1 0 1 0 1]
  数据bit 0: 乘以扩频码取反                      -> 得[0 1 0 0 1 1 0 1 0 1 0]

  1个数据bit -> 11个chips -> 带宽扩展11倍
  chip率/数据率 = 扩频因子 = 处理增益
```

### 2.2 接收端解扩

```python
def dsss_despread(received_signal, spreading_code):
    """DSSS解扩: 将接收信号与本地扩频码相关"""
    chip_length = len(spreading_code)
    correlation = 0
    for i in range(chip_length):
        code_chip = 1 if spreading_code[i] == 1 else -1
        correlation += received_signal[i] * code_chip
    
    # 期望信号与码匹配 -> 相关值 = +/- chip_length (强)
    # 干扰与码不相关   -> 相关值 约 0 (弱)
    # 信号增强chip_length倍, 干扰不变 -> SNR提升!
    return 1 if correlation > 0 else 0
```

### 2.3 为什么干扰被抑制

```
直觉解释:

发送端: 数据 -> [扩频: 乘11-chip码] -> 宽带信号
空中:   宽带信号 + 窄带干扰(只占1/11带宽)
接收端: [解扩: 乘同一个码]
  对信号: 解扩="收拢" -> 能量集中回窄带
  对干扰: 解扩="扩散" -> 能量被摊到整个带宽
  窄带滤波后: 信号全通过, 干扰只剩1/11

结果: 干扰衰减11倍(10.4dB处理增益)
```

### 2.4 扩频码选择

| 码类型 | 特点 | 应用 |
|--------|------|------|
| Barker码 | 良好自相关,长度<=13 | 802.11b(11-chip) |
| Gold码 | 大量低互相关码 | GPS, CDMA |
| Walsh码 | 完全正交(同步时) | CDMA下行 |
| 802.15.4码 | 32-chip PN序列 | Zigbee |

## 3. 跳频扩频(FHSS)

### 3.1 工作原理

FHSS不改变瞬时带宽,而是在多个频率间快速跳转:

```
频率 ^
 f7  |     [数据]
 f5  |          [数据]
 f3  |                [数据]
 f2  |                      [数据]
 f1  | [数据]
     +-----------------------------> 时间

跳频序列(伪随机): f1, f7, f5, f2, f3, ...
接收端知道同一序列 -> 跟着跳 -> 能接收
干扰者不知道 -> 只能干扰某个频率 -> 只偶尔命中
```

### 3.2 处理增益

```
FHSS处理增益 = 可用跳频信道数 N

蓝牙: 79个1MHz信道 -> Gp = 79 (约19dB)
含义: 窄带干扰固定在某频率, 信号在79频率跳
      只有1/79时间被干扰 -> 等效衰减79倍

注意: FHSS处理增益是"概率性"的
  跳到干扰频率: 该hop可能丢失(需FEC纠错恢复)
  跳到干净频率: 完全正常
```

### 3.3 自适应跳频(AFH)

```python
class AdaptiveFrequencyHopping:
    """蓝牙AFH: 不跳到有干扰的频率"""
    
    def __init__(self, total_channels=79):
        self.channel_map = ['good'] * total_channels
    
    def assess_channel(self, ch_id, error_rate):
        """评估信道质量"""
        if error_rate > 0.3:
            self.channel_map[ch_id] = 'bad'
        elif error_rate < 0.05:
            self.channel_map[ch_id] = 'good'
    
    def get_hop_set(self):
        """只在好的信道跳频(至少保留20个)"""
        good = [i for i, s in enumerate(self.channel_map) if s == 'good']
        return good if len(good) >= 20 else self.reassess()

# 效果: WiFi占68个信道 -> AFH标记为bad -> 只在11个干净信道跳
# 完全避开WiFi干扰!
```

## 4. DSSS在Zigbee中的应用

### 4.1 IEEE 802.15.4 2.4GHz PHY

```
处理流程: 数据 -> 4-bit分组 -> 查表得32-chip序列 -> O-QPSK调制

参数:
- 数据率: 250 kbps, 码片率: 2 Mchip/s
- 每4bit映射到一个32-chip近正交PN序列
- 16种4-bit组合 -> 16个不同32-chip序列
- 处理增益: ~9 dB(带宽比: 2MHz/250kHz=8)
```

### 4.2 Zigbee抗WiFi干扰实例

```python
def calculate_zigbee_processing_gain():
    """Zigbee在WiFi干扰下的抗干扰增益"""
    import math
    
    # 扩频增益: chip_rate / data_rate
    spreading_gain = 10 * math.log10(2e6 / 250e3)  # = 9.0 dB
    
    # 频率选择性: WiFi 20MHz中只有2MHz与Zigbee重叠
    freq_selectivity = 10 * math.log10(20e6 / 2e6)  # = 10.0 dB
    
    total_gain = spreading_gain + freq_selectivity   # = 19.0 dB
    # 含义: 即使WiFi比Zigbee强19dB, Zigbee仍能工作!
    return total_gain
```

### 4.3 实测结果

```
WiFi距离(m) | 无DSSS理论丢包率 | 实际Zigbee丢包率
  2          |   ~95%           |   22%
  5          |   ~50%           |   2%
  8          |   ~20%           |   0.5%

DSSS的10dB增益让"有效干扰距离"缩短约3倍
```

## 5. FHSS在蓝牙中的应用

### 5.1 蓝牙经典FHSS参数

```
跳频带宽: 79 MHz (2402-2480 MHz)
信道数: 79个(各1MHz)
跳频速率: 1600 hops/sec
驻留时间: 625 us(1个时隙)
序列由master蓝牙地址和时钟决定(伪随机)
```

### 5.2 BLE信道策略

BLE使用40个2MHz信道(37数据+3广播),连接后每个事件跳到不同数据信道。跳频间隔=connInterval(7.5ms-4s),比经典蓝牙慢(省电优先),同样支持AFH。

### 5.3 与WiFi共存

```
2.4GHz共存分析:
WiFi CH1/6/11各占22MHz, 蓝牙79个1MHz信道
约68/79=86%的跳落在WiFi区域

AFH前: 丢包率很高(86%概率遇到WiFi)
AFH后: 标记68个重叠信道为bad, 只在11个干净信道跳
        丢包率降到接近0
```

## 6. CSS在LoRa中的应用

### 6.1 啁啾扩频原理

```
LoRa CSS: 频率随时间线性扫描(chirp)
- 数据编码在chirp起始频率(相位偏移)
- SF决定chirp中有多少种起始频率:
  SF7:  128种 -> 每symbol 7 bits
  SF12: 4096种 -> 每symbol 12 bits

SF越高 -> symbol越长 -> 数据率越低 -> 但处理增益越高
```

### 6.2 LoRa处理增益

```
Gp = 10*log10(2^SF / SF) dB

SF7:  12.6 dB     SF10: 20.1 dB
SF8:  15.1 dB     SF11: 22.7 dB
SF9:  17.5 dB     SF12: 25.3 dB

SF12比SF7多13dB -> 覆盖距离约翻倍 -> 代价: 速率降64倍
```

### 6.3 三种扩频方式对比

| 特性 | DSSS | FHSS | CSS(LoRa) |
|------|------|------|-----------|
| 带宽使用 | 持续占全带宽 | 瞬时窄带跳频 | 持续线性扫频 |
| 抗窄带干扰 | 处理增益过滤 | 跳开干扰频率 | chirp扫过(短暂影响) |
| 多址方式 | 不同扩频码 | 不同跳频序列 | 不同SF正交 |
| IoT应用 | Zigbee, WiFi | 蓝牙 | LoRa |
| 覆盖距离 | 短(10-100m) | 短-中(10-100m) | 长(2-15km) |

## 7. 综合抗干扰对比

### 7.1 不同干扰类型下的表现

```
              窄带干扰  宽带干扰  脉冲干扰  多路径
DSSS(Zigbee)  +++      ++       ++       +++
FHSS(蓝牙)    +++      +        +++      ++
CSS(LoRa)     +++      +++      ++       +++

+低 ++中 +++高
```

### 7.2 应用场景匹配

| 场景 | 推荐技术 | 理由 |
|------|----------|------|
| 智能家居(短距多设备) | FHSS(BLE) | 与WiFi共存好 |
| 工业传感网(可靠性) | DSSS(802.15.4) | 抗干扰稳定 |
| 广域低功耗(远距离) | CSS(LoRa) | 高处理增益 |
| 高密度多协议共存 | FHSS+AFH | 自适应避干扰 |

### 7.3 设计权衡

处理增益vs频谱效率(更高增益占更多带宽); 复杂度vs性能(DSSS需精确同步,FHSS需快速频率合成器); 延迟vs可靠性(高SF传输时间长但更可靠)。IoT通常数据率低,可以"挥霍"带宽换可靠性。

## 总结

扩频技术是IoT在拥挤ISM频段可靠通信的关键保障:

- 扩频本质是用带宽换信噪比,获得处理增益抵抗干扰
- DSSS通过码片序列展开信号,解扩时压制非匹配干扰
- FHSS通过快速跳频避开窄带干扰,AFH进一步自适应避开已知干扰源
- CSS(LoRa)通过chirp扫频获得高处理增益,SF越高增益越大
- Zigbee DSSS在同频WiFi干扰下提供约10dB处理增益
- 三种技术各有优势: DSSS稳定可靠,FHSS多协议共存,CSS远距离低功耗

## 参考文献

1. Goldsmith, A. (2005). Wireless Communications. Cambridge University Press. Chapter 13.
2. IEEE 802.15.4-2020. Standard for Low-Rate Wireless Networks.
3. Bluetooth SIG. (2023). Bluetooth Core Specification v5.4.
4. Semtech. (2015). AN1200.22: LoRa Modulation Basics.
5. Rappaport, T. S. (2024). Wireless Communications: Principles and Practice. 3rd Edition.
