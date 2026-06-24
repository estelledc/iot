# NFC读卡器模式与卡模拟在IoT中的应用
> **难度**：🟡 中级 | **领域**：NFC应用模式 | **阅读时间**：约 20 分钟

## 引言

想象你手里有一张万能门禁卡，走到公司大门、小区门口、停车场闸机前都能刷开。现在再想象你的手机变成了这张万能卡——不用带实体卡，手机碰一下闸机就能通过。更进一步，想象门锁本身也变聪明了——它不只是被动等你刷卡，还能主动读取你口袋里标签上的信息。这两个方向分别对应 NFC 的两种核心工作模式：读卡器模式(Reader Mode，设备主动读取标签)和卡模拟模式(Card Emulation，设备被动充当智能卡)。

在 IoT 场景中，智能门锁用读卡器模式识别门禁卡，手机用卡模拟模式充当门禁卡，工业设备用读卡器模式读取资产标签，机器人用卡模拟模式通过门禁系统。本文系统介绍这两种模式的原理、实现方式和 IoT 应用。

## 1. NFC工作模式回顾

### 1.1 模式对比与核心区别

```
| 模式            | 设备角色    | 对端       | RF场提供方 | 典型场景      |
|----------------|-----------|-----------|----------|-------------|
| 读写模式(R/W)   | 主动读卡器  | 被动标签    | 设备      | 读NFC标签     |
| 卡模拟(CE)      | 被动卡片   | 主动读卡器  | 读卡器    | 手机当门禁卡   |
| 点对点(P2P)     | 双方对等   | NFC设备    | 交替      | 设备间交换     |
```

核心区别在于谁产生 13.56 MHz 的 RF 能量场。读写模式下设备自己产生 RF 场为标签供电；卡模拟模式下设备在外部读卡器的 RF 场中被动响应，假装自己是一张卡。

## 2. 读卡器模式(Reader/Writer Mode)

### 2.1 工作原理

在读卡器模式中，NFC 设备产生 13.56 MHz 的射频场，为被动 NFC 标签供电并与之通信：

```
[读卡器]                          [NFC标签]
    |                                |
    |--- 产生RF场(13.56MHz) -------->|  标签获得能量
    |--- 防碰撞+选择(ATQA/SAK) ----->|  发现并锁定标签
    |<-- 标签应答(UID) --------------|  获得唯一ID
    |--- 读取命令(READ) ------------>|
    |<-- 数据(NDEF/扇区) ------------|  获取标签内容
    |--- 写入命令(WRITE) ----------->|  (可选)写入数据
```

### 2.2 IoT设备中的读卡器应用

```
场景1: 智能门锁
  [门锁(NFC读卡器)] <--读取--> [门禁卡/手机]
  读取卡片UID或认证数据, 比对授权列表, 匹配则开锁

场景2: 工业设备读取资产标签
  [手持终端] <--读取--> [设备上的NFC标签]
  读取设备序列号/维护记录, 记录巡检数据

场景3: 自动售货机
  [售货机(NFC读卡器)] <--读取--> [银行卡/手机]
  执行EMV非接触支付协议, 完成扣款
```

### 2.3 读卡器硬件选择

```
常用NFC读卡器芯片:
| 芯片         | 厂商  | 接口    | 特点                |
|-------------|------|--------|--------------------| 
| PN532       | NXP  | SPI/I2C| 经典, 社区资源丰富    |
| PN7150      | NXP  | I2C    | 新一代, 支持全模式    |
| RC522       | NXP  | SPI    | 低成本(~5元), 仅读卡  |
| ST25R3916   | ST   | SPI    | 高性能, 支持NFC-V    |
```

### 2.4 读卡器实现示例

```python
# 使用PN532读取NFC标签UID(MicroPython)
from pn532 import PN532_SPI

nfc = PN532_SPI(cs=5, reset=4)
nfc.SAM_configuration()

print("等待NFC标签...")
while True:
    uid = nfc.read_passive_target(timeout=1000)
    if uid is not None:
        uid_hex = ''.join(['{:02X}'.format(b) for b in uid])
        print(f"检测到标签, UID: {uid_hex}")
        ndef_data = nfc.ntag2xx_read_block(4)
        if ndef_data:
            print(f"NDEF数据: {ndef_data}")
```

## 3. 卡模拟模式(Card Emulation)

### 3.1 工作原理

卡模拟模式让 NFC 设备表现得像一张非接触式智能卡，在外部读卡器的 RF 场中被动响应：

