---
schema_version: '1.0'
id: matter-device-types-clusters
title: Matter设备类型与Cluster数据模型
layer: 2
content_type: UNKNOWN
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# Matter设备类型与Cluster数据模型
> **难度**：🟡 中级 | **领域**：Matter数据模型 | **阅读时间**：约 20 分钟

## 引言

想象你走进一家标准化的快餐店。无论在哪个城市,菜单的分类方式都是一样的:主食、饮料、小吃。每个分类下有固定的属性(价格、份量)和操作(点单、加料)。Matter的数据模型就像这套标准化菜单系统——它定义了智能设备"长什么样"、"能做什么",让所有控制器都能看懂并操作任何符合标准的设备。

本文将深入解析Matter数据模型的层次结构,从Node到Endpoint再到Cluster,理解设备类型如何通过Cluster组合来定义。

## 1. 数据模型层次概览

### 1.1 四层架构

Matter数据模型采用严格的层次结构,从上到下分为四层:

| 层级 | 名称 | 类比 | 说明 |
|------|------|------|------|
| 第一层 | Node | 整栋楼 | 物理设备,拥有唯一Node ID |
| 第二层 | Endpoint | 楼里的房间 | 逻辑子设备,编号从0开始 |
| 第三层 | Cluster | 房间里的功能区 | 一组相关功能的集合 |
| 第四层 | 元素 | 功能区的具体设施 | Attribute/Command/Event |

### 1.2 设计哲学与Zigbee传承

这套层次结构继承自Zigbee Cluster Library(ZCL)的设计遗产,但进行了现代化改进。标准化结构确保互操作性,分层解耦让物理设备与逻辑功能分离,同时支持厂商自定义扩展而不破坏标准兼容性。

```
Zigbee Cluster Library (ZCL)
    |
    v  继承 + 现代化改进
Matter Cluster 定义
    +-- 保留: 核心Cluster ID和语义
    +-- 改进: 更严格的类型系统
    +-- 新增: 适配IP网络的特性
```

## 2. Node与Endpoint

### 2.1 Node(节点)

Node代表一个物理设备在Matter fabric中的存在。每个Node拥有唯一的64位Node ID,通过commissioning过程加入fabric,可以同时属于多个fabric(多管理员)。

### 2.2 Endpoint(端点)

Endpoint是Node内部的逻辑子设备,用数字编号:

```
智能灯带 (Node)
|
+-- Endpoint 0: Root Node (系统管理)
+-- Endpoint 1: 灯带主控 (Color Temperature Light)
+-- Endpoint 2: 灯带氛围模式 (Extended Color Light)
```

关键规则: Endpoint 0保留给Root Node,承载系统级Cluster; Endpoint 1+为应用功能端点; 多功能设备通过多个Endpoint表达不同能力。

### 2.3 多功能设备示例

| Endpoint | 设备类型 | 功能 |
|----------|----------|------|
| 0 | Root Node | 系统管理 |
| 1 | Dimmable Light | 可调光灯 |
| 2 | Fan | 风扇控制 |

控制器看到这个Node时,能分别独立控制灯和风扇。

## 3. Cluster核心概念

### 3.1 Cluster定义

Cluster是一组相关功能的逻辑分组,包含三类元素: Attribute(属性)表示状态; Command(命令)触发动作; Event(事件)通知变化。

### 3.2 Cluster标识与角色

每个Cluster由32位Cluster ID标识。标准Cluster范围为0x0000_0000到0x0000_7FFF(CSA定义),厂商自定义范围为0xFFF1_0000到0xFFF4_FFFE。

每个Cluster有Server和Client两个角色: Server持有数据和状态(如灯保存亮度), Client发起请求(如开关发送开灯命令)。

```
[开关] Client ---> OnOff Cluster ---> Server [灯]
          发送Toggle命令            执行切换
```

### 3.3 Attribute详解

```
OnOff Cluster 的 Attribute:
+------------------+--------+--------+--------+
| Attribute        | ID     | 类型   | 访问   |
+------------------+--------+--------+--------+
| OnOff            | 0x0000 | bool   | 只读   |
| GlobalSceneCtrl  | 0x4000 | bool   | 只读   |
| OnTime           | 0x4001 | uint16 | 读写   |
| OffWaitTime      | 0x4002 | uint16 | 读写   |
| StartUpOnOff     | 0x4003 | enum8  | 读写   |
+------------------+--------+--------+--------+
```

