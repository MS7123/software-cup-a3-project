# 架构设计

## 架构结论

采用前后端分离的中等规模工程架构：

- 前端：`React + Vite + TypeScript + Tailwind CSS`
- 后端：`FastAPI + Pydantic + SQLAlchemy`
- 业务数据库：`PostgreSQL`
- 向量库：第一阶段 `Chroma`，通过 adapter 隔离，后续可评估 `pgvector`
- 异步任务：`Redis + RQ`，如任务编排复杂再评估 `Celery`
- Agent 编排：第一阶段轻量自研 `AgentOrchestrator`，如状态图和多轮工具调用复杂度上升再评估 `LangGraph`
- LLM 接入：统一封装 OpenAI-compatible API

该决策见 `docs/architecture/0001-architecture-baseline.md`。

## 设计理由

- `React + Vite + TypeScript` 足够支撑学习路径、知识图谱、测验和 Agent 执行记录等交互，同时比重型全栈框架更容易在比赛周期内控制。
- `FastAPI + Pydantic` 适合清晰定义 API 契约、数据校验和自动文档。
- `PostgreSQL` 负责可靠保存业务实体、学习记录、任务状态和 Agent 日志。
- `Chroma` 能快速完成第一阶段向量检索；通过 adapter 隔离后，后续可切换到 `pgvector`。
- 自研轻量 `AgentOrchestrator` 能保持可控边界，避免过早引入复杂 Agent framework。
- `Redis + RQ` 足以支撑文档解析、embedding、资源生成、测验生成等长任务。

## 替代方案

| 方案 | 结论 | 原因 |
|---|---|---|
| `Next.js` 全栈 | 暂不采用 | 前后端边界容易混杂，后端 AI pipeline 与 Python 生态结合不如 `FastAPI` 直接 |
| `Streamlit` 原型 | 不作为最终主架构 | 适合验证流程，但工程化、权限、任务和演示扩展性不足 |
| `Neo4j + OpenSearch` | 第一阶段不采用 | 部署和建模成本较高，当前可用 `PostgreSQL` 表表达知识点关系 |
| `LangGraph` | 暂缓引入 | 当前 MVP 可用轻量 orchestrator；当 Agent 状态流转明显复杂后再通过 ADR 评估 |
| `pgvector` | 后续评估 | 如果希望减少部署组件，可用 `PostgreSQL + pgvector` 替换 `Chroma` |

## 模块边界

### Frontend

职责：

- 展示学生画像、课程知识点、学习路径、资源、测验、Agent 执行记录。
- 通过后端 API 发起任务和查询状态。

禁止：

- 直接访问数据库、向量库、Redis 或 LLM API。
- 在前端实现核心学习路径生成、掌握度更新和 Agent 决策逻辑。

### API Layer

职责：

- 暴露 REST API。
- 做认证预留、请求校验、响应封装、错误码转换。
- 调用 domain service，不直接写复杂业务逻辑。

### Domain Services

职责：

- `ProfileService`：学生画像和掌握度。
- `CourseService`：课程、知识点、知识点关系。
- `KnowledgeBaseService`：文档、chunk、检索。
- `LearningPathService`：学习路径生成与状态推进。
- `AssessmentService`：测验、作答、评价和掌握度更新。
- `AgentRunService`：Agent 执行记录。

禁止：

- 在 domain service 中直接调用具体 LLM SDK。
- 在 domain service 中直接依赖具体向量库 SDK。

### Agent Orchestration

职责：

- 统一调度 `Planner Agent`、`Resource Agent`、`Tutor Agent`、`Quiz Agent`、`Evaluator Agent`。
- 管理 Agent 输入输出结构、工具调用、执行状态和日志。
- 将每次运行写入 `agent_runs`。

禁止：

- Agent 直接操作数据库表；必须通过 service 或 repository。
- Agent prompt 中硬编码数据库、向量库或供应商细节。

### Infrastructure Adapters

职责：

