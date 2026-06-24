# BLE 5.0新特性：Coded PHY与远距离通信
> **难度**：🟡 中级 | **领域**：BLE协议演进 | **阅读时间**：约 20 分钟

## 引言

想象你在一个足球场的一端喊话给另一端的朋友。正常说话（1M PHY）只能让几米内的人听清，大声喊（Coded PHY S=2）能让更远的人模糊听到，而用扩音器反复喊同一句话（Coded PHY S=8）则能让整个球场的人都听清楚——代价是说一句话的时间变长了。BLE 5.0 的 Coded PHY 就是这个"扩音器+重复"的思路：通过增加冗余编码来换取更远的通信距离。

2016 年蓝牙技术联盟（Bluetooth SIG）发布了 BLE 5.0 规范，这是自 BLE 4.0 以来最大的一次升级。它同时在速度、距离和广播数据量三个维度进行了突破，为物联网应用打开了全新的可能性。

本文将深入解析 BLE 5.0 的三大核心特性，重点讲解 Coded PHY 的工作原理和实际应用。

## 1. BLE 5.0 版本概览

### 1.1 从 BLE 4.2 到 5.0 的演进

BLE 4.2（2014年发布）引入了数据长度扩展（DLE）和隐私增强等特性，但在物理层（PHY）方面仍然只有 1Mbps 的传输速率。BLE 5.0 在物理层进行了根本性的扩展，提供了三种 PHY 模式：

| PHY 模式 | 符号速率 | 数据吞吐 | 主要优势 |
|-----------|----------|-----------|----------|
| 1M PHY（LE 1M） | 1 Msym/s | ~800 kbps | 兼容 BLE 4.x |
| 2M PHY（LE 2M） | 2 Msym/s | ~1400 kbps | 2倍速度，更省电 |
| Coded PHY S=2 | 1 Msym/s | 500 kbps | 2倍距离（+6dB） |
| Coded PHY S=8 | 1 Msym/s | 125 kbps | 4倍距离（+12dB） |

### 1.2 三大核心改进

BLE 5.0 的官方宣传语是"2x speed, 4x range, 8x advertising data"：

- **2倍速度**：2M PHY 将空中比特率提升到 2Mbps
- **4倍距离**：Coded PHY S=8 通过前向纠错编码提升链路预算 12dB
- **8倍广播数据**：扩展广播允许最多 255 字节 PDU，链式 PDU 可达更大数据量

## 2. Coded PHY 详解

### 2.1 编码原理

Coded PHY 的核心思想是用时间换可靠性。它在物理层引入了前向纠错编码（FEC），使接收端能够在信号较弱时仍然正确解码数据。

Coded PHY 的编码流程包含三个阶段：

```
原始数据 --> 卷积编码器 --> 模式映射器 --> 空中传输
(1 bit)    (1:2 编码)    (S=2或S=8)   (冗余符号)
```

**卷积编码（Convolutional Coding）**：每个输入比特经过约束长度为 4 的卷积编码器，产生 2 个输出比特。这种编码方式建立了比特之间的关联性，使得即使部分比特出错，接收端也能通过维特比（Viterbi）解码恢复原始数据。

**模式映射器（Pattern Mapper）**：

- S=2 模式：每个编码比特映射为 2 个符号，总扩展因子 = 2（卷积） x 2（映射）= 4 符号/原始比特
- S=8 模式：每个编码比特映射为 4 个符号，总扩展因子 = 2（卷积） x 4（映射）= 8 符号/原始比特

### 2.2 数据包结构

Coded PHY 的数据包结构与 1M PHY 有显著差异：

```
+----------+--------+--------+------+------+
| Preamble | CI     | TERM1  | PDU  | TERM2|
| (80 us)  | (2bit) | (3bit) | ...  | (3b) |
| S=8固定  | S=8固定| S=8固定| S=2/8| S=2/8|
+----------+--------+--------+------+------+
```

关键点：数据包的前导码（Preamble）、编码指示符（CI）和第一个终止字段（TERM1）始终使用 S=8 编码，确保接收端能可靠地检测并解码包头。CI 字段告诉接收端后续 PDU 使用 S=2 还是 S=8。

### 2.3 S=2 与 S=8 对比

```c
// 概念示意：发送同样 1 字节数据的空中时间对比
// 1M PHY:   8 bits / 1Mbps = 8 us
// Coded S=2: 8 bits * 4 symbols / 1Msym/s = 32 us (4倍时间)
// Coded S=8: 8 bits * 8 symbols / 1Msym/s = 64 us (8倍时间)
```

