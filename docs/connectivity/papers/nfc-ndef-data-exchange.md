# NFC NDEF数据交换格式与标签类型
> **难度**：🟢 初级 | **领域**：NFC基础 | **阅读时间**：约 18 分钟

## 引言

想象你在超市里拿起一件商品，翻到背面扫一下条形码就能看到价格和产地。NFC 标签就像一个"数字条形码"，但信息量更大也更灵活——你用手机碰一下，就能打开一个网页、连接一台 WiFi、启动一个 App，甚至完成支付。而让手机能正确理解标签里存了什么内容的，就是 NDEF(NFC Data Exchange Format)这套标准数据格式。就像条形码有统一的编码规则(UPC/EAN)，NDEF 定义了 NFC 世界里"怎么组织数据才能被所有设备理解"。

本文介绍 NFC 的基本概念、NDEF 数据格式的结构、常用记录类型，以及 NFC 标签的分类和 IoT 应用场景。

## 1. NFC技术概述

### 1.1 什么是NFC

NFC(Near Field Communication，近场通信)是一种极短距离的无线通信技术。工作频率 13.56 MHz，有效通信距离通常不超过 10 厘米，从 RFID(射频识别)技术演化而来。

```
NFC基本参数:
| 参数       | 值            |
|-----------|--------------|
| 频率       | 13.56 MHz    |
| 有效距离    | <10cm(典型4cm)|
| 数据速率    | 106/212/424 kbps |
| 标准       | ISO 14443, ISO 18092 |
| 供电方式    | 读卡器RF场为标签供电(被动标签无需电池) |
```

NFC 最大的特点是"碰一下就行"——用户不需要搜索配对、输入密码或选择设备，物理接触的动作本身就是交互指令。

### 1.2 NFC三种工作模式

```
模式1: 读写模式(Reader/Writer)
  [手机/读卡器] --读取--> [NFC标签(被动)]
  用途: 读取标签上的URL、文本、配置信息

模式2: 点对点模式(Peer-to-Peer)
  [NFC设备A] <--双向交换--> [NFC设备B]
  用途: 设备间数据交换(已较少使用)

模式3: 卡模拟模式(Card Emulation)
  [NFC读卡器] --读取--> [手机模拟成智能卡]
  用途: Apple Pay, 公交卡, 门禁卡
```

其中读写模式和卡模拟模式最常用。NFC 是 RFID 的一个子集，专指 13.56 MHz 频段、遵循 ISO 14443 或 ISO 18092 标准的近场通信，继承了被动标签无需电池的优势，增加了标准化数据格式(NDEF)。

## 2. NDEF数据格式

### 2.1 为什么需要NDEF

在 NDEF 出现之前，不同厂商的 NFC 标签使用各自的数据格式。NDEF 由 NFC Forum 制定，提供了一种通用数据结构——任何支持 NFC 的手机都能读取任何符合 NDEF 格式的标签。

```
没有NDEF:
  标签A(厂商X格式) --> 手机: "不认识这个格式"

有了NDEF:
  标签A(NDEF格式) --> 手机: "这是一个URL, 打开浏览器"
  标签B(NDEF格式) --> 手机: "这是WiFi配置, 自动连接"
```

### 2.2 NDEF消息与记录结构

NDEF 数据以"消息(Message)"为单位，每条消息包含一个或多个"记录(Record)"：

```
NDEF消息(Message):
+--------------------------------------------------+
| Record 1 (MB=1)  | Record 2 | ... | Record N (ME=1)|
+--------------------------------------------------+
  MB=Message Begin    ME=Message End

每条NDEF记录(Record)结构:
+------+------+----------+--------+---------+
| Flags| Type | Payload  | Type   | Payload |
| (1B) | Len  | Len      |        |         |
+------+------+----------+--------+---------+

Flags字节关键bit:
  MB/ME: 消息首尾标记
  SR: Short Record, 载荷<256字节时=1
  TNF(bit2-0): Type Name Format, 类型命名格式
```

TNF(Type Name Format)字段定义了 Type 字段如何解释：

```
TNF值对照:
| TNF值 | 含义              | Type字段示例     |
|-------|------------------|-----------------|
| 0x01  | NFC Forum定义类型  | "U"(URI), "T"(Text) |
| 0x02  | MIME类型          | "text/plain"    |
| 0x04  | NFC Forum外部类型  | "vendor.com:mytype" |
```

## 3. NDEF记录类型详解

### 3.1 URI记录

URI 记录是最常用的 NDEF 记录类型，用于存储网页链接、电话号码、邮箱地址等。手机碰一下就会自动打开浏览器或拨打电话。

```
URI标识符代码(节省标签存储空间):
| 代码  | 前缀                |
|------|--------------------| 
| 0x00 | (无, 完整URI)       |
| 0x01 | http://www.         |
| 0x02 | https://www.        |
| 0x03 | http://             |
| 0x04 | https://            |
| 0x05 | tel:                |
| 0x06 | mailto:             |

示例: 存储 "https://www.example.com/iot"
  不压缩: 27字节
  用代码0x02: 0x02 + "example.com/iot" = 16字节
  节省40%存储空间
```

