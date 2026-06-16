# RAG Phase 4 Citation Quality Plan

最后更新：2026-06-16

面向角色：Builder Agent / Reviewer Agent

本文档定义 RAG Phase 4：citation quality。目标是在已有 `source_refs` 的基础上，让回答中的关键结论能够更精确地对应资料片段，提升评委对 grounded answer 的信任度和可检查性。

## 1. 阶段定位

### 1.1 当前前置条件

Phase 4 必须建立在以下能力稳定之后：

- 文档导入和 chunking 已完成。
- `source_ref` 已稳定。
- Tutor / Resource response 已保留 `source_refs`。
- Agent trace 已能展示 grounded sources。
- Phase 2/3 的 retrieval 或 reranking 结果可提供 chunk metadata。

### 1.2 本阶段目标

让评委能回答这三个问题：

```text
这个结论来自哪份资料？
来自哪个 chunk？
能否看到原文片段？
```

本阶段不是追求更强检索，而是追求更强可解释性。

## 2. 明确非目标

本阶段不做：

- 不做 PDF / Word 上传解析。
- 不做完整知识库管理后台。
- 不把整篇文档塞进前端。
- 不改变 Tutor / Resource API schema，除非后续单独立项并同步测试。
- 不让前端生成假的 citation。
- 不让 LLM 自由编造不存在的 source_ref。
- 不引入 PostgreSQL / pgvector 默认依赖。

## 3. 推荐技术路线

### 3.1 第一版能力

第一版只做轻量可见增强：

```text
source_ref
-> chunk excerpt
-> source detail metadata
-> frontend source panel / expandable citation
-> trace source reason
```

### 3.2 推荐优先级

| 功能 | 优先级 | 说明 |
|---|---|---|
| Source excerpt | P1 | 展示 chunk 短摘录 |
| Expandable source refs | P1 | 点击或展开查看资料片段 |
| Citation metadata | P1 | 展示 score、retrieval_mode、matched_terms |
| Inline citation prompt | P1 | 约束 LLM 在关键结论后引用 source |
| Citation coverage check | P2 | 检查回答段落是否有引用 |
| Full source viewer | P2 | 后续知识库管理阶段再做 |

## 4. 架构边界

### 4.1 推荐新增组件

```text
CitationService
SourceExcerptBuilder
```

推荐位置：

```text
src/backend/app/services/citation_service.py
```

或先在 `KnowledgeBaseService` 内部收敛 source excerpt 生成，等复杂度上升后再拆 service。

### 4.2 允许修改

- `src/backend/app/services/knowledge_base_service.py`
- `src/backend/app/services/tutor_service.py`
- `src/backend/app/services/resource_service.py`
- `src/backend/app/agents/tutor_prompts.py`
- `src/frontend/src/App.tsx`
- `src/frontend/src/styles.css`
- `tests/test_rag_citations.py`
- `src/frontend/tests/student-loop.spec.ts`

### 4.3 禁止修改方向

- 不在前端伪造 excerpt。
- 不在前端把 answer 文本解析成假的 source refs。
- 不让 LLM 输出未出现在 retrieved chunks 中的 source refs。
- 不把完整 chunk 大量塞进 Agent trace。
- 不破坏 `KnowledgeSearchResult` 兼容性。

## 5. Citation 数据设计

### 5.1 当前 source_ref 格式

继续使用：

```text
document:{document_id}#chunk:{chunk_index}
```

### 5.2 推荐 metadata

在 retrieval result metadata 中补充：

```json
{
  "document_id": 4,
  "chunk_id": 12,
  "source_ref": "document:4#chunk:3",
  "source_title": "bfs-dfs-rag-note.md",
  "chunk_index": 3,
  "char_start": 1200,
  "char_end": 1800,
  "excerpt": "BFS 使用队列逐层扩展...",
  "retrieval_mode": "hybrid",
  "keyword_score": 0.7,
  "vector_score": 0.91,
  "rerank_score": 0.88
}
```

### 5.3 Excerpt 规则

第一版 excerpt 应满足：

```text
长度 120-240 字符
不展示整篇文档
保留中文和英文关键术语
不包含 secret
不由 LLM 生成
```

## 6. 实现拆分

### 6.1 `IMPL-CITE-001`: Source Excerpt Metadata

目标：

- retrieval results 增加 source title 和 excerpt。
- 不改变 API schema，只扩展 metadata。

验收标准：

| ID | 标准 |
|---|---|
| CITE-AC1 | 每个命中 chunk metadata 包含 `source_ref` |
| CITE-AC2 | metadata 包含 `excerpt` |
| CITE-AC3 | excerpt 来自真实 chunk content |
| CITE-AC4 | excerpt 长度受控 |
| CITE-AC5 | 无 chunk 时不伪造 excerpt |

### 6.2 `IMPL-CITE-002`: Frontend Source Panel

目标：

- 前端 `Grounded source` 不只显示 source_ref 字符串。
- 可展开查看 source title、score、excerpt。

推荐 UI：

