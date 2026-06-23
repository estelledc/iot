# Layer 2: 无线接入 (Connectivity)

> 万物互联的第一步，是让设备"说上话"。这一层解决的核心问题是：如何把传感器采集到的数据，通过无线电波送出去。

---

## 这一层讲什么？

想象你要寄一封信。你得先选择运输方式——同城快递（短距）、跨省物流（广域）、还是国际航空（卫星）。无线接入层做的就是这件事：为每个物联网设备选择最合适的"无线邮路"。

物联网的无线技术大致分三个圈层：

**近场 / 短距通信（< 100m）**：设备和设备之间"面对面聊天"。蓝牙、星闪、UWB、ZigBee/Thread/Matter 属于这一类。功耗低、延迟小，适合可穿戴、智能家居、精密定位。

**广域 / 低功耗广域网（1-50km）**：设备隔着几公里甚至几十公里"喊话"。LoRaWAN、NB-IoT、LTE-M、Sigfox 属于这一类。信号穿透力强、电池能撑好几年，适合抄表、农业、资产追踪。

**蜂窝 / 卫星接入**：借助已有的手机基站或天上的卫星来联网。5G RedCap、卫星物联网属于这一类。覆盖广、可靠性高，适合车联网、远洋监测、偏远地区。

另外还有一些"反常规"的技术——比如反向散射通信，设备自己不发信号，而是"反射"环境中已有的 WiFi/BLE 信号来传数据，功耗低到几乎为零。

---

## 为什么这一层重要？

选错了无线技术，整个物联网系统都会出问题：

- 选了高功耗技术给电池设备 → 三个月就没电了
- 选了短距技术给农田监测 → 信号根本传不到
- 选了低速率技术传视频 → 数据永远传不完
- 选了不安全的协议 → 设备被劫持

这一层的选型直接决定了上层所有设计的约束条件。

---

## 论文导读

### 短距通信

| # | 论文 | 关键词 | 难度 |
|---|------|--------|------|
| 1 | [星闪 vs 蓝牙 6.0：下一代短距无线技术对决](papers/sparklink-vs-ble6.md) | SparkLink, BLE 6.0, Channel Sounding, 车联网 | 🟡 进阶 |
| 2 | [UWB 超宽带高精度定位技术](papers/uwb-positioning.md) | IEEE 802.15.4z, TWR, TDoA, 数字车钥匙 | 🟡 进阶 |
| 3 | [ZigBee/Matter/Thread：智能家居协议演进](papers/zigbee-matter-thread.md) | Matter, Thread, ZigBee 3.0, 智能家居 | 🟢 入门 |

### 广域 / LPWAN

| # | 论文 | 关键词 | 难度 |
|---|------|--------|------|
| 4 | [LPWAN 技术全面对比](papers/lpwan-comparison.md) | LoRaWAN, NB-IoT, LTE-M, Sigfox | 🟢 入门 |
| 5 | [NB-IoT 规模部署：从标准到实践](papers/nb-iot-deployment.md) | NB-IoT, 智能抄表, 覆盖增强 | 🟡 进阶 |
| 6 | [LoRaWAN 网络可扩展性](papers/lorawan-scalability.md) | LoRa, CSS, ADR, 大规模部署 | 🟠 挑战 |

### 蜂窝 / WiFi / 卫星

| # | 论文 | 关键词 | 难度 |
|---|------|--------|------|
| 7 | [WiFi 7 对物联网接入的适用性分析](papers/wifi7-iot.md) | 802.11be, MLO, WiFi HaLow | 🟡 进阶 |
| 8 | [5G RedCap：为物联网量身定制的 5G](papers/5g-redcap-iot.md) | RedCap, eRedCap, 3GPP R17/R18 | 🟡 进阶 |
| 9 | [卫星物联网：天地一体的连接覆盖](papers/satellite-iot.md) | LEO, NTN, D2S, 海洋/农业 | 🟠 挑战 |

### 前沿探索

| # | 论文 | 关键词 | 难度 |
|---|------|--------|------|
| 10 | [反向散射通信：迈向零功耗物联网](papers/backscatter-communication.md) | Ambient Backscatter, WiFi/BLE/LoRa | 🔴 研究前沿 |

---

## 阅读建议

**零基础路线**：先读 LPWAN 对比 → ZigBee/Matter/Thread → 星闪 vs 蓝牙 → 其余按兴趣选读

**有基础路线**：直接跳到感兴趣的技术方向，每篇独立可读

**研究路线**：重点关注反向散射通信、卫星物联网、UWB 定位这三篇前沿内容

---

## 与其他层的关系

```
Layer 1 (感知与硬件)
    ↓ 传感器数据
Layer 2 (无线接入) ← 你在这里
    ↓ 连接建立
Layer 3 (网络协议)
    ↓ 数据传输
Layer 4 (计算平台)
```

- **向下**：Layer 1 的传感器和 MCU 决定了可用的无线接口（比如 ESP32 支持 WiFi/BLE，不支持 LoRa）
- **向上**：Layer 3 的协议（MQTT、CoAP）需要基于这一层建立的无线链路来运行
- **交叉**：Layer 6 的安全机制需要在无线接入层就开始考虑（比如 UWB 的安全测距）
