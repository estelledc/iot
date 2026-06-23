# DECT-2020 NR：从无绳电话到工业物联网的蜕变

> 难度：🟡 中级 | 领域：短距无线通信、工业物联网 | 更新：2025-06

---

## 一句话总结

DECT-2020 NR 是 DECT（数字增强无绳通信）标准的最新演进，它从一个"家用无绳电话协议"脱胎换骨为 ITU-R 认可的 5G 物联网技术，核心能力是无需基础设施即可自组 mesh 网络，在 1.9 GHz 免授权频段提供低于 1 ms 的确定性延迟。

---

## 从日常场景说起

你家里可能用过无绳电话——一个基座连着电话线，手持话机可以拿着在家里走动。这个无绳通信用的就是 DECT 技术，在欧洲几乎每个家庭都有。

现在想象一个大型工厂：几千个传感器分布在车间各处，测量温度、振动、压力。你需要一个无线网络把它们连起来，但工厂的特殊性在于——金属设备密集（信号反射严重）、不允许随意部署基站（安全合规），而且某些控制信号必须在 1 毫秒内送达（否则机器可能失控）。

DECT-2020 NR 就是为这种场景设计的：你把传感器撒在工厂里，它们会自动互相发现、自组网络、自选路由，不需要预先部署任何基础设施（AP、网关、基站都不需要）。就像一群人在没有电话网络的荒野里用对讲机自发组成通讯链——每个人既是用户也是中继站。

这种"自治"能力是 DECT-2020 NR 最独特的卖点，Thread 和 Zigbee 也能组 mesh，但它们没有 DECT-2020 NR 的延迟保证和频谱优势。

---

## 1. DECT 的前世今生

### 1.1 从无绳电话到 5G 标准

DECT（Digital Enhanced Cordless Telecommunications）的历史可以追溯到 1992 年，最初是欧洲电信标准化协会（ETSI）为家用/企业无绳电话设计的标准。

| 阶段 | 时间 | 特征 |
|------|------|------|
| DECT 1.0 | 1992 | 家用无绳电话，语音通信 |
| DECT 6.0 | 2005 | 北美版本，2.4 GHz 避让 |
| DECT ULE | 2011 | 超低功耗扩展，智能家居 |
| DECT-2020 NR | 2020 | 全新物理层和 MAC 层，面向工业 IoT |
| ITU-R IMT-2020 | 2022 | 被 ITU 接受为 5G mMTC/URLLC 技术 |

关键转折点：2022 年，ITU-R 将 DECT-2020 NR 正式纳入 IMT-2020（即 5G）技术族，使其成为唯一一个运行在免授权频段的 5G 标准。这意味着它在理论上与 3GPP NR（运营商 5G）有同等的"5G"身份地位。

### 1.2 为什么不直接用 Thread/Zigbee/BLE Mesh？

既然 mesh 网络不是新概念，DECT-2020 NR 凭什么要"重新发明轮子"？答案在于三个维度的差距：

| 维度 | DECT-2020 NR | Thread 1.3 | Zigbee 3.0 | BLE Mesh |
|------|-------------|-----------|-----------|---------|
| 频段 | 1.9 GHz (专用) | 2.4 GHz (拥挤) | 2.4 GHz (拥挤) | 2.4 GHz (拥挤) |
| 端到端延迟 | < 1 ms (保证) | 10-100 ms | 20-200 ms | 50-500 ms |
| 单网络节点数 | > 10,000 | ~250 (理论) | ~65,000 (理论 200 实际) | ~32,000 (理论) |
| 需要协调器/边界路由器 | 不需要 | 需要 | 需要 | 不需要 (但需 provisioner) |
| 网络自组织 | 全自治 | 半自治 | 需要预配置 | 需要 provisioning |
| 频谱干扰风险 | 极低 | 高 (WiFi 共存) | 高 (WiFi 共存) | 高 (WiFi 共存) |

1.9 GHz DECT 频段是 DECT-2020 NR 最大的"护城河"：这个频段在全球大部分地区被专门留给 DECT 使用，几乎没有其他技术与之竞争。而 2.4 GHz ISM 频段则是 WiFi、BLE、Zigbee、Thread 的"战场"，干扰严重。

---

## 2. 物理层架构

### 2.1 OFDM + 灵活子载波

DECT-2020 NR 采用 OFDM（正交频分复用）调制，与 WiFi 和 4G/5G 类似。但它的子载波间距可以灵活配置：

