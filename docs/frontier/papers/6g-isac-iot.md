---
schema_version: '1.0'
id: 6g-isac-iot
title: 6G 通感一体化（ISAC）与 IoT
layer: 8
content_type: technical_analysis
difficulty: advanced
reading_time: 30
prerequisites:
  - ris-intelligent-surface
tags:
- ISAC
- 通感一体化
- 6G
- OFDM
- RIS
- 感知通信
- IoT
- 波形设计
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 6G 通感一体化（ISAC）与 IoT

> **难度**：🟠 进阶 | **领域**：6G 通信 × 感知 | **阅读时间**：约 30 分钟

## 一句话总结

通感一体化（Integrated Sensing and Communication, ISAC）让同一套无线信号既能传数据又能"看世界"，是 6G 时代 IoT 感知能力的核心底座。

## 从"各干各的"到"一心二用"

### 日常类比

想象你在黑暗的房间里，手里有一个手电筒。传统做法是：用手电筒照路（通信），然后再换一个雷达扫描周围环境（感知）——两套设备、两种信号、两段时间。

ISAC 的思路是：让手电筒的光既能照亮前方（通信），同时根据光的反射判断周围物体的位置和形状（感知）。一束光，两个用途。

### 技术背景

在 5G 及之前的系统中，通信和雷达感知是完全独立的系统：

| 维度 | 传统通信 | 传统雷达 | ISAC |
|------|---------|---------|------|
| 目的 | 传输信息 | 探测目标 | 同时完成两者 |
| 频段 | Sub-6GHz / mmWave | 专用雷达频段 | 共享频段 |
| 波形 | OFDM / SC-FDMA | 线性调频脉冲 | 统一波形设计 |
| 硬件 | 基站天线 | 雷达天线阵 | 共用天线阵列 |
| 频谱效率 | 仅通信 | 仅感知 | 两者复用 |
| 成本 | 分开部署 | 分开部署 | 一套系统 |

ISAC 的核心价值在于**频谱共享**和**硬件复用**，在频谱日益稀缺的 6G 时代尤为关键。

## ISAC 的三种融合层级

### Level 1：共存（Coexistence）

通信和感知使用相同频段但相互独立，通过干扰管理避免冲突。类似于两个人在同一个房间各做各的事，但约定不要互相打扰。

### Level 2：协作（Cooperation）

通信和感知系统共享信息辅助对方。通信系统利用感知信息优化波束方向；感知系统利用通信链路传输感知结果。

### Level 3：深度一体化（Deep Integration）

同一个信号同时承载通信数据和感知功能，硬件完全共用。这是 ISAC 的终极形态，也是当前研究的主要方向。

从工程落地看，Level 1→2→3 并非一次性跃迁：运营商往往先在现网做共存干扰协调，再引入感知结果回传与波束辅助，最后才在波形与射频前端上做深度一体化。每一级都对应不同的标准化成熟度与硬件改造成本。

## 波形设计：ISAC 的核心技术

### OFDM-based ISAC

OFDM（Orthogonal Frequency Division Multiplexing，正交频分复用）是 4G/5G 的核心波形，天然适合扩展为 ISAC 波形：

**通信角度**：子载波正交，抗多径干扰，频谱效率高
**感知角度**：通过分析接收回波的时延和多普勒频移，可估计目标距离和速度

```
OFDM ISAC 信号结构：
├── 数据子载波：承载通信数据
├── 导频子载波：辅助信道估计 + 感知参考
└── 保护间隔（CP）：吸收多径 + 提供感知模糊度
```

距离分辨率：Δr = c / (2B)，其中 B 为带宽
速度分辨率：Δv = c / (2f_c · T_frame)，其中 T_frame 为帧长

感知处理链路通常为：匹配滤波/相关 → 距离-多普勒二维 FFT → CFAR（Constant False Alarm Rate，恒虚警率）检测 → 多目标关联跟踪。通信侧仍按常规信道估计与解调进行；关键在于导频与数据子载波的功率、密度如何在通感之间分配——这直接决定 Pareto 折中曲线的位置。

### ISAC 专用波形设计

| 波形方案 | 通信性能 | 感知性能 | 复杂度 | 适用场景 |
|---------|---------|---------|--------|---------|
| OFDM-ISAC | ★★★★☆ | ★★★☆☆ | 低 | 通用室内/城市 |
| OTFS | ★★★☆☆ | ★★★★★ | 高 | 高速移动 |
| FMCW-comm | ★★☆☆☆ | ★★★★★ | 中 | 车载雷达通信 |
| OCDM | ★★★★☆ | ★★★★☆ | 中 | 水下/恶劣信道 |
| Pulsed-OFDM | ★★★☆☆ | ★★★★☆ | 中 | 远距离感知 |

