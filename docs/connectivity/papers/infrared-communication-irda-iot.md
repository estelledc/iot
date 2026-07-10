---
schema_version: '1.0'
id: infrared-communication-irda-iot
title: 红外通信IrDA在IoT遥控中的应用与局限
layer: 2
content_type: UNKNOWN
difficulty: beginner
reading_time: 18
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 红外通信IrDA在IoT遥控中的应用与局限
> **难度**：🟢 初级 | **领域**：红外通信 | **阅读时间**：约 18 分钟

## 引言

想象你在客厅里拿起电视遥控器,对着电视按下开关键,电视瞬间亮了起来。这个再日常不过的动作背后,其实隐藏着一种历史悠久的无线通信技术——红外通信。遥控器前端的小灯珠发出人眼看不见的红外光,电视机上的接收器捕捉到这束光,解码出"开机"指令,整个过程在毫秒间完成。

红外通信就像用手电筒打摩斯密码:你对着对方闪灯,对方看到闪烁的规律就能读出信息。只不过红外通信用的"手电筒"发出的是人眼不可见的红外光,闪烁的速度也远比人手快得多。这种"用光传信"的方式,决定了红外通信的核心特征——必须"看得见"才能通信,挡住光路就断了联系。

在物联网时代,虽然WiFi、蓝牙、Zigbee等射频技术已经成为主流,但红外通信并没有完全退场。恰恰相反,它在智能家居领域扮演着一个独特的角色:作为"桥梁",让那些只支持红外遥控的传统家电也能接入智能家居系统。本文将系统介绍红外通信的原理、IrDA标准、IoT中的应用场景,以及它不可避免的局限性。

## 1. 红外通信基础原理

### 1.1 什么是红外光

红外光是电磁波谱中波长在700nm到1mm之间的部分,人眼无法看到。在通信领域,常用的红外波长集中在850nm到950nm之间,这个波段的红外LED制造成本低、效率高,且与硅基光电二极管的响应特性匹配良好。

红外通信的基本架构非常简单:

- 发送端: 红外LED(发光二极管),通电时发出红外光
- 接收端: 光电二极管或光电晶体管,检测红外光并转换为电信号
- 调制方式: 通过控制LED的亮灭模式来编码数据

### 1.2 载波调制

直接用LED的亮灭来表示0和1会遇到一个问题:环境中充满了红外光源(太阳光、白炽灯等),接收器无法区分通信信号和环境噪声。解决方案是使用载波调制。

发送端将数据信号调制到一个特定频率的载波上,通常是36kHz到40kHz之间。接收端配备一个带通滤波器,只响应该载波频率附近的信号,从而滤除环境噪声。常见的一体化红外接收头(如TSOP38238)内部集成了滤波、放大和解调电路,直接输出解调后的数字信号。

```
发送端流程:
数据位 -> 载波调制(38kHz) -> 驱动红外LED -> 发出调制红外光

接收端流程:
光电二极管 -> 带通滤波(38kHz) -> 放大 -> 解调 -> 输出数字信号
```

### 1.3 编码协议

红外遥控领域有多种编码协议,最常见的三种如下。

NEC协议是目前使用最广泛的红外遥控协议。它使用脉冲距离编码(Pulse Distance Encoding):逻辑"1"和逻辑"0"都以一个562.5us的脉冲开始,区别在于脉冲后的间隔时间不同。逻辑"1"的间隔为1687.5us,逻辑"0"的间隔为562.5us。一帧完整的NEC数据包含引导码、8位地址、8位地址反码、8位命令、8位命令反码。

RC5协议由飞利浦开发,使用曼彻斯特编码(Manchester Encoding):每个位周期的中间发生电平跳变,从低到高表示逻辑"1",从高到低表示逻辑"0"。RC5帧包含2位起始位、1位翻转位、5位地址和6位命令。

Sony SIRC协议使用脉冲宽度编码(Pulse Width Encoding):逻辑"1"的脉冲宽度为1200us,逻辑"0"为600us,间隔固定为600us。根据版本不同有12位、15位和20位三种格式。

## 2. IrDA标准体系

### 2.1 IrDA协会与标准演进

IrDA(Infrared Data Association,红外数据协会)成立于1993年,目标是制定红外数据通信的行业标准。与遥控器使用的单向、低速红外通信不同,IrDA标准面向的是设备间的双向数据交换,例如手机与打印机之间传文件、PDA与电脑同步数据等。

