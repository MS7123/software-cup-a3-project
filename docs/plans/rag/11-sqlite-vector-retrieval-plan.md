# SQLite Vector Retrieval Increment Plan

最后更新：2026-06-16

面向角色：Builder Agent / Reviewer Agent

本文档确定后续 RAG 数据库与向量检索路线：

```text
默认数据库：SQLite
后续增强数据库：PostgreSQL
向量检索默认方案：SQLite + Python cosine similarity
后续增强方案：PostgreSQL + pgvector
```

目标是在不增加默认部署门槛、不影响当前 keyword RAG 性能和稳定性的前提下，补上轻量 embedding-based retrieval 能力，并为后续 pgvector 留出清晰 adapter 边界。

## 1. 核心结论

### 1.1 默认方案

当前比赛阶段默认使用：

```text
SQLite
+ chunk_embeddings 表
+ EmbeddingProvider adapter
+ Python cosine similarity
+ hybrid retrieval
```

这个方案可以完成真实语义检索演示，但不引入 Chroma、FAISS、PostgreSQL 或 pgvector 默认依赖。

### 1.2 后续增强方案

后续需要云端部署、多用户并发、大量 chunks 或生产级向量索引时，再接入：

```text
PostgreSQL + pgvector
```

pgvector 必须作为 optional VectorStore adapter，不得影响默认 SQLite 启动、默认 smoke 和比赛本地部署。

## 2. 背景与判断

### 2.1 已知事实

当前项目已经具备：

- `documents` / `document_chunks` 表。
- `DocumentIngestionService`。
- `ChunkingService`。
- `KnowledgeBaseService.search()` keyword retrieval。
- Tutor / Resource grounded answer。
- `source_refs` 和 Agent trace。
- 默认 SQLite 本地演示。

当前未完成：

- chunk embedding 生成。
- query embedding 生成。
- embedding 存储。
- vector score。
- keyword + vector hybrid ranking。

### 2.2 为什么不默认接 PostgreSQL

PostgreSQL 对产品化有价值，但对当前比赛默认演示会增加：

- 安装门槛。
- 连接配置。
- 账号密码和 secret 管理。
- Windows 本地部署风险。
- `verify.ps1` 和 smoke 复杂度。

因此 PostgreSQL 只能作为后续 opt-in，不作为默认依赖。

### 2.3 为什么先用 Python cosine similarity

比赛数据规模通常是几十到几百个 chunks。Python 全量计算 cosine similarity 足够快，且不需要专业向量数据库。

核心流程：

```text
query
-> embedding
-> 从 SQLite 读取当前 course 的 chunk embeddings
-> Python 计算 cosine similarity
-> 取 top_k
-> 与 keyword score 合并
-> 返回 KnowledgeSearchResult
```

## 3. 明确非目标

本轮不做：

- 不把默认数据库改成 PostgreSQL。
- 不引入 pgvector 默认依赖。
- 不引入 Chroma / FAISS / Qdrant / Milvus。
- 不引入本地 sentence-transformers 大模型依赖。
- 不强制所有文档导入时都生成 embedding。
- 不让 embedding provider 失败影响 keyword retrieval。
- 不改变 `/api/v1/knowledge/search` request / response schema。
- 不让 API handler 或 frontend 计算 embedding / cosine similarity。
- 不把真实 API key 写入仓库、日志、测试输出、frontend bundle 或 Agent trace。

## 4. 总体架构

### 4.1 默认架构

```text
Document ingestion
-> DocumentChunk
-> optional embedding indexing
-> chunk_embeddings in SQLite

Knowledge search
-> keyword retrieval
-> optional vector retrieval via Python cosine
-> hybrid ranking
-> KnowledgeSearchResult
```

### 4.2 后续 pgvector 架构

```text
Document ingestion
-> DocumentChunk
-> EmbeddingProvider
-> PgVectorStore
-> PostgreSQL + pgvector

Knowledge search
-> KeywordRetriever
-> PgVectorStore.search()
-> hybrid ranking
```

### 4.3 Adapter 边界

需要预留但不立即实现完整 pgvector：

```text
EmbeddingProvider
VectorStore
SQLiteVectorStore
PgVectorStore  后续实现
```

第一阶段只实现：

```text
EmbeddingProvider protocol
OpenAICompatibleEmbeddingProvider
SQLiteVectorStore / PythonCosineVectorStore
```

## 5. 数据模型设计

### 5.1 推荐新增表：chunk_embeddings

不要直接把 embedding 塞进 `document_chunks` 主表。推荐新增表：

```text
chunk_embeddings
```

