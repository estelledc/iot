# BACnet楼宇自动化IoT通信协议
> **难度**：🟡 中级 | **领域**：楼宇自动化 | **阅读时间**：约 20 分钟

## 引言

你每天走进办公楼, 空调自动调到舒适温度, 灯光根据自然光调节, 电梯知道哪层人多优先调度。这些"隐形服务"背后是庞大的楼宇自动化系统 -- 数千传感器、执行器、控制器协同工作。但空调厂商、照明厂商、门禁厂商各说各话, 就像住着说不同语言的邻居。BACnet就是这栋楼的"通用语言", 让所有楼宇设备用统一方式交换信息。不管大金空调还是西门子控制器, 只要说BACnet就能互相理解。

## 1 BACnet概述

### 1.1 标准背景

BACnet(Building Automation and Control Networks)由ASHRAE制定:

- 1995年: ASHRAE Standard 135首次发布
- 2003年: 成为ISO 16484-5国际标准
- 持续更新: 每隔几年发布新修订版
- 市场地位: 商业建筑自动化领域主导协议

### 1.2 设计目标

BACnet设计聚焦于: 不同厂商设备互操作、覆盖全部楼宇子系统(HVAC/照明/门禁/消防/电梯)、从单房间到摩天大楼可扩展、长生命周期(建筑50年以上)。

### 1.3 覆盖范围

| 子系统 | BACnet对象 | 典型应用 |
|--------|------------|----------|
| HVAC | 模拟输入/输出 | 温度控制, 新风调节 |
| 照明 | 二进制输出, 调度 | 灯光开关, 场景 |
| 门禁 | 凭证, 门锁对象 | 刷卡进入 |
| 消防 | 报警对象 | 烟感, 联动控制 |
| 电梯 | 升降机组对象 | 群控调度 |
| 能源 | 累积器 | 电表水表气表 |

## 2 对象模型

### 2.1 一切皆对象

楼宇中每个数据点被抽象为对象(Object), 每个对象有标准化属性(Property):

```
对象示例 - Analog Input, Instance 1:
+----------------------------------+
| Object_Name: "AHU-1 Supply Temp" |
| Present_Value: 23.5              |
| Units: degrees-Celsius           |
| Status_Flags: {in_alarm: false,  |
|   fault: false, overridden: false}|
| High_Limit: 28.0                 |
| Low_Limit: 16.0                  |
+----------------------------------+
```

### 2.2 输入/输出对象类型

| 类型 | 用途 | 示例 |
|------|------|------|
| Analog Input (AI) | 读模拟量 | 温度, 压力传感器 |
| Analog Output (AO) | 输出模拟量 | 阀门开度, 变频器 |
| Analog Value (AV) | 模拟量变量 | 设定值, 计算结果 |
| Binary Input (BI) | 读开关量 | 风机状态, 门磁 |
| Binary Output (BO) | 输出开关量 | 灯开关, 阀门 |
| Binary Value (BV) | 开关量变量 | 模式标志 |
| Multi-state Input (MSI) | 多状态输入 | 运行模式 |
| Multi-state Output (MSO) | 多状态输出 | 风机档位 |

### 2.3 功能对象类型

| 类型 | 用途 | 示例 |
|------|------|------|
| Schedule | 时间计划 | 工作日空调模式 |
| Calendar | 日历定义 | 节假日 |
| Trend Log | 趋势记录 | 温度历史数据 |
| Loop | PID控制 | 温度闭环 |
| Notification Class | 报警通知 | 高温报警方式 |
| Event Enrollment | 事件注册 | 条件触发报警 |

### 2.4 优先级数组

模拟/二进制输出对象有16级优先级数组(Priority Array):

```
Level 1:  手动生命安全(消防联动) -- 最高优先
Level 2:  自动生命安全
Level 5:  关键设备控制
Level 8:  手动操作(操作员覆写)
Level 16: 最低(默认自动控制)
```

多个控制源同时写入不同优先级, 设备执行最高有效优先级命令。消防联动永远优先于普通自动控制 -- 楼宇安全核心机制。

## 3 BACnet服务

### 3.1 设备发现

Who-Is / I-Am: 动态发现网络设备

```
控制器广播: Who-Is (设备范围: 1-1000)
设备10: I-Am (实例=10, 厂商=Trane, 型号=UC800)
设备15: I-Am (实例=15, 厂商=Honeywell, 型号=Spyder)
设备22: I-Am (实例=22, 厂商=Siemens, 型号=PXC)
```

### 3.2 数据访问

ReadProperty / WriteProperty:

```
读取: ReadProperty(设备=10, AI.1, Present_Value)
响应: 23.5

写入: WriteProperty(设备=10, AV.3, Present_Value, 24.0, 优先级=16)
响应: Success

ReadPropertyMultiple: 一次读多个属性减少交互
```

