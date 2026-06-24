# LoRaWAN安全密钥体系与入网流程
> **难度**：🟡 中级 | **领域**：LoRaWAN安全 | **阅读时间**：约 20 分钟

## 引言

想象你要加入一个需要身份验证的私密俱乐部。你先出示会员卡(证明身份),门卫验证后给你一把当天的临时钥匙(会话密钥),你用这把钥匙打开储物柜存取物品,但看不到别人的储物柜内容。LoRaWAN的安全体系就是这样——设备用永久的"身份凭证"完成入网,然后获得临时的"会话钥匙"进行日常通信,网络运营商和应用提供商各自只能访问自己有权限的数据。

LoRaWAN实现了真正的端到端应用层加密——即使网络服务器被攻破,攻击者也无法读取应用数据。

## 1. 安全架构概览

### 1.1 双层加密设计

```
+---------------------------------------------------+
|  应用层安全: AppSKey端到端加密(设备<->应用服务器)  |
+---------------------------------------------------+
|  网络层安全: NwkSKey完整性(设备<->网络服务器)      |
+---------------------------------------------------+
```

### 1.2 密钥层次结构

```
AppKey (128-bit, 永久根密钥)
    |
    | [入网时推导]
    |
    +-- NwkSKey (网络会话密钥, 持有者: 设备+NS)
    +-- AppSKey (应用会话密钥, 持有者: 设备+AS)
```

分离确保: NS验证帧真实性但不能读内容;AS解密数据但不参与网络管理;一把密钥泄露另一层仍有效。

## 2. 根密钥AppKey

### 2.1 AppKey属性

```
长度: 128 bit (16字节)
算法: AES-128
生命周期: 永久(设备整个生命周期)
预置方式: 制造时写入设备和Join Server
唯一性: 每个设备一个独立AppKey
```

### 2.2 安全存储

```c
// 不安全: 固件中硬编码(永远不要这样做!)
// const uint8_t APP_KEY[] = {0x01, 0x02, ...};

// 安全: 使用安全元件
typedef struct {
    secure_element_t se;  // 如ATECC608A
    uint8_t dev_eui[8];
    // AppKey不直接暴露,只通过SE接口使用
} device_credentials_t;

int derive_session_keys(device_credentials_t *cred,
                        uint8_t *app_nonce, uint8_t *net_id,
                        uint8_t *dev_nonce,
                        uint8_t *nwk_key_out, uint8_t *app_key_out) {
    // SE内部计算,密钥不离开硬件
    return se_derive_keys(cred->se, app_nonce, net_id,
                          dev_nonce, nwk_key_out, app_key_out);
}
```

## 3. OTAA入网流程

### 3.1 JoinRequest消息

```
+----------+----------+-----------+-----+
| AppEUI   | DevEUI   | DevNonce  | MIC |
| (8字节)  | (8字节)  | (2字节)   |(4B) |
+----------+----------+-----------+-----+
```

- AppEUI: 应用标识符(标识Join Server)
- DevEUI: 设备全球唯一标识
- DevNonce: 随机数(防重放,每次入网不同)
- MIC: 用AppKey计算的完整性码

### 3.2 Join Server验证

```python
class JoinServer:
    def process_join_request(self, request):
        # 1. 查找AppKey
        app_key = self.key_store.get_app_key(request.dev_eui)
        if not app_key:
            return None

        # 2. 验证MIC
        expected_mic = compute_join_mic(app_key, request)
        if request.mic != expected_mic:
            return None  # 认证失败

        # 3. 检查DevNonce重复(防重放)
        if self.nonce_store.is_used(request.dev_eui, request.dev_nonce):
            return None
        self.nonce_store.mark_used(request.dev_eui, request.dev_nonce)

        # 4. 生成AppNonce
        app_nonce = generate_random_bytes(3)

        # 5. 构造JoinAccept
        return self.build_join_accept(app_key, app_nonce, request)
```

### 3.3 JoinAccept与密钥推导

```python
def derive_session_keys(app_key, app_nonce, net_id, dev_nonce):
    """双方独立推导相同的会话密钥"""

    # NwkSKey = aes128_encrypt(AppKey, 0x01|AppNonce|NetID|DevNonce|pad)
    nwk_input = bytes([0x01]) + app_nonce + net_id + dev_nonce
    nwk_input += bytes(16 - len(nwk_input))
    nwk_s_key = aes_encrypt(app_key, nwk_input)

    # AppSKey = aes128_encrypt(AppKey, 0x02|AppNonce|NetID|DevNonce|pad)
    app_input = bytes([0x02]) + app_nonce + net_id + dev_nonce
    app_input += bytes(16 - len(app_input))
    app_s_key = aes_encrypt(app_key, app_input)

    return nwk_s_key, app_s_key
```

关键: 两个密钥用相同输入只有首字节不同;推导确定性;双方无需传输密钥本身。

## 4. ABP激活方式

### 4.1 ABP概述

直接将会话密钥预编程到设备中,无需入网流程:

```c
typedef struct {
    uint8_t dev_addr[4];     // 固定设备地址
    uint8_t nwk_s_key[16];   // 预编程网络密钥
    uint8_t app_s_key[16];   // 预编程应用密钥
} abp_config_t;
```

### 4.2 OTAA vs ABP安全对比

| 安全特性 | OTAA | ABP |
|---------|------|-----|
| 密钥更新 | 每次入网更新 | 永不更新 |
| 前向安全性 | 有 | 无 |
| DevAddr | 动态分配 | 固定 |
| 帧计数器重置 | 入网时安全重置 | 重启后回零(危险) |
| 适用场景 | 生产部署 | 快速原型 |

### 4.3 ABP帧计数器问题