**OTFS（Orthogonal Time Frequency Space，正交时频空间）**在时延-多普勒域调制信号，特别适合高速场景（如车联网），但实现复杂度较高。**FMCW**（Frequency Modulated Continuous Wave，调频连续波）源自车载雷达，通信扩展能力有限；**OCDM**（Orthogonal Chirp Division Multiplexing，正交啁啾分复用）在恶劣信道下鲁棒性较好。

## RIS 辅助的 ISAC

### 为什么 RIS + ISAC 是"天作之合"

RIS（Reconfigurable Intelligent Surface，可重构智能超表面）可以智能调控无线信号的反射方向。在 ISAC 场景中，RIS 带来独特优势：

1. **扩展覆盖**：将 ISAC 信号反射到非视距（Non-Line-of-Sight, NLoS）区域
2. **增强感知**：创造额外的感知路径，提高目标检测概率
3. **通感解耦**：通过不同反射方向同时服务通信用户和感知目标
4. **波束赋形增益**：被动反射增强信号强度，无需额外有源发射功耗

### RIS-ISAC 系统模型

```
        通信用户
         ↑
    直射路径 + RIS反射路径
         |
基站 ──→ RIS面板 ──→ 感知目标
 ↑        (N个元素)        ↓
 └───── 回波接收 ──────────┘
```

基站发射 ISAC 信号，同时：
- 直射路径服务通信用户
- RIS 反射路径照射感知目标
- 目标回波被基站接收，提取感知信息

### 联合优化问题

RIS-ISAC 的核心优化问题：

**目标**：最大化感知信噪比（或最小化 CRB，Cramér-Rao Bound，克拉美-罗下界）
**约束**：通信 SINR（Signal-to-Interference-plus-Noise Ratio，信干噪比）≥ 阈值；RIS 相位 ∈ [0, 2π)；发射功率 ≤ P_max

这是一个非凸优化问题，常用求解方法：
- 交替优化（Alternating Optimization, AO）：交替优化基站波束和 RIS 相位
- 半正定松弛（Semidefinite Relaxation, SDR）
- 深度学习端到端优化

## IoT 感知应用场景

### 场景 1：智能交通

- **车辆检测与跟踪**：基站同时为车辆提供通信服务和感知周围车辆位置
- **行人检测**：毫米波（mmWave）ISAC 在十字路口检测行人，据公开资料端到端时延可做到约数十毫秒量级（具体取决于帧结构与处理链路）
- **交通流量估计**：通过多普勒谱分析车流密度

### 场景 2：室内定位与活动识别

- **WiFi 感知**：利用 WiFi 信号（本质是 OFDM 通信信号）实现手势识别、跌倒检测
- **精度对比**：据公开资料与实验报道，ISAC/通感定位精度可达约亚米级（约 0.1–0.5 m），通常优于纯 WiFi RSSI（Received Signal Strength Indicator，接收信号强度指示，约 2–5 m）

### 场景 3：工业 IoT

- **设备状态监测**：5G 基站在提供数据回传的同时，通过回波分析设备振动
- **入侵检测**：利用 ISAC 信号的环境变化检测非授权进入

### 场景 4：无人机网络

- **避障 + 通信**：无人机利用 ISAC 波形同时感知障碍物和与地面站通信
- **集群协同**：多无人机通过 ISAC 信号实现相互定位和数据共享

## 性能指标与理论极限

### 感知性能指标

| 指标 | 定义 | 典型值（mmWave ISAC，量级参考） |
|------|------|---------------------|
| 距离分辨率 | 区分两个目标的最小距离 | 约 3.75 cm（4 GHz 带宽，按 Δr=c/(2B)） |
| 速度分辨率 | 区分两个目标的最小速度差 | 约 0.5 m/s（28 GHz, 10 ms 帧，公式量级） |
| 角度分辨率 | 区分两个目标的最小角度差 | 约 2°（64 天线阵列，阵列孔径量级） |
| 最大感知距离 | 可检测目标的最远距离 | 约百米级（与发射功率、RCS、杂波强相关） |
| 检测概率 | 正确检测目标的概率 | 高 SNR 条件下可 >95%（需结合虚警率约束） |

### 通感性能折中

ISAC 系统存在固有的通感性能折中——增强感知性能可能损害通信质量，反之亦然。

**Pareto 前沿**描述了在给定资源约束下，通信速率和感知精度的最优折中曲线。据公开综述与仿真研究，相比独立部署的通信+雷达系统，ISAC 有望在感知性能损失较小（约个位数百分比量级）的情况下，提升通信频谱效率；具体增益高度依赖场景、波形与功率分配，不宜当作普适工程承诺。

## 标准化进展

### 3GPP 标准化

