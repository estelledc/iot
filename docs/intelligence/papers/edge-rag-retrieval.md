---
schema_version: '1.0'
id: edge-rag-retrieval
title: 边缘 RAG：检索增强生成在边缘的实现
layer: 5
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - llm-quantization-gptq-awq
  - transformer-edge-deployment
tags:
  - RAG
  - 向量数据库
  - Embedding
  - 边缘LLM
  - 混合检索
  - SQLite-vec
  - 离线推理
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 边缘 RAG：检索增强生成在边缘的实现

> **难度**：🟡 中级 | **领域**：检索增强生成、向量数据库、边缘智能 | **阅读时间**：约 22 分钟

## 日常类比

维修工程师带手册去现场：不必把整本背下。**检索增强生成（Retrieval-Augmented Generation, RAG）** 像聪明助手——先翻到相关页（检索），再据此作答（生成）[1]。

边缘 RAG 的约束是：不能随时打电话回公司（弱网/离线），手册必须塞进工具箱（本地向量库），助手脑容量有限（量化小模型）。好处是快、数据不出设备。

## 摘要

本文对比云端与边缘 RAG，介绍 SQLite-vec / Qdrant 嵌入式向量库、轻量句向量模型、物联网（Internet of Things, IoT）手册分块、稠密+稀疏混合检索与端到端延迟优化。文中延迟与体积为单板机量级示意，需按机型实测[3][6][7]。

## 1. RAG 架构基础

### 1.1 标准流程

```
查询 → Embedding → 查询向量
文档 → 分块 → Embedding → 向量库 → Top-K
                              ↓
                    查询 + 上下文 → LLM → 回答
```

稠密检索（Dense Passage Retrieval 等）是现代开放域问答的基础组件之一[2]。

### 1.2 边缘 vs 云端

| 维度 | 云端 RAG（常见） | 边缘 RAG（常见） |
|------|------------------|------------------|
| 模型规模 | 很大 | 约 1–7B 量化 |
| 向量库规模 | 百万–十亿级 | 千–十万级 |
| Embedding 维 | 较高 | 约 256–384 |
| 检索延迟 | 毫秒–数十毫秒 | 本地毫秒级 |
| 生成延迟 | 相对快（强 GPU） | 常为秒级（CPU） |
| 网络 | 必需 | 可离线 |
| 隐私 | 需传查询/文档 | 可完全本地 |
| 知识更新 | 近实时 | 定期同步 |

### 1.3 适用场景

工业离线手册、医疗设备诊断（隐私）、车载弱网助手、偏远农业指导等——共同特点是**知识相对静态、延迟与隐私优先于百科广度**。

## 2. 边缘向量数据库

### 2.1 SQLite-vec

零依赖扩展、单文件，适合嵌入式知识库[3]：

```python
import sqlite3
import sqlite_vec
import struct

db = sqlite3.connect("knowledge.db")
db.enable_load_extension(True)
sqlite_vec.load(db)

db.execute("""
    CREATE VIRTUAL TABLE documents USING vec0(
        embedding float[384],
        +content TEXT,
        +source TEXT
    )
""")

def serialize_f32(vector):
    return struct.pack(f"{len(vector)}f", *vector)

def search(db, query_embedding, top_k=5):
    return db.execute(
        """
        SELECT content, source, distance FROM documents
        WHERE embedding MATCH ? ORDER BY distance LIMIT ?
        """,
        [serialize_f32(query_embedding), top_k],
    ).fetchall()
```

公开材料称在树莓派级硬件、万级 384 维向量上检索可达数毫秒量级；插入吞吐与库体积随维度/索引而变，部署前应基准测试[3]。

### 2.2 Qdrant 嵌入式

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(path="./qdrant_data")
client.create_collection(
    collection_name="iot_manuals",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)
```

过滤（按设备型号）比纯 FAISS 更省事，但运行时与磁盘占用高于 SQLite-vec[6]。

### 2.3 向量库对比（示意）

| 特性 | SQLite-vec | Qdrant 嵌入式 | FAISS | ChromaDB |
|------|-----------|---------------|-------|----------|
| 依赖 | 极轻 | Rust 运行时 | numpy 等 | Python 生态 |
| 内存倾向 | 低 | 中 | 中 | 偏高 |
| 过滤 | SQL | 丰富 | 弱 | 基础 |
| 持久化 | 自动 | 自动 | 常需自管 | 自动 |
| 设备倾向 | MCU 网关 / RPi | RPi / Jetson | Jetson+ | 开发机 / 强边缘 |

## 3. 边缘 Embedding

### 3.1 轻量模型选型（公开榜单量级）

| 模型 | 维 | 参数量级 | 任务倾向 |
|------|----|---------|---------|
| all-MiniLM-L6-v2 | 384 | 约 22M | 通用英文[4] |
| all-MiniLM-L12-v2 | 384 | 约 33M | 精度优先 |
| BGE-small 系列 | 384/512 | 约 24–33M | 中英检索[5][9] |
| E5-small / GTE-small | 384 | 约 33M | 多语/平衡 |

MTEB 等分数随版本变化；边缘应同时看延迟与领域适配，而非只追榜[5][9]。

### 3.2 ONNX 推理骨架

```python
import onnxruntime as ort
import numpy as np
from tokenizers import Tokenizer

