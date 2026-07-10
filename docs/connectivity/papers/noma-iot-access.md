---
schema_version: '1.0'
id: noma-iot-access
title: NOMA 非正交多址接入技术：让更多设备"同时说话"
layer: 2
content_type: UNKNOWN
difficulty: intermediate
reading_time: 22
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# NOMA 非正交多址接入技术：让更多设备"同时说话"

> **难度**：🟡 中级 | **领域**：多址接入、5G mMTC、物理层技术 | **阅读时间**：约 22 分钟

## 日常类比

在一个教室里，传统的"正交"方式是老师点名回答——每次只有一个学生说话（TDMA），或者每个学生用不同频率的对讲机（FDMA）。这种方式井然有序但效率低：30 个学生，每人只能说 1/30 的时间。

NOMA 的思路像"同时开口但音量不同"。想象两个学生同时回答问题：一个声音大（近处的学生，信号强），一个声音小（远处的学生，信号弱）。老师先听清声音大的回答，在脑中"减去"这个声音，剩下的就是声音小那位的回答。这就是逐次干扰消除（SIC）的原理。

对 IoT 场景（mMTC：海量机器类通信）而言，一个基站可能需要同时服务数万个传感器。如果每个设备都要"排队等话筒"，延迟和信令开销不可接受。NOMA 允许多个设备复用同一资源块，代价是接收端更复杂的解码——但对基站来说这算不了什么。

## 1. 功率域 NOMA 原理

### 1.1 基本模型

考虑下行链路，基站向两个用户（近端用户 U1、远端用户 U2）同时发送：

```
发送信号: x = sqrt(P1)*s1 + sqrt(P2)*s2
其中: P1 + P2 = P_total
      P1 < P2 (远端用户分配更多功率)
```

功率分配原则：信道条件差的用户（远端）分配更多功率，确保其能解码。信道条件好的用户（近端）分配较少功率，但因为信道好，仍能通过 SIC 解码。

### 1.2 SIC 解码过程

近端用户 U1 的接收信号：

```
y1 = h1 * (sqrt(P1)*s1 + sqrt(P2)*s2) + n1
```

U1 解码步骤：
1. 先解码 U2 的信号 s2（因为 P2 > P1，s2 "更响"）
2. 从接收信号中减去 s2 的贡献
3. 从残余信号中解码自己的 s1

远端用户 U2 直接把 U1 的信号当噪声处理（因为 P1 小，干扰有限）。

### 1.3 数学推导

用户 U2 的信干噪比（SINR）：

```
SINR_2 = (|h2|^2 * P2) / (|h2|^2 * P1 + sigma^2)
```

用户 U1 在 SIC 后的 SINR：

```
SINR_1 = (|h1|^2 * P1) / sigma^2  （理想 SIC，完全消除）
```

### 1.4 Python 仿真：2 用户功率域 NOMA

```python
import numpy as np
import matplotlib.pyplot as plt

def simulate_noma_2user(snr_db_range, alpha=0.25):
    """
    2 用户下行 NOMA 仿真
    alpha: 近端用户功率比例 (P1/P_total), 远端 = 1-alpha
    """
    results = {"noma_u1": [], "noma_u2": [], "oma_u1": [], "oma_u2": []}

    for snr_db in snr_db_range:
        snr_linear = 10 ** (snr_db / 10)

        # 信道增益: U1(近端)=2, U2(远端)=0.5 (归一化)
        h1_sq = 2.0  # 近端用户信道增益
        h2_sq = 0.5  # 远端用户信道增益
        P_total = snr_linear  # 归一化噪声功率=1

        # NOMA 容量
        P1 = alpha * P_total
        P2 = (1 - alpha) * P_total

        # U2: 将 U1 信号视为噪声
        sinr_u2 = (h2_sq * P2) / (h2_sq * P1 + 1)
        rate_u2_noma = np.log2(1 + sinr_u2)

        # U1: SIC 后无干扰 (理想 SIC)
        sinr_u1 = h1_sq * P1  # 噪声功率=1
        rate_u1_noma = np.log2(1 + sinr_u1)

        # OMA (OFDMA): 各分一半带宽
        rate_u1_oma = 0.5 * np.log2(1 + h1_sq * P_total)
        rate_u2_oma = 0.5 * np.log2(1 + h2_sq * P_total)

        results["noma_u1"].append(rate_u1_noma)
        results["noma_u2"].append(rate_u2_noma)
        results["oma_u1"].append(rate_u1_oma)
        results["oma_u2"].append(rate_u2_oma)

    return results

# 运行仿真
snr_range = np.arange(0, 30, 1)
res = simulate_noma_2user(snr_range, alpha=0.25)

# 总和速率对比
noma_sum = np.array(res["noma_u1"]) + np.array(res["noma_u2"])
oma_sum = np.array(res["oma_u1"]) + np.array(res["oma_u2"])

print(f"SNR=20dB 时:")
print(f"  NOMA 总和速率: {noma_sum[20]:.2f} bps/Hz")
print(f"  OMA  总和速率: {oma_sum[20]:.2f} bps/Hz")
print(f"  NOMA 增益: {(noma_sum[20]/oma_sum[20]-1)*100:.1f}%")
# 典型输出: NOMA 增益约 15-25%
```

