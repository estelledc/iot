# 身份联邦 FIDO2/WebAuthn 在 IoT 中的应用

> **难度**：🟡 中级 | **领域**：身份认证、设备管理 | **阅读时间**：约 18 分钟

## 日常类比

传统的门禁系统用钥匙或密码卡：你得记住密码，或者随身带卡。丢了密码本或卡被复制，别人就能冒充你进门。

FIDO2/WebAuthn 像是升级版的生物识别门禁：你的指纹（私钥）永远不离开你的身体（设备），门禁系统只需要确认"这个人的指纹和注册时一致"。即使有人偷拍了门禁系统的数据库，也拿不到你的指纹——因为数据库里只有指纹的"数学摘要"（公钥），无法反推出原始指纹。

对 IoT 设备来说，这意味着：每个设备出厂时就有自己独一无二的"指纹"（设备密钥），注册到云平台时只上传"摘要"，即使云平台被攻破，攻击者也无法伪造设备身份。

## 1. FIDO2 架构

### 1.1 核心组件

```
┌─────────────────────────────────────────────────────┐
│                    依赖方 (Relying Party)             │
│                    (云平台/服务器)                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  存储: 公钥 + 凭证 ID + 设备元数据          │    │
│  └─────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────┘
                       │ WebAuthn API / FIDO2 协议
                       │
┌──────────────────────┴──────────────────────────────┐
│                    客户端 (Client)                    │
│              (浏览器 / 设备代理 / 网关)               │
└──────────────────────┬──────────────────────────────┘
                       │ CTAP2 协议
                       │
┌──────────────────────┴──────────────────────────────┐
│                 认证器 (Authenticator)                │
│           (安全元件 / TPM / 生物识别模块)             │
│  ┌─────────────────────────────────────────────┐    │
│  │  存储: 私钥 (永不导出)                       │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 1.2 协议栈

| 层级 | 协议 | 功能 |
|------|------|------|
| 应用层 | WebAuthn API | 浏览器/应用与 RP 交互 |
| 传输层 | CTAP2 | 客户端与认证器通信 |
| 认证器 | CTAP2 命令 | 密钥生成、签名 |
| 硬件层 | 安全元件/TPM | 密钥存储与保护 |

### 1.3 与传统方案对比

| 维度 | 密码 | PKI 证书 | OAuth 2.0 | FIDO2 |
|------|------|---------|-----------|-------|
| 凭证存储 | 服务器 | 设备+CA | 授权服务器 | 仅设备 |
| 钓鱼防护 | 无 | 部分 | 部分 | 完全 |
| 可扩展性 | 差 | 中（CA瓶颈） | 好 | 好 |
| 设备成本 | 无 | 中（证书管理） | 低 | 低-中 |
| 离线能力 | 有 | 有 | 无 | 有 |
| 密钥泄露影响 | 全局 | 单设备 | 令牌有效期 | 单设备 |

## 2. WebAuthn 注册与认证流程

### 2.1 设备注册（Registration）

```python
# 服务端：生成注册挑战
import secrets
import json
from base64 import urlsafe_b64encode

def generate_registration_options(device_id, device_name):
    """生成 WebAuthn 注册选项"""
    challenge = secrets.token_bytes(32)
    
    options = {
        "challenge": urlsafe_b64encode(challenge).decode(),
        "rp": {
            "name": "IoT Cloud Platform",
            "id": "iot.example.com"
        },
        "user": {
            "id": urlsafe_b64encode(device_id.encode()).decode(),
            "name": device_name,
            "displayName": f"Device: {device_name}"
        },
        "pubKeyCredParams": [
            {"type": "public-key", "alg": -7},   # ES256 (P-256)
            {"type": "public-key", "alg": -8},   # EdDSA (Ed25519)
        ],
        "authenticatorSelection": {
            "authenticatorAttachment": "platform",  # 平台内置认证器
            "residentKey": "required",
            "userVerification": "discouraged"  # IoT 设备无用户交互
        },
        "attestation": "direct",  # 要求设备证明
        "timeout": 60000
    }
    
    # 保存 challenge 用于验证响应
    store_challenge(device_id, challenge)
    return options
```

### 2.2 设备认证（Authentication）

```python
# 服务端：验证认证响应
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
import cbor2

