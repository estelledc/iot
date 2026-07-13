---
schema_version: '1.0'
id: uwb-fira-car-digital-key
title: UWB FiRa数字车钥匙技术方案
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites:
  - uwb-ieee-802-15-4z-ranging
  - uwb-secure-ranging-distance-bounding
tags:
  - UWB
  - FiRa
  - CCC
  - 数字车钥匙
  - STS
  - 中继攻击
  - BLE
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# UWB FiRa数字车钥匙技术方案

> **难度**：🔴 高级 | **领域**：UWB应用 | **阅读时间**：约 18 分钟

## 日常类比

酒店房卡只认“卡在读卡器上”，不认“卡在楼里某处”。BLE（Bluetooth Low Energy，低功耗蓝牙）无钥匙像“楼里有信号就开门”；UWB（Ultra-Wideband，超宽带）数字车钥匙像“必须站在门前才开”——用飞行时间证明物理距离，中继转发会拉长往返时延而被拒绝[1][2]。

## 摘要

架构是 **BLE 发现/认证 + UWB 安全测距 + SE（Secure Element，安全元件）存钥**。FiRa（Fine Ranging）推动互操作配置，CCC（Car Connectivity Consortium）Digital Key 定义车钥匙剖面。文中距离阈值、锚点数量与成本为量级示意，**以 CCC/厂商实现与现场标定为准**[1][3]。

## 1. 为何需要 UWB

遥控钥匙与 BLE 被动进入验证的是身份与加密会话，不验证距离。中继攻击（Relay Attack）把车与钥匙间的合法帧经两台设备转发，车端仍看到有效认证，却可能相隔百米级[2][4]。

UWB 带宽通常 ≥500 MHz，时间分辨率可达纳秒量级；中继的接收—转发引入额外延迟，测得距离偏大，超过解锁阈值即拒绝[3][5]。

| 代际 | 典型机制 | 主要缺口 |
|------|----------|----------|
| 机械/遥控 | 物理或滚动码 | 便利性或早期固定码风险 |
| BLE 被动进入 | 加密认证 | 不防中继 |
| UWB 数字钥匙 | 认证 + ToF（Time of Flight）测距 | 需多锚点与手机 UWB 覆盖 |

## 2. 标准与角色

**FiRa**：基于 IEEE 802.15.4z 定义测距配置、安全与互操作认证，覆盖门禁、寻物、车钥匙等用例[2][6]。

**CCC Digital Key**：车—手机互操作规范；Release 3.x 引入 UWB 测距与被动进入/启动等要求。公开材料常引用厘米级测距与 STS（Scrambled Timestamp Sequence，加扰时间戳序列）安全测距——**具体指标以正式规范与认证测试为准**[1][7]。

| 组件 | 主要职责 |
|------|----------|
| BLE | 发现、会话、身份与密钥协商 |
| UWB | STS 保护测距、多锚点区域判断 |
| SE | 凭证/私钥、密码运算、抗篡改存储 |

## 3. 车端与手机端

车端常部署多个 UWB 锚点（公开方案多为数个至十余个量级），经车载总线连 ECU（Electronic Control Unit），配合 BLE 与 SE[4][7]。手机侧需 UWB 芯片、系统 API、SE/安全飞地与数字钥匙应用（如 Wallet/CarKey 类集成）[8][9]。

## 4. 解锁流程（机制）

1. **BLE 发现**：近距建立连接。
2. **双向认证**：SE 侧挑战—响应，派生/协商 UWB STS 密钥。
3. **UWB 测距**：STS 帧与多锚点测距/定位，校验距离与区域。
4. **分区动作**：迎宾、侧门解锁、后备箱、驾驶座允许启动、离开落锁等策略由 ECU 执行。
5. **持续跟踪**：离开有效区后停 UWB、落锁，回 BLE 待机扫描以控功耗[1][3]。

STS：双方用共享密钥生成伪随机序列嵌入测距帧；接收端相关匹配才采信到达时刻，降低伪造/重放测距的可行性[3][5]。

| 区域（示意） | 动作倾向 |
|--------------|----------|
| 数米迎宾区 | 唤醒、迎宾灯 |
| 近门区 | 对应侧门解锁 |
| 驾驶座区 | 允许启动 |
| 离开区 | 延迟确认后落锁 |

阈值与分区几何依赖锚点布局与标定，不可照搬示意数字[1][7]。

## 5. 备用与边界

CCC 类方案常要求 NFC（Near Field Communication）备用：手机深度掉电时 SE 可借读卡器场能完成近距解锁（能力通常弱于完整 UWB 会话）[1][8]。厚金属壳可衰减 UWB；多手机同场需靠定位区分驾驶员与乘客[7][9]。

## 6. 局限、挑战与可改进方向

### 1. 手机 UWB 覆盖不均

**局限**：中低端机型常无 UWB，跨品牌互操作依赖认证进度。
**改进**：NFC/实体钥匙兜底；采购前核对 CCC/FiRa 认证矩阵与机型清单[1][6]。

### 2. 车端锚点成本与标定

**局限**：多锚点、线束与产线标定抬高 BOM 与售后复杂度。
**改进**：按车型优化锚点数；产线天线延迟与区域阈值自动化标定[4][7]。

### 3. 多用户与误动作

**局限**：多钥匙同场、乘客侧靠近可能导致误解锁或启动策略歧义。
**改进**：驾驶座几何约束 + 明确优先级策略；记录测距轨迹审计[1][9]。

### 4. 环境与壳体退化

**局限**：NLOS（Non-Line-of-Sight）、人体遮挡、金属壳使测距变差。
**改进**：质量门限下增加测距轮次；劣于门限则拒绝自动动作并提示用户确认[3][5]。

## 7. 实践要点

1. 安全叙事以“STS + 距离阈值”为主，勿只谈 BLE 加密。
2. 验收做中继演练与分区边界路测，记录误拒/误开率。
3. 明确掉电 NFC 能力边界（能否启动等）。

## 参考文献

[1] Car Connectivity Consortium, Digital Key Release 3.x specification / public overview.
[2] FiRa Consortium, UWB secure ranging and use-case profiles.
[3] IEEE Std 802.15.4z-2020, Enhanced Impulse Radio.
[4] Automotive digital key application notes (e.g. NXP NCJ29D5 / Trimension materials).
[5] Singh, M. et al., UWB ranging/localization tutorials and surveys, IEEE ComST / related.
[6] FiRa Consortium, interoperability and certification program documentation.
[7] Coppens, D. et al., "An Overview of UWB Standards and Organizations," IEEE Access, 2022.
[8] Apple, Car Keys / Nearby Interaction developer documentation.
[9] Google / Android, UWB API and Digital Car Key framework documentation.
[10] Samsung, Digital Key / Exynos Connect UWB product materials.
[11] Brands & Chaum; Rasmussen & Capkun — distance bounding background (threat model).
[12] Industry reports on relay attacks against passive entry systems (treat case numbers as anecdotal).