- `LLMProvider`：封装 OpenAI-compatible API。
- `VectorStore`：封装 `Chroma`，保留 `pgvector` 替换接口。
- `TaskQueue`：封装 `Redis + RQ`。
- `DocumentParser`：封装 PDF、Word、PPT 或纯文本解析。

## 数据模型

第一阶段核心实体如下，具体字段可在实现时细化，但不得破坏模块含义。

| 实体 | 核心字段 | 说明 |
|---|---|---|
| `users` | `id`, `name`, `role`, `created_at` | 用户基础信息 |
| `student_profiles` | `id`, `user_id`, `goal`, `level`, `preferences`, `time_budget` | 学生画像 |
| `courses` | `id`, `title`, `description`, `created_at` | 课程 |
| `concepts` | `id`, `course_id`, `name`, `description`, `difficulty` | 知识点 |
| `concept_relations` | `id`, `source_concept_id`, `target_concept_id`, `relation_type` | 先修、相关、包含关系 |
| `documents` | `id`, `course_id`, `title`, `source_type`, `status` | 课程资料 |
| `document_chunks` | `id`, `document_id`, `content`, `vector_ref`, `metadata` | 检索片段 |
| `learning_paths` | `id`, `student_profile_id`, `course_id`, `status` | 学习路径 |
| `learning_path_items` | `id`, `path_id`, `concept_id`, `order_index`, `status` | 路径节点 |
| `generated_resources` | `id`, `path_item_id`, `resource_type`, `content`, `source_refs` | 生成资源 |
| `quizzes` | `id`, `concept_id`, `student_profile_id`, `status` | 测验 |
| `quiz_items` | `id`, `quiz_id`, `question`, `answer`, `explanation`, `difficulty` | 测验题 |
| `attempts` | `id`, `quiz_id`, `student_profile_id`, `answers`, `score` | 作答记录 |
| `mastery_records` | `id`, `student_profile_id`, `concept_id`, `mastery_score`, `evidence` | 掌握度 |
| `tasks` | `id`, `task_type`, `status`, `result_ref`, `error` | 异步任务 |
| `agent_runs` | `id`, `agent_type`, `status`, `input_summary`, `output_summary`, `duration_ms`, `error` | Agent 可解释记录 |

## 接口契约

API 路径使用 `/api/v1` 前缀。所有请求和响应必须有 `Pydantic` Schema。

### Student Profile

- `POST /api/v1/student-profiles`
  - 创建学生画像。
- `GET /api/v1/student-profiles/{profile_id}`
  - 查询学生画像和掌握度摘要。

### Course and Concepts

- `POST /api/v1/courses`
  - 创建课程。
- `POST /api/v1/courses/{course_id}/concepts`
  - 创建知识点。
- `POST /api/v1/concept-relations`
  - 创建知识点关系。
- `GET /api/v1/courses/{course_id}/graph`
  - 查询课程知识点图数据。

### Knowledge Base

- `POST /api/v1/courses/{course_id}/documents`
  - 创建资料记录并返回处理任务。
- `GET /api/v1/documents/{document_id}/chunks`
  - 查询资料切片。
- `POST /api/v1/knowledge/search`
  - 输入 `course_id`, `query`, `top_k`，返回 chunk 列表和来源元数据。

### Learning Path

- `POST /api/v1/learning-paths`
  - 输入 `student_profile_id`, `course_id`, `goal`，创建路径生成任务或同步返回短路径。
- `GET /api/v1/learning-paths/{path_id}`
  - 查询学习路径和节点状态。

### Resources and Tutor

- `POST /api/v1/resources/generate`
  - 输入 `path_item_id`, `resource_type`，返回异步任务。
- `POST /api/v1/tutor/ask`
  - 输入 `student_profile_id`, `course_id`, `question`，返回回答和 `source_refs`。

### Quiz and Evaluation

- `POST /api/v1/quizzes/generate`
  - 输入 `student_profile_id`, `concept_id`, `difficulty`，返回测验。