def verify_authentication(device_id, response):
    """验证设备的认证响应"""
    # 1. 获取存储的公钥和挑战
    stored_pubkey = get_stored_public_key(device_id)
    challenge = get_stored_challenge(device_id)
    
    # 2. 解析认证器数据
    auth_data = response['authenticatorData']
    client_data_json = response['clientDataJSON']
    signature = response['signature']
    
    # 3. 验证 RP ID 哈希
    rp_id_hash = auth_data[:32]
    expected_hash = hashlib.sha256(b"iot.example.com").digest()
    assert rp_id_hash == expected_hash
    
    # 4. 验证签名计数器（防重放）
    sign_count = int.from_bytes(auth_data[33:37], 'big')
    stored_count = get_stored_sign_count(device_id)
    assert sign_count > stored_count
    
    # 5. 验证签名
    # signed_data = authenticatorData || SHA-256(clientDataJSON)
    client_data_hash = hashlib.sha256(client_data_json).digest()
    signed_data = auth_data + client_data_hash
    
    public_key = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256R1(), stored_pubkey
    )
    public_key.verify(signature, signed_data, ec.ECDSA(hashes.SHA256()))
    
    # 6. 更新签名计数器
    update_sign_count(device_id, sign_count)
    
    return True
```

## 3. Passkeys 与设备凭证

### 3.1 Passkeys 概念

Passkeys 是 FIDO2 的消费者友好品牌名，核心特性：
- 可发现凭证（Discoverable Credentials）：无需输入用户名
- 跨设备同步（通过 iCloud/Google 密码管理器）
- 对 IoT：设备凭证不同步，绑定硬件

### 3.2 IoT 设备凭证 vs 用户 Passkeys

| 特性 | 用户 Passkeys | IoT 设备凭证 |
|------|--------------|-------------|
| 同步 | 跨设备同步 | 绑定单一硬件 |
| 用户验证 | 生物识别/PIN | 无（自动） |
| 生命周期 | 用户控制 | 设备生命周期 |
| 证明 | 可选 | 必须（设备身份） |
| 数量 | 少量（每人几十个） | 海量（百万级） |

### 3.3 设备证明（Attestation）

```c
// 设备端：使用安全元件生成证明
#include "atecc608b.h"

typedef struct {
    uint8_t aaguid[16];        // 认证器类型标识
    uint8_t credential_id[64]; // 凭证 ID
    uint8_t public_key[65];    // ECDSA P-256 公钥
    uint8_t attestation_sig[64]; // 设备证书签名
} attestation_object_t;

int create_credential(const uint8_t *challenge, size_t challenge_len,
                      attestation_object_t *output) {
    // 1. 在安全元件中生成新密钥对
    uint8_t key_slot = find_free_slot();
    atecc_genkey(key_slot, output->public_key);
    
    // 2. 生成凭证 ID（包含密钥槽位信息，加密保护）
    generate_credential_id(key_slot, output->credential_id);
    
    // 3. 构造待签名数据
    uint8_t auth_data[200];
    size_t auth_data_len = build_auth_data(
        output->aaguid, output->credential_id, 
        output->public_key, auth_data
    );
    
    // 4. 使用设备证明密钥签名（出厂预置）
    uint8_t signed_data[32];
    sha256(auth_data, auth_data_len, signed_data);
    atecc_sign(ATTESTATION_KEY_SLOT, signed_data, 
               output->attestation_sig);
    
    return 0;
}
```

## 4. FIDO Device Onboard (FDO)

### 4.1 零接触配置问题

传统 IoT 设备部署流程：
1. 工厂生产 → 2. 运输 → 3. 现场安装 → 4. 手动配置 WiFi/证书 → 5. 注册到云平台

FDO 的目标：消除步骤 4 的人工干预。

### 4.2 FDO 架构

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│  制造商   │    │  中间商/集成商 │    │  最终用户     │
│          │    │              │    │  (设备所有者)  │
│ 写入初始  │    │  转移所有权   │    │  完成配置     │
│ 凭证     │    │  凭证        │    │              │
└────┬─────┘    └──────┬───────┘    └──────┬───────┘
     │                 │                   │
     ↓                 ↓                   ↓
┌─────────────────────────────────────────────────┐
│                    FDO 协议                       │
│                                                  │
│  TO0: 所有者注册 (Owner → Rendezvous Server)     │
│  TO1: 设备发现 (Device → Rendezvous Server)      │
│  TO2: 设备配置 (Device ↔ Owner)                  │
└─────────────────────────────────────────────────┘
```

