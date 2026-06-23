# 同态加密实用化进展：从理论突破到 IoT 落地

> **难度**：🟡 中级 | **领域**：密码学、隐私计算 | **阅读时间**：约 25 分钟

---

## 日常类比

想象你有一个上锁的手套箱。你把一些零件放进去锁好，然后寄给一个技术精湛的工匠。工匠不需要打开箱子——他通过箱子外面的特殊操作孔，隔着手套对里面的零件进行加工（切割、焊接、组装）。加工完毕后把箱子寄回来，你打开锁一看：里面已经是一个精美的成品了。工匠全程没看到零件的样子，也不知道做出来的是什么。

这就是同态加密（Homomorphic Encryption, HE）的核心思想：**在加密数据上直接计算，得到的加密结果解密后等于对明文计算的结果**。

对 IoT 来说意义重大：传感器数据可以在端侧加密后上传到边缘/云端，云端在密文上执行聚合、统计甚至 AI 推理，全程不解密。即使云端被攻破，攻击者拿到的也只是密文。

---

## 1. 同态加密分类体系

### 1.1 按功能分类

| 类型 | 全称 | 支持操作 | 典型方案 | 实用程度 |
|------|------|----------|----------|----------|
| PHE | 部分同态加密 | 仅加法或仅乘法 | Paillier（加法）、RSA（乘法） | 高，已工业部署 |
| SHE | 有限同态加密 | 加法 + 有限次乘法 | BGV、BFV | 中高 |
| LEVELED HE | 层级同态加密 | 预设深度的加法+乘法 | BGV/BFV（不自举） | 中高 |
| FHE | 全同态加密 | 任意次加法+乘法 | CKKS、TFHE、BGV+自举 | 中（快速进步中） |

核心困难：加密后的数据像"噪声信号"——每次运算都会增大噪声。乘法增噪远快于加法。当噪声超过阈值，解密就会出错。

### 1.2 自举（Bootstrapping）

Gentry 在 2009 年的突破性论文中提出了解决噪声增长的方法——**自举**：在密文上"同态地执行解密运算"，刷新噪声水平。

自举的代价极高：一次自举操作在 2024 年的优化实现上仍需要约 10-50 毫秒（取决于方案和参数），这比一次普通同态乘法慢 100-1000 倍。所以实际应用中，能不自举就不自举——通过设定足够大的初始参数来支撑需要的计算深度。

---

## 2. 三大主流 FHE 方案

### 2.1 BFV 方案（整数运算）

BFV（Brakerski/Fan-Vercauteren）工作在整数上，适合精确计算场景。

```python
# 使用 Microsoft SEAL 的 Python 绑定（tenseal）
import tenseal as ts

# 创建 BFV 上下文：多项式模 degree=8192，密文模数链
context = ts.context(
    ts.SCHEME_TYPE.BFV,
    poly_modulus_degree=8192,
    plain_modulus=1032193,  # 明文模数，决定可表示的整数范围
    coeff_mod_bit_sizes=[60, 40, 40, 60]  # 密文模数链
)
context.generate_galois_keys()  # 用于密文旋转（SIMD）

# 加密两个整数向量（IoT 传感器读数）
sensor_a = ts.bfv_vector(context, [23, 45, 67, 89])  # 温度
sensor_b = ts.bfv_vector(context, [10, 20, 30, 40])  # 湿度

# 在密文上直接运算
encrypted_sum = sensor_a + sensor_b      # 同态加法
encrypted_prod = sensor_a * sensor_b     # 同态乘法

# 解密查看结果
print(f"加法结果: {encrypted_sum.decrypt()}")   # [33, 65, 97, 129]
print(f"乘法结果: {encrypted_prod.decrypt()}")  # [230, 900, 2010, 3560]
```

### 2.2 CKKS 方案（近似实数运算）

CKKS（Cheon-Kim-Kim-Song）支持浮点近似运算，是 AI 推理的首选方案。

