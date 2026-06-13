# 后续可演示增量计划

最后更新：2026-06-13

面向角色：Builder Agent / Reviewer Agent

本文档用于指导 RAG 第一阶段之后的 4 个轻量可演示增量。目标是在不恢复旧的重多 Agent 流程、不引入大规模架构迁移的前提下，继续推进 A3 主线：

```text
画像 -> 学习路径 -> 资源生成 -> Tutor -> Quiz -> Evaluator -> Agent trace
```

当前已完成基础：

- 后端支持 `text` / `markdown` JSON 资料导入。
- 后端支持 `documents` / `document_chunks` 入库。
- `KnowledgeBaseService.search()` 已改为基于真实导入 chunk 的 keyword retrieval。
- Tutor / Resource 可保留真实 `source_refs`。
- 默认本地演示仍保持离线可运行，不强依赖 LLM、网络、PostgreSQL、Chroma 或 pgvector。

## 1. 前端知识导入 UI

### 目标

让演示者不再只能通过终端、Postman 或 Swagger 导入知识资料，而是在现有前端演示页面中完成最小文本导入。

### 比赛价值

- 评委能直观看到系统从真实课程资料进入 RAG 链路。
- 降低人工演示门槛。
- 让 `Tutor` 的 grounded answer 与导入资料形成可见闭环。

### 实现边界

允许：

- 新增一个轻量 `Knowledge setup` 区域。
- 提供 `title` 输入框。
- 提供 `source_type` 选择，第一版只支持 `text` / `markdown`。
- 提供 `content` 文本框，用于粘贴课程资料。
- 调用 `POST /api/v1/courses/{course_id}/documents`。
- 导入成功后显示 `document_id`、`chunk_count`、前 3 个 `source_ref`。
- 可选增加一个小型 search 验证框，调用 `POST /api/v1/knowledge/search`。

禁止：

- 不做 multipart 文件上传。
- 不做 PDF / Word / PPT 解析。
- 不在前端切分文档。
- 不在前端模拟 retrieval result。
- 不在前端硬编码 `source_ref`。
- 不改变现有 Tutor / Resource API contract。

### 实现路径

1. 找到当前前端主演示页面和 API client 组织方式。
2. 在课程或 Tutor 相关区域附近加入 `Knowledge setup`，避免做成独立复杂后台。
3. 新增 API client 方法：
   - `ingestCourseDocument(courseId, payload)`
   - 可选：`searchKnowledge(payload)`
4. 前端 state 至少包含：
   - `title`
   - `sourceType`
   - `content`
   - `isImporting`
   - `importResult`
   - `importError`
5. 导入成功后保留结果，便于下一步直接在 Tutor 输入问题测试。

### 验收标准

| ID | 标准 |
|---|---|
| UI-AC1 | 用户能在前端粘贴一段课程资料并点击导入 |
| UI-AC2 | 导入成功后显示 `document_id`、`chunk_count` 和至少 1 个 `source_ref` |
| UI-AC3 | 导入失败时有明确错误提示，页面不崩溃 |
| UI-AC4 | 前端不包含 chunking、retrieval scoring 或硬编码 source refs |
| UI-AC5 | 导入资料后，Tutor 提问能引用刚导入的 `document:{id}#chunk:{index}` |
| UI-AC6 | `npm run build` 通过 |
| UI-AC7 | Playwright smoke 通过或人工记录无法运行原因 |

### Reviewer 重点

- 检查前端是否只是调用后端 API。
- 检查是否有 hardcoded demo answer。
- 检查空内容、导入中、导入失败状态。
- 检查移动端或窄屏下按钮和文本框是否明显溢出。

## 2. LLM + RAG Tutor 手动验证

### 目标

验证真实 LLM 在 RAG 检索结果基础上生成 Tutor answer，而不是只用 rule-based 拼接回答。

### 比赛价值

- 对齐 A3 中“基于大模型的个性化资源生成与学习多智能体系统”方向。
- 证明当前 RAG chunk 能作为 LLM grounding context 使用。
- 同时保留无 API key 的 fallback 演示能力。

### 实现边界

允许：

