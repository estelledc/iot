# BLE安全机制：配对/绑定/加密详解
> **难度**：🟡 中级 | **领域**：BLE安全 | **阅读时间**：约 20 分钟

## 引言

想象你第一次去朋友家做客。门口的对讲机响了，朋友问谁啊，你回答名字后他开门让你进来--这就是配对(Pairing)。朋友记住了你的脸，下次来直接开门不用再自报家门--这就是绑定(Bonding)。而你们在家里的私密对话不会被路人听到--这就是加密(Encryption)。BLE 的安全机制正是围绕这三个核心概念构建的。

本文将系统讲解 BLE 安全体系的工作原理，帮助你在 IoT 项目中正确实施安全防护。

## 1. BLE安全体系概览

### 1.1 三大安全支柱

```
+--配对(Pairing)--+  +--加密(Encryption)--+  +--隐私(Privacy)--+
| 身份验证        |  | 数据保护            |  | 地址随机化      |
| 密钥交换        |  | AES-CCM加密        |  | 防止追踪        |
+-----------------+  +--------------------+  +-----------------+
       |                     |                      |
  [生成密钥]  -------->  [使用密钥]  <--------  [保护身份]
```

### 1.2 安全级别

| 级别 | 名称 | 要求 | 适用场景 |
|------|------|------|----------|
| Level 1 | 无安全 | 无加密无认证 | 公开广播 |
| Level 2 | 未认证加密 | 加密(Just Works) | 低风险数据 |
| Level 3 | 认证加密 | 加密+MITM保护 | 敏感数据 |
| Level 4 | SC认证加密 | LE Secure Connections+MITM | 高安全需求 |

### 1.3 安全管理器SMP

所有配对操作由 SMP(Security Manager Protocol)处理，使用固定 L2CAP 通道(CID=0x0006)。

## 2. 配对过程

### 2.1 配对三阶段

```
Phase 1: 特性交换
[Initiator] ---Pairing Request--->  [Responder]
            <--Pairing Response---
交换: IO能力、OOB可用性、认证需求、密钥长度

Phase 2: 密钥生成
Legacy: TK --> STK
Secure Connections: ECDH --> LTK

Phase 3: 密钥分发
分发LTK、IRK、CSRK(用Phase 2密钥加密传输)
```

### 2.2 IO能力与配对方法

设备输入输出能力决定配对方法：

```
IO能力类型:
- DisplayOnly: 有显示无输入
- DisplayYesNo: 有显示+是否按键
- KeyboardOnly: 有键盘无显示
- NoInputNoOutput: 无IO
- KeyboardDisplay: 键盘+显示

LE Secure Connections方法选择:
| Init \ Resp  | DispOnly | DispYN | Keybd  | NoIO |
|-------------|----------|--------|--------|------|
| DisplayOnly | JW       | JW     | PK(R)  | JW   |
| DisplayYesNo| JW       | NC     | PK(R)  | JW   |
| KeyboardOnly| PK(I)    | PK(I)  | PK(2)  | JW   |
| NoIO        | JW       | JW     | JW     | JW   |

JW=Just Works, NC=Numeric Comparison, PK=Passkey
```

## 3. Legacy Pairing(传统配对)

### 3.1 流程

BLE 4.0/4.1 使用的配对方式：

```
1. 生成TK(Temporary Key):
   - Just Works: TK = 0
   - Passkey: TK = 用户输入6位数字
   - OOB: TK = 带外通道传输的128位随机数
2. 计算确认值: Confirm = c1(TK, Rand, info)
3. 交换确认值和随机数并验证
4. 生成STK: STK = s1(TK, Srand, Mrand)
5. 用STK加密后分发LTK
```

### 3.2 安全缺陷

```
被动窃听攻击(Just Works):
- TK=0, 攻击者捕获Mrand/Srand后直接算出STK
- 结论: Legacy Just Works对被动窃听零防护

Passkey也不安全:
- 6位数字仅100万种可能
- 可离线暴力破解
```

## 4. LE Secure Connections

### 4.1 ECDH密钥交换

BLE 4.2 引入的安全连接使用椭圆曲线 Diffie-Hellman：

