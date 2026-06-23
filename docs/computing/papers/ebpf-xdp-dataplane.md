# eBPF/XDP 数据平面编程在 IoT 网关中的应用

> **难度**：🟡 中级 | **领域**：网络编程、Linux 内核、数据平面 | **阅读时间**：约 20 分钟

## 日常类比

想象一个快递分拣中心。传统方式（iptables）是所有包裹都进入大楼，经过登记台、安检、分类室等层层处理后才送到对应出口——安全但慢。XDP 的做法相当于在大楼门口就放了一台智能机器人：包裹刚到门口，机器人扫一眼标签就能决定"这个直接转到 3 号出口""那个丢掉""这个需要进楼详细检查"——绝大部分包裹根本不用进楼。

在 IoT 网关场景中，一台设备可能需要处理数万个传感器的数据流，同时抵御网络攻击。eBPF/XDP 让我们在数据包到达内核网络栈之前就完成处理，实现百万级 pps（packets per second）的转发能力，而无需任何专用硬件。

## 1. eBPF 基础架构

### 1.1 什么是 eBPF

eBPF（extended Berkeley Packet Filter）是 Linux 内核中的一个可编程虚拟机，允许用户在不修改内核源码的情况下，在内核关键路径上注入自定义逻辑：

```
用户态                          内核态
+-----------------+    +-------------------------------------------+
| eBPF 程序 (C)   |    |                                           |
| -> LLVM 编译    |--->| 验证器 (Verifier)                          |
| -> 字节码 .o    |    |   |                                       |
+-----------------+    |   v                                       |
                       | JIT 编译 -> 原生机器码                      |
                       |   |                                       |
                       |   v                                       |
                       | 挂载到 Hook 点:                            |
                       |   - XDP (网卡驱动层)                       |
                       |   - TC (流量控制层)                         |
                       |   - kprobe (内核函数)                      |
                       |   - tracepoint (跟踪点)                    |
                       |   - socket (套接字层)                      |
                       +-------------------------------------------+
```

### 1.2 安全保证：验证器

eBPF 验证器在加载时静态分析程序，确保：无无限循环（所有循环必须有界）、无越界内存访问、无未初始化变量读取、程序在有限步内终止（默认 100 万条指令），且只访问允许的内核数据结构。

```c
// 这段代码会被验证器拒绝（无界循环）
int bad_program(struct xdp_md *ctx) {
    int i;
    for (i = 0; ; i++) {  // 无界循环 -> 拒绝
        // ...
    }
    return XDP_PASS;
}

// 有界循环可以通过验证
int good_program(struct xdp_md *ctx) {
    int i;
    #pragma unroll
    for (i = 0; i < 100; i++) {
        // 有界 -> 通过
    }
    return XDP_PASS;
}
```

## 2. XDP：极速数据平面

### 2.1 XDP Hook 点

XDP（eXpress Data Path）是 eBPF 在网络栈最底层的 hook 点，直接在网卡驱动收到数据包后执行：

```
数据包到达网卡
     |
     v
[XDP Hook] <-- eBPF 程序在这里执行
     |
     | XDP_PASS (继续进入内核网络栈)
     | XDP_DROP (丢弃，不进入内核)
     | XDP_TX   (从同一网卡发回)
     | XDP_REDIRECT (转发到另一网卡/CPU)
     |
     v
  内核网络栈 (skb 分配, 协议解析, iptables...)
```

### 2.2 三种 XDP 模式

| 模式 | 位置 | 性能 | 要求 |
|------|------|------|------|
| Native XDP | 网卡驱动内 | 最高（24M pps/核） | 驱动支持 |
| Generic XDP | skb 分配后 | 中等（3-5M pps/核） | 任何网卡 |
| Offloaded XDP | 网卡硬件上 | 线速（100G+） | 智能网卡 |

### 2.3 与 iptables 的性能对比

测试环境：Intel Xeon E-2278G, 10G NIC (ixgbe), 64B 包

```
丢包性能 (Drop all packets):
  iptables -j DROP:     约 2M pps/core
  nftables drop:        约 3M pps/core
  XDP_DROP (generic):   约 5M pps/core
  XDP_DROP (native):    约 24M pps/core
  XDP_DROP (offload):   约 40M pps/core

转发性能 (Forward packets):
  Linux bridge:         约 1M pps/core
  iptables FORWARD:     约 0.8M pps/core
  XDP_REDIRECT:         约 12M pps/core
```

## 3. IoT 网关实战：智能流量分类

### 3.1 场景描述

一个 IoT 网关需要处理来自数千个传感器的 UDP 数据包，同时丢弃已知恶意 IP 的流量（DDoS 防护），按设备 ID 将流量分发到不同处理队列，并统计每个设备的流量。

### 3.2 eBPF 程序实现

