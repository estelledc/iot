# Modbus RTU/TCP在工业IoT中的协议分析

> **难度**：🟡 中级 | **领域**：工业通信协议 | **阅读时间**：约 20 分钟

## 引言

想象一个工厂车间，有几十台设备需要统一监控：温度传感器报告数值、变频器接收转速指令、电表上传能耗数据。如果每台设备都用自己的"语言"和"通信接口"，那集成工作将是一场噩梦。Modbus 就是工业界的"普通话"——它定义了一套统一的问答规则，让不同厂商的设备能够互相对话。

Modbus 诞生于 1979 年，是最早的工业通信协议之一。近半个世纪后它仍是工业领域使用最广泛的协议，原因很简单：协议公开、实现简单、稳定可靠。在工业 IoT 时代，Modbus 不但没有被淘汰，反而成为连接传统工业设备与云端平台的桥梁。本文将深入解析 Modbus RTU 和 TCP 两种变体，并探讨它们在现代 IIoT 中的定位和实践。

## 1. Modbus 协议概述

### 1.1 历史与定位

Modbus 于 1979 年由 Modicon(现施耐德电气)发布，2004 年成为完全开放的协议标准，2012 年成为我国国家标准 GB/T 30879。核心定位：应用层协议(与物理层无关)、请求-响应模型(Master/Slave 或 Client/Server)、面向寄存器的数据模型(一切皆寄存器)。

### 1.2 通信模型

RTU 模式采用 Master/Slave 架构，一个 Master 最多 247 个 Slave，同一时刻只有一个请求。TCP 模式为 Client/Server 架构，支持多 Client 并发访问，每个连接独立。关键区别：RTU 由 Master 控制总线仲裁，TCP 通过事务ID 支持并发。

### 1.3 协议分层

| 层次 | Modbus RTU | Modbus TCP |
|------|-----------|-----------|
| 应用层 | Modbus Application Protocol | Modbus Application Protocol |
| 传输层 | RS-485 / RS-232 | TCP/IP |
| 数据链路层 | Modbus Serial Frame | MBAP Header |
| 物理层 | 双绞线(差分信号) | 以太网 |

应用层协议(PDU)是共享的，差异仅在底层传输封装。

## 2. Modbus 数据模型

### 2.1 四种数据类型

| 数据类型 | 访问方式 | 典型用途 |
|----------|----------|----------|
| Coils (线圈) | 读写 | 开关量输出(启停控制) |
| Discrete Inputs (离散输入) | 只读 | 开关量输入(限位开关) |
| Holding Registers (保持寄存器) | 读写 | 模拟量输出(设定值) |
| Input Registers (输入寄存器) | 只读 | 模拟量输入(传感器值) |

日常类比：Coils = 电灯开关(能开/关)，Discrete Input = 门磁传感器(只能看)，Holding Reg = 空调温度设定(能改)，Input Reg = 温度计读数(只能看)。

### 2.2 地址与编号

协议地址 0-based(帧中传输)，寄存器编号 1-based(文档显示)。行业惯例：0xxxxx = Coils, 1xxxxx = Discrete Inputs, 3xxxxx = Input Registers, 4xxxxx = Holding Registers。如 Holding Register 40001 对应协议地址 0x0000。

### 2.3 寄存器映射设计

合理的寄存器映射是 Modbus 应用的核心设计：同类数据连续排列减少请求次数，32-bit 数据占两个连续寄存器须明确字节序，分组间留空便于扩展。示例：温度采集模块 HR 0x0000-0x0003 为四通道温度，0x0004 为湿度，0x0005-0x0006 为可写配置，0x0010-0x0011 为状态和版本。

## 3. 功能码详解

### 3.1 常用功能码

| 功能码 | 名称 | 操作对象 | 最大数量 |
|--------|------|----------|----------|
| 0x01 | Read Coils | 线圈 | 2000 |
| 0x02 | Read Discrete Inputs | 离散输入 | 2000 |
| 0x03 | Read Holding Registers | 保持寄存器 | 125 |
| 0x04 | Read Input Registers | 输入寄存器 | 125 |
| 0x05 | Write Single Coil | 单个线圈 | 1 |
| 0x06 | Write Single Register | 单个保持寄存器 | 1 |
| 0x0F | Write Multiple Coils | 多个线圈 | 1968 |
| 0x10 | Write Multiple Registers | 多个保持寄存器 | 123 |

### 3.2 功能码 03 示例

