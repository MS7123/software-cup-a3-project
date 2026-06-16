# RAG Phase 5 Knowledge Management Plan

最后更新：2026-06-16

面向角色：Builder Agent / Reviewer Agent

本文档定义 RAG Phase 5：full knowledge management。目标是在 Phase 1-4 已经完成资料导入、检索、hybrid retrieval、reranking 和 citation quality 的基础上，把 RAG 从“能导入一段资料并回答”推进到“能管理课程知识、支持多资料来源、支持用户私有知识库、保持演示稳定”的阶段。

## 1. 阶段定位

### 1.1 当前前置条件

Phase 5 必须建立在以下能力稳定之后：

- Phase 1 keyword RAG 已完成。
- Phase 2 hybrid retrieval 已完成，默认方案是 SQLite + Python cosine similarity。
- Phase 3 reranking 已完成，且默认关闭远程 rerank provider。
- Phase 4 citation quality 已完成，`source_ref`、`excerpt`、`source_refs` 和 source panel 可用于展示证据。
- `Document`、`DocumentChunk`、`ChunkEmbedding` 已能支持最小知识库数据流。

### 1.2 本阶段目标

Phase 5 的目标是补齐比赛演示中“知识库像一个真实系统”的关键体验：

```text
course documents
-> document management
-> parsing and chunking
-> optional embedding indexing
-> user/course scoped retrieval
-> grounded Tutor / Resource / Evaluator
-> visible source evidence
```

本阶段不是要一次性做成生产级知识库平台，而是优先保证评委能看到：

- 课程资料可以被管理，而不只是终端导入。
- 多份资料可以共存、查询和删除。
- 知识库内容可以按 course / user scope 隔离。
- PDF / Word 等常见文件有明确接入路径。
- 默认本地部署仍然轻量，不强制 PostgreSQL / pgvector。

## 2. 明确非目标

Phase 5 第一版不做：

- 不强制引入 PostgreSQL。
- 不强制引入 pgvector。
- 不引入 Chroma / FAISS 作为默认依赖。
- 不做完整权限系统和组织级知识库。
- 不做复杂文件版本控制系统。
- 不做在线协同编辑。
- 不把前端上传文件后直接在浏览器里 chunking。
- 不让 API handler 承载 parser / chunking / embedding / retrieval 业务逻辑。
- 不改变 Tutor / Resource / Quiz / Evaluator 已有 API contract。
- 不让无 API key / 无网络的默认 demo 失效。

## 3. 推荐总体路线

### 3.1 默认路线

默认路线继续保持轻量：

```text
SQLite
+ backend file upload / paste ingestion
+ parser adapter
+ chunking service
+ optional embedding index
+ KnowledgeBaseService scoped search
```

默认数据库：

```text
SQLite
```

默认向量检索：

```text
SQLite chunk_embeddings table
+ Python cosine similarity
```

默认文件处理：

```text
text / markdown / PDF / Word
-> backend parser adapter
-> normalized plain text
-> chunking
-> DocumentChunk
```

### 3.2 后续增强路线

后续增强必须是 opt-in：

| 能力 | 默认方案 | 后续增强方案 | 当前 Phase 5 第一版是否强制 |
|---|---|---|---:|
| relational database | SQLite | PostgreSQL | 否 |
| vector search | Python cosine similarity | pgvector / dedicated vector store | 否 |
| parser | local lightweight parser adapter | OCR / layout-aware parser | 否 |
| file storage | local filesystem or database metadata | object storage | 否 |
| knowledge scope | course / user scope | organization / class scope | 否 |
| reranking | rule-based reranker | provider rerank / cross-encoder | 否 |

## 4. 架构边界

### 4.1 推荐新增组件

推荐新增或扩展以下后端组件：

```text
DocumentManagementService
DocumentFileStorage
DocumentParserRegistry
PdfDocumentParser
WordDocumentParser
KnowledgeScopeResolver
```

推荐位置：

```text
src/backend/app/services/document_management_service.py
src/backend/app/services/document_storage_service.py
src/backend/app/adapters/document_parsers.py
```

如果当前 parser 已集中在 ingestion service 附近，也可以先在现有 parser adapter 文件内扩展，避免过早拆分。

### 4.2 允许修改

- `src/backend/app/api/*documents*` 或现有 document router。
- `src/backend/app/services/document_ingestion_service.py`
- `src/backend/app/services/knowledge_base_service.py`
- `src/backend/app/services/embedding_index_service.py`
- `src/backend/app/models.py`
- `src/backend/app/schemas.py`
- `src/frontend/src/App.tsx`
- `src/frontend/src/styles.css`
- `tests/test_rag_ingestion.py`
- `tests/test_rag_retrieval.py`
- `tests/test_document_management.py`
- `docs/process/05-agile-development-log.md`