```python
import tenseal as ts

# CKKS 上下文
context = ts.context(
    ts.SCHEME_TYPE.CKKS,
    poly_modulus_degree=16384,
    coeff_mod_bit_sizes=[60, 40, 40, 40, 40, 60]
)
context.global_scale = 2**40
context.generate_galois_keys()

# 加密浮点向量（IoT 温度传感器，精度到 0.01°C）
temps = ts.ckks_vector(context, [23.45, 24.12, 22.98, 25.01, 23.67])

# 密文上计算平均温度
enc_sum = temps.sum()           # 同态求和
enc_avg = enc_sum * (1.0 / 5)   # 同态除法（乘以倒数）

# 解密（结果是近似值，CKKS 固有的精度损失约 2^-40）
print(f"平均温度: {enc_avg.decrypt()[0]:.2f}")  # ≈ 23.85

# 密文上的线性回归推理
weights = [0.3, -0.1, 0.5, 0.2, -0.4]  # 模型权重（明文）
bias = 1.5
prediction = temps.dot(weights) + bias   # 同态点积 + 偏置
print(f"预测值: {prediction.decrypt()[0]:.4f}")
```

### 2.3 TFHE 方案（比特级运算）

TFHE（Torus FHE）在比特级别操作，每次运算后自动自举（门级自举），特别适合非线性运算。

| 特性 | BFV | CKKS | TFHE |
|------|-----|------|------|
| 数据类型 | 精确整数 | 近似实数 | 比特/小整数 |
| 打包能力 | 高（SIMD） | 高（SIMD） | 低（逐比特） |
| 乘法深度 | 受限（需参数匹配） | 受限 | 无限（自动自举） |
| 非线性运算 | 困难 | 困难（需多项式近似） | 原生支持 |
| 单次运算速度 | 快（μs 级） | 快（μs 级） | 慢（ms 级/门） |
| 适合场景 | 统计/聚合 | AI 推理/浮点计算 | 比较/控制逻辑 |

---

## 3. 性能基准（2024-2025）

### 3.1 基础运算性能

以下数据基于 Intel Xeon Platinum 8380 (单核) + OpenFHE 1.2 测量：

| 操作 | BFV (N=16384) | CKKS (N=16384) | TFHE |
|------|---------------|----------------|------|
| 密钥生成 | 0.8s | 1.2s | 0.05s |
| 加密 | 2.1ms | 3.5ms | 0.01ms/bit |
| 解密 | 0.8ms | 1.2ms | 0.01ms/bit |
| 同态加法 | 0.05ms | 0.08ms | 0.01ms/gate |
| 同态乘法 | 5.2ms | 8.7ms | — |
| 重线性化 | 3.1ms | 4.5ms | — |
| 门自举 | — | — | 13ms/gate |
| 密文旋转 | 3.8ms | 5.2ms | — |
| CKKS 自举 | — | 45ms | — |

### 3.2 IoT 典型任务性能

| 任务 | 数据规模 | 方案 | 密文大小 | 计算时间 | vs 明文 |
|------|----------|------|----------|----------|---------|
| 均值统计 | 1000 个传感器 | BFV | 512 KB | 12ms | 120x |
| 标准差 | 1000 个传感器 | CKKS | 1 MB | 85ms | 850x |
| 线性回归推理 | 100 维特征 | CKKS | 2 MB | 35ms | 350x |
| 逻辑回归推理 | 100 维特征 | CKKS | 4 MB | 250ms | 2500x |
| 决策树 (深度5) | 32 个特征 | TFHE | 64 KB | 3.2s | 32000x |
| 神经网络 (3层) | 784-128-10 | CKKS | 32 MB | 2.8s | 5600x |

### 3.3 密文膨胀

同态加密的一大痛点是密文比明文大得多：

| 方案 | 明文大小 | 密文大小 | 膨胀率 |
|------|----------|----------|--------|
| BFV (N=4096) | 8 KB | 128 KB | 16x |
| BFV (N=16384) | 32 KB | 512 KB | 16x |
| CKKS (N=16384) | 128 KB (8192 slots × 16B) | 1 MB | 8x |
| TFHE (1 bit) | 1 bit | 2 KB | 16384x |

对带宽受限的 IoT 网络（LoRaWAN 每包 < 242 字节），直接传输密文不可行。解决方案是在边缘网关批量加密后通过有线/5G 上传。

---

## 4. 硬件加速

### 4.1 Intel HEXL

Intel Homomorphic Encryption Acceleration Library（HEXL）利用 AVX-512 指令集加速 NTT（Number Theoretic Transform）等核心运算。

```cpp
// HEXL 加速的 NTT 运算
#include <hexl/hexl.hpp>

intel::hexl::NTT ntt(degree, modulus);
ntt.ComputeForward(result.data(), input.data(), 1, 1);
// AVX-512 加速后 NTT 性能提升 3-8x
```

