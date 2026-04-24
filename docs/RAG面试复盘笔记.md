# RAG 检索增强生成 — 面试复盘笔记

> 基于 LLMOps 企业级平台的实际项目经验整理

---

## 一、RAG 整体架构

### 写入流程（离线索引）

```
用户上传文件(PDF/Word/Excel/Markdown)
  → COS对象存储 持久化原始文件
  → Celery异步任务(build_documents) 后台处理
  → FileExtractor 文件解析（UnstructuredPDFLoader等）
  → TextSplitter 文本分块（按token数切分，支持自定义规则）
  → HuggingFace Inference API 生成 1024维 embedding 向量
  → 写入 Weaviate 向量数据库（向量 + metadata）
  → 写入 PostgreSQL（片段文本、关键词、状态等结构化数据）
  → Jieba 提取关键词 → 构建关键词倒排索引表（BM25用）
```

### 读取流程（在线检索）

```
用户输入 query
  → query 文本生成 embedding 向量（优先走 Redis 缓存）
  → 根据检索策略选择检索器：
      - 语义检索：Weaviate 向量相似度搜索
      - 全文检索：BM25 关键词匹配
      - 混合检索：两者加权融合
  → 按 dataset_id 过滤 + document_enabled/segment_enabled 过滤
  → 返回 Top-K 相关片段（附带相似度得分）
  → 注入 LLM prompt 作为上下文，生成最终回答
```

---

## 二、核心组件详解

### 1. Weaviate 向量数据库

**作用**：存储文本的向量表示，执行高维向量相似度搜索（余弦距离）。

**为什么不用 PostgreSQL 做语义检索？**

| 维度 | PostgreSQL | Weaviate |
|------|-----------|----------|
| 擅长 | 结构化查询、事务、关联关系 | 高维向量 ANN 近似最近邻搜索 |
| 检索方式 | 精确匹配、LIKE、全文索引 | 向量余弦相似度（理解语义） |
| 性能 | 向量检索需全表扫描，百万级数据慢 | HNSW 索引，毫秒级返回 |
| 过滤 | SQL WHERE 天然支持 | 支持 metadata 属性过滤 |
| 示例 | "找 id=xxx 的记录" | "找和'如何部署模型'语义最接近的段落" |

**Weaviate Schema 设计**：
- Collection: `Dataset`
- Properties: `text`, `dataset_id`, `document_id`, `segment_id`, `account_id`, `node_id`, `document_enabled`, `segment_enabled`
- 向量维度：1024（与 embedding 模型匹配）

### 2. 混合检索策略

项目实现了三种检索策略，由 `RetrievalService.search_in_datasets()` 统一调度：

**语义检索（SemanticRetriever）**：
- 继承 LangChain `BaseRetriever`
- 调用 `WeaviateVectorStore.similarity_search_with_relevance_scores()`
- 通过 `Filter.by_property("dataset_id")` 过滤指定知识库
- 返回带相似度得分的文档

**全文检索（FullTextRetriever/BM25）**：
- 基于 Jieba 分词 + 关键词倒排索引表（存储在 PostgreSQL）
- 使用 `rank-bm25` 库计算 BM25 得分
- 适合精确关键词匹配场景

**混合检索（EnsembleRetriever）**：
- LangChain 内置的 `EnsembleRetriever`
- 权重配比：语义 0.5 + 全文 0.5
- 融合两种检索结果，取长补短

```python
hybrid_retriever = EnsembleRetriever(
    retrievers=[semantic_retriever, full_text_retriever],
    weights=[0.5, 0.5],
)
```

### 3. Embedding 模型选型

| 项目 | 选择 |
|------|------|
| 模型 | `intfloat/multilingual-e5-large` |
| 维度 | 1024 |
| 多语言 | 支持中英日法等多语言 |
| 调用方式 | HuggingFace Router Inference API（`router.huggingface.co`） |
| 优势 | 不消耗本地GPU算力，API调用即用 |

**选型理由**：
- 多语言支持对中文知识库至关重要
- E5-large 在 MTEB 基准上表现优异
- 1024维在精度和性能之间取得平衡
- 通过API调用避免部署本地模型的运维成本

### 4. 缓存策略

```python
# 三层结构：CacheBackedEmbeddings → Redis → HuggingFace API
self._cache_backed_embeddings = CacheBackedEmbeddings.from_bytes_store(
    self._embeddings,      # 实际的 embedding 模型
    self._store,           # RedisStore 作为缓存后端
    namespace="embeddings",
)
```