读取从站1地址0x0000起的3个保持寄存器：

```
请求: 01 03 00 00 00 03 [CRC_L] [CRC_H]
  01 = 从站1, 03 = Read HR, 00 00 = 起始地址, 00 03 = 3个寄存器

响应: 01 03 06 00 64 01 2C 00 96 [CRC_L] [CRC_H]
  06 = 数据6字节, 00 64=100, 01 2C=300, 00 96=150
```

功能码 06 写入单个寄存器时，响应帧与请求帧完全相同(回显确认)。

## 4. Modbus RTU 帧格式

### 4.1 帧结构

```
| 从站地址(1B) | 功能码(1B) | 数据(NB) | CRC16(2B) |
|    1-247     |  0x01-0x7F | 变长     | 低字节在前 |

帧间静默: >= 3.5 字符时间 (9600bps 下约 4ms)
帧内间隔: < 1.5 字符时间 (9600bps 下约 1.7ms)
```

### 4.2 CRC16 校验

```c
uint16_t modbus_crc16(const uint8_t *data, uint16_t len) {
    uint16_t crc = 0xFFFF;
    for (uint16_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x0001) { crc >>= 1; crc ^= 0xA001; }
            else { crc >>= 1; }
        }
    }
    return crc; // 低字节先发
}
```

## 5. Modbus TCP 帧格式

### 5.1 MBAP 头

```
| 事务ID(2B) | 协议ID(2B) | 长度(2B) | 单元ID(1B) | PDU(NB) |

事务ID: 匹配请求和响应(Client 生成)
协议ID: 0x0000 = Modbus
长度: 从单元ID到帧尾的字节数
单元ID: 对应 RTU 的从站地址
```

### 5.2 TCP vs RTU 关键差异

TCP 无 CRC(TCP 层已有校验)，增加事务ID 支持并发请求，从站地址变为单元ID，默认端口 502。PDU 部分完全相同。

### 5.3 TCP 帧示例

```
请求: 00 01 00 00 00 06 01 03 00 00 00 02
  事务ID=1, 协议=Modbus, 长度=6, 单元=1, FC=03, 地址=0, 数量=2

响应: 00 01 00 00 00 07 01 03 04 00 64 00 C8
  事务ID=1, 长度=7, 数据=4字节: 100, 200
```

## 6. RTU 与 TCP 对比

| 特性 | Modbus RTU | Modbus TCP |
|------|-----------|-----------|
| 物理层 | RS-485/RS-232 | 以太网 |
| 传输速率 | 1.2k-115.2k bps | 10/100 Mbps |
| 最大从站数 | 247 | 理论无限制 |
| 通信距离 | RS-485 最远 1200m | 受网络限制 |
| 帧校验 | CRC16 | TCP 层校验 |
| 并发请求 | 不支持 | 支持 |
| 延迟 | 低(确定性) | 较高(受网络影响) |
| 安全性 | 无 | 无(协议本身) |
| 典型应用 | 车间级设备通信 | 车间到工厂级 |

选型建议：RTU 适合设备密集、实时性要求高、成本敏感、电磁干扰强的现场；TCP 适合远程访问、大数据量、多主站并发、与 IT 系统集成；混合使用最常见——现场 RTU + 网关汇聚 TCP。

## 7. Modbus 网关

### 7.1 RTU 到 TCP 桥接

```
[RTU 从站1] --\
[RTU 从站2] ----[RS-485]----[Modbus 网关]----[以太网]----[TCP Client]
[RTU 从站3] --/                    |
                              [单元ID映射表]

工作流程:
  1. TCP Client 发请求(含单元ID)
  2. 网关查表映射到 RTU 从站地址
  3. 网关构造 RTU 帧发往 RS-485
  4. 从站响应后网关转为 TCP 帧返回
```

### 7.2 网关配置要点

串口参数必须与从站一致(典型 9600-8-N-1)，TCP 端口 502，RTU 轮询周期不宜过短(>= 100ms/从站)，串口失败时网关应返回异常码而非超时无响应。

## 8. 异常响应处理

### 8.1 异常码

异常响应帧中功能码最高位置 1(原功能码 + 0x80)，后跟异常码。

| 异常码 | 含义 | 处理建议 |
|--------|------|----------|
| 01 | 非法功能码 | 不重试，修正功能码 |
| 02 | 非法数据地址 | 不重试，修正寄存器地址 |
| 03 | 非法数据值 | 不重试，修正写入值 |
| 04 | 从站故障 | 告警并跳过 |
| 05 | 确认(长操作) | 等待后重试 |
| 06 | 从站忙 | 等待后重试 |

