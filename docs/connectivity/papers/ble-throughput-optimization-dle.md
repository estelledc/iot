# BLE数据长度扩展DLE与吞吐量优化
> **难度**：🟡 中级 | **领域**：BLE性能优化 | **阅读时间**：约 20 分钟

## 引言

想象你在搬家，需要把一屋子的书从旧家搬到新家。BLE 4.0 时代就像你只有一个小书包，每次只能装几本书，跑一趟、回来、再装几本、再跑一趟。BLE 4.2 引入的数据长度扩展(DLE)就像给你换了一个大旅行箱——每趟能装的书多了近十倍，搬家总时间自然大幅缩短。而吞吐量优化的本质，就是想办法让每趟装更多、跑更快、少等待。

BLE 最初设计时以低功耗为第一优先级，数据传输能力被刻意限制。但随着可穿戴设备固件升级(OTA DFU)、传感器大量数据上传、音频传输等场景的出现，原始的 27 字节载荷上限成了明显的瓶颈。BLE 4.2 规范通过 DLE 特性将单包载荷上限提升到 251 字节，配合 BLE 5.0 的 2M PHY，使理论吞吐量从几百 kbps 跃升到接近 2Mbps。

本文将从数据包结构出发，详细讲解 DLE 的工作原理、吞吐量计算方法，以及在实际项目中榨取最大传输速度的完整优化方案。

## 1. BLE 数据包结构与开销

### 1.1 链路层数据包格式

理解吞吐量优化的第一步是搞清楚每个数据包里有多少是"有用载荷"，有多少是"协议开销"：

```
BLE 链路层数据包结构:
+----------+----------------+------------+---------+-----+
| Preamble | Access Address | PDU Header | Payload | CRC |
| 1-2 B    | 4 B            | 2-3 B      | 0-251 B | 3 B |
+----------+----------------+------------+---------+-----+
```

各字段的作用：

- **Preamble(前导码)**：1 字节(1M PHY)或 2 字节(2M PHY)，用于接收端的时钟同步和自动增益控制
- **Access Address(访问地址)**：4 字节，标识当前连接，区分不同连接的数据包
- **PDU Header(PDU 头)**：2-3 字节，包含载荷长度、LLID(链路层标识)等信息
- **Payload(载荷)**：0-251 字节，实际传输的数据(DLE 之前上限为 27 字节)
- **CRC(校验码)**：3 字节，用于检测传输错误

### 1.2 帧间间隔

两个连续数据包之间必须有 150us 的帧间间隔(T_IFS, Inter Frame Space)。这个间隔用于接收端处理上一个包并准备发送响应。在计算吞吐量时，IFS 是不可忽略的开销。

### 1.3 有效载荷比

每个数据包的协议开销(Preamble + Access Address + PDU Header + CRC)约 10-12 字节。当载荷只有 27 字节时，有效载荷比约为 27/(27+10) = 73%。当载荷扩展到 251 字节时，有效载荷比提升到 251/(251+10) = 96%。这就是 DLE 提升吞吐量的根本原因：减少了"每字节数据分摊的协议税"。

## 2. DLE 工作原理

### 2.1 DLE 协商过程

DLE 不是单方面生效的，需要连接双方协商。协商通过链路层控制协议(LLCP)的 LL_LENGTH_REQ 和 LL_LENGTH_RSP 消息完成：

```
Central                          Peripheral
   |                                  |
   |--- LL_LENGTH_REQ --------------->|
   |    MaxTxOctets: 251              |
   |    MaxTxTime: 2120us             |
   |    MaxRxOctets: 251              |
   |    MaxRxTime: 2120us             |
   |                                  |
   |<-- LL_LENGTH_RSP ----------------|
   |    MaxTxOctets: 251              |
   |    MaxTxTime: 2120us             |
   |    MaxRxOctets: 251              |
   |    MaxRxTime: 2120us             |
   |                                  |
   |== 双方使用 min(各方声明值) ========|
   |   Effective MaxTxOctets: 251     |
   |   Effective MaxTxTime: 2120us    |
```

协商结果取双方声明值中的较小值。如果一端声明最大 TX 251 字节，另一端只支持 100 字节，那么有效值就是 100 字节。

### 2.2 四个关键参数

DLE 涉及四个参数，分别描述发送和接收方向的能力：