| 子载波间距 | 符号时间 | 适用场景 |
|-----------|---------|---------|
| 27.78 kHz | 36 μs | 默认模式，覆盖与速率平衡 |
| 55.56 kHz | 18 μs | 低延迟模式，工业控制 |

信道带宽固定为 1.728 MHz（包含 64 个子载波），可以把多个信道绑定以提升速率。

### 2.2 调制与编码

| MCS | 调制 | 编码率 | 单信道速率 |
|-----|------|--------|----------|
| 0 | BPSK | 1/2 | ~0.6 Mbps |
| 1 | QPSK | 1/2 | ~1.2 Mbps |
| 2 | QPSK | 3/4 | ~1.8 Mbps |
| 3 | 16-QAM | 1/2 | ~2.4 Mbps |
| 4 | 16-QAM | 3/4 | ~3.6 Mbps |
| 5 | 64-QAM | 2/3 | ~4.8 Mbps |
| 6 | 64-QAM | 3/4 | ~5.4 Mbps |

多信道绑定时，最大速率可达数十 Mbps。对于大部分 IoT 场景，单信道的 Mbps 级速率已经绰绰有余。

### 2.3 覆盖距离

1.9 GHz 频段的传播特性介于 Sub-GHz 和 2.4 GHz 之间：

- 室内（办公室/工厂）：30-50 m 单跳，mesh 可扩展到数百米
- 室外视距（LOS）：300 m-1 km
- 穿墙能力：优于 2.4 GHz WiFi，但不如 Sub-GHz（LoRa/HaLow）

---

## 3. Mesh 自组网：核心竞争力

### 3.1 无基础设施运行

DECT-2020 NR 最革命性的设计是**完全去中心化**的网络架构。在一个 DECT-2020 NR 网络中：

- 每个节点都可以充当路由器（relay）
- 不需要预先指定协调器、根节点或边界路由器
- 节点开机后自动发现邻居、建立路由表
- 节点加入和离开不影响网络其他部分（自愈）

```
传统星型网络（WiFi/LoRa）：          DECT-2020 NR mesh：

     [AP/网关]                    [A]---[B]---[C]
    / | | | \                      |  \  |  /  |
  [1][2][3][4][5]                 [D]---[E]---[F]
                                   |  /  |  \  |
AP 故障 = 全部断连               [G]---[H]---[I]

                                 任一节点故障 = 自动绕行
```

### 3.2 路由机制

DECT-2020 NR 的路由协议设计兼顾了延迟确定性和能效：

**路由建立过程**：

1. 节点上电，在 DECT 频段上扫描信标（beacon）
2. 如果发现已有网络，发送关联请求加入
3. 如果没有发现网络，自己成为"集群头"（cluster head），开始发送信标
4. 路由表通过周期性的邻居发现和路径度量（信号质量 + 跳数 + 负载）维护

**关键路由特性**：

- **多路径冗余**：每个目的地维护多条路径，主路径故障时瞬间切换
- **QoS 感知路由**：延迟敏感的控制流量走最短路径，大数据流量走负载较轻的路径
- **最大跳数**：标准建议不超过 5-7 跳，以保证端到端延迟

### 3.3 延迟保证机制

DECT-2020 NR 如何实现 < 1 ms 的确定性延迟？关键在于时分复用（TDMA）和精确的时间同步：

```
时间帧结构 (10 ms 周期)：

├─ Slot 0 ─┤─ Slot 1 ─┤─ Slot 2 ─┤─...─┤─ Slot N ─┤
│  同步/信标 │  控制数据  │  用户数据  │     │  用户数据  │
│  (固定)    │  (预留)    │  (调度)    │     │  (调度)    │

每个 slot 的时长可配置为 0.625 ms / 1.25 ms / 2.5 ms
```

调度器知道每个 slot 的分配，因此可以保证数据包在确定的时间内被传输。这与 WiFi 的 CSMA/CA（"碰运气"竞争）有本质区别。

---

## 4. 与 3GPP 5G NR 的关系

### 4.1 同为 5G，有何不同？

| 特性 | DECT-2020 NR | 3GPP 5G NR |
|------|-------------|-----------|
| 标准组织 | ETSI | 3GPP |
| 频谱 | 1.9 GHz 免授权 | 授权频谱 (sub-6G + mmWave) |
| 基础设施 | 不需要 (mesh) | 需要基站和核心网 |
| 部署成本 | 极低 (设备即网络) | 极高 (数百万美元) |
| 覆盖范围 | 数百米 (mesh) | 数公里 (宏站) |
| 峰值速率 | 数十 Mbps | 数 Gbps |
| 目标场景 | mMTC, URLLC (局部) | eMBB, mMTC, URLLC |
| 运营模式 | 自运营 (企业) | 运营商运营 |

