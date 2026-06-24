# 硬件安全模块HSM在IoT设备中的集成
> **难度**：🔴 高级 | **领域**：硬件安全 | **阅读时间**：约 22 分钟

## 引言

想象一下,你家大门的钥匙不是放在门口的鞋柜里,而是锁在一个焊死在墙里的保险箱中。即使有人闯入你的房间,也无法取出钥匙。硬件安全模块(HSM)就是这个"焊死在墙里的保险箱"——密钥永远不会离开它的保护范围,所有加密运算都在模块内部完成,外界只能拿到运算结果,碰不到密钥本身。

在IoT领域,设备往往部署在无人看守的环境中,物理安全无法保证。如果密钥存储在普通Flash或RAM中,攻击者可以通过调试接口、侧信道攻击甚至直接读取存储器来提取密钥。HSM从硬件层面彻底杜绝了这种可能性。

## 1. HSM定义与核心价值

### 1.1 什么是HSM

HSM(Hardware Security Module)是专门用于执行加密运算和保护密钥安全的物理计算设备。它的核心特征包括:

- **专用硬件**:独立处理器、加密协处理器、安全存储器
- **防篡改设计**:物理封装检测入侵,检测到攻击时自动擦除密钥
- **密钥不外泄**:所有涉及密钥的运算在模块内部完成,密钥永远不会以明文形式出现在HSM边界之外

```
HSM内部结构简图:
+-----------------------------------------------+
|  HSM Boundary (Tamper-Resistant Enclosure)    |
|  +-----------+  +------------+  +-----------+ |
|  | Secure CPU|  |Crypto Engine|  |Secure RAM | |
|  +-----------+  +------------+  +-----------+ |
|  +-----------+  +------------+               |
|  | True RNG  |  |Key Storage |               |
|  +-----------+  +------------+               |
+-----------------------------------------------+
         |
    Host Interface (PCIe/USB/I2C/Network)
```

### 1.2 为什么IoT需要HSM

| 威胁场景 | 无HSM | 有HSM |
|----------|-------|-------|
| 调试接口读取Flash | 密钥直接暴露 | 密钥不在Flash中 |
| 固件逆向分析 | 可提取硬编码密钥 | 密钥从未出现在固件中 |
| 侧信道攻击 | 软件实现易受攻击 | 硬件级防护 |
| 设备克隆 | 复制Flash即可克隆 | 密钥无法复制 |

具体而言,HSM为IoT设备提供四个核心价值:

1. **保护私钥不被提取**:密钥在安全硬件中生成,永远不会离开
2. **硬件加速加密**:专用加密引擎,比软件实现快且更安全
3. **安全密钥生成**:内置真随机数发生器,确保密钥质量
4. **合规要求**:许多行业标准(如FIPS、PCI DSS)要求使用HSM

### 1.3 HSM vs 软件加密

| 对比维度 | 软件加密 | HSM |
|----------|---------|-----|
| 密钥存储 | Flash/RAM,可被读取 | 安全存储器,不可提取 |
| 侧信道防护 | 极难防护 | 内置防护机制 |
| 加密性能 | 依赖CPU,受中断影响 | 专用引擎,性能稳定 |
| 安全认证 | 无 | FIPS 140-2/140-3认证 |
| 密钥生命周期 | 全靠软件策略 | 硬件强制执行 |
| 成本 | 仅软件成本 | 硬件成本 |

软件加密最大的风险在于:密钥在某个时刻必然以明文形式存在于RAM中,攻击者可以通过调试接口或DMA攻击读取。HSM从根本上消除了这个攻击面。

## 2. 安全等级与认证

### 2.1 FIPS 140-2/140-3安全等级

FIPS(Federal Information Processing Standard)是美国联邦信息处理标准,HSM最广泛认可的认证。

| 等级 | 物理安全 | 关键要求 | 典型应用 |
|------|---------|---------|---------|
| Level 1 | 无物理防护 | 网络可访问HSM | 开发测试 |
| Level 2 | 防篡改涂层 | 角色认证,审计日志 | 一般商业 |
| Level 3 | 防篡改检测与响应 | 身份认证,密钥不出模块 | 金融支付 |
| Level 4 | 完全封装 | 环境故障防护,零化擦除 | 国防/高价值 |

对于IoT设备中的嵌入式HSM,通常通过FIPS 140-3的物理不可提取性要求来证明密钥安全。

### 2.2 Common Criteria (CC) EAL

