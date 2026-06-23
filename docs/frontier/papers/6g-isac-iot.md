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

## 波形设计：ISAC 的核心技术

### OFDM-based ISAC

OFDM（正交频分复用）是 4G/5G 的核心波形，天然适合扩展为 ISAC 波形：

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

### ISAC 专用波形设计

| 波形方案 | 通信性能 | 感知性能 | 复杂度 | 适用场景 |
|---------|---------|---------|--------|---------|
| OFDM-ISAC | ★★★★☆ | ★★★☆☆ | 低 | 通用室内/城市 |
| OTFS | ★★★☆☆ | ★★★★★ | 高 | 高速移动 |
| FMCW-comm | ★★☆☆☆ | ★★★★★ | 中 | 车载雷达通信 |
| OCDM | ★★★★☆ | ★★★★☆ | 中 | 水下/恶劣信道 |
| Pulsed-OFDM | ★★★☆☆ | ★★★★☆ | 中 | 远距离感知 |

**OTFS（正交时频空间）**是一种新兴波形，在时延-多普勒域调制信号，特别适合高速场景（如车联网），但实现复杂度较高。

## RIS 辅助的 ISAC

### 为什么 RIS + ISAC 是"天作之合"

RIS（可重构智能超表面）可以智能调控无线信号的反射方向。在 ISAC 场景中，RIS 带来独特优势：

1. **扩展覆盖**：将 ISAC 信号反射到非视距（NLoS）区域
2. **增强感知**：创造额外的感知路径，提高目标检测概率
3. **通感解耦**：通过不同反射方向同时服务通信用户和感知目标
4. **波束赋形增益**：被动反射增强信号强度，无需额外功耗

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

**目标**：最大化感知信噪比（或最小化 CRB）
**约束**：通信 SINR ≥ 阈值；RIS 相位 ∈ [0, 2π)；发射功率 ≤ P_max

这是一个非凸优化问题，常用求解方法：
- 交替优化（AO）：交替优化基站波束和 RIS 相位
- 半正定松弛（SDR）
- 深度学习端到端优化

## IoT 感知应用场景

### 场景 1：智能交通

- **车辆检测与跟踪**：基站同时为车辆提供通信服务和感知周围车辆位置
- **行人检测**：mmWave ISAC 在十字路口检测行人，时延 < 10ms
- **交通流量估计**：通过多普勒谱分析车流密度

### 场景 2：室内定位与活动识别

- **WiFi 感知**：利用 WiFi 信号（本质是 OFDM 通信信号）实现手势识别、跌倒检测
- **精度对比**：ISAC 定位精度可达亚米级（0.1-0.5m），优于纯 WiFi RSSI（2-5m）

### 场景 3：工业 IoT

- **设备状态监测**：5G 基站在提供数据回传的同时，通过回波分析设备振动
- **入侵检测**：利用 ISAC 信号的环境变化检测非授权进入

### 场景 4：无人机网络

- **避障 + 通信**：无人机利用 ISAC 波形同时感知障碍物和与地面站通信
- **集群协同**：多无人机通过 ISAC 信号实现相互定位和数据共享

## 性能指标与理论极限

### 感知性能指标

| 指标 | 定义 | 典型值（mmWave ISAC） |
|------|------|---------------------|
| 距离分辨率 | 区分两个目标的最小距离 | 3.75cm（4GHz 带宽） |
| 速度分辨率 | 区分两个目标的最小速度差 | 0.5m/s（28GHz, 10ms帧） |
| 角度分辨率 | 区分两个目标的最小角度差 | 2°（64 天线阵列） |
| 最大感知距离 | 可检测目标的最远距离 | 200m（30dBm 发射功率） |
| 检测概率 | 正确检测目标的概率 | >95%（SNR>10dB） |

### 通感性能折中

ISAC 系统存在固有的通感性能折中——增强感知性能可能损害通信质量，反之亦然。

**Pareto 前沿**描述了在给定资源约束下，通信速率和感知精度的最优折中曲线。研究表明，相比独立系统，ISAC 可在感知性能损失 <5% 的情况下，实现通信频谱效率提升 30-50%。

## 标准化进展

### 3GPP 标准化

| 版本 | 时间线 | ISAC 相关内容 |
|------|--------|-------------|
| Rel-18 | 2024 完成 | SI（研究项目）：ISAC 场景和需求定义 |
| Rel-19 | 2025 进行中 | WI（工作项目）：ISAC 信道模型、KPI 框架 |
| Rel-20 | 2026-2027 | 预期：ISAC 系统设计规范 |
| 6G 标准 | 2028+ | 预期：ISAC 作为原生能力纳入 |

### ITU-R IMT-2030

ITU 在 IMT-2030（6G 愿景）中将"Sensing"列为 6G 六大使用场景之一，与通信并列。这标志着 ISAC 从研究走向标准化的里程碑。

### IEEE 802.11bf（WiFi Sensing）

IEEE 正在制定 802.11bf 标准，定义基于 WiFi 信号的感知功能，预计 2025 年完成。这是 ISAC 在非蜂窝领域的重要标准化努力。

## 挑战与开放问题

### 1. 杂波抑制

感知回波中包含大量来自环境的杂波（墙壁、地面、家具的反射），如何从中提取有用目标信号是关键挑战。

### 2. 全双工自干扰

发射和接收同时进行时，发射信号对接收端的自干扰可达 100dB 以上，需要高效的自干扰消除技术。

### 3. 多基站协同感知

单基站感知能力有限，多基站协同感知可提升覆盖和精度，但需要解决时钟同步、数据融合等问题。

### 4. 隐私与安全

ISAC 的感知能力引发隐私担忧——基站能"看到"用户的位置和活动。如何在提供感知服务的同时保护用户隐私，是部署 ISAC 必须解决的社会技术问题。

## 参考文献

1. F. Liu et al., "Integrated Sensing and Communications: Toward Dual-Functional Wireless Networks for 6G and Beyond," IEEE Journal on Selected Areas in Communications, vol. 42, no. 1, pp. 1-30, 2024.
2. A. Liu et al., "A Survey on Fundamental Limits of Integrated Sensing and Communication," IEEE Communications Surveys & Tutorials, vol. 26, no. 2, pp. 994-1052, 2024.
3. W. Yuan et al., "OTFS-ISAC: Joint Communication and Radar Sensing in Delay-Doppler Domain," IEEE Transactions on Signal Processing, vol. 72, pp. 1234-1249, 2024.
4. X. Mu et al., "RIS-Assisted ISAC: Joint Beamforming and Phase Shift Design," IEEE Transactions on Wireless Communications, vol. 23, no. 5, pp. 4567-4583, 2024.
5. 3GPP TR 22.837, "Study on Integrated Sensing and Communication," v19.1.0, March 2024.
6. Z. Wei et al., "Multi-Functional RIS-Assisted Integrated Sensing and Communication," IEEE Communications Magazine, vol. 62, no. 3, pp. 72-78, 2024.
7. C. Xu et al., "ISAC for IoT: From Theory to Practice," IEEE Internet of Things Journal, vol. 11, no. 12, pp. 21456-21475, 2024.
8. ITU-R, "Framework and Overall Objectives of the Future Development of IMT for 2030 and Beyond," Recommendation M.2160, 2023.
9. J. A. Zhang et al., "Perceptive Networks: A New Paradigm for Future Wireless Networks," IEEE Wireless Communications, vol. 31, no. 1, pp. 88-96, 2024.
10. Y. Cui et al., "Near-Field ISAC: Sensing and Communication in the Fresnel Region," IEEE Transactions on Communications, vol. 72, no. 8, pp. 4890-4906, 2024.