- `POST /api/v1/quizzes/{quiz_id}/attempts`
  - 提交答案，返回评分、解释和掌握度更新。

### Tasks and Agent Runs

- `GET /api/v1/tasks/{task_id}`
  - 查询异步任务状态。
- `GET /api/v1/agent-runs/{run_id}`
  - 查询 Agent 执行记录。
- `GET /api/v1/agent-runs?student_profile_id=&agent_type=`
  - 查询执行记录列表。

## 风险与约束

- 比赛周期内必须优先做完整学习闭环，避免堆功能。
- 知识图谱第一阶段只做必要关系，不追求通用图数据库能力。
- Agent 输出必须尽量 grounded in retrieved context；不能把自由生成内容伪装成课程事实。
- 长任务必须落任务状态，避免前端长时间无反馈。
- 所有外部开源项目只能按合规文档使用，核心业务逻辑必须自主实现。
- 技术栈变更、引入 `LangGraph`、切换向量库或引入图数据库都必须新增 ADR。

## 给 Implementation Agent 的实施说明

1. 先搭后端基础包结构和 API schema，不要先写前端页面。
2. 先实现 `courses`, `concepts`, `student_profiles`, `learning_paths`, `agent_runs`, `tasks` 的最小数据模型。
3. 所有 LLM 调用必须通过 `LLMProvider` adapter；业务服务中不得直接 import 具体供应商 SDK。
4. 所有向量检索必须通过 `VectorStore` adapter；不得在 API handler 中直接调用 `Chroma`。
5. 先实现一条可演示闭环：画像创建、课程和知识点、路径生成、资源生成、测验、评价、Agent 日志。
6. 每完成一个跨模块能力，更新 `docs/project/06-project-state.md`。
7. 如果连续两次修复同一问题失败，停止直接改代码，先补充 failure analysis：复现、根因假设、最小验证、最小修复。

## 数据结构 MVP 架构细化

最后更新：2026-06-03

### 架构调整结论

不需要调整已 Accepted 的架构基线，也不需要新增 ADR。

当前需求只是把 MVP 从通用 A3 收敛为“数据结构课程 + 学生端闭环 + Agent 摘要展示”，属于架构细化，不涉及技术栈替换、模块边界推翻、引入 `LangGraph`、切换向量库或引入图数据库。

实现侧需要在现有架构内细化：

- 数据结构课程 seed data。
- 3 个模拟学生画像。
- Agent run / Agent step 摘要记录。
- 学生端 MVP API schema。
- 后端 service 和 adapter 的函数契约。

### 涉及模块

| 模块 | 本轮细化职责 |
|---|---|
| `Frontend` | 学生画像选择/编辑、学习路径展示、学习资源展示、Tutor 问答、Quiz 作答、掌握度和 Agent 流程摘要展示 |
| `API Layer` | `/api/v1` REST API、请求/响应 `Pydantic` Schema、任务状态与错误响应封装 |
| `Domain Services` | `ProfileService`、`CourseService`、`KnowledgeBaseService`、`LearningPathService`、`AssessmentService`、`AgentRunService` |
| `Agent Orchestration` | 调度 `Planner Agent`、`Resource Agent`、`Tutor Agent`、`Quiz Agent`、`Evaluator Agent` |
| `Infrastructure Adapters` | `LLMProvider`、`VectorStore`、`TaskQueue`、`DocumentParser` |
| `Persistence` | `PostgreSQL` 业务数据、`Chroma` 向量索引引用、seed data 初始化脚本 |

### MVP 数据结构细化

第一阶段围绕数据结构课程 MVP 加字段，不泛化成完整教学平台。

