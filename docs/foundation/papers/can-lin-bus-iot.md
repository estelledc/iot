---
schema_version: '1.0'
id: can-lin-bus-iot
title: CAN/LIN 总线在 IoT 中的应用
layer: 1
content_type: UNKNOWN
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# CAN/LIN 总线在 IoT 中的应用

> **难度**：🟡 中级 | **领域**：工业通信、车联网 | **阅读时间**：约 20 分钟

## 日常类比

想象一个公司的会议室只有一个麦克风（共享总线）。所有人都想发言，怎么办？CAN 总线的方案是：每个人举手时同时喊出自己的"优先级编号"，编号最小的人获得发言权，其他人自动退让——而且这个过程不会产生冲突（非破坏性仲裁）。LIN 总线更简单：有一个主持人（Master）按顺序点名，被点到的人才能说话。

在 IoT 场景中，CAN 总线就像工厂车间里连接几十个传感器和执行器的"神经网络"——可靠、实时、抗干扰。LIN 总线则像汽车里连接车窗、座椅调节等不那么紧急的设备的"经济型网络"。这篇文章将深入解析这两种总线协议在 IoT 中的应用。

## 1. CAN 总线基础架构

### 1.1 物理层

CAN 使用差分信号传输（CAN_H 和 CAN_L），这是它抗干扰能力强的根本原因：

```
CAN_H:  ___/---\___/---\___     显性(0): CAN_H=3.5V, CAN_L=1.5V, 差值=2V
CAN_L:  ---\___/---\___/---     隐性(1): CAN_H=2.5V, CAN_L=2.5V, 差值=0V

总线空闲 = 隐性状态
任何节点拉低 = 显性状态（0 覆盖 1）
```

关键参数：

| 参数 | CAN 2.0 | CAN FD | CAN XL |
|------|---------|--------|--------|
| 最大速率 | 1 Mbps | 8 Mbps (数据段) | 20 Mbps |
| 仲裁段速率 | 1 Mbps | 1 Mbps | 1 Mbps |
| 数据长度 | 0-8 字节 | 0-64 字节 | 0-2048 字节 |
| 总线长度@1Mbps | 40 m | 40 m | 40 m |
| 总线长度@125kbps | 500 m | 500 m | 500 m |
| 节点数 | 最多 127 | 最多 127 | 最多 127 |
| 错误检测 | 15-bit CRC | 17/21-bit CRC | 32-bit CRC |

### 1.2 帧格式

CAN 2.0 标准帧结构：

```
| SOF | 仲裁段(11-bit ID) | RTR | IDE | r0 | DLC(4) | 数据(0-8B) | CRC(15) | ACK | EOF |
  1b       11 bits          1b   1b   1b    4b       0-64 bits     15b       2b   7b
```

CAN FD 的改进：数据段可以切换到更高速率（Bit Rate Switch），数据长度扩展到 64 字节。

### 1.3 非破坏性仲裁

CAN 的精髓在于仲裁机制——多个节点同时发送时，ID 值最小的自动获胜：

```c
// 仲裁过程示意（位级别）
// 节点 A 发送 ID = 0x123 = 0001 0010 0011
// 节点 B 发送 ID = 0x125 = 0001 0010 0101
// 节点 C 发送 ID = 0x120 = 0001 0010 0000

// 逐位比较（显性0覆盖隐性1）：
// Bit 10: A=0, B=0, C=0 -> 总线=0, 三者继续
// Bit 9:  A=0, B=0, C=0 -> 总线=0, 三者继续
// Bit 8:  A=0, B=0, C=0 -> 总线=0, 三者继续
// Bit 7:  A=1, B=1, C=1 -> 总线=1, 三者继续
// ...
// Bit 2:  A=0, B=1, C=0 -> 总线=0, B 检测到冲突退出
// Bit 1:  A=1, C=0      -> 总线=0, A 检测到冲突退出
// Bit 0:  C=0           -> C 获胜！

// 结果：ID 最小的节点 C (0x120) 获得总线访问权
// 关键：失败的节点没有破坏任何数据，可以在下一轮重试
```

## 2. CAN 2.0 vs CAN FD vs CAN XL

### 2.1 演进动机

CAN 2.0 的 8 字节数据限制在现代应用中越来越捉襟见肘。一个典型的 IoT 传感器数据包可能包含：时间戳(4B) + 传感器ID(2B) + 数据(4-20B) + 校验(2B) = 12-28 字节。CAN 2.0 需要拆成多帧传输，增加了延迟和复杂度。

### 2.2 CAN FD 的双速率机制

