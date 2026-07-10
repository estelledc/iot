---
schema_version: '1.0'
id: ble-beacon-ibeacon-eddystone
title: BLE信标iBeacon与Eddystone协议对比
layer: 2
content_type: UNKNOWN
difficulty: beginner
reading_time: 18
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# BLE信标iBeacon与Eddystone协议对比
> **难度**：🟢 初级 | **领域**：BLE广播应用 | **阅读时间**：约 18 分钟

## 引言

想象你走进一座博物馆，每件展品旁边都有一个隐形导游。你不需要主动询问，只要靠近展品，手机就会自动弹出相关介绍。这个隐形导游就是 BLE 信标(Beacon)--一种只负责广播信号的小型蓝牙设备，就像灯塔不断向四周发出光芒，周围的船只(手机)接收到光芒就能判断自己离灯塔有多远。

本文将对比两种主流 BLE 信标协议：Apple 的 iBeacon 和 Google 的 Eddystone。

## 1. BLE Beacon基本概念

### 1.1 什么是BLE信标

BLE 信标是一种纯广播设备，周期性地发送广告包(Advertising Packets)，不需要与接收设备建立连接。这种单向通信模式极大地简化了设计并降低了功耗。

```
信标设备                         接收设备(手机)
   |                                |
   |--- 广告包(每隔N毫秒) -------->|
   |--- 广告包 -------------------->|  --> 检测到信标
   |--- 广告包 -------------------->|  --> 计算RSSI, 估算距离
```

### 1.2 信标与普通BLE设备的区别

普通 BLE 设备需要建立连接才能交换数据，而信标仅利用广告阶段进行数据传输：

- 无需配对或连接，任何扫描设备都能接收
- 一个信标可以同时被无数设备检测到
- 设计极简，功耗极低(纽扣电池运行数年)
- 数据传输是单向的，信标不知道谁在监听

## 2. iBeacon协议详解

### 2.1 iBeacon数据格式

iBeacon 是 Apple 在 2013 年推出的信标标准，广告包格式固定且简洁：

```
iBeacon广告数据结构 (30字节):
+----------+--------+--------+--------+----------+
| Prefix   | UUID   | Major  | Minor  | TX Power |
| (9字节)  | (16B)  | (2B)   | (2B)   | (1B)     |
+----------+--------+--------+--------+----------+
```

### 2.2 三级标识体系

| 层级 | 字段 | 长度 | 用途示例 |
|------|------|------|----------|
| 组织 | UUID | 16字节 | 整个连锁品牌 |
| 区域 | Major | 2字节 | 某一家门店 |
| 节点 | Minor | 2字节 | 门店内具体位置 |

```python
# iBeacon标识示例
beacon_config = {
    "uuid": "f7826da6-4fa2-4e98-8024-bc5b71e0893e",
    "major": 100,   # 北京朝阳门店
    "minor": 1,     # 入口处
    "tx_power": -59  # 1米处校准RSSI值(dBm)
}
```

### 2.3 iOS原生支持

iBeacon 在 iOS 中通过 Core Location 框架享有原生支持：

```swift
// iOS iBeacon区域监控
let uuid = UUID(uuidString: "f7826da6-4fa2-4e98-8024-bc5b71e0893e")!
let region = CLBeaconRegion(uuid: uuid, major: 100, minor: 1,
                            identifier: "store-entrance")
locationManager.startMonitoring(for: region)
locationManager.startRangingBeacons(
    satisfying: region.beaconIdentityConstraint)
```

iOS 将距离分为三区：Immediate(小于0.5m)、Near(0.5-3m)、Far(大于3m)。

## 3. Eddystone协议详解

### 3.1 多帧类型架构

Eddystone 是 Google 在 2015 年推出的开放信标标准，支持多种帧类型：

| 帧类型 | 用途 | 数据内容 |
|--------|------|----------|
| Eddystone-UID | 唯一标识 | 10字节Namespace + 6字节Instance |
| Eddystone-URL | 物理网络 | 压缩URL(最长17字节) |
| Eddystone-TLM | 遥测数据 | 电池电压、温度、广播计数 |
| Eddystone-EID | 短暂标识 | 8字节旋转标识符(防伪造) |