| 实体 | MVP 字段约束 |
|---|---|
| `student_profiles` | 增加 `profile_type`，枚举值为 `weak_foundation`、`exam_sprint`、`algorithm_practice` |
| `courses` | 增加 `is_demo`，用于标记演示课程 |
| `concepts` | 增加 `slug`、`chapter`；MVP seed 必须包含复杂度分析、链表、栈/队列、二叉树遍历、BFS/DFS |
| `document_chunks` | 增加 `concept_id`、`source_ref`，便于 Tutor 回答返回引用线索 |
| `learning_paths` | 增加 `goal`、`rationale`，用于展示路径依据 |
| `learning_path_items` | 增加 `title`、`objective`、`rationale`，用于前端展示阶段化学习步骤 |
| `quizzes` | 保留 `student_profile_id`、`concept_id`、`difficulty`，确保题目绑定画像、知识点和难度 |
| `quiz_items` | 增加 `concept_tags`，便于展示题目覆盖的知识点 |
| `attempts` | 增加 `feedback`，保存评价反馈 |
| `agent_runs` | 改为一次学习流程的 run 级记录，保存 `run_type`、`final_summary`、`created_at`、`completed_at` |

为满足 AC9，必须新增或等价实现 `agent_run_steps`：

| 实体 | 核心字段 | 说明 |
|---|---|---|
| `agent_run_steps` | `id`, `agent_run_id`, `agent_type`, `step_order`, `status`, `input_summary`, `output_summary`, `decision_basis`, `duration_ms`, `error` | 记录每个 Agent 的调用顺序、摘要和关键决策依据 |

设计约束：

- `agent_runs` 表示一次完整学习流程。
- `agent_run_steps` 表示流程中的单个 Agent 调用。
- 前端展示 Agent 流程时按 `step_order` 排序。
- 不要求展示完整 prompt 或完整 LLM 输出，但摘要字段必须可独立读取。

### MVP API 契约补充

除前文通用 API 外，MVP 需要补充以下接口。

#### Demo Data

- `GET /api/v1/demo-data/status`
  - 查询数据结构 MVP seed data 是否已加载。
- `POST /api/v1/demo-data/load`
  - 加载数据结构课程、5 个知识点、3 个学生画像、模拟资料 chunk。
  - 仅用于开发和演示环境。

#### Student Profiles

- `GET /api/v1/student-profiles`
  - 返回模拟画像列表。
  - 第一阶段必须至少返回基础薄弱型、考试冲刺型、算法实践型 3 个画像。

#### Agent Runs

- `GET /api/v1/agent-runs/{run_id}`
  - 返回 run 级摘要和按 `step_order` 排序的 step 列表。
- `GET /api/v1/agent-runs?student_profile_id=&agent_type=`
  - 查询 Agent run 列表。

### 后端函数契约

Implementation Agent 应按以下 service / adapter 契约组织代码。具体文件名可按后端目录规范调整，但职责边界不得混淆。

```text
ProfileService.get_profile(profile_id) -> StudentProfile
ProfileService.list_demo_profiles() -> list[StudentProfile]

CourseService.get_concept_graph(course_id) -> ConceptGraph
CourseService.ensure_demo_course_loaded() -> DemoDataStatus

KnowledgeBaseService.search(course_id, query, top_k) -> list[KnowledgeChunk]

LearningPathService.create_path(profile_id, course_id, goal) -> LearningPath

AssessmentService.generate_quiz(profile_id, concept_id, difficulty) -> Quiz
AssessmentService.submit_attempt(quiz_id, profile_id, answers) -> EvaluationResult

AgentRunService.start_run(run_type, profile_id, course_id) -> AgentRun
AgentRunService.record_step(run_id, agent_type, input_summary, output_summary, decision_basis, status) -> AgentRunStep
AgentRunService.complete_run(run_id, final_summary) -> AgentRun

AgentOrchestrator.run_learning_flow(profile_id, course_id, goal) -> LearningFlowResult

LLMProvider.generate(messages, response_schema=None) -> LLMResult
VectorStore.search(collection, query, top_k, filters=None) -> list[VectorSearchResult]
```

### ADR 判断

本次不新增 ADR。原因：

- 没有更换技术栈。
- 没有推翻 `ADR 0001`。
- 没有引入 `LangGraph`、图数据库、新向量库或新任务框架。
- `agent_run_steps` 属于现有 `AgentRunService` 的模型细化，不是架构级决策。