```
[外部读卡器]                    [手机/IoT设备(模拟卡)]
    |                                |
    |--- 产生RF场 ------------------>|  设备检测到场
    |--- ATQA请求 ------------------>|
    |<-- ATQA应答(模拟卡类型) --------|  假装是一张卡
    |--- SELECT UID ---------------->|
    |<-- 模拟的UID ------------------|
    |--- APDU命令 ------------------>|
    |<-- APDU响应 -------------------|
    读卡器认为在和一张真实卡片通信
```

### 3.2 SE-based vs HCE两种实现

```
方式1: 基于安全元件(SE-based)
  卡模拟逻辑和密钥存储在硬件SE中
  特点: 硬件级安全, Apple Pay专用, 需SE授权
  适合: 支付, 高安全门禁

方式2: 主机卡模拟(HCE, Host Card Emulation)
  卡模拟逻辑在App中软件运行
  特点: Android 4.4+原生支持, 无需SE硬件
  适合: 门禁, 会员卡等非支付场景
```

### 3.3 AID路由

当多个应用注册卡模拟时，NFC 控制器通过 AID(Application Identifier)路由：

```
外部读卡器发送SELECT命令:
  SELECT AID = "F0010203040506"

NFC控制器查找AID注册表:
  "A0000000041010" --> Google Pay (SE)
  "F0010203040506" --> 门禁App (HCE)
  "D2760000850101" --> 交通卡 (SE)

匹配后路由到对应处理方
```

### 3.4 HCE实现示例

```java
// Android HCE服务: 模拟门禁卡
public class DoorAccessService extends HostApduService {
    
    @Override
    public byte[] processCommandApdu(byte[] apdu, 
                                      Bundle extras) {
        if (isSelectAid(apdu)) {
            return new byte[]{(byte)0x90, (byte)0x00};
        }
        if (isAuthRequest(apdu)) {
            byte[] credential = getStoredCredential();
            return concat(credential, 
                new byte[]{(byte)0x90, (byte)0x00});
        }
        return new byte[]{(byte)0x6F, (byte)0x00};
    }
}
```

```xml
<!-- AndroidManifest.xml注册HCE服务 -->
<service android:name=".DoorAccessService"
    android:permission="android.permission.BIND_NFC_SERVICE">
    <intent-filter>
        <action android:name=
            "android.nfc.cardemulation.action.HOST_APDU_SERVICE"/>
    </intent-filter>
    <meta-data android:name=
        "android.nfc.cardemulation.host_apdu_service"
        android:resource="@xml/door_access_aid"/>
</service>
```

## 4. IoT中的读卡器应用

### 4.1 智能门锁系统架构

```
  [用户手机(HCE)]              [实体门禁卡]
        |                          |
  +--[NFC读卡器模块(RC522)]--+
  +------|-------------------+
  +------v-----------+
  |   主控MCU(ESP32)  |  凭证验证 + 授权列表 + 日志
  +------|------------+
  +------v-----------+
  |   电锁驱动        |  开门/关门
  +------------------+
```

### 4.2 工业设备维护

设备上贴 NFC 标签，存储序列号、维护日期和手册 URL。维护人员用手持终端碰标签即可读取设备信息并自动打开工单，完成维护后写入新日期。NFC 标签不怕条形码磨损，UID 唯一防伪，且内容可反复更新。

### 4.3 医疗场景

患者 NFC 腕带用于确认身份避免用错药，药瓶 NFC 标签用于验证药品真伪，医疗设备 NFC 用于验证校准状态和记录使用日志。

## 5. IoT中的卡模拟应用

### 5.1 IoT设备模拟卡片

```
场景: 仓库机器人自动通过门禁
  [门禁读卡器(已有)] <--NFC--> [机器人(卡模拟)]
  机器人NFC模块模拟已授权门禁卡, 到达门禁自动刷卡通过
  优势: 不需要改造现有门禁系统
```

### 5.2 可穿戴设备与手机统一入口

智能手表模拟交通卡碰闸机通过、模拟门禁卡碰读卡器开门、模拟支付卡碰 POS 机支付。智能戒指内置被动 NFC 芯片(无需电池)，碰一下开门。

手机通过 NFC 卡模拟成为通用钥匙: 不同 App 注册不同 AID，NFC 控制器按 AID 自动路由到门禁 App(HCE)、交通 App(SE)、支付 App(SE)等。一部手机替代所有实体卡片。

## 6. NFC与BLE的组合模式

### 6.1 NFC触发BLE连接

NFC 和 BLE 经常组合使用——NFC 负责"第一次碰触"建立信任，BLE 负责后续持续通信：