```
仲裁段 (1 Mbps)          数据段 (8 Mbps)         仲裁段 (1 Mbps)
|<-- 低速保证仲裁 -->|<-- 高速传数据 -->|<-- 低速确认 -->|

[SOF][ID][BRS=1][ESI][DLC]  [DATA 0-64 bytes]  [CRC][ACK][EOF]
         ^                                        ^
         |-- Bit Rate Switch 标志                 |-- 切回低速
```

### 2.3 CAN XL：面向未来

CAN XL（2024 年标准化）是最新一代，主要面向汽车以太网过渡期：

| 特性 | CAN FD | CAN XL |
|------|--------|--------|
| 最大数据 | 64 字节 | 2048 字节 |
| 数据段速率 | 8 Mbps | 20 Mbps |
| 以太网兼容 | 否 | 可封装以太网帧 |
| 安全特性 | 无 | 内置 MAC 认证 |
| 向后兼容 | CAN 2.0 | CAN FD + CAN 2.0 |

## 3. LIN 总线基础

### 3.1 LIN 的定位

LIN（Local Interconnect Network）是 CAN 的低成本补充，用于不需要高速和高可靠性的场景：

| 对比维度 | CAN | LIN |
|---------|-----|-----|
| 拓扑 | 多主 | 单主多从 |
| 速率 | 1 Mbps | 20 kbps |
| 物理层 | 差分双线 | 单线 + 地 |
| 成本/节点 | 约 5 元 | 约 1 元 |
| 节点数 | 127 | 16 |
| 同步 | 需要晶振 | 从节点可用 RC 振荡器 |
| 典型应用 | 发动机控制、ABS | 车窗、座椅、雨刷 |

### 3.2 LIN 帧格式

```
主节点发送:  [Break][Sync(0x55)][PID]
从节点响应:  [Data 1-8 bytes][Checksum]

Break: 至少 13 个显性位（同步用）
Sync:  0x55 = 01010101（从节点用此校准波特率）
PID:   6-bit ID + 2-bit 奇偶校验
```

### 3.3 LIN 在 IoT 中的新应用

虽然 LIN 最初为汽车设计，但其低成本特性使它在 IoT 中找到新用途：

- 智能建筑：连接窗帘电机、灯光调节器（不需要高速）
- 农业 IoT：连接土壤传感器阵列（单线布线简单）
- 工业传感器网络：低速环境监测（温湿度、气压）

## 4. 错误处理机制

### 4.1 CAN 的五层错误检测

CAN 协议内置了极其强大的错误检测机制，残余错误率低于 4.7 * 10^-11：

1. **位监控**：发送节点同时监听总线，发现不一致立即报错
2. **位填充**：连续 5 个相同位后自动插入反转位，检测同步丢失
3. **CRC 校验**：15-bit CRC（CAN 2.0）或 17/21-bit CRC（CAN FD）
4. **帧格式检查**：固定格式字段（ACK、EOF）必须符合规范
5. **ACK 检查**：至少一个接收节点必须确认

### 4.2 错误状态机

```c
// CAN 节点的三种错误状态
typedef enum {
    ERROR_ACTIVE,    // TEC < 128 且 REC < 128：正常工作，可发错误帧
    ERROR_PASSIVE,   // TEC >= 128 或 REC >= 128：仍可通信，但不能主动报错
    BUS_OFF          // TEC >= 256：断开总线，需要恢复流程
} CAN_ErrorState;

// 错误计数器规则：
// - 发送成功: TEC -= 1
// - 接收成功: REC -= 1 (如果 > 0)
// - 检测到错误(发送方): TEC += 8
// - 检测到错误(接收方): REC += 1 或 +8

// Bus-Off 恢复：检测到 128 次 11 个连续隐性位后自动恢复
```

### 4.3 IoT 场景中的错误处理策略

```c
// 工业 IoT 场景：传感器数据丢失的处理
typedef struct {
    uint32_t msg_id;
    uint32_t last_received_ms;
    uint32_t timeout_ms;
    uint8_t  miss_count;
    uint8_t  max_miss;
} SensorWatchdog;

void check_sensor_health(SensorWatchdog* wd, uint32_t now_ms) {
    if (now_ms - wd->last_received_ms > wd->timeout_ms) {
        wd->miss_count++;
        if (wd->miss_count >= wd->max_miss) {
            // 传感器可能故障，触发告警
            trigger_alarm(wd->msg_id, ALARM_SENSOR_OFFLINE);
            // 切换到安全模式/使用上一个有效值
            use_last_valid_value(wd->msg_id);
        }
    } else {
        wd->miss_count = 0;  // 收到数据，重置计数
    }
}
```

## 5. MCP2515 代码实例

### 5.1 硬件连接