```c
// iot_gateway.bpf.c
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>

// 黑名单 Map（存储恶意 IP）
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10000);
    __type(key, __u32);    // IP 地址
    __type(value, __u64);  // 丢包计数
} blacklist SEC(".maps");

// 流量统计 Map（per-CPU 避免锁竞争）
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_HASH);
    __uint(max_entries, 65536);
    __type(key, __u32);    // 设备 ID
    __type(value, __u64);  // 字节数
} traffic_stats SEC(".maps");

SEC("xdp")
int iot_packet_filter(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    // 解析以太网头
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return XDP_PASS;

    // 解析 IP 头
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;

    // 黑名单检查（O(1) 哈希查找）
    __u32 src_ip = ip->saddr;
    __u64 *blocked = bpf_map_lookup_elem(&blacklist, &src_ip);
    if (blocked) {
        __sync_fetch_and_add(blocked, 1);
        return XDP_DROP;  // 直接丢弃，不进入内核
    }

    // UDP 流量统计
    if (ip->protocol == IPPROTO_UDP) {
        struct udphdr *udp = (void *)ip + (ip->ihl * 4);
        if ((void *)(udp + 1) > data_end)
            return XDP_PASS;

        // 假设 UDP payload 前 4 字节是设备 ID
        __u32 *device_id = (void *)(udp + 1);
        if ((void *)(device_id + 1) > data_end)
            return XDP_PASS;

        __u64 pkt_len = data_end - data;
        __u64 *bytes = bpf_map_lookup_elem(&traffic_stats, device_id);
        if (bytes) {
            __sync_fetch_and_add(bytes, pkt_len);
        } else {
            bpf_map_update_elem(&traffic_stats, device_id,
                               &pkt_len, BPF_ANY);
        }
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

### 3.3 用户态管理程序

```python
#!/usr/bin/env python3
# iot_gateway_ctrl.py - 用户态控制程序
from bcc import BPF
import ctypes
import time

# 加载 eBPF 程序
b = BPF(src_file="iot_gateway.bpf.c")
fn = b.load_func("iot_packet_filter", BPF.XDP)
b.attach_xdp("eth0", fn, 0)  # 0 = native mode

# 获取 Map 引用
blacklist = b.get_table("blacklist")
traffic_stats = b.get_table("traffic_stats")

# 添加黑名单 IP
def block_ip(ip_str):
    import socket, struct
    ip_int = struct.unpack("!I", socket.inet_aton(ip_str))[0]
    blacklist[ctypes.c_uint32(ip_int)] = ctypes.c_uint64(0)

# 添加一些恶意 IP
block_ip("192.168.1.100")
block_ip("10.0.0.50")

# 周期性打印统计
try:
    while True:
        time.sleep(5)
        print("=== Traffic Stats ===")
        for k, v in traffic_stats.items():
            print(f"  Device {k.value:#010x}: {v.value} bytes")
        print(f"=== Blocked IPs ===")
        for k, v in blacklist.items():
            import socket, struct
            ip = socket.inet_ntoa(struct.pack("!I", k.value))
            print(f"  {ip}: {v.value} packets dropped")
except KeyboardInterrupt:
    b.remove_xdp("eth0", 0)
```

## 4. DDoS 防护在边缘

### 4.1 速率限制

```c
// 基于令牌桶的速率限制
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 100000);
    __type(key, __u32);
    __type(value, struct rate_limit_entry);
} rate_limiter SEC(".maps");

struct rate_limit_entry {
    __u64 tokens;
    __u64 last_refill;
};

#define TOKENS_PER_SEC  1000  // 每秒允许 1000 个包
#define BUCKET_SIZE     100   // 突发容量

static __always_inline int check_rate_limit(__u32 src_ip) {
    struct rate_limit_entry *entry;
    entry = bpf_map_lookup_elem(&rate_limiter, &src_ip);

    __u64 now = bpf_ktime_get_ns();

    if (!entry) {
        struct rate_limit_entry new_entry = {
            .tokens = BUCKET_SIZE - 1,
            .last_refill = now,
        };
        bpf_map_update_elem(&rate_limiter, &src_ip, &new_entry, BPF_ANY);
        return 1;  // 允许
    }

    // 补充令牌
    __u64 elapsed_ns = now - entry->last_refill;
    __u64 new_tokens = (elapsed_ns * TOKENS_PER_SEC) / 1000000000ULL;
    if (new_tokens > 0) {
        entry->tokens += new_tokens;
        if (entry->tokens > BUCKET_SIZE)
            entry->tokens = BUCKET_SIZE;
        entry->last_refill = now;
    }

    // 消费令牌
    if (entry->tokens > 0) {
        entry->tokens--;
        return 1;  // 允许
    }
    return 0;  // 丢弃
}
```

### 4.2 SYN Flood 防护

XDP 可以在网卡驱动层实现 SYN Cookie，无需 TCP 连接表：

```
传统方式:                   XDP 方式:
SYN -> 内核 -> 分配连接     SYN -> XDP 计算 cookie
     -> 半连接队列                -> XDP_TX 发回 SYN-ACK
     (容易被打满)                  (无状态，无法被耗尽)