CC(Common Criteria)是国际通用评估准则,EAL(Evaluation Assurance Level)从1到7递增:

- **EAL 1-3**:功能测试,低到中等保障
- **EAL 4**:方法论设计和测试,商业级最高
- **EAL 5+**:半形式化设计和测试,IoT安全芯片常见等级
- **EAL 6-7**:形式化验证,最高保障级别

## 3. HSM形态因子

### 3.1 网络HSM (Network HSM)

```
[Application Server] ---Network--- [Network HSM (Rack-mounted)]
```

- **形态**:机架式设备,1U/2U
- **用途**:云服务、PKI基础设施、密钥管理服务
- **接口**:PKCS#11、Microsoft CNG、REST API
- **IoT场景**:IoT云平台后端,设备证书签发与管理

### 3.2 PCIe卡HSM

```
[Host Server] ---PCIe--- [HSM Card]
```

- **形态**:PCIe插卡
- **用途**:服务器集成,性能敏感场景
- **接口**:PKCS#11、CNG
- **IoT场景**:IoT平台认证服务器,大规模设备认证

### 3.3 嵌入式HSM (Embedded HSM)

```
[MCU] ---I2C/SPI--- [Embedded HSM Chip]
```

- **形态**:独立IC芯片或IP核
- **用途**:IoT终端设备,资源受限环境
- **接口**:I2C、SPI
- **IoT场景**:设备端密钥存储与加密运算

嵌入式HSM是IoT设备最相关的形态,也是本文的重点。

## 4. IoT嵌入式HSM产品

### 4.1 主流产品对比

| 产品 | 厂商 | 接口 | 加密算法 | 安全认证 | 典型价格 |
|------|------|------|---------|---------|---------|
| ATECC608A/B | Microchip | I2C | ECC P256, AES-128, SHA-256 | FIPS 140-3 | $0.50-0.80 |
| OPTIGA Trust M | Infineon | I2C | ECC P256/P384, AES-128, SHA-256 | CC EAL 5+ | $0.80-1.20 |
| SE050 | NXP | I2C | ECC/ RSA/ AES, 多算法 | CC EAL 6+ | $1.00-1.50 |
| STSAFE-A110 | ST | I2C | ECC P256, AES-128 | CC EAL 5+ | $0.60-1.00 |

### 4.2 ATECC608A/B详解

ATECC608A/B是IoT领域使用最广泛的嵌入式HSM之一:

- **加密引擎**:ECC P256、AES-128、SHA-256/HMAC
- **安全存储**:16个密钥槽,每个可独立配置权限
- **唯一序列号**:72位出厂唯一ID
- **随机数发生器**:内置TRNG
- **防篡改**:电压/温度监测,异常时锁定

```
ATECC608A 密钥槽配置示例:
Slot 0: ECC Private Key (不可读, 可签名)
Slot 1: ECC Private Key (不可读, 可签名)
Slot 2: AES Key (不可读, 可加密/解密)
Slot 3: Shared Secret (不可读, 可ECDH)
...
Slot 15: General Purpose Data (可读写)
```

### 4.3 NXP SE050详解

SE050提供更强大的功能:

- **安全微控制器**:带有CC EAL 6+认证的安全CPU
- **多算法支持**:ECC(多曲线)、RSA、AES、DES、3DES
- **Java Card兼容**:支持Java Card applet
- **动态密钥管理**:运行时创建/删除密钥对
- **安全域**:支持多个安全域隔离

## 5. HSM密钥操作

### 5.1 核心操作列表

HSM支持的核心密码学操作:

1. **密钥生成**:在HSM内部生成密钥对,私钥不外泄
2. **密钥存储**:存储在安全存储器中,受访问策略保护
3. **ECDSA签名/验证**:用存储的私钥签名,或验证外部签名
4. **ECDH密钥协商**:两方密钥协商,生成共享密钥
5. **AES加密/解密**:对称加密运算
6. **SHA哈希**:消息摘要计算
7. **HMAC**:消息认证码计算

### 5.2 操作流程

所有操作遵循统一模式:请求者发送命令,HSM内部处理,返回结果。

```
操作示例: ECDSA签名
1. 主机发送: Sign命令(槽位号, 待签名数据哈希)
2. HSM内部:  读取对应槽位的私钥
3. HSM内部:  执行ECDSA签名运算
4. HSM返回:  签名值(r, s)
5. 私钥从未出现在I2C总线上
```

## 6. I2C接口与命令协议

### 6.1 I2C通信架构

