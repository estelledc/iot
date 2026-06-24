# Thread网络调试入网流程与安全凭证
> **难度**：🟡 中级 | **领域**：Thread安全 | **阅读时间**：约 20 分钟

## 引言

想象你刚搬进一栋高档公寓, 要连接公寓的门禁系统。你不能直接走进去 -- 首先, 物业管理员(Commissioner)需要验证你的身份; 你拿出入住合同上的验证码(PSKd), 管理员核实后给你一把门禁卡(Network Master Key); 从此你就可以自由进出公寓大门, 刷卡开门。而且这个过程是加密的 -- 即使有人在旁边偷听你和管理员的对话, 也无法伪造一把门禁卡。

Thread网络的调试入网(Commissioning)流程正是这个原理。每个想加入Thread网络的新设备(Joiner)都必须经过一个安全的认证过程, 由Commissioner验证其身份并分发网络密钥。这个过程确保了只有授权设备才能加入网络, 并且密钥分发过程本身也是加密的, 防止中间人攻击。

## 1. Commissioning概述

### 1.1 基本概念

Thread的Commissioning是一个安全的设备入网流程, 涉及三个核心角色:

```
Commissioning三角色:

  Commissioner (认证授权者)
    - 验证Joiner身份, 分发网络密钥
    - 可以是手机App或Border Router

  Joiner (请求入网的设备)
    - 持有PSKd(设备预共享密钥)
    - 接收网络密钥后加入网络

  Joiner Router (消息中继者)
    - 已在Thread网络中的设备
    - 在Commissioner和Joiner之间中继消息
```

### 1.2 为什么需要Commissioning

直接把网络密钥写入设备出厂固件看似简单, 但存在严重安全隐患: 如果所有设备出厂预置相同密钥, 一台设备被破解则整个网络暴露; 如果任何知道密钥的设备都能加入, 恶意设备可以窃听或注入消息; 邻居的设备可能使用相同密钥加入你的网络。

Commissioning通过要求物理验证(PSKd印在设备标签上, 需要物理接触)和设备特定的密钥, 从根本上解决了这些问题。

## 2. Commissioning凭证

### 2.1 PSKd(设备预共享密钥)

PSKd是Commissioning过程中最重要的凭证:

```
PSKd特征:

  全称:    Pre-Shared Key for Device
  长度:    6-32个字符
  字符集:  大写字母 + 数字(排除易混淆字符I/O/Q/Z)
  存储:    印在设备标签或包装盒上, 也可编码在QR码中
  用途:    DTLS握手中的J-PAKE认证

  示例:
    标签上印着: PSKd: J01NME
    QR码包含:   v=1&eui=A8C412FFFE345678&cc=J01NME

  安全性:
    6字符PSKd约4.78亿种组合(22^6)
    推荐使用更长的PSKd增加安全性
    物理访问要求本身提供了额外安全层
```

### 2.2 PSKc(Commissioner凭证)

PSKc(Pre-Shared Key for Commissioner)用于验证Commissioner有权管理此Thread网络。它基于Passphrase、Network Name和Extended PAN ID通过PBKDF2算法生成, 长度128 bit。Commissioner向Leader请求成为活跃Commissioner时需要提供PSKc进行认证。

## 3. Commissioning完整流程

### 3.1 流程概述

```
Commissioning完整流程:

  Commissioner                 Joiner Router               Joiner
      |                             |                        |
  [1] Petition(PSKc) --> Leader    |                        |
      Accept <--                   |                        |
      |                             |                        |
  [2] Commissioner Set             |                        |
      (指定允许入网的EUI-64)        |                        |
      |                             |                        |
  [3]                               |<--Discovery Request---|
      |                             |                        |
  [4] <--Relay(Discovery Req)------|                        |
      |                             |                        |
  [5] <=========== DTLS(J-PAKE, 使用PSKd) =============>   |
      |    (通过Joiner Router中继)  |                        |
      |                             |                        |
  [6] ---Network Master Key + ==========================>  |
      |   Network Name + Channel   |                        |
      |                             |                        |
  [7]                               |<----MLE Attach--------|
      |                             |-----Accept------------>|
```

### 3.2 关键步骤详解

**步骤1 -- Commissioner请求激活**: Commissioner向Leader发送Petition请求, 使用PSKc进行认证。Leader验证PSKc正确且当前没有活跃Commissioner后接受请求。Thread网络同一时间只允许一个活跃Commissioner, 防止多个Commissioner同时操作导致冲突。

