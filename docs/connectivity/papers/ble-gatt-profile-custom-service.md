# BLE GATT自定义服务与特征值设计
> **难度**：🟢 初级 | **领域**：BLE应用开发 | **阅读时间**：约 18 分钟

## 引言

把 BLE 设备想象成一个自动售货机。售货机（GATT Server）上有多个货架（Service），每个货架放着不同类型的商品（Characteristic）。你（GATT Client）走到售货机前，先看一眼目录牌了解有哪些货架和商品（Service Discovery），然后可以查看某个商品的信息（Read）、投币购买（Write），或者订阅补货通知（Notify）——有新货到了售货机主动告诉你。

GATT（Generic Attribute Profile）是 BLE 数据交换的核心协议。几乎所有 BLE 应用层通信都建立在 GATT 之上：心率监测、温湿度传感器、智能灯控制、固件升级——都是通过定义合适的 Service 和 Characteristic 来实现的。

本文将从 GATT 的基本概念讲起，逐步深入到如何设计和实现自定义服务，适合刚接触 BLE 应用开发的读者。

## 1. GATT 基本概念

### 1.1 客户端-服务器模型

GATT 采用客户端-服务器（Client-Server）架构：

- **GATT Server（服务端）**：持有数据的设备，通常是传感器、外设
- **GATT Client（客户端）**：请求数据的设备，通常是手机、网关

```
手机 (Client)                    传感器 (Server)
    |                                |
    |-- Discover Services ---------->|
    |<-- Service List ---------------|
    |                                |
    |-- Read Characteristic -------->|
    |<-- Value ----------------------|
    |                                |
    |-- Enable Notification -------->|
    |<-- Notification (主动推送) ----|
    |<-- Notification ---------------|
```

注意：Client/Server 角色与 Central/Peripheral 角色是独立的概念。虽然通常 Peripheral 是 Server、Central 是 Client，但技术上可以反转。

### 1.2 GATT 层次结构

GATT 的数据组织是严格的层次结构：

```
Profile（配置文件）
  |
  +-- Service（服务）         [UUID标识]
  |     |
  |     +-- Characteristic（特征值）  [UUID标识]
  |     |     |
  |     |     +-- Value（值）          [实际数据]
  |     |     +-- Descriptor（描述符）  [元数据]
  |     |           |
  |     |           +-- CCCD (0x2902)  [通知开关]
  |     |           +-- 用户描述 (0x2901)
  |     |
  |     +-- Characteristic
  |           |
  |           +-- Value
  |           +-- Descriptor
  |
  +-- Service
        |
        +-- ...
```

### 1.3 属性（Attribute）基础

GATT 层次中的每个元素本质上都是一个属性（Attribute），包含四个字段：

| 字段 | 大小 | 说明 |
|------|------|------|
| Handle | 16-bit | 属性在服务器上的唯一索引号 |
| Type | 16/128-bit UUID | 标识属性的类型 |
| Value | 0-512 bytes | 属性的实际数据 |
| Permissions | - | 读/写/加密等访问权限 |

Handle 是 Client 访问 Server 上特定属性时使用的"地址"，在服务发现阶段获取。

## 2. 服务（Service）

### 2.1 服务的定义

服务是一组逻辑相关的特征值的集合。例如"心率服务"包含心率测量值、身体传感器位置等特征值。

服务分为两类：

- **主服务（Primary Service）**：设备的主要功能，可被发现
- **次服务（Secondary Service）**：被其他服务包含引用的辅助服务（较少使用）

### 2.2 服务 UUID

每个服务由 UUID 唯一标识：

**16位 UUID（SIG 标准服务）**：

蓝牙 SIG 预定义了一系列标准服务，使用 16 位短 UUID。完整的 128 位形式是将 16 位值嵌入蓝牙基础 UUID：

```
基础 UUID: 0000XXXX-0000-1000-8000-00805F9B34FB
         (XXXX 替换为16位UUID)

例: Battery Service = 0x180F
完整: 0000180F-0000-1000-8000-00805F9B34FB
```

**128位 UUID（自定义服务）**：

