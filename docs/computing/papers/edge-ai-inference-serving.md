# 边缘 AI 推理服务化

> **难度**：🟡 中级 | **领域**：模型服务、推理优化、边缘计算 | **阅读时间**：约 22 分钟

## 日常类比

你去奶茶店点单。如果每杯奶茶都由一个人从头做到尾（接单、煮茶、加料、封口），效率很低。成熟的奶茶店会把流程拆成工位：一个人专门煮茶底，一个人专门加料，一个人专门封口打包。更聪明的做法是，热门款（珍珠奶茶）提前备好半成品，冷门款才现做。

AI 推理服务化做的事情类似：把训练好的模型"摆上柜台"，接收请求、排队、批量处理、返回结果。在边缘场景下，这个"柜台"资源有限——可能只有一块手机芯片大小的 NPU——所以如何在有限资源上高效地"出餐"，是核心问题。

和云端不同，边缘推理还多了一个约束：延迟 SLA。云端的用户可以等 200ms，但工厂的缺陷检测可能只允许 20ms，自动驾驶的感知模块更是要求 <10ms。

## 1. 模型服务框架概览

### 1.1 三大主流框架

| 框架 | 维护者 | 核心特点 | 资源占用 |
|------|--------|----------|---------|
| TensorFlow Serving | Google | gRPC/REST API，TF 生态原生 | 中等（~500MB 镜像） |
| Triton Inference Server | NVIDIA | 多框架支持，动态 batching | 较大（~2GB+ 镜像） |
| ONNX Runtime | Microsoft | 跨平台，EP 插件架构 | 最小（~100MB 核心） |

在边缘场景中，ONNX Runtime 因为体积小、支持多种硬件加速后端（Execution Providers）而最受欢迎。Triton 在有 NVIDIA GPU 的边缘服务器上表现最好。TF Serving 逐渐退出边缘主流。

### 1.2 ONNX Runtime 的 Execution Provider 架构

```
               ┌──────────────────┐
               │  ONNX Runtime    │
               │  统一推理接口     │
               └──────┬───────────┘
                      │
      ┌───────────────┼───────────────┐
      ▼               ▼               ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ CPU EP   │   │ CUDA EP  │   │ TensorRT │
│ (x86/ARM)│   │ (NVIDIA) │   │ EP       │
└──────────┘   └──────────┘   └──────────┘
      ▼               ▼
┌──────────┐   ┌──────────┐
│ OpenVINO │   │ QNN EP   │
│ EP(Intel)│   │(Qualcomm)│
└──────────┘   └──────────┘
```

同一个 ONNX 模型可以在不同硬件上运行，只需切换 EP：

```python
import onnxruntime as ort

# CPU 推理
session_cpu = ort.InferenceSession("yolov8n.onnx",
    providers=["CPUExecutionProvider"])

# NVIDIA GPU 推理（TensorRT 加速）
session_gpu = ort.InferenceSession("yolov8n.onnx",
    providers=["TensorrtExecutionProvider", "CUDAExecutionProvider"])

# Qualcomm NPU 推理
session_npu = ort.InferenceSession("yolov8n.onnx",
    providers=["QNNExecutionProvider"])

# 统一推理接口
input_name = session_cpu.get_inputs()[0].name
result = session_cpu.run(None, {input_name: input_data})
```

## 2. 边缘推理优化技术

### 2.1 动态 Batching

单条推理请求的 GPU 利用率通常只有 10-30%。动态 batching 把短时间内到达的多个请求合并成一个 batch 一起推理：

```python
import asyncio
import time
from collections import deque

class DynamicBatcher:
    """边缘场景的动态 batching 服务"""
    def __init__(self, model_session, max_batch=8, max_wait_ms=5):
        self.session = model_session
        self.max_batch = max_batch
        self.max_wait_ms = max_wait_ms
        self.queue = deque()
        self.input_name = model_session.get_inputs()[0].name

    async def infer(self, input_data):
        future = asyncio.get_event_loop().create_future()
        self.queue.append((input_data, future))

        if len(self.queue) >= self.max_batch:
            await self._flush()
        else:
            # 等待更多请求或超时
            await asyncio.sleep(self.max_wait_ms / 1000)
            if not future.done():
                await self._flush()

        return await future

    async def _flush(self):
        batch_items = []
        while self.queue and len(batch_items) < self.max_batch:
            batch_items.append(self.queue.popleft())

        import numpy as np
        inputs = np.stack([item[0] for item in batch_items])
        results = self.session.run(None, {self.input_name: inputs})

        for i, (_, future) in enumerate(batch_items):
            if not future.done():
                future.set_result(results[0][i])
```

Triton 的动态 batching 在 Jetson Orin（64GB）上实测：YOLOv8-n 单条推理 8ms，batch=8 时总耗时 15ms——吞吐量提升 4.3 倍。

### 2.2 模型缓存与预热

边缘设备内存有限，不可能把所有模型同时加载。模型缓存策略：