## 2. NOMA vs OMA 对比

### 2.1 多址技术演进

| 代际 | 技术 | 类型 | 正交性 |
|------|------|------|--------|
| 1G | FDMA | 频分 | 正交 |
| 2G | TDMA/FDMA | 时频分 | 正交 |
| 3G | CDMA | 码分 | 准正交 |
| 4G | OFDMA | 频分(子载波) | 正交 |
| 5G (初期) | OFDMA + NOMA | 混合 | 非正交 |
| 5G-A/6G | Grant-free NOMA | 免调度 | 非正交 |

### 2.2 详细性能对比

| 维度 | OMA (OFDMA) | 功率域 NOMA |
|------|-------------|-------------|
| 频谱效率 | 基准 | +15-30% (2用户) |
| 用户公平性 | 较好（资源均分） | 需功率分配优化 |
| 接收复杂度 | 低（单用户解码） | 高（SIC 多次解码） |
| 信令开销 | 高（调度 grant） | 可免调度 |
| 对 CSI 要求 | 中 | 高（需精确功率分配） |
| mMTC 接入延迟 | 高（排队等调度） | 低（免 grant） |
| 错误传播 | 无 | SIC 解码失败会传播 |

### 2.3 NOMA 的容量优势——信息论视角

在广播信道（下行）中，NOMA 实际上就是超位编码（Superposition Coding），在信息论中已被证明是达到容量域边界的最优策略。OMA 只能达到容量域的一个子集。

对于上行多址信道（MAC），NOMA + SIC 同样可达到容量域的所有角点（corner points），通过时间共享可达到整个容量域。

## 3. 免调度 NOMA（Grant-Free NOMA for mMTC）

### 3.1 传统调度 vs 免调度

传统 LTE/NR 接入流程：

```
设备 --[Preamble]--> 基站 --[RAR]--> 设备 --[RRC Request]--> 基站 --[Grant]--> 设备 --[数据]-->
总延迟: 10-50 ms, 信令开销: 数百 bit
```

Grant-Free NOMA：

```
设备 --[Preamble + 数据 (预配置资源)]--> 基站 --[ACK]-->
总延迟: 1-5 ms, 信令开销: 极少
```

### 3.2 关键技术要素

| 要素 | 作用 | 典型方案 |
|------|------|----------|
| 导频设计 | 设备活跃检测 | 非正交导频序列 |
| 扩频码 | 区分复用用户 | SCMA codebook, MUSA 序列 |
| 活跃检测 | 识别哪些设备在发 | 压缩感知 (CS) |
| 信道估计 | 获取各用户 CSI | 联合检测 |
| 多用户检测 | 分离叠加信号 | SIC / MPA / EP |

### 3.3 SCMA（稀疏码多址）

SCMA 是华为提出的免调度 NOMA 方案：

```
6 个用户复用 4 个 OFDM 子载波 (过载率 150%)

用户-子载波映射 (因子图):
        子载波 1  子载波 2  子载波 3  子载波 4
用户 1:    x                    x
用户 2:    x         x
用户 3:              x                    x
用户 4:    x                              x
用户 5:              x         x
用户 6:                        x          x

每个用户只在 2 个子载波上发送 (稀疏)
每个子载波被 3 个用户复用
解码: 消息传递算法 (MPA) 在因子图上迭代
```

```python
import numpy as np

def scma_factor_graph():
    """SCMA 因子图定义 (6用户, 4资源)"""
    # F[j][k] = 1 表示用户 j 使用资源 k
    F = np.array([
        [1, 0, 1, 0],  # User 1
        [1, 1, 0, 0],  # User 2
        [0, 1, 0, 1],  # User 3
        [1, 0, 0, 1],  # User 4
        [0, 1, 1, 0],  # User 5
        [0, 0, 1, 1],  # User 6
    ])
    overload = F.shape[0] / F.shape[1]
    print(f"用户数: {F.shape[0]}, 资源数: {F.shape[1]}")
    print(f"过载率: {overload*100:.0f}%")
    print(f"每用户使用资源数: {F.sum(axis=1)[0]}")
    print(f"每资源复用用户数: {F.sum(axis=0)[0]}")
    return F

F = scma_factor_graph()
# 输出: 用户数: 6, 资源数: 4, 过载率: 150%
```

