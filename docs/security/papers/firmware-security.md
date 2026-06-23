# IoT固件安全分析：从提取到防护的全链路

> 难度：🟠 挑战 | 领域：固件安全/逆向工程 | 更新：2025-06

---

## 一句话总结

IoT 设备的固件是攻防的核心战场——攻击者通过提取和逆向固件发现漏洞，防御者通过安全启动链和签名验证保护固件完整性。本文覆盖固件提取方法、逆向工程技术、自动化漏洞发现（Fuzzing/符号执行）以及安全启动链的设计。

---

## 从日常场景说起

你家路由器的"系统"是什么？不是 Windows 也不是 macOS，而是一个几 MB 大的"固件"——它包含了操作系统（通常是精简 Linux）、应用程序、配置文件和密钥，全部打包成一个二进制文件烧写在 Flash 芯片里。

如果有人能拿到这个固件文件并分析它，就可能找到硬编码的密码、不安全的服务、已知漏洞的老旧组件——这就是固件安全分析。好的一面：安全研究员用同样的方法帮厂商找到问题；坏的一面：攻击者也在用同样的方法找攻击入口。

---

## IoT 固件安全现状

### 2024 年行业数据

Finite State 2024 报告（分析了 4000+ 固件镜像）的关键发现：

| 指标 | 数值 |
|------|------|
| 平均每个固件的已知 CVE | 27 个 |
| 高危/严重 CVE 占比 | 12% |
| 使用已知不安全函数的固件比例 | 78% |
| 包含硬编码凭证的固件比例 | 21% |
| 使用 5 年以上老旧组件的比例 | 63% |
| 支持安全 OTA 更新的比例 | 34% |
| 实现安全启动的比例 | 28% |

根因分析：IoT 厂商往往是硬件公司，软件安全能力薄弱。为了节省成本和缩短开发周期，大量使用过时的 SDK 和开源组件，且从不更新。

---

## 固件提取

要分析固件，第一步是获取它。从易到难有多种方法：

### 提取方法对比

| 方法 | 难度 | 需要的设备 | 成功率 | 风险 |
|------|------|-----------|--------|------|
| 官网下载 | 低 | 浏览器 | 中（很多厂商不提供） | 无 |
| OTA 更新截获 | 低 | 抓包工具 | 高（如果 OTA 不加密） | 无 |
| UART/JTAG 读取 | 中 | TTL转USB, OpenOCD | 高 | 低 |
| SPI Flash 直读 | 中 | SPI 编程器 + 热风枪 | 高 | 可能损坏设备 |
| 芯片脱焊读取 | 高 | BGA 返修台 | 很高 | 需要经验 |
| 侧信道辅助提取 | 高 | 示波器 + 专用工具 | 中 | 需要专业知识 |
| 故障注入绕过保护 | 很高 | 故障注入设备 | 中 | 可能永久损坏 |

### 常见固件格式

| 格式 | 常见设备 | 文件系统 | 提取工具 |
|------|----------|----------|----------|
| Squashfs + 内核 | 路由器, NVR | SquashFS | binwalk, unsquashfs |
| JFFS2 | 旧款路由器 | JFFS2 | jefferson |
| UBI/UBIFS | 现代 IoT 网关 | UBIFS | ubi_reader |
| 裸机 binary | MCU 设备 | 无文件系统 | 直接加载到 Ghidra |
| 加密固件 | 高端设备 | 加密容器 | 需要先破解密钥 |
| 签名+加密 | 安全设备 | 多层保护 | 极难提取有效内容 |

---

## 逆向工程

提取固件后，下一步是理解它的结构和逻辑。

### 工具链

