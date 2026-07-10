---
schema_version: '1.0'
id: ble-periodic-advertising-sync
title: BLE周期性广播与同步传输应用
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
# BLE周期性广播与同步传输应用
> **难度**：🔴 高级 | **领域**：BLE高级特性 | **阅读时间**：约 22 分钟

## 引言

想象一个火车站的到站信息显示屏系统。传统做法(BLE 连接模式)是车站控制中心逐个给每块显示屏打电话，一块一块地通知更新——有 100 块显示屏就要打 100 通电话。而周期性广播就像车站的广播喇叭：控制中心每隔一段时间广播一次最新的列车到达信息，所有显示屏只要"调到正确的频道"，就能在约定的时刻自动接收更新，不需要逐一建立连接。更妙的是，显示屏不需要一直竖着耳朵听——它知道下一次广播的精确时间，平时可以"打个盹"，到点再醒来听就行。

BLE 5.0 引入的周期性广播(Periodic Advertising)正是这样一种机制：广播者以固定的时间间隔发送数据，扫描者同步到这个时间节奏后，只在广播到来的精确时刻唤醒射频接收数据。这彻底改变了传统广播模式中"扫描者必须持续监听"的高功耗困境。

本文将深入讲解周期性广播的工作原理、同步流程、功耗优势，以及 BLE 5.1 PAST 和 BLE 5.4 PAwR 等后续演进。

## 1. 传统广播的局限

### 1.1 普通广播的工作方式

BLE 4.x 的传统广播(Legacy Advertising)有以下特点：

- 广播者在三个广播信道(37/38/39)上发送广播包
- 广播间隔存在随机延迟(0-10ms)，使得广播时刻不可精确预测
- 扫描者必须持续打开射频接收机进行监听
- 扫描者不知道下一个广播包何时到来

### 1.2 持续扫描的功耗问题

传统扫描模式下，扫描者的射频接收机必须保持开启才能捕获广播包。射频接收消耗的电流通常为 5-8mA：

```
传统扫描功耗估算:
扫描占空比 100%(持续扫描):
  I_avg = I_rx = 6 mA
  CR2032 电池 230mAh
  续航 = 230 / 6 = 约 38 小时

扫描占空比 10%(间歇扫描):
  I_avg = 6mA * 0.1 + 0.002mA * 0.9 = 0.6 mA
  续航 = 230 / 0.6 = 约 16 天
  代价: 可能错过广播包
```

这对于电池供电的接收设备来说是不可接受的。周期性广播正是为了解决这个问题。

## 2. 周期性广播原理

### 2.1 核心概念

周期性广播建立在 BLE 5.0 扩展广播(Extended Advertising)之上。它的核心思想是：广播者承诺按照严格固定的时间间隔发送数据，接收者一旦获知这个时间节奏，就可以精准预测每一次广播的到来时刻。

关键组件：

- **扩展广播**：携带 SyncInfo 信息，告知扫描者如何同步到周期性广播
- **周期性广播列车**：以固定间隔发送的一系列广播事件
- **SyncInfo**：包含间隔、时间偏移、信道映射、访问地址等同步参数

### 2.2 广播者的行为

广播者同时维护两种广播：

```
广播者的工作流程:
1. 发送扩展广播 (ADV_EXT_IND) -- 在主广播信道
   --> 包含 AuxPtr，指向辅助广播

2. 发送辅助广播 (AUX_ADV_IND) -- 在数据信道
   --> 包含 SyncInfo(同步信息)

3. 按固定间隔发送周期性广播 (AUX_SYNC_IND)
   --> 间隔范围: 7.5ms - 81918.75ms
   --> 每次在不同数据信道上(跳频)
   --> 携带最多 254 字节用户数据
```

### 2.3 与普通广播的对比

| 特性 | 普通广播 | 周期性广播 |
|------|---------|-----------|
| 定时精度 | 有 0-10ms 随机延迟 | 严格固定间隔 |
| 数据容量 | 31B(传统)/254B(扩展) | 254B，可链式扩展 |
| 接收端行为 | 持续或间歇扫描 | 同步后按时唤醒 |
| 功耗 | 接收端功耗高 | 接收端功耗极低 |
| 信道使用 | 仅广播信道(3个) | 数据信道(37个)跳频 |

## 3. 同步流程详解

### 3.1 扫描者发现并同步

