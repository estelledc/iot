---
schema_version: '1.0'
id: multi-tenant-edge-isolation
title: 多租户边缘隔离技术
layer: 4
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - container-orchestration-edge
  - wasm-edge-sandbox
  - mec-5g-integration
tags:
- 多租户
- 隔离
- Kata
- TrustZone
- SGX
- Cilium
- MIG
- MEC
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 多租户边缘隔离技术

> **难度**：🟡 中级 | **领域**：边缘计算、安全隔离、多租户 | **阅读时间**：约 22 分钟

## 日常类比

合租房：每人有卧室（计算隔离），共用客厅厨房（共享基础设施）。要防 A 拿 B 的东西（数据）、C 吵到别人（资源干扰），还要分摊水电（计量）。边缘多租户同一套硬件跑互不信任负载；节点可能只有数核 CPU、十余 GB 内存与一块 GPU，不能“一人一台大虚机”。MEC（Multi-access Edge Computing，多接入边缘计算）上游戏、缓存与企业 AI 共存时，隔离是硬需求[1]。

## 摘要

覆盖计算/网络/存储三维隔离、容器到硬件 TEE（Trusted Execution Environment，可信执行环境）的强度光谱、Calico/Cilium 策略、GPU 共享（MIG/time-slicing）与选型。性能与开销数字为文献或厂商材料的**量级示意**，跨平台差异大。

## 1. 隔离的三个维度

| 维度 | 隔离目标 | 风险场景 |
|------|---------|---------|
| 计算 | CPU/GPU/内存不被抢占 | 大任务拖慢邻居 |
| 网络 | 流量不被嗅探/篡改 | 跨租户抓包 |
| 存储 | 文件/数据不越权 | 读走他人模型 |

### 隔离强度光谱

```
进程 → 容器(cgroup/namespace) → gVisor/Kata → 虚拟机 → 硬件(TrustZone/SGX/TDX)
开销↑小                                              开销↑大
隔离↑弱                                              隔离↑强
```

无绝对最优，只有安全需求与性能预算的折中。

## 2. 基于 Namespace 的容器隔离

Linux 容器依赖命名空间 + cgroup v2：

| Namespace | 隔离内容 | 标志 |
|-----------|---------|------|
| PID | 进程 ID | CLONE_NEWPID |
| NET | 网络栈 | CLONE_NEWNET |
| MNT | 挂载点 | CLONE_NEWNS |
| UTS | 主机名 | CLONE_NEWUTS |
| IPC | 信号量/共享内存 | CLONE_NEWIPC |
| USER | UID/GID | CLONE_NEWUSER |

```yaml
# Kubernetes Pod 资源限制示意
apiVersion: v1
kind: Pod
metadata:
  name: tenant-a-inference
spec:
  containers:
  - name: model-server
    image: triton:24.05
    resources:
      requests: { cpu: "2", memory: "4Gi", nvidia.com/gpu: "1" }
      limits:   { cpu: "4", memory: "8Gi", nvidia.com/gpu: "1" }
    securityContext:
      runAsNonRoot: true
      readOnlyRootFilesystem: true
      capabilities: { drop: ["ALL"] }
```

**局限**：共享宿主机内核。历史上存在 runc 等逃逸类 CVE；侧信道（如缓存）与 I/O/缓存干扰仍在 cgroup 之外。互不信任租户需叠加更强隔离。

## 3. 硬件辅助隔离

### 3.1 ARM TrustZone

Normal World 跑租户业务；Secure World（如 OP-TEE）做密钥、安全启动与敏感推理。典型不是“每租户一个安全世界”（仅两世界），而是敏感操作进 Secure World，业务用容器隔离[6]。

### 3.2 Intel SGX / TDX 与 AMD SEV-SNP

SGX（Software Guard Extensions）提供 Enclave 加密内存，OS 被攻破也难直接读权重；EPC（Enclave Page Cache）容量有限（早期约百 MB 量级，后续可扩展但仍有开销），大模型不适合整模塞入，更适合保护关键密钥/权重片段[5]。TDX（Trust Domain Extensions）与 AMD SEV-SNP 偏 VM 级机密计算。ARM CCA（Confidential Compute Architecture）以 Realm 为目标形态，开销需按平台实测[6]。

### 3.3 硬件方案对比

| 方案 | 粒度 | 性能开销量级 | 平台 | 典型用途 |
|------|------|-------------|------|---------|
| TrustZone | 两世界 | 常较低（个位数百分比量级） | ARM Cortex-A | 密钥、安全启动 |
| SGX | 进程内 Enclave | 常十余–数十百分比量级 | Intel Xeon 等 | 模型 IP 保护 |
| TDX | VM 级 | 常个位数–十余百分比 | 新一代 Xeon | 机密 VM |
| SEV-SNP | VM 级 | 常较低 | AMD EPYC | 机密 VM |
| CCA | Realm | 视实现 | ARMv9 | 下一代边缘安全 |

## 4. 网络隔离

### 4.1 NetworkPolicy（Calico 等）

默认拒绝跨租户，再按需放开；DNS 等基础设施单独放行[8]。

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: tenant-a-isolation
  namespace: tenant-a
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
  ingress:
  - from:
    - namespaceSelector: { matchLabels: { tenant: a } }
  egress:
  - to:
    - namespaceSelector: { matchLabels: { tenant: a } }
  - to:
    - namespaceSelector: {}
      podSelector: { matchLabels: { k8s-app: kube-dns } }
    ports: [{ port: 53, protocol: UDP }]