### 4.3 禁止修改方向

- 不在 frontend 实现文件解析、chunking、embedding 或 retrieval scoring。
- 不在 API handler 中写 parser / chunking / indexing 细节。
- 不把用户上传文件硬编码成 demo answer。
- 不让删除资料后旧 chunk 继续参与 retrieval。
- 不让不同 course / user 的 private documents 被无意召回。
- 不把 PostgreSQL / pgvector 写成默认启动条件。
- 不破坏现有 JSON paste ingestion 路径。

## 5. 数据模型建议

### 5.1 当前模型继续保留

继续保留：

```text
Document
DocumentChunk
ChunkEmbedding
```

### 5.2 推荐补充字段

如果现有模型字段不足，优先以兼容方式补充：

| 字段 | 推荐位置 | 用途 |
|---|---|---|
| `owner_user_id` | `Document` | 标记用户私有资料 |
| `visibility` | `Document` | `course` / `private` / `demo` |
| `file_name` | `Document` | 原始文件名 |
| `mime_type` | `Document` | 文件类型 |
| `file_size` | `Document` | 文件大小展示和限制 |
| `parser_name` | `Document` | 记录使用的 parser |
| `status` | `Document` | `ready` / `failed` / `deleted` |
| `error_message` | `Document` | 解析失败原因 |

如果本轮不想做数据库 migration，可以先将非关键字段放入 existing metadata JSON；但 `visibility` 和 `owner_user_id` 如果要做 scope 隔离，建议成为明确字段或有稳定查询方式。

### 5.3 删除策略

第一版建议使用硬删除或软删除二选一，不混用。

推荐比赛默认：

```text
soft delete document
exclude deleted documents/chunks from search
keep trace source_refs readable
```

最低要求：

- 删除 document 后，新 retrieval 不再召回其 chunks。
- 已生成历史 answer / trace 可以继续显示旧 `source_ref` 字符串。
- 不要求历史 trace 反查完整原文。

## 6. Scope 设计

### 6.1 Course knowledge

课程级知识库用于教师或 demo seed 资料：

```text
course_id = 1
visibility = course / demo
owner_user_id = null
```

所有该课程学生都可以检索。

### 6.2 User private knowledge

用户私有知识库用于学生上传自己的笔记：

```text
course_id = 1
visibility = private
owner_user_id = current user/profile user
```

检索时必须满足：

```text
same course
AND (
  visibility in course/demo
  OR owner_user_id == current user
)
```

当前项目如果尚未实现完整 auth/user session，可以先用 `student_profile.user_id` 或显式 `user_id` 字段作为最小 scope key，后续再接正式认证。

## 7. File Parsing 路线

### 7.1 第一版支持格式

| source type | 第一版处理方式 | 阻塞默认 demo |
|---|---|---:|
| text | 已有 plain text parser | 否 |
| markdown | 已有 markdown parser | 否 |
| PDF | backend parser adapter 提取文本 | 否 |
| Word `.docx` | backend parser adapter 提取文本 | 否 |

### 7.2 Parser adapter contract

建议统一 parser 输出：

```python
class ParsedDocument:
    title: str
    text: str
    metadata: dict
```

Parser 只负责：

- 校验文件类型。
- 提取文本。
- 返回 metadata。
- 抛出可转为 4xx 的解析错误。

Parser 不负责：

- chunking。
- embedding。
- retrieval。
- LLM generation。
- API response assembly。

### 7.3 PDF / Word 最小实现

PDF 第一版：

```text
pypdf or pdfplumber
-> extract text by page
-> join with page markers
-> chunk
```

Word 第一版：

```text
python-docx
-> extract paragraphs and tables as text
-> chunk
```

第一版不做 OCR。扫描版 PDF 可返回明确错误：

```text
No extractable text found. OCR is not supported in the current demo mode.
```

## 8. 实现拆分

### 8.1 `IMPL-KM-001`: Document List and Delete

目标：

- 前端能看到当前 course 的 documents。
- 后端提供 document list / detail / delete。
- 删除后资料不再参与 retrieval。

建议 API：

```text
GET /api/v1/courses/{course_id}/documents
GET /api/v1/documents/{document_id}
DELETE /api/v1/documents/{document_id}
```

验收标准：

| ID | 标准 |
|---|---|
| KM-LIST-AC1 | 前端能展示 document title、source_type、chunk_count、status |
| KM-LIST-AC2 | 删除 document 后 search 不再返回其 chunks |
| KM-LIST-AC3 | 删除 document 不破坏已有 Agent trace 展示 |
| KM-LIST-AC4 | API handler 不包含 delete cascade 业务逻辑 |
| KM-LIST-AC5 | 默认 demo seed documents 可按规则保留或禁止删除 |

### 8.2 `IMPL-KM-002`: Multipart File Upload

