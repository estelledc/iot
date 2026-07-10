---
schema_version: '1.0'
id: secure-multiparty-computation
title: 安全多方计算 MPC 在 IoT 中的应用
layer: 6
content_type: UNKNOWN
difficulty: intermediate
reading_time: 25
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 安全多方计算 MPC 在 IoT 中的应用

> **难度**：🟡 中级 | **领域**：隐私计算、密码学 | **阅读时间**：约 25 分钟

---

## 日常类比

想象三个邻居想知道他们三家的平均月收入，但谁都不想暴露自己的实际工资。传统做法需要一个"可信第三方"——比如找一个大家都信任的公证人来收集数据、算平均值，再把结果告诉大家。

安全多方计算（Secure Multi-Party Computation, MPC）的厉害之处在于：不需要这个公证人。三个邻居可以通过一套巧妙的数学协议，各自只交换加密片段，最终共同计算出平均工资，但谁也无法推断出另外两个人的具体数字。

在 IoT 场景中，这意味着：多个智能家居设备可以联合统计用电模式而不暴露各家的具体用电数据；多家医院的可穿戴设备数据可以联合训练疾病预测模型而不需要汇集原始患者数据。MPC 把"数据可用而不可见"从理论变成了工程实践。

---

## 1. MPC 核心概念与安全模型

### 1.1 形式化定义

MPC 的目标用一句话概括：n 个参与方各持有私有输入 x₁, x₂, ..., xₙ，希望共同计算一个函数 f(x₁, x₂, ..., xₙ)，使得每个参与方只学到计算结果，不泄露其他方的输入。

安全性的核心保证是：MPC 协议的执行应当与"存在一个理想的可信第三方"等价——如果你信不出在理想世界和现实协议之间的区别，这个协议就是安全的。这叫做**理想-现实模拟范式**（Ideal-Real Simulation Paradigm）。

### 1.2 敌手模型

| 敌手类型 | 行为特征 | 安全假设 | 适用场景 |
|----------|----------|----------|----------|
| 半诚实（Semi-honest） | 遵守协议但试图从收到的消息推断信息 | 较弱 | 企业间联合分析 |
| 恶意（Malicious） | 可能任意偏离协议 | 较强 | 对抗性强的场景 |
| 隐蔽（Covert） | 可能作弊但害怕被抓 | 居中 | 商业场景有声誉约束 |

在 IoT 环境下，设备可能被物理攻破，因此恶意模型更贴近现实——但恶意模型的通信和计算开销也更大，这正是 IoT 部署 MPC 的核心矛盾。

### 1.3 安全性参数

- **计算安全**：假设多项式时间内的敌手无法破解（基于计算困难假设如 DDH）
- **统计安全**：允许 2⁻⁴⁰ 量级的出错概率
- **信息论安全**：无论计算能力多强都安全（如 Shamir 秘密共享在诚实多数下）

---

## 2. 基础密码原语

### 2.1 秘密共享（Secret Sharing）

秘密共享是 MPC 最重要的构建模块。直觉是：把一个秘密"拆"成多个碎片分发给参与方，单个碎片不泄露任何信息，但足够多的碎片可以恢复秘密。

**Shamir 秘密共享**（t-out-of-n 阈值方案）：

```python
import random
from functools import reduce

PRIME = 2**61 - 1  # 大质数，定义有限域

def share_secret(secret, n_shares, threshold):
    """将秘密拆成 n_shares 份，任意 threshold 份可恢复"""
    # 随机选 threshold-1 个系数，构造 t-1 次多项式
    coeffs = [secret] + [random.randrange(PRIME) for _ in range(threshold - 1)]
    shares = []
    for i in range(1, n_shares + 1):
        # 在 x=i 处求值：f(i) = a0 + a1*i + a2*i^2 + ...
        y = sum(c * pow(i, k, PRIME) for k, c in enumerate(coeffs)) % PRIME
        shares.append((i, y))
    return shares

def reconstruct(shares, prime=PRIME):
    """拉格朗日插值恢复秘密"""
    def lagrange_basis(j, xs):
        num = den = 1
        for k, xk in enumerate(xs):
            if k != j:
                num = num * (0 - xk) % prime
                den = den * (xs[j] - xk) % prime
        return num * pow(den, -1, prime) % prime

    xs = [s[0] for s in shares]
    return sum(s[1] * lagrange_basis(i, xs) for i, s in enumerate(shares)) % prime

# 示例：将秘密 42 拆成 5 份，任意 3 份可恢复
shares = share_secret(42, 5, 3)
print(f"份额: {shares}")
print(f"用前 3 份恢复: {reconstruct(shares[:3])}")  # 输出 42
```

