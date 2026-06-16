# RAG Phase 3 Reranking Plan

最后更新：2026-06-16

面向角色：Builder Agent / Reviewer Agent

本文档定义 RAG Phase 3：reranking。目标是在 Phase 2 已提供 keyword / vector / hybrid retrieval candidates 的基础上，对候选 chunks 做轻量重排序，让传给 Tutor / Resource / Evaluator 的上下文更准确、更少、更稳定。

## 1. 阶段定位

### 1.1 当前前置条件

Phase 3 必须建立在以下能力稳定之后：

- Phase 1 keyword RAG 已完成。
- Phase 2 SQLite hybrid retrieval 已完成或至少可用。
- `KnowledgeBaseService.search()` 能返回带 metadata 的 candidates。
- `source_refs`、`document_id`、`chunk_id`、`keyword_score`、`vector_score` 可用于解释。

### 1.2 本阶段目标

```text
retrieval candidates
-> rerank
-> top context chunks
-> LLM grounded generation
```

本阶段不是为了召回更多 chunks，而是为了从已召回 candidates 中选出更适合进入 LLM context 的内容。

## 2. 明确非目标

本阶段不做：

- 不引入默认远程 rerank provider。
- 不引入 cross-encoder 大模型默认依赖。
- 不引入 Chroma / FAISS / pgvector。
- 不改变 `/api/v1/knowledge/search` request / response schema。
- 不改变 Tutor / Resource / Quiz / Evaluator API contract。
- 不让 API handler 或 frontend 执行 reranking。
- 不把 reranking 失败变成主演示链路失败。
- 不让 LLM 读取整篇文档替代 retrieval。

## 3. 推荐技术路线

### 3.1 第一版：Rule-based Reranker

第一版只做轻量、可解释、可测试的 reranker：

```text
keyword_score
+ vector_score
+ anchor coverage
+ source diversity
+ concept alignment
+ chunk length penalty
-> rerank_score
```

### 3.2 后续可选增强

| 方案 | 当前是否做 | 原因 |
|---|---:|---|
| Rule-based reranker | 是 | 轻量、稳定、无外部依赖 |
| LLM reranker | 否 | 慢，增加 API key 和成本依赖 |
| Cross-encoder reranker | 否 | 依赖重，Windows 部署风险高 |
| Provider rerank API | 否 | 需要外部服务和 fallback 设计 |

## 4. 架构边界

### 4.1 推荐新增组件

```text
Reranker protocol
RuleBasedReranker
RetrievalCandidate
RerankResult
```

推荐位置：

```text
src/backend/app/services/reranking_service.py
```

或：

```text
src/backend/app/services/retrieval_reranker.py
```

### 4.2 允许修改

- `src/backend/app/services/knowledge_base_service.py`
- 新增 reranking service。
- `tests/test_rag_reranking.py`
- `tests/test_rag_retrieval.py`
- `docs/05-agile-development-log.md`
- `docs/rag-demo-runbook.md`

### 4.3 禁止修改方向

- 不在 frontend 计算 rerank score。
- 不在 router / API handler 中计算 rerank score。
- 不改 search response schema，只能扩展 `metadata`。
- 不把 reranking 绑定到真实 LLM provider。

## 5. Reranking 输入输出

### 5.1 输入

输入是已有 retrieval results：

```text
list[KnowledgeSearchResult]
```

每个 result 应尽量包含：

```json
{
  "chunk_id": 1,
  "source_ref": "document:4#chunk:3",
  "score": 0.82,
  "metadata": {
    "retrieval_mode": "hybrid",
    "keyword_score": 0.7,
    "vector_score": 0.91,
    "matched_terms": ["bfs", "dfs"],
    "anchor_matches": ["bfs", "dfs"],
    "coverage_bucket": "bfs_dfs_compare"
  }
}
```

### 5.2 输出

输出仍是：

```text
list[KnowledgeSearchResult]
```

只允许通过 metadata 增加解释字段：

```json
{
  "rerank_score": 0.88,
  "rerank_reasons": [
    "covers_required_anchor:bfs",
    "covers_required_anchor:dfs",
    "source_diversity_bonus"
  ]
}
```

## 6. Scoring 规则

### 6.1 推荐权重

第一版建议：

| 维度 | 默认权重 | 说明 |
|---|---:|---|
| normalized retrieval score | 0.45 | 来自 keyword/vector/hybrid 原始分 |
| anchor coverage | 0.25 | 覆盖问题中的关键概念 |
| source diversity | 0.10 | 避免 top chunks 全来自同一重复片段 |
| concept alignment | 0.10 | 如果 chunk 绑定当前 concept，可加分 |
| concise context bonus | 0.10 | 过长 chunk 降权，适中 chunk 加分 |