| 版本 | 时间线 | ISAC 相关内容 |
|------|--------|-------------|
| Rel-18 | 2024 完成 | SI（Study Item，研究项目）：ISAC 场景和需求定义 |
| Rel-19 | 2025–2026 进行中 | WI（Work Item，工作项目）：ISAC 信道模型、KPI 框架 |
| Rel-20 | 约 2026–2027 | 预期：ISAC 系统设计规范 |
| 6G 标准 | 约 2028+ | 预期：ISAC 作为原生能力纳入 |

### ITU-R IMT-2030

ITU（International Telecommunication Union，国际电信联盟）在 IMT-2030（6G 愿景）中将 Sensing 列为 6G 六大使用场景之一，与通信并列。这标志着 ISAC 从研究走向标准化的里程碑。

### IEEE 802.11bf（WiFi Sensing）

IEEE 正在制定 802.11bf 标准，定义基于 WiFi 信号的感知功能。这是 ISAC 在非蜂窝领域的重要标准化努力，进度以工作组最新草案为准。

## 局限、挑战与可改进方向

### 1. 杂波抑制不足

**局限**：感知回波中包含大量来自墙壁、地面、家具的杂波，静态杂波与慢速目标在距离-多普勒域易重叠，导致虚警或漏检。
**改进**：引入自适应杂波图 + 多帧相参积累；在边缘侧用轻量 ML 做杂波/目标分类；部署前用场地标定建立环境基线。

### 2. 全双工自干扰

**局限**：发射与接收同时进行时，自干扰可达约 100 dB 量级（据公开全双工研究），远超常规 ADC 动态范围，是单站 ISAC 的硬瓶颈。
**改进**：射频域模拟消除 + 数字域残余消除级联；优先评估双站/多站感知拓扑以规避同站自干扰；在协议层用时分通感作为过渡方案。

### 3. 多基站协同感知的同步与融合

**局限**：单基站覆盖与角度分辨有限；多基站协同可提升精度，但时钟同步误差、回传带宽与数据融合延迟会抵消协同增益。
**改进**：采用 GNSS/PTP 混合授时并量化同步误差对测距的影响；感知特征在边缘压缩后再回传；先做"软协同"（共享检测列表）再演进到"硬协同"（原始 IQ 融合）。

### 4. 隐私与安全治理缺失

**局限**：基站级感知可推断用户位置与活动模式，现有通信隐私框架（如加密）无法直接覆盖"被动感知"风险。
**改进**：在标准中明确感知数据最小化与用途限制；对原始感知张量做本地特征化后再上传；提供用户可关闭的感知服务开关与审计日志。

### 5. 通感资源分配缺乏可运营 KPI

**局限**：实验室 Pareto 曲线难以直接映射为运营商可计费、可保障的 SLA。
**改进**：定义通感联合 KPI（如"在给定通信吞吐下的检测概率/定位 RMSE"）；在 Rel-19/20 试验网中做场景化基线测试并公开测量方法。

## 参考文献

[1] F. Liu et al., "Integrated Sensing and Communications: Toward Dual-Functional Wireless Networks for 6G and Beyond," IEEE Journal on Selected Areas in Communications, 2024.
[2] A. Liu et al., "A Survey on Fundamental Limits of Integrated Sensing and Communication," IEEE Communications Surveys & Tutorials, 2024.
[3] W. Yuan et al., "OTFS-ISAC: Joint Communication and Radar Sensing in Delay-Doppler Domain," IEEE Transactions on Signal Processing, 2024.
[4] X. Mu et al., "RIS-Assisted ISAC: Joint Beamforming and Phase Shift Design," IEEE Transactions on Wireless Communications, 2024.
[5] 3GPP, "Study on Integrated Sensing and Communication," TR 22.837, 2024.
[6] Z. Wei et al., "Multi-Functional RIS-Assisted Integrated Sensing and Communication," IEEE Communications Magazine, 2024.
[7] C. Xu et al., "ISAC for IoT: From Theory to Practice," IEEE Internet of Things Journal, 2024.
[8] ITU-R, "Framework and Overall Objectives of the Future Development of IMT for 2030 and Beyond," Recommendation M.2160, 2023.
[9] J. A. Zhang et al., "Perceptive Networks: A New Paradigm for Future Wireless Networks," IEEE Wireless Communications, 2024.
[10] Y. Cui et al., "Near-Field ISAC: Sensing and Communication in the Fresnel Region," IEEE Transactions on Communications, 2024.
[11] IEEE 802.11bf Task Group, "WLAN Sensing," IEEE Standards Association, 2024.
[12] C. Sturm and W. Wiesbeck, "Waveform Design and Signal Processing Aspects for Fusion of Wireless Communications and Radar Sensing," Proceedings of the IEEE, 2011.