### 3.4 Command与Event

Command是触发动作的指令,如OnOff Cluster的Off(0x00)、On(0x01)、Toggle(0x02)。Event是异步通知,带时间戳和优先级,如Switch Cluster的InitialPress、LongPress、MultiPressOngoing等。

## 4. 常用标准Cluster

### 4.1 控制类Cluster

**OnOff Cluster (0x0006)**: 最基础的开关控制,属性为OnOff状态,命令为On/Off/Toggle。

**Level Control Cluster (0x0008)**: 连续值控制(亮度、音量等),属性CurrentLevel范围0-254,命令包括MoveToLevel/Move/Step/Stop。

**Color Control Cluster (0x0300)**: 颜色控制,属性包括Hue/Saturation/ColorTemperature,命令包括MoveToHue/MoveToSaturation/MoveToColorTemperature。

### 4.2 传感器与安防类Cluster

**Temperature Measurement (0x0402)**: 温度传感器读数,属性为MeasuredValue/MinMeasuredValue/MaxMeasuredValue,无命令。

**Occupancy Sensing (0x0406)**: 人体存在检测,属性为Occupancy位图和OccupancySensorType。

**Door Lock (0x0101)**: 门锁控制,属性为LockState/LockType,命令为LockDoor/UnlockDoor,事件包括DoorLockAlarm。

## 5. 设备类型(Device Type)

### 5.1 设备类型的作用

设备类型是Cluster的标准化组合,定义产品品类必须具备的最低功能。这确保任何"可调光灯"都至少支持OnOff和LevelControl,控制器看到设备类型就知道能做什么。

### 5.2 设备类型列表

| 设备类型 | 必选Cluster | 功能 |
|----------|-------------|------|
| On/Off Light | OnOff, Identify | 只能开关 |
| Dimmable Light | OnOff, LevelControl, Identify | 可调亮度 |
| Color Temperature Light | OnOff, LevelControl, ColorControl | 可调色温 |
| Temperature Sensor | TemperatureMeasurement | 测温 |
| Occupancy Sensor | OccupancySensing | 人体检测 |
| Contact Sensor | BooleanState | 门窗开合 |
| Thermostat | Thermostat, Identify | 温控器 |
| Door Lock | DoorLock, Identify | 门锁 |
| On/Off Plug | OnOff, Identify | 智能插座 |

### 5.3 必选与可选Cluster

每个设备类型规范明确列出必选和可选Cluster:

```
Dimmable Light 设备类型规范:
+-------------------+--------+--------+
| Cluster           | 角色   | 要求   |
+-------------------+--------+--------+
| Identify          | Server | 必选   |
| Groups            | Server | 必选   |
| OnOff             | Server | 必选   |
| Level Control     | Server | 必选   |
| Scenes Management | Server | 可选   |
+-------------------+--------+--------+
```

## 6. Descriptor Cluster与设备发现

### 6.1 核心发现机制

Descriptor Cluster是每个Endpoint必备的系统Cluster,告诉控制器"这个端点上有什么":

```
Descriptor Cluster 属性:
+------------------+-----------------------------------+
| 属性             | 说明                              |
+------------------+-----------------------------------+
| DeviceTypeList   | 此端点实现的设备类型列表          |
| ServerList       | 此端点上的Server Cluster列表      |
| ClientList       | 此端点上的Client Cluster列表      |
| PartsList        | 子端点列表(组合设备用)            |
+------------------+-----------------------------------+
```

### 6.2 设备发现流程

控制器发现新设备的标准流程: 读取Endpoint 0的Descriptor获取PartsList, 遍历每个Endpoint读取Descriptor, 从DeviceTypeList确定设备类型, 从ServerList确定可用功能, 构建设备UI和控制界面。

## 7. 交互模式

### 7.1 四种基本交互

```
Read: Controller读取属性获取状态
  Path: Endpoint 1 / OnOff Cluster / OnOff Attribute
  Response: true (灯开着)

Write: Controller修改可写属性
  Path: Endpoint 1 / LevelControl / OnLevel -> 200

Invoke: Controller调用命令执行动作
  Path: Endpoint 1 / OnOff / Toggle

Subscribe: Controller订阅属性变化获取实时更新
  Path: Endpoint 1 / OnOff / OnOff
  MinInterval: 0s, MaxInterval: 60s
  -> 状态变化时自动推送报告
```

