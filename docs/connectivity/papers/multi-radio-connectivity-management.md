# 多射频连接管理与无缝切换策略
> **难度**：🔴 高级 | **领域**：连接管理 | **阅读时间**：约 22 分钟

## 引言

想象你出门时带了三部手机: 一部信号特别好但费电, 一部省电但速度慢, 还有一部只有在WiFi环境下才能用但完全免费. 你根据不同场景换用不同手机 -- 在家用WiFi手机, 出门用信号好的, 电量低时切到省电的. IoT设备面临的正是同样的处境: 一台设备可能同时拥有BLE, WiFi, 蜂窝等多种射频模块, 如何在它们之间智能切换, 就是多射频连接管理要解决的核心问题.

现代IoT设备越来越多地集成多种无线通信模块. 一个物流追踪器可能同时具备BLE, WiFi和LTE-M三种射频; 一个工业传感器可能有WiFi和LoRa两种连接方式. 每种射频技术都有自己的优势场景: BLE适合近距离低功耗配置, WiFi适合室内高速传输, 蜂窝网络适合广域覆盖, LoRa适合超远距离低速率场景. 多射频连接管理的目标, 就是让设备根据当前环境和需求, 自动选择最合适的射频通道.

## 1 多射频架构设计

### 1.1 硬件层面

一个多射频IoT设备在硬件上通常包含以下组件:

- 多个射频模块: 例如ESP32同时集成了WiFi和BLE, 或者通过外接模块添加LoRa和LTE-M
- 各模块独立的PHY(物理层)和MAC(媒体访问控制层)
- 共享的主控MCU, 通过SPI, UART或I2C与各射频模块通信
- 天线系统: 可能共享天线(如2.4GHz的WiFi和BLE)或使用独立天线

### 1.2 软件架构

软件层面的架构可以分为四个关键层:

```
+---------------------------+
|      应用层 Application    |  <-- 不关心底层使用哪个射频
+---------------------------+
|   连接管理器 Conn Manager  |  <-- 决策核心: 选哪个射频
+---------------------------+
|    策略引擎 Policy Engine  |  <-- 规则库: 何时用哪个
+---------------------------+
| 射频抽象层 Radio Abstract  |  <-- 统一API封装各射频差异
+---------------------------+
| BLE | WiFi | LoRa | LTE-M |  <-- 物理射频模块
+---------------------------+
```

**射频抽象层(RAL)** 是关键设计, 它向上层提供统一的接口:

```c
// 射频抽象层统一接口
typedef struct {
    int (*init)(void);
    int (*connect)(const char *target);
    int (*send)(const uint8_t *data, size_t len);
    int (*recv)(uint8_t *buf, size_t max_len);
    int (*disconnect)(void);
    int (*get_signal_quality)(void);  // 返回0-100的质量值
    int (*get_energy_cost)(void);     // 每字节能耗估算
} radio_interface_t;

// 各射频模块实现同一接口
radio_interface_t ble_radio = { ble_init, ble_connect, ... };
radio_interface_t wifi_radio = { wifi_init, wifi_connect, ... };
radio_interface_t lte_radio = { lte_init, lte_connect, ... };
```

应用层通过连接管理器发送数据时, 完全不需要知道底层使用的是哪个射频模块. 连接管理器根据策略引擎的决策, 自动路由到合适的射频通道.

### 1.3 连接管理器的核心职责

连接管理器需要完成以下关键任务:

- 监控各射频模块的状态(是否可用, 信号质量, 能耗)
- 根据策略引擎的规则做出射频选择决策
- 协调射频切换过程, 确保数据不丢失
- 管理各射频模块的开关(未使用的模块应关闭以省电)
- 向应用层提供连接状态变更的回调通知

## 2 射频选择标准

### 2.1 多维度评估

选择使用哪个射频不是简单的单一指标比较, 而是一个多维度的综合评估:

| 评估维度 | BLE | WiFi | LoRa | LTE-M |
|----------|-----|------|------|-------|
| 覆盖范围 | 10-100m | 50-200m | 2-15km | 全域 |
| 数据速率 | 1-2 Mbps | 10-100 Mbps | 0.3-50 kbps | 1 Mbps |
| 每字节能耗 | 低 | 中高 | 很低 | 高 |
| 延迟 | 低 | 低 | 高 | 中 |
| 通信成本 | 免费 | 免费 | 免费 | 付费 |
| 可靠性 | 中 | 中 | 中低 | 高 |