| 参数 | 含义 | 不启用 DLE 的默认值 | DLE 最大值 |
|------|------|---------------------|-----------|
| MaxTxOctets | 最大发送载荷字节数 | 27 | 251 |
| MaxRxOctets | 最大接收载荷字节数 | 27 | 251 |
| MaxTxTime | 最大发送时间 | 328 us | 17040 us |
| MaxRxTime | 最大接收时间 | 328 us | 17040 us |

MaxTxTime/MaxRxTime 的上限值 17040us 对应 Coded PHY S=8 模式下 251 字节载荷的空中传输时间。在 1M PHY 下，251 字节载荷的传输时间约为 2120us。

### 2.3 DLE 与 PDU 大小的关系

启用 DLE 后，链路层 PDU 的最大长度从 27+4=31 字节扩展到 251+4=255 字节(4 字节是 MIC，加密时使用)。在非加密连接中，PDU 载荷直接就是 L2CAP 数据。

## 3. 吞吐量计算

### 3.1 单包传输时间

以 1M PHY 为例，计算一个数据包从开始发送到发送完毕的时间：

```
不启用 DLE (27 字节载荷):
T_packet = Preamble(8us) + AA(32us) + Header(16us) +
           Payload(27*8=216us) + CRC(24us)
         = 296us

启用 DLE (251 字节载荷):
T_packet = Preamble(8us) + AA(32us) + Header(16us) +
           Payload(251*8=2008us) + CRC(24us)
         = 2088us
```

### 3.2 理论吞吐量对比

一个完整的数据交换周期包括：数据包 + IFS + 空应答包 + IFS：

```
不启用 DLE (1M PHY):
T_cycle = T_data(296us) + IFS(150us) + T_ack(80us) + IFS(150us)
        = 676us
Throughput = 27 * 8 / 676us = 319 kbps

启用 DLE (1M PHY):
T_cycle = T_data(2088us) + IFS(150us) + T_ack(80us) + IFS(150us)
        = 2468us
Throughput = 251 * 8 / 2468us = 813 kbps

启用 DLE (2M PHY):
T_cycle = T_data(1052us) + IFS(150us) + T_ack(44us) + IFS(150us)
        = 1396us
Throughput = 251 * 8 / 1396us = 1438 kbps
```

### 3.3 吞吐量对比表

| 配置 | 单包载荷 | PHY | 理论吞吐量 | 相对倍数 |
|------|----------|-----|-----------|---------|
| 无 DLE | 27 B | 1M | ~319 kbps | 1x |
| 有 DLE | 251 B | 1M | ~813 kbps | 2.5x |
| 无 DLE | 27 B | 2M | ~615 kbps | 1.9x |
| 有 DLE | 251 B | 2M | ~1438 kbps | 4.5x |

## 4. ATT MTU 与 DLE 的配合

### 4.1 ATT MTU 的角色

ATT(Attribute Protocol)的 MTU 决定了应用层单次操作可以传输的最大数据量。默认 ATT MTU 是 23 字节(其中 3 字节是 ATT 头，20 字节是实际数据)。如果只增大了 DLE 但不增大 ATT MTU，应用层数据仍然被限制在 20 字节每次操作，DLE 的优势就浪费了。

### 4.2 MTU 与 DLE 的对齐

理想情况下，ATT MTU 应该与 DLE 能力对齐，使得一个 ATT PDU 刚好装进一个链路层 PDU：

```
协议栈数据封装:
ATT Data (MTU-3 bytes)
  + ATT Header (3 bytes)
  = ATT PDU (MTU bytes)
  + L2CAP Header (4 bytes)
  = L2CAP PDU (MTU+4 bytes)
  = LL Payload

理想对齐: MTU + 4 <= MaxTxOctets
例: MaxTxOctets=251 --> MTU <= 247
```

当 ATT MTU 设为 247 时，一个 ATT PDU(247 字节)加上 L2CAP 头(4 字节)= 251 字节，刚好等于 DLE 的最大载荷。这避免了 L2CAP 分片(segmentation)，减少了额外开销。

### 4.3 MTU 协商

ATT MTU 通过 ATT_EXCHANGE_MTU_REQ/RSP 消息协商，通常在连接建立后立即进行：

```c
// nRF Connect SDK MTU 协商示例
static struct bt_gatt_exchange_params exchange_params;

static void exchange_func(struct bt_conn *conn, uint8_t err,
                          struct bt_gatt_exchange_params *params) {
    if (!err) {
        uint16_t mtu = bt_gatt_get_mtu(conn);
        printk("MTU exchange done: MTU = %u\n", mtu);
    }
}

void request_mtu_update(struct bt_conn *conn) {
    exchange_params.func = exchange_func;
    bt_gatt_exchange_mtu(conn, &exchange_params);
}
```