IrDA标准的速率经历了多次升级:

| 标准 | 速率 | 发布年份 | 说明 |
|------|------|----------|------|
| SIR | 115.2kbps | 1994 | 兼容串口速率 |
| MIR | 1.152Mbps | 1995 | 中速扩展 |
| FIR | 4Mbps | 1996 | 快速红外 |
| VFIR | 16Mbps | 1999 | 甚快红外 |
| UFIR | 96Mbps | 2005 | 超快红外 |

### 2.2 IrDA协议栈

IrDA定义了完整的协议栈:

- 物理层(IrPHY): 定义光学参数、调制方式和数据速率
- 链路接入层(IrLAP): 设备发现、连接建立和数据帧传输
- 链路管理层(IrLMP): 多路复用,允许多个上层应用共享链路
- 传输层(TinyTP): 流量控制
- 应用层: IrOBEX(对象交换)、IrCOMM(串口仿真)等

IrDA通信的典型特征包括: 点对点通信(非广播)、半双工(收发交替)、通信距离通常在0到1米之间、要求设备对准(锥角约30度)。

### 2.3 IrDA的兴衰

IrDA在上世纪90年代末到21世纪初曾经广泛应用于手机、笔记本电脑和PDA上。许多人还记得两部手机"对着头"传文件的场景。然而随着蓝牙技术的成熟和WiFi的普及,IrDA在消费电子领域迅速衰落。蓝牙不需要对准方向、可以穿越障碍物、支持多设备同时连接,这些优势使得IrDA在数据传输场景中完全被取代。

到2010年前后,几乎所有主流手机都移除了IrDA接口。如今IrDA在消费领域的遗产主要体现在少数手机(如某些小米型号)保留的红外发射器上,用途仅限于模拟遥控器控制家电。

## 3. 红外遥控的编解码实现

### 3.1 硬件组成

一个基本的红外收发系统包含以下硬件:

```
发送端:
- 红外LED(940nm, 典型正向电流20-100mA)
- NPN晶体管(驱动LED, 因为MCU的GPIO电流不足)
- 限流电阻
- 微控制器GPIO(产生调制信号)

接收端:
- 一体化红外接收头(如TSOP38238, 内含滤波和解调)
- 微控制器GPIO(捕获解调后的数字信号)
```

### 3.2 Arduino发送NEC红外码示例

以下是使用Arduino和IRremote库发送NEC格式红外码的示例:

```cpp
#include <IRremote.hpp>

#define IR_SEND_PIN 3  // 红外LED连接到D3引脚

void setup() {
    Serial.begin(115200);
    IrSender.begin(IR_SEND_PIN);  // 初始化红外发送
    Serial.println("IR Sender Ready");
}

void loop() {
    // 发送NEC格式: 地址0x04, 命令0x08
    // 这是某品牌电视的开关机码
    IrSender.sendNEC(0x04, 0x08, 0);
    Serial.println("Sent NEC: addr=0x04, cmd=0x08");
    delay(5000);  // 每5秒发送一次
}
```

### 3.3 ESP32接收和学习红外码

在IoT场景中,更常见的需求是"学习"——捕获原始遥控器发出的红外码,然后存储和重放:

```cpp
#include <IRremoteESP8266.h>
#include <IRrecv.h>
#include <IRsend.h>
#include <IRutils.h>

const uint16_t kRecvPin = 14;  // 红外接收引脚
const uint16_t kSendPin = 4;   // 红外发送引脚

IRrecv irrecv(kRecvPin);
IRsend irsend(kSendPin);
decode_results results;

void setup() {
    Serial.begin(115200);
    irrecv.enableIRIn();   // 开启红外接收
    irsend.begin();        // 初始化发送
}

void loop() {
    if (irrecv.decode(&results)) {
        // 打印接收到的红外码信息
        Serial.print("Protocol: ");
        Serial.println(typeToString(results.decode_type));
        Serial.print("Value: 0x");
        Serial.println(resultToHexidecimal(&results));
        Serial.print("Bits: ");
        Serial.println(results.bits);
        irrecv.resume();  // 继续接收下一帧
    }
}
```

## 4. 红外通信在IoT中的角色

### 4.1 智能家居中的红外桥接