自定义服务使用完整的 128 位 UUID，通常使用 UUID 生成工具随机生成：

```
例: 12345678-1234-5678-1234-56789ABCDEF0
```

### 2.3 常见标准服务

| 服务名称 | UUID | 用途 |
|----------|------|------|
| Generic Access | 0x1800 | 设备名称、外观等基本信息 |
| Generic Attribute | 0x1801 | 服务变更通知 |
| Battery Service | 0x180F | 电池电量 |
| Device Information | 0x180A | 厂商、型号、固件版本等 |
| Heart Rate | 0x180D | 心率测量 |
| Environmental Sensing | 0x181A | 温度、湿度、气压等 |
| Automation IO | 0x1815 | 数字/模拟IO控制 |

## 3. 特征值（Characteristic）

### 3.1 特征值的组成

一个特征值由以下部分组成：

```
Characteristic Declaration (声明)
  - Properties: 该特征值支持的操作
  - Value Handle: 指向值的句柄
  - UUID: 特征值的类型标识

Characteristic Value (值)
  - 实际数据内容

Characteristic Descriptor(s) (描述符，可选)
  - CCCD: 客户端配置（开关通知/指示）
  - 用户描述: 人类可读的文字描述
  - 格式描述: 数据格式、单位等
```

### 3.2 特征值属性（Properties）

Properties 字段定义了客户端可以对该特征值执行的操作：

| 属性位 | 名称 | 说明 |
|--------|------|------|
| 0x01 | Broadcast | 可在广播中携带 |
| 0x02 | Read | 客户端可读取 |
| 0x04 | Write Without Response | 写入无需应答（快速） |
| 0x08 | Write | 写入需要应答（可靠） |
| 0x10 | Notify | 服务端主动推送（无应答） |
| 0x20 | Indicate | 服务端主动推送（需应答） |
| 0x40 | Auth Signed Write | 带签名的写入 |
| 0x80 | Extended Properties | 有扩展属性描述符 |

一个特征值可以同时具有多个属性，例如 Read + Notify 表示既可以主动读取也可以订阅通知。

### 3.3 Notify vs Indicate

两者都是服务端主动推送数据给客户端，区别在于：

```
Notify (通知):
  Server --[数据]--> Client  (无应答，可能丢失)
  优点：速度快，开销小
  缺点：不保证送达

Indicate (指示):
  Server --[数据]--> Client
  Client --[确认]--> Server  (有应答，可靠传输)
  优点：保证送达
  缺点：速度慢（等待确认才能发下一个）
```

大多数物联网传感器使用 Notify，因为传感器数据通常是周期性的，偶尔丢一包影响不大。对于关键控制指令或配置确认，使用 Indicate 更合适。

## 4. 客户端特征值配置描述符（CCCD）

### 4.1 CCCD 的作用

CCCD（Client Characteristic Configuration Descriptor，UUID = 0x2902）是 Notify/Indicate 机制的"开关"。客户端必须先写入 CCCD 来启用通知，服务端才会开始推送数据。

```c
// CCCD 值定义
#define CCCD_DISABLE          0x0000  // 关闭通知和指示
#define CCCD_NOTIFY_ENABLE    0x0001  // 开启通知
#define CCCD_INDICATE_ENABLE  0x0002  // 开启指示
```

### 4.2 为什么需要 CCCD

设计 CCCD 的原因是省电：如果没有客户端关心某个数据，服务端就不需要浪费功耗去发送通知。只有当客户端明确表示"我要接收这个数据"时，服务端才开始推送。

### 4.3 CCCD 的持久化

CCCD 的值是按客户端存储的（per-client per-characteristic）。在配对绑定的场景下，CCCD 值会持久保存——设备重新连接后不需要重新使能通知。未配对的连接中，CCCD 在断连后重置。

## 5. 设计自定义服务

### 5.1 设计原则

设计自定义 GATT 服务时需要考虑：