| 参数 | Coded S=2 | Coded S=8 |
|------|-----------|-----------|
| 有效数据率 | 500 kbps | 125 kbps |
| 链路预算增益 | +6 dB | +12 dB |
| 理论距离提升 | 约 2 倍 | 约 4 倍 |
| 单包最大空中时间 | ~4.4 ms | ~17.1 ms |
| FEC 纠错能力 | 中等 | 强 |

## 3. 前向纠错编码（FEC）机制

### 3.1 为什么需要 FEC

在传统 1M PHY 中，如果接收到的比特有错误，唯一的办法是通过 CRC 校验发现错误然后请求重传。在远距离通信中，信号衰减严重，误比特率（BER）升高，频繁重传会导致：

- 实际吞吐量大幅下降
- 延迟不可预测
- 功耗增加（每次重传都需要射频开启）

FEC 允许接收端在不需要重传的情况下纠正一定数量的比特错误。

### 3.2 卷积编码的工作方式

BLE 5.0 Coded PHY 使用的是 rate-1/2、约束长度 K=4 的卷积编码器：

```
输入比特流: b[0], b[1], b[2], ...
移位寄存器: [b[n], b[n-1], b[n-2], b[n-3]]

输出 0 = b[n] XOR b[n-1] XOR b[n-2] XOR b[n-3]  (生成多项式 g0=1111)
输出 1 = b[n] XOR b[n-2] XOR b[n-3]              (生成多项式 g1=1011)
```

每输入 1 比特，输出 2 比特——这就是"rate-1/2"的含义。输出的 2 比特之间存在数学关联，接收端利用这种关联进行纠错。

### 3.3 维特比解码

接收端使用维特比算法（Viterbi Decoder）进行最大似然解码。它的直觉是：

1. 构建一个格状图（Trellis），表示编码器所有可能的状态转移
2. 对接收到的每个符号，计算与所有可能路径的"距离"
3. 保留最可能的路径（最小累积距离）
4. 最终回溯得到最可能的原始比特序列

即使中间有若干比特被噪声翻转，只要错误不超过编码的纠错能力，维特比解码器仍能恢复正确数据。

## 4. 距离与链路预算分析

### 4.1 链路预算基础

无线通信距离由链路预算（Link Budget）决定：

```
链路预算 = 发射功率 + 天线增益 - 路径损耗 - 接收灵敏度
```

Coded PHY 的增益来自接收灵敏度的改善：

| PHY 模式 | 典型接收灵敏度 | 相对 1M 改善 |
|-----------|----------------|--------------|
| 1M PHY | -96 dBm | 基准 |
| 2M PHY | -93 dBm | -3 dB（更差） |
| Coded S=2 | -102 dBm | +6 dB |
| Coded S=8 | -108 dBm | +12 dB |

### 4.2 实际距离测试结果

以 nRF52840（发射功率 +8dBm）为例：

**室外开阔地（Line of Sight）**：

| PHY | 典型最大距离 | 备注 |
|-----|------------|------|
| 1M PHY | 100-200m | 取决于环境 |
| Coded S=2 | 200-400m | 约 2 倍 |
| Coded S=8 | 400-800m | 约 4 倍 |

**室内环境**：

| PHY | 典型可靠距离 | 场景 |
|-----|------------|------|
| 1M PHY | 20-40m | 办公室，有墙壁 |
| Coded S=2 | 40-80m | 穿 2-3 面墙 |
| Coded S=8 | 60-120m | 穿 4-5 面墙 |

### 4.3 影响实际距离的因素

实际距离会受到多种因素影响：

- **障碍物**：混凝土墙每面约衰减 10-15dB，石膏板墙 3-5dB
- **多径效应**：室内反射导致信号忽强忽弱
- **干扰**：WiFi、微波炉、其他蓝牙设备共用 2.4GHz 频段
- **天线方向**：PCB 天线有方向性，相对角度影响增益
- **人体遮挡**：人体在 2.4GHz 约衰减 3-5dB

## 5. 2M PHY 高速模式

### 5.1 2M PHY 的优势

2M PHY 将符号速率从 1Msym/s 提升到 2Msym/s，数据包空中时间减半：

```c
// 发送 251 字节 PDU 的空中时间对比
// 1M PHY: (preamble + header + payload + CRC) / 1Mbps
//       = (1 + 2 + 251 + 3) * 8 / 1M = 2056 us
// 2M PHY: (preamble + header + payload + CRC) / 2Mbps
//       = (2 + 2 + 251 + 3) * 8 / 2M = 1032 us
```

空中时间减少意味着：

