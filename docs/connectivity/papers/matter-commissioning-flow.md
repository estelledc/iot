# Matter设备入网调试流程详解
> **难度**：🟡 中级 | **领域**：Matter配网 | **阅读时间**：约 20 分钟

## 引言

想象你要入住一家高端酒店。你不能直接闯进房间,而需要经过一套标准流程:出示预订码(身份初验)、前台核实身份(安全认证)、获取房卡(凭证发放)、连接WiFi(网络接入)。Matter设备加入智能家居网络的过程——commissioning(入网调试)——与此高度类似。每一步都有明确的安全目的,确保只有合法设备能加入网络,只有授权控制器能管理设备。

## 1. Commissioning概述

### 1.1 什么是Commissioning

Commissioning是将全新Matter设备添加到网络和fabric的标准化过程,包含三个核心任务: 网络配置(Network Provisioning)告诉设备如何连接网络; 安全建立(Security Establishment)建立加密通信通道; Fabric加入(Fabric Joining)使设备获得fabric身份证书。

### 1.2 参与角色

| 角色 | 说明 | 示例 |
|------|------|------|
| Commissionee | 等待被添加的新设备 | 新买的智能灯 |
| Commissioner | 执行添加操作的控制器 | 手机App |
| Fabric CA | 签发证书的证书颁发机构 | 云端服务 |

### 1.3 整体流程

```
[设备进入Commissioning模式]
        |
        v
[设备发现 - BLE/mDNS广播]
        |
        v
[PASE会话 - 用配对码建立临时安全通道]
        |
        v
[设备认证 - 验证设备真伪]
        |
        v
[网络配置 - 发送WiFi或Thread凭据]
        |
        v
[CASE会话 - 用证书建立永久安全通道]
        |
        v
[Commissioning完成 - 设备加入Fabric]
```

## 2. 前置条件与Setup Payload

### 2.1 设备进入Commissioning模式

设备必须主动进入commissioning模式才能被发现: 首次上电时未配置的新设备自动进入; 工厂重置后清除配置重新进入; 已配网设备可通过按住特定按钮手动触发(用于添加新fabric)。

### 2.2 Setup Payload(QR码)

每个Matter设备出厂附带Setup Payload,通常以QR码形式印在设备或包装上:

```
QR Code 编码字段:
+-------------------+--------+--------------------------------+
| 字段              | 位数   | 说明                           |
+-------------------+--------+--------------------------------+
| Version           | 3      | Payload版本号                  |
| Vendor ID         | 16     | 厂商标识                       |
| Product ID        | 16     | 产品标识                       |
| Commissioning Flow| 2      | 配网流程类型                   |
| Rendezvous Info   | 8      | 发现方式(BLE/WiFi/自定义)      |
| Discriminator     | 12     | 设备区分码                     |
| Passcode          | 27     | 配对密码                       |
+-------------------+--------+--------------------------------+
```

对于无摄像头场景,提供11位或21位数字Manual Pairing Code。

### 2.3 Discriminator的作用

当多个设备同时处于commissioning模式时,12位discriminator用于精确区分:

```
场景: 同时开箱3个新灯泡
灯泡A: discriminator = 0x4A2
灯泡B: discriminator = 0x8F1
灯泡C: discriminator = 0xC37

App扫描灯泡B的QR码获取0x8F1
在BLE广播中查找匹配的discriminator
精确连接到灯泡B
```

## 3. 设备发现

### 3.1 BLE发现

最常见的发现方式,适用于WiFi和Thread设备(配网前尚无网络连接):

```
设备: 发送BLE广播包(含discriminator + Vendor/Product ID)
      广播间隔: 20-100ms
Commissioner: 扫描BLE广播, 用discriminator过滤, 建立BLE连接
```

### 3.2 IP网络发现(mDNS)

设备已在网络上时(如以太网设备或打开commissioning窗口的已配网设备):

```
设备: 通过mDNS广播 _matterc._udp 服务
      TXT记录含discriminator和Vendor/Product ID
Commissioner: 发送mDNS查询, 匹配discriminator, 通过IP直接连接
```

### 3.3 发现方式选择

| 设备类型 | 首选方式 | 原因 |
|----------|----------|------|
| WiFi设备 | BLE | 配网前没有WiFi连接 |
| Thread设备 | BLE | 需要凭据才能加入Thread |
| 以太网设备 | IP/mDNS | 插网线即有网络 |
| 已配网设备(添加fabric) | IP/mDNS | 已在网络上 |