**步骤5 -- DTLS握手(核心安全步骤)**: 这是整个Commissioning中最关键的安全环节。使用J-PAKE(Password-Authenticated Key Exchange by Juggling)协议:

```
J-PAKE握手过程:

  Round 1: 双方交换随机数的承诺, 附带零知识证明
    Commissioner -> Joiner: g^x1, g^x2, ZKP(x1), ZKP(x2)
    Joiner -> Commissioner: g^x3, g^x4, ZKP(x3), ZKP(x4)

  Round 2: 双方用PSKd计算共享值
    Commissioner -> Joiner: A = g^((x1+x3+x4)*x2*s), ZKP(x2*s)
    Joiner -> Commissioner: B = g^((x1+x2+x3)*x4*s), ZKP(x4*s)
    (s = PSKd)

  密钥确认:
    PSKd相同 --> 会话密钥K相同 --> 握手成功
    PSKd不同 --> 会话密钥K不同 --> 握手失败

  安全特性:
    前向安全: PSKd事后泄露, 历史会话密钥仍安全
    抗离线字典攻击: 攻击者无法离线枚举PSKd
    双向认证: 双方互相证明知道PSKd
```

## 4. 分发的网络凭证

### 4.1 凭证清单

Commissioning成功后, Joiner获得一组完整的网络凭证, 统称"Active Operational Dataset":

| 凭证 | 说明 |
|------|------|
| Network Master Key | 128bit, 加密所有Thread通信 |
| Network Name | 人类可读的网络名称 |
| Extended PAN ID | 64bit, 网络唯一标识 |
| PAN ID | 16bit, MAC层网络标识 |
| Channel | 802.15.4信道(11-26) |
| Mesh-Local Prefix | /64前缀, 用于mesh内部地址 |
| PSKc | Commissioner凭证(派生值) |
| Security Policy | 安全策略标志位 |
| Active Timestamp | 数据集版本时间戳 |

这些凭证存储在设备的非易失性存储器中, 设备重启后自动使用这些凭证重新加入网络。

### 4.2 Network Master Key与密钥派生

Network Master Key是Thread安全体系的核心, 所有其他安全密钥都从它派生:

```
密钥派生层级:

  Network Master Key (128bit, 网络创建时随机生成)
    |
    +--> MAC Key (用于MAC层帧加密/认证)
    +--> MLE Key (用于MLE消息加密/认证)
    +--> KEK    (Key Encryption Key, 用于密钥更新)

  密钥轮换:
    Key Sequence Counter递增触发新密钥生成
    旧密钥保留一段时间(Guard Time, 默认624小时)
    确保所有设备平滑过渡到新密钥
```

## 5. Commissioner类型

### 5.1 Native Commissioner

Native Commissioner运行在Thread mesh内部的设备上, 直接通过mesh通信, 无需Border Router中继。适合已有Thread设备充当Commissioner的场景, 但需要一个始终在线的Thread设备。

### 5.2 External Commissioner

External Commissioner运行在Thread mesh外部的设备上(如手机), 通过Border Router连接到Thread网络。这是最常见的使用方式, 用户通过手机App完成设备入网, 体验最为友好。

```
External Commissioner架构:

  [手机 App]                    Thread Mesh
  (External Commissioner)    +-------------------+
       |                     |  [Border Router]  |
    WiFi/以太网               |       |           |
       |                     |  [Joiner Router]  |
       +------ DTLS -------->|       |           |
       (通过Border Router)   |    [Joiner]       |
                             +-------------------+
```

## 6. Thread 1.2安全增强

Thread 1.2引入了多项Commissioning改进: 域代理(Domain Proxy)支持企业级场景的大规模设备管理和统一策略管控; 商业调试(Commercial Commissioning)支持批量设备入网和工厂预配置; CCM(Cloud-based Commissioner)支持基于云的远程设备管理。

### 6.1 与Matter的Commissioning集成

Matter over Thread的Commissioning将Thread层入网和Matter层入网统一到一个流程中:

```
统一Commissioning流程:

  1. 用户扫描设备QR码(包含Thread PSKd + Matter Setup Code)
  2. 手机App作为External Commissioner
  3. 完成Thread Commissioning(分发网络密钥)
  4. 设备加入Thread mesh
  5. 启动Matter PASE(使用QR码中的Setup Code)
  6. 完成Matter Fabric加入
  7. 设备可被Matter控制器管理

  QR码内容:
    Thread PSKd: 用于Thread入网认证
    Matter Setup Code: 用于Matter PASE认证
    Vendor ID / Product ID: 设备识别
    Discriminator: 设备区分码
```

