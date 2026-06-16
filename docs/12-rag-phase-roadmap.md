# RAG Phase Roadmap

最后更新：2026-06-16

面向角色：Builder Agent / Reviewer Agent

本文档用于串联当前项目的 RAG 五阶段路线，帮助后续开发 Agent 判断当前应该做什么、不应该做什么，以及每一阶段的验收边界。本文档是路线图，不替代具体实现计划。

## 1. 总体结论

当前 RAG 路线确定为：

```text
Phase 1: keyword RAG
-> Phase 2: hybrid retrieval
-> Phase 3: reranking
-> Phase 4: citation quality
-> Phase 5: full knowledge management
```

当前项目状态：

| 阶段 | 状态 | 当前定位 |
|---|---|---|
| Phase 1 | 已完成 | 已支持资料导入、chunking、keyword retrieval、source_refs、Tutor grounded answer |
| Phase 2 | 当前计划 | 默认 SQLite + Python cosine similarity，后续 pgvector opt-in |
| Phase 3 | 后续 | 对召回结果做 reranking，不改 API contract |
| Phase 4 | 后续 | 提高引用精度和可解释性 |
| Phase 5 | 后续 | 完整知识库管理、PDF / Word、多课程、用户私有知识库 |

当前下一步不应跳到 Phase 5，也不应把 PostgreSQL / pgvector 设为默认依赖。当前最合理的技术路线是：

```text
默认 keyword RAG 稳定运行
-> opt-in SQLite embedding hybrid retrieval
-> 后续 pgvector adapter
```

## 2. 阶段依赖关系

```text
Phase 1 keyword RAG
  depends on: documents, document_chunks, KnowledgeBaseService

Phase 2 hybrid retrieval
  depends on: Phase 1, EmbeddingProvider, chunk_embeddings, Python cosine

Phase 3 reranking
  depends on: Phase 2 retrieval candidates, stable metadata

Phase 4 citation quality
  depends on: stable chunks, source_refs, chunk metadata spans

Phase 5 full knowledge management
  depends on: stable ingestion, indexing, deletion, rebuild, user/course boundaries
```

任何后续阶段都不得破坏前一阶段的默认演示能力。

## 3. Phase 1: Keyword RAG

### 3.1 状态

```text
已完成
```

相关文档：

- `docs/07-rag-implementation-plan.md`
- `docs/09-rag-retrieval-coverage-plan.md`
- `docs/rag-demo-runbook.md`

### 3.2 已实现能力

| 能力 | 状态 |
|---|---|
| `text` / `markdown` 资料导入 | 已完成 |
| Document 记录 | 已完成 |
| Chunking | 已完成 |
| `document_chunks` 存储 | 已完成 |
| `source_ref` | 已完成 |
| Keyword retrieval | 已完成 |
| BFS/DFS 复合问题召回优化 | 已完成 |
| Tutor grounded answer | 已完成 |
| Resource grounded source_refs | 已完成 |
| Agent trace grounded sources | 已完成 |
| 前端导入和搜索可见性 | 已完成 |

### 3.3 技术基础

Phase 1 建立在：

- SQLite。
- SQLAlchemy。
- `documents` / `document_chunks`。
- `DocumentIngestionService`。
- `ChunkingService`。
- `KnowledgeBaseService.search()`。
- keyword scoring。

### 3.4 验收标准

| ID | 标准 |
|---|---|
| P1-AC1 | 可导入真实 `text` / `markdown` 课程资料 |
| P1-AC2 | 导入后生成稳定 `document:{id}#chunk:{index}` |
| P1-AC3 | `KnowledgeBaseService.search()` 可从真实 chunks 检索 |
| P1-AC4 | Tutor answer 保留真实 `source_refs` |
| P1-AC5 | Agent trace 展示 grounded sources |
| P1-AC6 | 默认本地演示不需要 API key、PostgreSQL、VectorStore 或 embedding |
| P1-AC7 | `verify.ps1` 通过 |

### 3.5 不再重复做的事情

后续 Agent 不应重复重写：

- 文档导入 API。
- 基础 chunking。
- 基础 keyword retrieval。
- `source_ref` 格式。
- Tutor / Resource response schema。

除非 Reviewer 明确指出当前实现存在阻塞级缺陷。

## 4. Phase 2: Hybrid Retrieval

### 4.1 状态

```text
当前计划
```

相关文档：

- `docs/11-sqlite-vector-retrieval-plan.md`

### 4.2 目标

在不破坏默认 keyword RAG 的基础上，引入 embedding-based semantic retrieval。

默认方案：

```text
SQLite + chunk_embeddings + Python cosine similarity
```

后续增强：

```text
PostgreSQL + pgvector
```

### 4.3 技术基础

Phase 2 建立在：

- `EmbeddingProvider` adapter。
- `chunk_embeddings` 表。
- query embedding。
- chunk embedding。
- Python cosine similarity。
- hybrid ranking。

### 4.4 推荐实现增量