```
第1步: NFC碰触(<0.5秒)
  [手机] --NFC碰--> [IoT设备]
  交换BLE配对信息(MAC地址+密钥)

第2步: BLE自动连接
  [手机] <--BLE--> [IoT设备]
  传输传感器数据, 配置参数等(距离10-30米)

NFC确认"碰的是这个设备"(物理接触=用户意图)
BLE提供持续数据通道(不需要一直贴着)
```

### 6.2 蓝牙OOB配对

NFC 作为蓝牙的 OOB(Out of Band)配对通道，NFC 标签中存储蓝牙 OOB 数据(BLE 设备地址 + 设备名 + 安全信息)，碰一下即完成配对，免去传统蓝牙配对的搜索和 PIN 输入。

## 7. NTAG I2C在IoT设备中的应用

### 7.1 双接口架构

NTAG I2C 是专为 IoT 设计的 NFC 芯片，同时提供 NFC 无线接口和 I2C 有线接口，两个接口访问同一块共享内存(888 字节)：

```
  [手机/读卡器]
       |  NFC RF接口
  +----v----+
  | NTAG I2C|  共享内存
  +----^----+
       |  I2C有线接口
  [MCU(ESP32等)]
```

### 7.2 通信模式与能量采集

MCU 写入模式: MCU 更新传感器数据到 NTAG 内存(I2C)，手机碰标签读取最新数据(NFC)，适合无屏设备状态查询。手机写入模式: 手机写入配置参数(NFC)，MCU 检测到写入事件后读取新配置(I2C)。

能量采集模式特别有意思: NFC 读卡器的 RF 场为 NTAG 供能，NTAG 通过 VOUT 引脚为 MCU 和传感器供电，整个系统无需电池，只在手机碰触瞬间工作。适合冷链物流温度抽检、设备状态点检。

## 8. 安全考量

### 8.1 读卡器模式安全

仅依赖 UID 认证不安全(UID 可被复制)。安全等级从低到高: 仅 UID 匹配(容易克隆)、密码保护(NTAG 密码功能)、挑战-响应加加密(DESFire AES-128)。敏感数据应在标签中加密存储。

### 8.2 卡模拟安全

支付场景必须使用 SE(硬件隔离)，门禁场景可用 HCE 加云端令牌轮换，大额支付要求指纹/面容确认，使用令牌化避免暴露真实卡号。

NFC 的极短通信距离(小于 10cm)本身就是天然安全特性——用户必须有意识地将设备靠近读卡器，这个物理动作等价于一次"同意授权"。相比蓝牙(10-30 米)和 WiFi(50-100 米)，NFC 被远程窃听的风险极低。

## 9. 实际部署案例

### 9.1 智能家居门锁方案

```
硬件: ESP32主控 + RC522 NFC读卡器 + 电磁锁
流程:
  1. RC522持续扫描NFC标签/卡片
  2. 检测到卡片 -> 读取UID
  3. 与本地授权列表比对
  4. 匹配 -> 开门(5秒后自动落锁)
  5. 不匹配 -> LED闪红灯
  6. WiFi上传开锁日志到云端

支持: 实体门禁卡 + 手机HCE + Apple Wallet NFC钥匙
```

### 9.2 成本对比

NFC 读卡模块(RC522 + 天线 + 线缆)BOM 成本约 10 元，远低于指纹模块(30-80 元)和人脸识别(100-300 元)，是最经济的身份识别方案。

## 总结

NFC 的读卡器模式和卡模拟模式为 IoT 提供了两种互补的交互方式。读卡器模式让 IoT 设备识别 NFC 标签和卡片，应用于门禁、资产管理和设备维护。卡模拟模式让手机和 IoT 设备充当智能卡，复用现有读卡器基础设施。HCE 技术降低了卡模拟门槛，任何 Android App 都可以实现卡模拟。NFC 与 BLE 的组合("碰一下配对，BLE 持续通信")成为 IoT 配网的最佳实践。NTAG I2C 双接口芯片为 IoT 设备提供了独特的数据桥接和能量采集能力。

## 参考文献

1. NFC Forum, "NFC Controller Interface (NCI) Technical Specification," NFCForum-TS-NCI-2.0, 2020.
2. NXP Semiconductors, "PN532/C1 NFC Controller Datasheet," Rev. 7.2, 2023.
3. Android Developers, "Host-based Card Emulation Guide," developer.android.com, 2024.
4. NXP Semiconductors, "NTAG I2C Plus Datasheet," Rev. 3.3, 2023.
5. Apple Inc., "Apple Pay Security Overview," support.apple.com, 2024.