建议配置：

```env
RAG_RERANK_ENABLED=false
RAG_RERANK_MAX_CANDIDATES=12
RAG_RERANK_TOP_CONTEXT=5
RAG_RERANK_CONTEXT_CHAR_LIMIT=3500
```

默认必须保持：

```env
RAG_RERANK_ENABLED=false
```

### 6.2 Context 控制

reranker 不只是排序，还要控制进入 LLM 的 context：

```text
max_chunks <= 5
total_chars <= 3500
per_chunk_chars <= 900
```

这能降低 LLM 延迟和回答跑偏风险。

## 7. 实现拆分

### 7.1 `IMPL-RERANK-001`: RuleBasedReranker

目标：

- 新增 rule-based reranker。
- 给已有 retrieval results 添加 `rerank_score` 和 `rerank_reasons`。
- 不改变 API schema。

验收标准：

| ID | 标准 |
|---|---|
| RERANK-AC1 | 默认 `RAG_RERANK_ENABLED=false` 时行为不变 |
| RERANK-AC2 | 启用 rerank 后 results 仍是 `KnowledgeSearchResult` |
| RERANK-AC3 | metadata 包含 `rerank_score` 和 `rerank_reasons` |
| RERANK-AC4 | BFS/DFS compare chunk 排名优先 |
| RERANK-AC5 | reranker 不依赖远程 LLM |

### 7.2 `IMPL-RERANK-002`: Context Budgeting

目标：

- Tutor / Resource 使用 reranked context。
- 控制最大 chunks 和最大字符数。

验收标准：

| ID | 标准 |
|---|---|
| CTX-AC1 | Tutor LLM context 不超过配置的 chunk 数 |
| CTX-AC2 | Tutor LLM context 不超过配置的总字符数 |
| CTX-AC3 | source_refs 仍对应实际传入 context 的 chunks |
| CTX-AC4 | context 截断不产生伪造 source_ref |
| CTX-AC5 | LLM latency 不因 reranking 变差 |

### 7.3 `IMPL-RERANK-003`: Trace Explainability

目标：

- Agent trace 展示 reranking 使用了哪些来源。
- 不新增复杂 trace schema，优先复用现有 step 文本字段。

验收标准：

| ID | 标准 |
|---|---|
| TRACE-RERANK-AC1 | Agent trace 能看到 reranked sources |
| TRACE-RERANK-AC2 | trace 显示简短 rerank reason |
| TRACE-RERANK-AC3 | 无 reranking 时 trace 不伪造 rerank 信息 |

## 8. 测试计划

### 8.1 单元测试

建议新增：

```text
tests/test_rag_reranking.py
```

必须覆盖：

- 默认关闭时不改变排序。
- 启用后 compare chunk 优先。
- source diversity 生效。
- context char limit 生效。
- reranker failure fallback 到原始 results。

### 8.2 回归测试

必须继续通过：

```powershell
python -m unittest tests.test_rag_retrieval tests.test_vector_retrieval tests.test_backend_contracts -v
```

### 8.3 完整验证

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

## 9. Reviewer 检查清单

### Blocking

- 默认本地演示因为 reranker 失败。
- API handler 或 frontend 承载 reranking。
- source_refs 与实际传给 LLM 的 chunks 不一致。
- 默认引入远程 rerank provider。
- 破坏默认 keyword retrieval。

### Fix Before Merge

- `RAG_RERANK_ENABLED=false` 时行为仍被改变。
- rerank metadata 缺少解释字段。
- BFS/DFS compare query 回归。
- context budgeting 后 answer 无法引用真实来源。
- 新增配置未写入文档。

### Optional

- LLM reranker。
- Cross-encoder reranker。
- provider rerank API。
- 更细粒度 query intent classification。

## 10. Builder 自检格式

```text
Self-review:
- RAG phase: Phase 3
- Increment ID:
- Default rerank disabled: Yes/No
- API contract changed: Yes/No
- API handler contains reranking logic: Yes/No
- Frontend contains reranking logic: Yes/No
- Source refs preserved: Yes/No
- Context budget enforced: Yes/No
- Tests run:
- Manual demo steps:
- Known gaps:
- Ready for review: Yes/No
```

## 11. 最终合并标准

允许合并的最低标准：

- 默认模式不受影响。
- 启用 reranking 后检索结果更可解释。
- Tutor / Resource 使用的 context 更受控。
- source_refs 仍真实、稳定、可追踪。
- 不引入新的默认外部依赖。
