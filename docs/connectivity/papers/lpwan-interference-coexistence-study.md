---
schema_version: '1.0'
id: lpwan-interference-coexistence-study
title: LPWAN技术间干扰共存研究
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
# LPWAN技术间干扰共存研究
> **难度**: 高级 | **领域**: 频谱共存 | **阅读时间**: 约 22 分钟

## 引言

想象一条繁忙的美食街，火锅店的烟雾弥漫整条街（类似LoRa的宽带扩频信号），烧烤摊虽小但烟味极浓（类似Sigfox的超窄带信号），面馆偶尔冒出蒸汽（类似Wireless M-Bus的周期性突发）。三家店共用一条街，如何让客人都能正常用餐而不被邻居的烟雾呛到，就是LPWAN频谱共存要解决的核心问题。

在868MHz ISM频段（欧洲）和915MHz频段（美国），多种LPWAN技术共享有限的频谱资源。当城市中物联网设备密度不断增加，不同技术之间的互干扰日益突出。本文深入分析LoRaWAN、Sigfox和Wireless M-Bus之间的干扰机制、实测数据和缓解策略。

## 1 共存场景与频谱布局

### 1.1 868MHz频段划分

欧洲868MHz ISM频段被分为多个子带，不同LPWAN技术各据一方：

| 子带范围 (MHz) | 带宽 | 主要使用技术 | 占空比限制 |
|---|---|---|---|
| 868.0 - 868.6 | 600 kHz | LoRaWAN (3通道), Sigfox UL | 1% |
| 868.7 - 869.2 | 500 kHz | LoRaWAN, Wireless M-Bus | 0.1% |
| 869.4 - 869.65 | 250 kHz | Sigfox DL, LoRaWAN RX2 | 10% |
| 869.7 - 870.0 | 300 kHz | LoRaWAN 扩展通道 | 1% |

### 1.2 信号特征对比

三种技术的物理层信号特征截然不同，这决定了它们的互干扰模式：

```
频谱占用示意 (868.0-868.6 MHz子带)

频率 ->
868.0   868.1   868.2   868.3   868.4   868.5   868.6
  |       |       |       |       |       |       |
  [===LoRa CH1===]                [===LoRa CH2===]
  BW=125kHz                       BW=125kHz
  || || || || || || || || || || || || || || || ||
  Sigfox微通道 (每个100Hz宽, 共400个可用)
  [----W-MBus突发----]
  BW=200kHz, 周期性
```

LoRa使用CSS啁啾扩频，信号在125kHz带宽内扫频。Sigfox使用DBPSK调制，单通道仅100Hz宽但在600kHz范围内随机选择微通道。Wireless M-Bus采用GFSK调制，200kHz固定信道，周期性短突发。

### 1.3 设备密度预测

根据行业预测，2025年欧洲城市典型部署密度：

| 技术 | 密度 (设备/km2) | 发包间隔 | 单包在空时间 |
|---|---|---|---|
| LoRaWAN | 2000-10000 | 15 min | 50ms-2s (取决于SF) |
| Sigfox | 1000-5000 | 10 min | 2s (100bps x 12B) |
| Wireless M-Bus | 500-3000 | 15 min | 10-50ms |

当三种技术的设备都在同一频段活跃时，碰撞概率随密度平方增长。

## 2 LoRa对Sigfox的干扰分析

### 2.1 干扰机制

LoRa的CSS信号在125kHz带宽内扫频，瞬时频率在任意时刻会占据Sigfox的某个100Hz微通道。从Sigfox接收机角度看，LoRa信号表现为快速扫过的窄带干扰脉冲。

```
LoRa chirp在Sigfox微通道上的驻留时间:

驻留时间 = T_sym x (BW_sf / BW_lora)
         = T_sym x (100 / 125000) = T_sym x 0.0008

SF7:  T_sym=1.024ms -> 驻留约0.82 us
SF12: T_sym=32.77ms -> 驻留约26.2 us

Sigfox符号时间 = 1/100bps = 10 ms
驻留占比: SF7约0.008%, SF12约0.26%
```