class EdgeEmbedder:
    def __init__(self, model_path, tokenizer_path, threads=4):
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = threads
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(
            model_path, providers=["CPUExecutionProvider"], sess_options=opts
        )
        self.tokenizer = Tokenizer.from_file(tokenizer_path)
        self.tokenizer.enable_truncation(max_length=128)
        self.tokenizer.enable_padding(length=128)

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        enc = self.tokenizer.encode_batch(texts)
        input_ids = np.array([e.ids for e in enc], dtype=np.int64)
        mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
        emb = self.session.run(
            None, {"input_ids": input_ids, "attention_mask": mask}
        )[0]
        m = mask[:, :, None].astype(np.float32)
        pooled = (emb * m).sum(1) / m.sum(1)
        return pooled / np.linalg.norm(pooled, axis=1, keepdims=True)
```

Sentence-BERT 类双塔是句向量主流范式之一[4]。

## 4. 文档分块

| 方法 | 优点 | 缺点 | 适用 |
|------|------|------|------|
| 固定长度 | 简单 | 易切断语义 | 结构化文本 |
| 句子分割 | 语义较完整 | 长度不均 | 叙述性手册 |
| 递归分割 | 灵活 | 实现复杂 | 通用 |
| 语义分割 | 边界更好 | 需模型 | 高精度 |

IoT 手册建议：按章节标题切；表格整块保留；块长约数百字符并带小重叠——过长检索糊，过短缺上下文。

## 5. 混合检索

稠密向量抓语义，BM25 抓型号/错误码等关键词；线性融合常优于单路[2][7]。

```python
final_scores = alpha * dense_norm + (1 - alpha) * sparse_norm
```

\(\alpha\) 需按语料调；错误码密集的手册可略降 \(\alpha\)。

## 6. 端到端系统

```python
class EdgeRAG:
    def __init__(self, embedder, vector_db, llm_path):
        from llama_cpp import Llama
        self.embedder, self.db = embedder, vector_db
        self.llm = Llama(model_path=llm_path, n_ctx=2048, n_threads=4, n_gpu_layers=0)

    def query(self, question, top_k=3):
        qv = self.embedder.encode(question)
        results = search(self.db, qv[0], top_k=top_k)
        context = "\n---\n".join(r[0] for r in results)
        prompt = f"基于参考资料回答；若无相关信息请说明。\n资料：\n{context}\n问题：{question}\n回答："
        out = self.llm(prompt, max_tokens=256, temperature=0.1)
        return {"answer": out["choices"][0]["text"], "sources": [r[1] for r in results]}
```

### 延迟优化

| 手段 | 效果倾向 | 难度 |
|------|---------|------|
| Embedding 缓存 | 省重复编码 | 低 |
| 向量量化 (PQ) | 加速检索，精度略损 | 中 |
| 热门查询预计算 | 近零检索 | 低 |
| 流式生成 | 降低首 token 等待 | 中 |
| 模型预热 | 减冷启动 | 低 |
| 无生成降级 | 只返回片段，毫秒级 | 低 |

小上下文窗口下 Top-K=3 往往比 K=5 更稳，避免塞爆上下文[7]。

### 云边协作

有网：边缘检索 + 云端大模型；离线：本地小模型；混合：先本地快答，再云端精修。

## 7. 实践建议

1. PC 上用 LangChain 等跑通 RAG 闭环。
2. 换成 MiniLM + SQLite-vec + 量化小模型。
3. 在目标单板机测 embedding / 检索 / 生成三段延迟。
4. 调分块与混合检索 \(\alpha\)。
5. 加缓存与离线降级。

## 8. 局限、挑战与可改进方向

### 1. 生成才是瓶颈

**局限**：检索毫秒级，1–3B 模型 CPU 生成常要数秒，体验像"卡死"[7][10]。
**改进**：流式输出、更小专用模型、检索直出、热问题缓存。

### 2. 幻觉与过时手册

**局限**：小模型更易无视检索结果胡编；现场固件与手册版本不一致[1][7]。
**改进**：强制引用片段；版本化索引；答不出就说不知道。

### 3. 中文工业术语

**局限**：通用英文句向量对设备型号、故障码召回弱[5][9]。
**改进**：领域微调 / 中文小模型；混合 BM25；同义词表。

### 4. 更新与一致性

**局限**：边缘索引定期同步，窗口期内答旧知识。
**改进**：差分更新包；查询时带知识版本号；关键安全规程走强校验通道。

## 参考文献

[1] P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," NeurIPS, 2020.
[2] V. Karpukhin et al., "Dense Passage Retrieval for Open-Domain Question Answering," EMNLP, 2020.
[3] SQLite-vec, "A vector search SQLite extension," GitHub, 2024.
[4] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," EMNLP, 2019.
[5] S. Xiao et al., "C-Pack: Packaged Resources To Advance General Chinese Embedding," arXiv, 2023.
[6] Qdrant, "Qdrant: Vector Search Engine," Documentation, 2024.
[7] Y. Gao et al., "Retrieval-Augmented Generation for Large Language Models: A Survey," arXiv, 2024.
[8] X. Ma et al., "Fine-Tuning LLaMA for Multi-Stage Text Retrieval," SIGIR, 2024.
[9] J. Chen et al., "BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity," arXiv, 2024.
[10] Edge Impulse 等, "Deploying RAG on Edge Devices" 技术博文与实践报告, 2024.