### 3.3 变化值订阅(COV)

SubscribeCOV(Change of Value): 值变化时才通知

```
1. 客户端: SubscribeCOV(设备=10, AI.1, 生存期=300s)
2. 服务器: SimpleACK确认
3. (AI.1值变化超过COV增量)
4. 服务器: COVNotification(新值=24.1)
5. 客户端: SimpleACK确认
```

避免轮询, 只传输有意义的变化, 天然契合IoT事件驱动模式。

### 3.4 报警与事件

完整报警机制: 事件注册监测条件(如温度超限), 触发生成通知发送多个接收者, 支持确认(Acknowledge)机制, 报警记录和历史查询。

## 4 网络层

### 4.1 BACnet/IP

最常用网络层, 运行在标准IP网络:

- UDP端口47808(十六进制0xBAC0)
- 广播用于设备发现, 单播用于点对点
- 与标准IT基础设施兼容

### 4.2 BBMD

BBMD(BACnet Broadcast Management Device)解决跨子网广播:

```
子网A: [设备1] [设备2] [BBMD-A] <--> [BBMD-B] [设备3] [设备4] :子网B
```

设备1的Who-Is广播通过BBMD转发到子网B, 实现跨子网设备发现。

### 4.3 BACnet MS/TP

RS-485串行总线用于现场级设备:

| 参数 | 值 |
|------|-----|
| 物理层 | RS-485差分信号 |
| 拓扑 | 菊花链 |
| 波特率 | 9600-115200 bps |
| 最大设备 | 127 |
| 最大距离 | 1200米 |
| 介质访问 | 令牌传递(Token Passing) |

典型应用: VAV末端控制器、温湿度传感器、风阀执行器。

### 4.4 BACnet/SC (Secure Connect)

2019年发布的最新网络层:

- 基于WebSocket: NAT友好, 防火墙友好
- TLS 1.3: 强制加密通信
- X.509证书: 每个节点需要证书认证
- Hub-Spoke拓扑: 中心Hub管理连接
- 云就绪: 可穿透企业防火墙连接云端

### 4.5 典型分层架构

```
[云平台/远程管理] --- BACnet/SC (安全穿透NAT)
        |
[楼宇管理工作站] --- BACnet/IP (以太网)
        |
[楼层DDC控制器] --- BACnet/IP (楼层交换机)
        |
[末端设备/传感器] --- BACnet MS/TP (RS-485总线)
```

## 5 IoT集成

### 5.1 BACnet到云端

**方式一 - BACnet/SC直连**: WebSocket/TLS穿透防火墙连接云端, 保持完整BACnet语义, 无需协议转换。

**方式二 - BACnet/MQTT网关**:

```
[BACnet设备] -> [BACnet/MQTT网关] -> [MQTT Broker] -> [IoT平台]
AI.1/Present_Value -> building/floor1/ahu1/supply_temp
```

COV订阅转MQTT发布, 可配置过滤和聚合。

**方式三 - RESTful API封装**:

```
GET /devices/10/objects/AI.1/present-value
Response: {"value": 23.5, "unit": "degC", "status": "good"}
```

### 5.2 COV与事件驱动

BACnet COV天然契合IoT: 只在值变化时通知避免无意义轮询, COV通知直接转为MQTT消息发布, 节省云端计算(只处理有意义变化)。

### 5.3 趋势日志导出

设备本地Trend Log可批量导出: 断网期间数据不丢失, 恢复连接后批量上传历史, 补全云端时序数据库空洞。

## 6 智慧楼宇应用

### 6.1 能源管理

```python
# 基于BACnet数据的能源优化概念
class EnergyOptimizer:
    def get_current_load(self):
        """读当前电力负荷"""
        return self.client.read_property(
            device=100, object_type="AI", instance=50,
            property="present_value")
    
    def set_demand_limit(self, limit_kw):
        """设需量限制避免峰值电费"""
        self.client.write_property(
            device=100, object_type="AV", instance=10,
            property="present_value", value=limit_kw, priority=14)
```

### 6.2 舒适度控制

多参数协同: 温度(AI) + 湿度(AI) + CO2(AI) 综合判断室内舒适度, 自动调整空调参数(AO), 记录历史趋势(Trend Log)。

### 6.3 预测性维护

基于BACnet数据监测设备健康: 风机运行小时数(累积器), 过滤器压差趋势(AI), 阀门行程异常(AO反馈偏差), 报警频率统计(事件日志)。

## 7 与其他楼宇协议对比

### 7.1 主要协议