- 使用现有 `LLMProvider` / OpenAI-compatible provider 边界。
- 使用现有 `LLM_ENABLE_FOR_TUTOR`、`LLM_FALLBACK_MODE` 等配置。
- 补充一份手动验证文档。
- 在 Agent trace 中记录 LLM provider 是否被使用。

禁止：

- 不把 API key 写入仓库。
- 不把 LLM SDK 调用写进 API handler。
- 不让前端直接调用 LLM。
- 不改变 `/api/v1/tutor/ask` response schema。
- 不要求本地默认 smoke 必须联网。

### 实现路径

1. 使用已有 RAG 手动样例资料导入课程。
2. 用 rule-based 模式先确认 retrieval 和 source refs 正常。
3. 启用远端 Tutor LLM：
   - `LLM_PROVIDER=openai_compatible`
   - `LLM_ENABLE_FOR_TUTOR=true`
   - `LLM_FALLBACK_MODE=rule_based`
4. 使用同一个问题再次调用 Tutor。
5. 对比 answer、source_refs 和 Agent trace。
6. 将操作步骤、输入、输出评价标准写入 `docs/` 或 `data/samples/` 下的手动验证文档。

### 推荐测试输入

```text
为什么 BFS 在无权图中第一次到达节点就代表最少边数？请和 DFS 对比。
```

```text
栈和队列最容易混淆的操作是什么？请用 BFS/DFS 的场景解释。
```

### 验收标准

| ID | 标准 |
|---|---|
| LLM-RAG-AC1 | 启用 Tutor LLM 后，Tutor answer 仍保留真实 `source_refs` |
| LLM-RAG-AC2 | Agent trace 能看出使用了 LLM provider 或 fallback |
| LLM-RAG-AC3 | LLM 不得声称资料中不存在的关键结论 |
| LLM-RAG-AC4 | LLM provider 失败时，fallback 仍可返回 rule-based answer |
| LLM-RAG-AC5 | 默认无 API key 本地演示不崩溃 |
| LLM-RAG-AC6 | 手动验证文档记录输入、配置、预期输出和评价标准 |

### Reviewer 重点

- 检查 secret 是否泄露。
- 检查 LLM 失败路径是否保留 fallback。
- 检查 trace 是否足够说明回答来源。
- 检查是否把“LLM 已验证”误写成默认本地能力。

## 3. Agent Trace 显示具体来源

### 目标

让演示页面中的 Agent trace 不只显示“使用了 chunk 和 source_ref”，而是展示具体 `document:{id}#chunk:{index}` 来源。

### 比赛价值

- 强化“多智能体过程可追踪”的展示效果。
- 让评委能看到 Tutor / Resource 的决策依据来自真实资料。
- 改善当前 trace 表述过泛的问题。

### 实现边界

允许：

- 在 Tutor / Resource 的 Agent run step 中写入前 1-3 个 `source_ref`。
- 在 `decision_basis` 或 `output_summary` 中增加简短来源摘要。
- 前端 trace 继续读取现有 step 字段展示。

禁止：

- 不新增复杂 trace schema。
- 不修改数据库表结构。
- 不改变已有 Agent run API response shape。
- 不把完整 chunk 原文大量塞进 trace。
- 不让 trace 成为第二套 retrieval 逻辑。

### 实现路径

1. 定位 Tutor / Resource 记录 Agent step 的 service。
2. 从已有 response 或 retrieved results 中提取前 1-3 个 `source_ref`。
3. 将来源写入现有 trace 文本字段，例如：

```text
Grounded sources: document:2#chunk:1, document:2#chunk:4
```

4. 前端如果已有展示能力，只调整文案；如果没有，做最小 UI 展示。
5. 保持缺少资料时 trace 能表达 fallback 或资料不足。

### 验收标准

| ID | 标准 |
|---|---|
| TRACE-AC1 | Tutor Agent step 能展示具体 `source_ref` |
| TRACE-AC2 | Resource Agent step 能展示具体 `source_ref` |
| TRACE-AC3 | 无资料或无命中时 trace 不显示伪造 source |
| TRACE-AC4 | 不新增数据库表或破坏 Agent run response schema |
| TRACE-AC5 | 前端 trace 区域不会因为 source refs 过长而布局溢出 |
| TRACE-AC6 | 相关后端测试或 API contract 测试通过 |

### Reviewer 重点

