---
schema_version: '1.0'
id: graph-neural-network-iot
title: 图神经网络在 IoT 中的应用
layer: 5
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - edge-anomaly-detection
  - federated-learning-iot
tags:
  - GNN
  - GCN
  - 时空图
  - 交通预测
  - 传感器网络
  - 图异常检测
  - 边缘部署
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 图神经网络在 IoT 中的应用

> **难度**：🟡 中级 | **领域**：图神经网络、IoT 网络分析、时空预测 | **阅读时间**：约 22 分钟

## 日常类比

地铁网络里，一站拥挤不只看本站——上游挤了，你这站很快也会挤。把每站当孤立时间序列，会丢掉"邻居效应"。

**图神经网络（Graph Neural Network, GNN）** 让每个节点询问邻居再更新自己。物联网（Internet of Things, IoT）传感器网、电网、路网天然是图，GNN 是匹配的归纳偏置[1][10]。

## 摘要

本文介绍消息传递、图卷积网络（Graph Convolutional Network, GCN）/ 图注意力网络（Graph Attention Network, GAT）/ GraphSAGE，说明如何把 IoT 建成图，并覆盖时空 GNN 交通预测、图自编码异常检测、联邦 GNN 与边缘压缩部署。METR-LA 等表中误差为文献报告值，换传感器拓扑需重测[4][5][10]。

## 1. GNN 基础

### 1.1 消息传递

```python
import torch
import torch.nn as nn

class SimpleGNNLayer(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.linear = nn.Linear(in_dim, out_dim)

    def forward(self, x, adj):
        # x: [N, F], adj: 归一化邻接
        return torch.relu(self.linear(torch.matmul(adj, x)))
```

### 1.2 主流架构

| 架构 | 聚合 | 特点 | 复杂度倾向 |
|------|------|------|-----------|
| GCN | 归一化均值 | 简单高效[1] | \(O(E\cdot d)\) |
| GAT | 注意力加权 | 自适应邻居权重[2] | 更高 |
| GraphSAGE | 采样聚合 | 可扩展大图[3] | 与采样数相关 |

### 1.3 GCN 骨架

```python
import torch.nn.functional as F

class GCN(nn.Module):
    def __init__(self, in_dim, hidden_dim, out_dim, n_layers=2, dropout=0.5):
        super().__init__()
        self.layers = nn.ModuleList([nn.Linear(in_dim, hidden_dim)])
        for _ in range(n_layers - 2):
            self.layers.append(nn.Linear(hidden_dim, hidden_dim))
        self.layers.append(nn.Linear(hidden_dim, out_dim))
        self.dropout = dropout

    def forward(self, x, adj_norm):
        for layer in self.layers[:-1]:
            x = F.relu(layer(torch.matmul(adj_norm, x)))
            x = F.dropout(x, self.dropout, training=self.training)
        return self.layers[-1](torch.matmul(adj_norm, x))
```

GAT 用可学习注意力替代固定归一化，适合邻居重要性不均的设备网[2]；大图优先 GraphSAGE 邻居采样[3]。

## 2. IoT 网络建模为图

| 图类型 | IoT 场景 | 节点 | 边 |
|--------|---------|------|-----|
| 静态同构 | 固定传感器网 | 传感器 | 物理/通信连接 |
| 动态图 | 移动设备 | 设备 | 时变链路 |
| 异构图 | 智能家居 | 多类型设备 | 多类型关系 |
| 时空图 | 交通/环境场 | 路口/站点 | 道路/相关边 |
| 超图 | 群组通信 | 设备 | 多对多 |

边可来自物理距离、相关系数、工艺拓扑或因果先验——**边定义往往比层数更影响效果**。

```python
from torch_geometric.data import Data

def build_iot_graph(devices, connections, features):
    x = torch.stack([torch.tensor(features[d["id"]]) for d in devices])
    edge_index = torch.tensor(
        [[c[0] for c in connections], [c[1] for c in connections]], dtype=torch.long
    )
    edge_attr = torch.tensor([c[2] for c in connections], dtype=torch.float)
    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
```

## 3. 时空 GNN 与交通预测

时空图卷积网络（Spatio-Temporal GCN, STGCN）交替做时间卷积与空间图卷积[4]；Graph WaveNet、DCRNN 等进一步建模扩散与自适应邻接[5][10]。

### METR-LA 类结果（文献报告，15 分钟预测量级）

| 模型 | MAE 量级 | 参数量级 | 边缘推理倾向 |
|------|---------|---------|-------------|
| 历史平均 | 较高 | 0 | 极快 |
| LSTM | 中 | 数十万 | 快 |
| GCN+LSTM | 中低 | 更高 | 中 |
| STGCN | 较低 | 约百万 | 中[4] |
| Graph WaveNet | 更低 | 更高 | 较慢[5] |
| DCRNN | 低 | 较高 | 较慢 |

绝对 MAE/RMSE 以原论文与数据划分为准；Jetson 延迟随实现与批大小变化。

