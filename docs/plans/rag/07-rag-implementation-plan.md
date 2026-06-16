# 真实 RAG 最小闭环实现计划

最后更新：2026-06-13

面向角色：Builder Agent / 敏捷开发 Agent

本文档用于指导下一轮真实 RAG 增量开发。目标是把当前 demo chunk 检索升级为“真实课程资料导入、chunking、可追踪检索、source_refs 引用”的最小闭环，而不是一次性完成完整 RAG 平台。

## 1. 当前结论

不要一上来做 `PostgreSQL + pgvector + 完整上传解析平台`。

当前最稳实现路径是：

```text
真实课程资料
-> Document record
-> Chunking
-> SQLite keyword retrieval
-> Tutor / Resource grounded generation
-> source_refs / Agent trace
```

第一阶段只做 `.txt` / `.md` 文本内容导入和 SQLite keyword retrieval。等这条链路稳定后，再考虑 `VectorStore` / Chroma / embedding。

## 2. 当前代码基础

已有可复用基础：

- `documents` / `document_chunks` 表已存在。
- `DocumentChunk` 已包含：
  - `content`
  - `vector_ref`
  - `metadata_json`
  - `source_ref`
  - `concept_id`
- `KnowledgeBaseService.search()` 已被 `TutorService`、`ResourceService`、`AssessmentService` 使用。
- `VectorStore`、`DocumentParser` protocol 已存在。
- Tutor / Resource 已能接收 `KnowledgeSearchResult.source_ref` 并返回引用来源。
- 默认本地演示和 smoke 已通过 `DemoDataService` 提供稳定数据底座。

当前关键缺口：

- `KnowledgeBaseService.search()` 当前隐式调用 `DemoDataService.load_demo_data()`，真实 RAG 不应有这个副作用。
- 当前检索仍是 demo chunk 的简单 substring / fixed score。
- 没有课程资料导入 API。
- 没有 `DocumentParser` 实现。
- 没有 `ChunkingService`。
- 没有真实 `VectorStore` adapter。

## 3. 第一阶段目标

第一阶段目标是完成真实 RAG 最小闭环：

```text
用户提交一段数据结构课程资料
-> 后端创建 Document
-> 后端切分为 DocumentChunk
-> KnowledgeBaseService.search() 能从这些 chunks 中检索
-> Tutor / Resource 使用检索结果
-> response 和 Agent trace 中保留 source_refs
```

必须保持：

- 默认本地 demo 不依赖外部网络。
- 默认本地 demo 不依赖真实 LLM。
- 默认本地 demo 不依赖 Chroma、pgvector、PostgreSQL。
- 现有 `/api/v1/tutor/ask`、`/api/v1/resources/generate` response schema 不变。
- 当前 Playwright smoke 主流程仍可运行。

## 4. 明确非目标

第一阶段不要做：

- `PostgreSQL` / `pgvector` 迁移。
- Chroma / FAISS / Qdrant / Milvus。
- embedding provider。
- PDF / Word / PPT 解析。
- multipart 文件上传。
- 大文件存储。
- 异步任务队列。
- rerank。
- 复杂文档管理后台。
- 让 LLM 直接读全文替代 retrieval。
- 把真实 RAG 和真实 LLM、Resource、Quiz、Evaluator 同时大改。

这些可以作为后续阶段，但不得进入第一阶段最小增量。

## 5. 实现边界

### API Layer

允许：

- 接收课程资料导入请求。
- 调用 `DocumentIngestionService`。
- 返回 document / chunk / search response。
- 把 domain exception 转换为 HTTP error。

禁止：

- 在 API handler 中切分文档。
- 在 API handler 中计算相似度。
- 在 API handler 中写死 demo chunks。
- 在 API handler 中直接调用 Chroma、embedding SDK、LLM SDK。

### Domain Services

建议新增：

- `DocumentIngestionService`
  - 校验 course 是否存在。
  - 创建 `Document`。
  - 调用 parser。
  - 调用 chunker。
  - 写入 `DocumentChunk`。
  - 生成稳定 `source_ref`。

- `ChunkingService`
  - 负责 chunk size。
  - 负责 overlap。
  - 负责 `char_start` / `char_end` metadata。
  - 不访问 HTTP 层。
  - 不访问 LLM / VectorStore。

建议改造：

- `KnowledgeBaseService`
  - 只负责检索。
  - 返回 `KnowledgeSearchResult`。
  - 不再隐式调用 `DemoDataService.load_demo_data()`。
  - 不直接 import 具体 vector DB SDK。

### Adapters

第一阶段实现：

- `PlainTextDocumentParser`
- `MarkdownDocumentParser`

第一阶段可保持 very thin：

```text
输入 content
-> 输出纯文本段落
```

