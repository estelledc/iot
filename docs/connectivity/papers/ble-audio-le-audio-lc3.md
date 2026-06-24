# LE Audio与LC3编解码器在IoT音频中的应用
> **难度**：🔴 高级 | **领域**：BLE音频技术 | **阅读时间**：约 22 分钟

## 引言

想象一个老式广播电台：主播对着麦克风说话，信号通过电波发出去，成千上万的收音机同时收听，没有人数限制。现在想象蓝牙耳机：手机和耳机之间建立一对一连接，一次只能给一副耳机播放。LE Audio 就像把蓝牙从打电话模式升级到了广播电台模式--既能一对一通话，也能一对多广播，同时音质更好功耗更低。

本文将解析 LE Audio 架构、LC3 编解码器原理及 IoT 音频应用。

## 1. LE Audio概述

### 1.1 从经典蓝牙音频到LE Audio

```
经典蓝牙音频(Classic Audio):
- 基于BR/EDR传输
- A2DP单向高质量 / HFP双向通话
- 强制编码器: SBC
- 仅点对点连接

LE Audio(低功耗音频):
- 基于BLE传输
- 统一框架: 流媒体+通话+广播
- 强制编码器: LC3(更高效)
- 点对点 + 广播(Auracast)
```

### 1.2 LE Audio协议栈

```
+--------------------------------------------------+
|  BAP  |  CAP  |  TMAP  |  HAP  |  PBP  |  MCP  |
| 基础  | 通用  | 电话  | 助听  | 公播  | 媒体  |
| 音频  | 音频  | 媒体  | 器    | 广播  | 控制  |
+--------------------------------------------------+
|            ASCS (音频流控制服务)                   |
+--------------------------------------------------+
|         ISO传输层 (CIS / BIS)                    |
+--------------------------------------------------+
|              LC3编解码器                           |
+--------------------------------------------------+
|          BLE链路层 (LE Isochronous)              |
+--------------------------------------------------+
```

### 1.3 核心Profile

| Profile | 全称 | 功能 |
|---------|------|------|
| BAP | Basic Audio Profile | 音频流建立和管理 |
| CAP | Common Audio Profile | 通用音频过程 |
| TMAP | Telephony and Media Audio | 通话和媒体 |
| HAP | Hearing Access Profile | 助听器接入 |
| PBP | Public Broadcast Profile | 公共广播 |

## 2. LC3编解码器

### 2.1 LC3基本参数

```
LC3关键参数:
- 采样率: 8/16/24/32/44.1/48 kHz
- 帧长: 7.5ms 或 10ms
- 比特率: 16-320 kbps
- 算法延迟: 5ms(7.5ms帧) / 7.5ms(10ms帧)

典型配置:
- 音乐: 48kHz / 96-128kbps / 10ms帧
- 通话: 16kHz / 32kbps / 10ms帧
- 广播: 48kHz / 96kbps / 10ms帧
```

### 2.2 LC3编码流程

```
输入PCM --> [MDCT变换] --> [频谱量化] --> [熵编码] --> 输出
               |               |              |
          时域转频域      比特预算分配     算术编码

帧处理示例:
- 输入: 10ms@48kHz = 480个PCM样本
- 输出: 96kbps*10ms = 120字节压缩帧
```

### 2.3 LC3 vs SBC性能

```
主观听音测试(MUSHRA评分):
| 配置          | SBC  | LC3  |
|--------------|------|------|
| 345 kbps     | 83分 |  -   |
| 160 kbps     | 68分 | 85分 |
| 96 kbps      |  -   | 76分 |
| 64 kbps      | 45分 | 65分 |

结论: LC3@160kbps 音质优于 SBC@345kbps (节省54%带宽)
```

### 2.4 计算复杂度

```c
/*
 * LC3复杂度(48kHz/10ms/96kbps):
 * - 总计约2 MOPS
 * - 对比: SBC约5 MOPS, AAC约20 MOPS
 *
 * Cortex-M4@64MHz上:
 * - 48kHz编码: 约8% CPU
 * - 16kHz编码: 约3% CPU
 * - 低复杂度 -> 适合低功耗MCU
 */
```

## 3. Isochronous通道

### 3.1 CIS(连接等时流)

CIS 用于点对点音频传输：

```
单一CIS:
[Source] ====CIS====> [Sink]

CIG(连接等时组) - 真无线立体声:
             +====CIS_L====> [左耳机]
[手机] ------+
             +====CIS_R====> [右耳机]

CIG参数: SDU间隔/传输延迟/重传次数/PHY
```

### 3.2 BIS(广播等时流)

BIS 用于一对多音频广播：

```
BIS广播(Auracast):
                    +----> [接收器1]
[广播源] ===BIS====+----> [接收器2]
                    +----> [接收器3]
                    +----> [...无限]

BIG可包含多个BIS(如多语言频道):
| BIS_1(中文) | BIS_2(英文) | BIS_3(日文) |
```

### 3.3 CIS vs BIS

| 特性 | CIS | BIS |
|------|-----|-----|
| 连接方式 | 点对点 | 一对多(无连接) |
| 接收者数量 | 有限 | 无限 |
| 方向 | 双向可能 | 仅单向 |
| 加密 | 连接级加密 | 广播密钥 |
| 典型应用 | 耳机通话 | 公共广播 |

## 4. Auracast广播音频

### 4.1 应用场景

```
机场: [广播器] --BIS(中文)--> [旅客A耳机]
               --BIS(英文)--> [旅客B耳机]

健身房: [跑步机电视] --BIS--> [用户耳机](各听各的频道)

博物馆: [展品解说器] --BIS--> [游客们耳机](替代导览器)
```

