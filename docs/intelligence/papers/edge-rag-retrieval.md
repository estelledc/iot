# 边缘 RAG：检索增强生成在边缘的实现

> **难度**：🟡 中级 | **领域**：检索增强生成、向量数据库、边缘智能 | **阅读时间**：约 20 分钟

## 日常类比

想象你是一个维修工程师，带着一本厚厚的设备手册去现场维修（离线场景）。传统做法是把整本手册背下来（把所有知识塞进模型），但这不现实。RAG 的做法是：你带着手册（知识库）和一个聪明的助手（生成模型），遇到问题时助手先帮你翻到相关页面（检索），然后基于这几页内容给你解答（生成）。

边缘 RAG 的挑战在于：你不能打电话回公司查资料（没有云端连接），手册必须装在你的工具箱里（本地向量数据库），而且助手的脑容量有限（小模型）。但好处是响应快、不依赖网络、数据不出设备。

## 1. RAG 架构基础

### 1.1 标准 RAG 流程

```
用户查询 -> [Embedding 模型] -> 查询向量
                                    |
                                    v
知识文档 -> [分块] -> [Embedding] -> 向量数据库 -> Top-K 检索
                                                      |
                                                      v
                                    查询 + 检索结果 -> [LLM] -> 回答
```

### 1.2 边缘 RAG vs 云端 RAG

| 维度 | 云端 RAG | 边缘 RAG |
|------|---------|---------|
| 模型大小 | 70B+ | 1-7B (量化) |
| 向量库规模 | 百万-十亿级 | 千-十万级 |
| Embedding 维度 | 768-4096 | 256-384 |
| 检索延迟 | 10-50 ms | 5-20 ms (本地) |
| 生成延迟 | 100-500 ms | 500-3000 ms |
| 网络依赖 | 必须 | 无 |
| 数据隐私 | 需传输 | 完全本地 |
| 知识更新 | 实时 | 定期同步 |

### 1.3 边缘 RAG 适用场景

- 工业设备维护手册查询（离线工厂环境）
- 医疗设备故障诊断（隐私敏感）
- 智能家居语音助手（低延迟要求）
- 车载信息系统（网络不稳定）
- 农业 IoT 种植指导（偏远地区无网络）

## 2. 边缘向量数据库

### 2.1 SQLite-vec

SQLite-vec 是 SQLite 的向量搜索扩展，零依赖、单文件、适合嵌入式：

```python
import sqlite3
import sqlite_vec
import struct
import numpy as np

# 初始化数据库
db = sqlite3.connect("knowledge.db")
db.enable_load_extension(True)
sqlite_vec.load(db)

# 创建向量表 (384 维，匹配 all-MiniLM-L6-v2)
db.execute("""
    CREATE VIRTUAL TABLE documents USING vec0(
        embedding float[384],
        +content TEXT,
        +source TEXT
    )
""")

# 插入文档向量
def insert_document(db, embedding, content, source):
    db.execute(
        "INSERT INTO documents(embedding, content, source) VALUES (?, ?, ?)",
        [serialize_f32(embedding), content, source]
    )

def serialize_f32(vector):
    """将 numpy 数组序列化为 bytes"""
    return struct.pack(f"{len(vector)}f", *vector)

# 相似度搜索
def search(db, query_embedding, top_k=5):
    results = db.execute("""
        SELECT content, source, distance
        FROM documents
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT ?
    """, [serialize_f32(query_embedding), top_k]).fetchall()
    return results

# 性能基准 (RPi 4, 10000 文档, 384维):
# - 插入: ~2000 docs/s
# - 搜索: ~3 ms (top-5)
# - 数据库大小: ~15 MB
```

### 2.2 Qdrant (嵌入式模式)

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 嵌入式模式，无需启动服务器
client = QdrantClient(path="./qdrant_data")

# 创建集合
client.create_collection(
    collection_name="iot_manuals",
    vectors_config=VectorParams(
        size=384,
        distance=Distance.COSINE
    )
)

# 批量插入
points = [
    PointStruct(
        id=i,
        vector=embeddings[i].tolist(),
        payload={"content": chunks[i], "device": device_ids[i]}
    )
    for i in range(len(chunks))
]
client.upsert(collection_name="iot_manuals", points=points)