```

### 4.2 Cilium eBPF

规则规模大时，eBPF 路径相对 iptables 链遍历更稳；Cilium 还可做 L7（HTTP/gRPC 方法级）策略[3]：

| 指标 | iptables 路径 | eBPF 路径（Calico/Cilium） |
|------|--------------|---------------------------|
| 策略更新 | 规则多时可达秒级 | 常毫秒级量级 |
| 转发附加延迟 | 相对更高 | 相对更低（微秒量级差） |
| L7 策略 | 通常无 | Cilium 支持 |
| 加密 | WireGuard 等可选 | WireGuard / IPsec 等 |

具体微秒数依赖内核、网卡与规则集，表中仅为量级对照。

## 5. 资源配额与 GPU 共享

### 5.1 ResourceQuota

按 namespace 设 CPU/内存/GPU/Pod/PVC 硬上限，防止单租户挤占节点。

### 5.2 GPU 共享

| 方案 | 原理 | 隔离 | 性能损耗量级 |
|------|------|------|-------------|
| MPS | 多进程共享 | 弱（共享地址空间语义） | 常个位数–十余百分比 |
| MIG | 硬件分区（A100/H100 等） | 强 | 常较低 |
| vGPU | 虚拟化（常需许可） | 强 | 常十余百分比量级 |
| time-slicing | 时间片复用 | 弱 | 视争用 |

MIG（Multi-Instance GPU）适合多租户硬隔离，但 Jetson/T4 等边缘卡通常不支持[4]。不支持时可用 Device Plugin time-slicing，并明确告知租户非硬隔离。

### 5.3 公平调度

默认 kube-scheduler 不感知租户公平；Volcano 等可用 Queue 权重与可回收配额做比例公平[9]。

## 6. 方案对比与 MEC 选型

| 维度 | 容器+NetworkPolicy | Kata | Firecracker | SGX 等 |
|------|-------------------|------|-------------|--------|
| 启动 | 亚秒–秒级 | 常秒级 | 常亚秒–秒级 | N/A（库内） |
| 内存开销 | 基线 | 每实例数十 MB 量级 | 每实例数–十余 MB 量级 | EPC/加密开销 |
| 安全 | 中 | 高 | 高 | 最高（特定威胁模型） |
| 场景 | 互信租户 | 互不信任 | Serverless 边缘 | IP/密钥保护 |
| 运维 | 低 | 中 | 中 | 高 |

公开材料中，运营商 MEC 有 OpenStack+Kata、K8s+Calico、microVM+可信根等不同路线；ETSI MEC 相关规范强调至少 namespace 级隔离，关键场景建议硬件辅助[1][2][7]。具体运营商部署细节随版本变化，宜对照当期规范与招标技术附件。

## 7. 实践要点

- 互信部门：容器 + default-deny NetworkPolicy 往往够用；互不信任才上 Kata/microVM/硬件。
- GPU：能 MIG 优先 MIG；否则 time-slicing 并写清 SLA。
- 运行时监控：Falco/Tracee 等检测异常 syscall 与提权尝试。
- 入门：`unshare` 感受 namespace → NetworkPolicy 互通测试 → RuntimeClass 对比 Kata。

## 8. 局限、挑战与可改进方向

### 1. 共享内核的残余风险

**局限**：再严的 cgroup 也无法消除内核逃逸与部分侧信道面。
**改进**：互不信任租户默认 Kata/Firecracker；关键密钥进 TEE；持续 CVE 与运行时检测[2][7]。

### 2. 边缘 GPU 硬隔离缺口

**局限**：主流边缘 GPU 无 MIG，time-slicing/MPS 隔离弱[4]。
**改进**：租户合同写明干扰边界；按模型分时窗口；或拆物理卡/节点。

### 3. 硬件 TEE 容量与移植成本

**局限**：SGX EPC 等限制大工作负载；API 与运维陡[5]。
**改进**：只保护密钥与小关键路径；大推理放机密 VM（TDX/SEV）或独立节点。

### 4. 策略规模与误配

**局限**：百千条 NetworkPolicy 易误放行；iptables 路径更新抖动。
**改进**：default-deny + 租户模板；eBPF 数据面；策略变更走评审与连通性测试[3][8]。

## 参考文献

[1] ETSI, "Multi-access Edge Computing (MEC); Security Framework," GS MEC 相关规范, 2024.
[2] Kata Containers, "Architecture Documentation," https://katacontainers.io/
[3] Cilium, "Network Policy Documentation," https://docs.cilium.io/
[4] NVIDIA, "Multi-Instance GPU User Guide," https://docs.nvidia.com/datacenter/tesla/mig-user-guide/
[5] Intel, "Intel SGX Developer Reference," https://www.intel.com/content/www/us/en/developer/tools/software-guard-extensions/overview.html
[6] ARM, "Arm Confidential Compute Architecture," https://www.arm.com/architecture/security-features/arm-confidential-compute-architecture
[7] Firecracker, "Firecracker Documentation," https://firecracker-microvm.github.io/
[8] Tigera/Calico, "Network Policy," https://docs.tigera.io/calico/latest/network-policy/
[9] Volcano, "Queue and Fair Scheduling," https://volcano.sh/en/docs/
[10] T. Zhang et al., "Multi-Tenant Edge Computing: Security Isolation Mechanisms and Performance Analysis," IEEE TCC, 2023.
[11] gVisor Project, "gVisor Documentation," https://gvisor.dev/docs/
[12] Kubernetes SIGs, "Pod Security Standards," https://kubernetes.io/docs/concepts/security/pod-security-standards/