**加法秘密共享**（Additive Secret Sharing）：更简单，直接把秘密拆成 n 个随机数之和。

```python
def additive_share(secret, n, prime=PRIME):
    """加法秘密共享：s = s1 + s2 + ... + sn mod p"""
    shares = [random.randrange(prime) for _ in range(n - 1)]
    shares.append((secret - sum(shares)) % prime)
    return shares

# 加法份额天然支持加法同态：share(a) + share(b) = share(a+b)
a_shares = additive_share(10, 3)
b_shares = additive_share(20, 3)
sum_shares = [(a + b) % PRIME for a, b in zip(a_shares, b_shares)]
print(f"加法结果: {sum(sum_shares) % PRIME}")  # 输出 30
```

### 2.2 不经意传输（Oblivious Transfer, OT）

OT 是另一个核心原语：发送方有两条消息 m₀ 和 m₁，接收方有一个选择位 b。OT 协议让接收方得到 m_b，而发送方不知道 b 是 0 还是 1，接收方也不知道 m_{1-b}。

OT 在混淆电路（Garbled Circuit）中用于传输输入方的加密标签。2024 年的 SoftSpoken OT 协议将 OT 扩展的通信量降低到接近理论最优。

### 2.3 混淆电路（Garbled Circuits）

Yao 的混淆电路协议将计算函数表示为布尔电路，然后"加密"整个电路：

1. 构造者（Garbler）为每条线的 0/1 各生成一个随机标签
2. 每个门的真值表用标签加密，然后打乱顺序
3. 计算者（Evaluator）拿到加密电路和自己输入对应的标签（通过 OT 获取）
4. 逐门解密得到输出标签，最后查输出映射表得到结果

---

## 3. MPC 协议族

### 3.1 主流协议对比

| 协议 | 年代 | 基础 | 参与方 | 安全模型 | 适合场景 |
|------|------|------|--------|----------|----------|
| Yao GC | 1986 | 混淆电路 | 2 方 | 半诚实 | 布尔计算 |
| GMW | 1987 | OT + 秘密共享 | 多方 | 半诚实/恶意 | 通用布尔/算术 |
| BGW | 1988 | Shamir 共享 | 多方（诚实多数） | 信息论安全 | 算术运算 |
| SPDZ | 2012 | 加法共享 + MAC | 多方（不诚实多数） | 恶意安全 | 算术运算 |
| ABY | 2015 | 混合共享 | 2 方 | 半诚实 | 混合计算 |
| ABY3 | 2018 | 3 方复制共享 | 3 方 | 恶意安全 | ML 训练 |

### 3.2 SPDZ 协议详解

SPDZ（读作"Speedz"）是目前工业界最常用的恶意安全 MPC 协议之一。它的核心思路是把协议分成两个阶段：

**离线阶段**（与输入无关）：预生成大量"Beaver 三元组"（a, b, c 满足 c = a·b）。这些三元组不依赖实际输入，可以提前批量生成。

**在线阶段**（输入相关）：用预生成的三元组辅助乘法运算，每次乘法只需要一轮通信。