对于存储空间只有几十到几百字节的 NFC 标签来说，URI 前缀压缩非常实用。

### 3.2 Text记录

Text 记录存储纯文本，支持多语言：

```
Text记录结构:
+--------+----------+------------------+
| Status | Language | Text String      |
| (1B)   | Code     |                  |
+--------+----------+------------------+

Status字节:
  bit7: 编码(0=UTF-8, 1=UTF-16)
  bit5-0: 语言代码长度
语言代码: ISO 639-1(如"en", "zh", "ja")
```

一条 NDEF 消息可以包含多条不同语言的 Text 记录，手机根据系统语言自动选择显示。

### 3.3 Smart Poster记录

Smart Poster 是一种复合记录，将 URI、标题文本、图标和推荐动作组合在一起：

```
Smart Poster = 一条NDEF记录, 载荷是嵌套的NDEF消息:

外层Record(TNF=0x01, Type="Sp"):
  内层Message:
    Record 1: URI记录 (核心链接)
    Record 2: Text记录 (标题/描述)
    Record 3: Action记录 (推荐动作: 打开/保存/编辑)
```

例如博物馆的 NFC 标签可以用 Smart Poster 包含展品名称(Text)、详情页链接(URI)和推荐动作(打开浏览器)。

### 3.4 MIME类型与External Type记录

MIME 类型记录(TNF=0x02)可以存储任意 MIME 格式的数据，在 IoT 中常见的包括: WiFi 配置(application/vnd.wfa.wsc)、蓝牙配对信息(application/vnd.bluetooth.ep.oob)、电子名片(text/vcard)等。

External Type(TNF=0x04)允许厂商定义自己的数据类型，格式为"域名:类型名"(如 "example.com:deviceconfig")。这为 IoT 设备提供了灵活的自定义数据交换机制。

## 4. NFC标签类型

### 4.1 NFC Forum定义的五种标签类型

```
| 类型    | 基础标准    | 存储容量      | 速率       | 特点            |
|--------|-----------|-------------|-----------|----------------|
| Type 1 | ISO 14443A| 96B-2KB     | 106 kbps  | 读写, 已少用     |
| Type 2 | ISO 14443A| 48B-888B    | 106 kbps  | 最常用(NTAG21x) |
| Type 3 | JIS 6319-4| 1KB-4KB     | 212 kbps  | FeliCa, 日本常用 |
| Type 4 | ISO 14443 | 4KB-32KB    | 106-424kb | 最强(DESFire)   |
| Type 5 | ISO 15693 | 256B-64KB   | 26 kbps   | 较远距离(~1m)   |
```

### 4.2 Type 2标签(最常用)

Type 2 标签基于 NXP 的 NTAG 系列，是 IoT 应用中最常用的 NFC 标签：

```
NTAG21x系列对比:
| 型号      | 用户存储  | 特殊功能          | 典型单价   |
|----------|---------|------------------|----------|
| NTAG213  | 144字节  | 密码保护, 计数器    | 0.1-0.3元 |
| NTAG215  | 504字节  | 同上              | 0.2-0.5元 |
| NTAG216  | 888字节  | 同上              | 0.3-0.8元 |
| NTAG I2C | 888字节  | I2C接口连MCU      | 2-5元     |
```

NTAG213(144 字节)足以存储一条 URL(约 100 字符)、一条 WiFi 配置或一条蓝牙配对信息。Type 4 标签(DESFire)支持 AES-128 加密和多应用文件结构，适合门禁卡、交通卡等安全应用。Type 5 标签(ISO 15693)工作距离可达 1 米，常用于物流仓储。

## 5. NFC标签内存结构

### 5.1 标签内存布局与CC

以 NTAG213 为例：

```
NTAG213内存布局(180字节总, 144字节用户可用):
+------------------+
| 页0-1: UID(序列号)|  7字节唯一标识
+------------------+
| 页3: CC(能力容器)  |  描述标签类型和NDEF支持
+------------------+
| 页4-39: 用户数据   |  144字节, 存放NDEF消息
+------------------+
| 页41-42: 配置     |  密码/访问控制
+------------------+

CC字段(4字节): E1 10 12 00
  E1: 支持NDEF  10: 版本1.0
  12: 18x8=144字节可用  00: 读写均允许
```

### 5.2 NDEF在标签中的TLV存储

NDEF 消息在标签中使用 TLV(Type-Length-Value)格式包装：

```
标签内存示例(存储URL "https://www.example.com"):
  03 12 D1 01 0E 55 02 65 78 61 6D 70 6C 65 2E 63 6F 6D FE
  |  |  |                                               |
  |  |  +-- NDEF消息(URI记录)                            +-- 终止TLV(FE)
  |  +-- 长度=18字节
  +-- NDEF消息TLV类型(03)
```