| 策略 | 适用场景 | 实现方式 |
|------|----------|---------|
| 常驻加载 | 核心模型（<3 个） | 启动时加载，永不卸载 |
| LRU 缓存 | 中等模型数（3-10 个） | 按最近使用淘汰 |
| 按需加载 | 大量模型（>10 个） | 请求时加载，空闲时卸载 |

模型预热（warm-up）是容易被忽略的环节。首次推理通常比后续慢 5-50 倍（因为 GPU kernel 编译、内存分配等）。生产环境必须在模型上线前用虚拟输入跑几次预热。

## 3. 硬件加速选型

### 3.1 NPU/GPU/VPU 对比

2024-2025 年边缘 AI 硬件市场的主要选手：

| 硬件 | 代表产品 | INT8 算力 | 功耗 | 适用场景 |
|------|---------|-----------|------|---------|
| 边缘 GPU | Jetson Orin NX 16GB | 100 TOPS | 15-25W | 多任务推理 |
| NPU | Qualcomm Cloud AI 100 | 400 TOPS | 25-75W | 高吞吐推理 |
| VPU | Intel Movidius (已停产) | 4 TOPS | 1-2W | 超低功耗视觉 |
| NPU SoC | 瑞芯微 RK3588 | 6 TOPS | 5-8W | 低成本边缘盒子 |
| Apple NPU | M4 Neural Engine | 38 TOPS | 集成 | 消费电子 |

选型的核心不是看 TOPS 数字，而是看"每瓦特有效吞吐量"。一个 400 TOPS 的芯片如果只有 30% 的算子覆盖率（其余 fallback 到 CPU），实际性能可能不如 100 TOPS 但覆盖率 90% 的芯片。

### 3.2 量化对推理性能的影响

在 Jetson Orin NX 上对 YOLOv8-n（目标检测）的实测：

```
精度      | 模型大小 | 延迟(ms) | mAP@0.5 | 吞吐(FPS)
----------|---------|---------|---------|----------
FP32      | 12.2 MB | 8.1     | 37.3    | 123
FP16      | 6.1 MB  | 4.2     | 37.2    | 238
INT8(PTQ) | 3.2 MB  | 2.8     | 36.1    | 357
INT8(QAT) | 3.2 MB  | 2.8     | 37.0    | 357
```

INT8 量化带来 2.9 倍加速，精度损失仅 0.3%（QAT 方式）。对于边缘场景，FP16 是安全的默认选择，INT8 需要验证精度后再上线。

## 4. A/B 测试与多模型管理

### 4.1 边缘 A/B 测试的挑战

云端 A/B 测试可以用负载均衡器按比例分流。边缘场景的困难在于：

- 每个边缘节点的数据分布可能不同（工厂 A 和工厂 B 的产品不一样）
- 网络不稳定，分流规则更新可能延迟
- 需要本地收集指标，定期上报

```yaml
# 边缘 A/B 测试配置示例
model_serving:
  default_model: "defect_detector_v2"
  ab_test:
    name: "v2_vs_v3_accuracy"
    variants:
      - model: "defect_detector_v2"
        weight: 70          # 70% 流量
        metrics: ["latency_p99", "precision", "recall"]
      - model: "defect_detector_v3"
        weight: 30
        metrics: ["latency_p99", "precision", "recall"]
    duration_hours: 168     # 一周
    min_samples: 10000
    rollback_if:
      precision_drop: 0.02  # 精度下降超过 2% 自动回退
```

### 4.2 多模型编排

一个边缘节点上往往需要同时运行多个模型。以智能工厂质检为例：

```
摄像头帧 → [目标检测] → 裁剪 ROI → [缺陷分类] → 结果
                                  → [OCR 识别序列号] → 追溯
```

模型编排需要解决资源竞争问题。Triton 支持 Model Ensemble（模型流水线），可以自动管理模型间的数据传递和 GPU 显存共享。

## 5. 延迟 SLA 管理

### 5.1 延迟预算分解

一个端到端推理请求的延迟组成：

```
总延迟 = 网络传输 + 预处理 + 队列等待 + 推理计算 + 后处理 + 返回

示例（目标检测，SLA = 50ms）：
  网络传输：5ms（局域网内）
  图像解码 + resize：3ms
  队列等待：0-10ms（取决于负载）
  推理（YOLOv8-n FP16）：4ms
  NMS 后处理：2ms
  结果返回：1ms
  ──────────────
  总计：15-25ms（预留 25ms 余量给突发）
```

### 5.2 过载保护策略

当请求速率超过处理能力时，三种策略：

1. **丢帧**：跳过部分输入帧（视频场景常用，从 30fps 降到 15fps）
2. **降级推理**：切换到更小的模型（YOLOv8-n → YOLOv8-pico）
3. **排队限流**：设置队列长度上限，超出直接拒绝