**加速效果**（N=16384）：

| 运算 | 无 HEXL | 有 HEXL | 加速比 |
|------|---------|---------|--------|
| NTT | 0.32ms | 0.05ms | 6.4x |
| 同态乘法 | 8.7ms | 2.1ms | 4.1x |
| 密钥切换 | 12ms | 3.5ms | 3.4x |

### 4.2 GPU 加速

NVIDIA 在 2024 年发布的 cuFHE 和 100x 项目展示了 GPU 加速 FHE 的潜力：

| 平台 | CKKS 乘法 (N=32768) | TFHE 门自举 |
|------|---------------------|-------------|
| CPU（单核） | 15ms | 13ms |
| CPU（多核 32T） | 2ms | 1.5ms |
| NVIDIA A100 | 0.3ms | 0.15ms |
| NVIDIA H100 | 0.18ms | 0.08ms |

### 4.3 FPGA/ASIC 专用加速器

| 加速器 | 目标方案 | 性能提升 | 功耗 | 状态 |
|--------|----------|----------|------|------|
| Intel HERACLES | BFV/CKKS | 10-30x vs CPU | ~75W | 研究原型 |
| BASALISC (DARPA) | CKKS | 100x vs CPU | ~200W | 研究原型 |
| CraterLake | BFV/CKKS | 1000x vs CPU | ~150W | 论文阶段 |
| Samsung HE-PIM | CKKS | 性能/瓦 50x | <10W | 原型 |

---

## 5. 实用 FHE 库对比

### 5.1 主流库

| 库 | 维护方 | 方案支持 | 语言 | 性能 | 文档 | IoT 适配 |
|----|--------|----------|------|------|------|----------|
| Microsoft SEAL | 微软 | BFV, CKKS | C++ | 高 | 优 | 中 |
| OpenFHE | Duality/NJIT | 全部 | C++ | 最高 | 良 | 中 |
| TFHE-rs | Zama | TFHE | Rust | 高 | 良 | 中 |
| Lattigo | Tune Insight | CKKS, BFV | Go | 中 | 良 | 高 |
| TenSEAL | OpenMined | BFV, CKKS | Python | 中 | 优 | 低 |
| Concrete | Zama | TFHE | Python/Rust | 中 | 优 | 低 |

### 5.2 OpenFHE 示例

```cpp
#include "openfhe.h"
using namespace lbcrypto;

int main() {
    // CKKS 参数设置
    CCParams<CryptoContextCKKSRNS> params;
    params.SetMultiplicativeDepth(3);    // 支持 3 层乘法
    params.SetScalingModSize(50);
    params.SetBatchSize(8);              // SIMD 打包 8 个值

    auto cc = GenCryptoContext(params);
    cc->Enable(PKE); cc->Enable(LEVELEDSHE);

    auto keys = cc->KeyGen();
    cc->EvalMultKeyGen(keys.secretKey);

    // 加密 IoT 传感器数据
    vector<double> sensor_data = {23.5, 24.1, 22.8, 25.0, 23.7, 24.5, 22.9, 24.3};
    auto pt = cc->MakeCKKSPackedPlaintext(sensor_data);
    auto ct = cc->Encrypt(keys.publicKey, pt);

    // 密文上计算：温度标准化 (x - mean) / range
    auto ct_shifted = cc->EvalSub(ct, 23.0);  // 减去基线
    auto ct_scaled = cc->EvalMult(ct_shifted, 1.0 / 5.0);  // 除以范围

    // 解密
    Plaintext result;
    cc->Decrypt(keys.secretKey, ct_scaled, &result);
    result->SetLength(8);
    cout << "标准化结果: " << result << endl;
    return 0;
}
```

---

## 6. IoT 可行的 HE 操作模式

### 6.1 端-边-云分层加密

```
IoT 终端                    边缘网关                     云端
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ 明文采集      │          │ 批量加密      │          │ 密文运算      │
│ ↓            │  明文     │ ↓            │  密文     │ ↓            │
│ 轻量预处理    │ -------> │ HE.Encrypt   │ -------> │ HE.Eval      │
│ (滤波/降采样) │  (短距)   │ ↓            │  (回传)   │ ↓            │
│              │          │ 缓存密文      │ <------- │ 加密结果      │
│              │          │ HE.Decrypt   │          │              │
│              │          │ → 下发控制指令 │          │              │
└──────────────┘          └──────────────┘          └──────────────┘
```