### 4.3 FDO 流程详解

```python
# FDO TO2 协议简化实现（设备端）
class FDODevice:
    def __init__(self, device_credential):
        self.cred = device_credential  # 出厂写入
        self.rendezvous_url = device_credential['rv_url']
    
    async def onboard(self):
        """设备上电后自动执行"""
        
        # TO1: 联系 Rendezvous Server，获取 Owner 地址
        owner_url = await self._to1_discover_owner()
        
        # TO2: 与 Owner 建立安全通道
        session = await self._to2_hello(owner_url)
        
        # TO2: 相互认证
        await self._to2_prove_device(session)
        owner_verified = await self._to2_verify_owner(session)
        
        if owner_verified:
            # 接收配置信息
            config = await self._to2_receive_config(session)
            
            # 应用配置（WiFi、MQTT broker、证书等）
            self._apply_config(config)
            
            # 替换凭证（绑定到新 Owner）
            new_cred = await self._to2_replace_credential(session)
            self._store_credential(new_cred)
            
            return True
        return False
    
    async def _to1_discover_owner(self):
        """TO1: 设备向 Rendezvous Server 查询 Owner"""
        # 使用出厂凭证中的 GUID 查询
        response = await http_post(
            f"{self.rendezvous_url}/to1",
            json={"guid": self.cred['guid']}
        )
        return response['owner_url']
```

### 4.4 FDO vs 传统配置方式

| 维度 | 手动配置 | 预配置 | FDO |
|------|---------|--------|-----|
| 现场人工 | 必须 | 不需要 | 不需要 |
| 供应链灵活性 | 高 | 低（绑定客户） | 高 |
| 安全性 | 低（明文密码） | 中 | 高（密码学绑定） |
| 规模化 | 差 | 中 | 好 |
| 所有权转移 | 复杂 | 需要重新配置 | 协议原生支持 |

## 5. 百万级设备的可扩展性

### 5.1 挑战

- 每个设备一个唯一密钥对 → 密钥管理复杂度
- 注册/认证请求峰值（设备批量上电）
- 证书/凭证吊销的实时性
- 跨区域部署的延迟要求

### 5.2 架构设计

```
                    ┌─────────────────────┐
                    │   全局注册中心       │
                    │   (凭证数据库)       │
                    └──────────┬──────────┘
                               │ 同步
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────┴──┐   ┌────────┴───┐   ┌───────┴────┐
    │ 区域节点 A  │   │ 区域节点 B  │   │ 区域节点 C  │
    │ (亚太)     │   │ (欧洲)     │   │ (北美)     │
    └─────┬──────┘   └─────┬──────┘   └─────┬──────┘
          │                │                │
    ┌─────┴─────┐    ┌────┴─────┐    ┌────┴─────┐
    │ 边缘网关   │    │ 边缘网关  │    │ 边缘网关  │
    │ (本地缓存) │    │ (本地缓存)│    │ (本地缓存)│
    └─────┬─────┘    └────┬─────┘    └────┬─────┘
          │               │               │
    ┌─────┴─────┐   ┌────┴─────┐   ┌────┴─────┐
    │ 设备群     │   │ 设备群    │   │ 设备群    │
    │ (1000+)   │   │ (1000+)  │   │ (1000+)  │
    └───────────┘   └──────────┘   └──────────┘
```

### 5.3 性能优化策略

```python
# 批量设备认证优化
class BatchAuthenticator:
    def __init__(self, max_batch_size=100, timeout_ms=50):
        self.batch = []
        self.max_batch_size = max_batch_size
        self.timeout_ms = timeout_ms
    
    async def authenticate(self, device_id, auth_response):
        """将认证请求加入批次"""
        future = asyncio.Future()
        self.batch.append((device_id, auth_response, future))
        
        if len(self.batch) >= self.max_batch_size:
            await self._process_batch()
        
        return await future
    
    async def _process_batch(self):
        """批量验证签名（利用硬件加速）"""
        batch = self.batch
        self.batch = []
        
        # 批量获取公钥（单次数据库查询）
        device_ids = [item[0] for item in batch]
        pubkeys = await db.batch_get_pubkeys(device_ids)
        
        # 并行验证签名
        tasks = []
        for (device_id, response, future), pubkey in zip(batch, pubkeys):
            task = self._verify_single(device_id, response, pubkey, future)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
```