- **更省电**：射频模块开启时间更短
- **更高吞吐**：单位时间能传更多数据
- **更少碰撞**：数据包占用信道时间更短，多设备共存更好

### 5.2 适用场景

- **音频传输**：BLE Audio（LE Audio）标准利用 2M PHY 传输高质量音频
- **固件升级（OTA DFU）**：大数据量传输场景，2M PHY 可将升级时间减半
- **高频传感器数据**：加速度计、陀螺仪等高采样率传感器
- **图像传输**：低分辨率图像的 BLE 传输

### 5.3 2M PHY 的限制

- **距离更短**：接收灵敏度比 1M PHY 差约 3dB
- **不支持 Coded 编码**：没有 FEC 纠错能力
- **兼容性**：BLE 4.x 设备不支持 2M PHY

## 6. 扩展广播（Extended Advertising）

### 6.1 传统广播的限制

BLE 4.x 的广播数据限制在 31 字节（AD 结构中可用约 28 字节），这对很多场景不够用：

- 设备名称 + UUID 就可能超出限制
- 无法在广播中包含丰富的传感器数据
- Beacon 应用受限于数据量

### 6.2 扩展广播架构

BLE 5.0 引入了双层广播架构：

```
主广播信道（37/38/39）        数据信道（0-36）
+------------------+         +-------------------+
| ADV_EXT_IND      |-------->| AUX_ADV_IND      |
| (指向辅助包)     |         | (最多 255 字节)   |
+------------------+         +-------------------+
                                      |
                             +-------------------+
                             | AUX_CHAIN_IND    |
                             | (链式扩展)       |
                             +-------------------+
```

### 6.3 关键改进

- **广播集（Advertising Sets）**：设备可以同时运行多个独立的广播集，每个有不同的参数和数据
- **辅助信道广播**：主广播包仅包含指针信息，实际数据在数据信道上发送
- **链式 PDU**：多个 AUX_CHAIN_IND 串联，理论最大数据量可达 1650+ 字节
- **灵活 PHY 选择**：辅助广播包可以使用 1M、2M 或 Coded PHY

### 6.4 周期性广播（Periodic Advertising）

BLE 5.0 还引入了周期性广播，允许接收端与广播端同步，只在预定时刻唤醒接收：

```
广播端: |--ADV--|-----------|--ADV--|-----------|--ADV--|
接收端: |      |--sleep----|--RX--|--sleep----|--RX--|
         同步后只在广播时刻开启接收，极大节省功耗
```

## 7. 硬件支持情况

### 7.1 主流芯片支持

| 芯片 | 厂商 | 1M | 2M | Coded S=2 | Coded S=8 | Ext Adv |
|------|------|----|----|-----------|-----------|---------|
| nRF52840 | Nordic | Y | Y | Y | Y | Y |
| nRF5340 | Nordic | Y | Y | Y | Y | Y |
| CC2652R | TI | Y | Y | Y | Y | Y |
| EFR32BG22 | Silicon Labs | Y | Y | Y | Y | Y |
| ESP32-C3 | Espressif | Y | Y | N | N | Y |
| STM32WB55 | ST | Y | Y | Y | Y | Y |

### 7.2 注意事项

- 并非所有 BLE 5.0 芯片都支持全部特性，需查阅具体数据手册
- Coded PHY 需要双方（Central 和 Peripheral）都支持
- 手机端支持：Android 8.0+ 部分支持，iOS 不公开 Coded PHY API

## 8. 软件配置示例

### 8.1 Zephyr RTOS 中的 PHY 配置

```c
// prj.conf 中启用 Coded PHY 支持
// CONFIG_BT=y
// CONFIG_BT_CTLR_PHY_CODED=y
// CONFIG_BT_USER_PHY_UPDATE=y

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/hci.h>

// 连接建立后请求切换 PHY
void request_coded_phy(struct bt_conn *conn)
{
    struct bt_conn_le_phy_param phy_param = {
        .options = BT_CONN_LE_PHY_OPT_CODED_S8,
        .pref_tx_phy = BT_GAP_LE_PHY_CODED,
        .pref_rx_phy = BT_GAP_LE_PHY_CODED,
    };

    int err = bt_conn_le_phy_update(conn, &phy_param);
    if (err) {
        printk("PHY update request failed (err %d)\n", err);
    }
}

// PHY 更新完成回调
void phy_updated(struct bt_conn *conn,
                 struct bt_conn_le_phy_info *param)
{
    printk("PHY updated: TX PHY %u, RX PHY %u\n",
           param->tx_phy, param->rx_phy);
}

// 注册回调
static struct bt_conn_cb conn_callbacks = {
    .le_phy_updated = phy_updated,
};
```