```
1. 设备运行,帧计数器=100
2. 设备断电重启,计数器回零
3. 服务器期望FCnt>100
4. 服务器拒绝所有帧(认为重放攻击)
5. 设备无法通信!
```

## 5. 帧安全机制

### 5.1 载荷加密(AES-128 CTR)

```python
def encrypt_payload(app_s_key, dev_addr, direction, f_cnt, payload):
    """加密FRMPayload"""
    encrypted = bytearray()
    num_blocks = (len(payload) + 15) // 16

    for i in range(num_blocks):
        # 构造计数器块
        a_block = bytearray(16)
        a_block[0] = 0x01
        a_block[5] = direction  # 0=上行, 1=下行
        a_block[6:10] = dev_addr
        a_block[10:14] = f_cnt.to_bytes(4, 'little')
        a_block[15] = i + 1

        # 生成密钥流并XOR
        s_block = aes_encrypt(app_s_key, bytes(a_block))
        start = i * 16
        end = min(start + 16, len(payload))
        for j in range(end - start):
            encrypted.append(payload[start + j] ^ s_block[j])

    return bytes(encrypted)
```

### 5.2 MIC计算

```python
def compute_mic(nwk_s_key, direction, dev_addr, f_cnt, msg_body):
    """计算4字节MIC"""
    b0 = bytearray(16)
    b0[0] = 0x49
    b0[5] = direction
    b0[6:10] = dev_addr
    b0[10:14] = f_cnt.to_bytes(4, 'little')
    b0[15] = len(msg_body)

    cmac = aes_cmac(nwk_s_key, bytes(b0) + msg_body)
    return cmac[:4]
```

### 5.3 帧计数器防重放

帧计数器规则: 严格递增,接收方只接受比上次更大的FCnt。攻击者不能重放旧帧,不能篡改(MIC失败),不能打乱序列。

## 6. LoRaWAN 1.1安全增强

### 6.1 密钥进一步细化

```
LoRaWAN 1.0: AppKey --> NwkSKey + AppSKey (2把)
LoRaWAN 1.1: NwkKey --> FNwkSIntKey + SNwkSIntKey + NwkSEncKey (3把网络)
             AppKey --> AppSKey (1把应用)
```

- FNwkSIntKey: 上行MIC计算
- SNwkSIntKey: 下行MIC + 上行MIC的一部分
- NwkSEncKey: MAC命令加密

### 6.2 Join Server独立

1.1中NS只管网络,JS独立管理入网和密钥。NS被攻破不影响新设备入网,支持漫游。

### 6.3 ReJoin机制

允许不完全重新入网的情况下更新密钥: Type 0更新会话密钥,Type 1重新入网到新网络,Type 2更新DevAddr。

## 7. 安全威胁与防护

### 7.1 威胁模型

| 攻击类型 | 防护机制 |
|---------|---------|
| 窃听 | AES-128加密 |
| 重放攻击 | 帧计数器 |
| 帧伪造 | MIC校验 |
| 密钥提取 | 安全元件 |
| 流氓网关 | 无法解密,只能转发 |
| Bit-flipping | MIC检测篡改 |

### 7.2 流氓网关分析

```
能做: 接收转发LoRa帧(但无法解密),记录元数据
不能: 读应用数据/伪造合法帧/重放旧帧/解密JoinAccept
```

### 7.3 安全元件集成

```c
#include "cryptoauthlib.h"

int secure_join_request(uint8_t key_slot,
                        uint8_t *join_request,
                        size_t len,
                        uint8_t *mic_out) {
    // AppKey永远不离开安全元件,MIC在SE内计算
    return atcab_aes_cmac(key_slot, join_request, len, mic_out);
}
```

## 8. 密钥管理最佳实践

### 8.1 制造阶段

```
1. 每设备唯一AppKey(绝不共享)
2. HSM在安全环境中生成密钥
3. 安全通道写入设备安全元件
4. 同时注册到Join Server
5. 密钥不保留在制造系统中
```

### 8.2 运营阶段

```
密钥轮换: 通过重新入网自动更新(建议每月一次)
帧计数器: 使用32位/非易失存储/优先用OTAA
监控: 异常入网行为检测(高频入网可能是攻击)
```

### 8.3 固件安全编码

```c
// 1. 绝不在源码中硬编码密钥
// 2. 从安全元件加载
void init_credentials(void) {
    credentials_load_from_secure_element(&device_creds);
}
// 3. 清除内存中的敏感数据
void cleanup_session(void) {
    memset_s(session_keys, sizeof(session_keys), 0, sizeof(session_keys));
}
```

## 总结

LoRaWAN的安全体系通过精心设计的密钥层次和入网流程,在资源受限的物联网设备上实现了企业级安全保障。

核心要点:
- AppKey是安全基石,必须严格保护,每设备唯一
- OTAA通过随机数交换推导密钥,无需传输密钥本身
- NwkSKey/AppSKey分离实现端到端应用安全
- 帧计数器防重放,ABP计数器重置是主要风险
- LoRaWAN 1.1进一步细化密钥分离,增强漫游安全
- 安全元件是硬件级密钥保护的最佳实践
- 密钥管理贯穿设备全生命周期

## 参考文献

1. LoRa Alliance, "LoRaWAN 1.1 Specification", 2017
2. LoRa Alliance, "LoRaWAN Security: FAQ and Best Practices", 2020
3. G. Avoine et al., "Rescuing LoRaWAN 1.0", Financial Cryptography, 2019
4. Microchip, "ATECC608A Secure Element for LoRaWAN", Application Note
5. X. Yang, "LoRaWAN: Vulnerability Analysis and Practical Exploitation", 2020