```python
# SPDZ 在线阶段的乘法（简化演示）
# 假设 [x], [y] 是 x, y 的加法秘密共享
# 预计算的 Beaver 三元组 [a], [b], [c]，其中 c = a*b

def spdz_multiply(x_share, y_share, a_share, b_share, c_share, prime):
    """SPDZ 乘法：用 Beaver 三元组将乘法化归为加法"""
    # 第 1 步：本地计算 [e] = [x] - [a], [f] = [y] - [b]
    e_share = (x_share - a_share) % prime
    f_share = (y_share - b_share) % prime

    # 第 2 步：广播 e_share, f_share（一轮通信）
    # 重建 e = x - a 和 f = y - b（明文，不泄露 x, y）
    # e = reconstruct(e_shares), f = reconstruct(f_shares)

    # 第 3 步：本地计算 [xy] = [c] + f*[a] + e*[b] + e*f
    # 只有 party 0 加 e*f 项
    # xy_share = c_share + f * a_share + e * b_share  (+ e*f if party_id == 0)
    return  # 每方得到 [xy] 的一个份额
```

### 3.3 ABY 混合计算框架

ABY 的创新在于支持三种共享类型之间的高效转换：

- **A（Arithmetic）共享**：适合加法和线性运算
- **B（Boolean）共享**：适合比较和非线性运算
- **Y（Yao）共享**：适合常数轮复杂布尔运算

根据计算的不同部分选择最优共享类型，比全部用一种共享的方案快 2-10 倍。

---

## 4. 实用 MPC 框架

### 4.1 MP-SPDZ

MP-SPDZ 是当前最全面的 MPC 框架，支持 30+ 种协议变体：

```python
# MP-SPDZ 示例：隐私保护的 IoT 设备平均温度计算
# 文件：iot_avg_temp.mpc

# n_parties 个 IoT 网关各持有一个温度读数
n_parties = 3
temps = [sint.get_input_from(i) for i in range(n_parties)]

# 安全计算平均值
total = sum(temps)
avg = total / n_parties  # 安全除法

# 只公开平均值，不泄露各方原始数据
print_ln("平均温度: %s", avg.reveal())
```

```bash
# 编译并运行
$ python compile.py iot_avg_temp
$ Scripts/spdz2k.sh iot_avg_temp  # 使用 SPDZ2k 协议（整数域）
```

### 4.2 ABY 框架实践

```cpp
// ABY 框架：两方安全比较（哪个传感器读数更大）
// 使用 Yao 共享进行比较运算

#include "abycore/circuit/booleancircuits.h"
#include "abycore/sharing/sharing.h"

void secure_compare(ABYParty* party, uint32_t my_value) {
    auto sharings = party->GetSharings();
    auto yao_circ = (BooleanCircuit*)sharings[S_YAO]->GetCircuitBuildRoutine();

    // 各方输入自己的值
    share* s_a = yao_circ->PutINGate(my_value, 32, SERVER);
    share* s_b = yao_circ->PutINGate(my_value, 32, CLIENT);

    // 安全比较 a > b
    share* s_gt = yao_circ->PutGTGate(s_a, s_b);

    // 输出结果（双方都能看到谁更大，但看不到对方的值）
    share* s_out = yao_circ->PutOUTGate(s_gt, ALL);
    party->ExecCircuit();

    uint32_t result = s_out->get_clear_value<uint32_t>();
    printf("比较结果: %s\n", result ? "我方更大" : "对方更大或相等");
}
```

### 4.3 框架对比

| 框架 | 语言 | 协议数 | 恶意安全 | IoT 适配 | 活跃度 |
|------|------|--------|----------|----------|--------|
| MP-SPDZ | Python DSL | 30+ | 支持 | 中 | 高 |
| ABY/ABY3 | C++ | 3/1 | ABY3 支持 | 中 | 中 |
| CrypTen | Python/PyTorch | 2 | 不支持 | 低 | 高 |
| TF Encrypted | Python/TF | 3 | 部分 | 低 | 低 |
| MOTION | C++ | 5+ | 支持 | 高 | 中 |

---

## 5. IoT 场景中的 MPC 应用

### 5.1 隐私保护聚合