建议字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | integer primary key | embedding 记录 ID |
| `chunk_id` | foreign key | 关联 `document_chunks.id` |
| `provider` | string | embedding provider，例如 `openai_compatible` |
| `model` | string | embedding model 名称 |
| `embedding_json` | text | JSON 数组字符串 |
| `dimension` | integer | 向量维度 |
| `content_hash` | string | chunk 内容 hash，避免内容变更后复用旧向量 |
| `created_at` | datetime | 创建时间 |

建议唯一约束：

```text
unique(chunk_id, provider, model, content_hash)
```

### 5.2 为什么不用 document_chunks.embedding_json

新增表更适合后续扩展：

- 支持多个 embedding model。
- 支持重新索引。
- 支持删除和重建 embedding。
- 后续迁移到 pgvector 时更容易映射。
- 不影响 `document_chunks` keyword retrieval 性能。

## 6. 配置设计

### 6.1 默认配置

默认必须保持：

```env
APP_DATABASE_URL=sqlite:///./data/demo.sqlite3
RAG_RETRIEVAL_MODE=keyword
RAG_VECTOR_STORE=sqlite_cosine
RAG_EMBEDDING_ENABLED=false
```

含义：

- 不配置 embedding key 时，系统仍完整可演示。
- `KnowledgeBaseService.search()` 默认只走 keyword retrieval。
- `verify.ps1` 不依赖网络、不依赖 embedding provider。

### 6.2 启用 SQLite embedding retrieval

手动演示或本地增强时：

```env
RAG_RETRIEVAL_MODE=hybrid
RAG_EMBEDDING_ENABLED=true
RAG_VECTOR_STORE=sqlite_cosine
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_BASE_URL=<provider-base-url>
EMBEDDING_MODEL=<embedding-model>
EMBEDDING_API_KEY=<your-api-key>
EMBEDDING_TIMEOUT_SECONDS=10
```

### 6.3 后续 pgvector 配置

后续增强时：

```env
APP_DATABASE_URL=postgresql+psycopg2://user:password@host:5432/software_cup_a3
RAG_RETRIEVAL_MODE=hybrid
RAG_EMBEDDING_ENABLED=true
RAG_VECTOR_STORE=pgvector
PGVECTOR_INDEX_ENABLED=true
```

注意：

- 这些配置不得成为默认演示要求。
- README 必须明确 PostgreSQL / pgvector 是 optional。
- `run-local.ps1` 默认仍使用 SQLite。

## 7. 实现拆分

### 7.1 `IMPL-EMBED-001`: Embedding Provider Adapter

#### 目标

新增 embedding provider 边界，让系统可以把 chunk 和 query 转换为 embedding。

#### 允许修改

- `src/backend/app/adapters/protocols.py`
- `src/backend/app/adapters/embedding_provider.py`
- `src/backend/app/config` 或同类配置读取位置
- `tests/test_embedding_provider.py`

#### 边界要求

允许：

- 定义 `EmbeddingProvider` protocol。
- 实现 OpenAI-compatible embedding adapter。
- 使用环境变量配置 provider、base URL、model、API key、timeout。
- provider 失败时抛出受控异常。

禁止：

- 在 service 中直接写 provider HTTP 细节。
- 在 API handler 中调用 embedding API。
- 把 embedding API key 写进日志或 Agent trace。
- 让默认 smoke 依赖真实 embedding provider。

#### 验收标准

| ID | 标准 |
|---|---|
| EMBED-AC1 | 未配置 embedding provider 时，系统仍能启动并走 keyword retrieval |
| EMBED-AC2 | provider 配置完整时，可生成 list[float] embedding |
| EMBED-AC3 | provider error 不泄露 API key |
| EMBED-AC4 | adapter 有单元测试覆盖 request contract 和 error summary |
| EMBED-AC5 | `verify.ps1` 不需要真实 embedding key |

### 7.2 `IMPL-EMBED-002`: SQLite Chunk Embedding Index

#### 目标

新增 `chunk_embeddings` 表，并支持对已导入 chunks 生成和存储 embedding。

#### 允许修改

- `src/backend/app/models.py`
- `src/backend/app/services/document_ingestion_service.py`
- 新增 `EmbeddingIndexService`
- 相关 schema / tests

#### 推荐实现

新增 service：

```text
EmbeddingIndexService
```

职责：

- 找到需要 indexing 的 chunks。
- 调用 `EmbeddingProvider`。
- 计算 `content_hash`。
- 写入 `chunk_embeddings`。
- 跳过已有同 provider / model / content_hash 的 embedding。

#### 性能边界

必须避免影响默认方案性能：

- `RAG_EMBEDDING_ENABLED=false` 时，文档导入不调用 embedding provider。
- embedding indexing 可以手动触发或显式配置触发。
- 不允许每次 search 都为所有 chunks 重新生成 embedding。
- 不允许在 API handler 中同步批量 indexing 大量文档。