| 工具 | 用途 | 支持架构 | 开源 |
|------|------|----------|------|
| Ghidra | 反汇编+反编译 | ARM/MIPS/x86/RISC-V/+ | 是（NSA 发布） |
| IDA Pro | 反汇编+反编译 | 几乎所有 | 否（商业） |
| Binary Ninja | 反汇编+中间表示分析 | 主流架构 | 否（商业） |
| radare2/rizin | 命令行逆向框架 | 广泛支持 | 是 |
| binwalk | 固件解包/文件系统提取 | N/A | 是 |
| EMBA | 自动化固件安全扫描 | Linux-based | 是 |
| Firmwalker | 固件静态信息提取 | Linux-based | 是 |
| FirmAE | 固件仿真运行 | ARM/MIPS | 是 |

### 静态分析流程

1. **固件解包**：用 binwalk 识别和提取文件系统、内核、引导加载程序
2. **文件系统分析**：扫描硬编码密码、私钥、配置文件
3. **二进制分析**：用 Ghidra 逆向关键二进制（如 httpd、管理进程）
4. **组件识别**：通过字符串和库版本确定使用的开源组件及版本
5. **CVE 匹配**：将组件版本与已知 CVE 数据库比对

### 动态分析（仿真）

很多漏洞只在运行时才能触发。FirmAE/QEMU 可以在 PC 上模拟运行 IoT 固件：

- 用 QEMU 模拟 ARM/MIPS CPU
- 用 nvram 模拟设备配置存储
- 用虚拟网络接口模拟网络环境
- 成功仿真率：约 79%（FirmAE 论文数据）

仿真后可以：登录设备 Web 界面、发送网络请求、运行 exploit 验证漏洞。

---

## 自动化漏洞发现

### Fuzzing（模糊测试）

Fuzzing 的原理：向目标程序输入大量畸形/随机数据，观察是否导致崩溃或异常行为。

**IoT Fuzzing 的特殊挑战**：

| 挑战 | 说明 | 解决方案 |
|------|------|----------|
| 无法直接在设备上跑 | MCU 没有 OS 支持 | 仿真 + rehosting |
| 交叉编译复杂 | ARM/MIPS/RISC-V | 仿真器辅助 |
| 状态依赖 | 需要特定协议状态才能触发深层代码 | 协议感知 fuzzing |
| 外设依赖 | 固件访问特定硬件寄存器 | HAL 模拟/抽象 |
| 反馈困难 | 裸机固件无覆盖率反馈 | 硬件辅助/仿真插桩 |

**主要 IoT Fuzzer 对比**：

| 工具 | 方法 | 目标 | 发现漏洞数 | 适用范围 |
|------|------|------|-----------|----------|
| Fuzzware (2022) | 仿真 + 硬件模型 | MCU 固件 | 30+ (论文报告) | Cortex-M |
| SaTC (2021) | 前端入口点提取 + fuzzing | Linux IoT | 33 零日 | 路由器/摄像头 |
| FirmFuzz (2019) | 系统仿真 + AFL | Linux IoT | 12 零日 | 通用 |
| Greenhouse (2024) | LLM 辅助 + 选择性仿真 | MCU 固件 | 45+ | ARM Cortex-M |
| DIANE (2021) | 应用伴侣 app 分析 + fuzzing | IoT 设备 | 11 零日 | 有配套 app 的 |

### 符号执行（Symbolic Execution）

符号执行将程序输入设为"符号变量"（而非具体值），沿着所有可能的执行路径推导约束条件。当约束可满足时，自动生成能触发特定代码路径的具体输入。

**在 IoT 固件分析中的应用**：

- **angr**：Python 符号执行框架，支持 ARM/MIPS，可分析固件二进制
- **KLEE**：LLVM 级符号执行，需要源码
- **Triton**：动态符号执行（concolic），适合跟踪具体执行路径

**限制**：路径爆炸（分支太多时不可行）、环境建模困难（需要模拟 OS/硬件）。

### 2024 年新趋势：LLM 辅助漏洞发现

大语言模型正在被用于辅助固件安全分析：

