---
schema_version: '1.0'
id: side-channel-attack-defense
title: 侧信道攻击与防护
layer: 6
content_type: UNKNOWN
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 侧信道攻击与防护

> **难度**：🟡 中级 | **领域**：硬件安全、密码工程 | **阅读时间**：约 20 分钟

## 日常类比

想象你在猜一个保险箱的密码。正常方式是一个个试（暴力破解），但聪明的窃贼发现：转动密码盘时，转到正确数字会发出微妙的"咔嗒"声。他不需要试遍所有组合，只需要"听"就能逐位破解密码。

侧信道攻击的原理类似：不直接攻击加密算法的数学结构，而是通过观察设备运行时的"副产品"——功耗变化、执行时间、电磁辐射——来推断密钥。就像通过观察一个人打字时手指的移动来猜测密码，而不是去破解密码本身。对 IoT 设备来说，这种攻击特别危险，因为攻击者往往能物理接触设备。

## 1. 侧信道攻击分类

### 1.1 攻击类型总览

| 攻击类型 | 观测对象 | 设备要求 | 难度 | IoT 威胁等级 |
|---------|---------|---------|------|-------------|
| 时序攻击 | 执行时间 | 网络连接即可 | 低 | 高 |
| 简单功耗分析(SPA) | 功耗波形 | 示波器 | 中 | 高 |
| 差分功耗分析(DPA) | 功耗统计 | 示波器+采集卡 | 中高 | 高 |
| 相关功耗分析(CPA) | 功耗相关性 | 同 DPA | 高 | 高 |
| 电磁分析(EMA) | EM 辐射 | 近场探头 | 中高 | 中 |
| 缓存攻击 | 缓存命中/未命中 | 共享系统 | 高 | 中低 |
| 故障注入 | 计算错误 | 激光/电压毛刺 | 高 | 中 |

### 1.2 攻击模型

```
        ┌─────────────────────────────────┐
        │         加密设备                 │
        │  ┌─────────────────────────┐    │
        │  │  密钥 K (秘密)          │    │
  输入  │  │         ↓               │    │  输出
 ──────→│  │  加密算法 E(K, M)       │────→ 密文
        │  │         ↓               │    │
        │  └─────────────────────────┘    │
        └──────────┬──────────────────────┘
                   │ 泄露信息
            ┌──────┴──────┐
            │ 功耗/时间/EM │
            └──────┬──────┘
                   ↓
            ┌─────────────┐
            │  攻击者分析  │ → 恢复密钥 K
            └─────────────┘
```

## 2. 功耗分析攻击

### 2.1 简单功耗分析（SPA）

SPA 通过单条或少量功耗轨迹直接观察密码操作的模式：

```
功耗
 │    ┌─┐     ┌─┐  ┌─┐     ┌─┐  ┌─┐
 │    │ │     │ │  │ │     │ │  │ │
 │ ┌──┘ └──┐──┘ └──┘ └──┐──┘ └──┘ └──┐
 │ │   S   │  S    M    │  S    M    │
 └─┴───────┴────────────┴────────────┴── 时间
   
   S = Square (平方操作) → 密钥位 = 0
   M = Multiply (乘法操作) → 密钥位 = 1
   
   观察到的模式: S, SM, SM → 密钥位: 0, 1, 1
```

RSA 的"平方-乘"算法中，密钥为 1 时执行乘法（功耗高），为 0 时只做平方（功耗低）。

### 2.2 差分功耗分析（DPA）

DPA 使用统计方法从大量轨迹中提取密钥信息：

```python
# DPA 攻击 AES 第一轮的简化实现
import numpy as np

def dpa_attack_aes(traces, plaintexts, byte_index):
    """
    traces: N x T 矩阵 (N条轨迹，每条T个采样点)
    plaintexts: N x 16 矩阵 (N个明文)
    byte_index: 攻击的密钥字节索引 (0-15)
    """
    num_traces, num_samples = traces.shape
    
    # AES S-Box
    sbox = [0x63, 0x7c, 0x77, 0x7b, ...]  # 256 entries
    
    best_corr = 0
    best_key_byte = 0
    
    # 遍历所有可能的密钥字节值 (0-255)
    for key_guess in range(256):
        # 1. 计算假设的中间值
        hypothetical_values = np.array([
            sbox[plaintexts[i][byte_index] ^ key_guess]
            for i in range(num_traces)
        ])
        
        # 2. 计算假设功耗（汉明重量模型）
        hypothetical_power = np.array([
            bin(v).count('1') for v in hypothetical_values
        ])
        
        # 3. 计算与实际功耗轨迹的相关系数
        for t in range(num_samples):
            corr = np.corrcoef(hypothetical_power, traces[:, t])[0, 1]
            if abs(corr) > best_corr:
                best_corr = abs(corr)
                best_key_byte = key_guess
                best_sample = t
    
    return best_key_byte, best_corr
```