最典型的场景是多个 IoT 节点联合统计，不暴露各自的原始数据。

**案例：智能电网隐私用电统计**

电力公司需要知道一个区域的总用电量来调度发电，但不应该知道每户的具体用电模式（用电模式可以推断出住户的作息、是否在家、甚至宗教信仰）。

```
网关A (户1-100)      网关B (户101-200)      网关C (户201-300)
    [sum_A]               [sum_B]                [sum_C]
       \                    |                     /
        \                   |                    /
         -------- MPC 协议 --------
                     |
              总用电量 (明文)
              各区段用电量 (密文)
```

2024 年 IEEE SmartGridComm 报告显示，基于 SPDZ 的隐私聚合方案在 100 个智能电表规模下，延迟开销约 200ms，相比明文计算增加 15-20 倍，但在 15 分钟采集周期内完全可接受。

### 5.2 联合异常检测

多个工厂的 IoT 系统联合训练异常检测模型，不共享各自的生产数据。

**性能数据**（2024 USENIX Security 论文基准）：

| 操作 | 明文 | 2-PC（半诚实） | 3-PC（恶意） | 开销比 |
|------|------|----------------|--------------|--------|
| 加法（百万次） | 0.01s | 0.03s | 0.08s | 3-8x |
| 乘法（百万次） | 0.01s | 0.5s | 1.2s | 50-120x |
| 比较（百万次） | 0.02s | 2.1s | 4.5s | 100-225x |
| 逻辑回归推理 | 0.001s | 0.15s | 0.4s | 150-400x |

### 5.3 隐私保护机器学习推理

多个 IoT 设备联合进行模型推理：模型拥有方不想暴露模型参数，数据拥有方不想暴露推理输入。

```python
# 使用 CrypTen 进行安全推理（简化示例）
import crypten
import torch

crypten.init()

# 医院持有患者数据，模型公司持有训练好的模型
# 双方都不想暴露自己的输入
@crypten.mpc.run_multiprocess(world_size=2)
def secure_inference():
    # Party 0：加载加密模型
    model = crypten.load("heart_disease_model.pth", src=0)

    # Party 1：加载加密患者数据
    patient_data = crypten.load("patient_features.pt", src=1)

    # 安全推理：模型方看不到数据，数据方看不到模型
    prediction = model(patient_data)

    # 只有 Party 1（医院）能解密看到结果
    result = prediction.get_plain_text(dst=1)
    return result
```

---

## 6. IoT 环境的性能优化

### 6.1 通信优化

通信量是 IoT MPC 的首要瓶颈（低功耗广域网带宽有限）。

| 优化技术 | 原理 | 通信节省 | 适用协议 |
|----------|------|----------|----------|
| OT 扩展 | 用少量真 OT 生成大量伪 OT | 100x | GC, GMW |
| Silent OT | 用 LPN 假设进一步压缩 | 10x vs 传统 OT 扩展 | 所有基于 OT 的 |
| 函数秘密共享 FSS | 将比较/DPF 运算压缩为本地计算 | 去掉在线通信 | 特定函数 |
| 电路层面优化 | 减少乘法门（AND 门）数量 | 依电路而定 | 所有 |

### 6.2 分层 MPC 架构

针对 IoT 的资源异构性，采用分层设计：

```
终端层（MCU/传感器）     边缘层（网关/边缘服务器）     云层
┌─────────────────┐   ┌──────────────────────┐   ┌─────────┐
│ 轻量秘密共享      │   │ 完整 MPC 协议执行      │   │ 离线阶段 │
│ 只做加法共享拆分   │──>│ 在线阶段乘法/比较      │──>│ 预计算   │
│ 加密上报份额      │   │ 处理中等规模电路       │   │ 大规模   │
│ 能耗：< 1mW      │   │ 能耗：< 5W            │   │ Beaver  │
└─────────────────┘   └──────────────────────┘   │ 三元组   │
                                                  └─────────┘
```

### 6.3 与同态加密 / TEE 的对比