- **漏洞模式识别**：LLM 理解反编译代码并识别常见漏洞模式（缓冲区溢出、格式化字符串等）
- **Fuzzing 种子生成**：LLM 理解协议格式后生成高质量的 fuzzing 输入
- **逆向辅助**：LLM 为反编译的函数命名、添加注释
- Google Project Zero 和 DARPA AIxCC 项目已展示 LLM 辅助发现真实 CVE 的能力

---

## 安全启动链

### 什么是安全启动？

安全启动（Secure Boot）确保设备从上电到运行应用程序的每一步都经过验证——只有被信任的代码才能执行。

### 信任链模型

```
硬件信任根 (ROM/eFuse)
    | 验证签名
    v
第一级引导加载程序 (BL1)
    | 验证签名
    v
第二级引导加载程序 (BL2/U-Boot)
    | 验证签名
    v
操作系统内核
    | 验证签名
    v
应用程序/服务
```

每一级在启动下一级之前，用上一级传递的公钥验证下一级的签名。如果任何一级验证失败，启动终止。

### 信任根类型

| 信任根 | 安全强度 | 成本 | 灵活性 | 典型芯片 |
|--------|----------|------|--------|----------|
| Mask ROM | 高（不可修改） | 低 | 无（固化） | 大部分 MCU |
| OTP (eFuse) | 高（一次性写入） | 中 | 低 | NXP i.MX, STM32H7 |
| 安全芯片 | 很高 | 高 | 中 | ATECC608B, SE050 |
| PUF + ROM | 很高 | 低 | 中 | Intrinsic ID 方案 |

### MCUboot：IoT 安全启动的事实标准

MCUboot 是 Zephyr/Apache Mynewt 生态的开源安全引导加载程序：

- 支持 RSA-2048/ECDSA-P256/Ed25519 签名验证
- 支持回滚保护（版本号递增，不允许降级）
- 支持加密固件镜像（出厂加密，启动时解密）
- 占用 Flash：约 24-48 KB（取决于配置）
- 支持双分区 (A/B) 更新和回退

---

## 安全 OTA 更新

### 为什么 OTA 安全如此重要？

OTA 是修复漏洞的唯一途径（不可能派人去更新每个设备），但也是攻击面：如果 OTA 通道被攻破，攻击者可以向数百万设备推送恶意固件。

### SUIT（Software Updates for IoT）标准

IETF SUIT 工作组定义了面向资源受限设备的安全更新架构：

- **Manifest**：描述更新内容的签名元数据（版本、大小、哈希、依赖关系）
- **Envelope**：包含 Manifest 和固件镜像
- **COSE 签名**：使用 CBOR Object Signing and Encryption
- **最小实现**：约 4KB ROM, 1KB RAM

### OTA 安全方案对比

| 方案 | 签名验证 | 加密传输 | 回滚保护 | 增量更新 | 适合设备 |
|------|----------|----------|----------|----------|----------|
| 无安全 OTA | 无 | 无 | 无 | 无 | 不推荐 |
| HTTPS + 校验和 | 弱（仅完整性） | TLS | 无 | 可选 | 基本保护 |
| MCUboot + SUIT | ECDSA/Ed25519 | COSE_Encrypt | 版本号递增 | 是 (bsdiff) | IoT 终端 |
| Mender.io | RSA/ECDSA | mTLS | 是 | 是 (delta) | Linux IoT |
| AWS IoT OTA | Code Signing | TLS 1.2 | 是 | 是 | AWS 生态 |

---

## 固件安全评估框架

### OWASP Firmware Security Testing Methodology

OWASP 定义的固件安全测试清单：

| 测试项 | 检查内容 | 常见发现 |
|--------|----------|----------|
| 信息泄露 | 硬编码密码、API key、私钥 | 21% 固件含硬编码凭证 |
| 过时组件 | 已知漏洞的库/内核版本 | 63% 使用 5 年以上组件 |
| 不安全服务 | Telnet/FTP/无鉴权 debug 端口 | 44% 有不必要的服务暴露 |
| 加密弱点 | 弱算法(MD5/DES)、密钥管理缺陷 | 31% 使用过时加密 |
| 权限问题 | root 运行服务、SUID 滥用 | 56% 服务以 root 运行 |
| 更新机制 | 无签名、无回滚保护 | 66% 更新不验签名 |