红外通信在现代IoT中最重要的角色是"桥接器"——连接传统家电与智能家居系统。市面上大量的空调、电视、风扇、机顶盒仍然只支持红外遥控,没有WiFi或蓝牙接口。红外桥接设备解决了这个问题。

红外桥接的工作原理如下: WiFi/蓝牙网关接收来自手机App或语音助手的指令,将指令转换为对应的红外编码,通过高功率红外LED阵列向各个方向发射红外信号,传统家电接收红外信号并执行操作。

市场上主流的红外桥接产品包括:

- Broadlink RM4系列: 支持WiFi连接,内置红外码库,兼容天猫精灵和Google Home
- 小米万能遥控器: 接入米家生态,支持小爱同学语音控制
- 涂鸦智能红外网关: 面向OEM厂商的方案,支持涂鸦IoT平台

### 4.2 红外码库与学习

红外桥接设备的核心竞争力之一是红外码库的完整性。码库中存储了各品牌各型号设备的红外编码,用户选择品牌和型号即可直接控制,无需手动学习。

常见的红外码库格式:

- LIRC格式: Linux Infrared Remote Control项目维护的开源码库,包含数千种设备
- Pronto Hex格式: 飞利浦Pronto万能遥控器定义的格式,用十六进制描述原始时序
- 厂商私有格式: 各品牌桥接设备使用自己的码库格式

当码库中没有目标设备时,学习功能就派上用场:用户对着桥接设备按原始遥控器的按键,设备捕获红外时序并存储。这种方式几乎可以兼容任何使用标准红外调制的设备。

### 4.3 实际应用案例:智能空调控制

下面是一个典型的IoT红外控制方案——使用ESP32实现WiFi到红外的桥接:

```cpp
#include <WiFi.h>
#include <PubSubClient.h>    // MQTT客户端
#include <IRremoteESP8266.h>
#include <IRsend.h>
#include <ir_Gree.h>         // 格力空调协议库

const char* ssid = "HomeWiFi";
const char* mqtt_server = "192.168.1.100";

IRGreeAC ac(4);  // GPIO4连接红外LED
WiFiClient espClient;
PubSubClient client(espClient);

// MQTT消息回调
void callback(char* topic, byte* payload, unsigned int length) {
    String msg = "";
    for (unsigned int i = 0; i < length; i++) {
        msg += (char)payload[i];
    }
    if (String(topic) == "home/ac/power") {
        if (msg == "ON") {
            ac.on();
            ac.setTemp(26);
            ac.setMode(kGreeCool);
            ac.setFan(kGreeFanAuto);
            ac.send();
        } else {
            ac.off();
            ac.send();
        }
    }
}

void setup() {
    ac.begin();
    WiFi.begin(ssid, "password");
    while (WiFi.status() != WL_CONNECTED) delay(500);
    client.setServer(mqtt_server, 1883);
    client.setCallback(callback);
}

void loop() {
    if (!client.connected()) {
        client.connect("ESP32_AC");
        client.subscribe("home/ac/#");
    }
    client.loop();
}
```

## 5. 红外通信的优势

### 5.1 无射频干扰

红外通信使用光波而非无线电波,不会与WiFi、蓝牙、Zigbee等射频设备产生干扰。在电磁环境敏感的场所(如医院的特定区域、某些实验室),红外通信是一种安全的选择。

### 5.2 无需频率许可

射频通信需要使用特定的频段,虽然ISM频段免许可,但仍然受到功率和使用规则的限制。红外光通信不受无线电频率管理法规的约束,使用完全自由。

### 5.3 低成本和简单性

红外通信的硬件极其简单:一个红外LED加一个光电二极管,成本不到1元人民币。这使得红外遥控器成为消费电子产品中最廉价的无线控制方案。

### 5.4 天然的物理安全性

红外光无法穿透墙壁和不透明物体,通信自然被限制在单个房间内。这意味着红外通信具有天然的物理安全性:邻居无法截获你的红外遥控信号。

### 5.5 低功耗

对于发送简单控制指令的场景(如遥控器按键),红外通信的功耗非常低。一节普通电池可以支撑遥控器使用一到两年,因为发送一条指令只需要LED闪烁几十毫秒,其余时间完全不耗电。

## 6. 红外通信的局限性

### 6.1 视线遮挡问题

红外通信最根本的限制是需要视线(Line-of-Sight)通路。任何不透明的物体——手、书本、墙壁甚至一张纸——都能完全阻断红外信号。

