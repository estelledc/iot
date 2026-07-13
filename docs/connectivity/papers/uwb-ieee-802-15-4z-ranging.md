---
schema_version: '1.0'
id: uwb-ieee-802-15-4z-ranging
title: UWB IEEE 802.15.4z精密测距协议
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites:
  - uwb-positioning
tags:
  - UWB
  - IEEE-802.15.4z
  - STS
  - TWR
  - DS-TWR
  - TDoA
  - 测距
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# UWB IEEE 802.15.4z精密测距协议

> **难度**：🔴 高级 | **领域**：UWB精密定位 | **阅读时间**：约 18 分钟

## 日常类比

窄带测距像在雾里听持续喇叭声，难分直达与回声；UWB（Ultra-Wideband）像清脆拍手——短脉冲在时间轴上可分辨首达路径。802.15.4z 再给拍手加上“只有双方知道的暗号节奏”（STS），别人无法伪造合法到达时刻[1][2]。

## 摘要

覆盖 IR-UWB 测距物理基础、SS-TWR/DS-TWR、STS 安全增强、信道/PRF 要点，以及 TWR 与 TDoA 定位分工。文中厘米级精度、信道编号与芯片时钟分辨率为典型量级，**随 LOS/NLOS、天线延迟校准与实现而变**[1][3]。

## 1. 为何带宽决定测距

时间分辨率大致随带宽提高。BLE 等窄带难做可靠 ToF；UWB 常用 ≥500 MHz 带宽与亚纳秒级脉冲，配合首达路径检测，商用实现常报厘米量级测距（视距条件）[2][3]。

IEEE 802.15.4z（2020）在 802.15.4a 脉冲无线电基础上增强安全测距（STS）与互操作相关能力，是消费与汽车 UWB 的常见引用基线[1][4]。

## 2. TWR 机制

**SS-TWR（Single-Sided Two-Way Ranging）**：发起者发 POLL，响应者回 RESPONSE；用往返时间减处理时延得 ToF。两端晶振频偏会引入误差[1][3]。

**DS-TWR（Double-Sided TWR）**：增加 FINAL 等交换，用两侧往返/回复时间组合估计 ToF，抑制一阶时钟频偏，代价是多一轮空口[1][5]。

距离 ≈ ToF × c。天线与前端固定延迟必须校准，否则出现米级固定偏差[3][6]。

| 方法 | 要点 | 代价 |
|------|------|------|
| SS-TWR | 消息少 | 对频偏更敏感 |
| DS-TWR | 抑频偏 | 多帧、耗时/耗电略增 |
| TDoA | 标签多发少收 | 锚点需紧同步 |

## 3. STS 安全增强

无安全保护的测距可被中继或伪造时间戳操纵。STS（Scrambled Timestamp Sequence）由共享密钥与计数器经密码学派生，嵌入测距相关字段；接收端本地生成期望序列做相关，峰值不足则拒绝该次测距[1][2][7]。

| STS 模式（概念） | 特点 |
|------------------|------|
| Mode 0 | 无 STS，兼容/无此层保护 |
| Mode 1 | STS 与载荷同帧等配置 |
| Mode 2 | 强调测距、减小攻击面（常用于高安全） |
| Mode 3 | STS 与载荷相对位置的另一配置 |

具体帧格式与推荐模式以标准与 FiRa 配置文件为准[1][4]。

## 4. 物理层要点

常用信道包括 Channel 5、9 等（中心频率与约 500 MHz 带宽量级）；PRF（Pulse Repetition Frequency）与速率选项在功耗、距离与精度间权衡。前导码长度影响同步鲁棒性与开销[1][6]。

芯片时间戳分辨率可达数十皮秒量级（对应毫米级理论距离量子），**实际精度由多径、NLOS、校准主导**[3][6]。

## 5. 从测距到定位

- **多锚点 TWR/三边**：标签与各锚点测距后解算坐标；2D/3D 分别至少约 3/4 锚点，工程上常冗余部署[5]。
- **TDoA（Time Difference of Arrival）**：标签广播，同步锚点测到达时间差；标签侧省电、适合多标签，锚点同步是难点[5][8]。

| 条件 | 典型影响 |
|------|----------|
| LOS | 首达清晰，精度较好 |
| NLOS | ToA 偏大，精度退化；需检测/补偿 |
| 未校天线延迟 | 固定偏差 |
| 温漂 | 晶振与延迟漂移，工业场景需补偿 |

## 6. 局限、挑战与可改进方向

### 1. NLOS 被当成真距

**局限**：穿透/绕射使测距系统性偏大，区域判断误判。
**改进**：CIR/首达功率比等 NLOS 指示；多锚点一致性校验；拒绝低置信度样本[3][8]。

### 2. 安全模式配置错误

**局限**：Mode 0 或弱密钥管理使“有 UWB 无安全”。
**改进**：高价值场景强制 STS + SE 存钥；会话密钥派生与计数器防重放[1][7]。

### 3. 校准与温度

**局限**：产线未校或温漂导致整网偏差。
**改进**：已知基线距离校准；温度表或在线补偿；回归测试[6]。

### 4. TDoA 同步工程重

**局限**：有线/无线同步失败直接毁掉定位。
**改进**：小规模用 DS-TWR；大规模才上 TDoA 并监控同步残差[5][8]。

## 7. 实践要点

1. 先定安全等级再选 STS 模式与密钥生命周期。
2. 验收分 LOS/NLOS 报告误差分布，不报单一“标称厘米”。
3. 天线延迟写入版本化配置，与固件一并管理。

## 参考文献

[1] IEEE Std 802.15.4z-2020, Enhanced Impulse Radio.
[2] FiRa Consortium, UWB secure ranging technical overview.
[3] Singh, M. et al., UWB ranging and localization tutorial/survey literature.
[4] Coppens, D. et al., "An Overview of UWB Standards and Organizations," IEEE Access, 2022.
[5] Sahinoglu, Z., Gezici, S., Guvenc, I., Ultra-Wideband Positioning Systems, Cambridge Univ. Press.
[6] Qorvo / Decawave DW3000 family datasheets and application notes.
[7] Brands, S. and Chaum, D., Distance-bounding protocols, EUROCRYPT 1993 (conceptual background).
[8] Alarifi, A. et al., "Ultra Wideband Indoor Positioning Technologies," Sensors, 2016.
[9] Monica, S. and Ferrari, G., UWB localization and anchor placement, IEEE Access.
[10] NXP Trimension / automotive UWB product briefs.
[11] Apple Nearby Interaction / U1-U2 public technical materials (ecosystem reference).
[12] Ridolfi, M. et al., experimental UWB indoor positioning evaluations, Sensors.
