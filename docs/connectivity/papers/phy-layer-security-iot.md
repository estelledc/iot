---
schema_version: '1.0'
id: phy-layer-security-iot
title: 物理层安全在IoT无线通信中的应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites:
  - ble-security-pairing-bonding
  - fading-multipath-iot-channel
tags:
  - 物理层安全
  - 保密容量
  - 人工噪声
  - 信道密钥
  - RF指纹
  - 窃听信道
  - IoT安全
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 物理层安全在IoT无线通信中的应用

> **难度**：🔴 高级 | **领域**：通信安全 | **阅读时间**：约 18 分钟

## 日常类比

咖啡馆里低声近聊：旁人听不清，靠的是“信道优势”而非暗语。物理层安全（Physical Layer Security, PLS）用无线信道的衰落、空间方向与硬件瑕疵做保密/认证补充，**不替代** AES 等密码学，而是纵深一层[1][2]。

## 摘要

Wyner 窃听信道给出保密容量（Secrecy Capacity）直觉：主信道优于窃听信道时，可信息论意义保密。工程手段含波束成形、人工噪声（Artificial Noise, AN）、协作干扰、信道密钥生成与射频（RF）指纹。IoT 算力弱时有吸引力，但依赖信道优势、多天线与标准化不足——**商用仍以密码学为主、PLS 为辅**[5]。

## 1. 信息论要点

| 角色 | 含义 |
|------|------|
| Alice | 发送方 |
| Bob | 合法接收方 |
| Eve | 窃听者 |

`Cs ≈ max{C_AB − C_AE, 0}`。Cs>0 需主信道优势；Eve 更近/更好天线时可能 Cs=0[1]。

| 维度 | 传统加密 | PLS |
|------|----------|-----|
| 安全基础 | 计算假设 | 信息论/信道 |
| 密钥 | 需分发管理 | 可从信道提取 |
| 算力 | 中–高 | 信号处理级 |
| 条件 | 通用 | 需信道/空间优势 |
| 成熟度 | 标准成熟 | 研究/试验为主 |

## 2. 关键技术

**波束成形**：能量对准 Bob，对已知 Eve 方向置零；需信道状态信息（CSI）与多天线。
**人工噪声**：功率分给有用信号与落在 Bob 零空间的噪声；Eve 位置未知时更常用，但受辐射法规约束[2]。
**协作干扰**：空闲节点帮扰 Eve，适合密集传感网，需同步与信任模型。

**信道密钥生成**：互易性 → 探测 → 量化 → 信息协调 → 隐私放大。静态环境密钥率可极低（需人为扰动/跳频）[3]。公开叙述中的数百–数千 bps **高度场景依赖，不可当通用指标**。

**RF 指纹**：振荡器频偏、功放非线性、I/Q 失衡等作设备身份；网关侧提取，终端零开销。准确率随设备数、信道漂移与对抗仿真变化，**需持续模板更新**[4]。

## 3. 场景选型

| 场景 | 更贴合的 PLS | 注意 |
|------|--------------|------|
| 家居传感 | RF 指纹 + 信道密钥 | 静态信道密钥慢 |
| 工厂密集网 | AN / 协作干扰 | 法规与干扰预算 |
| V2X | 波束成形 | 高移动 CSI |
| 体域网 | 信道密钥 | 隐私与校准 |

## 4. 局限、挑战与可改进方向

### 1. Eve 未知与距离劣势

**局限**：零陷需 Eve 方向；Eve 更近则保密容量可能为零。
**改进**：AN + 传统加密并用；物理分区与功率控制；不把 PLS 当唯一防线。

### 2. 静态与半双工

**局限**：密钥率依赖信道变化；半双工探测破坏理想互易窗口。
**改进**：随机跳频/人为扰动；缩短探测间隔；密钥作会话补充而非唯一根密钥。

### 3. 硬件与标准

**局限**：AN/波束需多天线；低成本单天线终端难落地；缺统一商用标准。
**改进**：安全功能放网关侧；跟进 3GPP/学术试验；验收用对抗测试而非论文准确率。

### 4. RF 指纹漂移

**局限**：温漂、老化、信道变化导致误拒/漏检。
**改进**：慢漂移自适应；突变告警；与证书/配对双因素。

## 5. 实践要点

1. 默认：TLS/DTLS/链路加密 + 设备身份；PLS 仅作增强。
2. 评估前先测主/窃听几何与是否具备多天线网关。
3. 任何“99% 识别率”须绑定设备数、信道与对抗模型。

## 参考文献

[1] Wyner, A. D., "The Wire-Tap Channel," Bell Syst. Tech. J., 1975.
[2] Mukherjee, A. et al., "Principles of Physical Layer Security in Multiuser Wireless Networks," IEEE Commun. Surveys Tuts., 2014.
[3] Zhang, J. et al., "Key Generation from Wireless Channels: A Review," IEEE Access, 2016.
[4] Sankhe, K. et al., "ORACLE: Optimized Radio Classification through CNNs," IEEE INFOCOM, 2019.
[5] Wang, N. et al., "Physical-Layer Security of 5G Wireless Networks for IoT," IEEE IoT J., 2019.
[6] Bloch, M. and Barros, J., Physical-Layer Security, Cambridge Univ. Press.
[7] 3GPP study items / discussions on physical layer security (track release notes).
[8] Surveys on artificial noise and cooperative jamming for IoT.
[9] RF fingerprinting robustness and domain-shift studies.
[10] ITU/ETSI spectrum emission limits relevant to intentional AN.
[11] Hybrid crypto + PLS architecture notes for constrained devices.
