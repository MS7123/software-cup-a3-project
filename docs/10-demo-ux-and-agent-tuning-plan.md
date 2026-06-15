# Demo UX and Agent Tuning Increment Plan

最后更新：2026-06-15

面向角色：Builder Agent / Reviewer Agent

本文档定义下一轮可演示增量：优先修复 Tutor 响应体验、Markdown 渲染、LLM 输出稳定性和 RAG 演示可靠性。目标是在不重写前端、不引入新数据库强依赖、不恢复旧多 Agent 重流程的前提下，提高评委现场体验。

## 1. 背景

### 1.1 已知事实

当前项目已经完成以下演示基础：

- 主线流程已经覆盖 `profile -> learning path -> resource -> Tutor -> Quiz -> Evaluator -> Agent trace`。
- RAG 第一阶段已经支持 `text` / `markdown` 资料导入、chunking、keyword retrieval 和 `source_refs`。
- Tutor 可以基于 retrieved chunks 生成 grounded answer，并在 trace 中展示来源。
- 默认本地演示仍应保持离线可运行，不应强依赖 API key、网络、PostgreSQL、VectorStore 或 embedding provider。

### 1.2 当前演示风险

当前用户手动测试暴露出以下问题：

| 风险 | 当前表现 | 影响 |
|---|---|---|
| Tutor 响应慢 | LLM Tutor 可能约 20 秒才返回 | 评委会误以为系统卡死 |
| Markdown 未渲染 | LLM 输出 `**标题**`、列表等 Markdown 原文 | 答案显得粗糙，可读性差 |
| LLM 输出契合度不稳 | 有时未充分利用 retrieved chunks，或表达过于泛化 | 影响 A3 的个性化和 grounded QA 展示 |
| Reset 语义不清 | 清空 demo data 后上传资料可能仍保留 | 演示者和评委容易误解数据边界 |
| 前端观感较弱 | 布局、间距、层级和 trace 展示不够成熟 | 影响展示质量，但不应先于功能可靠性 |

## 2. 总体优先级

| 优先级 | Increment ID | 增量 | 是否本轮必做 | 说明 |
|---|---|---|---|---|
| P0 | `IMPL-DEMO-FREEZE-001` | 主演示链路冻结验证 | 是 | 先确认核心链路不崩 |
| P0 | `IMPL-TUTOR-UX-001` | Tutor loading / timeout / fallback | 是 | 解决“点击后像卡死”的演示风险 |
| P0 | `IMPL-MARKDOWN-RENDER-001` | Tutor / Resource Markdown 渲染 | 是 | 解决 LLM 输出不可读问题 |
| P0 | `IMPL-AGENT-TUNING-001` | Tutor prompt / output format tuning | 是 | 提高 LLM 契合度，不做 model fine-tuning |
| P0 | `IMPL-RAG-STABILITY-001` | RAG 对比问题稳定性回归 | 是 | 确保 BFS/DFS 等复合问题仍能召回双方资料 |
| P1 | `IMPL-KB-CLEANUP-001` | Reset / uploaded knowledge 语义修正 | 建议做 | 降低演示误解 |
| P1 | `IMPL-DB-OPTIN-001` | PostgreSQL opt-in 数据库加载 | 可后置 | 默认仍用 SQLite，云端数据库不阻塞演示 |
| P1 | `IMPL-FRONTEND-POLISH-001` | 前端整体视觉 polish | 最后做 | 只在功能稳定后做局部优化 |
| P2 | `IMPL-AUTH-PERSISTENCE-002` | 认证、多用户隔离、历史恢复 | 后置 | 风险高，容易影响现有 smoke |
| P2 | `IMPL-RAG-ADVANCED-001` | PDF / embedding / vector store | 后置 | 属于真实产品增强，不是当前最小演示闭环 |

## 3. 本轮推荐目标

本轮建议 Builder Agent 只执行以下 P0 组合：

```text
IMPL-TUTOR-UX-001
IMPL-MARKDOWN-RENDER-001
IMPL-AGENT-TUNING-001
IMPL-RAG-STABILITY-001 regression check
```

