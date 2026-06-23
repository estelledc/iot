# ZigBee/Matter/Thread：智能家居协议演进

> 难度：🟢 入门 | 领域：短距通信 · 智能家居 | 更新：2025-06

---

## 一句话总结

智能家居经历了"协议战国时代"——ZigBee、Z-Wave、WiFi、蓝牙各自为政，不同品牌的设备互不兼容。Matter 协议的出现终结了这场混战：它统一了应用层标准，让 Apple/Google/Amazon/Samsung 的设备终于能"说同一种语言"。Thread 则作为 Matter 的首选无线承载层，用 IPv6 Mesh 替代了 ZigBee 的非标准网络层。

---

## 从日常场景说起

你买了一个智能灯泡，包装盒上写着"支持 ZigBee"。你回家打开 iPhone 的 Home 应用——发现找不到这个灯泡。因为 Apple Home 不直接支持 ZigBee。你又下载了灯泡厂商的 App——能控制了，但不能和你的 Amazon Echo 联动。

这就是 2020 年之前智能家居的现状：

- 买了 Philips Hue（ZigBee），需要 Hue Bridge
- 买了 IKEA TRÅDFRI（ZigBee），需要 IKEA Hub
- 两个都是 ZigBee 设备，但直接连不通（应用层协议不同）
- 想用 Siri 控制？需要通过 HomeKit 桥接
- 想用 Alexa 控制？需要通过 Alexa Skill 桥接

每个生态系统都是一个"孤岛"。消费者被迫选边站队，或者装一堆 App 和桥接器。

Matter 的目标就是打破这些孤岛——**一个设备，配一次网，所有平台都能控制**。

---

## ZigBee 3.0：奠基者

### 历史与定位

ZigBee 是最早为物联网/智能家居设计的无线协议之一（2004 年首版）。它基于 IEEE 802.15.4 物理层，运行在 2.4 GHz 频段，主打低功耗、低速率、Mesh 组网。

ZigBee 3.0（2016 年发布）统一了之前碎片化的多个 ZigBee 配置文件（Home Automation、Light Link、Building Automation 等），形成了一个统一标准。

### ZigBee 3.0 技术概览

| 参数 | ZigBee 3.0 |
|------|-----------|
| 物理层 | IEEE 802.15.4 |
| 频段 | 2.4 GHz (全球)，868/915 MHz (可选) |
| 速率 | 250 kbps (2.4 GHz) |
| 网络拓扑 | Star, Tree, Mesh |
| 最大节点数 | 65,535 (理论) |
| 传输范围 | 10-30m (室内)，100m+ (室外) |
| 功耗 | 低 (休眠设备 < 1 μA) |
| 安全性 | AES-128 加密 + 网络密钥 |
| 寻址方式 | 16-bit 短地址 (非 IP) |

### ZigBee Mesh 网络

ZigBee 的 Mesh 网络由三种角色的设备组成：

**Coordinator（协调器）**：网络的创建者和管理者，整个 ZigBee 网络只有一个。通常是网关/Hub。

**Router（路由器）**：中继数据包的设备。必须常供电（不能休眠）。通常是灯泡、插座等有电源的设备。

**End Device（终端设备）**：只和自己的父节点（Router 或 Coordinator）通信，不参与中继。可以长时间休眠。通常是传感器、遥控器等电池设备。

Mesh 的好处是**自愈和扩展覆盖**：如果一条路径断了（比如某个灯泡坏了），数据可以自动绕道通过其他 Router。网络覆盖范围随 Router 的增加而扩大——理论上，一个足够大的 ZigBee Mesh 可以覆盖整栋大楼。

### ZigBee 的问题

1. **非 IP 协议**：ZigBee 使用自己的 16-bit 短地址，不是 IP 地址。要和互联网通信，必须通过 ZigBee 网关做协议翻译。这增加了复杂性和成本。
2. **互操作性不完美**：虽然 ZigBee 3.0 统一了配置文件，但不同厂商的实现仍有细微差异，导致"理论兼容、实际不通"的情况。
3. **安全模型简单**：ZigBee 的网络密钥是所有设备共享的。一旦一个设备被攻破，整个网络的密钥就泄露了。
4. **2.4 GHz 拥挤**：和 WiFi、蓝牙共享 2.4 GHz 频段，在设备密集的环境中可能被干扰。