### 2.2 场景化选择

不同场景下的最优选择完全不同:

**传感器周期上报**: 数据量小(几十字节), 频率低(每小时一次), 对延迟不敏感. 最优选择: LoRa或BLE(通过网关).

**固件更新**: 数据量大(几百KB到几MB), 一次性传输, 可以等待合适时机. 最优选择: WiFi(速度快且免费).

**紧急告警**: 数据量小但对可靠性和延迟要求高. 最优选择: LTE-M(最可靠, 覆盖广).

**本地配置**: 近距离, 交互式, 数据量中等. 最优选择: BLE(低功耗, 简单配对).

### 2.3 综合评分算法

一个实用的射频评分算法:

```python
def calculate_radio_score(radio, context):
    """计算某个射频在当前上下文的综合得分"""
    if not radio.is_available():
        return 0  # 不可用直接排除

    # 各维度得分 (0-100)
    coverage_score = radio.get_signal_quality()
    energy_score = 100 - radio.get_energy_cost_normalized()
    rate_score = min(100, radio.data_rate / context.required_rate * 100)
    latency_score = max(0, 100 - radio.latency / context.max_latency * 100)
    cost_score = 100 if radio.is_free else 20

    # 加权求和, 权重根据场景调整
    weights = context.get_weights()  # 例如紧急告警场景可靠性权重最高
    score = (weights.coverage * coverage_score +
             weights.energy * energy_score +
             weights.rate * rate_score +
             weights.latency * latency_score +
             weights.cost * cost_score)

    return score
```

## 3 垂直切换机制

### 3.1 什么是垂直切换

水平切换(Horizontal Handover)是在同一技术的不同接入点之间切换, 比如从一个WiFi热点切换到另一个. 垂直切换(Vertical Handover)则是在不同无线技术之间切换, 比如从WiFi切换到蜂窝网络.

垂直切换比水平切换复杂得多, 因为涉及:

- 完全不同的协议栈: WiFi用802.11, 蜂窝用3GPP
- IP地址可能变化: 不同网络分配不同IP
- QoS特性差异: 带宽, 延迟, 抖动都不同
- 会话连续性: 正在传输的数据不能丢失

### 3.2 切换触发条件

垂直切换的触发条件可以分为被动触发和主动触发:

**被动触发(不得不切换)**:
- 信号质量降低: 当前射频RSSI低于阈值
- 覆盖丢失: 当前射频完全不可用(例如离开WiFi覆盖区)
- 连接超时: 多次重传失败

**主动触发(可以更好)**:
- 应用需求变化: 需要传输大文件, 从BLE切到WiFi
- 能耗优化: 电量低时从WiFi切到LoRa
- 成本优化: 发现免费WiFi可用时从蜂窝切换
- 网络负载均衡: 当前网络拥塞时切换

### 3.3 切换判断中的迟滞机制

为了避免在两个射频之间频繁来回切换(乒乓效应), 需要引入迟滞(Hysteresis):

```
信号质量
  ^
  |     WiFi信号
  |  ___/\____/\___________
  | /                      \___
  |                              切换到蜂窝的阈值 (低)
  |----------------------------  30 dBm
  |
  |                              切回WiFi的阈值 (高)
  |----------------------------  40 dBm
  |
  +--------------------------------> 时间
```

只有当WiFi信号降到30dBm以下才切换到蜂窝, 而要切回WiFi则需要信号恢复到40dBm以上. 这10dBm的差值就是迟滞量, 防止信号在阈值附近波动时频繁切换.

### 3.4 驻留定时器

除了迟滞量, 驻留定时器(Dwell Timer)也是防止乒乓效应的重要机制. 切换到一个新射频后, 必须在新射频上停留至少一个最小驻留时间(例如30秒), 才允许再次切换. 这样即使信号短暂波动, 也不会触发多余的切换.

## 4 无缝切换技术

### 4.1 先建后断(Make-Before-Break)

最基本的无缝切换策略: 在断开当前射频之前, 先建立新射频的连接.

```
时间线:
  WiFi:  ====连接中========断开==
  LTE-M:          ==建立连接========连接中====
  数据:  ---WiFi发送---|--双发--|---LTE-M发送---
```

这种方式需要设备短时间内同时激活两个射频模块, 会增加瞬时功耗, 但保证了数据传输的连续性.

### 4.2 传输层方案: MPTCP

多路径TCP(Multipath TCP, MPTCP)是一种在传输层实现多射频并行使用的技术:

- 一个TCP连接可以同时使用多条路径(例如WiFi和蜂窝)
- 数据包在多条路径上分发, 聚合带宽
- 一条路径失败时, 自动在其他路径上继续, 实现无感知切换
- Apple在iOS上使用MPTCP来实现WiFi和蜂窝的无缝切换

对于IoT设备来说, 完整的MPTCP实现过于复杂和耗资源, 但简化版本可以在资源较充裕的网关设备上使用.

### 4.3 应用层方案

对于资源受限的IoT设备, 应用层的会话恢复机制是最实用的方案:

```c
// MQTT的持久会话机制
// 客户端设置 cleanSession = false
mqtt_connect_opts.cleanSession = 0;
mqtt_connect_opts.clientId = "device-001";

// 切换射频后重连
// 服务器会保留之前的订阅和未送达的消息
// QoS 1/2的消息会在重连后重新投递
void on_radio_switch_complete(radio_type_t new_radio) {
    mqtt_reconnect(new_radio);
    // 持久会话自动恢复, 不丢消息
}
```

MQTT的持久会话(Persistent Session)天然支持断线重连, 在切换射频导致短暂断连后, 通过新射频重连即可恢复会话, 服务器端缓存的消息会自动重新投递.

## 5 基于策略的管理

### 5.1 策略规则引擎

策略引擎定义了"在什么条件下使用哪个射频"的规则:

```python
# 策略规则示例
policies = [
    {
        "name": "indoor_wifi_preferred",
        "condition": "location == 'indoor' AND wifi.available",
        "action": "use_radio('wifi')",
        "priority": 10
    },
    {
        "name": "low_battery_lpwan",
        "condition": "battery < 20",
        "action": "use_radio('lora')",
        "priority": 20  # 高优先级
    },
    {
        "name": "firmware_update_wifi",
        "condition": "task == 'firmware_update'",
        "action": "use_radio('wifi')",
        "priority": 15
    },
    {
        "name": "emergency_cellular",
        "condition": "data.priority == 'critical'",
        "action": "use_radio('lte_m')",
        "priority": 25  # 最高优先级
    },
    {
        "name": "default_lowest_energy",
        "condition": "true",
        "action": "use_radio(lowest_energy_available())",
        "priority": 1  # 兜底规则
    }
]
```

### 5.2 策略来源

策略规则可以来自三种途径:

**静态配置**: 出厂时写入设备固件, 适用于部署环境已知且固定的场景.

**云端下发**: IoT平台根据设备运行数据分析后动态下发, 可以在不更新固件的情况下调整策略.

**自适应学习**: 设备根据历史经验自动调整, 例如发现某个位置WiFi总是不稳定, 自动降低该位置WiFi的优先级.

### 5.3 策略冲突处理

当多条策略同时匹配时, 通过优先级解决冲突. 上面的例子中, 如果设备电量低(触发low_battery_lpwan, 优先级20)同时有紧急告警(触发emergency_cellular, 优先级25), 紧急告警的优先级更高, 会使用蜂窝网络发送.

## 6 能耗感知的连接管理

### 6.1 射频能耗特征

不同射频模块的能耗差异巨大:

| 状态 | BLE | WiFi | LoRa | LTE-M |
|------|-----|------|------|-------|
| 空闲监听(mA) | 0.01 | 2-5 | 0.002 | 3-6 |
| 扫描/发现(mA) | 5-10 | 80-200 | N/A | 50-100 |
| 发送(mA) | 8-15 | 150-300 | 20-40 | 200-400 |
| 接收(mA) | 5-10 | 100-200 | 10-15 | 50-100 |

### 6.2 能耗优化策略

**低功耗射频常开策略**: 保持BLE或LoRa始终处于低功耗监听状态, 用作"唤醒通道". 当需要高速传输时, 通过低功耗通道接收唤醒信号, 再激活WiFi或蜂窝模块.

```
正常状态:  BLE低功耗监听 (10uA)
           WiFi/LTE-M 完全关闭 (0)

收到唤醒:  BLE接收"需要OTA更新"信号
           -> 唤醒WiFi模块
           -> WiFi连接下载固件 (3分钟)
           -> 关闭WiFi
           -> BLE恢复低功耗监听
```

这种方式相比WiFi始终保持连接, 可以节省90%以上的待机功耗.

### 6.3 传输能效计算

选择射频时不仅要看发送功率, 还要考虑传输效率:

发送100字节数据的总能耗 = 射频启动能耗 + 连接建立能耗 + 数据传输能耗

对于小数据包, BLE或LoRa的总能耗最低(启动快, 连接开销小). 对于大数据传输, WiFi虽然发送功率高, 但传输速度快, 总能耗可能反而更低. 这就是"传输效率"的概念 -- 每比特的能耗而不是瞬时功率.

## 7 云端管理的多射频系统

### 7.1 云端决策模型

在云端管理模式下, 设备负责收集信息, 云端负责做决策:

设备上报的信息: 各射频模块的信号质量, 电池电量, 待发送数据队列长度, 当前位置(如果有GPS).

云端下发的指令: 使用哪个射频发送哪类数据, 各射频的开关时间表, 更新的策略规则.

### 7.2 全局优化的优势

云端管理的最大优势在于可以做全局优化. 单个设备只能根据自身情况做局部最优决策, 而云端可以综合考虑:

- 整个设备集群的网络负载分布
- 各基站/网关的容量状态
- 设备间的干扰关系
- 全网的能耗预算

例如, 当某个LoRa网关负载过高时, 云端可以指导部分设备切换到NB-IoT, 实现全网负载均衡.

### 7.3 策略热更新

云端管理允许在不更新设备固件的情况下调整连接策略. 当运营商调价, 网络拓扑变化, 或者发现某些策略效果不佳时, 可以即时修改策略并下发到设备, 大大提升了运维灵活性.

## 8 实际案例: 物流追踪设备

### 8.1 场景描述

一个物流追踪设备集成了GPS, BLE, WiFi和LTE-M四种射频模块, 需要在物流全流程中提供追踪和数据同步服务.

### 8.2 各阶段的射频选择

**在仓库内**: 使用WiFi进行高速率的库存数据同步. 仓库有稳定的WiFi覆盖, 传输免费且速度快, 适合同步大量库存信息和接收固件更新.

**运输途中**: 使用LTE-M每5分钟上报一次位置信息. 运输过程中只有蜂窝网络可用, 但数据量小(GPS坐标只有几十字节), LTE-M完全胜任.

**在客户现场**: 使用BLE进行本地签收确认. 配送员手机通过BLE连接设备, 完成电子签收, 无需网络覆盖.

**电池告急**: 仅使用LTE-M发送紧急告警. 当电量低于10%时, 关闭所有其他射频, 仅保留LTE-M在PSM模式下待机, 只在检测到异常时唤醒发送告警.

### 8.3 效果对比

| 指标 | 始终蜂窝 | 多射频管理 |
|------|----------|-----------|
| 电池寿命 | 7天 | 21天(3倍) |
| 数据成本 | 100% | 30%(70%通过WiFi) |
| 覆盖可靠性 | 95% | 99.5% |
| 大文件传输速度 | 中等 | 快(WiFi) |

通过智能的多射频管理, 设备电池寿命提升了3倍, 数据通信成本降低了70%, 同时保持了更高的整体可靠性.

## 总结

多射频连接管理是IoT设备面对复杂通信环境的关键能力. 核心理念可以归纳为:

架构方面, 射频抽象层解耦了应用与具体射频技术, 连接管理器和策略引擎实现了智能决策. 选择标准方面, 覆盖, 能耗, 速率, 延迟, 成本五个维度的综合评估决定了最优射频. 切换方面, 迟滞机制和驻留定时器防止乒乓效应, 先建后断和会话恢复保证数据连续性. 能耗方面, 低功耗射频常开加按需唤醒高功耗射频是最核心的策略. 管理方面, 云端管理实现全局优化和策略热更新.

随着IoT设备集成的射频技术越来越多, 多射频连接管理将从高端设备逐步普及到更广泛的IoT产品中, 成为IoT连接层不可或缺的核心能力.

## 参考文献

1. D. Kaspar, "Multipath TCP (MPTCP) for IoT: Opportunities and Challenges," IEEE Communications Magazine, 2021
2. A. Ahmed et al., "A Survey on Vertical Handover Decision Making in Heterogeneous Wireless Networks," Journal of Network and Computer Applications, 2019
3. S. Deng et al., "Energy-Efficient Multi-Radio Resource Management for IoT Devices," IEEE Internet of Things Journal, 2020
4. M. Lauridsen et al., "An Empirical NB-IoT Power Consumption Model for Battery Lifetime Estimation," IEEE VTC Spring, 2018
5. Thread Group, "Thread 1.3 Specification - Multi-Radio Support," 2022