## 4. 图上的异常检测

图自编码器：正常节点重建误差小；"单点读数正常但相对邻居异常"时，GNN 比独立检测器更敏感。

```python
class GNNAnomalyDetector(nn.Module):
    def __init__(self, encoder, decoder):
        super().__init__()
        self.encoder, self.decoder = encoder, decoder

    def detect(self, x, adj, threshold=None):
        z = self.encoder(x, adj)
        x_recon = self.decoder(z, adj)
        err = ((x - x_recon) ** 2).mean(dim=-1)
        if threshold is None:
            threshold = err.mean() + 3 * err.std()
        return err > threshold, err
```

| 方法倾向 | 相对能力 | 说明 |
|----------|---------|------|
| 阈值规则 | 基线 | 无拓扑 |
| Isolation Forest | 中 | 忽略图结构 |
| LSTM-AE | 中高 | 有时序、无邻居 |
| GNN-AE | 高（上下文异常） | 依赖图质量 |
| 时空 GNN-AE | 更高 | 成本上升 |

表中 Precision/Recall 若引自单次实验，只能作相对排序，不能当现场 SLA。

## 5. 联邦 GNN

电网分区、城际交通、多工厂拓扑数据常不能集中。FedGraphNN 等系统探索子图联邦训练[7]：本地在子图上更新，聚合参数——但跨客户端边缺失会导致结构偏差，需特殊处理。

## 6. 轻量部署

| 技术 | 压缩倾向 | 精度风险 | 场景 |
|------|---------|---------|------|
| 知识蒸馏 | 数倍–十余倍 | 低–中 | 通用 |
| 邻居/子图采样 | 数倍 | 中 | 大图 |
| INT8 量化 | ~4× | 通常较低 | 边缘 |
| 剪枝 | 数倍 | 低–中 | 稀疏图 |
| 减层 | 数倍 | 过平滑前有效 | 延迟敏感 |

导出时可用稠密/稀疏矩阵乘替代框架私有算子，便于 ONNX / TensorRT。百节点小图在 Jetson 级可达毫秒级推理，视层数与特征维而定[8][9]。

## 7. 实践建议

1. PyTorch Geometric 跑通 Cora 节点分类[8]。
2. 手写一层消息传递，确认邻接归一化。
3. 用 METR-LA 等公开交通数据建时空图[4][10]。
4. 对比 STGCN 与纯 LSTM。
5. 导出 ONNX，在目标边缘板测延迟与内存。

**调参要点**：2–3 层通常够用，更深易过平滑；邻接必须归一化；动态拓扑宜定期重建而非每步全量改边。

## 8. 局限、挑战与可改进方向

### 1. 边定义主观

**局限**：错误相关边会传播噪声，使"图优势"变成负迁移。
**改进**：多候选图对比；可学习自适应邻接[5]；物理拓扑与数据驱动边融合。

### 2. 过平滑与扩展性

**局限**：层数增加后节点表示趋同；全图训练在万级以上节点吃力[1][3]。
**改进**：残差/Jumping Knowledge；GraphSAGE/ClusterGCN 采样。

### 3. 动态与异构 IoT

**局限**：设备上下线、链路闪断使静态邻接失真；异构节点类型需更复杂模型。
**改进**：动态图/时序边；异构 GNN；缺失邻居的鲁棒聚合。

### 4. 联邦场景的切边问题

**局限**：组织边界切断跨域边，联邦 GNN 效果可能差于集中图[7]。
**改进**：安全的边界边摘要；分层图；仅共享非敏感聚合统计。

## 参考文献

[1] T. N. Kipf and M. Welling, "Semi-Supervised Classification with Graph Convolutional Networks," ICLR, 2017.
[2] P. Veličković et al., "Graph Attention Networks," ICLR, 2018.
[3] W. Hamilton et al., "Inductive Representation Learning on Large Graphs," NeurIPS, 2017.
[4] B. Yu et al., "Spatio-Temporal Graph Convolutional Networks: A Deep Learning Framework for Traffic Forecasting," IJCAI, 2018.
[5] Z. Wu et al., "Graph WaveNet for Deep Spatial-Temporal Graph Modeling," IJCAI, 2019.
[6] L. Zhao et al., "T-GCN: A Temporal Graph Convolutional Network for Traffic Prediction," IEEE TITS, 2020.
[7] C. He et al., "FedGraphNN: A Federated Learning System for Graph Neural Networks," arXiv, 2021.
[8] M. Fey and J. E. Lenssen, "Fast Graph Representation Learning with PyTorch Geometric," ICLR Workshop, 2019.
[9] M. Wang et al., "Deep Graph Library: A Graph-Centric, Highly-Performant Package for Graph Neural Networks," arXiv, 2019.
[10] W. Jiang and J. Luo, "Graph Neural Network for Traffic Forecasting: A Survey," Expert Systems with Applications, 2022.