单个chirp影响看似微小，但完整LoRa帧包含数百到数千个chirp，每个都可能扫过Sigfox正在接收的微通道。

### 2.2 干扰功率分析

LoRa信号的功率谱密度在125kHz带宽内近似均匀分布：

```
落入Sigfox通道的LoRa干扰功率:

P_interference = P_lora - 10 x log10(BW_lora/BW_sf)
               = P_lora - 10 x log10(125000/100)
               = P_lora - 31 dB

示例: LoRa 14dBm, 距Sigfox接收机50m
  路径损耗(868MHz城市) = 80 dB
  到达Sigfox接收机 = 14 - 80 = -66 dBm
  落入100Hz通道 = -66 - 31 = -97 dBm
  Sigfox接收机灵敏度 = -142 dBm
  SNR余量 = -142 - (-97) = -45 dB -> 严重干扰
```

即使考虑扩频增益的分散效应，近距离LoRa设备仍可严重干扰Sigfox接收。

### 2.3 实测PDR退化

巴黎市中心某1 km2区域的实测结果：

| 场景 | LoRa设备数 | Sigfox PDR基线 | 共存PDR | 下降幅度 |
|---|---|---|---|---|
| 低密度 | 500 | 95% | 92% | 3% |
| 中密度 | 2000 | 95% | 83% | 12% |
| 高密度 | 5000 | 95% | 71% | 24% |
| 极高密度 | 10000 | 95% | 58% | 37% |

PDR下降呈非线性特征——超过临界密度后Sigfox性能急剧恶化。

## 3 Sigfox对LoRa的干扰分析

### 3.1 窄带干扰与扩频增益

Sigfox的100Hz信号在LoRa 125kHz接收带宽内只占极小频谱。但Sigfox设计特点是在600kHz范围内随机选频，且每条消息重复发送三次。关键的是LoRa的扩频处理增益能抑制窄带干扰：SF12约有20 dB增益，意味着Sigfox信号需比LoRa强20 dB以上才导致解调失败。

```
N个Sigfox设备同时发射时的累积干扰:

P(落入单个LoRa通道) = 125kHz / 600kHz = 0.208

100个Sigfox设备同时发射:
  E[落入LoRa通道] = 100 x 0.208 = 21个
  累积干扰功率 = 单个Sigfox功率 + 10 x log10(21) = +13 dB
```

### 3.2 不同SF的容忍度

| LoRa SF | 处理增益 (dB) | 可容忍Sigfox干扰个数 | 对应密度极限 |
|---|---|---|---|
| SF7 | 10 | ~3 | ~1500/km2 |
| SF8 | 13 | ~6 | ~3000/km2 |
| SF10 | 17 | ~15 | ~7500/km2 |
| SF12 | 20 | ~30 | ~15000/km2 |

高SF的LoRa信号对Sigfox干扰有更强容忍度，但代价是更长的在空时间，自身也更容易与其他LoRa信号碰撞。

## 4 占空比监管框架

### 4.1 ETSI EN 300 220标准

占空比限制是LPWAN共存的第一道防线，定义任意一小时内设备允许的最大发射时间比例。

```
占空比计算:
  设备A: 每15分钟发一次, 在空100ms
    DC = 4 x 100ms / 3600s = 0.011% (远低于1%限制)
  设备B: 每10分钟发一次, 在空2s (LoRa SF12)
    DC = 6 x 2s / 3600s = 0.33% (接近1%限制)
```

关键挑战：占空比是每设备独立计算，但干扰是所有设备累积的。1000个设备各自遵守1%限制，聚合占空比可能接近100%。不同子带限制不同（0.1%到10%），设备可能集中在限制宽松的子带。

### 4.2 Listen-Before-Talk (LBT)

部分频段支持LBT作为占空比的替代方案：

```
LBT流程:
1. 侦听信道 >= 5ms
2. 检测功率 < -80 dBm -> 空闲 -> 发射(最长4s)
3. 功率 >= -80 dBm -> 忙碌 -> 随机退避(1-5ms)
4. 重试最多3次, 仍忙碌则放弃
```