```text
Grounded sources
- document:4#chunk:3  score 0.88
  BFS 使用队列逐层扩展...
- document:4#chunk:4  score 0.76
  DFS 使用递归或栈深入搜索...
```

验收标准：

| ID | 标准 |
|---|---|
| PANEL-AC1 | Tutor answer 展示 source refs |
| PANEL-AC2 | source ref 可查看 excerpt |
| PANEL-AC3 | 长 excerpt 不破坏布局 |
| PANEL-AC4 | 空 source_refs 时显示 honest empty state |
| PANEL-AC5 | 前端不计算 retrieval score |

### 6.3 `IMPL-CITE-003`: Inline Citation Prompt

目标：

- 约束 LLM 在关键结论后使用已有 source refs。
- 避免自由编造 source refs。

Prompt 规则：

```text
Only cite source refs listed in the retrieved chunks.
Use citations after key claims, for example [document:4#chunk:3].
If no source supports a claim, say it is not covered by the current material.
```

验收标准：

| ID | 标准 |
|---|---|
| PROMPT-CITE-AC1 | LLM prompt 明确禁止伪造 source_ref |
| PROMPT-CITE-AC2 | 有 retrieved chunks 时 answer 包含至少一个真实 source_ref |
| PROMPT-CITE-AC3 | 无 retrieved chunks 时不输出假 citation |
| PROMPT-CITE-AC4 | rule-based fallback 仍保留真实 source_refs |

### 6.4 `IMPL-CITE-004`: Trace Source Detail

目标：

- Agent trace 显示来源摘要和使用原因。
- 不增加复杂 schema，优先复用 step 文本。

示例：

```text
Grounded sources:
- document:4#chunk:3, score=0.88, reason=covers BFS queue shortest path
- document:4#chunk:4, score=0.76, reason=covers DFS contrast
```

验收标准：

| ID | 标准 |
|---|---|
| TRACE-CITE-AC1 | Trace 展示具体 source_ref |
| TRACE-CITE-AC2 | Trace 展示简短 reason 或 matched_terms |
| TRACE-CITE-AC3 | Trace 不塞入完整 chunk 原文 |
| TRACE-CITE-AC4 | 无来源时 trace 不伪造来源 |

## 7. Citation Coverage Check

### 7.1 后续增强目标

检查 answer 中关键段落是否引用了真实 source_ref。

第一版不做复杂 NLP，只做轻量检查：

```text
answer contains at least one source_ref when source_refs non-empty
all cited source_refs are in retrieved source_refs
```

### 7.2 验收标准

| ID | 标准 |
|---|---|
| COVERAGE-AC1 | answer 中出现的 source_ref 都来自 retrieval result |
| COVERAGE-AC2 | 有 source_refs 但 answer 未引用时记录 warning metadata 或 trace note |
| COVERAGE-AC3 | citation check 不阻断 fallback answer |

## 8. 测试计划

### 8.1 后端测试

建议新增：

```text
tests/test_rag_citations.py
```

必须覆盖：

- metadata excerpt 来自真实 chunk。
- excerpt 长度受控。
- LLM prompt 只允许已有 source refs。
- answer 中伪造 source_ref 可被检测。
- trace source detail 不包含完整 chunk。

### 8.2 前端测试

更新：

```text
src/frontend/tests/student-loop.spec.ts
```

覆盖：

- Tutor answer source panel 可见。
- excerpt 可见。
- 长 source_ref 不撑破布局。
- 无 source_refs 时 empty state 正常。

### 8.3 完整验证

```powershell
python -m unittest tests.test_rag_citations tests.test_rag_retrieval tests.test_llm_provider_tutor tests.test_backend_contracts -v
npm run build
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

## 9. Reviewer 检查清单

### Blocking

- citation 由前端硬编码。
- LLM 可以输出不存在的 source_ref 且没有检测。
- source_refs 与 retrieval result 不一致。
- 为 citation 改破 API contract。
- 默认本地演示需要外部 provider。

### Fix Before Merge

- excerpt 不是来自真实 chunk。
- excerpt 过长导致 UI 溢出。
- 无资料时伪造 source。
- trace 塞入完整 chunk 原文。
- source panel 展示 secret 或敏感环境变量。

### Optional

- 点击跳转完整文档。
- 高亮 answer 中对应句子。
- citation coverage score。
- 文档级 source browser。

## 10. Builder 自检格式

```text
Self-review:
- RAG phase: Phase 4
- Increment ID:
- API contract changed: Yes/No
- Citation source from retrieval result: Yes/No
- Frontend hardcoded citation: Yes/No
- Excerpt length controlled: Yes/No
- Fake citation prevented/detected: Yes/No
- Trace source detail added: Yes/No
- Tests run:
- Manual demo steps:
- Known gaps:
- Ready for review: Yes/No
```

## 11. 最终合并标准

允许合并的最低标准：

- citation 只来自真实 retrieval results。
- source excerpt 可见且长度受控。
- answer / trace 中的 source_refs 可追踪。
- 无资料时不伪造引用。
- 不改变默认 SQLite / keyword / hybrid 检索路径。