### 8.2 错误处理策略

RTU 超时建议 500ms-2s，重试 2-3 次；01/02/03 类异常不应重试应修正参数；04 类应告警跳过；05/06 类可等待后重试。上位软件应标记数据"有效/过期/故障"状态。

## 9. 安全性分析

### 9.1 安全缺陷

Modbus 设计于 1979 年，安全缺陷明显：无认证(任何人可读写)、无加密(明文传输)、无访问控制(功能码级别无权限区分)、无审计(无操作日志)。攻击场景包括网络嗅探截获工艺参数、伪造指令写入危险值、拒绝服务占用总线/连接。

### 9.2 安全加固

纵深防御：网络隔离(Modbus 网络与办公网物理隔离)、防火墙限制 502 端口、网关增加认证和白名单及操作日志、远程访问走 VPN 加密通道、关键场景评估 OPC UA 替代。

## 10. Modbus 在现代 IIoT 中的应用

### 10.1 Modbus + MQTT 桥接

```
[Modbus RTU] --RS-485--> [IoT 网关] --MQTT--> [云平台]

网关数据映射:
  读 HR 0x0000 --> 发布 topic: device/temp
  读 HR 0x0001 --> 发布 topic: device/humidity
  订阅 topic: device/setpoint --> 写 HR 0x0005

典型 MQTT Payload (JSON):
  {"device_id":"sensor_001","temperature":25.6,"humidity":65.2}
```

### 10.2 边缘计算集成

边缘网关承担数据采集(Modbus Master)、协议转换(Modbus -> MQTT)、本地存储(断网缓存)、边缘计算(阈值判断/本地控制)和 OTA 升级等功能。选型：工业级(Moxa/HMS/研华)或开源方案(树莓派 + pymodbus)或云厂商(AWS Greengrass/Azure IoT Edge)。

### 10.3 数据建模

Modbus 寄存器到 IoT 数据模型的映射：Holding Register 值映射为设备影子的 reported/desired 属性，时序数据库中以 measurement + tags(device_id/location) + fields(温度/湿度) + timestamp 存储。

## 11. 实现库与工具

### 11.1 libmodbus (C 语言)

```c
#include <modbus.h>

int main(void) {
    modbus_t *ctx = modbus_new_rtu("/dev/ttyUSB0", 9600, 'N', 8, 1);
    modbus_set_slave(ctx, 1);
    modbus_connect(ctx);

    uint16_t regs[10];
    int rc = modbus_read_registers(ctx, 0, 10, regs);
    if (rc != -1) {
        for (int i = 0; i < rc; i++)
            printf("reg[%d] = %d\n", i, regs[i]);
    }
    modbus_write_register(ctx, 5, 600);
    modbus_close(ctx);
    modbus_free(ctx);
    return 0;
}
```

### 11.2 pymodbus (Python)

```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('192.168.1.100', port=502)
client.connect()

result = client.read_holding_registers(address=0, count=5, slave=1)
if not result.isError():
    print(f"温度: {result.registers[0] * 0.1} C")
else:
    print(f"错误码: {result.exception_code}")

client.write_registers(address=5, values=[600, 250], slave=1)
client.close()
```

### 11.3 调试工具

| 工具 | 类型 | 用途 |
|------|------|------|
| ModScan | Windows GUI | RTU/TCP 扫描调试 |
| QModMaster | 跨平台 Qt | 开源 RTU/TCP 调试 |
| modpoll | 命令行 | 快速轮询测试 |
| pymodbus REPL | Python | 交互式调试 |

## 12. STM32 Modbus 从站实现

### 12.1 从站框架

```c
typedef struct {
    uint8_t  slave_addr;
    uint16_t holding_regs[100];
    uint16_t input_regs[100];
} modbus_slave_t;

void modbus_process(modbus_slave_t *slave, uint8_t *rx,
                    uint16_t rx_len, uint8_t *tx, uint16_t *tx_len)
{
    // CRC 校验
    uint16_t rx_crc = rx_buf[rx_len-2] | (rx_buf[rx_len-1] << 8);
    if (modbus_crc16(rx, rx_len-2) != rx_crc) { *tx_len = 0; return; }
    // 地址过滤
    if (rx[0] != slave->slave_addr && rx[0] != 0x00) { *tx_len = 0; return; }

    switch (rx[1]) {
        case 0x03: modbus_func03(slave, rx, tx, tx_len); break;
        case 0x06: modbus_func06(slave, rx, tx, tx_len); break;
        case 0x10: modbus_func10(slave, rx, tx, tx_len); break;
        default: modbus_exception(slave, rx[1], 0x01, tx, tx_len); break;
    }
}
```