```
        I2C Bus (SDA/SCL)
[MCU] <-----------------> [HSM (ATECC608A)]
  |                            |
  |--- Command ----------->   |
  |                           | (内部处理)
  |<--- Response -----------  |
```

- **I2C地址**:ATECC608A默认0x5C(7位地址)
- **时钟频率**:最高1MHz(Fast-mode Plus)
- **命令帧格式**:Word Address + 命令包(长度+命令+参数+数据+CRC)
- **响应帧格式**:长度+数据+CRC

### 6.2 命令协议细节

```
命令包格式:
+------+------+------+------+-----+------+
| Len  | CMD  | Param1|Param2| Data | CRC  |
| 1B   | 1B   | 1B    | 2B   | nB   | 2B   |
+------+------+------+------+-----+------+

响应包格式:
+------+------+------+
| Len  | Data | CRC  |
| 1B   | nB   | 2B   |
+------+------+------+
```

关键设计:命令和响应中都不包含密钥数据,只有操作指令和运算结果。

## 7. 设备配给工作流

### 7.1 工厂配给(Factory Provisioning)

```
[Manufacturer CA]            [Factory Line]
      |                           |
      | 1. 签发设备证书              |
      |<--------------------------|
      |                           | 2. 写入HSM:
      |                           |    - 设备私钥(或HSM内部生成)
      | 3. 设备证书                 |    - 设备证书
      |-------------------------->|    - CA证书链
      |                           |    - 配置参数
                                  |
                              [IoT Device]
```

工厂配给步骤:

1. HSM在安全环境中生成密钥对(或由CA生成后注入)
2. 将设备证书写入HSM
3. 将CA证书链写入HSM
4. 锁定HSM配置(防止后续修改)
5. 记录设备ID与证书的映射关系

### 7.2 自助配给(Self-Provisioning with CSR)

```
[IoT Device]                [Cloud CA]
      |                           |
      | 1. HSM内部生成密钥对        |
      | 2. 生成CSR(签名请求)        |
      |-------------------------->|
      |                           | 3. CA签发证书
      | 4. 设备证书                |
      |<--------------------------|
      | 5. 写入HSM                 |
      |                           |
```

自助配给的优势:私钥从未离开HSM,即使在工厂产线上也无法截获。

## 8. IoT应用场景

### 8.1 TLS双向认证

IoT设备与云平台建立TLS连接时,HSM存储设备私钥和证书:

```
[IoT Device]                     [Cloud Server]
  HSM:                           |
    - 设备私钥(不可读)            |
    - 设备证书(可读)              |
    - CA证书(可读)               |
      |                          |
      |--- ClientHello + Cert -->|
      |<-- ServerHello + Cert --- |
      |                          |
      |--- CertificateVerify --> | (HSM内部签名)
      |<-- ChangeCipherSpec ---- |
      |                          |
      |===== Encrypted TLS ===== |
```

### 8.2 安全启动验证

```
启动流程:
1. Boot ROM验证:使用HSM中的公钥哈希验证第一级引导程序签名
2. 第一级引导:使用HSM验证第二级引导程序签名
3. 应用程序:使用HSM验证应用程序签名
4. 任何一级验证失败,设备拒绝启动
```

### 8.3 固件签名验证

OTA更新时,使用HSM验证固件签名:

1. 下载固件包(含签名)
2. 计算固件哈希
3. 发送哈希和签名到HSM进行ECDSA验证
4. 验证通过后写入Flash

### 8.4 数据加密

采集的敏感数据在传输前通过HSM加密:

1. 通过ECDH协商出对称密钥
2. 使用AES-128加密数据
3. 密文上传到云端
4. 云端使用对应密钥解密

## 9. 集成架构

### 9.1 典型MCU + HSM架构

```
+------------------+        +------------------+
|     MCU          |        |   HSM Chip       |
| (e.g. ESP32)     |  I2C   | (e.g. ATECC608A) |
|                  |<------>|                  |
| - Application    |        | - ECC Key Pairs  |
| - TLS Stack      |        | - Device Cert    |
| - Network Stack  |        | - AES Keys       |
| - HSM Driver     |        | - TRNG           |
+------------------+        +------------------+
        |                          |
     Wi-Fi/Ethernet          (Keys Never Leave)
        |
  [Cloud Platform]
```

### 9.2 软件层次

```
Application Layer
    |
TLS Library (mbedTLS / wolfSSL)
    |            |
PKCS#11 API   Vendor API
    |            |
HSM Driver / Middleware
    |
I2C HAL
    |
Hardware (I2C Peripheral)
```