| Increment ID | 内容 | 优先级 |
|---|---|---|
| `IMPL-EMBED-001` | Embedding Provider Adapter | P1 |
| `IMPL-EMBED-002` | SQLite Chunk Embedding Index | P1 |
| `IMPL-VECTOR-001` | SQLite Python Cosine Vector Search | P1 |
| `IMPL-HYBRID-001` | Keyword + Vector Hybrid Ranking | P1 |
| `IMPL-PGVECTOR-001` | PostgreSQL + pgvector opt-in | P2 |

### 4.5 验收标准

| ID | 标准 |
|---|---|
| P2-AC1 | 默认 `RAG_RETRIEVAL_MODE=keyword` 不变 |
| P2-AC2 | 未配置 embedding key 时系统完整可演示 |
| P2-AC3 | 启用 `hybrid` 后能返回 `vector_score` |
| P2-AC4 | vector 失败时 fallback 到 keyword retrieval |
| P2-AC5 | API handler 不包含 embedding / cosine logic |
| P2-AC6 | 不引入 Chroma / FAISS / pgvector 默认依赖 |
| P2-AC7 | BFS/DFS 已有 retrieval tests 不回退 |

### 4.6 本阶段禁止事项

- 不把 PostgreSQL 设为默认数据库。
- 不默认启用 embedding provider。
- 不在 search 时为所有 chunks 实时生成 embedding。
- 不把 vector search 写到 frontend。
- 不让 embedding 失败影响默认演示。

## 5. Phase 3: Reranking

### 5.1 状态

```text
后续
```

Phase 3 只在 Phase 2 稳定后启动。

### 5.2 目标

对 Phase 2 召回的候选 chunks 重新排序，让传给 LLM 的 context 更准确、更少、更稳。

典型流程：

```text
keyword/vector recall
-> candidates
-> reranker
-> top context chunks
-> LLM
```

### 5.3 技术路线

优先级从轻到重：

| 方案 | 是否建议优先 | 说明 |
|---|---:|---|
| Rule-based reranker | 是 | 基于 anchor coverage、source diversity、score normalization |
| LLM reranker | 后续 | 成本高、慢，适合 opt-in |
| Cross-encoder reranker | 后续 | 效果好但依赖重 |
| Provider rerank API | 后续 | 依赖外部服务，需 fallback |

### 5.4 推荐实现边界

允许：

- 新增 `Reranker` protocol。
- 新增 `RuleBasedReranker`。
- 在 service 层合并 keyword score、vector score、coverage score。
- 控制传给 LLM 的最大 chunks 和最大字符数。

禁止：

- API handler 承载 reranking。
- 前端执行 reranking。
- 默认依赖远程 rerank provider。
- reranking 失败导致无 fallback。

### 5.5 验收标准

| ID | 标准 |
|---|---|
| P3-AC1 | reranking 不改变 search API schema |
| P3-AC2 | reranking metadata 可解释，例如 `rerank_score` |
| P3-AC3 | BFS/DFS compare query 优先保留 compare chunk |
| P3-AC4 | LLM context chunk 数和字符数受控 |
| P3-AC5 | reranker 失败时仍可返回原始 retrieval results |

## 6. Phase 4: Citation Quality

### 6.1 状态

```text
后续
```

Phase 4 目标不是召回更多，而是让引用更可信、更可检查。

### 6.2 目标

让评委能看到：

```text
回答中的每个关键结论来自哪份资料、哪个 chunk、哪段原文
```

### 6.3 技术基础

Phase 4 建立在：

- 稳定 `source_ref`。
- chunk metadata。
- `char_start` / `char_end`。
- chunk excerpt。
- Agent trace。
- 前端 source panel。

### 6.4 推荐功能

| 功能 | 说明 |
|---|---|
| Inline citation | 回答中使用 `[document:4#chunk:3]` 或短引用标记 |
| Source excerpt | 展示被引用 chunk 的短摘录 |
| Source panel | 点击 source_ref 查看资料片段 |
| Citation coverage check | 检查关键段落是否有来源 |
| Trace source detail | Agent trace 展示来源、分数、命中原因 |

### 6.5 验收标准

| ID | 标准 |
|---|---|
| P4-AC1 | answer 中关键结论能对应 source_ref |
| P4-AC2 | source_ref 可展开查看 chunk excerpt |
| P4-AC3 | source panel 不展示过长全文 |
| P4-AC4 | 无资料时不伪造 citation |
| P4-AC5 | citation 仍来自 retrieval result，不由前端硬编码 |
| P4-AC6 | trace 能说明 source 被使用的原因 |

### 6.6 禁止事项

- 不把整篇文档塞进前端。
- 不让 LLM 伪造不存在的 source_ref。
- 不为了 citation 改破 Tutor API contract。
- 不在 frontend 生成假的引用。

## 7. Phase 5: Full Knowledge Management

### 7.1 状态

```text
后续
```

Phase 5 是产品化知识库能力，不是当前比赛 P0。

### 7.2 目标

支持完整学习资料管理：

- PDF / Word / Markdown / text。
- 多课程资料。
- 用户私有知识库。
- 文档删除。
- 重新索引。
- 索引状态展示。
- 数据库可选迁移到 PostgreSQL。
- 向量检索可选迁移到 pgvector。