### 12.2 功能码 03 实现

```c
void modbus_func03(modbus_slave_t *slave, uint8_t *rx,
                   uint8_t *tx, uint16_t *tx_len)
{
    uint16_t addr  = (rx[2] << 8) | rx[3];
    uint16_t count = (rx[4] << 8) | rx[5];

    if (addr + count > 100) {
        modbus_exception(slave, 0x03, 0x02, tx, tx_len); return;
    }
    uint16_t idx = 0;
    tx[idx++] = slave->slave_addr;
    tx[idx++] = 0x03;
    tx[idx++] = count * 2;
    for (uint16_t i = 0; i < count; i++) {
        tx[idx++] = (slave->holding_regs[addr+i] >> 8) & 0xFF;
        tx[idx++] = slave->holding_regs[addr+i] & 0xFF;
    }
    uint16_t crc = modbus_crc16(tx, idx);
    tx[idx++] = crc & 0xFF;
    tx[idx++] = (crc >> 8) & 0xFF;
    *tx_len = idx;
}
```

### 12.3 RS-485 收发控制

```c
void rs485_tx_enable(void) {
    HAL_GPIO_WritePin(RS485_DE_PORT, RS485_DE_PIN, GPIO_PIN_SET);
    DELAY_US(10);
}
void rs485_rx_enable(void) {
    while (__HAL_UART_GET_FLAG(&huart1, UART_FLAG_TC) == RESET);
    DELAY_US(10);
    HAL_GPIO_WritePin(RS485_DE_PORT, RS485_DE_PIN, GPIO_PIN_RESET);
}
void modbus_send(uint8_t *buf, uint16_t len) {
    rs485_tx_enable();
    HAL_UART_Transmit(&huart1, buf, len, 100);
    rs485_rx_enable();
}
```

## 13. 常见问题与调试

### 13.1 通信失败排查

排查顺序：(1) RS-485 A/B 是否接反(最常见)；(2) 终端电阻 120R 是否正确；(3) 波特率/校验位/停止位是否一致，用 USB-RS485 抓包；(4) 从站地址和寄存器地址是否正确(0-based vs 1-based)；(5) RTU 帧间静默时间是否足够。

### 13.2 数据解析异常

读到的值与预期不符的常见原因：字节序问题(Modbus 大端但某些设备小端存储，需交换高低字节)；32-bit 数据占两个寄存器须确认存储顺序；缩放因子(如温度值 256 = 25.6 C 即 0.1 C/LSB)；有符号数需补码转换。

### 13.3 总线冲突

Modbus RTU 不支持多主站，如需多系统读取应通过网关/中间件转发。从站响应延迟导致帧重叠时，应增加请求间静默时间、实现帧间超时检测、等待响应超时后再发下一帧。

## 总结

Modbus 横跨 40 余年仍然活跃，靠的是极简的设计哲学：(1) 一切皆寄存器，四种数据类型覆盖工业控制所有需求；(2) RTU 重在可靠，差分信号 + CRC16 + 确定性总线适合恶劣现场；(3) TCP 重在互联，事务ID + 多连接解决 RTU 并发瓶颈；(4) 网关是桥梁，RTU 经网关接入以太网/云端是 IIoT 标准架构；(5) 安全是短板，必须通过网络隔离和网关安全机制弥补；(6) 数据建模是关键，寄存器到 IoT 数据模型的映射决定上层开发效率。建议从 RTU Master + pymodbus 开始实践，再深入 TCP 网关和 MQTT 桥接。

## 参考文献

1. Modbus Organization. Modbus Application Protocol Specification V1.1b3. 2012.
2. Modbus Organization. Modbus over Serial Line Specification and Implementation Guide V1.02. 2006.
3. Modbus Organization. Modbus Messaging on TCP/IP Implementation Guide V1.0b. 2012.
4. GB/T 30879-2014. 工业自动化产品通信协议 Modbus. 2014.
5. Stepwise. pymodbus Documentation. https://pymodbus.readthedocs.io/, 2024.
