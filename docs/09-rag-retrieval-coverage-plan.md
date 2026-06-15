# RAG Retrieval Coverage Increment Plan

最后更新：2026-06-15

面向角色：Builder Agent / Reviewer Agent

本文档定义下一轮 RAG 可演示增量：在不引入 embedding、VectorStore、PostgreSQL 或重写 RAG 架构的前提下，优化当前 keyword retrieval，使 BFS/DFS 这类复合问题能够稳定召回多个相关 chunk，避免 LLM 因上下文缺失而误判“资料中没有 DFS”。

## 1. 背景与问题

### 已知事实

当前 RAG 第一阶段已完成：

- 支持 `text` / `markdown` 资料导入。
- 支持 `documents` / `document_chunks` 入库。
- 支持 `KnowledgeBaseService.search()` 基于真实 chunk 做 keyword retrieval。
- Tutor / Resource response 保留真实 `source_refs`。
- Agent trace 显示具体 grounded sources。
- LLM + RAG Tutor 手动链路已验证。

### 当前问题

手动测试中，资料里已经存在 DFS 内容：

```text
document:4#chunk:3  DFS 的核心思想
document:4#chunk:4  BFS 与 DFS 的区别
document:4#chunk:5  易错点，包含 BFS / DFS 对比
```

但用户提问：

```text
为什么 BFS 在无权图中第一次到达节点就代表最少边数？请和 DFS 对比。
```

Tutor 实际引用的来源可能只有：

```text
document:2#chunk:1
document:4#chunk:1
```

这些 chunk 更偏 BFS，导致 LLM context 没有 DFS chunk。LLM 在 grounded answer 约束下会保守回答“当前资料中没有 DFS 内容”。

### 问题性质

这不是资料导入失败，也不是 LLM 失败，而是：

```text
keyword retrieval recall / coverage 不足
```

特别是复合问题需要同时覆盖多个概念：

```text
Intent 1: BFS 为什么能保证无权图最短路径
Intent 2: DFS 为什么不能保证最短路径，和 BFS 有什么区别
```

## 2. 本轮目标

实现 RAG keyword retrieval coverage 优化：

```text
复合 query
-> 检测概念 anchor
-> score chunks
-> 优先覆盖多个 anchor
-> 再按 score 补足 top_k
-> Tutor / LLM context 同时包含 BFS 和 DFS 资料
```

本轮完成后，同样问题应更稳定返回：

```text
document:4#chunk:1  BFS 的核心思想
document:4#chunk:3  DFS 的核心思想
document:4#chunk:4  BFS 与 DFS 的区别
```

## 3. 明确非目标

本轮不做：

- Chroma / FAISS / Qdrant / Milvus。
- pgvector。
- embedding provider。
- rerank model。
- PostgreSQL 合并。
- 认证系统合并。
- PDF / Word / PPT 上传解析。
- 重写 `KnowledgeBaseService` 为新架构。
- 修改 search API request / response schema。
- 在前端实现 scoring。
- 硬编码某一道 demo 问题的答案。

## 4. 实现边界

### Backend Service

允许修改：

- `src/backend/app/services/knowledge_base_service.py`
- `src/backend/app/services/tutor_service.py`
- `src/backend/app/services/resource_service.py`
- 相关测试文件。

要求：

- coverage 逻辑必须保持在 `KnowledgeBaseService` 内部。
- Tutor / Resource 可以提高 retrieval `top_k`，但不实现检索逻辑。
- 不改变 API handler 职责。
- 不新增数据库表。
- 不破坏现有 `KnowledgeSearchResult` 字段。

### Frontend

允许修改：

- `src/frontend/src/App.tsx`
- `src/frontend/src/api/types.ts`
- `src/frontend/src/styles.css`

要求：

- 前端只展示后端返回的 `matched_terms`、`score`、`source_ref`、content excerpt。
- 前端不做 scoring。
- 前端不伪造 `source_ref`。

## 5. 推荐实现方案

