# 多租户边缘隔离技术

> **难度**：🟡 中级 | **领域**：边缘计算、安全隔离、多租户 | **阅读时间**：约 20 分钟

## 日常类比

合租房是理解多租户隔离的最好类比。一套三居室住了三个租户，每人有独立卧室（计算隔离），共用客厅和厨房（共享基础设施）。问题在于：怎么保证 A 的东西不被 B 拿走（数据隔离）？怎么防止 C 半夜弹吉他吵到其他人（资源干扰）？怎么分配水电费（资源计量）？

边缘计算的多租户也是同一套硬件上跑多个互不信任的租户的工作负载。不同于云端有充裕的资源可以"一人一台虚拟机"，边缘节点资源紧张——可能只有 8 核 CPU、16GB 内存、一块 GPU。在这么有限的资源上做到安全隔离，同时不浪费性能，是核心挑战。

MEC（Multi-access Edge Computing）场景是多租户需求最典型的：运营商的边缘节点部署在基站侧，同时服务游戏公司的低延迟服务、视频公司的内容缓存、和企业的私有 AI 推理——它们之间绝不能互相访问对方的数据。

## 1. 隔离的三个维度

### 1.1 计算隔离、网络隔离、存储隔离

| 维度 | 隔离目标 | 风险场景 |
|------|---------|---------|
| 计算 | CPU/GPU/内存不被其他租户抢占 | 一个租户的大计算任务拖慢其他租户 |
| 网络 | 网络流量不被嗅探或篡改 | 租户 A 抓包获取租户 B 的数据 |
| 存储 | 文件和数据不被越权访问 | 租户 A 读取租户 B 的模型文件 |

三个维度需要同时满足。只做了计算隔离不做网络隔离，就像给每人一间卧室但不装门——还是形同虚设。

### 1.2 隔离强度的光谱

从弱到强排列：

```
进程级隔离 → 容器(cgroup/namespace) → gVisor/Kata → 虚拟机 → 硬件隔离(TrustZone/SGX)
  ↑ 开销最小              中等               开销最大 ↑
  ↑ 隔离最弱                                 隔离最强 ↑
```

没有"最好的隔离方案"，只有"最适合场景的方案"。关键是在安全需求和性能开销之间找平衡。

## 2. 基于 Namespace 的容器隔离

### 2.1 Linux 命名空间机制

Linux 容器的隔离建立在 6 种 namespace 之上：

| Namespace | 隔离内容 | 内核标志 |
|-----------|---------|---------|
| PID | 进程 ID 空间 | CLONE_NEWPID |
| NET | 网络栈（接口/路由/端口） | CLONE_NEWNET |
| MNT | 文件系统挂载点 | CLONE_NEWNS |
| UTS | 主机名和域名 | CLONE_NEWUTS |
| IPC | 进程间通信（信号量/共享内存） | CLONE_NEWIPC |
| USER | 用户和组 ID | CLONE_NEWUSER |

配合 cgroup v2 做资源限制：

```yaml
# Kubernetes Pod 资源限制示例
apiVersion: v1
kind: Pod
metadata:
  name: tenant-a-inference
spec:
  containers:
  - name: model-server
    image: triton:24.05
    resources:
      requests:
        cpu: "2"
        memory: "4Gi"
        nvidia.com/gpu: "1"
      limits:
        cpu: "4"
        memory: "8Gi"
        nvidia.com/gpu: "1"
    securityContext:
      runAsNonRoot: true
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
```

### 2.2 容器隔离的局限

容器共享宿主机内核，存在已知的逃逸风险：

- **CVE-2024-21626**（runc 容器逃逸）：通过特制的工作目录设置逃逸到宿主机
- **侧信道攻击**：共享 CPU 缓存可被利用进行 Flush+Reload 攻击
- **资源干扰**：即使设置了 cgroup 限制，I/O 带宽和 CPU 缓存仍然共享

对于互不信任的租户，纯容器隔离不够。需要叠加更强的隔离层。

## 3. 硬件辅助隔离

### 3.1 ARM TrustZone

TrustZone 把 ARM 处理器分成两个"世界"：

```
┌──────────────────────────────────────────┐
│              Normal World                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ 租户 A  │  │ 租户 B  │  │ 租户 C  │ │
│  │ (Linux) │  │ (Linux) │  │ (Linux) │ │
│  └─────────┘  └─────────┘  └─────────┘ │
├──────────────────────────────────────────┤
│              Secure World                 │
│  ┌──────────────────────────────┐        │
│  │  可信执行环境 (OP-TEE)       │        │
│  │  - 密钥管理                  │        │
│  │  - 安全启动验证              │        │
│  │  - 敏感模型推理              │        │
│  └──────────────────────────────┘        │
└──────────────────────────────────────────┘
```

TrustZone 的典型用法不是"每个租户一个安全世界"（只有两个世界），而是把密钥管理、身份认证等安全敏感操作放在 Secure World，业务逻辑在 Normal World 用容器隔离。