扫描者从零开始同步到周期性广播列车的完整流程：

```
阶段 1: 发现
  扫描者在广播信道上接收 ADV_EXT_IND
  --> 获得 AuxPtr，指向辅助广播的信道和时间偏移

阶段 2: 获取同步信息
  扫描者切换到数据信道，接收 AUX_ADV_IND
  --> 获得 SyncInfo(间隔、偏移、信道映射等)

阶段 3: 首次同步
  扫描者计算下一个 AUX_SYNC_IND 的时间和信道
  --> 在正确时刻和信道打开接收机
  --> 成功接收 = 同步建立

阶段 4: 持续接收
  根据间隔和跳频规则预测后续事件
  --> 每次只在预计时刻短暂打开接收机
  --> 接收后立即关闭接收机
```

### 3.2 SyncInfo 结构

SyncInfo 包含了扫描者同步所需的全部信息：

| 字段 | 大小 | 说明 |
|------|------|------|
| Sync Offset | 13 bits | 到下一个 AUX_SYNC_IND 的时间偏移 |
| Offset Units | 1 bit | 偏移单位：30us 或 300us |
| Interval | 13 bits | 周期性广播间隔(单位 1.25ms) |
| Channel Map | 37 bits | 使用的信道映射 |
| SCA | 3 bits | 睡眠时钟精度 |
| Access Address | 32 bits | 广播列车的访问地址 |
| CRC Init | 24 bits | CRC 初始值 |
| Event Counter | 16 bits | 当前事件计数 |

### 3.3 同步后的接收窗口

同步建立后，扫描者在每个事件到来前打开一个接收窗口。窗口大小取决于时钟漂移的累积：

```
接收窗口计算:
窗口 = 2 * (本地漂移 + 远端漂移) * 距上次同步的时间

例: 双方时钟精度 50ppm, 距上次接收 1 秒
窗口 = 2 * (50+50) * 10^-6 * 1s = 200us
加上裕量，实际窗口约 300-500us
```

如果连续多次接收失败，窗口逐渐增大以补偿更大的时钟漂移；一旦重新接收成功，窗口缩回正常大小。

## 4. 功耗分析

### 4.1 同步接收的功耗模型

```
设:
  I_rx = 6 mA, I_sleep = 0.002 mA
  T_active = 1.5 ms(接收窗口 + 数据接收)
  T_interval = 100 ms

  Duty_cycle = 1.5 / 100 = 1.5%
  I_avg = 6 * 0.015 + 0.002 * 0.985 = 0.092 mA = 92 uA
```

### 4.2 与其他模式的功耗对比

| 接收模式 | 平均电流 | CR2032 续航 |
|----------|---------|------------|
| 持续扫描 | 6000 uA | 约 38 小时 |
| 间歇扫描(10%占空比) | 600 uA | 约 16 天 |
| 周期性同步(100ms间隔) | 92 uA | 约 100 天 |
| 周期性同步(1s间隔) | 14 uA | 约 1.9 年 |
| BLE连接(CI=1s) | 8 uA | 约 3.3 年 |

周期性广播在一对多数据分发场景中，功耗远优于扫描模式，同时避免了连接模式的一对一限制。

## 5. PAST: 周期性广播同步传输

### 5.1 BLE 5.1 的改进

BLE 5.1 引入了 Periodic Advertising Sync Transfer(PAST)，解决了一个实际问题：如果设备 A 已经与某个周期性广播者同步，设备 B 要同步到同一个广播者，传统做法是 B 自己去扫描和发现。PAST 允许 A 通过已建立的 BLE 连接将同步信息直接传递给 B：

```
PAST 工作流程:

1. 设备 A 已与广播者 X 同步(接收周期性广播中)
2. 设备 B 通过 BLE 连接到设备 A
3. 设备 A 向设备 B 发送同步传输:
   --> LL_PERIODIC_SYNC_IND PDU
   --> 包含 X 的 SyncInfo + 当前同步状态
4. 设备 B 利用收到的信息直接同步到广播者 X
   --> 跳过了扫描和发现阶段
   --> 节省时间和功耗
```

### 5.2 PAST 的应用场景

PAST 在以下场景中特别有价值：

**快速加入广播网络**：新设备通过网关快速同步到已有的周期性广播者，无需自行扫描。

