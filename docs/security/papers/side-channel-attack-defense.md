---
schema_version: '1.0'
id: side-channel-attack-defense
title: 侧信道攻击与防护
layer: 6
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - secure-boot-root-of-trust
  - puf-device-authentication
tags:
- 侧信道
- DPA
- CPA
- 掩码
- ChipWhisperer
- 硬件安全
- 常量时间
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 侧信道攻击与防护

> **难度**：🟡 中级 | **领域**：硬件安全、密码工程 | **关键词**：SPA, DPA, CPA, 掩码, TVLA | **阅读时间**：约 22 分钟

## 日常类比

猜保险箱密码时，暴力试组合很慢；若转动到正确数字会发出细微"咔嗒"声，听声就能逐位缩小范围。侧信道攻击（Side-Channel Attack, SCA）同理：不硬攻加密算法的数学结构，而观察设备运行时的副产品——功耗、执行时间、电磁辐射——来推断密钥。对物联网（Internet of Things, IoT）设备尤其危险，因为攻击者常能物理接触设备。

## 摘要

本文梳理功耗分析、时序攻击与电磁分析的机制，对比掩码（Masking）、隐藏（Hiding）与常量时间编程等对策，并以 ChipWhisperer 与测试向量泄露评估（Test Vector Leakage Assessment, TVLA）说明工程评估路径。文中轨迹数、成功率与价格为文献/厂商量级，部署须以自有平台实测为准。

## 1. 侧信道攻击分类

### 1.1 攻击类型总览

| 攻击类型 | 观测对象 | 设备要求 | 难度 | IoT 威胁 |
|---------|---------|---------|------|---------|
| 时序攻击 | 执行时间 | 网络可达即可 | 低 | 高 |
| 简单功耗分析（Simple Power Analysis, SPA） | 功耗波形 | 示波器 | 中 | 高 |
| 差分功耗分析（Differential Power Analysis, DPA） | 功耗统计 | 示波器+采集 | 中高 | 高 |
| 相关功耗分析（Correlation Power Analysis, CPA） | 功耗相关性 | 同 DPA | 高 | 高 |
| 电磁分析（Electromagnetic Analysis, EMA） | EM 辐射 | 近场探头 | 中高 | 中 |
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
                   │ 泄露信息（功耗/时间/EM）
                   ↓
            ┌─────────────┐
            │  攻击者分析  │ → 恢复密钥 K
            └─────────────┘
```

## 2. 功耗分析攻击

### 2.1 简单功耗分析（SPA）

SPA 用单条或少量功耗轨迹直接观察密码操作模式。RSA 的"平方-乘"中，密钥位为 1 时多做乘法（功耗更高），为 0 时只做平方；波形上可见 S / SM 模式差异[1][7]。

### 2.2 差分/相关功耗分析（DPA / CPA）

DPA 用统计方法从大量轨迹提取密钥信息[1]；CPA 引入汉明重量等泄露模型，用相关系数选密钥猜测[2]。典型流程：对密钥字节穷举 → 假设中间值 → 功耗模型 → 与实测轨迹相关 → 取峰值对应猜测。

```python
# CPA/DPA 攻击 AES 第一轮的示意（非完整可运行 PoC）
import numpy as np

def cpa_guess_key_byte(traces, plaintexts, byte_index, sbox):
    """traces: N×T；plaintexts: N×16；返回最佳密钥字节猜测"""
    best_corr, best_key = 0.0, 0
    for key_guess in range(256):
        hyp = np.array([
            bin(sbox[plaintexts[i][byte_index] ^ key_guess]).count("1")
            for i in range(len(traces))
        ])
        for t in range(traces.shape[1]):
            corr = abs(np.corrcoef(hyp, traces[:, t])[0, 1])
            if corr > best_corr:
                best_corr, best_key = corr, key_guess
    return best_key, best_corr
```

### 2.3 所需轨迹数量（量级，非保证）

公开实验中，无防护高级加密标准（Advanced Encryption Standard, AES）常在数百条量级轨迹下被 CPA 攻破；一阶掩码常把需求抬到数万级；更高阶掩码则可达百万级量级，且成功率随噪声与实现质量变化[2][5][7]。下表为教学量级，勿当作产品安全证明。

| 目标算法 | 攻击方法 | 轨迹数量级 | 说明 |
|---------|---------|-----------|------|
| AES-128（无防护） | CPA | 数十–数百 | 实验室常见 |
| AES-128（1 阶掩码） | 2 阶 DPA | 万–十万 | 依赖实现质量 |
| AES-128（2 阶掩码） | 3 阶 DPA | 百万级 | 成本陡增 |
| RSA-2048（无防护平方-乘） | SPA | 极少 | 模式可见即可 |

## 3. 时序攻击

不同输入走不同路径会产生可测时间差。早期返回的字节比较可被逐字节猜测；网络侧即使有抖动，多次取中位数仍可能放大微秒级差异[6]。

```c
// 有漏洞：首个不匹配即返回
int insecure_compare(const uint8_t *a, const uint8_t *b, size_t len) {
    for (size_t i = 0; i < len; i++)
        if (a[i] != b[i]) return 0;
    return 1;
}