本轮完成后，评委现场应看到：

- 点击 `Ask tutor` 后立即出现明确 loading 状态。
- LLM 慢或失败时，系统能 timeout 并回退到 rule-based answer。
- Tutor answer 中的 Markdown 被正常渲染。
- Answer 结构稳定，能先回答问题，再展示依据和下一步建议。
- `Grounded source` 和 Agent trace 仍展示真实 `document:{id}#chunk:{index}`。

## 4. 明确非目标

本轮不做：

- 不做前端大重写。
- 不引入新的 UI framework。
- 不重构页面路由。
- 不引入 PostgreSQL 强依赖。
- 不合并 `feature/auth-and-persistence` 旧分支。
- 不引入 Chroma、FAISS、Qdrant、Milvus 或 pgvector。
- 不做 model fine-tuning。
- 不让前端直接调用 LLM。
- 不把 LLM SDK 调用写入 API handler。
- 不修改 `/api/v1/tutor/ask` request / response schema，除非现有类型已经无法表达错误状态，并且同步更新测试。

## 5. Increment 设计

### 5.1 `IMPL-TUTOR-UX-001`: Tutor Loading / Timeout / Fallback

#### 目标

让 Tutor 在 LLM 慢响应时仍然可演示，不出现“点击后无反馈”的状态。

#### 允许修改

- `src/frontend/src/App.tsx`
- `src/frontend/src/styles.css`
- `src/frontend/src/api/client.ts`
- `src/backend/app/services/tutor_service.py`
- `src/backend/app/agents/tutor_agents.py`
- 相关测试文件

#### 实现边界

允许：

- 前端增加 `isTutorLoading`、`tutorError`、`elapsed time` 或简短 loading 文案。
- 后端在 Tutor LLM 调用处增加合理 timeout。
- LLM timeout / provider error 时回退到 rule-based Tutor。
- Agent trace 中记录 `fallback` 原因。

禁止：

- 前端伪造 Tutor answer。
- 前端硬编码 demo response。
- API handler 直接实现 fallback 业务逻辑。
- 因 LLM timeout 直接让整条主演示链路失败。

#### 验收标准

| ID | 标准 |
|---|---|
| TUTOR-UX-AC1 | 点击 `Ask tutor` 后 1 秒内出现 loading 状态 |
| TUTOR-UX-AC2 | loading 状态不会遮挡或破坏已有 answer 区域 |
| TUTOR-UX-AC3 | LLM timeout 或 provider error 时返回 rule-based fallback answer |
| TUTOR-UX-AC4 | fallback answer 保留真实 `source_refs` |
| TUTOR-UX-AC5 | Agent trace 能看到 fallback 或 provider failure 的简短说明 |
| TUTOR-UX-AC6 | 无 API key / 无网络时默认演示不崩溃 |

### 5.2 `IMPL-MARKDOWN-RENDER-001`: Markdown Rendering

#### 目标

让 Tutor / Resource 中由 LLM 返回的 Markdown 以可读格式展示，而不是显示原始 Markdown 语法。

#### 允许修改

- `src/frontend/src/App.tsx`
- `src/frontend/src/styles.css`
- `src/frontend/package.json`
- `src/frontend/package-lock.json`
- 前端 smoke 测试

#### 推荐实现

优先使用轻量、成熟的 Markdown renderer，例如 `react-markdown`。如果引入依赖导致构建复杂度上升，可以先实现受限 Markdown 渲染，但必须避免使用不安全的 `dangerouslySetInnerHTML` 直接渲染未清洗 HTML。

#### 渲染范围

第一版只需要支持：

- 标题
- 加粗
- 有序列表
- 无序列表
- 行内 code
- code block
- 段落换行

#### 安全边界

禁止：

- 直接渲染任意 HTML。
- 允许 script、iframe、event handler。
- 为了渲染 Markdown 改动后端 answer schema。

#### 验收标准

