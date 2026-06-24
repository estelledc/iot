# IoT射频协处理器架构与主控分工
> **难度**: 中级 | **领域**: 硬件架构 | **阅读时间**: 约 20 分钟

## 引言

你去餐厅吃饭时,前台负责接待点餐,后厨负责做菜。如果让一个人既收银又炒菜,效率必然低下,而且一旦厨房着火,前台也跟着停工。IoT设备中的"主控+射频协处理器"架构就是同样的道理——把无线通信这个"专业活"交给专门的芯片去干,主控MCU专注于应用逻辑。

这种分工在IoT产品中极为常见:你的智能手表里可能有一颗应用处理器加一颗BLE芯片;WiFi路由器里有一颗主CPU加一颗WiFi SoC;LoRa网关里有一颗Linux主机加若干LoRa射频模块。理解这种架构的分工原则和通信接口,是设计IoT硬件的基础功课。

本文将介绍为什么要做主控与射频的分离、常见的分工模式、通信接口选择,以及实际产品中的典型实现。

## 1. 为什么要分离射频与应用

### 1.1 模块化与认证复用

将射频功能独立为一个模块有几个核心好处:

- 认证复用: 射频模块通过FCC/CE/SRRC等认证后,更换主控MCU不需要重新做射频认证
- 供应链灵活性: 可以根据成本/库存情况更换射频模块,而不改变应用代码
- 开发分离: 射频固件和应用固件可以由不同团队并行开发
- 风险隔离: 射频模块的bug修复不影响应用逻辑,反之亦然

无线产品的认证成本很高(FCC约$5,000-$20,000, CE RED约$8,000-$25,000, SRRC约30,000-80,000元)。如果应用MCU和射频一体化设计,每次修改PCB理论上都需要重新评估认证。而使用已认证的射频模块,只要不改变天线和射频部分,就可以保持认证有效。

### 1.2 功耗管理

射频模块的功耗特征与应用MCU完全不同。通过分离设计,当射频不需要工作时可以完全断电,而应用MCU继续处理传感器数据。这种独立的电源域管理在低功耗IoT设备中至关重要。

## 2. 主控-控制器架构模型

### 2.1 蓝牙的HCI分层

蓝牙协议栈定义了标准的Host-Controller接口(HCI),这是理解射频协处理器架构的经典范本:

```
+-------------------------------------------+
|          应用层 (Application)              |  <-- 主控MCU运行
+-------------------------------------------+
|          GATT / GAP                        |
+-------------------------------------------+
|          L2CAP                             |
+-------------------------------------------+
|          HCI (Host Controller Interface)   |  <-- 分界线
+============================================+
|          Link Layer (LL)                   |  <-- 射频协处理器运行
+-------------------------------------------+
|          Physical Layer (PHY)              |
+-------------------------------------------+
```

HCI定义了Host(主控)和Controller(射频)之间的标准命令集,包括HCI Commands(如开始扫描、建立连接)、HCI Events(如收到广播包)和HCI Data(双向数据传输)。

### 2.2 Network Co-Processor (NCP) 模式

NCP模式下,射频模块运行完整的协议栈(从PHY到网络层),主控只需要发送/接收应用数据:

```
主控MCU                          射频模块(NCP模式)
+-----------+                    +-------------------+
| 应用逻辑   |                    | 网络层/传输层      |
| 传感器驱动 |<--- 数据接口 --->  | MAC层             |
| 数据处理   |                    | PHY层 + 射频前端   |
+-----------+                    +-------------------+
```

优点: 主控极简,射频模块厂商负责协议栈维护。缺点: 主控对无线行为控制粒度有限。

### 2.3 Radio Co-Processor (RCP) 模式

RCP模式下,射频模块只负责PHY和MAC层,上层协议栈运行在主控MCU上:

```
主控MCU                          射频模块(RCP模式)
+-----------+                    +-------------------+
| 应用逻辑   |                    |                   |
| 网络层     |<--- 帧接口 --->    | MAC层             |
| MAC上层    |                    | PHY层 + 射频前端   |
+-----------+                    +-------------------+
```

优点: 主控对协议行为有完全控制,可深度定制。缺点: 主控需更多资源,开发复杂度更高。

## 3. 通信接口选择

### 3.1 UART + AT命令

最简单直观的接口方式,射频模块通过UART暴露一组文本命令:

```c
// AT命令接口示例 - LoRaWAN模块
AT+JOIN\r\n                     // 入网
AT+SEND=1:48656C6C6F\r\n        // 端口1发送"Hello"的hex
AT+DR=5\r\n                     // 设置数据速率
AT+ADR=1\r\n                    // 开启自适应数据速率

// WiFi模块
AT+CWJAP="MyNetwork","pass"\r\n // 连接WiFi
AT+CIPSTART="TCP","192.168.1.100",8080\r\n  // 建立TCP连接
AT+CIPSEND=13\r\n               // 发送13字节数据
```

特点: 开发难度低、波特率9600-115200bps、吞吐量低(文本编码开销大)、调试容易(串口终端即可)。

### 3.2 SPI二进制协议

SPI提供更高带宽和更低延迟的接口:

```c
// SPI接口 - 主控与射频模块通信
struct spi_frame {
    uint8_t  header;      // 帧头标识
    uint8_t  cmd_type;    // 命令类型: 0x01=数据, 0x02=控制
    uint16_t length;      // 有效载荷长度
    uint8_t  payload[];   // 有效载荷
    uint16_t crc;         // CRC校验
};

void send_to_radio(uint8_t *data, uint16_t len) {
    struct spi_frame frame;
    frame.header = 0xAA;
    frame.cmd_type = 0x01;
    frame.length = len;
    memcpy(frame.payload, data, len);
    frame.crc = calculate_crc(&frame, sizeof(frame) - 2);
    gpio_set_low(CS_PIN);
    spi_transfer(&frame, sizeof(frame));
    gpio_set_high(CS_PIN);
}
```

### 3.3 接口对比

| 接口 | 引脚数 | 最大速率 | 典型应用 | 功耗 |
|------|--------|---------|---------|------|
| UART | 2(TX/RX) | 1Mbps | LoRa, NB-IoT | 低 |
| SPI | 4(MOSI/MISO/CLK/CS) | 10Mbps+ | BLE, SubGHz | 中 |
| SDIO | 6(CMD/CLK/D0-D3) | 50MB/s | WiFi | 高 |

## 4. 典型产品案例

### 4.1 ESP32作为WiFi协处理器

ESP32可以作为独立的WiFi/BLE协处理器,为不具备无线能力的MCU提供网络连接:

```
应用MCU (STM32/Arduino)         ESP32 (WiFi协处理器)
+------------------+            +------------------+
| 传感器采集        |            | WiFi协议栈        |
| 数据处理          | <--SPI--> | TCP/IP + TLS     |
| 应用逻辑          |            | MQTT客户端        |
+------------------+            +------------------+
```

Espressif提供AT固件(UART文本命令)和SPI协议固件(类似网卡驱动)两种方案。

### 4.2 nRF52作为BLE控制器

Nordic nRF52系列支持标准HCI接口,可以纯粹作为BLE控制器使用。常见于树莓派 + nRF52 USB Dongle、i.MX RT主控 + nRF52协处理器等组合。

### 4.3 SX1276 LoRa射频模块

Semtech的LoRa芯片是典型的RCP模式——只提供调制解调,MAC层由主控实现:

```c
// SX1276 SPI控制示例
sx1276_write_reg(REG_MODEM_CONFIG1, BW_125kHz | CR_4_5);
sx1276_write_reg(REG_MODEM_CONFIG2, SF7 | CRC_ON);

void lora_send(uint8_t *data, uint8_t len) {
    sx1276_write_reg(REG_FIFO_ADDR_PTR, 0x00);
    sx1276_write_fifo(data, len);
    sx1276_write_reg(REG_PAYLOAD_LENGTH, len);
    sx1276_write_reg(REG_OP_MODE, MODE_TX);
    while(!gpio_read(DIO0_PIN));  // 等待TX完成中断
    sx1276_write_reg(REG_IRQ_FLAGS, IRQ_TX_DONE);
}
```

LoRaWAN协议栈(如LoRaMac-node)运行在主控MCU上,SX1276只负责物理层调制解调。

## 5. 射频模块固件更新

射频模块的固件需要更新的原因包括修复安全漏洞、增加新功能、修复协议栈bug等。为保证更新失败后仍能恢复,射频模块通常采用双区Flash设计:

```
Flash布局:
+------------------+
| Bootloader       |  <-- 固定不变,负责启动和更新管理
+------------------+
| Bank A (当前固件) |  <-- 正在运行的固件
+------------------+
| Bank B (备份/新)  |  <-- 新固件写入此区
+------------------+
| 配置区           |  <-- 标记当前活跃bank
+------------------+
```

常见更新方式: DFU(BLE标准OTA)、串口Bootloader、SWD/JTAG(开发阶段)。

## 6. 设计决策指南

选择一体化还是分离式:

```
                     需要灵活换射频?
                          |
                    +-----+-----+
                    |           |
                   是           否
                    |           |
              分离式架构     功耗敏感?
              (主控+模块)        |
                          +-----+-----+
                          |           |
                         是           否
                          |           |
                   分离式(独立电源域)  一体化SoC(如ESP32)
```

接口选择: 数据量小(<1kbps)用UART+AT; 中等(<1Mbps)用SPI; 大(>1Mbps)用SDIO。

## 7. 实际案例: STM32 + nRF52832智能传感器

### 7.1 需求与架构

工业环境监测传感器: 采集温湿度/气压/PM2.5,每5秒BLE广播,电池供电目标2年。选择STM32L0 + nRF52832:

```
+---------------------------+     +----------------------+
|  STM32L071 (应用MCU)      |     |  nRF52832 (BLE)      |
|  [传感器驱动] I2C/UART    |     |  [SoftDevice S132]   |
|  [数据处理] 滤波/报警     |UART |  [Link Layer + PHY]  |
|  [电源管理] 唤醒调度      |<--->|  [GATT Server]       |
+---------------------------+(HCI)+----------------------+
```

### 7.2 功耗分析

| 状态 | STM32L0 | nRF52832 | 合计 |
|------|---------|----------|------|
| 深度睡眠 | 0.5uA | 1.5uA | 2uA |
| 传感器采样 | 3mA, 50ms | 睡眠 | 150uC |
| BLE广播 | 睡眠 | 8mA, 1.5ms | 12uC |

平均电流(5秒周期): 约35uA。CR2477电池(1000mAh): 理论寿命约3.3年。

### 7.3 通信协议设计

主控与nRF52之间使用HCI over UART:

```c
// 主控侧: 通过HCI更新BLE广播数据
void update_ble_adv_data(sensor_data_t *data) {
    uint8_t adv_payload[12];
    adv_payload[0] = 0x02;  // 长度
    adv_payload[1] = 0x01;  // AD Type: Flags
    adv_payload[2] = 0x06;  // LE General Discoverable
    adv_payload[3] = 0x07;  // 长度
    adv_payload[4] = 0xFF;  // AD Type: Manufacturer Specific
    // 温度(0.01度精度, 大端序)
    adv_payload[5] = (uint8_t)(data->temperature >> 8);
    adv_payload[6] = (uint8_t)(data->temperature & 0xFF);
    // 湿度(0.1%精度)
    adv_payload[7] = (uint8_t)(data->humidity >> 8);
    adv_payload[8] = (uint8_t)(data->humidity & 0xFF);
    // PM2.5 (ug/m3)
    adv_payload[9] = (uint8_t)(data->pm25 >> 8);
    adv_payload[10] = (uint8_t)(data->pm25 & 0xFF);
    
    hci_send_command(HCI_LE_SET_ADV_DATA, adv_payload, 11);
}
```

### 7.4 分离架构的实际好处

- 固件独立更新: nRF52的SoftDevice更新不影响STM32应用代码
- 并行开发: 硬件工程师调试射频的同时,软件工程师开发应用逻辑
- 射频认证: nRF52模块已预认证,整机认证时射频测试简化
- 故障隔离: BLE协议栈崩溃时,STM32可以复位nRF52恢复
- 技术演进: 未来如需切换到BLE 6.0,只需更换射频模块

## 总结

IoT射频协处理器架构是一种"专业的人做专业的事"的设计哲学。其核心要点:

- 分离射频和应用的主要动机是认证复用、功耗管理和开发模块化
- NCP模式(射频跑完整协议栈)适合快速开发,RCP模式(射频只跑PHY/MAC)适合深度定制
- 接口选择取决于数据量: UART/AT适合低速, SPI适合中速, SDIO适合高速WiFi
- HCI是蓝牙标准的Host-Controller分界,是理解此架构的经典范本
- 实际产品中,STM32+nRF52、主控+ESP32、MCU+SX1276都是常见的分离式组合
- 射频模块的固件更新机制(DFU/双区设计)保证了产品的可维护性

选择一体化还是分离式的关键判断: 如果产品需要长期维护、可能更换射频技术、或需要最优功耗,分离式架构是更好的选择。

## 参考文献

1. Nordic Semiconductor. "nRF52832 Product Specification v1.8." Nordic, 2023.
2. Espressif Systems. "ESP-AT User Guide." Espressif, 2023. https://docs.espressif.com/projects/esp-at
3. Bluetooth SIG. "Bluetooth Core Specification v5.3 - Vol 4: Host Controller Interface." 2021.
4. Semtech. "SX1276/77/78/79 Datasheet." Semtech Corporation, 2020.
5. STMicroelectronics. "AN5289: Building wireless applications with STM32WB." ST, 2022.