### 5.1 Anchor Detection

在 `KnowledgeBaseService` 内部增加 anchor 检测。

建议第一版只支持有限、可解释的 anchor：

```python
ANCHOR_TERMS = {
    "bfs": ["bfs", "广度优先", "queue", "队列", "层"],
    "dfs": ["dfs", "深度优先", "stack", "递归", "回溯"],
}
```

判断 query 需要哪些 anchor：

```text
query_terms 命中 bfs anchor -> required_anchors 包含 bfs
query_terms 命中 dfs anchor -> required_anchors 包含 dfs
```

注意：

- anchor 是 retrieval coverage 规则，不是答案模板。
- 不要把 demo 问题全文写死到代码。
- 以后可以扩展到 stack / queue、tree traversal 等概念。

### 5.2 Chunk Anchor Matches

对每个 chunk 的 haystack 计算：

```text
anchor_matches = ["bfs", "dfs"]
```

可以写入 metadata：

```json
{
  "matched_terms": ["bfs", "dfs", "queue"],
  "term_match_count": 3,
  "anchor_matches": ["bfs", "dfs"],
  "coverage_bucket": "bfs_dfs_compare"
}
```

`coverage_bucket` 第一版可选：

| bucket | 含义 |
|---|---|
| `bfs` | chunk 主要覆盖 BFS |
| `dfs` | chunk 主要覆盖 DFS |
| `bfs_dfs_compare` | chunk 同时覆盖 BFS 和 DFS |
| `general` | 无明显 anchor |

### 5.3 Coverage-aware Ranking

当前流程大致为：

```text
query -> query_terms -> score chunks -> sort -> top_k
```

建议改为：

```text
query -> query_terms
-> score chunks
-> detect required anchors
-> pick compare chunks first
-> pick one best chunk per required anchor
-> fill remaining by score
-> top_k
```

伪逻辑：

```text
ranked = chunks sorted by score
selected = []

if required anchors >= 2:
  add best chunk covering multiple required anchors
  for each required anchor:
    add best chunk covering that anchor

fill selected with remaining ranked chunks
return selected[:top_k]
```

去重规则：

```text
同一个 chunk 只能出现一次
按 chunk_id 或 source_ref 去重
```

### 5.4 Tutor / Resource top_k

如果当前 Tutor / Resource retrieval top_k 太小，建议提高到：

```text
Tutor: top_k = 5
Resource: top_k = 5
```

要求：

- 不让前端传 `top_k`。
- 不改 `/api/v1/tutor/ask` schema。
- 不改 `/api/v1/resources/generate` schema。
- 如果没有足够命中，少于 5 条也可以。

## 6. Frontend Debug Visibility

### 目标

让演示者能直接看到 retrieval 为什么命中某些 chunk。

### 最小 UI

在 `Search imported chunks` 结果中展示：

```text
source_ref
score
matched_terms
content excerpt
```

示例：

```text
document:4#chunk:4
score 0.72
matched: bfs, dfs, 最短路径
BFS 更关注按层推进... DFS 更关注深入探索...
```

### 边界

- 只展示后端返回字段。
- 不在前端重新计算 matched terms。
- content excerpt 限制长度，避免卡片过长。
- source_ref 过长时允许换行，不允许布局溢出。

## 7. 测试计划

### 7.1 后端测试

在 `tests/test_rag_retrieval.py` 增加测试。

#### 测试 1：BFS/DFS 复合 query 召回 DFS 和 compare chunk

建议名称：

```python
test_bfs_dfs_compare_query_retrieves_dfs_and_compare_chunks
```

测试数据：

```text
BFS 的核心思想
DFS 的核心思想
BFS 与 DFS 的区别
```

输入：

```text
为什么 BFS 在无权图中第一次到达节点就代表最少边数？请和 DFS 对比。
```

断言：

```text
results 中包含 DFS chunk
results 中包含 BFS/DFS compare chunk
metadata.anchor_matches 包含 dfs
```