## 5. 批量传输优化技巧

### 5.1 Write Without Response

标准的 GATT Write 操作需要服务端回复确认(Write Response)，这引入了一个完整的往返延迟。Write Without Response 跳过了确认步骤，允许客户端连续发送多个写请求而不等待回复：

```
Write (需要确认):
Client: Write Request  --> Server
Client: <等待>         <-- Server: Write Response
Client: Write Request  --> Server
Client: <等待>         <-- Server: Write Response

Write Without Response:
Client: Write Command  --> Server
Client: Write Command  --> Server  (不等待，连续发)
Client: Write Command  --> Server
```

Write Without Response 的缺点是没有应用层的传输保证——如果链路层丢包，重传由链路层处理，但如果链路层缓冲区满，数据可能被丢弃。在可靠性要求高的场景(如 OTA 固件升级)，需要在应用层实现自己的确认机制。

### 5.2 Notification vs Indication

从服务端向客户端发送数据时有两种方式：

| 方式 | 确认 | 吞吐量 | 可靠性 |
|------|------|--------|--------|
| Notification | 无需确认 | 高 | 链路层保证 |
| Indication | 需要 Confirmation | 低 | 应用层保证 |

对于批量数据传输(如传感器数据流)，Notification 是更好的选择。

### 5.3 每个连接事件的多包传输

在一个连接事件内可以发送多个数据包，前提是在连接间隔的时间窗口内还有剩余时间。连接间隔越长，理论上单个事件内能传的包越多，但这也意味着事件之间的空闲时间更长。

```
连接间隔 7.5ms, DLE 251B, 1M PHY:
单包周期 = 2468us
7500us / 2468us = 3 个完整数据包
有效吞吐量 = 3 * 251 * 8 / 7500us = 803 kbps

连接间隔 30ms, DLE 251B, 1M PHY:
30000us / 2468us = 12 个完整数据包
有效吞吐量 = 12 * 251 * 8 / 30000us = 803 kbps
(吞吐量相同，但延迟不同)
```

### 5.4 连接间隔的选择

连接间隔对吞吐量和延迟有不同影响：

| 连接间隔 | 吞吐量 | 首包延迟 | 功耗 |
|----------|--------|---------|------|
| 7.5 ms | 最大 | 最低 | 最高 |
| 30 ms | 接近最大 | 中等 | 中等 |
| 100 ms | 较高 | 较高 | 较低 |
| 1000 ms | 受限 | 高 | 最低 |

## 6. L2CAP 信用流控

### 6.1 传统 GATT 的局限

传统 GATT 基于 ATT 协议，每次操作由客户端或服务端发起，属于请求-响应模型。对于大量连续数据传输，GATT 的效率不够理想——即使用 Write Without Response 或 Notification，每个 PDU 仍然受 ATT MTU 限制。

### 6.2 L2CAP CoC 面向连接信道

BLE 4.2 引入了 L2CAP Connection-Oriented Channels(CoC)，提供了基于信用的流量控制机制。这种方式类似于 TCP 的流控思想：

```
L2CAP CoC 流控过程:
1. 双方建立 L2CAP 连接，各自声明接收缓冲区大小
2. 接收方给发送方分配初始信用(credits)
3. 发送方每发一个 SDU，消耗一个信用
4. 接收方处理完数据后，补充新的信用
5. 发送方信用为零时暂停发送
```

### 6.3 L2CAP CoC 的优势

- **流量控制**：避免接收端缓冲区溢出
- **大 SDU 支持**：SDU 最大可达 65535 字节，自动在 L2CAP 层分片
- **无 ATT 开销**：绕过 GATT/ATT 层，减少协议栈开销
- **适合流式传输**：传感器数据流、文件传输等场景

## 7. 各平台 DLE 支持

### 7.1 嵌入式平台

```c
// Zephyr / nRF Connect SDK 启用 DLE
// prj.conf 中设置:
// CONFIG_BT_CTLR_DATA_LENGTH_MAX=251
// CONFIG_BT_BUF_ACL_TX_SIZE=251
// CONFIG_BT_BUF_ACL_RX_SIZE=251

void request_data_length_update(struct bt_conn *conn) {
    struct bt_conn_le_data_len_param param = {
        .tx_max_len = 251,
        .tx_max_time = 2120,
    };
    int err = bt_conn_le_data_len_update(conn, &param);
    if (err) {
        printk("DLE update request failed (err %d)\n", err);
    }
}
```