注意：当前 `DocumentParser` protocol 是 `parse(source_ref: str) -> list[str]`。如果第一阶段采用 JSON body 直接提交 content，可以选择：

- 新增更适合当前需求的 parser interface；或
- 在 implementation 中把 `source_ref` 解释为原始文本。

无论选择哪种方式，都必须保持 parser 逻辑在 adapter / service 边界内，不能写到 API handler。

### Frontend

第一阶段前端不是必须。如果要做前端入口，只做最小粘贴导入：

- 输入标题。
- 输入 `source_type`。
- 粘贴课程资料文本。
- 调用后端导入 API。
- 展示导入成功和 chunk 数量。

禁止：

- 前端切分文档。
- 前端模拟检索结果。
- 前端硬编码 source refs。
- 前端直接访问向量库或 LLM。

## 6. 推荐任务拆分

### IMPL-011: 文本资料导入与 chunking

目标：

实现 `.txt` / `.md` 内容导入，生成 `documents` 和 `document_chunks`。

建议 API：

```text
POST /api/v1/courses/{course_id}/documents
GET  /api/v1/documents/{document_id}/chunks
```

第一版请求体使用 JSON，不做 multipart：

```json
{
  "title": "bfs-note.md",
  "source_type": "markdown",
  "content": "BFS 按层扩展，可用于无权图最短路径..."
}
```

实现范围：

- 新增 request / response schema。
- 新增 `DocumentIngestionService`。
- 新增 `ChunkingService`。
- 新增 plain text / markdown parser implementation。
- 写入 `Document`。
- 写入多条 `DocumentChunk`。
- 生成稳定 `source_ref`。
- 失败时返回明确 error，不产生半完成脏数据。

`source_ref` 规范：

```text
document:{document_id}#chunk:{chunk_index}
```

chunk metadata 建议包含：

```json
{
  "chunk_index": 0,
  "filename": "bfs-note.md",
  "parser": "markdown",
  "char_start": 0,
  "char_end": 600
}
```

不做：

- 检索策略大改。
- Chroma / embedding。
- PDF / Word / PPT。
- PostgreSQL migration。
- 前端复杂上传页。

验收标准：

- `POST /api/v1/courses/{course_id}/documents` 可导入一段 `.txt` 或 `.md` 内容。
- 导入后数据库存在 1 条 `Document`。
- 导入后数据库存在至少 1 条 `DocumentChunk`。
- chunk `source_ref` 使用 `document:{document_id}#chunk:{chunk_index}`。
- chunk metadata 包含 `chunk_index`、`char_start`、`char_end`。
- API handler 不包含 chunking 逻辑。
- 文档导入失败有明确错误，不破坏已有 demo data。
- `python -m unittest discover -s tests -v` 通过。

### IMPL-012: KnowledgeBaseService 真实检索改造

目标：

让 `KnowledgeBaseService.search()` 从数据库中的真实 `document_chunks` 检索，不再隐式加载 demo data。

建议 API：

```text
POST /api/v1/knowledge/search
```

第一版请求体：

```json
{
  "course_id": 1,
  "query": "BFS 为什么适合最短路径",
  "top_k": 3
}
```

实现范围：

- 移除 `KnowledgeBaseService.search()` 中的隐式 `DemoDataService.load_demo_data()`。
- 基于 `DocumentChunk.content`、`source_ref`、`metadata_json` 做 keyword scoring。
- 返回 `KnowledgeSearchResult`。
- metadata 中增加：
  - `document_id`
  - `chunk_id`
  - `source_ref`
  - `score`
  - `retrieval_mode=keyword`
- Tutor / Resource 继续复用 `KnowledgeBaseService.search()`。
- 没有资料时返回空结果或让现有 fallback 生效，不能偷偷加载 demo data。

验收标准：

- 未加载 demo data 时，导入真实资料后 search 能命中该资料 chunk。
- search 不再自动创建 demo course / demo chunks。
- Tutor 使用真实资料时，response `source_refs` 指向真实导入 document chunk。
- Resource 使用真实资料时，response `source_refs` 指向真实导入 document chunk。
- 没有资料时，Tutor / Resource 不崩溃，走空资料 fallback 或明确资料不足提示。
- 现有 `run-local.ps1` 演示仍通过，因为脚本会显式加载 demo data。
- `./scripts/verify.ps1` 通过。

### TEST-RAG-001: RAG API 与 grounded source 测试

目标：

补齐 RAG 最小闭环自动化验证。

必须覆盖：

- 导入 `.txt` / `.md` 内容。
- chunks 入库。
- `KnowledgeBaseService.search()` 命中真实 chunk。
- Tutor response 保留真实 `source_refs`。
- Resource response 保留真实 `source_refs`。
- 未加载 demo data 时 search 不隐式 seed。
- API handler 不 import parser / vector SDK 细节。