## 4. NOMA + MIMO

### 4.1 MIMO-NOMA 基本思想

在 MIMO 系统中，波束赋形可以在空间维度上分离用户。MIMO-NOMA 的思想是：同一波束方向内的用户用功率域 NOMA 复用，不同波束方向的用户用空间域分离。

```
       波束 1 方向              波束 2 方向
    ┌───────────┐           ┌───────────┐
    │ U1(近) ───────┐       │ U3(近) ───────┐
    │ U2(远) ───┐   │       │ U4(远) ───┐   │
    └───────────┘   │       └───────────┘   │
                    ▼                        ▼
    功率域 NOMA     空间域隔离      功率域 NOMA
    (同波束内)     (波束间)        (同波束内)
```

### 4.2 用户分簇策略

如何将用户分到同一 NOMA 组（cluster）是关键问题：

| 策略 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 信道增益差异最大化 | 配对信道好/差用户 | SIC 性能好 | 公平性差 |
| 信道相关性 | 相关性高的配对 | 波束赋形增益 | 需 CSI 反馈 |
| 随机配对 | 简单随机分组 | 开销低 | 性能不稳定 |
| 基于 QoS | 按业务需求配对 | 满足差异化需求 | 算法复杂 |

### 4.3 大规模 MIMO + NOMA

在 64/128 天线 Massive MIMO 系统中，波束分辨率极高。研究表明当天线数 M 远大于用户数 K 时，NOMA 相比 OMA 的增益递减。但在过载场景（K > M）下，NOMA 仍是关键使能技术。

## 5. 中断概率分析

### 5.1 中断概率定义

中断概率 = 实际可达速率低于目标速率的概率：

```
P_out = Pr(log2(1 + SINR) < R_target)
     = Pr(SINR < 2^R_target - 1)
```

### 5.2 瑞利衰落下的闭合解

假设信道服从瑞利衰落（|h|^2 ~ Exponential(1/lambda)），2 用户下行 NOMA：

远端用户 U2 的中断概率：

```
P_out_2 = 1 - exp(-gamma_th2 / (lambda2 * (alpha2 - alpha1*gamma_th2) * rho))
条件: alpha2 > alpha1 * gamma_th2 (否则 P_out_2 = 1)
其中: gamma_th2 = 2^R2 - 1, rho = P/sigma^2
```

近端用户 U1（需先成功解码 U2）：

```
P_out_1 = 1 - exp(-max(gamma_th2/(lambda1*(alpha2-alpha1*gamma_th2)), gamma_th1/(lambda1*alpha1)) / rho)
```

```python
import numpy as np

def noma_outage_probability(snr_db, alpha1, alpha2, R1, R2, lambda1=2.0, lambda2=0.5):
    """
    计算 2 用户下行 NOMA 中断概率 (瑞利衰落)
    alpha1: 近端用户功率比例
    alpha2: 远端用户功率比例 (alpha1 + alpha2 = 1)
    R1, R2: 目标速率 (bps/Hz)
    lambda1, lambda2: 信道均值 (近端 > 远端)
    """
    rho = 10 ** (snr_db / 10)
    gamma1 = 2**R1 - 1  # 近端用户 SINR 门限
    gamma2 = 2**R2 - 1  # 远端用户 SINR 门限

    # 远端用户中断概率
    denom = alpha2 - alpha1 * gamma2
    if denom <= 0:
        p_out_2 = 1.0
    else:
        p_out_2 = 1 - np.exp(-gamma2 / (lambda2 * denom * rho))

    # 近端用户中断概率 (需先解 U2 再解 U1)
    if denom <= 0:
        p_out_1 = 1.0
    else:
        threshold = max(gamma2 / (lambda1 * denom), gamma1 / (lambda1 * alpha1))
        p_out_1 = 1 - np.exp(-threshold / rho)

    return p_out_1, p_out_2

# 计算不同 SNR 下的中断概率
snr_range = np.arange(0, 40, 1)
p1_list, p2_list = [], []
for snr in snr_range:
    p1, p2 = noma_outage_probability(snr, alpha1=0.2, alpha2=0.8, R1=2, R2=0.5)
    p1_list.append(p1)
    p2_list.append(p2)

# 找到 P_out = 1e-3 时所需 SNR
for i, snr in enumerate(snr_range):
    if p2_list[i] < 1e-3:
        print(f"远端用户达到 P_out=1e-3 需要 SNR >= {snr} dB")
        break
```

## 6. 3GPP MUST 与实际部署

### 6.1 3GPP 中的 NOMA 研究