简而言之，3GPP 5G NR 是"运营商的 5G"，DECT-2020 NR 是"企业自己的 5G"。两者在频谱、成本、部署模式上完全不同，但在 ITU 的框架中被视为互补的技术。

### 4.2 DECT-2020 NR 满足的 5G 指标

| IMT-2020 指标 | 要求 | DECT-2020 NR 表现 |
|--------------|------|-----------------|
| 连接密度 | 100 万设备/km² | 100 万+ (理论) |
| 用户面延迟 | 1 ms (URLLC) | < 1 ms |
| 可靠性 | 99.999% | 99.999% (mesh 冗余) |
| 移动性 | 支持 | 有限 (步行速度) |
| 频谱效率 | — | 较低 (窄带) |

---

## 5. 芯片与开发生态

### 5.1 Nordic nRF9161：首款商用芯片

Nordic Semiconductor 在 2023 年发布了 nRF9161 SiP（System in Package），是业界首款同时支持 LTE-M/NB-IoT 和 DECT NR+ 的芯片：

| 参数 | 值 |
|------|-----|
| 蜂窝 | LTE-M, NB-IoT (3GPP Release 14) |
| DECT NR+ | ETSI TS 103 636 |
| 处理器 | Arm Cortex-M33, 64 MHz |
| 闪存/RAM | 1 MB Flash / 256 KB RAM |
| GNSS | GPS, GLONASS, Galileo, BeiDou |
| 功耗 (DECT NR+ TX) | ~70 mA @ 19 dBm |
| 功耗 (深度睡眠) | < 2 μA |
| 封装 | 10×16 mm LGA |

Nordic 的 nRF Connect SDK 提供了 DECT NR+ 的完整协议栈，开发者可以用 Zephyr RTOS 编写应用。下面是一个最小的 DECT NR+ 数据发送示例：

```c
/* DECT NR+ 最小发送示例 (基于 nRF Connect SDK) */
#include <zephyr/kernel.h>
#include <nrf_modem_dect_phy.h>

#define DECT_CARRIER  1677  /* 1.9 GHz 频段中的载波号 */
#define TX_POWER_DBM  19

static uint8_t tx_buf[] = "Hello DECT-2020 NR!";

/* PHY 回调 */
void dect_phy_evt_handler(const struct nrf_modem_dect_phy_evt *evt) {
    switch (evt->id) {
    case NRF_MODEM_DECT_PHY_EVT_TX_COMPLETE:
        printk("TX complete, status=%d\n", evt->tx_complete.status);
        break;
    case NRF_MODEM_DECT_PHY_EVT_RX:
        printk("RX: len=%d, rssi=%d dBm\n",
               evt->rx.data_length, evt->rx.rssi_2 / 2);
        break;
    }
}

void main(void) {
    int err = nrf_modem_dect_phy_init(&(struct nrf_modem_dect_phy_init_params){
        .evt_handler = dect_phy_evt_handler,
    });
    if (err) { printk("DECT init failed: %d\n", err); return; }

    struct nrf_modem_dect_phy_tx_params tx_params = {
        .carrier = DECT_CARRIER,
        .network_id = 0x12345678,
        .phy_type = NRF_MODEM_DECT_PHY_HEADER_TYPE_1,
        .mcs = 1,  /* QPSK 1/2 */
        .data = tx_buf,
        .data_size = sizeof(tx_buf),
        .power = TX_POWER_DBM,
    };

    nrf_modem_dect_phy_tx(&tx_params);
    k_sleep(K_FOREVER);
}
```

### 5.2 开发板

- **Nordic nRF9161 DK**：$120 左右，含板载天线，支持 DECT NR+ 和 LTE-M/NB-IoT 双模
- **Nordic Thingy:91 X**：紧凑型原型开发板，含传感器套件
- **第三方模组**：陆续有厂商基于 nRF9161 推出 DECT NR+ 模组

---

## 6. 应用场景深度分析

### 6.1 工业自动化

这是 DECT-2020 NR 的主战场。一个典型的工厂部署场景：

