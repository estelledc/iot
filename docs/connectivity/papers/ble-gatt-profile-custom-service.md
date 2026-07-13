---
schema_version: '1.0'
id: ble-gatt-profile-custom-service
title: BLE GATT自定义服务与特征值设计
layer: 2
content_type: tutorial
difficulty: beginner
reading_time: 18
prerequisites:
  - ble-security-pairing-bonding
tags:
  - BLE
  - GATT
  - 特征值
  - UUID
  - CCCD
  - Zephyr
  - 自定义服务
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# BLE GATT自定义服务与特征值设计

> **难度**：🟢 初级 | **领域**：BLE应用开发 | **阅读时间**：约 18 分钟

## 日常类比

把蓝牙低功耗（Bluetooth Low Energy, BLE）设备想成自动售货机：售货机是通用属性配置文件（Generic Attribute Profile, GATT）服务器，货架是服务（Service），商品是特征值（Characteristic）。客户（GATT 客户端）先看目录（服务发现），再读取、投币写入，或订阅补货通知（Notify）。几乎所有 BLE 应用层数据交换都落在这套模型上[1]。

## 摘要

本文梳理 GATT 层次、标准与自定义 UUID、属性位、客户端特征值配置描述符（Client Characteristic Configuration Descriptor, CCCD），以及紧凑数据格式与 Zephyr 实现要点。默认最大传输单元（Maximum Transmission Unit, MTU）与通知可靠性等数字以规范与常见栈行为为准，**具体以协商结果为准**[1][3]。

## 1. GATT 基本概念

### 1.1 客户端–服务器

| 角色 | 持有数据？ | 典型设备 |
|------|------------|----------|
| GATT Server | 是 | 传感器、外设 |
| GATT Client | 否（请求方） | 手机、网关 |

Client/Server 与 Central/Peripheral 正交：常见 Peripheral=Server，但规范允许反转[1]。

### 1.2 层次与属性

```
Profile → Service → Characteristic → Value / Descriptor(CCCD 等)
```

每个属性含 Handle、Type（UUID）、Value、Permissions。

| 字段 | 大小倾向 | 说明 |
|------|----------|------|
| Handle | 16-bit | 服务器内索引 |
| Type | 16/128-bit UUID | 类型 |
| Value | 最长受 ATT 约束 | 实际数据 |
| Permissions | — | 读/写/加密等 |

## 2. 服务与 UUID

| 服务 | UUID | 用途 |
|------|------|------|
| Generic Access | 0x1800 | 名称、外观 |
| Generic Attribute | 0x1801 | 服务变更 |
| Battery | 0x180F | 电量 |
| Device Information | 0x180A | 厂商/型号/固件 |
| Heart Rate | 0x180D | 心率 |
| Environmental Sensing | 0x181A | 温湿度等 |

16-bit UUID 嵌入基础 UUID `0000XXXX-0000-1000-8000-00805F9B34FB`；自定义服务用随机 128-bit，并建议在同一基础 UUID 上递增分区编号以便文档化[2]。

## 3. 特征值属性

| 属性位 | 名称 | 说明 |
|--------|------|------|
| 0x02 | Read | 可读 |
| 0x04 | Write Without Response | 无应答写，更快 |
| 0x08 | Write | 有应答写 |
| 0x10 | Notify | 无应用层确认推送 |
| 0x20 | Indicate | 需 Confirmation |

| 方式 | 确认 | 吞吐倾向 | 适用 |
|------|------|----------|------|
| Notify | 无 | 高 | 周期传感器 |
| Indicate | 有 | 低 | 关键状态 |

默认 ATT MTU 常为 23（约 20 字节应用载荷）；更大载荷需先交换 MTU，并与数据长度扩展（Data Length Extension, DLE）对齐[1][7]。

## 4. CCCD

UUID `0x2902`：客户端写入后服务器才 Notify/Indicate。绑定场景下 CCCD 可持久化；未绑定连接断开后通常复位[1]。设计动机是省电——无人订阅则不推送。

## 5. 自定义服务设计

原则：功能分组、控制特征值数量、属性最小化、定点紧凑编码、预留版本字节。示例环境传感器：温度/湿度 Notify+Read，配置 Read+Write，LED Write Without Response；温度用 `int16` 表示 0.01°C。

| 做法 | 收益 | 风险 |
|------|------|------|
| 多传感器打包一特征值 | 少通知次数 | 解析耦合 |
| 分特征值 | 语义清晰 | 发现与空口更重 |
| 浮点直接传 | 省编码 | 字节序/尺寸差 |

## 6. 实现与调试

Zephyr 用 `BT_GATT_SERVICE_DEFINE` 注册主服务、特征与 `BT_GATT_CCC`；在线程上下文调用 `bt_gatt_notify`，避免在中断里直接发[3]。手机侧用 nRF Connect 等完成发现、写 CCCD、观察通知。

| 工具 | 用途 |
|------|------|
| nRF Connect | 读写/通知 |
| Wireshark + Sniffer | 空中包 |
| LightBlue 等 | 快速扫描 |

## 7. 安全与兼容

敏感写操作要求加密链路与认证；写回调校验长度；能用 SIG 标准服务则复用；小端字节序；iOS/Android 栈行为差异需实机测[4][5]。

## 8. 局限、挑战与可改进方向

### 1. 服务发现膨胀

**局限**：特征值过多拉长发现时间与耗电，弱网下易失败[1]。
**改进**：合并相关量；缓存发现结果；变更时用服务变更指示。

### 2. MTU/DLE 未对齐

**局限**：只开 Notify 仍用默认 MTU，大结构被截断或被迫分片。
**改进**：连接后交换 MTU；嵌入式侧同步提高 ACL 缓冲与 DLE[7]。

### 3. Notify 语义被高估

**局限**：应用层无 ACK，拥塞时栈可能丢待发通知。
**改进**：关键配置用 Write/Indicate；序列号+周期全量快照。

### 4. UUID 与文档漂移

**局限**：随机 UUID 无文档导致 App 硬编码错误。
**改进**：单一基础 UUID 规划；发布特征值字典与版本字段。

## 9. 实践要点

1. 传感器优先 Notify，控制类区分可靠写与快速写。
2. 生产固件关闭冗余日志，避免“调试态 GATT”与量产行为不一致。
3. 用 sniffer 确认 CCCD 与字节序，而不是只看 App UI。

## 参考文献

[1] Bluetooth SIG, "Bluetooth Core Specification," Vol 3 Part G: GATT.
[2] Bluetooth SIG, "Assigned Numbers" (16-bit UUIDs).
[3] Zephyr Project, Bluetooth GATT API documentation.
[4] Townsend, K. et al., "Getting Started with Bluetooth Low Energy," O'Reilly, 2014.
[5] Novel Bits / Afaneh, M., BLE GATT practical guides.
[6] Bluetooth SIG, "Generic Access Profile" related sections (GAP roles vs GATT).
[7] Bluetooth SIG, ATT MTU and Data Length Extension related core vol sections.
[8] Nordic Semiconductor, nRF Connect / GATT client testing documentation.
[9] Android Developers, BluetoothGatt / requestMtu documentation.
[10] Apple Core Bluetooth programming guides (MTU/CCCD behavior notes).
[11] Bluetooth SIG, Characteristic Descriptor assignments (e.g., 0x2902 CCCD).