密钥只存在于边缘网关——云端全程接触不到明文，终端不承担加密运算。

### 6.2 实际可行的运算类型

| 运算 | 复杂度 | IoT 可行性 | 典型应用 |
|------|--------|-----------|----------|
| 加法聚合 | 乘法深度 0 | 完全可行 | 区域用电统计 |
| 加权求和 | 乘法深度 1 | 完全可行 | 线性回归推理 |
| 多项式近似 | 乘法深度 3-5 | 可行 | sigmoid/ReLU 近似 |
| 矩阵乘法 | 乘法深度 1-2 | 可行 | 小规模神经网络 |
| 排序/比较 | 乘法深度 10+ | 困难 | 需要 TFHE |
| 完整 DNN | 乘法深度 20+ | 需要自举 | ResNet 级模型 |

---

## 7. 实践建议

### 7.1 初学者入门路径

1. **动手第一步**：安装 TenSEAL（`pip install tenseal`），用 CKKS 加密两个数相加，感受"密文上做加法"的魔力
2. **理解噪声预算**：用 SEAL 的 `noise_budget()` API 观察每次乘法后噪声预算如何减少
3. **选择方案**：
   - 需要精确整数运算 → BFV
   - 需要浮点/AI 推理 → CKKS
   - 需要非线性/比较 → TFHE
4. **SIMD 批处理**：学会利用 CKKS/BFV 的"打包"能力，一次加密处理数千个数据点
5. **性能调参**：多项式模 degree 越大越安全但越慢，找到安全和性能的平衡点

### 7.2 具体调优建议

**参数选择指南**：

| 安全级别 | poly_modulus_degree | 密文大小 | 适合场景 |
|----------|---------------------|----------|----------|
| 128-bit | 4096 | 128 KB | 简单加法聚合 |
| 128-bit | 8192 | 256 KB | 1-2 层乘法 |
| 128-bit | 16384 | 512 KB | 3-5 层乘法 |
| 128-bit | 32768 | 1 MB | 深度计算/自举 |

**IoT 部署注意事项**：

- 密文膨胀是最大障碍：优先使用 SIMD 打包减少有效膨胀率（8192 个 slot 共享 512 KB 密文 → 每个数据点仅 64 字节开销）
- 解密权限管理：私钥绝不能存在云端。使用阈值解密（多方持有密钥碎片）消除单点故障
- 精度需求评估：CKKS 的近似计算会累积误差，IoT 传感器本身精度有限（±0.1°C），10⁻⁷ 级的 CKKS 误差完全可接受
- 计算外包模式：终端只做明文采集，网关做加解密，云端做密文计算——三层分工匹配 IoT 架构
- 与 MPC 互补：HE 适合"一对一外包"（数据方 → 计算方），MPC 适合"多对多协作"（多个数据方联合计算）

---

## 参考文献

1. Gentry, C. "Fully Homomorphic Encryption Using Ideal Lattices." STOC 2009.
2. Brakerski, Z. "Fully Homomorphic Encryption without Modulus Switching." CRYPTO 2012. (BFV 基础)
3. Cheon, J.H. et al. "Homomorphic Encryption for Arithmetic of Approximate Numbers." ASIACRYPT 2017. (CKKS)
4. Chillotti, I. et al. "TFHE: Fast Fully Homomorphic Encryption over the Torus." Journal of Cryptology, 2020.
5. Microsoft SEAL Documentation. https://github.com/microsoft/SEAL, 2024.
6. Al Badawi, A. et al. "OpenFHE: Open-Source Fully Homomorphic Encryption Library." CCS 2022.
7. Bossuat, J. et al. "Efficient Bootstrapping for Approximate Homomorphic Encryption." Eurocrypt 2024.
8. Samardzic, N. et al. "CraterLake: A Hardware Accelerator for Efficient Unbounded Computation on Encrypted Data." ISCA 2022.
9. Kim, S. et al. "HE-PIM: Processing-in-Memory Acceleration for Homomorphic Encryption." IEEE Micro, 2024.
10. Mouchet, C. et al. "Multiparty Homomorphic Encryption from Ring-Learning-with-Errors." PoPETs 2021.