# 搜索 (支持过滤)
results = client.search(
    collection_name="iot_manuals",
    query_vector=query_embedding.tolist(),
    query_filter={"must": [{"key": "device", "match": {"value": "pump-001"}}]},
    limit=5
)
```

### 2.3 向量数据库对比

| 特性 | SQLite-vec | Qdrant (嵌入式) | FAISS | ChromaDB |
|------|-----------|----------------|-------|----------|
| 依赖 | 零 (单 .so) | Rust 运行时 | numpy | Python 生态 |
| 内存占用 | ~5 MB | ~50 MB | ~20 MB | ~100 MB |
| 10K 搜索延迟 | 3 ms | 2 ms | 1 ms | 5 ms |
| 过滤支持 | SQL WHERE | 丰富 | 无原生 | 基础 |
| 持久化 | 自动 (SQLite) | 自动 | 手动 | 自动 |
| 适合设备 | MCU/RPi | RPi/Jetson | Jetson | PC/Jetson |

## 3. 边缘 Embedding 模型

### 3.1 轻量级 Embedding 模型选择

| 模型 | 维度 | 参数量 | MTEB 分数 | RPi4 延迟 | 适用场景 |
|------|------|--------|-----------|-----------|----------|
| all-MiniLM-L6-v2 | 384 | 22M | 56.3 | ~45 ms | 通用英文 |
| all-MiniLM-L12-v2 | 384 | 33M | 59.8 | ~85 ms | 精度优先 |
| BGE-small-zh | 512 | 24M | 57.8 | ~50 ms | 中文场景 |
| BGE-small-en | 384 | 33M | 62.1 | ~80 ms | 英文精度 |
| E5-small-v2 | 384 | 33M | 59.9 | ~80 ms | 多语言 |
| GTE-small | 384 | 33M | 61.4 | ~75 ms | 平衡选择 |

### 3.2 ONNX 部署 Embedding 模型

```python
import onnxruntime as ort
import numpy as np
from tokenizers import Tokenizer

class EdgeEmbedder:
    """边缘设备上的轻量级 Embedding 推理"""
    
    def __init__(self, model_path, tokenizer_path):
        # 使用 ONNX Runtime，支持 ARM CPU
        self.session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
            sess_options=self._get_options()
        )
        self.tokenizer = Tokenizer.from_file(tokenizer_path)
        self.tokenizer.enable_truncation(max_length=128)
        self.tokenizer.enable_padding(length=128)
    
    def _get_options(self):
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4  # RPi 4 核
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        return opts
    
    def encode(self, texts):
        """批量编码文本为向量"""
        if isinstance(texts, str):
            texts = [texts]
        
        encodings = self.tokenizer.encode_batch(texts)
        input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        
        outputs = self.session.run(None, {
            "input_ids": input_ids,
            "attention_mask": attention_mask
        })
        
        # Mean pooling
        embeddings = outputs[0]  # [batch, seq_len, dim]
        mask = attention_mask[:, :, np.newaxis].astype(np.float32)
        pooled = (embeddings * mask).sum(axis=1) / mask.sum(axis=1)
        
        # L2 归一化
        norms = np.linalg.norm(pooled, axis=1, keepdims=True)
        return pooled / norms

# 使用示例
embedder = EdgeEmbedder("minilm-l6.onnx", "tokenizer.json")
vectors = embedder.encode(["设备温度过高报警", "泵体振动异常"])
# RPi 4 延迟: ~45 ms/句 (batch=1), ~30 ms/句 (batch=8)
```

## 4. 文档分块策略

### 4.1 分块方法对比

| 方法 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 固定长度 | 简单、均匀 | 可能切断语义 | 结构化文档 |
| 句子分割 | 保持语义完整 | 长度不均 | 自然语言文本 |
| 递归分割 | 层次化、灵活 | 实现复杂 | 通用 |
| 语义分割 | 语义最优 | 需要模型 | 精度要求高 |

### 4.2 IoT 场景的分块实践

```python
import re