```python
class AdaptiveInferenceManager:
    """根据延迟 SLA 自动切换模型"""
    def __init__(self, sla_ms=50):
        self.sla_ms = sla_ms
        self.models = {
            "high": load_model("yolov8s.onnx"),   # 精度高，慢
            "medium": load_model("yolov8n.onnx"),  # 平衡
            "low": load_model("yolov8pico.onnx"),  # 快，精度低
        }
        self.current_tier = "medium"
        self.latency_window = []

    def maybe_switch(self, last_latency_ms):
        self.latency_window.append(last_latency_ms)
        if len(self.latency_window) > 100:
            self.latency_window.pop(0)

        p95 = sorted(self.latency_window)[int(len(self.latency_window)*0.95)]

        if p95 > self.sla_ms * 0.8 and self.current_tier != "low":
            self.current_tier = "low"   # 降级
        elif p95 < self.sla_ms * 0.5 and self.current_tier != "high":
            self.current_tier = "high"  # 升级
```

## 6. KServe 与边缘 Kubernetes

### 6.1 KServe 简介

KServe（原 KFServing）是 Kubernetes 上的模型推理标准。它提供：

- 统一的 InferenceService CRD
- 自动缩放（含缩至零）
- Canary 发布和流量分割
- 支持自定义 Transformer（预/后处理）

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: defect-detector
spec:
  predictor:
    model:
      modelFormat:
        name: onnx
      storageUri: "s3://models/defect-detector-v3"
      resources:
        limits:
          cpu: "2"
          memory: "4Gi"
          nvidia.com/gpu: "1"
        requests:
          cpu: "1"
          memory: "2Gi"
  transformer:
    containers:
    - image: preprocess:v1
      name: image-preprocessor
```

### 6.2 边缘 Kubernetes 的适配

在 KubeEdge/K3s 上运行 KServe 需要注意：

- **Knative 依赖**：KServe 依赖 Knative Serving，资源开销约 500MB+ 内存。边缘可用 KServe Raw Deployment 模式跳过 Knative。
- **镜像预拉取**：边缘带宽有限，2GB+ 的 Triton 镜像拉取可能超时。建议用边缘镜像仓库（如 Harbor edge）预分发。
- **GPU 调度**：K3s 通过 NVIDIA Device Plugin 暴露 GPU 资源，需要额外安装 `k3s-gpu-support`。

## 7. 实践建议

### 7.1 初学者入门路径

**第一步**：在本地用 ONNX Runtime 跑一个预训练模型（如 MobileNetV2 图像分类），感受"模型即服务"的概念。不需要训练，直接用 Hugging Face 上的 ONNX 模型。

**第二步**：用 FastAPI 包装成 HTTP 服务，加上动态 batching 逻辑。用 `wrk` 或 `hey` 做压测，观察吞吐量和延迟的关系。

**第三步**：尝试在 Jetson 或树莓派上部署，体验硬件加速（TensorRT / NNAPI）和资源约束的差异。

**第四步**：用 Docker Compose 编排多模型流水线（检测 + 分类），理解模型编排的复杂性。

### 7.2 具体调优建议

**先 profile 再优化**。用 ONNX Runtime 的 profiling 功能找到耗时最长的算子，而不是盲目量化。

```python
# 开启 profiling
options = ort.SessionOptions()
options.enable_profiling = True
session = ort.InferenceSession("model.onnx", options)
# 推理后查看 profile 文件
```

**批大小不是越大越好**。边缘场景中，batch=4 往往是甜蜜点——GPU 利用率足够高，单条延迟增加有限。batch=32 虽然吞吐更高，但单条延迟会膨胀到不可接受。

**模型格式标准化**。不管训练框架是什么（PyTorch/TF/PaddlePaddle），统一导出为 ONNX 格式上线。这样服务化框架只需要适配一种格式，运维复杂度大幅降低。

**监控不能少**。至少采集四个指标：推理延迟（P50/P95/P99）、吞吐量（QPS）、GPU 利用率、队列深度。用 Prometheus + Grafana 可视化，设置告警阈值。

## 参考文献

1. NVIDIA. (2024). Triton Inference Server Documentation. https://docs.nvidia.com/deeplearning/triton-inference-server/
2. Microsoft. (2024). ONNX Runtime Performance Tuning Guide. https://onnxruntime.ai/docs/performance/
3. KServe. (2024). KServe Documentation — ModelMesh and Raw Deployment. https://kserve.github.io/
4. NVIDIA. (2024). Jetson Orin NX Module Data Sheet. https://developer.nvidia.com/embedded/
5. Qualcomm. (2024). Cloud AI 100 Inference Accelerator. https://www.qualcomm.com/products/technology/processors/cloud-artificial-intelligence/
6. Ultralytics. (2024). YOLOv8 Benchmarks on Edge Devices. https://docs.ultralytics.com/
7. TensorFlow. (2024). TensorFlow Serving Architecture Overview. https://www.tensorflow.org/tfx/serving/architecture
8. Chen, Y., et al. (2023). Dynamic Batching for Edge Inference: A Survey. IEEE Internet of Things Journal, 10(15), 13421-13435.
9. Wang, X., et al. (2024). Adaptive Model Serving at the Edge. ACM Computing Surveys, 56(3), 1-38.
10. CNCF. (2024). KServe: Serverless Inferencing on Kubernetes. https://www.cncf.io/projects/kserve/