---

## Thread：IPv6 的 Mesh

### 为什么需要 Thread？

Thread 的诞生（2014 年）就是为了解决 ZigBee 的痛点：非 IP、互操作性差、安全模型弱。Thread Group 的创始成员包括 Google（Nest）、ARM、Samsung、NXP 等。

Thread 的核心理念是：**在 IEEE 802.15.4 物理层上运行标准的 IPv6 网络协议**。

### Thread 技术架构

```
┌───────────────────────────────┐
│   应用层 (CoAP, HTTP, etc.)   │ ← 可直接用标准 IP 应用协议
├───────────────────────────────┤
│   传输层 (UDP)                │
├───────────────────────────────┤
│   网络层 (IPv6 / 6LoWPAN)     │ ← 标准 IPv6，用 6LoWPAN 压缩
├───────────────────────────────┤
│   Mesh 转发 (MLE + 路由)      │ ← 自组织 Mesh 路由
├───────────────────────────────┤
│   MAC 层 (IEEE 802.15.4)      │
├───────────────────────────────┤
│   物理层 (IEEE 802.15.4)      │ ← 和 ZigBee 共用同一物理层
│   2.4 GHz, 250 kbps           │
└───────────────────────────────┘
```

### Thread 的关键概念

**Border Router（边界路由器）**：连接 Thread 网络和外部 IP 网络（WiFi/以太网）的设备。它做的是 IPv6 地址翻译和路由，不是协议转换——Thread 设备有自己的 IPv6 地址，可以被外部 IP 网络直接寻址。

Apple HomePod Mini、Apple TV 4K、Google Nest Hub、Amazon Echo（第四代）都内置了 Thread Border Router 功能。用户无需购买额外的网关。

**Mesh 组网**：Thread 使用 MLE（Mesh Link Establishment）协议自动建立和维护 Mesh 拓扑。设备角色动态分配：Router（中继）、REED（Router-Eligible End Device，有能力当 Router 但当前是终端）、SED（Sleepy End Device，休眠终端）。

**无单点故障**：和 ZigBee 的 Coordinator 不同，Thread 网络没有单一的中央控制器。任何 Router 都可以转发数据，任何 Border Router 都可以连接外网。一个 Border Router 坏了，流量自动切换到另一个。

### Thread vs ZigBee 详细对比

| 特性 | ZigBee 3.0 | Thread 1.3 |
|------|-----------|-----------|
| 物理层 | IEEE 802.15.4 | IEEE 802.15.4 |
| 网络层 | ZigBee Network Layer (非IP) | IPv6 / 6LoWPAN |
| 寻址 | 16-bit 短地址 | 128-bit IPv6 地址 |
| Mesh 路由 | AODV / Tree Routing | MLE + RPL |
| 需要网关协议转换？ | 是 | 否 (Border Router 仅做路由) |
| 安全模型 | 单一网络密钥 | DTLS + 独立设备证书 |
| 入网方式 | Coordinator 允许 | Commissioner 认证 |
| 单点故障 | Coordinator | 无 (多 Border Router) |
| 最大设备数 | 65,535 (理论) | ~250 (单网络推荐上限) |
| 多协议共存 | 不直接支持 | 和 BLE 共存 (双协议芯片) |
| 标准化程度 | ZigBee Alliance 私有标准 | Thread Group 标准，基于 IETF RFC |
| 与 Matter 关系 | Matter over ZigBee（不推荐） | Matter over Thread（首选） |

---

## Matter：终极统一者

### 诞生背景

2019 年 12 月，Apple、Google、Amazon、ZigBee Alliance（后改名 CSA）联合宣布了 **Project CHIP（Connected Home over IP）**。2022 年 10 月，CHIP 正式更名为 **Matter 1.0**，同时发布了首版规范。

Matter 不是一个新的无线技术——它是一个**应用层协议**，定义了设备之间如何"对话"的语义（"灯泡开""调亮度到 50%""传感器报温度 22.5°C"）。Matter 可以运行在多种底层传输技术之上：

```
┌───────────────────────────────────────────┐
│           Matter 应用层                    │
│  (设备类型、集群、属性、命令、事件)         │
├───────────┬───────────┬───────────────────┤
│  Thread   │   WiFi    │   以太网           │
│ (802.15.4)│ (802.11)  │ (802.3)           │
└───────────┴───────────┴───────────────────┘
         BLE 用于设备配网（commissioning）
```