后续如出现以下任一情况，必须新增 ADR：

- 从轻量 `AgentOrchestrator` 切换到 `LangGraph`。
- 从 `Chroma` 切换到 `pgvector`。
- 引入 `Neo4j` 或其他图数据库。
- 从 `RQ` 切换到 `Celery`。
- 改为 `Next.js` 全栈或其他主技术栈。

### 给 Implementation Agent 的 MVP 开发约束

1. 先实现后端基础结构、数据库模型、`Pydantic` schema 和 seed data，不要先做复杂前端页面。
2. MVP 只覆盖数据结构课程：复杂度分析、链表、栈/队列、二叉树遍历、BFS/DFS。
3. 必须提供 3 个模拟学生画像：基础薄弱型、考试冲刺型、算法实践型。
4. Agent 展示只需要摘要，但数据库必须记录 `input_summary`、`output_summary`、`decision_basis`、`step_order`、`status`。
5. 不允许把完整 prompt 或长篇 LLM 输出当作唯一可展示日志；必须生成短摘要字段。
6. 业务服务不得直接调用具体 LLM SDK，必须经过 `LLMProvider`。
7. API handler 不得直接调用 `Chroma`、Redis/RQ 或数据库细节，应进入 service / adapter。
8. 第一阶段知识图谱用 `PostgreSQL` 表表达，不引入 `Neo4j`。
9. 第一阶段可以使用模拟资料和 seed data，但 seed data 必须通过脚本或明确 API 加载，不要散落硬编码在业务逻辑里。
10. 每个核心 API 都必须有明确 request/response schema；返回错误时使用统一错误结构。
11. 每完成一个跨模块能力，更新 `docs/project/06-project-state.md`。
12. 如果同一问题连续两次修复失败，停止继续 trial-and-error，先写 failure analysis。

## 真实 LLM 最小接入方案

最后更新：2026-06-04

### 推荐方案摘要

真实 LLM 接入应作为现有 `LLMProvider` adapter 边界的实现细化，不调整已 Accepted 的架构基线，不新增 ADR，不引入新技术栈。

第一批推荐接入 `Tutor Agent`，原因：

- `Tutor` 已天然面向自然语言问答，真实 LLM 的演示收益最高。
- 当前 `TutorService` 已经通过 `KnowledgeBaseService.search()` 获取 demo chunk 和 `source_refs`，可以先做 grounded answer，不必同时实现真实 RAG / VectorStore。
- `Tutor` 输出结构较简单：`answer`、`source_refs`、`agent_run_id`，保持 `/api/v1/tutor/ask` schema 稳定的成本最低。
- `Tutor` 失败时可自然回退到现有 rule-based answer，不影响学习路径、Quiz 存储和 mastery update。

第一批暂不建议接入：

| 模块 | 暂缓原因 |
|---|---|
| `Resource Agent` | 生成内容较长，token 成本和质量波动更高；可在 `Tutor` 稳定后第二批接入 |
| `Quiz Agent` | 题目、答案、解析必须结构化且可评分，LLM 输出格式漂移会直接影响后续 `Evaluator` |
| `Evaluator Agent` | 评分稳定性和可解释性要求更高，真实 LLM 评分可能带来非确定性和验收波动 |
| `Planner Agent` | 当前路径依赖知识点顺序和先修关系，先应处理 `REFACTOR-001` 中 concept relation 顺序问题，不宜先交给 LLM |

### 架构判断

真实 LLM 接入触及以下模块：

- `Infrastructure Adapters`：新增 OpenAI-compatible `LLMProvider` 实现和 provider factory。
- `Agent / strategy`：新增 `LLMTutorAgent` 或等价 strategy，保留 `RuleBasedTutorAgent` fallback。
- `Domain Services`：`TutorService` 通过抽象 agent / provider 调用，不直接依赖具体 SDK。
- `Configuration`：新增 LLM provider 运行配置、timeout、retry、fallback 开关。
- `Review & Test`：增加 mock provider contract test、fallback test、API schema stability test。