#### 验收标准

| ID | 标准 |
|---|---|
| INDEX-AC1 | 新表 `chunk_embeddings` 被声明并可创建 |
| INDEX-AC2 | 已导入 chunk 可生成并保存 embedding |
| INDEX-AC3 | 重复 indexing 不重复写入相同 embedding |
| INDEX-AC4 | chunk 内容变化后不会复用旧 content_hash |
| INDEX-AC5 | 默认 `RAG_EMBEDDING_ENABLED=false` 时导入性能不受 embedding provider 影响 |

### 7.3 `IMPL-VECTOR-001`: SQLite Python Cosine Vector Search

#### 目标

基于 SQLite 中保存的 embeddings，用 Python cosine similarity 实现轻量 vector retrieval。

#### 允许修改

- `src/backend/app/services/knowledge_base_service.py`
- 新增 `VectorSearchService` 或 `SQLiteVectorStore`
- `tests/test_vector_retrieval.py`

#### 核心算法

```python
def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
```

#### 性能要求

第一版必须控制范围：

- 只查询当前 `course_id` 的 chunk embeddings。
- 给候选 chunk 设置上限，例如 `RAG_VECTOR_MAX_CANDIDATES=1000`。
- 每次 search 只生成一次 query embedding。
- 没有 chunk embeddings 时直接返回空 vector results，不阻塞 keyword retrieval。
- vector search 超时或 provider error 时 fallback 到 keyword retrieval。

#### 验收标准

| ID | 标准 |
|---|---|
| VECTOR-AC1 | 有 chunk embeddings 时，query embedding 可召回语义相近 chunks |
| VECTOR-AC2 | 无 chunk embeddings 时，不影响 keyword retrieval |
| VECTOR-AC3 | vector score 写入 metadata，例如 `vector_score` |
| VECTOR-AC4 | 不改 search API schema |
| VECTOR-AC5 | 不引入 Chroma / FAISS / pgvector 依赖 |
| VECTOR-AC6 | 当前 course 范围外的 chunks 不参与检索 |

### 7.4 `IMPL-HYBRID-001`: Keyword + Vector Hybrid Ranking

#### 目标

保持当前 keyword retrieval 稳定性，同时引入 vector score 作为增强。

#### 推荐 ranking

```text
final_score = keyword_weight * normalized_keyword_score
            + vector_weight * normalized_vector_score
```

默认建议：

```env
RAG_KEYWORD_WEIGHT=0.45
RAG_VECTOR_WEIGHT=0.55
```

#### fallback 规则

```text
RAG_RETRIEVAL_MODE=keyword
-> 只走 keyword

RAG_RETRIEVAL_MODE=vector
-> 只走 vector；失败时按 fallback 策略返回 keyword 或空结果

RAG_RETRIEVAL_MODE=hybrid
-> keyword + vector；vector 不可用时返回 keyword
```

#### 验收标准

| ID | 标准 |
|---|---|
| HYBRID-AC1 | 默认 mode 仍是 `keyword` |
| HYBRID-AC2 | `hybrid` 模式下 keyword results 仍可参与排序 |
| HYBRID-AC3 | vector provider 失败时 keyword retrieval 仍返回 |
| HYBRID-AC4 | BFS/DFS 已有检索回归不被破坏 |
| HYBRID-AC5 | metadata 能解释 `retrieval_mode`、`keyword_score`、`vector_score` |

## 8. 后续 pgvector 接入边界

### 8.1 未来要替换的部分

未来接入 pgvector 时，只允许替换：

```text
VectorStore implementation
embedding storage backend
vector similarity SQL
```

不应改动：

- API handler。
- Tutor / Resource contract。
- `KnowledgeSearchResult` 基本字段。
- 前端调用方式。
- 默认 SQLite 演示脚本。

### 8.2 pgvector 增强计划占位

后续单独开计划：

```text
IMPL-PGVECTOR-001: PostgreSQL + pgvector opt-in
```

范围：

- 增加 PostgreSQL 依赖说明。
- 增加 pgvector extension 初始化说明。
- 实现 `PgVectorStore`。
- 保持 `SQLiteVectorStore` 默认可用。
- 增加 PostgreSQL 手动验证文档。

### 8.3 不影响默认性能的要求

pgvector 相关代码必须满足：

- 未设置 `RAG_VECTOR_STORE=pgvector` 时不 import pgvector 特定驱动细节。
- 默认 `run-local.ps1` 不连接 PostgreSQL。
- 默认 `verify.ps1` 不启动 PostgreSQL。
- 默认 SQLite keyword retrieval 不读取 `chunk_embeddings`。
- `hybrid` 模式才读取 embedding 表。

## 9. 手动验证方案

### 9.1 默认 keyword 模式