## 6. IoT中的NDEF应用

### 6.1 设备配网(Provisioning)

NFC 标签在 IoT 设备配网中非常实用：

```
方案1: WiFi凭证传递
  NFC标签NDEF: MIME "application/vnd.wfa.wsc"
  载荷: SSID + 密码 + 加密方式
  手机碰标签 -> 自动连接WiFi

方案2: BLE配对信息
  NFC标签NDEF: MIME "application/vnd.bluetooth.le.oob"
  载荷: BLE MAC地址 + 配对密钥
  手机碰标签 -> 自动建立BLE连接
```

### 6.2 Matter设备入网

Matter 协议支持 NFC 作为设备入网(commissioning)的一种方式。设备上的 NFC 标签包含 Setup Payload(Discriminator + Setup Passcode + Vendor/Product ID)，等同于扫描 QR 码但更快捷。

### 6.3 产品信息与售后

消费电子碰一下打开电子说明书，食品包装碰一下查看产地溯源，服装碰一下验证正品，工业设备碰一下获取维护手册。

## 7. 编程操作NDEF标签

### 7.1 Android端写入

```java
// Android写入NDEF URI记录
NdefRecord uriRecord = NdefRecord.createUri(
    "https://www.example.com/iot-device");
NdefMessage message = new NdefMessage(
    new NdefRecord[]{uriRecord});

Tag tag = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG);
Ndef ndef = Ndef.get(tag);
ndef.connect();
ndef.writeNdefMessage(message);
ndef.close();
```

### 7.2 iOS端读取

```swift
// iOS读取NDEF(Core NFC)
import CoreNFC

class NFCReader: NSObject, NFCNDEFReaderSessionDelegate {
    func beginScanning() {
        let session = NFCNDEFReaderSession(
            delegate: self, queue: nil,
            invalidateAfterFirstRead: true)
        session.begin()
    }
    
    func readerSession(_ session: NFCNDEFReaderSession,
                       didDetectNDEFs messages: [NFCNDEFMessage]) {
        for message in messages {
            for record in message.records {
                if let url = record.wellKnownTypeURIPayload() {
                    print("URL: \(url)")
                }
            }
        }
    }
}
```

### 7.3 MCU端动态内容(NTAG I2C)

NTAG I2C 带有 I2C 接口可以连接微控制器，MCU 通过 I2C 更新标签内存中的 NDEF 内容，手机每次碰标签都读到最新数据(如实时传感器读数)。标签 NFC 通信不需要电池(RF 场供电)，MCU 可以检测到手机碰触事件(场检测中断)。

```
NTAG I2C工作模式:
+------------+       +----------+       +--------+
|  手机NFC   | <---> | NTAG I2C | <---> |  MCU   |
| (RF接口)   |       | (标签)   |       | (I2C)  |
+------------+       +----------+       +--------+
```

## 8. 实际应用示例

### 8.1 IoT设备一碰配网

```
完整流程:
1. 用户购买智能灯泡, 灯泡底部有NFC标签
2. 标签中NDEF内容:
   Record 1: URI "https://app.example.com/setup?id=SN12345"
   Record 2: External Type "example.com:blepairing"
             载荷: BLE MAC=AA:BB:CC:DD:EE:FF, PIN=123456
3. 用户手机碰灯泡底部
4. 手机读取NDEF:
   - 已安装App: 直接启动, 用BLE配对信息连接灯泡
   - 未安装App: 打开URL, 引导下载
5. App通过BLE连接灯泡, 发送WiFi凭证完成配网
```

这种方案比扫描 QR 码更方便(不需要对准摄像头)，比手动输入密码更安全(不需要在标签上印刷密码)。

## 总结

NDEF 是 NFC 世界的"通用语言"，定义了标签和设备之间标准化的数据交换格式。通过 URI、Text、Smart Poster、MIME 和 External Type 五种核心记录类型，NDEF 覆盖了从网页链接到设备配网的广泛应用场景。NFC 标签按 NFC Forum 分为五种类型，其中 Type 2(NTAG 系列)因低成本和够用的存储容量成为 IoT 应用的首选。在 IoT 领域，NFC NDEF 最大的价值在于"一碰配网"——用 NFC 传递 WiFi 凭证或 BLE 配对信息，将复杂的设备入网流程简化为一次物理接触。

## 参考文献

1. NFC Forum, "NFC Data Exchange Format (NDEF) Technical Specification," NFCForum-TS-NDEF_1.0, 2006.
2. NFC Forum, "NFC Record Type Definition (RTD) Technical Specification," NFCForum-TS-RTD_1.0, 2006.
3. NXP Semiconductors, "NTAG213/215/216 NFC Forum Type 2 Tag IC Datasheet," Rev. 3.4, 2023.
4. Apple Inc., "Core NFC Framework Documentation," developer.apple.com, 2024.
5. Android Developers, "NFC Guide: Read and Write NDEF Messages," developer.android.com, 2024.