### Matter 的核心设计

**设备类型标准化**：Matter 定义了标准的设备类型——灯泡、开关、温控器、门锁、传感器、窗帘、空气质量监测器等 40+ 种设备类型。每种设备类型对应一组标准化的"集群（Cluster）"，集群定义了属性（如亮度）、命令（如开/关）和事件（如按钮按下）。

**多管理员（Multi-Admin）**：一个 Matter 设备可以同时被多个生态系统控制——比如同一个灯泡同时加入 Apple Home、Google Home 和 Amazon Alexa。每个生态系统有自己的管理员权限，互不冲突。

**本地控制优先**：Matter 设备之间的通信是本地的（通过局域网），不需要经过云端。这意味着即使互联网断了，你仍然可以用手机控制灯泡。

**安全性**：Matter 使用 CASE（Certificate Authenticated Session Establishment）建立安全会话，每个设备有唯一的设备证书（DAC）。入网时通过 PASE（Passcode-Authenticated Session Establishment）验证，支持 QR 码扫描或 NFC 触碰。

### Matter 版本演进

| 版本 | 发布时间 | 新增设备类型 / 功能 |
|------|---------|-------------------|
| Matter 1.0 | 2022.10 | 灯泡、开关、插座、温控器、门锁、窗帘、传感器 |
| Matter 1.1 | 2023.05 | ICD（间歇连接设备）优化、Bug修复 |
| Matter 1.2 | 2023.10 | 冰箱、洗衣机、扫地机器人、烟感、空气质量、空调 |
| Matter 1.3 | 2024.05 | 能源管理、EV 充电、微波炉、烤箱、水阀控制 |
| Matter 1.4 | 2024.11 | 增强型 ICD、场景管理、Thread 网络诊断 |
| Matter 2.0 | 2025+ (预期) | 摄像头（关注焦点）、高带宽设备支持 |

### 实际体验：Matter 设备配网流程

1. 打开 Matter 设备（如灯泡），灯泡开始广播 BLE 信号
2. 打开手机上的 Home App（Apple/Google/Amazon 任一个）
3. 扫描灯泡包装上的 QR 码 / Matter Setup Code
4. App 通过 BLE 和灯泡建立 PASE 安全连接
5. App 将 WiFi 密码或 Thread 网络凭据发送给灯泡
6. 灯泡加入 WiFi 或 Thread 网络
7. App 向 DCL（分布式合规账本）验证灯泡的设备证书
8. 配网完成，灯泡出现在 Home App 中

整个过程约 30-60 秒。用户不需要知道灯泡是 WiFi 的还是 Thread 的，Matter 在底层处理了一切。

---

## 生态系统现状

### 各平台 Matter 支持情况（2025 年初）

| 平台 | 控制器设备 | Thread BR | Matter 支持版本 |
|------|-----------|----------|---------------|
| Apple Home | iPhone, iPad, Mac, Apple Watch | HomePod Mini, Apple TV 4K | Matter 1.2+ |
| Google Home | Android, Nest Hub | Nest Hub (2nd gen), Nest WiFi Pro | Matter 1.2+ |
| Amazon Alexa | Echo, Fire TV | Echo (4th gen) | Matter 1.2+ |
| Samsung SmartThings | Galaxy 手机, SmartThings Hub | SmartThings Station | Matter 1.2+ |
| Home Assistant | 任何浏览器/App | 需要 Thread dongle | Matter 1.3 (通过 Python SDK) |

### 市场数据

- Matter 认证设备数量：~1500+（截至 2025 年初，CSA 官方数据）
- 主要品牌均已推出 Matter 设备：Philips Hue、IKEA、Eve、Nanoleaf、Aqara、Yale、Schlage 等
- 约 40% 的新 Matter 设备使用 Thread 作为底层传输，50% 使用 WiFi，10% 使用以太网
- 中国市场：Aqara、Yeelight、绿米、欧瑞博等品牌积极拥抱 Matter

---

## 从 ZigBee 迁移到 Matter

### 迁移路径

对于拥有大量 ZigBee 设备的用户，迁移到 Matter 有几种方式：