### 3.2 Intel SGX / TDX

SGX（Software Guard Extensions）提供 Enclave——一块加密内存区域，即使 OS 被攻破也无法读取。

```c
// SGX Enclave 内的敏感推理（简化示例）
#include <sgx_urts.h>

// Enclave 内函数：模型推理（外部不可窥探权重）
sgx_status_t ecall_inference(
    sgx_enclave_id_t eid,
    float* input,  size_t input_size,
    float* output, size_t output_size)
{
    // input 被拷贝进 enclave 加密内存
    // 模型权重预加载在 enclave 内
    // 推理结果拷贝出来（明文或加密）
    return SGX_SUCCESS;
}
```

SGX 的限制：EPC（Enclave Page Cache）大小有限（SGX1 为 128MB，SGX2 可扩展但仍有 overhead）。不适合跑大模型，但适合保护模型权重不被边缘运维人员拷贝。

Intel TDX（Trust Domain Extensions）是 SGX 的演进，提供 VM 级别的机密计算，适合保护整个虚拟机。

### 3.3 硬件隔离方案对比

| 方案 | 隔离粒度 | 性能开销 | 适用平台 | 典型用途 |
|------|---------|---------|---------|---------|
| TrustZone | 两个世界 | <5% | ARM (Cortex-A) | 密钥保护、安全启动 |
| SGX | Enclave（进程内） | 10-30% | Intel Xeon (v5+) | 模型IP保护 |
| TDX | 虚拟机级 | 5-10% | Intel 4th Gen Xeon+ | 机密 VM |
| AMD SEV-SNP | 虚拟机级 | 2-5% | AMD EPYC 3rd Gen+ | 机密 VM |
| CCA | Realm（VM/容器） | 预计 <10% | ARMv9 | 下一代边缘安全 |

## 4. 网络隔离策略

### 4.1 Calico 网络策略

Calico 用 eBPF 或 iptables 实现 Kubernetes 网络策略：

```yaml
# 租户 A 的网络策略：只允许同命名空间内通信
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: tenant-a-isolation
  namespace: tenant-a
spec:
  podSelector: {}     # 应用到 namespace 下所有 Pod
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          tenant: a    # 只允许同租户入站
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          tenant: a
  - to:                # 允许 DNS 查询
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - port: 53
      protocol: UDP
```

### 4.2 Cilium 的 eBPF 优势

Cilium 用 eBPF 替代 iptables，性能优势在大规模策略（>1000 条规则）时尤为明显：

| 指标 | Calico (iptables) | Calico (eBPF) | Cilium (eBPF) |
|------|-------------------|---------------|----------------|
| 策略更新延迟 | 秒级（规则多时） | 毫秒级 | 毫秒级 |
| 包转发延迟 | +15-20μs | +5-8μs | +3-5μs |
| 内存开销 | 与规则数线性 | 较低 | 最低 |
| L7 策略 | 不支持 | 不支持 | 支持（HTTP/gRPC） |
| 加密 | WireGuard 可选 | WireGuard 可选 | WireGuard / IPsec |

Cilium 的 L7 策略能力在边缘多租户场景很有价值——可以限制租户 A 只能调用特定的 gRPC 方法，而不仅仅是网络层的端口隔离。

## 5. 资源配额与公平调度

### 5.1 Kubernetes 资源配额

为每个租户的 namespace 设置硬性配额：

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-a-quota
  namespace: tenant-a
spec:
  hard:
    requests.cpu: "8"
    requests.memory: "16Gi"
    limits.cpu: "16"
    limits.memory: "32Gi"
    requests.nvidia.com/gpu: "2"
    pods: "20"
    persistentvolumeclaims: "10"
```

### 5.2 GPU 共享的挑战

单块 GPU 的多租户共享是当前最棘手的问题。三种方案：

| 方案 | 原理 | 隔离强度 | 性能损耗 |
|------|------|---------|---------|
| 时分复用 (MPS) | NVIDIA MPS 多进程服务 | 弱（共享内存空间） | 5-10% |
| MIG | 物理分区（A100/H100） | 强 | 0-5% |
| vGPU | 虚拟化（需 License） | 强 | 10-15% |

MIG（Multi-Instance GPU）是最适合多租户的方案——A100 可以分成最多 7 个独立实例，每个实例有独立的显存和计算单元。但边缘常用的 Jetson / T4 不支持 MIG。

对于不支持 MIG 的 GPU，可以用 NVIDIA Device Plugin 的 time-slicing 功能：

```yaml
# NVIDIA device plugin 配置 GPU 时间片共享
apiVersion: v1
kind: ConfigMap
metadata:
  name: nvidia-device-plugin
data:
  config.yaml: |
    version: v1
    sharing:
      timeSlicing:
        resources:
        - name: nvidia.com/gpu
          replicas: 4          # 一块 GPU 虚拟成 4 份
          failRequestsGreaterThanOne: true