## 4. PASE会话建立

### 4.1 PASE的目的

PASE(Passcode-Authenticated Session Establishment)使用配对码建立临时加密通道,采用SPAKE2+协议实现密码认证密钥交换,不会泄露passcode本身。

### 4.2 SPAKE2+协议流程

```
Commissioner (Prover)          Device (Verifier)
      |                              |
      |  已知: passcode              | 已知: passcode验证器(w0,L)
      |                              |
      |--- pA (公开值) ------------->|
      |<--- pB (公开值) -------------|
      |                              |
      | 双方各自计算共享密钥K         |
      |                              |
      |--- cA (确认值) ------------->| 验证cA
      | 验证cB <--- cB (确认值) -----|
      |                              |
      |====== 加密通道建立 ==========|
```

### 4.3 安全特性

SPAKE2+提供三重安全保证: 离线字典攻击防护(窃听者无法用captured数据暴力破解); 前向安全(即使passcode泄露,过去通信仍安全); 双向认证(双方确认对方知道passcode)。

### 4.4 PASE的临时性

PASE会话仅用于commissioning过程。建立后传输配置数据,完成commissioning后即销毁,由CASE会话接管所有后续通信。

## 5. 设备认证(Device Attestation)

### 5.1 为什么需要设备认证

在PASE建立后,Commissioner验证设备是否为正品,防止假冒设备加入网络。

### 5.2 证书链结构

```
PAA (Product Attestation Authority) - CSA根证书或授权CA
 |
 v
PAI (Product Attestation Intermediate) - 厂商级中间证书
 |
 v
DAC (Device Attestation Certificate) - 设备级证书,每个设备唯一
```

### 5.3 认证流程

```
Commissioner执行:
1. 请求设备的DAC证书
2. 请求Certification Declaration (CD)
3. 验证 DAC -> PAI -> PAA 证书链
4. 验证CD签名(由CSA签发)
5. 确认Vendor ID和Product ID一致
6. 认证通过, 继续commissioning
   (失败则拒绝设备)
```

Certification Declaration是CSA为通过认证的产品签发的声明,包含Vendor ID、Product ID列表和CSA数字签名。只有通过Matter认证的产品才能获得合法CD。

## 6. 网络配置(Network Provisioning)

### 6.1 WiFi网络配置

通过PASE加密通道发送WiFi凭据:

```
Commissioner -> Device (PASE加密):
  NetworkCommissioning/ScanNetworks
    -> 设备返回可用WiFi列表
  NetworkCommissioning/AddOrUpdateWiFiNetwork
    SSID: "HomeNetwork"
    Credentials: "password123"
  NetworkCommissioning/ConnectNetwork
    -> 设备连接WiFi, 获得IP地址

Device -> Commissioner:
  ConnectNetworkResponse: Success
```

### 6.2 Thread网络配置

Thread设备接收Thread操作数据集:

```
Commissioner -> Device (PASE加密):
  NetworkCommissioning/AddOrUpdateThreadNetwork
    OperationalDataset: (含Network Name, Channel,
      PAN ID, Extended PAN ID, Network Key)
  NetworkCommissioning/ConnectNetwork
    -> 设备加入Thread网络

Device -> Commissioner:
  ConnectNetworkResponse: Success
```

### 6.3 网络切换

设备连接到操作网络后,通信从BLE切换到IP。Commissioner通过IP网络发现设备,准备建立CASE会话。

## 7. CASE会话建立

### 7.1 CASE的目的

CASE(Certificate-Authenticated Session Establishment)是基于证书的永久安全通道。取代临时PASE会话,使用fabric证书进行双向认证,设备重启后可重新建立。

### 7.2 NOC(Network Operational Certificate)

设备加入fabric时获得的身份证书:

| 字段 | 说明 |
|------|------|
| Fabric ID | 所属fabric标识 |
| Node ID | 设备在fabric中的唯一ID |
| Public Key | 设备的操作公钥 |
| Issuer | 签发CA(controller的fabric CA) |
| Validity | 有效期 |

### 7.3 CASE建立流程(Sigma协议)