本轮不触及：

- `/api/v1` request / response schema。
- 真实 `VectorStore` / `Chroma` 接入。
- 真实文档上传、embedding、chunk indexing。
- `LangGraph` 或其他 Agent framework。
- 前端 LLM 配置页面。

### 最小接入方案

#### LLM Provider 所在层

真实 LLM provider 必须位于 `Infrastructure Adapters` 层，例如 `app/adapters/llm_provider.py` 或同类路径。它实现现有 `LLMProvider` protocol：

```text
LLMProvider.generate(messages, response_schema=None) -> LLMResult
```

业务 service、API handler 和 frontend 不得直接 import OpenAI-compatible SDK 或直接读取 API key。

#### 是否沿用现有边界

必须沿用现有 `LLMProvider` / adapter 边界。当前 `LLMProvider` protocol 已足够支撑最小接入，不需要新增 ADR。

最小实现只允许扩展 provider 实现和配置读取，不允许破坏：

- `LLMResult(content, metadata)`
- `TutorAskResponse(answer, source_refs, agent_run_id)`
- `agent_runs` / `agent_run_steps`
- `/api/v1/tutor/ask`

#### Service / Orchestrator / Provider 职责

| 层 | 职责 | 禁止事项 |
|---|---|---|
| API handler | 接收请求、调用 `TutorService`、转换错误 | 不拼 prompt，不读 API key，不调用 SDK |
| `TutorService` | 查询 profile / course，调用 `KnowledgeBaseService.search()`，调用 Tutor agent / strategy，记录 run | 不直接依赖具体 LLM SDK |
| Tutor agent / strategy | 维护 prompt input 组装、调用 `LLMProvider`、解析 `LLMResult`，产出 `TutorAgentResult` 形状 | 不访问数据库，不改变 API schema |
| `LLMProvider` adapter | 封装 OpenAI-compatible HTTP / SDK 调用、timeout、基础错误映射、metadata | 不包含课程业务规则 |
| `AgentRunService` | 统一记录 input summary、output summary、decision basis、status、error | 不记录完整 API key、完整 provider response 或敏感 prompt |

`AgentOrchestrator` 暂不需要改成统一 LLM orchestration。`Tutor` 的第一批真实 LLM 接入可以在 `TutorService` 内通过 strategy/factory 选择 `LLMTutorAgent` 或 `RuleBasedTutorAgent`。

#### Prompt 维护位置

Prompt 不应放在 API handler 或 frontend。第一阶段建议：

- 放在 `app/agents/prompts/` 或 `app/agents/tutor_prompts.py`。
- prompt 模板只接收结构化输入：student profile summary、question、top chunks、source refs、course/concept hints。
- prompt 模板必须要求回答 grounded in provided chunks；没有资料时说明不足，而不是编造课程事实。
- prompt 模板不得包含 API key、数据库连接、provider 名称等基础设施细节。

#### 失败回退策略

失败回退策略应分两层：

- Provider 层：处理 timeout、HTTP error、rate limit、invalid response，返回明确异常或 error metadata。
- Agent / strategy 层：捕获 provider 失败，按配置决定是否 fallback 到 `RuleBasedTutorAgent`。

`TutorService` 应能把 fallback 情况写入 `agent_run_steps.decision_basis` 或 `output_summary`，例如“LLM provider failed; fallback to rule-based tutor”。前端仍只消费原有 `TutorAskResponse`。

#### Timeout / Retry / Fallback / Mock 切换边界

| 能力 | 所在边界 | 最小策略 |
|---|---|---|
| timeout | `LLMProvider` adapter | 单次请求 timeout，默认 15-30 秒 |
| retry | `LLMProvider` adapter | 最多 0-1 次轻量 retry，避免演示卡死 |
| fallback | Agent / strategy | LLM 失败或未配置时回退 rule-based |
| mock / real 切换 | provider factory / configuration | 通过环境变量选择，不在 service 中散落 `if demo_mode` |
| response validation | Agent / strategy | 空回答、明显无效回答回退 rule-based 或返回可解释错误 |