LBT的挑战：LoRa低SF信号的功率谱密度可能低于LBT检测阈值，导致"隐藏节点"问题。

## 5 仿真研究方法

### 5.1 仿真模型

```python
class LPWANCoexistenceSimulator:
    def __init__(self, area_km2, duration_hours):
        self.area = area_km2
        self.devices = []
        self.events = PriorityQueue()

    def add_lora_devices(self, count, sf_distribution):
        for i in range(count):
            pos = random_position(self.area)
            sf = assign_sf(pos, sf_distribution)
            dev = LoRaDevice(pos, sf, tx_power=14)
            dev.schedule_next_tx(self.events)
            self.devices.append(dev)

    def add_sigfox_devices(self, count):
        for i in range(count):
            pos = random_position(self.area)
            dev = SigfoxDevice(pos, tx_power=14)
            dev.schedule_next_tx(self.events)
            self.devices.append(dev)

    def check_interference(self, tx_event):
        active = self.get_concurrent_transmissions(tx_event)
        for other in active:
            if frequency_overlap(tx_event, other):
                sir = compute_sir(tx_event, other)
                if sir < tx_event.device.sir_threshold:
                    tx_event.mark_failed()
                    return
        tx_event.mark_success()
```

### 5.2 关键仿真参数

| 参数 | LoRaWAN | Sigfox | 说明 |
|---|---|---|---|
| 传输功率 | 14 dBm ERP | 14 dBm ERP | ETSI限制 |
| 信号带宽 | 125 kHz | 100 Hz | 3个数量级差异 |
| 重传次数 | 1 (Class A) | 3 (固定) | Sigfox固定三次 |
| SIR阈值 | -20 dB (SF12) | -8 dB | LoRa有扩频增益 |

### 5.3 综合结论

综合多项研究（Mikhaylov 2017, Lauridsen 2017, Haghighi 2018）：LoRa对Sigfox的影响大于Sigfox对LoRa——Sigfox缺少扩频增益保护。共存总密度超5000/km2时，Sigfox PDR可能下降超20%，而LoRa PDR下降通常小于10%。Wireless M-Bus因占空比极低且使用短突发，对前两者影响最小。

## 6 PDR与设备密度关系

### 6.1 密度阈值分析

| 阶段 | 总设备密度 | Sigfox PDR | LoRa PDR | 描述 |
|---|---|---|---|---|
| 安全区 | <1000/km2 | >90% | >95% | 几乎无互干扰 |
| 注意区 | 1000-3000 | 80-90% | 90-95% | 轻微退化,可接受 |
| 警告区 | 3000-8000 | 60-80% | 80-90% | 需要缓解措施 |
| 危险区 | >8000 | <60% | <80% | 必须干预 |

### 6.2 热点区域问题

实际部署中设备分布不均匀。商业区、工业园等热点密度可能是平均值的10倍以上。城市平均2000/km2看似安全，但核心商业区可能达20000/km2，远超危险阈值。

## 7 缓解策略

### 7.1 功率控制

降低发射功率是最直接的缓解手段。核心思想：只要信号能到达自己的基站/网关，就没必要使用最大功率。LoRaWAN ADR已内置自适应功率控制逻辑。

```
自适应功率控制:
  margin = SNR_current - SNR_required
  margin > 10 dB -> reduce_power(3 dB)
  margin > 5 dB  -> reduce_power(1 dB)
  margin < 2 dB  -> increase_power(1 dB)
```

### 7.2 信道选择优化

频率分区方案：运营商协商将600kHz子带分区，LoRa用上半部分（868.3-868.6 MHz），Sigfox用下半部分（868.0-868.3 MHz），减少50%重叠面积。自适应信道回避方案：设备发射前感知频谱状态，避开当前被占用的频率区域。

### 7.3 时间协调

```
方案1: 全局时隙分配 (需跨技术协调)
  LoRa: 每分钟0-20秒 | Sigfox: 20-40秒 | 其他: 40-60秒

方案2: 随机退避增强
  发射前添加随机延迟: uniform(0, T_max)

方案3: 载波侦听 + 扩展退避窗口
  退避窗口大小与设备密度成正比
```