| ID | 标准 |
|---|---|
| MD-AC1 | Tutor answer 中的 `**重点**` 能渲染为加粗 |
| MD-AC2 | Tutor answer 中的列表能渲染为列表 |
| MD-AC3 | `Grounded source` 不被误渲染成正文的一部分 |
| MD-AC4 | 长答案不会溢出 answer container |
| MD-AC5 | `npm run build` 通过 |
| MD-AC6 | Playwright smoke 通过或补充手动验证记录 |

### 5.3 `IMPL-AGENT-TUNING-001`: Tutor Prompt / Output Format Tuning

#### 目标

提高 LLM Tutor 输出和用户画像、retrieved chunks、问题意图之间的契合度。

#### 关键判断

这里的“微调 agent”指 prompt 和 orchestration tuning，不是 model weights fine-tuning。当前比赛阶段不建议做真正的 fine-tuning，因为成本高、验证慢、收益不稳定。

#### 允许修改

- `src/backend/app/agents/tutor_prompts.py`
- `src/backend/app/agents/tutor_agents.py`
- `src/backend/app/services/tutor_service.py`
- `tests/test_llm_provider_tutor.py`
- `tests/test_rag_retrieval.py`

#### 输出格式建议

Tutor answer 建议稳定包含三段：

```text
1. Direct answer
2. Based on your current profile
3. Grounded next step
```

中文展示时可对应为：

```text
1. 直接回答
2. 结合你的当前画像
3. 下一步练习建议
```

#### Prompt 约束

需要明确告诉 LLM：

- retrieved chunks 非空时，优先基于 chunks 回答。
- 如果 chunks 只支持部分问题，先回答被支持部分，再说明缺口。
- 不要在有相关 chunks 时声称“资料中没有相关内容”。
- 必须保留 source refs 或 inline citation。
- 回答应适配 student profile，例如基础薄弱、目标考试、练习偏好、时间预算。

#### 验收标准

| ID | 标准 |
|---|---|
| AGENT-AC1 | Tutor answer 能直接回答用户问题，不先输出泛泛寒暄 |
| AGENT-AC2 | Tutor answer 能引用 retrieved chunks 的核心概念 |
| AGENT-AC3 | Tutor answer 能结合 profile 中的 level、goal、weak points 或 time |
| AGENT-AC4 | 当 retrieved chunks 非空时，LLM 不应错误声称没有资料 |
| AGENT-AC5 | LLM 输出失败或矛盾时仍能 fallback |
| AGENT-AC6 | 新增或更新最小单元测试覆盖 prompt/fallback 关键路径 |

### 5.4 `IMPL-RAG-STABILITY-001`: RAG Regression Check

#### 目标

保证本轮 UX 和 prompt 调整不会破坏已有 RAG retrieval coverage。

#### 必测问题

```text
为什么 BFS 在无权图中第一次到达节点就代表最少边数？请和 DFS 对比。
```

```text
栈和队列最容易混淆的操作是什么？请结合 BFS 和 DFS 解释。
```

#### 验收标准

| ID | 标准 |
|---|---|
| RAG-STABLE-AC1 | BFS/DFS 对比问题仍能召回 BFS 和 DFS 相关 chunk |
| RAG-STABLE-AC2 | Tutor answer 不再因为 retrieval 缺口错误声称没有 DFS |
| RAG-STABLE-AC3 | `source_refs` 至少包含一个 DFS 或 compare chunk |
| RAG-STABLE-AC4 | Agent trace 显示多个 grounded sources |
| RAG-STABLE-AC5 | 无关 query 不被强行匹配为高置信来源 |

## 6. 后续 P1 / P2 增量

### 6.1 `IMPL-KB-CLEANUP-001`: Reset / Uploaded Knowledge 语义修正

#### 目标

解决“清空 demo data 后，之前上传资料依然存在”的演示困惑。

#### 推荐方案

优先改文案和按钮语义：

- 将 `Clear demo data` 明确为 `Reset demo scenario`。
- 增加独立的 `Clear imported knowledge`，只清理当前 course 的 imported documents/chunks。
- 清理后刷新 `Knowledge setup` 和 search result 状态。

#### 优先级判断

这是 P1，不应先于 Tutor loading、Markdown 和 agent tuning。