```

## 5. Cilium：eBPF 驱动的 IoT 网络

### 5.1 Cilium 在边缘

Cilium 是基于 eBPF 的 CNI 插件，在边缘 Kubernetes 集群中替代 kube-proxy 和 iptables：

| 传统 kube-proxy | Cilium eBPF |
|----------------|-------------|
| iptables 规则数随 Service 线性增长 | O(1) 哈希查找 |
| 连接跟踪在用户态 | 连接跟踪在内核 eBPF Map |
| Service 多时性能下降 | 万级 Service 性能不变 |
| 无法做 L7 策略 | 支持 HTTP/gRPC 过滤 |

### 5.2 IoT 特有场景

```yaml
# Cilium 网络策略：限制 IoT 设备只能访问 MQTT broker
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: iot-device-policy
spec:
  endpointSelector:
    matchLabels:
      app: iot-sensor
  egress:
  - toEndpoints:
    - matchLabels:
        app: mqtt-broker
    toPorts:
    - ports:
      - port: "1883"
        protocol: TCP
  - toCIDR:
    - 0.0.0.0/0
    toPorts:
    - ports:
      - port: "53"
        protocol: UDP  # 允许 DNS
```

## 6. BCC/libbpf 工具链

### 6.1 开发工具选择

| 工具 | 优势 | 劣势 | 适合场景 |
|------|------|------|---------|
| BCC (Python) | 快速原型、丰富的辅助函数 | 运行时编译、依赖大 | 调试、一次性分析 |
| libbpf (C) | CO-RE、无运行时依赖 | 开发复杂 | 生产部署 |
| libbpf-rs (Rust) | 类型安全、CO-RE | 生态较新 | Rust 项目 |
| cilium/ebpf (Go) | Go 生态集成好 | 性能略逊于 C | K8s 生态 |

### 6.2 CO-RE（Compile Once, Run Everywhere）

CO-RE 解决了 eBPF 程序在不同内核版本间的可移植性问题：

```c
// 使用 CO-RE 读取 task_struct 字段
// 即使不同内核版本字段偏移不同也能工作
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>

SEC("kprobe/do_sys_open")
int trace_open(struct pt_regs *ctx) {
    struct task_struct *task = (void *)bpf_get_current_task();

    // CO-RE 重定位：编译器记录字段访问，加载时自动修正偏移
    pid_t pid = BPF_CORE_READ(task, tgid);
    pid_t ppid = BPF_CORE_READ(task, real_parent, tgid);

    bpf_printk("pid=%d ppid=%d\n", pid, ppid);
    return 0;
}
```

## 7. 实践建议

### 7.1 初学者入门路径

1. 安装 bcc-tools，运行现成工具（tcptop、biolatency）感受 eBPF 能力
2. 用 BCC Python 写一个简单的 XDP 丢包程序
3. 在虚拟网卡（veth）上测试 XDP_REDIRECT
4. 学习 libbpf + CO-RE 编写可移植的生产级程序
5. 部署到实际边缘网关，配合 Prometheus 导出统计数据

### 7.2 具体调优建议

- **Map 选型**：高频读取用 BPF_MAP_TYPE_PERCPU_HASH 避免锁竞争
- **尾调用**：复杂逻辑用 bpf_tail_call 拆分，绕过指令数限制
- **批量操作**：用 bpf_map_lookup_batch 减少系统调用次数
- **AF_XDP**：需要用户态处理时，用 AF_XDP socket 零拷贝收包
- **BTF 启用**：确保内核开启 CONFIG_DEBUG_INFO_BTF，支持 CO-RE

### 7.3 边缘场景注意事项

- ARM 上的 eBPF JIT 性能略低于 x86，但仍远优于 iptables
- 低端设备（如 OpenWrt 路由器）内核可能未启用 BTF，需用旧版 BCC
- eBPF Map 内存占用需要规划，避免在内存受限设备上 OOM
- XDP 不支持所有网卡驱动，部署前检查 generic 模式是否满足性能需求

## 参考文献

1. Hoiland-Jorgensen, T., et al. "The eXpress Data Path: Fast Programmable Packet Processing in the Operating System Kernel." CoNEXT 2018.
2. Vieira, M., et al. "Fast Packet Processing with eBPF and XDP." ACM Computing Surveys, 2020.
3. Cilium Project. "eBPF-based Networking, Observability, Security." 2024. https://cilium.io/
4. Gregg, B. "BPF Performance Tools." Addison-Wesley, 2019.
5. Scholz, D., et al. "Performance Implications of Packet Filtering with Linux eBPF." IEEE NOMS, 2018.
6. libbpf Project. "libbpf: eBPF library for Linux." 2024. https://github.com/libbpf/libbpf
7. Cloudflare. "L4Drop: XDP DDoS Mitigations." 2024. https://blog.cloudflare.com/
8. Meta. "Katran: A high performance layer 4 load balancer." 2024. https://github.com/facebookincubator/katran
9. Andrii Nakryiko. "BPF CO-RE Reference Guide." 2024.
10. XDP Project. "XDP Tutorial." 2024. https://github.com/xdp-project/xdp-tutorial