```
Commissioner                    Device
     |-- Sigma1 (含NOC信息) ----->|
     |                            | 验证Commissioner的NOC
     |<-- Sigma2 (含NOC信息) -----|
     | 验证Device的NOC            |
     |-- Sigma3 (确认) --------->|
     |===== CASE会话建立 =========|
     |   双向证书认证完成          |
```

### 7.4 PASE vs CASE

| 特性 | PASE | CASE |
|------|------|------|
| 凭据 | Passcode(短期) | NOC证书(长期) |
| 用途 | 仅Commissioning | 所有操作通信 |
| 持久性 | 一次性 | 可重建 |
| 安全级别 | 依赖passcode强度 | 公钥密码学 |

## 8. Fabric与多管理员

### 8.1 Fabric概念

Fabric是一个信任域,共享同一CA签发的证书,所有成员互相信任可安全通信。

### 8.2 多Fabric支持

Matter设备可同时属于多个Fabric:

```
灯泡 Node:
+-- Fabric 1: Apple Home (NOC-1, Node ID: 0x01)
+-- Fabric 2: Google Home (NOC-2, Node ID: 0x02)
+-- Fabric 3: Alexa (NOC-3, Node ID: 0x03)
每个Fabric独立管理, 互不干扰
```

### 8.3 多管理员Commissioning

已配网设备添加到新Fabric的流程: 现有管理员打开Commissioning窗口(设时间限制,生成新PASE验证器); 新控制器通过mDNS发现设备; 建立新PASE会话; 新控制器签发新NOC; 设备同时属于两个Fabric。

## 9. 失败处理

### 9.1 常见失败与恢复

| 阶段 | 失败原因 | 处理方式 |
|------|----------|----------|
| 发现 | 设备不在commissioning模式 | 重置或按配对按钮 |
| PASE | Passcode错误 | 重新扫描QR码 |
| 认证 | DAC验证失败 | 拒绝设备(可能假冒) |
| 网络 | WiFi密码错误 | 重新输入凭据 |
| 网络 | Thread不可达 | 检查Border Router |
| CASE | 证书签发失败 | 检查网络连接到CA |

### 9.2 超时机制

设备广播超时15分钟(无人连接则退出commissioning模式); PASE建立超时30秒; 网络连接超时30秒; 整体超时由Commissioner设定。

### 9.3 重试策略

PASE失败重新扫描QR码重试; 网络失败重新输入凭据重试; 整体失败工厂重置后完全重新开始。

## 10. 安全体系总结

### 10.1 各阶段安全措施

```
发现阶段: Discriminator防止连错设备
PASE阶段: SPAKE2+防止密码泄露
认证阶段: DAC证书链防止假冒设备
网络阶段: PASE加密保护网络凭据
CASE阶段: 证书双向认证防止中间人
运行阶段: 所有通信CASE加密
```

### 10.2 端到端安全链

从物理到逻辑的完整保障: 物理层(QR码需物理接触)、认证层(DAC确保设备合法)、传输层(PASE/CASE加密通信)、应用层(ACL控制访问权限)。

## 总结

Matter的Commissioning流程每一步都有明确安全目的: Setup Payload提供初始信任锚点(物理持有证明); PASE用passcode建立临时安全通道(无需预共享密钥基础设施); Device Attestation验证设备真伪(防止假冒); Network Provisioning通过安全通道传递凭据(保护密码); CASE用证书建立永久安全通道(长期运行保障); Multi-Fabric让设备服务于多个生态(用户自由选择)。理解这个流程对于开发Matter设备、调试配网问题都至关重要。

## 参考文献

- [Matter Specification - Commissioning](https://csa-iot.org/developer-resource/specifications-download-request/) - CSA官方规范Commissioning章节
- [Matter Specification - Security](https://csa-iot.org/developer-resource/specifications-download-request/) - PASE/CASE/Attestation安全规范
- [SPAKE2+ RFC (draft-bar-cfrg-spake2plus)](https://datatracker.ietf.org/doc/draft-bar-cfrg-spake2plus/) - SPAKE2+密码认证协议
- [Project CHIP - Commissioning Flow](https://github.com/project-chip/connectedhomeip/blob/master/docs/guides/commissioning.md) - 开源实现配网指南
- [Nordic Semiconductor - Matter Commissioning](https://developer.nordicsemi.com/nRF_Connect_SDK/doc/latest/matter/commissioning.html) - 芯片平台配网实践