MCP2515 是最常用的 SPI-CAN 控制器，适合给没有内置 CAN 的 MCU（如 ESP32、Arduino）添加 CAN 接口：

```
MCU (SPI)          MCP2515           TJA1050          CAN Bus
  MOSI  --------> SI                 TXD <-----> CANH ===
  MISO  <-------- SO                 RXD <-----> CANL ===
  SCK   --------> SCK                             |
  CS    --------> CS                            120R (终端电阻)
  INT   <-------- INT
                   |
                 8MHz 晶振
```

### 5.2 完整的发送/接收代码

```c
// MCP2515 CAN 通信完整示例（Arduino/ESP32）
#include <SPI.h>

#define MCP2515_CS    5
#define MCP2515_INT   4

// MCP2515 寄存器地址
#define CANSTAT       0x0E
#define CANCTRL       0x0F
#define CNF1          0x2A
#define CNF2          0x29
#define CNF3          0x28
#define TXB0CTRL      0x30
#define TXB0SIDH      0x31
#define TXB0SIDL      0x32
#define TXB0DLC       0x35
#define TXB0D0        0x36
#define RXB0CTRL      0x60
#define RXB0SIDH      0x61
#define RXB0D0        0x66

// SPI 操作
void mcp2515_write(uint8_t addr, uint8_t data) {
    digitalWrite(MCP2515_CS, LOW);
    SPI.transfer(0x02);  // Write 指令
    SPI.transfer(addr);
    SPI.transfer(data);
    digitalWrite(MCP2515_CS, HIGH);
}

uint8_t mcp2515_read(uint8_t addr) {
    digitalWrite(MCP2515_CS, LOW);
    SPI.transfer(0x03);  // Read 指令
    SPI.transfer(addr);
    uint8_t result = SPI.transfer(0x00);
    digitalWrite(MCP2515_CS, HIGH);
    return result;
}

// 初始化 MCP2515 (500kbps, 8MHz 晶振)
void mcp2515_init(void) {
    // 复位
    digitalWrite(MCP2515_CS, LOW);
    SPI.transfer(0xC0);
    digitalWrite(MCP2515_CS, HIGH);
    delay(10);

    // 配置模式
    mcp2515_write(CANCTRL, 0x80);  // Configuration mode

    // 波特率配置: 500kbps @ 8MHz
    // TQ = 2/Fosc = 250ns, 8 TQ/bit
    mcp2515_write(CNF1, 0x00);  // SJW=1, BRP=0 (TQ=2/8MHz=250ns)
    mcp2515_write(CNF2, 0x90);  // BTLMODE=1, SAM=0, PHSEG1=2, PRSEG=0
    mcp2515_write(CNF3, 0x02);  // PHSEG2=2

    // 接收所有消息（不过滤）
    mcp2515_write(RXB0CTRL, 0x60);  // 关闭过滤器

    // 切换到正常模式
    mcp2515_write(CANCTRL, 0x00);
    delay(10);
}

// 发送 CAN 消息
void can_send(uint16_t id, uint8_t* data, uint8_t len) {
    // 等待发送缓冲区空闲
    while (mcp2515_read(TXB0CTRL) & 0x08);

    // 设置 ID
    mcp2515_write(TXB0SIDH, (id >> 3) & 0xFF);
    mcp2515_write(TXB0SIDL, (id << 5) & 0xE0);

    // 设置数据长度
    mcp2515_write(TXB0DLC, len & 0x0F);

    // 写入数据
    for (uint8_t i = 0; i < len; i++) {
        mcp2515_write(TXB0D0 + i, data[i]);
    }

    // 请求发送
    mcp2515_write(TXB0CTRL, 0x08);
}

// 使用示例：发送温度传感器数据
void send_temperature(float temp) {
    uint8_t data[4];
    memcpy(data, &temp, 4);  // float 转 4 字节
    can_send(0x201, data, 4);  // ID=0x201, 4字节温度数据
}
```

### 5.3 Python 版本（使用 python-can 库）

```python
import can
import struct
import time

# 创建 CAN 接口（Linux SocketCAN）
bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=500000)

# 发送传感器数据
def send_sensor_data(sensor_id: int, temperature: float, humidity: float):
    """
    CAN ID 编码规则（自定义）：
    Bit 10-8: 优先级 (0=最高)
    Bit 7-4:  节点地址
    Bit 3-0:  消息类型
    """
    can_id = (0x2 << 8) | (sensor_id << 4) | 0x01  # 优先级2, 类型1=环境数据
    data = struct.pack('<ff', temperature, humidity)  # 小端序，2个float=8字节

    msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)
    bus.send(msg)
    print(f"Sent: ID=0x{can_id:03X}, Temp={temperature:.1f}C, Hum={humidity:.1f}%")

# 接收并解析
def receive_loop():
    while True:
        msg = bus.recv(timeout=1.0)
        if msg is None:
            continue

        msg_type = msg.arbitration_id & 0x0F
        node_id = (msg.arbitration_id >> 4) & 0x0F

        if msg_type == 0x01 and len(msg.data) == 8:
            temp, hum = struct.unpack('<ff', msg.data)
            print(f"Node {node_id}: {temp:.1f}C, {hum:.1f}%")

# 示例运行
send_sensor_data(sensor_id=3, temperature=25.6, humidity=65.2)
```