#### API schema 稳定

第一批真实 LLM 接入不得新增或改变 `/api/v1/tutor/ask` 的 request / response 字段。真实 LLM 的附加信息只能进入：

- `agent_runs`
- `agent_run_steps`
- `LLMResult.metadata`
- 后端日志或测试断言

如未来需要在前端展示 provider 信息，应先新增可选字段并单独评估兼容性，不得破坏已有 smoke test。

#### Implementation Boundary Standard

真实 LLM 接入必须继续满足：

- AC17：真实 provider 与 mock provider 使用同一 adapter contract。
- AC18：LLM tutor logic 位于 Agent / strategy / service 边界，不进入 handler 或 frontend。
- AC19：替换 provider 不破坏 API schema、service contract、adapter contract 和 run/step 结构。
- AC20：Review 必须包含 `Implementation Boundary Review`。

### 配置方案

最小新增环境变量建议：

| 环境变量 | 用途 | dev/demo 默认 | future production |
|---|---|---|---|
| `LLM_PROVIDER` | provider 类型：`rule_based` / `openai_compatible` | `rule_based` | `openai_compatible` |
| `LLM_BASE_URL` | OpenAI-compatible endpoint base URL | 空 | 由部署环境注入 |
| `LLM_API_KEY` | provider API key | 空，不写入仓库 | secret manager / CI secret / server env |
| `LLM_MODEL` | 模型名称 | 空或 demo model placeholder | 按部署选择 |
| `LLM_TIMEOUT_SECONDS` | 单次调用超时 | `20` | 按 SLA 调整 |
| `LLM_MAX_RETRIES` | 轻量 retry 次数 | `0` 或 `1` | 按 provider 稳定性调整 |
| `LLM_FALLBACK_MODE` | fallback 策略：`rule_based` / `error` | `rule_based` | 生产可按需求选择 |
| `LLM_ENABLE_FOR_TUTOR` | 是否启用 Tutor LLM | `false` | `true` |

Secrets 处理要求：

- `LLM_API_KEY` 不得写入 `deployment/local.env.example` 的真实值。
- 不得提交 `.env`、shell history、日志中的 key。
- Review 时检查 `git diff` 中是否出现疑似 key。
- 本地演示可在 PowerShell 环境变量中临时设置。

当前必须保留 rule-based fallback。原因：

- 保证无 key、无网络、provider rate limit 时本地 demo 仍可运行。
- 保持 `scripts/run-local.ps1 -SmokeOnly` 和现有 Playwright smoke 稳定。
- 降低真实 LLM 输出漂移对已通过 MVP 的影响。

### 风险与边界

#### 最可能破坏稳定性的点

- LLM 调用 timeout 导致 `/api/v1/tutor/ask` 响应变慢或失败。
- LLM 输出不 grounded，编造课程事实，削弱 A3 可信度。
- Provider 配置缺失导致本地 demo 不能运行。
- Service 直接依赖具体 SDK，破坏 adapter boundary。
- Prompt 或 provider response 被完整写入 `agent_run_steps`，造成日志过长或泄露敏感信息。
- 真实 LLM 输出格式不稳定，影响前端展示和测试。

#### 架构风险

- 绕过 `LLMProvider`，让 service / handler 直接调用具体 SDK。
- 把 prompt 模板放入 frontend 或 API handler。
- 为真实 LLM 修改 `/api/v1` schema，破坏现有前端和 smoke。
- 把真实 LLM 与真实 RAG / VectorStore 一次性捆绑，任务过大。
- 移除 rule-based fallback，导致无网络演示不可用。

#### 实现细节

- 选择 HTTP client 或 SDK 的具体方式。
- timeout 默认值和 retry 次数。
- prompt 文案迭代。
- provider error class 命名。
- metadata 字段中记录哪些非敏感诊断信息。

#### 现在不该做