1. **功能分组**：相关数据放在同一个 Service 下
2. **减少特征值数量**：每个特征值有开销，必要时将多个数据打包到一个特征值中
3. **选择合适的属性**：只开放需要的操作
4. **数据格式紧凑**：BLE 带宽有限，使用定点数替代浮点数
5. **版本兼容**：预留版本字段，方便未来扩展

### 5.2 UUID 规划

为自定义服务规划 UUID 的推荐方式：

```
定义一个基础 UUID（随机生成128位）:
  XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX

服务UUID:   基础UUID的第1-4字节设为 0001
特征值1:    基础UUID的第1-4字节设为 0002
特征值2:    基础UUID的第1-4字节设为 0003
...

例:
基础:  A0E5F9B0-1234-5678-9ABC-DEF012345678
服务:  A0E50001-1234-5678-9ABC-DEF012345678
温度:  A0E50002-1234-5678-9ABC-DEF012345678
湿度:  A0E50003-1234-5678-9ABC-DEF012345678
配置:  A0E50004-1234-5678-9ABC-DEF012345678
```

这种规划方式使得服务和特征值的 UUID 有规律可循，便于文档化和调试。

### 5.3 实际设计案例：物联网环境传感器

设计一个包含温湿度传感器和 LED 指示灯的物联网设备服务：

```
IoT Sensor Service (A0E50001-...)
  |
  +-- Temperature Characteristic (A0E50002-...)
  |     Properties: Notify + Read
  |     Format: int16, 单位 0.01C (2500 = 25.00C)
  |     CCCD: 允许客户端启用温度通知
  |
  +-- Humidity Characteristic (A0E50003-...)
  |     Properties: Notify + Read
  |     Format: uint16, 单位 0.01% (6500 = 65.00%)
  |     CCCD: 允许客户端启用湿度通知
  |
  +-- Config Characteristic (A0E50004-...)
  |     Properties: Read + Write
  |     Format: struct { uint8 interval_s; uint8 mode; }
  |     用途: 配置采样间隔和工作模式
  |
  +-- LED Control Characteristic (A0E50005-...)
        Properties: Write Without Response
        Format: uint8 (0=OFF, 1=RED, 2=GREEN, 3=BLUE)
        用途: 控制设备指示灯颜色
```

## 6. 数据格式设计

### 6.1 整数定点表示

BLE 数据传输中应避免使用浮点数（float 占 4 字节且需要处理字节序），推荐使用定点整数：

```c
// 温度表示方案对比
// 方案A (浮点): float temp = 25.73;  // 4字节，需处理IEEE 754
// 方案B (定点): int16_t temp = 2573; // 2字节，除以100得到实际值

// 编码
float actual_temp = 25.73;
int16_t encoded = (int16_t)(actual_temp * 100);  // 2573

// 解码 (客户端)
int16_t received = 2573;
float decoded = received / 100.0f;  // 25.73
```

### 6.2 多值打包

将多个相关数据打包到一个特征值中可以减少交互次数：

```c
// 方案A: 分开的特征值 (3次通知)
// Temperature: 2 bytes
// Humidity:    2 bytes
// Battery:     1 byte

// 方案B: 打包到一个特征值 (1次通知, 推荐)
struct __attribute__((packed)) sensor_data {
    int16_t  temperature;  // 0.01C
    uint16_t humidity;     // 0.01%
    uint8_t  battery;      // 百分比 0-100
    uint8_t  status;       // 状态标志位
};
// 总共 6 字节，一次 Notify 搞定
```

### 6.3 版本字段

为未来扩展预留版本标识：

```c
struct __attribute__((packed)) sensor_data_v1 {
    uint8_t  version;      // = 1, 客户端据此解析
    int16_t  temperature;
    uint16_t humidity;
    uint8_t  battery;
};

// 未来扩展 v2 时，客户端可以根据 version 字段
// 判断数据格式，实现前向兼容
```

## 7. Zephyr RTOS 实现示例

### 7.1 定义自定义服务