### 7.3 技术基础

Phase 5 建立在：

- `DocumentParser` adapter。
- `DocumentIngestionService`。
- `EmbeddingIndexService`。
- `VectorStore` adapter。
- 用户 / course / document 权限边界。
- 可选 PostgreSQL。

### 7.4 推荐实现增量

| Increment ID | 内容 | 优先级 |
|---|---|---|
| `IMPL-KM-001` | Document delete + chunk cleanup | P2 |
| `IMPL-KM-002` | Re-index imported documents | P2 |
| `IMPL-KM-003` | PDF parser opt-in | P2 |
| `IMPL-KM-004` | Word parser opt-in | P2 |
| `IMPL-KM-005` | Course-scoped knowledge library UI | P2 |
| `IMPL-KM-006` | User private knowledge library | P3 |

### 7.5 验收标准

| ID | 标准 |
|---|---|
| P5-AC1 | 文档删除能清理 chunks、embeddings 和相关索引 |
| P5-AC2 | re-index 不产生重复 chunk_embeddings |
| P5-AC3 | 多课程资料不会跨 course 检索 |
| P5-AC4 | 用户私有资料不会跨用户泄露 |
| P5-AC5 | PDF / Word parser 是 opt-in，不影响默认 text / markdown |
| P5-AC6 | PostgreSQL / pgvector 仍是可选部署，不影响 SQLite 默认演示 |

## 8. 当前推荐优先级

当前阶段按以下顺序推进：

| 优先级 | 任务 | 原因 |
|---|---|---|
| P0 | 保持 Phase 1 稳定 | 已是主演示底座 |
| P1 | Phase 2 SQLite hybrid retrieval | 提升 RAG 技术含量，默认部署仍轻 |
| P1 | Tutor latency / context 控制 | 防止 LLM 慢影响演示 |
| P1 | Citation excerpt 小增强 | 增强可解释性，成本低 |
| P2 | Phase 3 lightweight reranking | Phase 2 稳定后做 |
| P2 | pgvector opt-in | 作为工程增强，不默认启用 |
| P2/P3 | Phase 5 knowledge management | 产品化增强，后置 |

## 9. Builder 使用规则

Builder Agent 开始 RAG 相关任务前必须判断：

```text
当前任务属于 Phase 几？
是否依赖前一阶段已经稳定？
是否会改变默认 SQLite / keyword 演示路径？
是否引入外部服务或 secret？
是否需要 Reviewer 特别检查 API contract？
```

Builder 自检格式：

```text
RAG phase:
- Phase:
- Increment ID:
- Default SQLite preserved: Yes/No
- Default keyword retrieval preserved: Yes/No
- API contract changed: Yes/No
- External provider required by default: Yes/No
- Fallback preserved: Yes/No
- Source refs preserved: Yes/No
- Tests run:
- Manual demo steps:
- Known gaps:
```

## 10. Reviewer 使用规则

Reviewer 审查 RAG 增量时必须按阶段判断，不要把后续阶段未完成项误判为当前 regression。

### Blocking

- 默认本地演示无法运行。
- 默认 SQLite 被替换成强制 PostgreSQL。
- 默认 keyword retrieval 被破坏。
- 无 API key / 无网络时无法 fallback。
- API handler 或 frontend 承载核心 retrieval / embedding / reranking 逻辑。
- source_refs 伪造或丢失。
- secret 泄露。

### Fix Before Merge

- 当前阶段声明完成的功能没有最小测试。
- 跨 course 或跨 user 检索资料。
- embedding / vector 失败影响 keyword fallback。
- pgvector / PostgreSQL 变成默认依赖。
- citation 由前端硬编码。
- reranking 结果无法解释且破坏已有检索回归。

### Optional

- Chroma / FAISS adapter。
- 生产级 async indexing。
- 大规模向量索引优化。
- 多格式文档解析。
- 用户私有知识库 UI polish。

## 11. 与现有文档的关系

| 文档 | 作用 |
|---|---|
| `docs/07-rag-implementation-plan.md` | Phase 1 最小真实 RAG 闭环 |
| `docs/09-rag-retrieval-coverage-plan.md` | Phase 1 keyword coverage 增强 |
| `docs/11-sqlite-vector-retrieval-plan.md` | Phase 2 SQLite hybrid retrieval 实现计划 |
| `docs/12-rag-phase-roadmap.md` | Phase 1 到 Phase 5 总路线图 |
| `docs/rag-demo-runbook.md` | 当前 RAG 手动演示和排错 |

后续如果更新具体实现细节，优先更新对应阶段文档，不要把所有实现细节塞进本路线图。

## 12. 最终路线确认

当前正式路线为：

```text
Phase 1 已完成：keyword RAG
Phase 2 下一步：SQLite + Python cosine hybrid retrieval
Phase 3 后续：lightweight reranking
Phase 4 后续：citation quality
Phase 5 后续：full knowledge management
```

默认部署路线为：

```text
SQLite
+ keyword retrieval
+ optional SQLite embedding hybrid retrieval
```

后续增强路线为：

```text
PostgreSQL
+ pgvector
+ production-grade knowledge management
```