- 不做真实 RAG / embedding / Chroma indexing。
- 不做多 provider UI 配置页。
- 不做 streaming response。
- 不做 LangGraph 迁移。
- 不让 LLM 接管 Planner / Quiz / Evaluator。
- 不把生产级 secret manager、rate-limit dashboard、cost accounting 纳入第一批任务。

### 任务拆分建议

以下仅为 Architect Agent 建议，不直接修改 `tasks/current.md` 或 `tasks/backlog.md` 状态。

#### PLAN-007: 真实 LLM 接入配置与测试计划

- 任务目标：明确 LLM provider 配置、secret 处理、本地 fallback 验证、mock/real provider contract test 计划。
- 前置依赖：`PLAN-002` 测试计划完成或同步更新。
- 影响模块：`deployment/local.env.example`、`deployment/README.md`、`scripts/verify.ps1` 测试计划说明、Review 模板。
- 验收重点：
  - 配置项覆盖 `LLM_PROVIDER`、`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`、timeout、retry、fallback。
  - 明确无 key 时仍使用 rule-based fallback。
  - 明确 secrets 不入仓库。
  - 明确真实 LLM 测试不应阻塞默认 CI / smoke。
- 是否建议进入当前阶段：建议先进入 Backlog，不打断当前 `PLAN-002`。

#### IMPL-010: 接入 OpenAI-compatible `LLMProvider` 并用于 `Tutor Agent`

- 任务目标：实现最小真实 LLM provider，通过配置选择 `rule_based` 或 `openai_compatible`，第一批只接入 `Tutor Agent`。
- 前置依赖：`PLAN-007` 或等价配置方案已确认；`PLAN-002` 不必完全阻塞，但测试边界需明确。
- 影响模块：
  - `app/adapters/`
  - `app/agents/`
  - `app/services/tutor_service.py`
  - `deployment/local.env.example`
  - backend tests
- 验收重点：
  - `/api/v1/tutor/ask` request / response schema 不变。
  - 无 LLM 配置时继续走 rule-based fallback，现有 smoke 仍通过。
  - 有 mock OpenAI-compatible provider 测试，验证 `LLMProvider.generate()` contract。
  - provider 失败时 fallback 并记录到 `agent_run_steps`。
  - service / API handler 不直接 import 具体 provider SDK。
  - `Implementation Boundary Review` 为 Pass。
- 是否建议进入当前阶段：建议在 `PLAN-002` 之后作为下一项 IMPL 候选；不建议直接抢占当前 Current。

#### REFACTOR-004: 抽离 Tutor agent strategy / factory

- 任务目标：在不改变 API 的前提下，把 `RuleBasedTutorAgent` 与未来 `LLMTutorAgent` 统一到 strategy / factory 边界。
- 前置依赖：可作为 `IMPL-010` 的前置子任务，也可并入 `IMPL-010`，但不得扩大到 Resource / Quiz / Evaluator。
- 影响模块：`app/agents/`、`TutorService`、backend boundary tests。
- 验收重点：
  - `TutorService` 不直接实例化具体 rule-based / LLM agent。
  - 通过配置或 dependency factory 选择 agent。
  - 现有 tutor API 和 tests 不变。
- 是否建议进入当前阶段：如果当前 `TutorService` 直接实例化 rule-based agent 会阻碍 provider 切换，则建议作为 `IMPL-010` 的第一步；否则不单独开大任务。

### 是否建议立即进入 Current

不建议立即改变当前 Current。当前 `tasks/current.md` 是 `PLAN-002: 编写测试计划`，应先完成测试计划，避免真实 LLM 接入缺少稳定验证边界。

建议顺序：

1. 完成 `PLAN-002`。
2. State Manager 将 `PLAN-007` 放入 Backlog 或 Current，用于冻结配置和测试边界。
3. 再推进 `IMPL-010`，只接入 `Tutor Agent`。
4. `Resource Agent` 作为第二批候选；`Quiz`、`Evaluator` 暂缓。