```c
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/uuid.h>

// 定义 UUID
#define SENSOR_SERVICE_UUID \
    BT_UUID_128_ENCODE(0xA0E50001, 0x1234, 0x5678, 0x9ABC, 0xDEF012345678)
#define TEMP_CHAR_UUID \
    BT_UUID_128_ENCODE(0xA0E50002, 0x1234, 0x5678, 0x9ABC, 0xDEF012345678)
#define LED_CHAR_UUID \
    BT_UUID_128_ENCODE(0xA0E50005, 0x1234, 0x5678, 0x9ABC, 0xDEF012345678)

static struct bt_uuid_128 sensor_svc_uuid = BT_UUID_INIT_128(SENSOR_SERVICE_UUID);
static struct bt_uuid_128 temp_char_uuid = BT_UUID_INIT_128(TEMP_CHAR_UUID);
static struct bt_uuid_128 led_char_uuid = BT_UUID_INIT_128(LED_CHAR_UUID);

// 温度数据
static int16_t temperature_value = 2500; // 25.00C

// 温度特征值读取回调
static ssize_t read_temperature(struct bt_conn *conn,
                                const struct bt_gatt_attr *attr,
                                void *buf, uint16_t len, uint16_t offset)
{
    return bt_gatt_attr_read(conn, attr, buf, len, offset,
                            &temperature_value, sizeof(temperature_value));
}

// LED 控制写入回调
static ssize_t write_led(struct bt_conn *conn,
                         const struct bt_gatt_attr *attr,
                         const void *buf, uint16_t len,
                         uint16_t offset, uint8_t flags)
{
    if (len != 1) {
        return BT_GATT_ERR(BT_ATT_ERR_INVALID_ATTRIBUTE_LEN);
    }

    uint8_t led_color = *((uint8_t *)buf);
    // 根据 led_color 控制硬件 LED
    set_led_color(led_color);

    return len;
}
```

### 7.2 注册服务

```c
// 使用宏注册 GATT 服务
BT_GATT_SERVICE_DEFINE(sensor_svc,
    // 服务声明
    BT_GATT_PRIMARY_SERVICE(&sensor_svc_uuid),

    // 温度特征值: Read + Notify
    BT_GATT_CHARACTERISTIC(&temp_char_uuid.uuid,
                           BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY,
                           BT_GATT_PERM_READ,
                           read_temperature, NULL, &temperature_value),
    // CCCD (自动添加，因为有 NOTIFY 属性)
    BT_GATT_CCC(temp_ccc_changed, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),

    // LED 控制特征值: Write Without Response
    BT_GATT_CHARACTERISTIC(&led_char_uuid.uuid,
                           BT_GATT_CHRC_WRITE_WITHOUT_RESP,
                           BT_GATT_PERM_WRITE,
                           NULL, write_led, NULL),
);

// CCCD 状态变更回调
static void temp_ccc_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
    bool notify_enabled = (value == BT_GATT_CCC_NOTIFY);
    printk("Temperature notifications %s\n",
           notify_enabled ? "enabled" : "disabled");
}
```

### 7.3 发送通知

```c
// 更新温度并发送通知
void update_temperature(int16_t new_temp)
{
    temperature_value = new_temp;

    // 向所有已启用通知的客户端发送
    int err = bt_gatt_notify(NULL, &sensor_svc.attrs[2],
                            &temperature_value, sizeof(temperature_value));
    if (err && err != -ENOTCONN) {
        printk("Notify failed (err %d)\n", err);
    }
}

// 周期性采样和通知（在主循环或定时器中调用）
void sensor_sample_timer_handler(void)
{
    int16_t raw_temp = read_sensor_hardware();
    update_temperature(raw_temp);
}
```

## 8. 手机端交互流程

### 8.1 完整交互序列

从手机 App 角度，与自定义 BLE 服务交互的完整流程：

```
1. 扫描 (Scan)
   发现设备广播，获取设备地址和名称

2. 连接 (Connect)
   建立 BLE 连接，完成参数协商

3. 服务发现 (Discover Services)
   遍历 Server 上所有服务和特征值
   获取每个特征值的 Handle

4. 读取初始值 (Read)
   读取温度当前值
   读取配置当前值

5. 使能通知 (Write CCCD)
   写入 CCCD = 0x0001 开启温度通知

6. 接收通知 (Notification Callback)
   持续接收服务端推送的温度更新

7. 写入控制 (Write)
   写入 LED 颜色值控制指示灯
   写入配置修改采样间隔

8. 断开 (Disconnect)
   结束通信
```