## 10. 实战案例: ATECC608A + ESP32连接AWS IoT Core

### 10.1 硬件连接

```
ESP32 Pin         ATECC608A Pin
GPIO 21 (SDA) <--> SDA
GPIO 22 (SCL) <--> SCL
3.3V          <--> VCC
GND           <--> GND
```

### 10.2 软件配置

```c
// ESP-IDF项目中使用ATECC608A的配置示例
// sdkconfig中启用:
// CONFIG_ESP_TLS_USE_SECURE_ELEMENT=y
// CONFIG_ATCA_MBEDTLS_ECDH_BACKEND=y

// 初始化HSM
#include "cryptoauthlib.h"

ATCAIfaceCfg cfg = {
    .iface_type = ATCA_I2C_IFACE,
    .devtype = ATECC608A,
    .atcai2c.slave_address = 0x5C,
    .atcai2c.bus = 0,
    .atcai2c.baud = 100000,
};

atcab_init(&cfg);

// 使用HSM进行ECDSA签名
uint8_t message_hash[32];
uint8_t signature[64];
atcab_sign(0, message_hash, signature);  // 槽位0的私钥签名
```

### 10.3 连接AWS IoT Core

```c
// mutual TLS配置
esp_tls_cfg_t tls_cfg = {
    .use_secure_element = true,    // 使用HSM
    .clientcert_buf = device_cert,  // 设备证书(从HSM读取)
    .clientcert_bytes = cert_len,
};

// 建立TLS连接,私钥签名由HSM完成
esp_tls_conn_new_sync(AWS_ENDPOINT, strlen(AWS_ENDPOINT),
                       8883, &tls_cfg);
```

AWS IoT Core通过Just-In-Time Provisioning(JITP)自动注册设备:设备首次连接时提交设备证书,如果证书由注册的CA签发,IoT Core自动创建Thing并授予权限。

## 11. 挑战与权衡

### 11.1 成本考量

| 成本项 | 无HSM | 有HSM | 备注 |
|--------|-------|-------|------|
| BOM成本 | $0 | $0.50-1.50 | 取决于型号 |
| 开发成本 | 低 | 中 | 需要驱动和集成工作 |
| 认证成本 | 无 | 取决于需求 | FIPS认证费用高 |
| 安全风险成本 | 高 | 低 | 数据泄露、设备克隆风险 |

### 11.2 规模化配给挑战

- **密钥注入**:百万级设备需要在工厂线上逐一配给
- **证书管理**:每个设备一张证书,生命周期管理复杂
- **密钥归档**:是否需要备份密钥?如何安全备份?
- **供应链安全**:HSM从出厂到焊接的整个供应链需要信任链

### 11.3 密钥生命周期管理

```
生成 -> 配给 -> 部署 -> 使用 -> 轮换 -> 归档/销毁
 |       |       |       |       |        |
 HSM内部  工厂    设备    运行中   证书到期  设备退役
 或CA    产线    现场    持续    密钥更新  密钥擦除
```

关键问题:
- 密钥轮换如何在不取出旧密钥的情况下完成?
- 证书到期后如何续期?
- 设备退役时如何确保密钥不可恢复?

## 总结

HSM为IoT设备提供了密钥安全的硬件级保障。核心要点:

1. **密钥不外泄**:所有涉及密钥的运算在HSM内部完成,这是最大的安全优势
2. **防篡改**:物理攻击检测与密钥自毁机制
3. **合规认证**:FIPS/CC认证为安全提供独立验证
4. **多种形态**:从云端的网络HSM到设备端的嵌入式HSM,覆盖全链路
5. **IoT集成**:通过I2C接口,MCU可以轻松集成嵌入式HSM

对于资源受限的IoT设备,嵌入式HSM(如ATECC608A、SE050)以不到1美元的成本提供了不可替代的安全价值。在实际项目中,应将HSM作为设备安全架构的基础设施,而非可选组件。

## 参考文献

1. NIST FIPS 140-3, "Security Requirements for Cryptographic Modules", 2019
2. Microchip, "ATECC608A Data Sheet", DS40002165B, 2020
3. NXP, "SE050 Product Data Sheet", SE050-DS, 2021
4. Amazon Web Services, "Connecting ESP32 to AWS IoT Core with ATECC608A", AWS IoT Documentation, 2022
5. GlobalPlatform, "Secure Element Protection Profile", v2.1, 2020