目标：

- 保留现有 JSON paste ingestion。
- 新增 multipart 文件上传入口。
- 文件解析仍在 backend parser adapter。

建议 API：

```text
POST /api/v1/courses/{course_id}/documents/upload
```

请求：

```text
multipart/form-data
file
title optional
visibility optional
owner_user_id optional
```

验收标准：

| ID | 标准 |
|---|---|
| KM-UPLOAD-AC1 | 上传 `.txt` / `.md` 可创建 document 和 chunks |
| KM-UPLOAD-AC2 | 上传超大文件返回明确 4xx 错误 |
| KM-UPLOAD-AC3 | 不支持的文件类型返回明确 4xx 错误 |
| KM-UPLOAD-AC4 | upload endpoint 不执行 retrieval scoring |
| KM-UPLOAD-AC5 | JSON paste ingestion 回归通过 |

### 8.3 `IMPL-KM-003`: PDF and Word Parser

目标：

- 支持 PDF / Word 文本提取。
- 保持扫描版或解析失败时的清晰 fallback。

验收标准：

| ID | 标准 |
|---|---|
| KM-PARSER-AC1 | 文本型 PDF 能提取正文并生成 chunks |
| KM-PARSER-AC2 | `.docx` 能提取段落文本并生成 chunks |
| KM-PARSER-AC3 | 解析失败不会留下半成品 chunks |
| KM-PARSER-AC4 | parser metadata 记录 file type 和 parser name |
| KM-PARSER-AC5 | 不支持 OCR 时返回 honest error |

### 8.4 `IMPL-KM-004`: Knowledge Scope Filter

目标：

- 支持 course knowledge 与 user private knowledge 的最小隔离。
- 检索时不会串资料。

验收标准：

| ID | 标准 |
|---|---|
| KM-SCOPE-AC1 | course document 可被同课程请求检索 |
| KM-SCOPE-AC2 | private document 只被同 owner 检索 |
| KM-SCOPE-AC3 | 不同 course 的 document 不会被召回 |
| KM-SCOPE-AC4 | Tutor / Resource 使用相同 scope 规则 |
| KM-SCOPE-AC5 | scope 缺失时默认只查 course/demo knowledge |

### 8.5 `IMPL-KM-005`: Embedding Reindex Control

目标：

- 前端或 API 能触发单个 document reindex。
- 仍然默认关闭 embedding。
- 失败时不影响 keyword retrieval。

建议 API：

```text
POST /api/v1/documents/{document_id}/reindex
```

验收标准：

| ID | 标准 |
|---|---|
| KM-INDEX-AC1 | `RAG_EMBEDDING_ENABLED=false` 时不会强制远程 embedding |
| KM-INDEX-AC2 | reindex 只处理目标 document chunks |
| KM-INDEX-AC3 | content hash 相同的 chunk 可跳过重复 embedding |
| KM-INDEX-AC4 | embedding 失败后 keyword search 仍可用 |
| KM-INDEX-AC5 | metadata 显示 indexed / skipped / failed 结果 |

### 8.6 `IMPL-KM-006`: Knowledge Management UI

目标：

- 前端有一个轻量知识库管理区域。
- 评委不需要终端导入资料即可演示。

推荐 UI 能力：

```text
Knowledge setup
- paste text / markdown
- upload file
- document list
- search test
- source preview
- delete document
- reindex document
```

验收标准：

| ID | 标准 |
|---|---|
| KM-UI-AC1 | 用户可从页面上传或粘贴资料 |
| KM-UI-AC2 | 用户可看到 document list 和 chunk_count |
| KM-UI-AC3 | 用户可删除非保护 document |
| KM-UI-AC4 | 用户可运行 search test 并看到 source_refs |
| KM-UI-AC5 | 空状态、解析失败、上传中状态都有明确 UI |

## 9. API Contract 原则

### 9.1 允许新增 API

允许新增：

```text
GET /api/v1/courses/{course_id}/documents
GET /api/v1/documents/{document_id}
DELETE /api/v1/documents/{document_id}
POST /api/v1/courses/{course_id}/documents/upload
POST /api/v1/documents/{document_id}/reindex
```

### 9.2 不允许破坏已有 API

不得破坏：

```text
POST /api/v1/courses/{course_id}/documents
GET /api/v1/documents/{document_id}/chunks
POST /api/v1/knowledge/search
POST /api/v1/tutor/ask
POST /api/v1/resources/generate
```

### 9.3 Response schema 策略

新增字段优先放在：

```text
metadata
status
source_refs
```

不得删除或重命名已有字段。

## 10. 性能和部署约束

### 10.1 默认本地部署

默认部署必须仍然满足：

```text
SQLite
no PostgreSQL required
no vector database required
no embedding key required
no LLM key required for smoke
```

### 10.2 文件大小限制