### 8.2 常见开发工具

调试自定义 GATT 服务的工具：

| 工具 | 平台 | 用途 |
|------|------|------|
| nRF Connect | iOS/Android | 扫描、连接、读写特征值 |
| LightBlue | iOS/Android | 类似 nRF Connect |
| Wireshark + nRF Sniffer | PC | 抓取空中 BLE 数据包 |
| BLE Scanner | Android | 轻量级扫描工具 |

使用 nRF Connect 的典型调试流程：

1. 打开 App，扫描找到设备
2. 点击连接，自动进行服务发现
3. 展开自定义服务，看到各特征值
4. 点击向下箭头启用 Notify
5. 观察通知数据是否正确
6. 点击向上箭头写入数据测试写操作

## 9. 最佳实践

### 9.1 性能优化

- **减少服务发现时间**：特征值数量直接影响发现耗时，保持精简
- **使用 Notify 而非轮询**：Read 轮询浪费双方功耗，Notify 按需推送
- **批量打包数据**：一次 Notify 发送多个传感器值，减少通知次数
- **合理设置 MTU**：协商更大 MTU 可以在一个包中发送更多数据

### 9.2 安全考虑

- **敏感数据加密**：对配置写入要求加密连接（Encrypted Link）
- **认证写入**：关键控制操作要求配对认证
- **只读保护**：传感器数据只设 Read/Notify，不开放 Write
- **长度校验**：Write 回调中始终检查数据长度

### 9.3 兼容性建议

- **遵循标准**：能用标准服务就不自定义（如 Battery Service）
- **文档化数据格式**：为每个特征值编写清晰的数据格式文档
- **小端字节序**：BLE 标准规定使用小端（Little-Endian）
- **测试多平台**：iOS 和 Android 的 BLE 栈行为有差异

### 9.4 常见错误避免

```c
// 错误1: 忘记检查 Notify 是否已启用就发送
// 正确做法: bt_gatt_notify 内部会检查，但最好自己也维护状态

// 错误2: 特征值数据超过 MTU
// 默认 MTU=23, ATT header=3, 有效载荷最多20字节
// 如果数据超过 MTU-3 字节，需要先协商更大 MTU

// 错误3: 在中断上下文中调用 bt_gatt_notify
// 通知发送应在线程上下文中进行，中断中应设置标志位

// 错误4: 没有处理断连后的清理
// 断连后需要重置相关状态，等待重新连接
```

## 总结

GATT 是 BLE 应用开发的基础框架，理解它的层次结构（Service -> Characteristic -> Descriptor）和通信模式（Read/Write/Notify/Indicate）是开发任何 BLE 产品的前提。

设计自定义服务的核心思路是：先明确设备需要暴露哪些数据和控制接口，再按照功能分组组织成 Service，为每个数据点选择合适的 Properties 和数据格式，最后考虑安全性和兼容性。

记住几个关键原则：Notify 优于 Read 轮询、打包优于分散、定点整数优于浮点、始终文档化数据格式。这些原则能帮你设计出高效、低功耗、易维护的 BLE 服务。

## 参考文献

1. Bluetooth SIG. "GATT (Generic Attribute Profile) Specification." Bluetooth Core Specification v5.3, Vol 3, Part G.
2. Bluetooth SIG. "Assigned Numbers - 16-bit UUIDs." https://www.bluetooth.com/specifications/assigned-numbers/
3. Nordic Semiconductor. "Zephyr BLE GATT Documentation." https://docs.zephyrproject.org/latest/connectivity/bluetooth/api/gatt.html
4. Townsend, K. et al. "Getting Started with Bluetooth Low Energy." O'Reilly Media, 2014.
5. Afaneh, M. "The Ultimate Guide to BLE GATT." Novel Bits, 2021.