### 2.3 所需轨迹数量

| 目标算法 | 攻击方法 | 典型轨迹数 | 成功率 |
|---------|---------|-----------|--------|
| AES-128 (无防护) | CPA | 50-200 | >99% |
| AES-128 (1阶掩码) | 2阶 DPA | 10,000-50,000 | >95% |
| AES-128 (2阶掩码) | 3阶 DPA | >1,000,000 | ~80% |
| RSA-2048 (无防护) | SPA | 1 | >90% |

## 3. 时序攻击

### 3.1 原理

不同的输入导致不同的执行路径，产生可测量的时间差异：

```c
// 有漏洞的密码比较（时序泄露）
int insecure_compare(const uint8_t *a, const uint8_t *b, size_t len) {
    for (size_t i = 0; i < len; i++) {
        if (a[i] != b[i]) {
            return 0;  // 第一个不匹配就返回
            // 攻击者可以逐字节猜测：
            // 第1字节正确 → 比较到第2字节 → 时间更长
        }
    }
    return 1;
}

// 安全的常量时间比较
int secure_compare(const uint8_t *a, const uint8_t *b, size_t len) {
    volatile uint8_t result = 0;
    for (size_t i = 0; i < len; i++) {
        result |= a[i] ^ b[i];  // 始终比较所有字节
    }
    return (result == 0) ? 1 : 0;
}
```

### 3.2 远程时序攻击

即使通过网络，微秒级的时间差异也可能被利用：

```python
# 远程时序攻击示例（攻击 HMAC 验证）
import time
import requests
import numpy as np

def timing_attack_hmac(url, known_bytes=b''):
    """逐字节恢复 HMAC 值"""
    
    for byte_pos in range(32):  # SHA-256 HMAC = 32 bytes
        timings = {}
        
        for guess in range(256):
            candidate = known_bytes + bytes([guess]) + b'\x00' * (31 - byte_pos)
            
            # 多次测量取中位数（减少网络抖动）
            measurements = []
            for _ in range(100):
                start = time.perf_counter_ns()
                requests.post(url, data={'mac': candidate.hex()})
                elapsed = time.perf_counter_ns() - start
                measurements.append(elapsed)
            
            timings[guess] = np.median(measurements)
        
        # 时间最长的字节值最可能正确
        best_byte = max(timings, key=timings.get)
        known_bytes += bytes([best_byte])
        print(f"Byte {byte_pos}: 0x{best_byte:02x}")
    
    return known_bytes
```

## 4. 电磁辐射分析

### 4.1 近场 vs 远场

| 特性 | 近场探测 | 远场探测 |
|------|---------|---------|
| 距离 | < 1 cm | 数米 |
| 分辨率 | 可定位单个模块 | 整体信号 |
| 设备 | 近场探头 + 示波器 | 天线 + SDR |
| 信噪比 | 高 | 低 |
| 实用性 | 实验室攻击 | 理论/高级攻击 |

### 4.2 EM 攻击的优势

相比功耗分析，电磁分析有独特优势：
- 非接触式（不需要修改电路）
- 可以定位芯片上的特定区域
- 即使有功耗滤波器也可能有效
- 对多核/多模块系统可以分别分析

## 5. 防护对策

### 5.1 掩码（Masking）

核心思想：将敏感中间值与随机数异或，使功耗与密钥无关。