**方式 1：ZigBee-to-Matter 桥接器**

最低成本方案。在 ZigBee 网关（如 Hue Bridge）上运行 Matter Bridge 功能，让 ZigBee 设备以 "桥接设备"的形式暴露给 Matter 控制器。

- Philips Hue Bridge 已通过固件升级支持 Matter Bridge
- 用户不需要更换任何硬件
- 但桥接设备的功能受限于桥接器的翻译能力

**方式 2：双协议芯片**

新设备使用 Thread + ZigBee 双协议芯片（如 Silicon Labs EFR32MG24），硬件同时支持两种协议，通过 OTA 固件升级从 ZigBee 切换到 Thread/Matter。

**方式 3：逐步替换**

随着旧设备到寿命终点，用 Matter 原生设备替换。对于灯泡（寿命 2-3 万小时 ≈ 5-8 年），自然淘汰周期内即可完成迁移。

### 芯片平台

| 芯片厂商 | 产品系列 | 支持协议 | 特点 |
|----------|---------|---------|------|
| Silicon Labs | EFR32MG24 | Thread + ZigBee + BLE | 最成熟的 Matter 开发平台 |
| Nordic | nRF5340 + nRF21540 | Thread + BLE | 低功耗强项 |
| NXP | RW612 | Thread + WiFi + BLE | 三协议集成 |
| Espressif | ESP32-H2 | Thread + BLE | 最低成本选项 |
| Telink | TLSR9 | Thread + BLE | 超低功耗，面向传感器 |
| Bouffalo Lab | BL702 | Thread + BLE | 中国本土方案 |

---

## 对比总结

| 维度 | ZigBee 3.0 | Thread 1.3 | Matter 1.4 |
|------|-----------|-----------|-----------|
| 层级 | 完整栈 (PHY→APP) | 网络层 + 传输层 | 应用层 |
| IP 支持 | 否 | 是 (IPv6) | 是 (IP 原生) |
| 需要网关 | 是 (协议翻译) | Border Router (仅路由) | 不一定 (WiFi 设备不需要) |
| 互操作性 | 有限 | 网络层互通 | 应用层完全互通 |
| 生态统一 | ZigBee 内部 | Thread 内部 | Apple+Google+Amazon+Samsung |
| 安全性 | AES-128 共享密钥 | DTLS + 设备证书 | CASE/PASE + DAC |
| 功耗 | 极低 | 极低 | 取决于底层传输 |
| 成熟度 | 成熟 (20 年) | 成熟 (10 年) | 成长期 (3 年) |
| 未来定位 | 存量维护 | Matter 的首选承载 | 智能家居统一标准 |

---

## 给初学者的总结

如果你正在做智能家居产品：

1. **新产品一律选 Matter**——无论底层用 Thread 还是 WiFi
2. **电池供电的小设备**（传感器、遥控器）→ Thread（低功耗 Mesh）
3. **有电源的大设备**（灯泡、插座、空调）→ WiFi 或 Thread 都行
4. **已有 ZigBee 产品线**→ 考虑双协议芯片 + OTA 升级路径
5. **不要再从零开始做 ZigBee 新产品**，除非是维护已有产品线

---

## 参考文献

1. CSA (Connectivity Standards Alliance). "Matter 1.0 Core Specification," Oct 2022.
2. CSA. "Matter 1.4 Specification," Nov 2024.
3. Thread Group. "Thread 1.3.0 Specification," 2023.
4. ZigBee Alliance. "ZigBee 3.0 Base Device Behavior Specification," 2016.
5. Google. "Matter & Thread: Architecture and Implementation Guide," developer.android.com, 2024.
6. Apple. "Matter Support in HomeKit and Home App," developer.apple.com, 2024.
7. Silicon Labs. "EFR32MG24: Multiprotocol Wireless SoC for Matter," Product Brief, 2024.
8. Nordic Semiconductor. "nRF Connect SDK: Matter Development Guide," 2024.
9. Espressif. "ESP-Matter: Open-Source Matter SDK on ESP32," GitHub, 2024.
10. S. Raza et al., "IPv6 Mesh Networking for Smart Home: Thread Protocol Analysis," IEEE Access, vol. 11, 2023.
11. ABI Research. "Smart Home Protocol Market: Matter Adoption Forecast 2024-2029," Q3 2024.