## 6. 工业 IoT 与车联网应用

### 6.1 工业传感器网络架构

```
[温度传感器] --+
[压力传感器] --+-- CAN Bus (500kbps) --+-- [网关/PLC]
[振动传感器] --+                        |
[流量计]     --+                        +-- [云平台]
                                        |
[车窗控制] ---+                         +-- [本地 HMI]
[座椅加热] ---+-- LIN Bus (19.2kbps) --+
[氛围灯]   ---+
```

### 6.2 协议选型对比

| 场景 | 推荐协议 | 原因 |
|------|---------|------|
| 发动机/底盘控制 | CAN FD | 实时性要求高，数据量中等 |
| ADAS 传感器 | CAN XL / 以太网 | 大数据量（雷达、摄像头） |
| 车身电子 | CAN 2.0 | 成熟可靠，数据量小 |
| 舒适系统 | LIN | 成本敏感，实时性要求低 |
| 工厂产线 | CAN FD | 多节点、中等速率、高可靠 |
| 楼宇自动化 | LIN / RS-485 | 长距离、低速、低成本 |
| 农业传感器 | CAN 2.0 | 恶劣环境、抗干扰 |

### 6.3 CAN 在智能工厂中的实际部署

一个典型的 CNC 机床监测系统：

- 32 个振动传感器（采样率 1kHz，每个 2 字节）
- 8 个温度传感器（采样率 10Hz）
- 4 个电流传感器（采样率 100Hz）
- 总线负载率计算：32 * 1000 * (47+64+25) / 1000000 = 4.35 Mbps -> 需要 CAN FD

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：购买 MCP2515 模块（约 15 元）+ Arduino，实现两节点通信
2. **第二步**：用逻辑分析仪（如 Saleae Logic）观察 CAN 帧的位时序
3. **第三步**：在 Linux 上用 SocketCAN + can-utils 工具集做总线分析
4. **第四步**：实现一个 3 节点传感器网络，理解仲裁和优先级
5. **第五步**：尝试 CAN FD（使用 STM32G4 内置 FDCAN 控制器）

### 7.2 具体调优建议

**波特率选择**：总线长度决定最大波特率。经验公式：最大波特率(Mbps) = 50 / 总线长度(m)。10 米内用 1Mbps，50 米用 500kbps，500 米用 125kbps。

**终端电阻**：CAN 总线两端各需要一个 120 欧姆终端电阻。缺少终端电阻会导致信号反射，表现为间歇性通信错误。用万用表测量 CAN_H 和 CAN_L 之间的电阻，应该约为 60 欧姆（两个 120 欧姆并联）。

**ID 分配策略**：优先级最高的消息分配最小的 ID。建议预留 ID 空间：0x000-0x0FF 用于紧急/安全消息，0x100-0x3FF 用于周期性传感器数据，0x400-0x7FF 用于配置和诊断。

**总线负载率**：建议不超过 70%。超过后仲裁延迟急剧增加，低优先级消息可能"饿死"。

## 参考文献

1. Bosch. "CAN Specification Version 2.0." Robert Bosch GmbH, 1991.
2. ISO 11898-1:2015. "Road vehicles - Controller area network (CAN)." ISO, 2015.
3. CAN in Automation (CiA). "CAN FD Specification Version 1.0." 2012.
4. CiA 610-1. "CAN XL Data Link Layer." 2024.
5. LIN Consortium. "LIN Specification Package Revision 2.2A." 2010.
6. Microchip. "MCP2515 Stand-Alone CAN Controller with SPI Interface Datasheet." 2019.
7. Corrigan, S. "Introduction to the Controller Area Network (CAN)." TI Application Report SLOA101, 2016.
8. Hartwich, F. "CAN with Flexible Data-Rate." Bosch, 2012.
9. Di Natale, M., et al. "Understanding and Using the Controller Area Network Communication Protocol." Springer, 2012.
10. Voss, W. "A Comprehensible Guide to Controller Area Network." Copperhill Technologies, 2023.