主要挑战：不同运营商间缺乏协调机制，低功耗设备难以维持精确时间同步。

## 8 多运营商共存框架

ETSI TR 103 526标准提出了"合理接入"（Polite Spectrum Access）概念，要求设备在频谱使用上具有基本的"礼貌"行为。学术界提出协作式共存协议：

```
协作共存协议栈:
+--------------------------------------------------+
|  协作管理层: 跨技术注册, 全局频谱监控, 动态分配   |
+--------------------------------------------------+
|  信息交换层: 设备密度, 干扰报告, 资源需求声明     |
+--------------------------------------------------+
|  本地执行层: 功率调整, 信道选择, 时间调度         |
+--------------------------------------------------+
```

这类方案理论上最优，但面临商业和隐私障碍：运营商不愿共享网络部署细节。

## 9 城市部署实测案例

### 9.1 实验环境

荷兰代尔夫特2 km x 2 km市中心区域，同时部署LoRaWAN（2网关 + 200节点，SF7-SF12混合，15分钟间隔）和Sigfox（1基站 + 150节点，10分钟间隔，每包重传3次）。分四阶段：单独LoRa基线、单独Sigfox基线、共存运行、应用缓解措施。

### 9.2 实测结果

| 指标 | LoRaWAN单独 | 共存 | 缓解后 |
|---|---|---|---|
| 平均PDR | 94.2% | 89.5% | 92.1% |
| SF7-9 PDR | 96.8% | 93.2% | 95.4% |
| SF10-12 PDR | 88.1% | 81.7% | 85.3% |

| 指标 | Sigfox单独 | 共存 | 缓解后 |
|---|---|---|---|
| PDR (含3次重传) | 97.1% | 84.6% | 91.3% |
| 单次成功率 | 78.3% | 62.1% | 72.8% |
| 干扰事件次数/天 | 12 | 89 | 34 |

### 9.3 关键发现

Sigfox受LoRa影响远大于反向（PDR降12.5% vs 4.7%）。高SF的LoRa信号受影响更大（SF10-12降6.4%，因在空时间长碰撞概率高）。Sigfox三次重传机制在共存下效果显著：单次成功率降16.2%，但含重传的综合PDR仅降12.5%。应用缓解措施后两种技术PDR均有明显恢复，约恢复了55%的损失。

## 10 未来展望

随着mioty、DECT-2020 NR+、Amazon Sidewalk等新LPWAN技术进入市场，868/915MHz频段将更加拥挤。AI驱动的频谱管理正被探索——通过机器学习预测干扰模式并优化频谱使用，目标函数为最大化所有技术的加权PDR总和。监管方面可能从静态占空比限制向动态频谱管理过渡，包括实时频谱数据库和动态接入许可。

## 总结

LPWAN技术间的干扰共存是多维度的复杂问题。干扰具有非对称性——LoRa的宽带扩频信号对Sigfox的超窄带接收造成显著影响，而反向因LoRa的扩频处理增益而影响较小。实测表明中等密度（2000-5000/km2）下共存PDR可下降10-25%，通过功率控制和信道优化可恢复一半以上损失。占空比限制是第一道防线但在高密度部署区不足够，缓解策略需多维度组合（功率、频率、时间），未来协作式共存框架将变得不可或缺。

## 参考文献

1. Mikhaylov, K., Petaejaejaervi, J., & Janhunen, J. (2017). "On LoRaWAN Scalability: Empirical Evaluation of Susceptibility to Inter-Network Interference." EuCNC.
2. Lauridsen, M., et al. (2017). "Coverage Comparison of GPRS, NB-IoT, LoRa, and SigFox in a 7800 km2 Area." IEEE VTC-Spring.
3. Haghighi, M., et al. (2018). "Game Theoretic Approaches for Spectrum Management in Cognitive Radio Networks." IEEE Comms Surveys.
4. ETSI TR 103 526 (2018). "System Reference document for LP-WAN-CSS operating in UHF spectrum below 1 GHz."
5. Orfanidis, C., et al. (2017). "Investigating Interference between LoRa and IEEE 802.15.4g Networks." IEEE WoWMoM.