### 自动化评估工具

**EMBA（Embedded Firmware Analyzer）**：

- 全自动固件安全扫描
- 支持：CVE 匹配、密码搜索、加密分析、配置检查
- 输出：HTML 报告 + 严重度评分
- 覆盖：超过 150 项检查规则
- 2024 年已集成 LLM 辅助分析（GPT-4 解释漏洞影响）

---

## 真实漏洞案例分析

### 案例 1：TP-Link 路由器命令注入 (CVE-2024-XXXX)

- 漏洞：Web 管理界面的 ping 诊断功能未过滤用户输入
- 发现方法：binwalk 解包 -> Ghidra 逆向 httpd -> 发现 system() 调用
- 影响：远程代码执行（RCE），无需认证
- 修复：输入验证 + 使用安全的 API 替代 system()

### 案例 2：某智能门锁固件降级攻击 (2024)

- 漏洞：OTA 更新没有回滚保护，可以推送旧版固件
- 攻击链：MITM 截获更新请求 -> 替换为含已知漏洞的旧版固件 -> 利用旧漏洞获取控制
- 修复：MCUboot 启用版本号递增检查

### 案例 3：工业 PLC 硬编码密钥 (2024)

- 漏洞：固件中硬编码了用于设备间通信的对称密钥
- 影响：任何获取固件的人都能伪造通信
- 发现方法：EMBA 自动扫描 -> 字符串搜索发现 128-bit 密钥
- 正确做法：使用 PUF 生成设备唯一密钥 + TLS mutual auth

---

## 2024-2025 发展趋势

**SBOM（Software Bill of Materials）强制化**：EU CRA 和美国行政令要求 IoT 设备提供 SBOM，列出所有软件组件及版本。这使得漏洞追踪和修复更加可行。

**Rust for IoT Firmware**：Rust 的内存安全特性从根源上消除缓冲区溢出类漏洞。Embassy（Rust 嵌入式异步框架）正在被越来越多的 IoT 项目采用。

**eBPF for Firmware Monitoring**：在 Linux IoT 设备上用 eBPF 做运行时行为监控，检测异常系统调用和内存访问模式。

**AI 驱动的漏洞挖掘**：LLM + Fuzzing + 符号执行的组合正在大幅提升漏洞发现效率。Google 的 OSS-Fuzz + AI 项目在 2024 年发现了 26 个新的开源组件漏洞。

---

## 参考文献

1. Finite State. "The State of IoT/Connected Device Security 2024." Annual Report, 2024.
2. Costin, A., et al. "A Large-Scale Analysis of the Security of Embedded Firmwares." USENIX Security, 2014.
3. Chen, D., et al. "FirmAE: Towards Large-Scale Emulation of IoT Firmware for Dynamic Analysis." USENIX Security, 2020.
4. Scharnowski, T., et al. "Fuzzware: Using Precise MMIO Modeling for Effective Firmware Fuzzing." USENIX Security, 2022.
5. IETF. "SUIT: Software Updates for Internet of Things." RFC 9019 / draft-ietf-suit-manifest, 2024.
6. MCUboot Project. "MCUboot: Secure Boot for 32-bit Microcontrollers." Documentation, 2024.
7. Shoshitaishvili, Y., et al. "SOK: (State of) The Art of War: Offensive Techniques in Binary Analysis." IEEE S&P, 2016.
8. EMBA Project. "EMBA: The Firmware Security Analyzer." GitHub, 2024.
9. Feng, Q., et al. "Greenhouse: LLM-assisted Firmware Rehosting and Fuzzing." USENIX Security, 2024.
10. OWASP. "Firmware Security Testing Methodology." OWASP IoT Project, 2024.
