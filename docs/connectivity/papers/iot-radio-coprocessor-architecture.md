---
schema_version: '1.0'
id: iot-radio-coprocessor-architecture
title: IoT射频协处理器架构与主控分工
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - iot-radio-certification-process
  - ble-gatt-profile-custom-service
tags:
  - 射频协处理器
  - HCI
  - NCP
  - RCP
  - UART
  - SPI
  - 主机控制器
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# IoT射频协处理器架构与主控分工

> **难度**：🟡 中级 | **领域**：硬件架构 | **阅读时间**：约 20 分钟

## 日常类比

餐厅前台点餐、后厨做菜：一人兼两职则慢且故障互相拖累。主控微控制器（MCU）跑应用，射频协处理器专管无线——像把“炒菜”外包给专业灶台[3]。

## 摘要

分离动机：认证复用、电源域独立、团队并行。网络协处理器（Network Co-Processor, NCP）跑完整栈；射频协处理器（Radio Co-Processor, RCP）偏 PHY/MAC。接口按吞吐选 UART/AT、SPI 或 SDIO。功耗与寿命数字依赖占空比，**需实测**[1][5]。

## 1. 为何分离

| 收益 | 说明 |
|------|------|
| 认证复用 | 已认证模组换主控，常可避免全量射频重测（仍守集成条件） |
| 供应链 | 射频与应用料号可相对独立替换 |
| 开发隔离 | 协议栈与应用固件并行、故障域分离 |
| 功耗 | 射频断电时 MCU 仍可采传感 |

整机射频认证费用常达数千至数万美元量级，一体化每次改射频相关 PCB 都可能触发重评——**以实验室评估为准**[见认证文]。

## 2. 分工模型

蓝牙主机控制器接口（Host Controller Interface, HCI）是经典分界：Host 跑 GATT/L2CAP 等，Controller 跑链路层与 PHY[3]。

| 模式 | 射频侧职责 | 主控侧 | 适合 |
|------|------------|--------|------|
| NCP | PHY→网络/传输较完整 | 应用数据收发 | 快速上市、厂商维护栈 |
| RCP | 偏 PHY/MAC | 上层协议+应用 | 深度定制、开源栈 |
| HCI（BLE） | LL+PHY | Host 协议 | 标准蓝牙主机 |

## 3. 接口选择

| 接口 | 引脚 | 速率量级 | 典型 |
|------|------|----------|------|
| UART + AT | 2 | 常至约 1 Mbps | LoRaWAN、蜂窝模组 |
| SPI 二进制 | 4 | 数 Mbps～十余 Mbps | BLE、Sub-GHz |
| SDIO | 较多 | 更高 | Wi-Fi 网卡式 |

AT 易调试、文本开销大；SPI 需自定义帧与 CRC；Wi-Fi 高吞吐常见 SDIO。

## 4. 产品形态

- **ESP32 作 Wi-Fi/BLE 协处理**：主控经 UART AT 或 SPI 协议固件上网[2]。
- **nRF52 作 BLE Controller**：HCI over UART/USB 常见于 Linux/RTOS 主机[1]。
- **SX1276 类 LoRa**：典型 RCP，LoRaWAN 栈在主控，芯片管调制解调[4]。

固件更新宜双 Bank + 固定 Bootloader，支持 DFU/串口/SWD；失败可回滚。

## 5. 案例要点（STM32 + nRF52）

工业传感：STM32L0 类采数与电源管理，nRF52 SoftDevice 管 BLE。深度睡眠合计微安量级、周期广播微库仑量级电荷——**寿命随电池容量与温漂变化，勿直接抄标称年数**[1][5]。HCI 更新广播载荷即可上报温湿度等。

## 6. 局限、挑战与可改进方向

### 1. 控制粒度不足（NCP）

**局限**：主控难精细调度射频时序与共存参数。
**改进**：需深度定制时改 RCP/HCI；或选开放 NCP API 的模组。

### 2. 接口成为瓶颈

**局限**：高通知率 BLE 或 Wi-Fi 吞吐被 UART AT 拖死。
**改进**：按峰值吞吐选 SPI/SDIO；批量聚合上报。

### 3. 双固件运维

**局限**：两套镜像版本矩阵、部分更新导致不兼容。
**改进**：版本契约与兼容表；原子双端升级策略。

### 4. 一体化诱惑

**局限**：ESP32 类 SoC 省料，但认证与电源域灵活性下降。
**改进**：产品稳定、不换射频技术可选一体；长生命周期或可换射频则分离。

## 7. 实践要点

1. 先问：要否换射频、要否独立断电、团队是否分栈。
2. 数据量小用 UART+AT；中等 SPI；Wi-Fi 级 SDIO。
3. 模组预认证 + 独立复位脚，便于协议栈挂死时主控拉复位。

## 参考文献

[1] Nordic Semiconductor, nRF52832 Product Specification (current).
[2] Espressif, ESP-AT User Guide, https://docs.espressif.com/projects/esp-at
[3] Bluetooth SIG, Bluetooth Core Specification, Vol 4: HCI.
[4] Semtech, SX1276/77/78/79 Datasheet.
[5] STMicroelectronics, AN5289 / STM32 wireless application notes.
[6] Thread/OpenThread RCP vs NCP architecture documentation.
[7] Zephyr / Mynewt HCI driver and controller split materials.
[8] LoRaMac-node and related host-stack-on-MCU designs.
[9] USB DFU / Nordic DFU documentation for radio firmware update.
[10] Module vendor host MCU interface application notes (SPI framing).
[11] FCC/CE modular approval notes relevant to host+module splits.
[12] SDIO Wi-Fi companion chip integration guides.