```
大型车间 (200m × 100m)：

   [传感器]──[传感器]──[传感器]──[传感器]
       │          │          │          │
   [传感器]──[路由节点]──[路由节点]──[传感器]
       │          │          │          │
   [传感器]──[路由节点]──[网关节点]──[传感器]
       │          │          │    ↓     │
   [传感器]──[传感器]──[传感器]  [以太网]  [传感器]
                                 ↓
                            [工厂MES]

无需布线 / 无需 AP / 自动 mesh / < 1ms 延迟
```

优势：传统工厂如果要给每个设备拉网线，布线成本往往占项目总成本的 60-80%。DECT-2020 NR 的 mesh 完全消除了这个成本。

### 6.2 智慧楼宇

暖通空调（HVAC）、照明控制、消防报警等系统通常各自独立部署，DECT-2020 NR 可以用一个统一的 mesh 网络覆盖所有子系统：

- 温湿度传感器每分钟上报数据（低功耗模式）
- 消防报警传感器需要 < 10 ms 延迟（高优先级模式）
- 照明控制需要双向通信（开关指令 + 状态反馈）

所有这些在同一个 DECT-2020 NR 网络中通过 QoS 分级共存。

### 6.3 不适合的场景

- **需要运营商覆盖的广域 IoT**：DECT-2020 NR 是局域技术，覆盖不了城市级别
- **极高带宽需求**：视频监控等场景还是需要 WiFi 或 5G NR
- **已有成熟 WiFi 基础设施的场所**：如果 WiFi 已经部署完善，加一层 DECT 增加了管理复杂度

---

## 7. 实践建议

### 7.1 初学者入门路径

1. **理解背景**：先读 ETSI 的 DECT-2020 NR 概述文档（ETSI TR 103 636-1），了解协议族的整体架构
2. **入手开发板**：购买 Nordic nRF9161 DK（约 $120），安装 nRF Connect SDK
3. **跑通 PHY 层示例**：先实现两块板之间的 DECT NR+ 点对点通信
4. **尝试 mesh**：用 3-5 块板搭建简单的 mesh 网络，观察自组网过程
5. **性能测试**：测量不同跳数下的端到端延迟，验证 < 1 ms 的承诺
6. **对比实验**：用 BLE Mesh 做同样的拓扑，对比延迟和可靠性

### 7.2 具体调优建议

- **载波选择**：1.9 GHz DECT 频段有多个载波，部署前先做频谱扫描，选择干扰最小的载波
- **发射功率**：室内场景通常 10-14 dBm 足够，不需要用满 19 dBm，减小功率可以降低对其他节点的干扰
- **mesh 跳数**：控制在 3-5 跳以内。超过 7 跳后延迟和可靠性会显著下降
- **节点密度**：保证每个节点至少能"看到"2-3 个邻居，这样才有冗余路径
- **固件升级策略**：利用 mesh 的多路径能力做 OTA 升级，但要错开时间，避免大量节点同时下载导致网络拥塞
- **与 LTE-M 混合部署**：nRF9161 支持 DECT NR+ 和 LTE-M 双模。可以用 DECT 做局域 mesh，LTE-M 做广域回传，实现"本地低延迟 + 远程可达"

---

## 参考文献

1. ETSI. "ETSI TS 103 636: Digital Enhanced Cordless Telecommunications (DECT-2020 New Radio)," Parts 1-6, 2023.
2. ITU-R. "IMT-2020 (5G) Detailed Specifications: DECT-2020 NR," Recommendation M.2150, 2022.
3. Nordic Semiconductor. "nRF9161 Product Specification," v1.1, 2024.
4. Nordic Semiconductor. "DECT NR+ Getting Started Guide," nRF Connect SDK Documentation, 2024.
5. S. Olsen et al., "DECT-2020 New Radio: The Next Generation Wireless Solution for Industrial IoT," IEEE Communications Magazine, vol. 62, no. 3, 2024.
6. ETSI. "ETSI TR 103 636-1: DECT-2020 NR Overview," v1.3.1, 2023.
7. P. Mogensen et al., "DECT-2020 NR: Autonomous Mesh Networking for Massive IoT," IEEE Internet of Things Journal, vol. 11, no. 5, 2024.
8. WiFi Alliance vs DECT Forum. "Comparison of IoT Wireless Technologies," DECT Forum White Paper, 2024.
9. J. Hämäläinen et al., "Performance Evaluation of DECT-2020 NR for Industrial Automation," Proc. IEEE WCNC, 2024.
10. Nordic Semiconductor. "DECT NR+ and Cellular IoT: A Dual-Mode Approach," Technical Blog, 2024.