### 3.2 Eddystone-URL

信标直接广播 URL，接收设备无需安装特定 App：

```
URL编码方案(节省字节):
0x00 = "http://www."    0x01 = "https://www."
0x02 = "http://"        0x03 = "https://"
后缀: 0x00=".com/"  0x01=".org/"  0x02=".edu/"

示例: https://www.museum.com/exhibit/01 编码后仅需约15字节
```

### 3.3 Eddystone-TLM遥测帧

```c
// TLM帧数据结构
struct eddystone_tlm {
    uint8_t  frame_type;    // 0x20
    uint8_t  version;       // 0x00
    uint16_t battery_mv;    // 电池电压(毫伏)
    int16_t  temperature;   // 温度(8.8定点数)
    uint32_t adv_count;     // 广播次数
    uint32_t sec_count;     // 运行时间(x0.1s)
};
```

### 3.4 Eddystone-EID安全特性

EID 标识符定期旋转，只有注册过的服务器能解析：

```
EID旋转机制:
1. 信标与服务器共享密钥(注册时)
2. 信标用HKDF算法生成临时ID
3. 旋转周期可配置(2^K秒, K=0-15)
4. 服务器用相同算法验证ID真实性
```

## 4. iBeacon与Eddystone对比

### 4.1 综合对比表

| 特性 | iBeacon | Eddystone |
|------|---------|-----------|
| 开发者 | Apple | Google |
| 开放性 | 授权使用 | Apache 2.0开源 |
| 帧类型 | 单一固定格式 | 4种帧类型 |
| URL广播 | 不支持 | 原生支持 |
| 遥测数据 | 不支持 | 原生支持(TLM) |
| 防伪造 | 无内置机制 | EID旋转标识 |
| iOS支持 | 原生(CoreLocation) | 需第三方SDK |
| Android支持 | 需第三方SDK | 原生(Nearby) |

### 4.2 选择建议

```
决策流程:
1. 目标用户主要用iOS?       --> iBeacon
2. 需要URL广播/免App?       --> Eddystone-URL
3. 需要信标健康监控?         --> Eddystone(TLM帧)
4. 需要防伪造安全?           --> Eddystone-EID
5. 想最简单部署?             --> iBeacon
6. 跨平台均衡?              --> 双模信标(同时广播两种)
```

## 5. 距离估算原理

### 5.1 RSSI路径损耗模型

```
公式: RSSI(d) = RSSI(d0) - 10 * n * log10(d/d0)
反解: d = d0 * 10^((RSSI(d0) - RSSI(d)) / (10*n))

其中: d0=参考距离(1米), n=路径损耗指数(室内2-4)
```

### 5.2 距离估算代码

```python
import math

def estimate_distance(rssi, tx_power, n=2.5):
    """
    rssi: 当前接收信号强度(dBm)
    tx_power: 1米处校准RSSI值(dBm)
    n: 路径损耗指数
    """
    if rssi >= tx_power:
        return 0.1
    ratio = (tx_power - rssi) / (10.0 * n)
    return round(math.pow(10, ratio), 2)

# 示例: tx_power=-59, rssi=-75 --> 约3.5米
```

### 5.3 精度影响因素

实际精度通常在 1-3 米，影响因素：多径效应(墙壁反射)、人体遮挡(衰减3-5dB)、信标朝向、环境噪声(WiFi等同频干扰)、RSSI波动(静止时也有5-10dB波动)。

## 6. 广告间隔与功耗

### 6.1 广告间隔选择

| 广告间隔 | 检测延迟 | 适用场景 | 相对功耗 |
|----------|----------|----------|----------|
| 100ms | 极快 | 高精度追踪 | 10x |
| 500ms | 中等 | 零售促销 | 2x |
| 1000ms | 较慢 | 资产管理 | 1x(基准) |
| 2000ms | 慢 | 存在检测 | 0.5x |