建议测试文件：

```text
tests/test_rag_ingestion.py
tests/test_rag_retrieval.py
```

### IMPL-013: VectorStore / Chroma opt-in

目标：

在不改变 API schema 的情况下，把 retrieval 从 keyword 扩展为可选 vector search。

前置条件：

- IMPL-011 通过。
- IMPL-012 通过。
- 默认 keyword retrieval 已稳定。

范围：

- 实现 `VectorStore` adapter。
- 可选 Chroma。
- 增加 embedding provider 边界。
- `document_chunks.vector_ref` 保存向量索引引用。
- `KnowledgeBaseService.search()` 根据配置选择：
  - `RAG_RETRIEVAL_MODE=keyword`
  - `RAG_RETRIEVAL_MODE=vector`
  - `RAG_RETRIEVAL_MODE=hybrid`

不建议作为第一阶段任务。

## 7. 配置约定

第一阶段新增：

```text
RAG_RETRIEVAL_MODE=keyword
RAG_CHUNK_SIZE=600
RAG_CHUNK_OVERLAP=80
RAG_AUTO_INDEX=false
```

默认本地 demo 保持：

```text
RAG_RETRIEVAL_MODE=keyword
```

第二阶段 VectorStore 再考虑：

```text
VECTOR_STORE_PROVIDER=chroma
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_PROVIDER=...
EMBEDDING_MODEL=...
EMBEDDING_API_KEY=...
```

任何新增 secret 都不得写入仓库、测试输出、frontend bundle 或 Agent trace。

## 8. 验收标准

RAG 最小闭环验收项：

| ID | 验收标准 |
|---|---|
| RAG-AC1 | 系统能通过 JSON body 导入至少一种真实课程资料格式，第一阶段为 `.txt` 或 `.md` |
| RAG-AC2 | 导入后系统能创建 `documents` 和 `document_chunks`，chunk 包含稳定 `source_ref` |
| RAG-AC3 | `KnowledgeBaseService.search()` 能基于真实导入资料返回相关 chunk，不依赖 demo data 自动加载 |
| RAG-AC4 | `Tutor Agent` 使用真实检索结果时，response 中保留真实 `source_refs` |
| RAG-AC5 | `Resource Agent` 使用真实检索结果时，response 中保留真实 `source_refs` |
| RAG-AC6 | 默认本地 smoke 不依赖真实 VectorStore、embedding provider、PostgreSQL 或外部网络 |
| RAG-AC7 | API handler 和 frontend 不实现 chunking / retrieval 逻辑 |
| RAG-AC8 | RAG 实现通过 `DocumentParser` / service / `VectorStore` adapter 边界组织 |
| RAG-AC9 | 没有资料或检索不到资料时，Tutor / Resource 不崩溃，并给出明确 fallback 或资料不足提示 |
| RAG-AC10 | `./scripts/verify.ps1` 通过 |

## 9. Review 检查清单

Reviewer 应检查：

- `KnowledgeBaseService.search()` 是否仍有隐式 `load_demo_data()`。
- API handler 是否包含 chunking、scoring、parser、vector SDK 细节。
- 前端是否模拟 chunks、source_refs 或 retrieval result。
- `DocumentIngestionService` 是否负责导入流程，而不是把逻辑散落在 router。
- chunk 是否可追踪到 document。
- `source_refs` 是否进入 Tutor / Resource response。
- Agent trace 是否能看到检索或来源依据。
- 是否保持 `/api/v1/tutor/ask` 和 `/api/v1/resources/generate` schema 稳定。
- 是否把真实 RAG 和真实 LLM 强绑定。
- 默认 smoke 是否仍然离线可运行。
- 是否引入了未记录的新依赖或 secret。

## 10. Builder 自审格式

每轮 RAG 增量结束前，Builder 必须输出：

```text
Self-review:
- RAG task:
- API/schema changed: Yes/No
- Database model changed: Yes/No
- KnowledgeBaseService implicit demo load removed/kept:
- Source refs verified: Yes/No
- Tutor/Resource grounded flow checked: Yes/No
- Default offline smoke preserved: Yes/No
- Tests run:
- Known gaps:
- Ready for review: Yes/No
```

## 11. 最小落地顺序

推荐顺序：

```text
IMPL-011 文档导入 + chunking
-> IMPL-012 KnowledgeBaseService 真实检索
-> TEST-RAG-001 RAG API / Tutor / Resource grounded source 测试
-> IMPL-013 Chroma VectorStore opt-in
```

如果只能做一个可演示增量，优先做：

```text
IMPL-011 + IMPL-012 的收窄版：
JSON 文本导入 + chunking + SQLite keyword retrieval + source_ref
```

该增量足以把项目从“demo chunk retrieval”推进到“真实资料 RAG 最小闭环”。