**工作原理**：
1. 对文本计算 hash 作为缓存 key
2. 先查 Redis，命中则直接返回向量
3. 未命中才调用 HuggingFace API，结果写回 Redis
4. 相同文本不会重复调用 API（节省成本+降低延迟）

### 5. 三层存储分工

```
┌─────────────────┐  结构化数据（用户、应用、知识库、文档、片段）
│   PostgreSQL    │  关键词倒排索引表（BM25检索用）
│                 │  会话历史、消息记录
└─────────────────┘

┌─────────────────┐  文本向量 + metadata
│    Weaviate     │  ANN 近似最近邻搜索
│                 │  按 dataset_id 等属性过滤
└─────────────────┘

┌─────────────────┐  Embedding 向量缓存（避免重复API调用）
│     Redis       │  Celery 任务队列 broker + result backend
│                 │  JWT Token 相关缓存
└─────────────────┘
```

---

## 三、知识库三级数据结构

```
Dataset（知识库）
  ├── Document（文档）—— 对应一个上传文件
  │     ├── Segment（片段）—— 文本分块后的最小检索单元
  │     ├── Segment
  │     └── ...
  ├── Document
  │     ├── Segment
  │     └── ...
  └── ...
```

- **Dataset**：知识库，归属某个用户（account_id），可关联多个 App
- **Document**：文档，对应一个上传文件，有处理状态流转（waiting→parsing→splitting→indexing→completed）
- **Segment**：片段，文本分块的最小单元，存储在 PostgreSQL（结构化）和 Weaviate（向量化），有独立的 enabled 开关

**多对多关联**：App 和 Dataset 通过 `AppDatasetJoin` 关联表实现多对多关系。

---

## 四、面试高频问题 & 回答要点

### Q1: 你的 RAG 系统是怎么实现的？

> 采用离线索引 + 在线检索的架构。离线：文件上传后通过 Celery 异步处理，经过解析→分块→Embedding→存入 Weaviate 向量库。在线：用户 query 经过同一 Embedding 模型转为向量，在 Weaviate 中做 ANN 检索，返回 Top-K 相关片段注入 LLM prompt。支持语义检索、全文检索、混合检索三种策略。

### Q2: 为什么用混合检索而不是单纯的向量检索？

> 向量检索擅长语义理解但可能丢失精确关键词匹配（如专有名词、代码片段）；BM25 擅长精确匹配但不理解语义。混合检索通过 EnsembleRetriever 加权融合两者结果（各 0.5），在语义相关性和关键词精确性之间取得平衡。实际项目中可根据业务场景调整权重。

### Q3: Embedding 向量是怎么缓存的？

> 使用 LangChain 的 CacheBackedEmbeddings，以 Redis 作为缓存后端。对文本计算 hash 作为 key，首次调用 HuggingFace API 后将向量写入 Redis，后续相同文本直接从缓存读取。这样避免了重复 API 调用，既节省成本又降低延迟。

### Q4: 文档处理流程中如何保证可靠性？

> 1）Celery 异步任务处理，失败可重试；2）文档有完整的状态机流转（waiting→parsing→splitting→indexing→completed/error）；3）每个片段单独记录状态，部分失败不影响整体；4）向量存储和结构化存储分开事务，通过 segment.node_id 关联。

### Q5: 如何处理大文件和大量片段？

> 1）文件解析使用 Unstructured 库的 fast 策略；2）分块按 token 数控制（而非字符数），确保不超 LLM 上下文限制；3）向量存储每次批量 10 条，通过多线程并发写入 Weaviate；4）Embedding 有 Redis 缓存层，避免重复计算。

### Q6: Weaviate 的 schema 是怎么设计的？为什么 metadata 要存在向量库里？

> Dataset 集合包含 text + 7 个 metadata 属性（dataset_id、document_id、segment_id 等）。metadata 存在 Weaviate 是为了在向量检索时直接做属性过滤（如只检索某个知识库、只检索已启用的文档/片段），避免检索后再到 PostgreSQL 二次过滤，减少网络往返。

### Q7: 如果让你优化这个 RAG 系统，你会怎么做？

> 1）**重排序**：检索结果经过 Cross-Encoder 重排序提升精度；2）**查询改写**：对用户 query 做扩展/改写，提升召回率；3）**分块策略**：尝试语义分块（按段落/章节）替代固定长度分块；4）**多路召回**：增加摘要检索、父文档检索等策略；5）**评估体系**：建立召回率/准确率的量化评估指标。