#### 测试 2：Tutor source_refs 覆盖 DFS

调用：

```text
POST /api/v1/tutor/ask
```

断言：

```text
source_refs 中包含 DFS 或 BFS/DFS compare chunk
Agent trace 中包含对应 source_ref
```

#### 测试 3：无关 query 不乱召回

输入：

```text
AVL rotation red black tree
```

断言：

```text
results 为空或不产生高置信 source
Tutor 不伪造 source_ref
```

### 7.2 前端测试

更新 Playwright smoke 或新增轻量断言：

- 导入 BFS/DFS 样例。
- 搜索 BFS/DFS 对比问题。
- search result 显示：
  - `document:`
  - `score`
  - `matched`
  - chunk excerpt。

## 8. 验收标准

| ID | 标准 |
|---|---|
| RAG-RECALL-AC1 | BFS/DFS 复合问题能同时召回 BFS 和 DFS chunk |
| RAG-RECALL-AC2 | BFS/DFS 复合问题优先召回 compare chunk |
| RAG-RECALL-AC3 | Tutor LLM 不再因 retrieval 缺失而说“资料中没有 DFS” |
| RAG-RECALL-AC4 | Agent trace 展示多个 grounded sources |
| RAG-RECALL-AC5 | Search UI 显示 `matched_terms` 和 chunk 摘要 |
| RAG-RECALL-AC6 | 无关 query 不被强行匹配 |
| RAG-RECALL-AC7 | 不引入 embedding / VectorStore / PostgreSQL 强依赖 |
| RAG-RECALL-AC8 | `python -m unittest tests.test_rag_retrieval -v` 通过 |
| RAG-RECALL-AC9 | `npm run build` 通过 |
| RAG-RECALL-AC10 | `./scripts/verify.ps1` 通过 |

## 9. Reviewer 检查清单

Reviewer 应重点检查：

- `KnowledgeBaseService` 是否仍是唯一 retrieval scoring / coverage 位置。
- API handler 是否没有新增 retrieval 逻辑。
- 前端是否只展示 metadata，不做 scoring。
- 是否存在 hardcoded answer 或 hardcoded demo source_ref。
- 是否保留无资料 fallback。
- `top_k` 增大后是否导致上下文过长或输出混乱。
- 无关 query 是否被 coverage 规则误召回。
- RAG tests 是否覆盖 BFS/DFS 复合问题。
- 默认离线 smoke 是否仍可运行。

## 10. Builder 自审格式

Builder 完成本轮后，在 review 请求中给出：

```text
Self-review:
- Increment ID: RAG-RECALL-001
- Demo value:
- API/schema changed: Yes/No
- Database model changed: Yes/No
- Retrieval coverage implemented in KnowledgeBaseService: Yes/No
- Tutor top_k changed: Yes/No
- Resource top_k changed: Yes/No
- Frontend only displays backend metadata: Yes/No
- Hardcoded answer/source_ref risk: Yes/No
- Offline fallback preserved: Yes/No
- Tests run:
- Manual demo steps:
- Known gaps:
- Ready for review: Yes/No
```

## 11. 推荐交付顺序

```text
1. 先写失败复现测试
2. 实现 anchor detection
3. 实现 coverage-aware ranking
4. 提高 Tutor / Resource top_k
5. 增加前端 matched_terms / excerpt 展示
6. 跑 backend targeted tests
7. 跑 frontend build
8. 跑 verify.ps1
9. 记录开发日志和 review 结果
```

## 12. 手动验证问题

推荐验证问题：

```text
为什么 BFS 在无权图中第一次到达节点就代表最少边数？请和 DFS 对比。
```

```text
栈和队列最容易混淆的操作是什么？请结合 BFS 和 DFS 解释。
```

通过判断：

```text
Tutor answer 同时解释 BFS 和 DFS
source_refs 至少包含一个 DFS 或 compare chunk
Agent trace 包含多个 Grounded sources
Search UI 能看到 matched_terms 和 chunk 摘要
```