## 8. Binding与Groups

### 8.1 Binding(绑定)

Binding实现设备间直接通信,无需控制器中转:

```
场景: 墙壁开关直接控制灯
[开关] --Binding--> [灯]

配置: 在开关的Binding Cluster中添加:
  Target: Node X, Endpoint 1, Cluster: OnOff
```

按下开关时命令直接发送给灯,即使控制器离线也能工作。

### 8.2 Groups(群组)

Groups实现一对多控制。通过IPv6多播地址,一条消息同时到达所有组成员:

```
Group ID: 0x0001 (客厅灯组)
成员: 灯A-Endpoint1, 灯B-Endpoint1, 灯C-Endpoint1
控制: 发送 OnOff/Toggle 到 Group 0x0001
结果: 三盏灯同时切换状态
```

## 9. 实际案例: 带能耗监测的智能插座

```
智能插座 Node (Node ID: 0x1234)
|
+-- Endpoint 0: Root Node
|   +-- Basic Information Cluster
|   +-- Network Commissioning Cluster
|
+-- Endpoint 1: On/Off Plug-in Unit
    +-- Descriptor Cluster
    |   DeviceTypeList: [On/Off Plug-in Unit]
    |   ServerList: [OnOff, ElectricalPowerMeasurement,
    |                PowerSource, Identify]
    +-- OnOff Cluster (Server)
    |   Commands: On, Off, Toggle
    +-- Electrical Power Measurement Cluster (Server)
    |   Attributes: ActivePower, Voltage, ActiveCurrent
    +-- Identify Cluster (Server)
```

控制器交互: 读取Descriptor得知设备类型, Invoke Toggle开关插座, Subscribe ActivePower监测功耗, 实时展示瓦数并在异常时通知。

## 10. 可扩展性

### 10.1 厂商自定义Cluster

厂商可以添加私有功能而不破坏标准兼容性:

```
Endpoint 1: Dimmable Light
  +-- OnOff Cluster (标准, 必选)
  +-- Level Control Cluster (标准, 必选)
  +-- Vendor Specific Cluster (厂商自定义)
      Cluster ID: 0xFFF10001
      Attributes: 自定义呼吸灯模式, 自定义节律参数
```

### 10.2 互操作性保证

关键原则: 必须先实现所有必选标准Cluster; 自定义Cluster是额外的,不替代标准功能; 不认识自定义Cluster的控制器可以安全忽略; 标准功能始终可用,厂商功能锦上添花。

### 10.3 标准演进

CSA持续扩展Matter标准:

- 新版本添加新的标准Cluster(如机器人吸尘器、摄像头、能源管理)
- 新设备类型定义新的Cluster组合要求
- 向后兼容: 旧设备不受新标准影响,新控制器仍能操作旧设备
- 厂商可以提前用自定义Cluster实现功能,待标准化后迁移到标准ID

### 10.4 开发实践建议

开发Matter设备时的数据模型设计原则:

```
1. 确定产品品类 -> 查找对应Device Type规范
2. 实现所有必选Cluster (不可省略)
3. 根据产品特点选择可选Cluster
4. 如需私有功能 -> 使用厂商自定义Cluster ID范围
5. 测试: 确保标准Controller能正确发现和操作基本功能
```

## 总结

Matter数据模型通过Node-Endpoint-Cluster-Attribute/Command/Event的层次结构,为智能家居设备建立了统一的"语言"。Node是物理设备的网络身份,Endpoint将多功能设备拆分为独立逻辑单元,Cluster是功能的标准化封装,Device Type通过Cluster组合定义产品品类最低要求,Descriptor Cluster让控制器能自动发现和理解任何设备,Binding和Groups支持设备间直接通信和组控制。这套体系源自Zigbee十多年的实践积累,是跨厂商互操作的基石。

## 参考文献

- [Matter Specification - Data Model](https://csa-iot.org/developer-resource/specifications-download-request/) - CSA官方Matter规范数据模型章节
- [Matter Device Library Specification](https://csa-iot.org/developer-resource/specifications-download-request/) - 设备类型定义规范
- [Project CHIP - Device Types](https://github.com/project-chip/connectedhomeip/tree/master/src/app/zap-templates/zcl/data-model) - 开源实现中的数据模型定义
- [Zigbee Cluster Library Specification](https://csa-iot.org/developer-resource/specifications-download-request/) - Matter Cluster的历史起源