```
1. 双方各自生成ECDH密钥对: (SK, PK)
2. 交换公钥: PKi <--> PKr
3. 计算共享密钥: DHKey = ECDH(自己SK, 对方PK)
4. 认证阶段(取决于配对方法)
5. 派生LTK: LTK = f5(DHKey, N_I, N_R, Addr_I, Addr_R)

被动窃听者只能看到公钥, 无法推导DHKey(ECDH难题)
```

### 4.2 Numeric Comparison

LE Secure Connections 引入的新方法：

```python
def numeric_comparison():
    # 双方已交换公钥并计算DHKey
    # 1. 各自生成128位随机数Na, Nb
    # 2. 计算commitment并交换验证
    # 3. 双方独立计算6位验证码:
    Va = g2(PKi_x, PKr_x, Na, Nb) % 1000000
    Vb = g2(PKi_x, PKr_x, Na, Nb) % 1000000
    # 4. 用户确认两端显示数字一致
    # 一致=安全, 不一致=有中间人攻击
```

### 4.3 Legacy vs Secure Connections

| 特性 | Legacy | Secure Connections |
|------|--------|-------------------|
| 密钥交换 | 对称TK方案 | ECDH非对称 |
| 抗被动窃听 | JW不抗 | 全部抗 |
| 前向安全 | 无 | 有 |
| 要求BLE版本 | 4.0+ | 4.2+ |

## 5. 关联模型详解

### 5.1 Just Works

无用户交互自动完成。不提供MITM保护，适用于无IO能力的传感器。Legacy下TK=0无安全性；SC下ECDH保护，抗被动窃听但不抗主动MITM。

### 5.2 Passkey Entry

一端显示6位数字，用户在另一端输入。SC模式下每一位独立验证(20轮)，暴力需2^20次在线尝试。

### 5.3 Out-of-Band(OOB)

利用非蓝牙通道交换认证信息：

```
常见OOB通道:
- NFC: 触碰配对(通信范围仅几厘米, 安全性最高)
- QR码: 扫码配对
- USB: 有线传输
```

## 6. 密钥体系

### 6.1 密钥类型

| 密钥 | 全称 | 用途 |
|------|------|------|
| LTK | Long Term Key | 连接加密 |
| IRK | Identity Resolving Key | 解析随机地址 |
| CSRK | Connection Signature Resolving Key | 数据签名 |

### 6.2 绑定(Bonding)

将配对密钥持久化存储，重连时无需重新配对：

```c
// 绑定信息结构
struct bond_info {
    bt_addr_le_t peer_addr;     // 对端地址
    uint8_t      ltk[16];       // 加密密钥
    uint8_t      irk[16];       // 隐私密钥
    uint8_t      csrk[16];      // 签名密钥
    uint8_t      security_level;
};
// 存储于Flash/EEPROM, 每条约80字节, 通常8-16槽
```

### 6.3 重连流程

```
1. Central连接到Peripheral
2. Central发送LL_ENC_REQ(含EDIV+Rand标识)
3. Peripheral查找匹配LTK
4. 双方用LTK建立加密(几十毫秒, 无需配对)
```

## 7. 加密机制

### 7.1 AES-CCM加密

BLE 使用 AES-128-CCM 进行链路层加密：

```
参数:
- 密钥: 128位(LTK或STK)
- Nonce: 13字节(packetCounter + direction + IV)
- 输出: 密文 + 4字节MIC(消息完整性码)

加密包: [Header(明文)] [Payload(密文)] [MIC(4B)]
特点: 链路层实现, 对上层透明, 每包不同Nonce防重放
```

### 7.2 加密代码示例

```c
void ll_encrypt_pdu(uint8_t *pdu, uint16_t len,
                    uint8_t *key, uint64_t counter,
                    uint8_t direction) {
    uint8_t nonce[13];
    // nonce = counter(5B) + direction(1B) + IV(7B)
    build_nonce(nonce, counter, direction, iv);

    uint8_t mic[4];
    aes_ccm_encrypt(key, nonce,
                    pdu, 1,           // AAD: header
                    pdu + 1, len - 1, // payload
                    pdu + 1,          // 密文输出
                    mic);
    memcpy(pdu + len, mic, 4);
}
```

## 8. 隐私机制