| 协议 | 优势领域 | 特点 |
|------|----------|------|
| BACnet | HVAC, 综合管理 | 开放标准, 对象模型丰富 |
| KNX | 照明, 遮阳, 房间控制 | 分布式, 欧洲主导 |
| Modbus | 简单监测, 电力仪表 | 极简单, 无标准对象模型 |
| LonWorks | 综合楼控 | 市场份额下降 |
| DALI | 照明专用 | 专用照明总线 |

### 7.2 BACnet vs KNX

BACnet面向系统集成适合大型商业建筑集中管理; KNX面向分布式控制适合房间级舒适度。实际常见组合: KNX管房间级照明遮阳, BACnet管整体HVAC和能源。

### 7.3 BACnet vs Modbus

BACnet: 标准对象模型, 设备自描述, 真正互操作, 有发现/报警/调度/趋势功能。Modbus: 只有寄存器地址无语义, 需查手册, 但极简单几乎所有设备支持, 实现成本最低。

## 8 安全

### 8.1 传统安全问题

传统BACnet/IP和MS/TP几乎无安全: 无认证(任何人可读写)、无加密(明文传输)、无审计。历史原因: 设计时楼宇网络是物理隔离的。

### 8.2 BACnet/SC改进

| 安全需求 | BACnet/SC方案 |
|----------|---------------|
| 身份认证 | X.509证书 |
| 通信加密 | TLS 1.3强制 |
| 完整性 | TLS校验 |
| NAT穿透 | WebSocket |

### 8.3 网络级措施

即使不用BACnet/SC: VLAN隔离(楼控与办公网分离)、防火墙(限制47808端口)、VPN(远程访问加密)、流量监控(检测异常BACnet行为)。

## 9 实践案例: 商业办公楼

### 9.1 系统规模

20层办公楼: 5台AHU(BACnet/IP控制器), 200个VAV(MS/TP), 照明(BACnet/IP网关), 门禁, 能源计量。

### 9.2 网络架构

```
[云端AI平台] <-- BACnet/SC --> [SC Hub]
                                   |
[管理工作站] <-- BACnet/IP --> [IP路由器]
                                   |
            +------+------+------+------+
            |      |      |      |      |
          [AHU1][AHU2] [AHU3] [AHU4] [AHU5]
            |
       [MS/TP总线]
       |    |    |    |
     [VAV][VAV][VAV][VAV]...
```

### 9.3 数据流

温度传感器(MS/TP AI) -> VAV控制器 -> DDC主控 -> 管理工作站。BACnet/SC网关 -> 云端: COV数据流、能源数据、报警。云端AI -> 优化建议 -> 操作员确认 -> 写入设定值。

### 9.4 节能效果

BACnet数据驱动AI优化: 按需通风节省风机能耗约15%, 自适应启停减少预冷预热, 冷冻水温度优化综合COP提升约10%, 总体节能约20%。

## 10 未来发展

### 10.1 数字孪生

BACnet设备数据作为数字孪生实时源: 对象模型映射到孪生实体, COV通知驱动状态更新, 仿真结果写回设定值, 形成闭环优化。

### 10.2 新连接技术

WiFi 6确定性延迟适合楼宇控制, 5G专网可能取代部分RS-485布线, BACnet/SC的WebSocket基础使无线接入更容易。

### 10.3 与OPC UA融合

OPC UA for BACnet伴随规范正在制定: BACnet对象映射为OPC UA信息模型, 统一IT/OT数据访问层, 适合智慧园区(楼宇加工厂)场景。

## 总结

BACnet核心价值在于标准化对象模型。通过将温度、阀门、调度、报警等楼宇概念抽象为统一对象和属性, 实现不同厂商设备真正互操作。随着BACnet/SC引入和IoT平台集成深化, BACnet正从封闭楼控网络走向开放智慧楼宇生态。

对于IoT工程师, 理解BACnet不仅是学一个协议, 更是理解楼宇自动化的领域知识。BACnet对象模型(AI/AO/BI/BO/Schedule/TrendLog)本质上是楼宇运维经验的标准化编码, 掌握这些概念将帮助设计出真正贴合建筑运营需求的IoT方案。

## 参考文献

1. ASHRAE, "ANSI/ASHRAE Standard 135-2020: BACnet - A Data Communication Protocol for Building Automation and Control Networks", 2020.
2. ISO 16484-5:2022, "Building automation and control systems - Part 5: Data communication protocol", 2022.
3. Newman, H.M., "BACnet: The Global Standard for Building Automation and Control Networks", Momentum Press, 2013.
4. ASHRAE, "Addendum bj to Standard 135-2016: BACnet Secure Connect", 2019.
5. BACnet International, "BACnet Testing Laboratories (BTL) Listing Program", https://www.bacnetinternational.org.