### 6.2 距离限制

实际应用中红外遥控的有效距离通常在1到10米之间。虽然通过增大LED功率和使用透镜聚焦可以延长距离,但远距离通信的可靠性迅速下降。

### 6.3 单向通信

消费级红外遥控几乎都是单向通信:遥控器只负责发送,设备只负责接收。遥控器无法知道指令是否被成功接收和执行。

### 6.4 环境光干扰

强烈的阳光包含大量红外成分,可能干扰红外通信。在阳光直射的环境中,红外接收器的信噪比显著降低。

### 6.5 数据速率限制

对于现代IoT应用来说,红外通信的数据速率严重不足。大多数红外遥控场景使用的速率只有几kbps。

## 7. 红外通信与射频技术的对比

| 特性 | 红外(IR) | BLE | WiFi | Zigbee |
|------|----------|-----|------|--------|
| 通信方向 | 单向为主 | 双向 | 双向 | 双向 |
| 是否需要视线 | 是 | 否 | 否 | 否 |
| 穿墙能力 | 无 | 弱 | 中 | 弱 |
| 典型距离 | 1-10m | 10-50m | 30-100m | 10-100m |
| 数据速率 | kbps级 | 1-2Mbps | 数百Mbps | 250kbps |
| 功耗 | 极低 | 低 | 中高 | 低 |
| 硬件成本 | 极低 | 低 | 中 | 低 |
| 安全性 | 物理隔离 | 加密 | 加密 | 加密 |

从表中可以清晰看出,射频技术在几乎所有方面都优于红外通信。红外通信在新建IoT系统中不具备竞争力,但在连接传统家电方面仍然是不可替代的桥接方案。

## 8. 红外通信的未来展望

### 8.1 持续存在的领域

尽管红外通信在新设备中正被射频技术全面替代,但它在以下领域仍将持续存在。传统家电控制是红外通信最稳固的阵地,全球有数十亿台只支持红外遥控的空调、电视和风扇仍在使用中,这些设备的使用寿命通常在10到15年以上。

视线安全性方面,红外通信无法穿墙的特性在某些场景中是优势而非劣势。例如酒店房间内的设备控制可以确保信号不会干扰到隔壁房间。

### 8.2 新兴方向

在学术研究领域,自由空间光通信(Free-Space Optical Communication, FSO)正在探索使用红外激光实现高速、长距离的点对点通信。这种技术可以达到Gbps级别的数据速率,用于建筑之间的网络互联等场景。

### 8.3 对IoT从业者的建议

如果你正在设计新的IoT产品:优先选择BLE或WiFi作为通信方式,只有在需要兼容传统红外设备时才考虑集成红外功能。如果你正在做智能家居改造:红外桥接器(如WiFi转红外网关)是性价比最高的方案,可以让旧家电融入智能生态而不需要更换设备。

## 总结

红外通信是一种成熟而简单的光学无线通信技术,使用850-950nm波长的红外光进行数据传输。它在消费电子遥控领域有着数十年的应用历史,NEC、RC5、Sony SIRC等协议至今仍被广泛使用。

IrDA标准曾经为设备间的红外数据传输提供了从115.2kbps到96Mbps的速率支持,但已被蓝牙和WiFi彻底取代。红外通信在IoT时代的核心价值在于作为"桥梁技术",通过WiFi转红外网关将传统家电接入智能家居系统。

红外通信的优势——低成本、无射频干扰、物理安全性——在特定场景下仍然有价值。但它的根本局限——视线遮挡、短距离、单向通信——决定了它不可能成为IoT通信的主角。随着新一代智能家电原生集成WiFi或蓝牙,红外通信的使用场景将持续收窄,但在未来十年内仍将作为桥接方案存在。

## 参考文献

1. IrDA Official Specifications, Infrared Data Association. https://www.irda.org/
2. Altium Designer, "Understanding Infrared Communication: Protocols, Standards, and Applications in IoT." Altium Technical Resources, 2022.
3. Ken Shirriff, "Understanding IR Remote Control Protocols: NEC, RC5, and Others." Shirriff's Blog, 2013.
4. Espressif Systems, "IRremoteESP8266 Library Documentation." GitHub Repository, 2023.
5. SB-Projects, "IR Remote Control Theory and Protocols." https://www.sbprojects.net/knowledge/ir/