### 4.2 发现和接入流程

```
1. 广播源发送Extended Advertising(含名称/元数据)
2. 接收设备扫描发现可用广播
3. 用户选择收听的频道
4. 同步到PA(Periodic Advertising)获取BIG参数
5. 同步到BIG接收音频流
6. (加密时需Broadcast Code, 类似WiFi密码)
```

### 4.3 实现框架

```c
// Zephyr RTOS Auracast广播源框架
#include <zephyr/bluetooth/audio/bap.h>

static struct bt_bap_broadcast_source *source;

int start_auracast(void) {
    struct bt_bap_broadcast_source_param param = {
        .params_count = 1,
        .params = &subgroup_param,
        .qos = &preset_48_4_1.qos,
        .encryption = false,
    };
    return bt_bap_broadcast_source_create(&param, &source);
}

// 发送音频帧
void send_frame(struct bt_bap_stream *stream) {
    int16_t pcm[480];  // 10ms@48kHz
    uint8_t encoded[120];  // 96kbps*10ms
    audio_source_read(pcm, 480);
    lc3_encode(encoder, pcm, encoded, 120);
    // 通过ISO通道发送
    struct net_buf *buf = net_buf_alloc(&pool, K_FOREVER);
    net_buf_add_mem(buf, encoded, 120);
    bt_bap_stream_send(stream, buf, seq_num++, 0);
}
```

## 5. 助听器与多流

### 5.1 LE Audio助听器标准化

LE Audio 通过 HAP 实现助听器标准化(之前依赖Apple ASHA等私有方案)：双耳独立CIS精确同步、低延迟(目标20ms以下)、远程增益控制、环境音混合。

### 5.2 真无线立体声演进

```
经典TWS: [手机] --A2DP--> [主耳] --私有转发--> [从耳]
                                  额外延迟10-40ms

LE Audio TWS: [手机] --CIS_L--> [左耳]
                     --CIS_R--> [右耳]
              两条独立流, 左右延迟差<1ms
```

### 5.3 QoS配置

```c
// 高质量音乐
static const struct codec_qos qos_music = {
    .interval = 10000,   // 10ms
    .sdu = 120,          // 96kbps@10ms
    .rtn = 5,            // 5次重传
    .latency = 60,       // 60ms最大延迟
};

// 低延迟游戏
static const struct codec_qos qos_gaming = {
    .interval = 7500,    // 7.5ms
    .sdu = 90,           // 96kbps@7.5ms
    .rtn = 2,            // 2次重传(低延迟优先)
    .latency = 15,       // 15ms最大延迟
};
```

## 6. IoT音频应用

### 6.1 语音控制设备

```
[用户说话] --> [IoT麦克风] --> [LC3@16kHz/32kbps编码]
           --> [BLE CIS上传] --> [网关ASR识别]
           --> [结果返回] --> [设备执行+确认音广播]

功耗: 经典HFP约15mA vs LE Audio约5mA
```

### 6.2 工业安全广播

```
[中控室Auracast广播器]
  --BIS(安全警报)--> [工人A耳塞]
  --BIS(安全警报)--> [工人B耳塞]
  --BIS(紧急疏散)--> [所有设备]

优势: 无需单独配对, 新设备即戴即用, 支持分区
```

## 7. 硬件平台

### 7.1 芯片选型

| 芯片 | 厂商 | 角色 | 特点 |
|------|------|------|------|
| nRF5340 | Nordic | Source/Sink | 双核, LC3支持 |
| QCC305x | Qualcomm | Sink(TWS) | 集成ANC |
| AB1565 | Airoha | Sink(TWS) | 低成本 |
| ESP32-C6 | Espressif | Source/Sink | 开源方案 |

### 7.2 nRF5340双核架构

```
应用核(M33@128MHz): 音频处理 + LC3编解码 + 应用逻辑
网络核(M33@64MHz):  BLE协议栈 + ISO调度 + 射频控制

双核分工: 网络核专注实时BLE, 应用核全力处理音频
```

## 8. 功耗分析

### 8.1 LE Audio vs Classic功耗

```
音乐流(48kHz/96kbps):
| 指标         | A2DP   | LE Audio | 节省  |
|-------------|--------|----------|-------|
| Source电流   | 8.5mA  | 4.2mA   | 50%   |
| Sink电流     | 7.2mA  | 3.8mA   | 47%   |

TWS耳机续航(50mAh电池):
- A2DP: 50/7.2 = 6.9小时
- LE Audio: 50/3.8 = 13.2小时 (提升90%)
```

### 8.2 延迟预算

```
端到端: [采集] -> [编码] -> [传输] -> [解码] -> [播放]
          1ms    7.5ms   10-60ms   7.5ms    1ms

- 低延迟(游戏): ~30ms
- 标准(音乐): ~50-60ms
- 高可靠(广播): ~80-100ms
```

## 总结

LE Audio 代表蓝牙音频的重大飞跃。LC3 在更低码率下实现更高音质，Isochronous 通道提供可靠实时传输，Auracast 开创无限接收者的广播新范式。对 IoT 领域，低功耗特性使电池供电语音设备成为现实，广播能力为工业安全和公共信息提供全新方案。

## 参考文献

1. Bluetooth SIG, "LE Audio Specification Overview", bluetooth.com/le-audio, 2022
2. Bluetooth SIG, "LC3 Codec Specification", 2020
3. Nordic Semiconductor, "nRF5340 Audio DK User Guide", 2023
4. Bluetooth SIG, "Auracast - Broadcast Audio", auracast.bluetooth.com
5. Fraunhofer IIS, "LC3 - The Codec for LE Audio", fraunhofer.de/lc3
