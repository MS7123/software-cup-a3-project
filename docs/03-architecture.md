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

该决策见 `docs/decisions/0001-architecture-baseline.md`。

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
6. 每完成一个跨模块能力，更新 `docs/06-project-state.md`。
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
11. 每完成一个跨模块能力，更新 `docs/06-project-state.md`。
12. 如果同一问题连续两次修复失败，停止继续 trial-and-error，先写 failure analysis。