- 检查 trace 中的 source refs 是否来自真实 retrieval result。
- 检查是否有 hardcoded `document:1#chunk:0`。
- 检查 source refs 数量是否克制。
- 检查无资料 fallback 是否诚实。

## 4. RAG 检索质量小优化

### 目标

在保持 keyword retrieval 的前提下，小幅提升中文问题命中率和排序质量，为演示提供更稳定的 grounded answer。

### 比赛价值

- 减少“导入了资料但问法稍变就检索不到”的演示风险。
- 不引入 embedding / vector database 的复杂部署成本。
- 为后续 hybrid retrieval 留出边界。

### 实现边界

允许：

- 优化 query normalization。
- 增强中文 bigram / term matching。
- 对标题、`source_ref`、`concept_slug`、metadata 做轻量加权。
- 对 `top_k` 做边界保护。
- 增加命中解释 metadata，例如 `matched_terms`。

禁止：

- 不引入 Chroma / FAISS / pgvector。
- 不引入 embedding provider。
- 不改变 search API schema。
- 不在前端做 scoring。
- 不把 demo 问题硬编码到检索逻辑。

### 实现路径

1. 在 `KnowledgeBaseService` 内部收敛 scoring 改动。
2. 增加 `_query_terms()` 的中文和英文混合处理测试。
3. 增加 `_score()` 的排序测试。
4. 对 metadata 增加可选字段：
   - `matched_terms`
   - `term_match_count`
   - `retrieval_mode=keyword`
5. 用现有 RAG 手动样例验证 BFS/DFS、stack/queue 两组问题。

### 验收标准

| ID | 标准 |
|---|---|
| RETRIEVAL-AC1 | BFS/DFS 中文问题能稳定命中 BFS/DFS 资料 |
| RETRIEVAL-AC2 | stack/queue 中文问题能稳定命中栈/队列资料 |
| RETRIEVAL-AC3 | 无关问题返回空结果或低相关结果，不自动伪造答案 |
| RETRIEVAL-AC4 | search response schema 保持兼容 |
| RETRIEVAL-AC5 | metadata 可解释命中依据，但不暴露 secret |
| RETRIEVAL-AC6 | `python -m unittest tests.test_rag_retrieval -v` 通过 |

### Reviewer 重点

- 检查优化是否只在 service 层完成。
- 检查是否为了演示硬编码测试问题。
- 检查无关 query 是否被过度匹配。
- 检查排序变化是否影响 Tutor / Resource 主流程。

## 推荐执行顺序

| 顺序 | 增量 | 推荐原因 |
|---|---|---|
| 1 | 前端知识导入 UI | 最直接提升演示可操作性 |
| 2 | LLM + RAG Tutor 手动验证 | 证明 RAG 能进入真实 LLM Tutor |
| 3 | Agent Trace 显示具体来源 | 强化多智能体可解释展示 |
| 4 | RAG 检索质量小优化 | 降低现场问法变化导致的命中风险 |

## Builder 自审格式

每轮增量完成后，Builder Agent 必须在开发日志或 review 请求中给出：

```text
Self-review:
- Increment ID:
- Demo value:
- API/schema changed: Yes/No
- Database model changed: Yes/No
- Frontend business logic added: Yes/No
- Service/orchestrator boundary respected: Yes/No
- Adapter/provider boundary respected: Yes/No
- Hardcoded demo/mock risk: Yes/No
- Offline fallback preserved: Yes/No
- Tests run:
- Manual demo steps:
- Known gaps:
- Ready for review: Yes/No
```

## Reviewer 判定规则

Reviewer 只阻塞真正影响合并、演示或后续开发的问题：

- Blocking：
  - 本地无法启动。
  - 主演示链路崩溃。
  - API contract 被破坏且未同步调用方。
  - secret 泄露。
  - 真实 LLM / RAG 被强制设为默认依赖，导致无 key 无网络无法演示。

- Fix Before Merge：
  - 前端 hardcode source refs 或 demo answer。
  - API handler 承载 chunking / retrieval / LLM 调用。
  - 新增功能没有最小测试且风险直接影响演示。
  - 错误状态导致 UI 崩溃或卡死。

- Optional：
  - 文案细节。
  - 低风险 UI polish。
  - 不影响当前演示的长期架构优化。