### 7.2 Android

Android 从 API 21(Android 5.0)开始支持 BLE，但 DLE 支持的关键是调用 requestMtu()。Android 的 BLE 协议栈在 MTU 协商成功后会自动触发 DLE 协商：

```java
// Android DLE 间接触发
// 请求 MTU 时，协议栈自动协商 DLE
bluetoothGatt.requestMtu(247);
// 注意: 不需要显式调用 DLE API
// Android 协议栈会根据 MTU 自动设置 DLE 参数
```

### 7.3 iOS

iOS 从 iOS 10 开始自动协商 DLE。开发者不需要(也无法)显式请求 DLE——iOS 的 CoreBluetooth 框架在连接建立后自动与对端协商最大数据长度。开发者只需关注 ATT MTU 的协商。

## 8. 实际性能测量

### 8.1 测试方法

使用 Nordic nRF52840 DK 进行吞吐量测试，固件基于 nRF Connect SDK 的 throughput 示例：

| 测试配置 | 实测吞吐量 | 理论值 | 效率 |
|----------|-----------|--------|------|
| 无 DLE, 1M PHY, CI=7.5ms | 约 260 kbps | 319 kbps | 81% |
| 有 DLE, 1M PHY, CI=7.5ms | 约 700 kbps | 813 kbps | 86% |
| 有 DLE, 2M PHY, CI=7.5ms | 约 1400 kbps | 1438 kbps | 97% |

实测值低于理论值的原因：协议栈处理延迟、连接事件间的调度开销、偶发重传等。

### 8.2 OTA 固件升级场景

OTA DFU 是 DLE 优化效果最直观的场景。以 100KB 固件镜像为例：

```
无 DLE (1M PHY):
有效速率约 260 kbps = 32.5 KB/s
传输时间: 100KB / 32.5 KB/s = 约 3 秒纯传输
加上校验、重启等开销: 约 50 秒总时间

有 DLE + 2M PHY:
有效速率约 1400 kbps = 175 KB/s
传输时间: 100KB / 175 KB/s = 约 0.6 秒纯传输
加上校验、重启等开销: 约 8 秒总时间
```

从 50 秒降到 8 秒，这对用户体验的改善是巨大的。

## 9. 吞吐量优化清单

以下是一份完整的吞吐量优化检查清单，按影响程度排序：

| 优化项 | 预期提升 | 实施难度 | 注意事项 |
|--------|---------|---------|---------|
| 启用 DLE (251B) | 2-3x | 低 | 检查双端都支持 |
| 使用 2M PHY | 1.5-2x | 低 | 减少覆盖范围 |
| 增大 ATT MTU | 配合 DLE | 低 | MTU=247 对齐 DLE |
| 缩短连接间隔 | 减少延迟 | 低 | 增加功耗 |
| Write Without Response | 1.5-2x | 中 | 需要应用层确认 |
| L2CAP CoC | 额外 10-20% | 高 | 平台支持有限 |

## 总结

DLE 是 BLE 4.2 引入的最具实际影响力的特性之一。通过将单包载荷从 27 字节扩展到 251 字节，它将有效载荷比从约 73% 提升到 96%，显著减少了协议开销。配合 BLE 5.0 的 2M PHY、合理的 ATT MTU 配置和批量传输策略，BLE 的实测吞吐量可以从最初的约 260kbps 提升到 1.4Mbps 以上——提升幅度超过 5 倍。关键在于每一层协议栈的参数都要对齐：DLE 的 MaxTxOctets、ATT MTU 和连接间隔三者配合，才能释放出完整的性能潜力。

## 参考文献

- Bluetooth Core Specification v5.4, Vol 6 Part B Section 4.5.10: Data PDU Length Management, Bluetooth SIG, 2023
- Nordic Semiconductor, "Optimizing BLE Throughput," Application Note AN-152, 2022
- Gomez, C., et al., "Overview and Evaluation of Bluetooth Low Energy: An Emerging Low-Power Wireless Technology," Sensors, 2012
- Apple Developer Documentation, "Core Bluetooth Best Practices," 2023
- Android Developer Documentation, "Bluetooth Low Energy Overview," 2023