// 常量时间：始终扫完全部字节
int secure_compare(const uint8_t *a, const uint8_t *b, size_t len) {
    volatile uint8_t result = 0;
    for (size_t i = 0; i < len; i++)
        result |= a[i] ^ b[i];
    return (result == 0) ? 1 : 0;
}
```

## 4. 电磁辐射分析

| 特性 | 近场探测 | 远场探测 |
|------|---------|---------|
| 距离 | 厘米级 | 可达数米 |
| 分辨率 | 可定位模块 | 整体信号 |
| 设备 | 近场探头 + 示波器 | 天线 + 软件定义无线电（Software Defined Radio, SDR） |
| 信噪比 | 相对较高 | 相对较低 |
| 实用性 | 实验室常见 | 条件苛刻 |

相对功耗分析，EMA 可不改电路、可空间定位，且在存在简单功耗滤波时仍可能有效[7]。

## 5. 防护对策

### 5.1 掩码（Masking）

将敏感中间值与随机掩码混合，使瞬时功耗与密钥统计无关；高阶掩码可对抗高阶 DPA，但开销近似随阶数上升[5][10]。

### 5.2 隐藏（Hiding）

随机延迟、洗牌执行顺序、噪声注入等降低信噪比；单独使用通常弱于良好掩码，常作叠加层。

### 5.3 常量时间与硬件对策

| 对策 | 原理 | 开销量级 | 效果倾向 |
|------|------|---------|---------|
| 常量时间编程 | 消除数据依赖分支/访存 | 低–中 | 防时序/部分缓存 |
| 双轨逻辑 | 互补信号抵消功耗差 | 面积约翻倍 | 强 |
| 随机时钟 / 噪声源 | 打乱时间轴或抬噪声 | 低–中 | 中 |
| 金属屏蔽 | 抑制 EM 耦合 | 低 | 中 |
| 安全元件外置密码 | 密钥不出芯片 | 物料成本 | 高（依赖 SE 质量） |

## 6. ChipWhisperer 与 TVLA

ChipWhisperer 是开源侧信道采集/分析平台，适合教学与自评估[3][8]。厂商标称采样率与套件价格随型号变化（入门到专业跨数量级），采购以当期报价为准。

TVLA 用 Welch t 检验比较固定输入与随机输入轨迹；常用阈值约 |t|>4.5 作为"存在泄露迹象"的启发式，**不是**形式化安全证明[4]。

```python
def tvla_leaky_points(traces_fixed, traces_random, threshold=4.5):
    n1, n2 = len(traces_fixed), len(traces_random)
    mean1, mean2 = traces_fixed.mean(0), traces_random.mean(0)
    var1, var2 = traces_fixed.var(0), traces_random.var(0)
    t_stat = (mean1 - mean2) / np.sqrt(var1 / n1 + var2 / n2)
    return t_stat, np.where(np.abs(t_stat) > threshold)[0]
```

## 7. 实践优先级（IoT）

1. 常量时间比较与密钥处理（成本低，先堵住时序洞）。
2. 一阶布尔掩码 + 真随机源（对抗常见 DPA/CPA）。
3. 洗牌/随机延迟作叠加。
4. 高价值密钥放入经评估的安全元件（Secure Element, SE）。
5. 用 TVLA/自建 CPA 回归，防止编译器优化毁掉常量时间。

## 8. 局限、挑战与可改进方向

### 1. 实验室轨迹数 ≠ 现场可攻击性

**局限**：公开数字多在理想探头、同步触发、低噪声板上测得；量产外壳、去耦与时钟抖动会显著改变所需轨迹数。
**改进**：按威胁模型定义攻击者能力（接触距离、设备预算）；在量产样机上做 CPA/TVLA，而不是只测开发板。

### 2. 掩码实现易被毛刺与编译器破坏

**局限**：一阶掩码若存在毛刺（glitch）或中间值短暂去掩码，仍可能泄露；优化器可能重写"常量时间"代码。
**改进**：对照汇编；对关键路径做形式化/工具辅助检查；掩码刷新与随机源健康监测纳入发布门禁。

### 3. 只护加密、不护密钥装载与更新

**局限**：攻击者可在密钥从闪存/总线载入时采集；OTA 更新路径若明文处理密钥材料则前功尽弃。
**改进**：密钥仅在 SE/TEE 内使用；装载与派生路径纳入侧信道范围；与安全启动、安全供应流程联测。

### 4. 评估方法被误当成认证

**局限**：TVLA 通过不等于抗实际 CPA；反之失败也不自动等于可恢复完整密钥。
**改进**：分层证据：TVLA 作回归哨兵 + 针对性 CPA/模板攻击 +（高保证场景）第三方实验室评估。

## 参考文献

[1] P. Kocher, J. Jaffe, and B. Jun, "Differential Power Analysis," CRYPTO, 1999.
[2] E. Brier, C. Clavier, and F. Olivier, "Correlation Power Analysis with a Leakage Model," CHES, 2004.
[3] C. O'Flynn and Z. Chen, "ChipWhisperer: An Open-Source Platform for Hardware Embedded Security Research," COSADE, 2014.
[4] T. Schneider and A. Moradi, "Leakage Assessment Methodology," CHES, 2015.
[5] M. Rivain and E. Prouff, "Provably Secure Higher-Order Masking of AES," CHES, 2010.
[6] D. J. Bernstein, "Cache-Timing Attacks on AES," 2005.
[7] S. Mangard, E. Oswald, and T. Popp, *Power Analysis Attacks: Revealing the Secrets of Smart Cards*, Springer, 2007.
[8] NewAE Technology, "ChipWhisperer Documentation," 2024.
[9] O. Reparaz et al., "Masking vs. Multiparty Computation," TCHES, 2024.
[10] S. Chari, C. S. Jutla, J. R. Rao, and P. Rohatgi, "Towards Sound Approaches to Counteract Power-Analysis Attacks," CRYPTO, 1999.
[11] ISO/IEC 17825, "Testing methods for the mitigation of non-invasive attack classes against cryptographic modules," 相关版本.
[12] NIST, "FIPS 140-3 / related side-channel guidance for cryptographic modules," 近年修订材料.