```powershell
$env:RAG_RETRIEVAL_MODE='keyword'
$env:RAG_EMBEDDING_ENABLED='false'
.\scripts\run-local.ps1
```

验证：

- 导入 BFS/DFS 资料。
- 搜索 BFS/DFS 对比问题。
- Tutor answer 有 `source_refs`。
- 不需要 embedding API key。

### 9.2 SQLite hybrid 模式

```powershell
$env:RAG_RETRIEVAL_MODE='hybrid'
$env:RAG_EMBEDDING_ENABLED='true'
$env:RAG_VECTOR_STORE='sqlite_cosine'
$env:EMBEDDING_PROVIDER='openai_compatible'
$env:EMBEDDING_BASE_URL='<provider-base-url>'
$env:EMBEDDING_MODEL='<embedding-model>'
$env:EMBEDDING_API_KEY='<your-api-key>'
.\scripts\run-local.ps1
```

验证：

- 导入资料后生成 chunk embeddings。
- query 能返回 `vector_score`。
- 同义表达能比 keyword-only 更容易召回。
- 关闭 embedding key 后仍能 fallback 到 keyword。

### 9.3 必测问题

```text
为什么广度优先搜索适合找无权图的最少边路径？
```

```text
我不太懂层序扩展和深入回溯有什么区别，请结合 BFS 和 DFS 解释。
```

```text
队列和递归栈分别适合什么图搜索场景？
```

## 10. 自动测试要求

### 10.1 必须新增或更新测试

建议测试文件：

```text
tests/test_embedding_provider.py
tests/test_vector_retrieval.py
tests/test_rag_retrieval.py
tests/test_backend_contracts.py
```

必须覆盖：

- 未配置 embedding 时默认 keyword 可用。
- fake embedding provider 生成固定向量。
- chunk embeddings 可写入和去重。
- Python cosine 排序正确。
- hybrid 模式下 vector 失败 fallback keyword。
- search API schema 不变。

### 10.2 最小验证命令

```powershell
python -m unittest tests.test_vector_retrieval tests.test_rag_retrieval tests.test_backend_contracts -v
python -m compileall -q src\backend tests
git diff --check
```

完整验证：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

## 11. Builder 自检格式

Builder Agent 完成本轮后必须输出：

```text
Self-review:
- Increment ID:
- Default database remains SQLite: Yes/No
- PostgreSQL required for default run: Yes/No
- Vector store required for default run: Yes/No
- RAG_RETRIEVAL_MODE default:
- Embedding provider behind adapter: Yes/No
- API handler contains embedding/vector logic: Yes/No
- Keyword retrieval fallback preserved: Yes/No
- Existing source_refs preserved: Yes/No
- Tests run:
- Manual demo steps:
- Known gaps:
- Ready for review: Yes/No
```

## 12. Reviewer 检查清单

### 12.1 Blocking

- 默认启动必须安装 PostgreSQL / pgvector。
- 默认 smoke 必须配置 embedding API key。
- API handler 直接调用 embedding provider 或计算 cosine similarity。
- 前端直接调用 embedding provider。
- secret 泄露到仓库、日志、response、Agent trace 或 frontend bundle。
- embedding provider 失败导致 keyword RAG 不可用。

### 12.2 Fix Before Merge

- `RAG_RETRIEVAL_MODE=keyword` 时仍读取 embedding 表或调用 provider。
- 没有 course 范围过滤，导致跨课程召回。
- chunk 内容变更后复用旧 embedding。
- hybrid score 无法解释，metadata 缺少 `retrieval_mode` / `vector_score`。
- 新增依赖导致 `verify.ps1` 失败。
- 破坏 BFS/DFS 已有 retrieval tests。

### 12.3 Optional

- pgvector adapter。
- Chroma / FAISS adapter。
- reranker。
- embedding batch queue。
- 前端 embedding indexing 管理页面。

## 13. 推荐交付顺序

```text
1. 定义 EmbeddingProvider protocol
2. 新增 chunk_embeddings 表
3. 实现 fake embedding provider 测试
4. 实现 SQLite embedding index service
5. 实现 Python cosine vector search
6. 实现 hybrid ranking
7. 保持 default keyword mode
8. 补 fallback 和 contract tests
9. 更新 README / runbook 中的 optional 配置
10. 跑 targeted tests 和 verify.ps1
```

## 14. 最终合并标准

允许合并的最低标准：

- 默认数据库仍是 SQLite。
- 默认检索仍是 keyword。
- 未配置 embedding key 时系统完整可演示。
- 启用 `hybrid` 后可以用 SQLite + Python cosine 完成语义召回。
- embedding / vector 逻辑只存在于 adapter / service 层。
- 后续 pgvector 有清晰替换点，但不影响默认性能和部署。