建议第一版限制：

| 类型 | 建议上限 |
|---|---:|
| text / markdown | 1 MB |
| PDF | 5 MB |
| Word | 5 MB |
| chunks per document | 200 |

超出限制返回明确 4xx 错误，不进入 parser。

### 10.3 增强数据库预留

PostgreSQL / pgvector 后续接入时应通过 repository / service 边界替换实现：

```text
KnowledgeBaseService
-> RetrievalRepository protocol
-> SQLiteRetrievalRepository / PostgresRetrievalRepository
```

Phase 5 第一版不要为了未来 pgvector 重写当前 SQLite flow。

## 11. 测试计划

### 11.1 后端测试

建议新增：

```text
tests/test_document_management.py
tests/test_document_upload.py
tests/test_document_scope.py
```

必须覆盖：

- document list。
- document delete 后 search 不召回。
- upload txt / markdown。
- unsupported file type。
- parser failure rollback。
- course scope isolation。
- private scope isolation。
- embedding disabled fallback。

### 11.2 前端测试

更新：

```text
src/frontend/tests/student-loop.spec.ts
```

覆盖：

- 页面上传或粘贴资料。
- document list 可见。
- search test 可见 source refs。
- 删除 document 后 search 不再命中。
- parser error 显示。

### 11.3 完整验证

```powershell
python -m unittest tests.test_document_management tests.test_rag_ingestion tests.test_rag_retrieval tests.test_backend_contracts -v
npm run build
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

## 12. 手动演示方案

### 12.1 默认离线演示

```text
1. 启动本地应用。
2. 点击 Load demo data。
3. 在 Knowledge setup 上传或粘贴一份 BFS/DFS 资料。
4. 在 document list 中确认 title、chunk_count、status。
5. 搜索 “为什么 BFS 第一次到达节点代表最少边数，请和 DFS 对比”。
6. 确认 source refs、excerpt、retrieval metadata 可见。
7. 向 Tutor 提问同一问题。
8. 确认 Tutor answer 引用了真实 source。
9. 删除上传资料。
10. 再次搜索，确认旧资料不再被召回。
```

### 12.2 Hybrid / LLM 演示

仅当本地配置 API key 时启用：

```text
RAG_EMBEDDING_ENABLED=true
RAG_RETRIEVAL_MODE=hybrid
RAG_RERANK_ENABLED=true
LLM_ENABLE_FOR_TUTOR=true
```

必须确认：

- provider 失败时 fallback 到 keyword retrieval。
- embedding 失败时不影响 document list。
- LLM 失败时 Tutor fallback 仍能显示 grounded sources。

## 13. Reviewer 检查清单

### Blocking

- 默认本地部署必须安装 PostgreSQL / pgvector 才能启动。
- 删除 document 后仍能在 search 中召回其 chunks。
- private document 被其他 user / profile 检索到。
- API handler 或 frontend 承载 parser / chunking / retrieval scoring。
- PDF / Word 解析失败导致半成品数据污染。
- 破坏已有 RAG JSON paste ingestion。
- 破坏 Tutor / Resource API contract。

### Fix Before Merge

- document list 缺少 status 或错误信息。
- 文件大小无限制。
- unsupported file type 报 500。
- parser failure 没有 rollback。
- embedding reindex 失败阻断 keyword retrieval。
- source_refs 与实际 chunks 不一致。
- 前端没有 upload / delete 的 loading 或 error state。

### Optional

- OCR。
- 文件版本管理。
- 知识库标签系统。
- 批量上传。
- 全文 source browser。
- PostgreSQL / pgvector repository implementation。
- object storage。

## 14. Builder 自检格式

```text
Self-review:
- RAG phase: Phase 5
- Increment ID:
- Default database remains SQLite: Yes/No
- PostgreSQL required: Yes/No
- Existing JSON ingestion preserved: Yes/No
- API contract changed: Yes/No
- API handler contains parser/chunking/retrieval logic: Yes/No
- Frontend contains parser/chunking/retrieval logic: Yes/No
- Delete excludes chunks from search: Yes/No
- Course/private scope enforced: Yes/No
- Parser failure rollback: Yes/No
- Tests run:
- Manual demo steps:
- Known gaps:
- Ready for review: Yes/No
```

## 15. 最终合并标准

允许合并的最低标准：

- 默认 SQLite 本地演示不受影响。
- 不需要 PostgreSQL / pgvector / vector database。
- 已有 text / markdown JSON ingestion 不回归。
- 新增 document management API 和 UI 可演示。
- 删除资料后 search / Tutor / Resource 不再使用旧 chunks。
- scope 规则不会串 course / private knowledge。
- parser、chunking、embedding、retrieval 均保持在 service / adapter 边界内。
- 无 API key / 无网络时仍能完成核心 demo。