### 8.1 地址随机化

BLE 通过随机化地址防止追踪：

```
地址类型:
- Public: 固定, IEEE分配(可追踪)
- Random Static: 每次上电可变
- Random Resolvable(RPA): 周期变化, 已绑定设备可解析
- Random Non-Resolvable: 完全随机不可追踪
```

### 8.2 RPA解析

```python
def resolve_rpa(rpa_address, irk):
    """用IRK尝试解析随机可解析地址"""
    prand = rpa_address[3:6]       # 高3字节
    hash_recv = rpa_address[0:3]   # 低3字节
    # ah函数: 用IRK加密prand取低24位
    hash_calc = aes_encrypt(irk, pad(prand))[0:3]
    return hash_calc == hash_recv  # True=是该设备

# 扫描时遍历已绑定设备IRK尝试解析
for dev in bond_database:
    if resolve_rpa(scanned_addr, dev.irk):
        print(f"识别: {dev.name}")
```

### 8.3 RPA轮换

RPA 建议每 15 分钟更换一次(可配 1秒-11.5小时)。攻击者无法通过地址持续追踪，已绑定设备仍可通过 IRK 识别。

## 9. 已知漏洞

### 9.1 主要攻击

| 攻击 | 年份 | 原理 |
|------|------|------|
| KNOB | 2019 | 操纵密钥长度协商至7字节 |
| BLESA | 2020 | 重连时缺乏认证导致欺骗 |
| BLURtooth | 2020 | 跨传输密钥派生漏洞 |
| SweynTooth | 2020 | 链路层实现缺陷致拒绝服务 |

### 9.2 KNOB攻击

```
正常: A--"支持16字节密钥"-->B, 使用128位加密
攻击: A-->Attacker--"支持7字节"-->B, 使用56位(可暴力破解)
防护: 最小密钥长度设为16字节(BLE 5.1+已修复)
```

### 9.3 固定Passkey风险

某些IoT设备使用固定Passkey(如000000)。攻击者获知后可发起MITM攻击。应使用动态Passkey或OOB，并实现尝试次数限制。

## 10. IoT安全最佳实践

### 10.1 安全策略选择

```
数据敏感(健康/支付)?
  是 --> Level 4 (SC + Numeric Comparison/OOB)
  否 --> 需防伪造?
           是 --> Level 3 (Passkey)
           否 --> Level 2 (Just Works + 应用层补充)
```

### 10.2 无头设备方案

```c
// 无IO的IoT设备安全组合:
// 方案: 按钮触发窗口 + Just Works + 应用层Token

struct security_config {
    bool button_window;        // 按住才接受配对
    uint8_t window_sec;        // 窗口30-60秒
    uint8_t device_token[16];  // 出厂预置token
    // 流程: 按钮->JW配对->App用token做应用层认证
};
```

### 10.3 开发检查清单

```
密钥管理:
- 使用LE Secure Connections
- 最小密钥128位
- 绑定信息加密存储
- 限制最大绑定数量

配对控制:
- 非配对模式拒绝请求
- 配对失败计数+锁定
- 配对窗口有时间限制

数据保护:
- 敏感特征值要求加密访问
- 验证连接参数(防降级)

隐私:
- 启用RPA
- 设备名称不含个人信息
```

## 总结

BLE 安全是层次化体系：配对建立信任并生成密钥，加密保护数据不被窃听，隐私防止设备被追踪。LE Secure Connections 解决了传统配对的被动窃听漏洞，是当前推荐方式。IoT 设备通常缺少丰富界面，需结合物理确认、应用层认证和 OOB 通道来弥补 Just Works 的不足。安全需要从配对、密钥管理、加密到固件保护的全栈防御。

## 参考文献

1. Bluetooth SIG, "Core Specification v5.3, Vol 3 Part H: Security Manager", 2021
2. NIST, "Guide to Bluetooth Security (SP 800-121 Rev 2)", 2017
3. Antonioli D. et al., "KNOB Attack", USENIX Security, 2019
4. Wu J. et al., "BLESA: Spoofing Attacks against Reconnections in BLE", WOOT, 2020
5. Nordic Semiconductor, "nRF Connect SDK Security Guide", developer.nordicsemi.com