```

### 5.3 公平调度器

默认的 Kubernetes 调度器不感知租户公平性。Volcano 批调度器提供了 Proportional Fairness 插件：

```yaml
# Volcano Queue 定义租户配额和权重
apiVersion: scheduling.volcano.sh/v1beta1
kind: Queue
metadata:
  name: tenant-a
spec:
  weight: 3          # 权重 3（相对于其他租户）
  capability:
    cpu: "16"
    memory: "32Gi"
  reclaimable: true  # 空闲资源可被其他租户借用
```

## 6. 隔离方案对比与选型

### 6.1 综合对比表

| 维度 | 容器 + NetworkPolicy | Kata Containers | Firecracker microVM | 硬件隔离(SGX) |
|------|---------------------|-----------------|---------------------|--------------|
| 启动时间 | <1s | 1-3s | <1s | N/A |
| 内存开销 | 基线 | +30-50MB/实例 | +5-15MB/实例 | +10-30% EPC |
| 安全等级 | 中 | 高 | 高 | 最高 |
| 适用场景 | 互信租户 | 互不信任租户 | Serverless 边缘 | IP 保护 |
| 运维复杂度 | 低 | 中 | 中 | 高 |

### 6.2 MEC 实际部署中的选型

中国三大运营商的 MEC 部署经验：

- **中国移动**：基于 OpenStack + Kata Containers，每个 MEC 节点 2-5 个租户，以 VM 级隔离为主
- **中国联通**：基于 Kubernetes + Calico 网络策略，轻量级隔离，适合同一企业内不同业务线
- **中国电信**：天翼云边缘采用"安全沙箱"方案，Firecracker microVM + 硬件可信根

2024 年 ETSI MEC Phase 4 规范新增了 Multi-Tenancy 相关的安全要求，要求所有 MEC 平台必须支持至少 namespace 级别的隔离，并建议关键场景使用硬件辅助隔离。

## 7. 实践建议

### 7.1 初学者入门路径

**第一步：理解 Linux namespace**。用 `unshare` 命令创建一个隔离的进程空间，直观感受 namespace 的效果。

```bash
# 创建独立的 PID + Network namespace
sudo unshare --pid --net --fork --mount-proc bash
# 在新 namespace 里看进程列表——只有 bash 自己
ps aux
# 看网络接口——只有 lo
ip addr
```

**第二步：用 Kubernetes NetworkPolicy 做网络隔离**。创建两个 namespace，配置策略使其互不可达，然后测试跨 namespace 的网络不通。

**第三步：尝试 Kata Containers**。在一个 K3s 集群里安装 Kata 作为 RuntimeClass，对比普通容器和 Kata 容器的启动时间和隔离效果。

### 7.2 具体调优建议

**不要过度隔离**。每多一层隔离就多一层性能开销。如果租户之间是同一公司的不同部门（互信），容器 + NetworkPolicy 就足够了。只有互不信任的租户（如运营商卖 MEC 算力给第三方）才需要 VM 级或硬件级隔离。

**GPU 隔离优先用 MIG**。如果硬件支持 MIG（A30/A100/H100），这是性能损耗最小、隔离最彻底的方案。不支持 MIG 时，time-slicing 是可接受的折中——但要告知租户这不是硬隔离。

**网络策略 default-deny 起步**。先拒绝所有跨 namespace 流量，再按需开放——而不是先全通再逐步收紧。这是安全最佳实践。

**监控逃逸指标**。部署 Falco 或 Tracee 做运行时安全监控，检测容器逃逸尝试（异常系统调用、特权提升等）。

## 参考文献

1. ETSI. (2024). MEC Phase 4: Multi-access Edge Computing Security Framework. GS MEC 009 v4.1.1.
2. Kata Containers. (2024). Architecture Document. https://katacontainers.io/docs/
3. Cilium. (2024). Network Policy Documentation. https://docs.cilium.io/
4. NVIDIA. (2024). Multi-Instance GPU User Guide. https://docs.nvidia.com/datacenter/tesla/mig-user-guide/
5. Intel. (2024). Intel SGX Developer Reference. https://www.intel.com/content/www/us/en/developer/tools/software-guard-extensions/overview.html
6. ARM. (2024). ARM Confidential Compute Architecture (CCA). https://www.arm.com/architecture/security-features/arm-confidential-compute-architecture
7. Firecracker. (2024). Firecracker MicroVM Documentation. https://firecracker-microvm.github.io/
8. Calico. (2024). Network Policy Tutorial. https://docs.tigera.io/calico/latest/network-policy/
9. Volcano. (2024). Queue and Fair Scheduling. https://volcano.sh/en/docs/
10. Zhang, T., et al. (2023). Multi-Tenant Edge Computing: Security Isolation Mechanisms and Performance Analysis. IEEE Transactions on Cloud Computing, 11(3), 2145-2160.