| 维度 | MPC | 同态加密 (HE) | TEE |
|------|-----|---------------|-----|
| 信任假设 | 纯密码学 | 纯密码学 | 信任硬件厂商 |
| 计算类型 | 通用 | 通用但缓慢 | 通用且快速 |
| 通信开销 | 高（多轮交互） | 低（单向） | 极低 |
| 计算开销 | 中等 | 极高 | 接近明文 |
| 侧信道风险 | 无 | 无 | 有（Spectre 等） |
| IoT 适合度 | 中（需优化） | 低（太重） | 高（硬件支持时） |
| 组合性 | 好 | 好 | 差 |

实际项目中三者经常组合使用：TEE 做本地计算保护，MPC 做跨设备协作，HE 做单向外包计算。

---

## 7. 实践建议

### 7.1 初学者入门路径

1. **概念理解**：先用加法秘密共享实现一个两方安全加法，跑通端到端流程
2. **框架上手**：安装 MP-SPDZ，运行官方示例程序（均值计算、排序等）
3. **协议选择**：根据参与方数量、安全模型、计算类型选择合适协议
   - 两方半诚实 → Yao GC 或 ABY
   - 三方恶意 → ABY3 或 Replicated
   - 多方恶意 → SPDZ
4. **IoT 适配**：在树莓派上部署 MPC 客户端，测量实际延迟和带宽消耗
5. **进阶阅读**：Evans、Kolesnikov、Rosulek 的教材《A Pragmatic Introduction to MPC》

### 7.2 具体调优建议

**协议选择决策树**：

```
参与方数量？
├── 2 方
│   ├── 主要是布尔运算 → Yao GC
│   ├── 主要是算术运算 → 算术共享
│   └── 混合运算 → ABY
├── 3 方
│   ├── 可信至少 1 方诚实 → ABY3 (Replicated)
│   └── 不可信 → SPDZ (3方)
└── n 方 (n > 3)
    ├── 诚实多数 → BGW / Shamir
    └── 不诚实多数 → SPDZ / MASCOT
```

**IoT 部署清单**：

- 评估通信量：MPC 协议每次乘法需要 1-3 轮通信，LoRaWAN 环境（< 50 kbps）应控制乘法门数量在千级以下
- 预计算分离：将 Beaver 三元组生成放在夜间低峰时段或云端
- 批处理：多个 IoT 采集周期的数据打包执行一次 MPC，摊薄启动开销
- 安全级别：IoT 场景可接受 128 位安全参数，不必追求 256 位
- 容错设计：IoT 设备可能掉线，协议需支持"中途退出不影响已完成计算"

---

## 参考文献

1. Yao, A.C. "How to Generate and Exchange Secrets." FOCS 1986.
2. Goldreich, O., Micali, S., Wigderson, A. "How to Play ANY Mental Game." STOC 1987.
3. Ben-Or, M., Goldwasser, S., Wigderson, A. "Completeness Theorems for Non-Cryptographic Fault-Tolerant Distributed Computation." STOC 1988.
4. Damgård, I. et al. "Multiparty Computation from Somewhat Homomorphic Encryption." CRYPTO 2012. (SPDZ 论文)
5. Demmler, D., Schneider, T., Zohner, M. "ABY – A Framework for Efficient Mixed-Protocol Secure Two-Party Computation." NDSS 2015.
6. Mohassel, P., Rindal, P. "ABY3: A Mixed Protocol Framework for Machine Learning." CCS 2018.
7. Keller, M. "MP-SPDZ: A Versatile Framework for Multi-Party Computation." CCS 2020.
8. Boyle, E. et al. "Silent OT Extension and Its Applications." CRYPTO 2023.
9. Knott, B. et al. "CrypTen: Secure Multi-Party Computation Meets Machine Learning." NeurIPS 2021.
10. Evans, D., Kolesnikov, V., Rosulek, M. "A Pragmatic Introduction to Secure Multi-Party Computation." Foundations and Trends in Privacy and Security, 2018.