def chunk_iot_manual(text, chunk_size=256, overlap=50):
    """
    IoT 设备手册专用分块策略
    - 按章节标题分割
    - 保留设备型号和参数上下文
    - 表格不拆分
    """
    # 按标题分割
    sections = re.split(r'\n(#{1,3}\s+.+)\n', text)
    
    chunks = []
    current_chunk = ""
    current_header = ""
    
    for i, section in enumerate(sections):
        if section.startswith('#'):
            current_header = section.strip()
            continue
        
        # 检测表格，不拆分
        if '|' in section and section.count('|') > 4:
            chunks.append(f"{current_header}\n{section}")
            continue
        
        # 按句子累积到 chunk_size
        sentences = re.split(r'(?<=[。！？.!?])\s*', section)
        for sent in sentences:
            if len(current_chunk) + len(sent) > chunk_size:
                if current_chunk:
                    chunks.append(f"{current_header}\n{current_chunk}")
                # 保留 overlap
                words = current_chunk.split()
                current_chunk = ' '.join(words[-overlap//4:]) + sent
            else:
                current_chunk += sent
    
    if current_chunk:
        chunks.append(f"{current_header}\n{current_chunk}")
    
    return chunks
```

## 5. 混合检索策略

### 5.1 Dense + Sparse 混合搜索

```python
import numpy as np
from collections import Counter
import math

class HybridSearch:
    """稠密向量 + BM25 稀疏检索的混合方案"""
    
    def __init__(self, embedder, documents, alpha=0.7):
        self.embedder = embedder
        self.documents = documents
        self.alpha = alpha  # 稠密检索权重
        
        # 构建稠密索引
        self.dense_vectors = embedder.encode(documents)
        
        # 构建 BM25 稀疏索引
        self.bm25_index = self._build_bm25(documents)
    
    def _build_bm25(self, docs, k1=1.5, b=0.75):
        """构建 BM25 索引"""
        tokenized = [doc.split() for doc in docs]
        avg_dl = np.mean([len(d) for d in tokenized])
        
        # 计算 IDF
        df = Counter()
        for doc in tokenized:
            df.update(set(doc))
        
        n_docs = len(docs)
        idf = {word: math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1)
               for word, freq in df.items()}
        
        return {"tokenized": tokenized, "idf": idf, "avg_dl": avg_dl,
                "k1": k1, "b": b}
    
    def _bm25_score(self, query_tokens, doc_idx):
        """计算单个文档的 BM25 分数"""
        idx = self.bm25_index
        doc = idx["tokenized"][doc_idx]
        dl = len(doc)
        score = 0
        tf_dict = Counter(doc)
        
        for term in query_tokens:
            if term in idx["idf"]:
                tf = tf_dict.get(term, 0)
                numerator = tf * (idx["k1"] + 1)
                denominator = tf + idx["k1"] * (1 - idx["b"] + idx["b"] * dl / idx["avg_dl"])
                score += idx["idf"][term] * numerator / denominator
        return score
    
    def search(self, query, top_k=5):
        """混合检索"""
        # 稠密检索分数
        query_vec = self.embedder.encode(query)
        dense_scores = np.dot(self.dense_vectors, query_vec.T).flatten()
        
        # BM25 分数
        query_tokens = query.split()
        sparse_scores = np.array([
            self._bm25_score(query_tokens, i) 
            for i in range(len(self.documents))
        ])
        
        # 归一化并融合
        dense_norm = (dense_scores - dense_scores.min()) / (dense_scores.max() - dense_scores.min() + 1e-8)
        sparse_norm = (sparse_scores - sparse_scores.min()) / (sparse_scores.max() - sparse_scores.min() + 1e-8)
        
        final_scores = self.alpha * dense_norm + (1 - self.alpha) * sparse_norm
        
        top_indices = np.argsort(final_scores)[::-1][:top_k]
        return [(self.documents[i], final_scores[i]) for i in top_indices]
```

## 6. 端到端边缘 RAG 系统

### 6.1 完整架构

```python
class EdgeRAG:
    """完整的边缘 RAG 系统"""
    
    def __init__(self, embedder, vector_db, llm_path):
        self.embedder = embedder
        self.db = vector_db
        self.llm = self._load_llm(llm_path)
    
    def _load_llm(self, path):
        """加载量化 LLM (使用 llama-cpp-python)"""
        from llama_cpp import Llama
        return Llama(
            model_path=path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=0  # CPU only for RPi
        )
    
    def query(self, question, top_k=3):
        """RAG 查询流程"""
        # 1. 编码查询
        query_vec = self.embedder.encode(question)
        
        # 2. 检索相关文档
        results = search(self.db, query_vec[0], top_k=top_k)
        context = "\n---\n".join([r[0] for r in results])
        
        # 3. 构建 prompt
        prompt = f"""基于以下参考资料回答问题。如果资料中没有相关信息，请说明。

参考资料：
{context}

问题：{question}

回答："""
        
        # 4. 生成回答
        response = self.llm(prompt, max_tokens=256, temperature=0.1)
        return {
            "answer": response["choices"][0]["text"],
            "sources": [r[1] for r in results],
            "latency_ms": {
                "embedding": 45,   # 典型值
                "retrieval": 5,
                "generation": 2500  # 3B 模型在 RPi4
            }
        }
```

### 6.2 延迟优化技巧

| 优化手段 | 效果 | 实现难度 |
|----------|------|----------|
| Embedding 缓存 | 避免重复编码，节省 40ms | 低 |
| 向量量化 (PQ) | 搜索加速 2-3x，精度损失 <2% | 中 |
| 预计算常见查询 | 热门问题 0ms 检索 | 低 |
| 流式生成 | 首 token 延迟降低 80% | 中 |
| 异步预取 | 隐藏检索延迟 | 中 |
| 模型预热 | 避免冷启动 500ms | 低 |

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：在 PC 上用 LangChain 搭建基础 RAG，理解流程
2. **第二步**：替换为轻量组件（MiniLM + SQLite-vec + Phi-3-mini）
3. **第三步**：在 RPi 4 上部署，测量各环节延迟
4. **第四步**：优化分块策略和检索参数
5. **第五步**：添加混合检索和缓存机制

### 7.2 具体调优建议

- **Embedding 维度**：384 维是边缘场景的甜点——比 768 维快 2 倍，精度只损失 3-5%
- **分块大小**：IoT 手册建议 200-300 字符，太长检索不精确，太短缺乏上下文
- **Top-K 选择**：边缘 LLM 上下文窗口小，K=3 通常最优（K=5 可能超出 context）
- **更新策略**：设备手册更新不频繁，可以在夜间低负载时重建索引
- **降级方案**：LLM 推理太慢时，可以直接返回检索结果（无生成），延迟从秒级降到毫秒级

### 7.3 与云端 RAG 的协作模式

```
正常模式（有网络）：
  查询 -> 边缘检索 -> 云端 LLM 生成 -> 高质量回答

离线模式（无网络）：
  查询 -> 边缘检索 -> 本地小 LLM 生成 -> 可用回答

混合模式：
  查询 -> 边缘检索 -> 本地快速回答（先展示）
                   -> 同时发送云端 -> 云端精确回答（后更新）
```

## 参考文献

1. Lewis, P. et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020.
2. Karpukhin, V. et al. "Dense Passage Retrieval for Open-Domain Question Answering." EMNLP 2020.
3. SQLite-vec. "A vector search SQLite extension." GitHub, 2024.
4. Reimers, N. et al. "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks." EMNLP 2019.
5. Xiao, S. et al. "C-Pack: Packaged Resources To Advance General Chinese Embedding." arXiv 2023.
6. Qdrant. "Qdrant: Vector Search Engine." Documentation, 2024.
7. Gao, Y. et al. "Retrieval-Augmented Generation for Large Language Models: A Survey." arXiv 2024.
8. Ma, X. et al. "Fine-Tuning LLaMA for Multi-Stage Text Retrieval." SIGIR 2024.
9. Chen, J. et al. "BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity." arXiv 2024.
10. Edge Impulse. "Deploying RAG on Edge Devices." Technical Blog, 2024.