```c
// AES S-Box 的布尔掩码实现
// 原始: y = SBox[x ^ k]
// 掩码: y' = SBox[(x ^ m_in) ^ k] ^ m_out
//       其中 m_in, m_out 是随机掩码

// 预计算掩码 S-Box 表
void compute_masked_sbox(uint8_t masked_sbox[256], 
                         uint8_t m_in, uint8_t m_out) {
    for (int i = 0; i < 256; i++) {
        // 输入去掩码 → 查表 → 输出加掩码
        masked_sbox[i] = sbox[i ^ m_in] ^ m_out;
    }
}

// 掩码 AES 加密（1阶）
void aes_encrypt_masked(uint8_t state[16], const uint8_t key[16]) {
    uint8_t m_in, m_out;
    uint8_t masked_sbox[256];
    
    // 每次加密使用新的随机掩码
    m_in = hardware_rng();
    m_out = hardware_rng();
    compute_masked_sbox(masked_sbox, m_in, m_out);
    
    // 对状态加掩码
    for (int i = 0; i < 16; i++) {
        state[i] ^= m_in;
    }
    
    // AddRoundKey (掩码不影响 XOR)
    for (int i = 0; i < 16; i++) {
        state[i] ^= key[i];
    }
    
    // SubBytes (使用掩码 S-Box)
    for (int i = 0; i < 16; i++) {
        state[i] = masked_sbox[state[i]];
        // 此时 state[i] 带有 m_out 掩码
    }
    
    // ... 后续操作需要相应调整掩码传播
}
```

### 5.2 隐藏（Hiding）

通过添加噪声或随机化执行顺序来降低信噪比：

```c
// 随机延迟插入
void add_random_delays(void) {
    uint8_t delay = hardware_rng() & 0x0F;  // 0-15 个周期
    for (volatile int i = 0; i < delay; i++) {
        __NOP();  // 空操作
    }
}

// 随机化 S-Box 处理顺序（Shuffling）
void shuffled_subbytes(uint8_t state[16]) {
    uint8_t order[16] = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15};
    
    // Fisher-Yates 洗牌
    for (int i = 15; i > 0; i--) {
        uint8_t j = hardware_rng() % (i + 1);
        uint8_t tmp = order[i];
        order[i] = order[j];
        order[j] = tmp;
    }
    
    // 按随机顺序处理
    for (int i = 0; i < 16; i++) {
        state[order[i]] = sbox[state[order[i]]];
    }
}
```

### 5.3 常量时间编程

```c
// 常量时间条件选择（无分支）
uint32_t ct_select(uint32_t a, uint32_t b, uint32_t condition) {
    // condition = 0 → 返回 a
    // condition = 1 → 返回 b
    uint32_t mask = -(uint32_t)(condition != 0);
    return (a & ~mask) | (b & mask);
}

// 常量时间字节比较
uint32_t ct_is_zero(uint32_t x) {
    // 如果 x == 0 返回 1，否则返回 0
    return 1 ^ ((x | -x) >> 31);
}

// 常量时间内存拷贝（条件拷贝）
void ct_cmov(uint8_t *dst, const uint8_t *src, size_t len, 
             uint8_t condition) {
    uint8_t mask = -(uint8_t)(condition != 0);
    for (size_t i = 0; i < len; i++) {
        dst[i] = (dst[i] & ~mask) | (src[i] & mask);
    }
}
```

### 5.4 硬件对策

| 对策 | 原理 | 开销 | 效果 |
|------|------|------|------|
| 双轨逻辑 | 互补信号抵消功耗差异 | 面积 2x | 高 |
| 随机时钟 | 时钟频率随机变化 | 低 | 中 |
| 电压调节 | 片上稳压器平滑功耗 | 中 | 中 |
| 金属屏蔽 | 顶层金属阻挡 EM 泄露 | 低 | 中 |
| 噪声生成器 | 专用电路产生随机功耗 | 低 | 中低 |

## 6. ChipWhisperer 实战平台

### 6.1 平台介绍

ChipWhisperer 是开源的侧信道攻击/评估平台：

| 型号 | 价格 | 采样率 | 目标板 | 适用场景 |
|------|------|--------|--------|---------|
| CW-Lite | ~$250 | 105 MS/s | STM32F3 | 教学/入门 |
| CW-Husky | ~$550 | 200 MS/s | 多种 | 研究/评估 |
| CW-Pro | ~$3000 | 1 GS/s | 任意 | 专业评估 |

### 6.2 使用 ChipWhisperer 攻击 AES