## 7. 带外Commissioning

### 7.1 QR码入网

最常见的用户体验是扫描QR码入网:

```
QR码Commissioning:

  设备标签/包装盒上的QR码编码内容:
    v=1                              // 版本
    &eui=A8C412FFFE345678            // 设备EUI-64
    &cc=J01NME                       // PSKd/连接码
    &vp=65521+32769                  // Vendor/Product ID
    &d=3840                          // Discriminator

  用户操作:
    1. 打开手机App(如Apple Home)
    2. 点击"添加设备"
    3. 扫描QR码
    4. App自动完成所有Commissioning步骤
    5. 设备出现在App中, 可以控制
```

### 7.2 NFC入网

部分设备支持NFC触碰入网: 手机靠近设备的NFC区域, 自动读取设备凭证(等同QR码内容), App自动启动Commissioning。比扫码更快, 适合安装位置不便扫码的设备。

## 8. 安全注意事项

### 8.1 PSKd安全最佳实践

PSKd的安全性取决于几个因素: 长度方面, 最短6字符(约4.78亿组合), 推荐12字符以上; 物理安全方面, PSKd印在设备上需要物理接触, 安装后QR码通常被遮挡; 工厂安全方面, PSKd应在工厂随机生成并写入设备, 不同设备使用不同PSKd。

### 8.2 Commissioning攻击防护

```
已知攻击与防护:

  窃听DTLS握手:
    J-PAKE协议即使被完整抓包也无法推导密钥

  中间人攻击:
    J-PAKE双向认证, 冒充者无法通过验证

  暴力破解PSKd:
    J-PAKE抗离线字典攻击, 增加PSKd长度提高安全性

  重放攻击:
    DTLS使用随机数和序列号防重放

  拒绝服务:
    Commissioner有连接限制和超时机制
```

## 9. 实际应用示例

### 9.1 家庭场景

```
场景: 添加Thread智能灯泡

  准备:
    - 已有Thread网络(Apple TV作为Border Router)
    - 新购买的Thread灯泡(包装盒上有QR码)

  步骤:
    1. 灯泡装入灯座通电 --> 进入Commissioning模式
    2. 打开Apple Home App, 扫描QR码
    3. App解析QR码获得PSKd和EUI-64
    4. iPhone -> WiFi -> Apple TV(BR) -> Thread -> 灯泡
       DTLS握手(J-PAKE + PSKd) -> 网络密钥分发
    5. 灯泡加入Thread网络, 完成Matter Fabric加入
    6. 用户可以通过App、Siri或自动化控制灯泡

  耗时: 通常 10-30 秒
```

### 9.2 故障排查

常见Commissioning失败原因: PSKd错误导致DTLS握手失败, 需确认QR码清晰或手动输入; 信道不匹配导致Joiner收不到响应, 大多数设备默认全信道扫描需等待更长时间; Commissioner已过期被拒绝, 需等待超时或重启Border Router; 距离太远导致消息丢失和握手超时, 需将Joiner移近已有Thread设备。

## 总结

Thread的Commissioning流程体现了"安全不牺牲易用性"的设计哲学。通过PSKd + DTLS/J-PAKE的组合, Thread实现了物联网设备入网的三重保障: 物理安全(需要接触设备获取PSKd)、密码学安全(J-PAKE抗离线攻击和中间人攻击)、以及操作安全(同一时间只有一个活跃Commissioner)。

从用户体验角度看, 整个过程被简化为"扫一扫QR码"。底层的DTLS握手、密钥交换、凭证分发对用户完全透明。随着Matter的普及, Thread Commissioning与Matter的Commissioning进一步融合, 用户一次扫码即可完成网络层和应用层的双重入网, 真正实现了"即买即用"的物联网设备体验。

## 参考文献

1. Thread Group. "Thread 1.3.0 Specification - Commissioning." Thread Group, 2022. https://www.threadgroup.org/
2. Hao, F. and Ryan, P. "J-PAKE: Authenticated Key Exchange without PKI." Transactions on Computational Science XI, Springer, 2010.
3. Rescorla, E. and Modadugu, N. "Datagram Transport Layer Security Version 1.2." RFC 6347, IETF, 2012.
4. Connectivity Standards Alliance. "Matter Specification - Device Commissioning." CSA, 2022.
5. Google. "OpenThread Commissioning Guide." GitHub, 2021. https://openthread.io/guides/commissioning