### 6.2 `IMPL-DB-OPTIN-001`: PostgreSQL Opt-in 数据库加载

#### 目标

让 PostgreSQL 成为可选部署增强，而不是比赛本地演示的默认门槛。

#### 边界

- 默认仍使用 SQLite。
- PostgreSQL 只通过 `APP_DATABASE_URL` opt-in。
- 依赖、env example、README、verify 脚本必须一致。
- 不在本轮强制接入认证、多用户隔离。

### 6.3 `IMPL-FRONTEND-POLISH-001`: Frontend Visual Polish

#### 目标

在功能稳定后优化视觉层级和演示观感。

#### 范围

允许：

- 调整整体 spacing、typography、section hierarchy。
- 优化 Tutor answer、Knowledge setup、Agent trace 的视觉层级。
- 美化 source refs 和 status badge。
- 改善 mobile / narrow viewport 下的可读性。

禁止：

- 重写前端架构。
- 引入复杂设计系统。
- 为了视觉 polish 改 API contract。
- 把核心业务逻辑搬到前端。

## 7. Builder 自检格式

Builder Agent 完成本轮后，在 review 请求中必须给出：

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
- LLM timeout/fallback covered: Yes/No
- Markdown rendering covered: Yes/No
- Tests run:
- Manual demo steps:
- Known gaps:
- Ready for review: Yes/No
```

## 8. Reviewer 检查清单

Reviewer 只阻塞真正影响合并、演示或后续开发的问题。

### 8.1 Blocking

- 本地无法启动。
- 主演示链路崩溃。
- Tutor 在无 API key / 无网络时无法 fallback。
- API contract 被破坏且调用方未同步。
- secret 泄露。
- 前端直接调用 LLM provider。
- API handler 承载 retrieval / prompt / fallback 核心业务逻辑。

### 8.2 Fix Before Merge

- Tutor loading 状态缺失或错误状态导致 UI 卡死。
- Markdown 渲染使用不安全 HTML 注入。
- LLM 有 chunks 时仍稳定输出“资料中没有相关内容”。
- `source_refs` 被前端或测试硬编码。
- Reset / imported knowledge 文案造成明显演示误导，且本轮声明已解决。
- 新增依赖后 `npm run build` 不通过。

### 8.3 Optional

- 低风险 UI polish。
- 长期数据库部署优化。
- PDF / embedding / vector store。
- Auth / multi-user persistence。
- 更完整的设计系统。

## 9. 最小验证要求

### 9.1 自动验证

本轮完成后至少运行：

```powershell
python -m unittest tests.test_rag_retrieval tests.test_llm_provider_tutor tests.test_backend_contracts -v
npm run build
python -m compileall -q src\backend tests
git diff --check
```

如果时间允许，运行完整闸门：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

### 9.2 手动验证

手动验证必须覆盖：

1. 导入 BFS/DFS RAG 样例资料。
2. 搜索 BFS/DFS 对比问题，确认 returned chunks 包含 DFS 或 compare chunk。
3. 点击 `Ask tutor`，确认 loading 立即出现。
4. 等待 LLM answer，确认 Markdown 正常渲染。
5. 检查 answer 是否包含直接回答、profile 适配、下一步建议。
6. 检查 `Grounded source` 和 Agent trace 是否保留真实 source refs。
7. 关闭或移除 API key 后重试，确认 fallback 可用。

## 10. 推荐交付顺序

```text
1. 增加 Tutor loading / error UI
2. 增加后端 LLM timeout / fallback trace
3. 增加 Markdown renderer
4. 调整 Tutor prompt 和输出格式
5. 补最小 backend tests
6. 补或更新 frontend smoke
7. 跑 targeted tests 和 npm build
8. 跑 verify.ps1
9. 记录 agile log 和 review log
```

## 11. 最终合并标准

本轮允许合并的最低标准：

- Tutor 慢响应时 UI 不再像卡死。
- LLM 失败时默认演示仍可完成。
- Markdown answer 可读。
- RAG source evidence 仍真实可追踪。
- 不引入数据库、认证、向量库等横切风险。
- 自动测试或明确手动验证覆盖本轮关键路径。