### 8.2 PHY 协商流程

PHY 更新是一个协商过程，不是单方面决定：

```
Central                          Peripheral
   |                                 |
   |<-- LL_PHY_REQ (preferred PHY) --|
   |                                 |
   |-- LL_PHY_UPDATE_IND ----------->|
   |   (actual PHY to use)           |
   |                                 |
   |=== 新 PHY 生效的时间点 =========|
   |                                 |
```

双方都可以发起 PHY 更新请求，但最终由 Central 决定使用哪种 PHY。如果 Central 不支持请求的 PHY，会回退到双方都支持的模式。

## 9. 设计权衡与选型指南

### 9.1 Coded PHY 的权衡

**优势**：
- 无需增加发射功率即可延长距离
- FEC 减少重传次数，在高噪声环境中反而更省电
- 向后兼容同一硬件（软件切换）

**劣势**：
- 数据包空中时间更长，占用信道时间更多
- 单包功耗更高（射频开启时间长）
- 在多设备密集部署时增加碰撞概率
- 吞吐量显著降低

### 9.2 PHY 选择决策树

```
需要最远距离?
  |-- 是 --> Coded S=8（牺牲速度换距离）
  |-- 否 --> 需要高吞吐?
                |-- 是 --> 2M PHY（牺牲距离换速度）
                |-- 否 --> 需要穿墙?
                             |-- 是 --> Coded S=2（平衡选择）
                             |-- 否 --> 1M PHY（兼容性最好）
```

### 9.3 典型应用场景对应

| 应用场景 | 推荐 PHY | 理由 |
|----------|----------|------|
| 仓库资产追踪 | Coded S=8 | 大空间，低数据量 |
| 农业传感器 | Coded S=8 | 远距离，低频数据 |
| 跨楼层建筑自动化 | Coded S=2 | 穿透力+合理速度 |
| BLE 音频串流 | 2M PHY | 高吞吐低延迟 |
| 固件空中升级 | 2M PHY | 大数据量快速传输 |
| 可穿戴设备 | 1M PHY | 近距离，兼容性优先 |

## 10. 实际部署建议

### 10.1 距离测试方法

部署前务必进行实地测试：

1. **使用 RSSI 和 PER 作为指标**：不仅看最远距离，更要看丢包率
2. **测试最差情况**：人员走动时、多设备同时通信时
3. **预留 6-10dB 余量**：环境变化（湿度、温度）会影响传播
4. **测试不同方向**：天线方向性在实际产品中常被忽略

### 10.2 混合 PHY 策略

实际产品可以动态切换 PHY：

```c
// 伪代码：根据 RSSI 动态调整 PHY
void adaptive_phy_selection(int8_t rssi)
{
    if (rssi > -60) {
        // 信号好，用 2M PHY 追求速度
        request_phy(PHY_2M);
    } else if (rssi > -85) {
        // 信号中等，用 1M PHY 保持兼容
        request_phy(PHY_1M);
    } else {
        // 信号弱，切换 Coded PHY 保持连接
        request_phy(PHY_CODED_S8);
    }
}
```

## 总结

BLE 5.0 通过引入多 PHY 模式，将 BLE 从"近距离低功耗"扩展为"可按需调节的灵活无线技术"。三种 PHY 模式的核心关系是一个三角权衡：距离、速度、功耗——选择任何一个方向的优化，都意味着在其他方向做出让步。

关键要点回顾：

- Coded PHY 通过 FEC 编码提升接收灵敏度，以时间换距离
- S=2 提供 +6dB 增益（约 2 倍距离），S=8 提供 +12dB 增益（约 4 倍距离）
- 2M PHY 减少空中时间，适合高吞吐和低功耗场景
- 扩展广播突破 31 字节限制，支持丰富的无连接数据传输
- 实际选型需根据具体场景的距离、吞吐、功耗需求综合决策

## 参考文献

1. Bluetooth SIG. "Bluetooth Core Specification v5.0." 2016. https://www.bluetooth.com/specifications/specs/core-specification-5-0/
2. Nordic Semiconductor. "nRF52840 Product Specification." https://infocenter.nordicsemi.com/topic/ps_nrf52840/
3. Bluetooth SIG. "Bluetooth 5 - New Features for IoT." Bluetooth Technology Website.
4. Afaneh, M. "BLE 5.0 Long Range - Coded PHY." Novel Bits Blog, 2020.
5. Nordic Semiconductor. "Developing Bluetooth 5 Long Range Applications with nRF Connect SDK." Application Note, 2021.