```python
# ChipWhisperer CPA 攻击 AES-128 示例
import chipwhisperer as cw
import numpy as np

# 1. 连接设备
scope = cw.scope()
target = cw.target(scope)

# 2. 配置采集参数
scope.default_setup()
scope.adc.samples = 5000  # 每条轨迹 5000 个采样点

# 3. 采集功耗轨迹
num_traces = 200
traces = np.zeros((num_traces, scope.adc.samples))
textin = np.zeros((num_traces, 16), dtype=np.uint8)

for i in range(num_traces):
    # 生成随机明文
    pt = np.random.randint(0, 256, 16, dtype=np.uint8)
    textin[i] = pt
    
    # 发送明文并采集功耗
    target.simpleserial_write('p', pt.tobytes())
    scope.arm()
    scope.capture()
    traces[i] = scope.get_last_trace()

# 4. CPA 分析
import chipwhisperer.analyzer as cwa

attack = cwa.cpa(traces, textin)
results = attack.run()

# 5. 输出恢复的密钥
print("恢复的密钥:", results.key_guess().hex())
print("相关系数:", results.max_corr())
```

### 6.3 评估防护效果

```python
# 评估掩码实现的安全性
# 使用 TVLA (Test Vector Leakage Assessment)

def tvla_test(traces_fixed, traces_random):
    """
    Welch's t-test: 检测固定输入和随机输入的功耗是否有统计差异
    |t| > 4.5 表示存在泄露
    """
    n1 = len(traces_fixed)
    n2 = len(traces_random)
    
    mean1 = np.mean(traces_fixed, axis=0)
    mean2 = np.mean(traces_random, axis=0)
    var1 = np.var(traces_fixed, axis=0)
    var2 = np.var(traces_random, axis=0)
    
    t_stat = (mean1 - mean2) / np.sqrt(var1/n1 + var2/n2)
    
    # |t| > 4.5 的采样点存在泄露
    leaky_points = np.where(np.abs(t_stat) > 4.5)[0]
    
    return t_stat, leaky_points
```

## 7. 实践建议

### 7.1 初学者入门路径

1. 阅读 ChipWhisperer 官方教程（免费在线 Jupyter Notebooks）
2. 用软件模拟器理解 DPA/CPA 原理（不需要硬件）
3. 购买 CW-Lite 套件，完成 AES 攻击实验
4. 实现简单的掩码对策并验证效果
5. 学习 TVLA 方法评估自己的实现

### 7.2 具体调优建议

**IoT 设备防护优先级**：
- 最高优先：常量时间比较（零成本，防时序攻击）
- 高优先：1 阶布尔掩码（~2x 性能开销，防 DPA）
- 中优先：随机化执行顺序（低开销，增加攻击难度）
- 按需：硬件安全元件（将密码操作移入防护芯片）

**性能与安全的平衡**：
- 1 阶掩码：性能开销 ~2-3x，防护大多数实际攻击
- 2 阶掩码：性能开销 ~5-8x，防护高级攻击者
- 对于 IoT 设备，1 阶掩码 + 随机延迟通常足够

**常见错误**：
- 编译器优化可能消除常量时间代码 → 使用 volatile 或检查汇编
- 掩码实现中的"毛刺"（glitch）可能泄露信息 → 需要形式化验证
- 仅保护加密不保护密钥加载 → 攻击者可能在密钥从存储读取时攻击

## 参考文献

1. Kocher, P. et al. "Differential Power Analysis." CRYPTO 1999.
2. Brier, E. et al. "Correlation Power Analysis with a Leakage Model." CHES 2004.
3. O'Flynn, C. & Chen, Z. "ChipWhisperer: An Open-Source Platform for Hardware Embedded Security Research." COSADE 2014.
4. Schneider, T. & Moradi, A. "Leakage Assessment Methodology." CHES 2015.
5. Rivain, M. & Prouff, E. "Provably Secure Higher-Order Masking of AES." CHES 2010.
6. Bernstein, D.J. "Cache-Timing Attacks on AES." 2005.
7. Mangard, S. et al. "Power Analysis Attacks: Revealing the Secrets of Smart Cards." Springer, 2007.
8. NewAE Technology. "ChipWhisperer Documentation." 2024.
9. Reparaz, O. et al. "Masking vs. Multiparty Computation." TCHES 2024.
10. Chari, S. et al. "Towards Sound Approaches to Counteract Power-Analysis Attacks." CRYPTO 1999.