**音频广播(Auracast)**：手机已经同步到一个 Auracast 音频流，用户想让耳机也加入——手机通过 PAST 将同步信息传给耳机。

**传感器网络**：网关设备管理多个传感器节点，当需要所有节点同步到某个时间基准广播时，网关通过 PAST 逐一通知。

## 6. PAwR: 带响应的周期性广播

### 6.1 BLE 5.4 的突破

周期性广播的一个根本限制是它是单向的：广播者发送、接收者监听，接收者没有回传数据的通道。BLE 5.4 引入了 Periodic Advertising with Responses(PAwR)，在周期性广播的框架中加入了响应时隙：

```
PAwR 帧结构:

|<-- 周期性广播事件 -->|<-- 响应时隙 -->|
|                     |               |
| AUX_SYNC_SUBEVENT   | Response      |
|  (广播者发送数据)    | Slot 0        |
|                     | Response      |
|                     | Slot 1        |
|                     | ...           |
|                     | Response      |
|                     | Slot N        |
```

### 6.2 子事件机制

PAwR 将一个周期性广播事件划分为多个子事件(Subevent)，每个子事件可以寻址不同的接收者群组：

| 概念 | 说明 |
|------|------|
| Subevent | 周期性广播事件中的一个子单元 |
| Subevent Data | 广播者在子事件中发送的数据 |
| Response Slot | 子事件后的响应时隙 |
| Response Data | 接收者在响应时隙中回传的数据 |

### 6.3 电子货架标签的典型应用

PAwR 的最典型应用是电子货架标签(ESL)系统。一个超市可能有数千个电子价签，传统做法需要网关逐一连接每个标签进行更新。使用 PAwR：

```
ESL 更新流程:
1. 网关发起周期性广播
2. 子事件 0: 发送给标签组 A 的价格更新数据
   --> 标签组 A 的成员在对应的响应时隙中发送 ACK
3. 子事件 1: 发送给标签组 B 的价格更新数据
   --> 标签组 B 的成员回复 ACK
4. ...
5. 网关检查哪些标签没有回复 ACK，在后续事件中重试
```

这种方式可以在不建立连接的情况下实现对数千个设备的可靠数据分发。

## 7. 音频广播: Auracast

Auracast 是 Bluetooth SIG 推出的基于 LE Audio 的音频广播技术，底层传输建立在周期性广播之上。音频源(如机场广播系统)通过周期性广播发送编码后的音频流，接收设备(如助听器、耳机)同步接收。具体来说，Extended Advertising 携带 SyncInfo 指向周期性广播，周期性广播中包含 BIG Info(描述 BIS 的编解码器、采样率等参数)和元数据(节目名称、语言等)，而 BIS(Broadcast Isochronous Stream)承载实际的音频数据包。接收设备首先同步到周期性广播获取 BIG Info，然后加入对应的 BIS 开始接收音频。

## 8. 实现示例

### 8.1 Zephyr 广播者实现

```c
#include <zephyr/bluetooth/bluetooth.h>

// 周期性广播参数
static struct bt_le_per_adv_param per_adv_param = {
    .interval_min = BT_GAP_PER_ADV_SLOW_INT_MIN, // 100ms
    .interval_max = BT_GAP_PER_ADV_SLOW_INT_MAX,
    .options = 0,
};

// 周期性广播数据
static uint8_t per_adv_data[] = {
    0x02, 0x01, 0x06,  // Flags
    // 用户自定义数据
    0x0A, 0xFF, 0x59, 0x00,  // 厂商数据头
    0x01, 0x02, 0x03, 0x04, 0x05, 0x06,  // 传感器数据
};

static const struct bt_data per_ad[] = {
    BT_DATA(BT_DATA_MANUFACTURER_DATA,
            per_adv_data, sizeof(per_adv_data)),
};

int start_periodic_advertising(void) {
    struct bt_le_ext_adv *adv;
    int err;

    // 创建扩展广播集
    struct bt_le_adv_param adv_param =
        BT_LE_ADV_PARAM_INIT(BT_LE_ADV_OPT_EXT_ADV,
                             BT_GAP_ADV_FAST_INT_MIN_2,
                             BT_GAP_ADV_FAST_INT_MAX_2,
                             NULL);

    err = bt_le_ext_adv_create(&adv_param, NULL, &adv);
    if (err) { return err; }

    // 设置周期性广播参数
    err = bt_le_per_adv_set_param(adv, &per_adv_param);
    if (err) { return err; }

    // 设置周期性广播数据
    err = bt_le_per_adv_set_data(adv, per_ad,
                                  ARRAY_SIZE(per_ad));
    if (err) { return err; }

    // 启动周期性广播
    err = bt_le_per_adv_start(adv);
    if (err) { return err; }

    // 启动扩展广播(携带 SyncInfo)
    err = bt_le_ext_adv_start(adv,
        BT_LE_EXT_ADV_START_DEFAULT);
    return err;
}
```