| 3GPP 项目 | 版本 | 内容 |
|-----------|------|------|
| MUST (多用户叠加传输) | R13 SI | 下行 NOMA 研究项目 |
| NOMA Study Item | R15 SI | 上行免调度 NOMA 评估 |
| R16 NR | R16 | 未纳入标准（复杂度争议） |
| R18 Study | R18 | mMTC 场景重新评估 |

### 6.2 MUST 方案分类

3GPP 评估了三类 MUST 方案：

- **Category 1**: 自适应功率比 + Gray 映射，兼容 LTE UE
- **Category 2**: 自适应功率比 + 非 Gray 映射
- **Category 3**: 叠加编码 + 联合星座优化

最终结论：在小区边缘用户受限场景下，MUST 可带来 5-15% 吞吐量增益，但需要近端 UE 支持 SIC，增加了终端复杂度。

### 6.3 实际部署挑战

| 挑战 | 详细说明 | 缓解方案 |
|------|----------|----------|
| SIC 错误传播 | 第一层解码错误会传播到后续层 | CRC 辅助 + 重传 |
| CSI 不精确 | 功率分配依赖精确 CSI | 鲁棒功率分配设计 |
| 用户配对开销 | 需要频繁重新配对 | 半静态配对 + ML 预测 |
| 标准化阻力 | 终端复杂度增加 | 仅基站侧实现（上行 NOMA） |
| 公平性问题 | 近端用户承担 SIC 负担 | 动态角色轮换 |

## 7. 实践建议

### 7.1 初学者入门路径

1. 理论准备（1 周）：信息论基础（容量域、叠加编码）、检测理论（MAP/ML 检测）
2. 仿真入门（2 周）：用 Python/MATLAB 实现 2 用户 NOMA BER 仿真，对比 OMA
3. 进阶仿真（2 周）：加入瑞利衰落、不完美 SIC、多用户场景
4. 论文阅读：从 Ding et al. (2017) "A Survey on NOMA" 开始
5. 系统级仿真：在 ns-3 或 5G-LENA 中评估 NOMA 在 mMTC 场景的性能

### 7.2 具体调优建议

功率分配是 NOMA 性能的关键。固定功率分配（如 0.8/0.2）简单但非最优。分数阶发射功率分配（FTPA）根据信道增益动态调整：alpha_k 正比于 (|h_k|^2)^(-s)，其中 s 是衰减因子。认知无线电启发的功率分配确保远端用户先满足 QoS，剩余功率给近端用户。

SIC 接收机设计方面，实际 SIC 存在 1-5% 的残余干扰。建议在仿真中加入不完美 SIC 因子 epsilon（典型值 0.01-0.05）。软 SIC（使用 LLR 而非硬判决）比硬 SIC 性能好 1-2 dB。多用户场景建议 SIC 层数不超过 3-4 层，否则错误传播严重。

IoT 场景特别考量方面，mMTC 设备通常发送短包（20-100 bytes），香农容量公式不再精确，需用有限块长度（FBL）理论评估。Grant-free NOMA 的活跃用户检测是关键瓶颈——压缩感知算法（如 AMP）可在 5% 活跃率下实现 99% 检测准确率。

## 参考文献

1. Ding, Z., et al., "A Survey on Non-Orthogonal Multiple Access for 5G Networks," IEEE JSAC, vol. 35, no. 10, 2017.
2. 3GPP TR 36.859, "Study on Downlink Multiuser Superposition Transmission," v13.0.0, 2016.
3. Liu, Y., et al., "Nonorthogonal Multiple Access for 5G and Beyond," Proceedings of the IEEE, vol. 105, no. 12, 2017.
4. Dai, L., et al., "Non-Orthogonal Multiple Access for 5G: Solutions, Challenges, Opportunities, and Future Research Trends," IEEE COMST, vol. 20, no. 3, 2018.
5. Nikopour, H. and Baligh, H., "Sparse Code Multiple Access," IEEE PIMRC, 2013.
6. Ding, Z., et al., "Application of NOMA in 6G Networks: Future Vision and Research Opportunities," IEEE Network, vol. 38, 2024.
7. Wei, Z., et al., "Multi-User NOMA with Imperfect SIC: Outage Analysis," IEEE TVT, vol. 72, 2023.
8. Yuan, Y., et al., "NOMA for Next-Generation Massive IoT: Performance Analysis with FBL Codes," IEEE IoT Journal, vol. 11, 2024.
9. 3GPP TR 38.812, "Study on Non-Orthogonal Multiple Access (NOMA) for NR," v16.0.0, 2018.
10. Vaezi, M., et al., "NOMA: An Information-Theoretic Perspective," Springer, 2024.