### 6.2 电池寿命估算

```
CR2032: 容量230mAh, 电压3V
单次广告: ~15uA * 3ms * 3通道 = 135nAs
休眠电流: ~1uA

1秒间隔平均电流: ~1.13uA
理论寿命: 230mAh / 1.13uA = 23年
实际(含自放电): 约2-3年
```

## 7. 典型应用场景

### 7.1 博物馆导览

```python
class MuseumGuide:
    def __init__(self):
        self.exhibits = {
            (1, 1): {"name": "青铜器展", "audio": "bronze.mp3"},
            (1, 2): {"name": "瓷器展", "audio": "porcelain.mp3"},
        }

    def on_beacon_detected(self, major, minor, proximity):
        key = (major, minor)
        if key in self.exhibits and proximity == "near":
            exhibit = self.exhibits[key]
            self.show_exhibit_info(exhibit)
```

### 7.2 其他场景

- 零售商场：顾客进店自动推送优惠券，按楼层和专柜精确触发
- 资产追踪：物品贴信标，固定接收器检测存在状态
- 自动考勤：办公区部署接收器，员工手机与信标交互签到

## 8. 硬件选型与部署

### 8.1 主流芯片方案

| 芯片 | 厂商 | 特点 | 适用场景 |
|------|------|------|----------|
| nRF52832 | Nordic | 灵活可编程 | 原型开发 |
| DA14531 | Dialog | 极低功耗 | 超小型信标 |
| CC2640R2 | TI | 多协议 | 工业信标 |
| ESP32 | Espressif | WiFi加BLE | 网关加信标 |

### 8.2 部署建议

```
1. 安装高度: 2.5-3米(避免人体遮挡)
2. 天线朝向: 向下辐射覆盖地面
3. 间距规划: 精确触发3-5米, 区域识别8-10米
4. 避免金属/水体附近
5. 实际环境RSSI热力图测试验证
```

## 9. 安全性考量

### 9.1 信标伪造威胁

iBeacon 的标识是明文广播的，攻击者可以轻易复制并欺骗接收设备：

```
攻击流程:
1. 扫描获取目标信标的UUID/Major/Minor
2. 用另一个BLE设备广播相同数据
3. 欺骗附近的接收设备触发错误逻辑
```

### 9.2 防护措施

| 方案 | 实现方式 | 防护等级 |
|------|----------|----------|
| Eddystone-EID | 密钥旋转标识 | 高 |
| 应用层验证 | 服务端校验额外信息 | 中 |
| 环境指纹 | 多信标组合验证 | 中高 |
| 时间窗口限制 | 结合服务端时间校验 | 中 |

对于安全敏感场景(支付、门禁)，不应仅依赖信标距离判断，应结合服务端验证、多因素认证和异常检测。在生产环境中建议至少采用两种以上防护手段的组合。

## 总结

BLE 信标技术为近场交互提供了低成本、低功耗的解决方案。iBeacon 以简洁和 iOS 原生支持见长，适合 Apple 生态为主的场景；Eddystone 以灵活的多帧架构和开放性取胜，适合需要 URL 广播、遥测监控或安全防护的复杂场景。

在实际项目中，硬件选型、广告间隔配置和部署环境测试往往比协议选择本身更影响最终效果。建议从小规模试点开始，在真实环境中验证距离精度和检测可靠性，然后再进行大规模部署。

对于需要同时覆盖 iOS 和 Android 用户的场景，可以考虑使用双模信标同时广播两种协议格式，兼顾两个生态的原生支持优势。

## 参考文献

1. Apple iBeacon Specification - developer.apple.com/ibeacon
2. Eddystone Protocol Specification - github.com/google/eddystone
3. Bluetooth SIG, "Bluetooth Core Specification v5.3", 2021
4. Nordic Semiconductor, "nRF5 SDK Beacon Examples", developer.nordicsemi.com
5. Faragher R., Harle R., "Location Fingerprinting with Bluetooth Low Energy Beacons", IEEE JSAC, 2015