### 8.2 Zephyr 扫描者/同步者实现

```c
static struct bt_le_per_adv_sync *sync;

// 同步建立回调
static void sync_cb(struct bt_le_per_adv_sync *s,
                    struct bt_le_per_adv_sync_synced_info *info) {
    printk("Synced: interval=%u, phy=%u\n",
           info->interval, info->phy);
}

// 接收周期性广播数据回调
static void recv_cb(struct bt_le_per_adv_sync *s,
                    const struct bt_le_per_adv_sync_recv_info *info,
                    struct net_buf_simple *buf) {
    printk("Received %u bytes, rssi=%d\n",
           buf->len, info->rssi);
    // 处理接收到的数据
}

// 同步丢失回调
static void term_cb(struct bt_le_per_adv_sync *s,
                    const struct bt_le_per_adv_sync_term_info *info) {
    printk("Sync lost, reason=%u\n", info->reason);
}

static struct bt_le_per_adv_sync_cb sync_callbacks = {
    .synced = sync_cb,
    .recv = recv_cb,
    .term = term_cb,
};

int start_sync(const bt_addr_le_t *addr, uint8_t sid) {
    struct bt_le_per_adv_sync_param param = {
        .addr = *addr,
        .sid = sid,
        .skip = 0,
        .timeout = 1000, // 10 秒超时
    };
    bt_le_per_adv_sync_cb_register(&sync_callbacks);
    return bt_le_per_adv_sync_create(&param, &sync);
}
```

## 9. 与连接模式的对比选型

### 9.1 决策矩阵

| 需求维度 | 周期性广播 | BLE 连接 |
|----------|-----------|---------|
| 通信方向 | 主要单向(PAwR可双向) | 双向 |
| 接收者数量 | 无限制 | 受连接数限制 |
| 可靠性 | 无 ACK(PAwR 除外) | 链路层 ACK+重传 |
| 延迟确定性 | 高(固定间隔) | 高(固定 CI) |
| 功耗 | 接收端低 | 双端可优化 |
| 适用场景 | 广播信息分发 | 点对点数据交换 |

### 9.2 混合架构

实际系统中常常将两种模式结合使用。例如智能楼宇系统：

```
混合架构示例:
网关 --[周期性广播]--> 楼层平面图更新 --> 数百个房间显示屏
网关 --[BLE 连接]--> 单个门锁控制 --> 需要安全认证和双向通信
网关 --[PAwR]--> 温湿度传感器轮询 --> 批量采集+ACK 确认
```

## 总结

周期性广播是 BLE 5.0 引入的一项关键特性，它从根本上解决了一对多数据分发场景中的功耗和可扩展性问题。通过固定间隔的广播和精确的时间同步，接收设备可以将射频占空比降低到 1-2%，实现数月甚至数年的电池续航。BLE 5.1 的 PAST 进一步简化了同步建立过程，BLE 5.4 的 PAwR 则补上了响应通道的缺失，使得电子货架标签等需要确认的大规模部署成为现实。从 Auracast 音频广播到智能楼宇信息分发，周期性广播正在成为 BLE 生态系统中不可或缺的基础能力。

## 参考文献

- Bluetooth Core Specification v5.4, Vol 6 Part B Section 4.4.5: Periodic Advertising, Bluetooth SIG, 2023
- Bluetooth SIG, "Periodic Advertising with Responses (PAwR) Feature Overview," 2023
- Woolley, M., "Bluetooth LE Audio: The Future of Wireless Audio," Bluetooth SIG Whitepaper, 2022
- Nordic Semiconductor, "nRF Connect SDK: Periodic Advertising Sync Sample," 2023
- Bluetooth SIG, "Electronic Shelf Label (ESL) Profile Specification," Draft, 2023