## 6. 与现有 IoT 协议集成

### 6.1 MQTT + FIDO2

```
设备启动 → FIDO2 认证 → 获取短期 JWT → MQTT CONNECT (JWT as password)
                                              ↓
                                        Broker 验证 JWT
                                              ↓
                                        建立 MQTT 会话
```

### 6.2 CoAP + DTLS + FIDO2

```
设备 → DTLS 握手 (使用 FIDO2 派生的密钥) → CoAP 通信
```

### 6.3 实际集成示例

```python
# MQTT 客户端使用 FIDO2 认证
import paho.mqtt.client as mqtt
import json

class FIDO2MQTTClient:
    def __init__(self, broker_host, device_id):
        self.broker = broker_host
        self.device_id = device_id
        self.client = mqtt.Client(client_id=device_id)
    
    def connect(self):
        # 1. 执行 FIDO2 认证获取 JWT
        jwt_token = self._fido2_authenticate()
        
        # 2. 使用 JWT 作为 MQTT 密码
        self.client.username_pw_set(
            username=self.device_id,
            password=jwt_token
        )
        
        # 3. 连接 MQTT Broker
        self.client.tls_set()  # 启用 TLS
        self.client.connect(self.broker, port=8883)
    
    def _fido2_authenticate(self):
        """使用安全元件执行 FIDO2 认证"""
        # 从认证服务器获取挑战
        challenge = self._get_challenge()
        
        # 安全元件签名
        signature = secure_element.sign(
            key_slot=0,
            data=challenge
        )
        
        # 提交签名获取 JWT
        response = requests.post(
            f"https://auth.example.com/fido2/verify",
            json={
                "device_id": self.device_id,
                "challenge": challenge.hex(),
                "signature": signature.hex()
            }
        )
        
        return response.json()['jwt']
```

## 7. 实践建议

### 7.1 初学者入门路径

1. 在浏览器中体验 WebAuthn（webauthn.io 演示站点）
2. 使用 Python `fido2` 库实现简单的注册/认证服务器
3. 在 ESP32 + ATECC608B 上实现设备端 FIDO2
4. 搭建完整的设备注册 → 认证 → MQTT 连接流程
5. 研究 FIDO Device Onboard 规范

### 7.2 具体调优建议

**安全元件选择**：
- 低成本方案：ATECC608B（$0.60，支持 P-256）
- 需要 FDO：支持 FIDO2 的安全元件（如 NXP SE050）
- 高安全需求：带 CC 认证的专用 FIDO 芯片

**协议选择**：
- 设备 → 云：FIDO2 认证 + JWT 令牌
- 设备 → 网关：DTLS-PSK（预共享密钥，FIDO2 派生）
- 网关 → 云：mTLS + FIDO2 设备证明

**规模化部署**：
- 使用 FDO 实现零接触配置
- 区域化部署认证服务器（降低延迟）
- 实现凭证缓存（网关层缓存已认证设备）
- 设计优雅的降级策略（认证服务不可用时）

## 参考文献

1. FIDO Alliance. "FIDO2: Web Authentication (WebAuthn)." W3C Recommendation, 2021.
2. FIDO Alliance. "Client to Authenticator Protocol (CTAP) v2.1." 2024.
3. FIDO Alliance. "FIDO Device Onboard (FDO) Specification v1.1." 2023.
4. Bindel, N. et al. "FIDO2 for IoT: Scalable Device Authentication." IEEE IoT Journal, 2024.
5. Lundberg, E. "java-webauthn-server: Server-side WebAuthn Library." Yubico, GitHub, 2024.
6. NXP. "SE050 FIDO2 Implementation Guide." Application Note, 2024.
7. Microchip. "ATECC608B Trust Platform Design Guide." 2023.
8. IETF. "RFC 8152: CBOR Object Signing and Encryption (COSE)." 2017.
9. Google. "Passkeys Developer Guide." 2024.
10. Grassi, P. et al. "NIST SP 800-63B: Digital Identity Guidelines - Authentication." 2024.
