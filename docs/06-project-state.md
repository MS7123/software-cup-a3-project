# 项目状态

最后更新：2026-06-04  
维护角色：State Manager Agent / Task Manager

## 1. 当前项目状态摘要

当前仓库处于后端 MVP 基础能力、前端学生端关键交互、基础自动化验证和本地部署配置逐步落地阶段。`IMPL-001` 到 `IMPL-009` 均已由 Review & Test Agent 明确复核通过；通过范围均限定在对应阶段任务内，不代表完整 MVP 产品功能 Done。

用户已确认 MVP 边界：

- 继续做 A3。
- MVP 演示课程为数据结构。
- MVP 知识点范围为复杂度分析、链表、栈/队列、二叉树遍历、BFS/DFS。
- 第一阶段只做学生端闭环。
- 学生画像和课程资料使用模拟数据。
- 第一阶段学生画像样例控制在 3 个：基础薄弱型、考试冲刺型、算法实践型。
- 比赛展示优先突出 `Multi-Agent` 协作流程。
- `Multi-Agent` 流程展示摘要即可。

已确认完成：

- A3 开源项目技术调研与技术路线建议已整理到 `docs/research/a3-open-source-research.md`。
- 第三方开源项目使用边界已整理到 `docs/compliance/open-source-compliance.md`。
- A6 赛题讨论总结已整理到 `docs/research/a6-project-discussion-summary.md`，作为赛题比较材料。
- 项目简介已整理到 `docs/00-project-brief.md`，当前明确定位为 A3。
- 架构设计已整理到 `docs/03-architecture.md`。
- 架构基线 ADR 已在 `docs/decisions/0001-architecture-baseline.md` 中标记为 `Accepted`。
- Task Manager 已建立正式任务流转规则：`Backlog -> Current -> Review -> Done`、`Backlog -> Current -> Blocked`、`Blocked -> Backlog / Current`。
- Architect Agent 已补充长期生效的 MVP implementation boundary standard，用于约束 demo data、mock provider 和 rule-based logic；该标准不修改 ADR 0001，不新增 ADR，不引入新技术栈。
- 从当前阶段开始，`Implementation Boundary Check` 成为所有 `IMPL-*` Review 的常规检查项。
- 建议对 `IMPL-002` 到 `IMPL-004` 做一次轻量 targeted review，补查 demo data、mock provider、rule-based logic、API handler、service / adapter / orchestrator 边界。
- 该检查不是大规模重构门槛，只用于发现明显 hardcoded demo、边界绕过或 API contract 风险。
- `IMPL-001` 已通过 Review，范围限定为后端基础结构、数据模型和 API schema 骨架。
- `IMPL-002` 已通过 Review，范围限定为 demo data 加载能力。
- `IMPL-003` 已通过 Review，范围限定为学生画像与课程知识点 API。
- `IMPL-004` 已通过 Review，范围限定为学习路径与 `Planner Agent` 最小流程。
- Targeted Boundary Review 已对 `IMPL-002` 到 `IMPL-004` 做轻量补审，结论为 Pass。
- `IMPL-005` 已通过 Review，范围限定为资源生成、Tutor 问答、Quiz 和 Evaluator 最小闭环。
- `IMPL-006` 已通过 Review，范围限定为前端学生端工程初始化和基础页面骨架。
- `IMPL-007` 已通过 Review，范围限定为学生端 MVP 页面关键交互。
- `IMPL-008` 已通过 Review，范围限定为自动化测试与基础验证脚本。
- `IMPL-009` 已通过 Review，范围限定为本地部署与演示运行配置。

已新增实现：

- 后端 Python package 基础结构：`src/backend/app/`。
- FastAPI 应用入口。
- `/api/v1/demo-data/status`、`/api/v1/demo-data/load`。
- `GET /api/v1/student-profiles`、`POST /api/v1/student-profiles`、`GET /api/v1/student-profiles/{profile_id}`。
- `GET /api/v1/courses/{course_id}/graph`。
- `POST /api/v1/learning-paths`、`GET /api/v1/learning-paths/{path_id}`。
- `GET /api/v1/agent-runs/{run_id}`。
- `Pydantic` request / response schema。
- SQLAlchemy ORM model：`users`、`student_profiles`、`courses`、`concepts`、`concept_relations`、`documents`、`document_chunks`、`learning_paths`、`learning_path_items`、`generated_resources`、`quizzes`、`quiz_items`、`attempts`、`mastery_records`、`tasks`、`agent_runs`、`agent_run_steps`。
- service / adapter 边界骨架：`ProfileService`、`CourseService`、`KnowledgeBaseService`、`LearningPathService`、`AssessmentService`、`AgentRunService`、`LLMProvider`、`VectorStore`、`TaskQueue`、`DocumentParser`。
- domain exception 边界：service 层使用 `NotFoundError`，API layer 负责转换 HTTP 404。
- 学习路径生成：`LearningPathService.create_path()` 根据学生画像、课程知识点和目标生成阶段化路径。
- `Planner Agent` 最小流程：`AgentOrchestrator.run_learning_flow()` 调用 service 生成路径，并通过 `AgentRunService` 写入 `agent_runs` / `agent_run_steps` 摘要。
- demo data 加载实现：`src/backend/app/db/session.py`、`src/backend/app/seed/demo_data.py`、`src/backend/app/services/demo_data_service.py`。
- 测试：`tests/test_backend_contracts.py`、`tests/test_demo_data.py`、`tests/test_profile_course_api.py`、`tests/test_learning_path_api.py`。
- Resource / Tutor / Quiz / Evaluator 最小闭环：`src/backend/app/services/resource_service.py`、`src/backend/app/services/tutor_service.py`、`src/backend/app/services/assessment_service.py`、`src/backend/app/agents/rule_based_agents.py`。
- 新增 API：`POST /api/v1/resources/generate`、`POST /api/v1/tutor/ask`、`POST /api/v1/quizzes/generate`、`POST /api/v1/quizzes/{quiz_id}/attempts`。
- 新增测试：`tests/test_learning_loop_api.py`。
- 前端工程初始化：`src/frontend/package.json`、`src/frontend/vite.config.ts`、`src/frontend/src/api/client.ts`、`src/frontend/src/api/types.ts`、`src/frontend/src/App.tsx`。
- 学生端 MVP 页面关键交互：`src/frontend/src/App.tsx`、`src/frontend/src/styles.css`，已覆盖画像选择、学习路径查看、节点切换、资源查看、Tutor 问答、Quiz 提交、评价反馈和 Agent run 摘要展示。
- 自动化验证脚本：`scripts/verify.ps1`、`scripts/frontend-smoke.ps1`、`src/frontend/playwright.config.ts`、`src/frontend/tests/student-loop.spec.ts`。
- 本地部署与演示配置：`deployment/README.md`、`deployment/local.env.example`、`scripts/run-local.ps1`。

尚未实现：

- RAG / 知识库真实检索。
- 部署和演示脚本。

Review & Test Agent 验证结论：

- `IMPL-001`：通过。`python -m compileall -q src/backend tests` 通过；`python -m unittest discover -s tests -v` 通过，4 个测试通过；`python -m pip wheel . -w .build-review` 构建成功。
- `IMPL-002`：初次 Review 不通过，后复测通过。复测时 `python -m compileall -q src/backend tests` 通过；`python -m unittest discover -s tests -v` 通过，8 个测试全部通过。
- `IMPL-003`：初次 Review 不通过，原因是 service 层直接依赖 FastAPI / `HTTPException`，后复测通过。复测时 `python -m compileall -q src/backend tests` 通过；`python -m unittest discover -s tests -v` 通过，12 个测试全部通过；service 层未再直接 import `fastapi` 或 `HTTPException`。
- Implementation Agent 已完成 `IMPL-004` 实现侧验证：`python -m compileall -q src/backend tests` 通过；`python -m unittest discover -s tests -v` 通过，14 个测试全部通过；`python -m pip check` 通过；`python -m pip wheel . -w .build` 构建成功。
- `IMPL-004` 已由 Review & Test Agent 验收通过：`python -m compileall -q src/backend tests` 通过；`python -m unittest discover -s tests -v` 通过，14 个测试全部通过。
- `IMPL-004` 结论：通过，但仅限“学习路径与 Planner Agent 最小流程”；完整 AC4、AC9 和完整 MVP 产品功能仍未 Done。
- Targeted Boundary Review 结论：`IMPL-002` 到 `IMPL-004` 边界补审 Pass；允许进入 `IMPL-005`。
- `IMPL-005` 已由 Review & Test Agent 验收通过：`python -m compileall -q src/backend tests` 通过；`python -m unittest discover -s tests -v` 通过，16 个测试全部通过。
- `IMPL-005` 结论：通过，但仅限“资源生成、Tutor 问答、Quiz 和 Evaluator 最小闭环”；完整前端学习闭环、真实 RAG / LLM / VectorStore 和完整 MVP 产品功能仍未 Done。
- `IMPL-006` 已由 Review & Test Agent 验收通过：`npm ci` 通过；`npm run build` 通过；`python -m compileall -q src/backend tests` 通过；`python -m unittest discover -s tests -v` 通过，16 个测试全部通过。
- `IMPL-006` 结论：通过，但仅限“前端学生端工程初始化和基础页面骨架”；完整学生端 MVP 页面、浏览器联调、E2E 自动化和完整 MVP 产品功能仍未 Done。
- `IMPL-007` 已由 Review & Test Agent 验收通过：`npm ci` 通过；`npm run build` 通过；`python -m compileall -q src/backend tests` 通过；`python -m unittest discover -s tests -v` 通过，16 个测试全部通过；Playwright browser smoke 通过。
- `IMPL-007` 结论：通过，但仅限“学生端 MVP 页面关键交互”；正式 E2E 测试套件、部署配置、真实 RAG / LLM / VectorStore 和完整 MVP 产品功能仍未 Done。
- `IMPL-008` 已由 Review & Test Agent 复测通过：`./scripts/verify.ps1` 通过，覆盖 Python compile、backend unit tests、`pip check`、backend wheel build、frontend build 和 Playwright browser smoke。
- `IMPL-008` 结论：通过，但仅限“自动化测试与基础验证脚本”；部署配置、真实 RAG / LLM / VectorStore、完整生产级测试矩阵和完整 MVP 产品功能仍未 Done。
- `IMPL-009` 已由 Review & Test Agent 验收通过：`./scripts/verify.ps1` 通过；`./scripts/run-local.ps1 -SmokeOnly` 通过，并验证本地 backend/frontend 启动、demo data load 和运行配置。
- `IMPL-009` 结论：通过，但仅限“本地部署与演示运行配置”；生产级部署、数据库迁移、Redis/RQ、真实 LLMProvider、真实 VectorStore 和完整 MVP 产品功能仍未 Done。
- State Manager Agent / Task Manager 未执行测试，只引用 Review & Test Agent 已记录的测试和验收结果。

## 2. 需求覆盖矩阵

| 编号 | 需求 | 状态 | 证据 | 说明 |
|---|---|---|---|---|
| R1 | 课程资料上传、解析、切分和知识库构建 | Partial | `src/backend/app/seed/demo_data.py`, `src/backend/app/services/demo_data_service.py`, Review & Test Agent IMPL-002 结论 | 已有模拟资料 chunk、source_ref 和 demo 加载；尚未实现真实上传、文件解析和解析失败提示 |
| R2 | 学生画像 | Partial | `src/backend/app/services/profile_service.py`, `src/backend/app/api/v1/router.py`, Review & Test Agent IMPL-003 结论 | 已有学生画像列表、详情、创建 API，并能返回 3 个 seed 画像；前端选择/编辑体验仍未完成 |
| R3 | 课程知识点和先修关系建模 | Partial | `src/backend/app/services/course_service.py`, `src/backend/app/api/v1/router.py`, Review & Test Agent IMPL-003 结论 | 已有课程知识点图查询 API，可返回数据结构课程、5 个 MVP 知识点和知识点关系；完整课程知识点维护能力仍未完成 |
| R4 | 学习路径规划 Agent | Partial | `src/backend/app/services/learning_path_service.py`, `src/backend/app/agents/orchestrator.py`, Review & Test Agent IMPL-004 结论 | 已有同步学习路径创建 API 和 Planner 最小流程；完整多 Agent 学习流程仍待后续任务扩展 |
| R5 | 学习资源生成 Agent | Partial | `src/backend/app/services/resource_service.py`, `src/backend/app/agents/rule_based_agents.py`, Review & Test Agent IMPL-005 结论 | 已实现面向 `path_item_id` 的最小资源生成闭环；真实 LLM / richer content generation 仍未完成 |
| R6 | RAG Tutor Agent | Partial | `src/backend/app/services/tutor_service.py`, `src/backend/app/services/knowledge_base_service.py`, Review & Test Agent IMPL-005 结论 | 已实现基于 demo chunk 检索的 grounded tutor answer；真实 VectorStore / RAG pipeline 仍未完成 |
| R7 | Quiz Agent | Partial | `src/backend/app/services/assessment_service.py`, Review & Test Agent IMPL-005 结论 | 已实现最小测验生成；更完整题型、策略和前端交互仍未完成 |
| R8 | Evaluator Agent 和掌握度更新 | Partial | `src/backend/app/services/assessment_service.py`, Review & Test Agent IMPL-005 结论 | 已实现最小评分、反馈和 mastery update 建议；真实 evaluator 策略与持续追踪仍未完成 |
| R9 | Agent 执行日志和可解释性 | Partial | `src/backend/app/services/agent_run_service.py`, Review & Test Agent IMPL-004 / IMPL-005 结论 | Planner、Resource、Tutor、Quiz、Evaluator 均有最小 `agent_runs` / `agent_run_steps` 记录；统一 learning-flow 聚合展示仍待增强 |
| R10 | 前端核心界面 | Partial | `src/frontend/src/App.tsx`, `src/frontend/src/styles.css`, `src/frontend/tests/student-loop.spec.ts`, Review & Test Agent IMPL-006 / IMPL-007 / IMPL-008 结论 | 已有可 build 的前端学生端工程、关键交互和 Playwright smoke；更完整失败路径覆盖和生产级测试矩阵仍未完成 |
| R11 | 后端 API、数据库、任务队列、LLM 封装 | Partial | `src/backend/app/`, `pyproject.toml`, `deployment/README.md`, `deployment/local.env.example`, `scripts/run-local.ps1`, Review & Test Agent IMPL-001 / IMPL-002 / IMPL-003 / IMPL-009 结论 | 已有 FastAPI、schema、model、demo persistence、部分 API、package 配置和本地演示部署说明；尚未实现数据库迁移、正式 PostgreSQL 配置、队列和可替换 LLM 配置 |
| R12 | 开源合规边界 | Partial | `docs/compliance/open-source-compliance.md`, `pyproject.toml` | 已有原则文档和基础依赖声明，但依赖 license 清单仍需补全 |
| R13 | 架构基线与模块边界 | Partial | `docs/03-architecture.md`, `docs/decisions/0001-architecture-baseline.md`, Review & Test Agent IMPL-003 结论 | service / API 分层边界已修正；外部能力仍为 protocol / adapter 骨架；完整业务闭环未完成 |

## 3. 已完成任务

- 完成 A3 开源项目技术调研。
- 完成 A3 初步技术路线建议。
- 完成第三方开源项目使用边界说明。
- 完成 A6 赛题讨论总结，供赛题选择时参考。
- 完成项目简介。
- 完成架构设计。
- 完成架构基线 ADR。
- 建立项目状态与任务跟踪文件。
- `IMPL-001`：初始化后端基础结构、数据模型、API schema 和 service / adapter 边界骨架。Review & Test Agent 已明确通过，范围仅限骨架。
- `IMPL-002`：实现 demo data 加载能力。Review & Test Agent 复测通过，范围仅限 demo data 加载能力。
- `IMPL-003`：实现学生画像与课程知识点 API。Review & Test Agent 复测通过，范围仅限学生画像与课程知识点 API。
- `IMPL-004`：实现学习路径与 `Planner Agent` 最小流程。Review & Test Agent 验收通过，范围仅限学习路径与 Planner Agent 最小流程。
- `IMPL-005`：实现资源生成、Tutor 问答、Quiz 和 Evaluator 最小闭环。Review & Test Agent 验收通过，范围仅限后端最小闭环。
- `IMPL-006`：初始化前端学生端工程。Review & Test Agent 验收通过，范围仅限前端工程初始化和基础页面骨架。
- `IMPL-007`：实现学生端 MVP 页面。Review & Test Agent 验收通过，范围仅限学生端 MVP 页面关键交互。
- `IMPL-008`：添加自动化测试与基础验证脚本。Review & Test Agent 复测通过，范围仅限自动化验证入口与 browser smoke。
- `IMPL-009`：添加部署配置。Review & Test Agent 验收通过，范围仅限本地部署与演示运行配置。

## 4. 未完成任务

- 细化测试计划。
- 实现 RAG / 知识库真实检索。
- 补失败路径和多环境覆盖的自动化测试。
- 增加生产级部署配置和演示脚本。

## 5. 已知问题

| 编号 | 问题 | 影响 | 状态 |
|---|---|---|---|
| I1 | A6 讨论材料仍存在，但项目简介、ADR 和用户确认均明确当前仓库按 A3 推进 | 新 Agent 可能误读 A6 材料为当前方向 | Mitigated |
| I2 | `docs/02-acceptance-criteria.md` 的“当前不可验收项”描述曾过期 | 新 Agent 可能误以为仓库仍无实现代码、依赖配置和测试文件 | Mitigated：`PLAN-004` 已更新为 2026-06-04 的当前事实 |
| I3 | 仓库此前缺少 `.gitignore` | 测试运行可能生成 `__pycache__` / `.pyc` 并被误提交 | Mitigated：`PLAN-005` 已补充 Python、frontend、build 和 demo database ignore 规则 |
| I4 | 默认 SQLite demo database 需明确为开发/演示用途 | ADR 业务数据库方向为 PostgreSQL，后续需要正式配置路径 | Mitigated：`PLAN-006` 已在部署文档和示例环境变量中明确 SQLite 仅用于 demo / local，正式路径通过 `APP_DATABASE_URL` 切换到 PostgreSQL |
| I5 | `ProfileService.list_demo_profiles()` 当前返回所有 `StudentProfile` | 若默认数据库中已有用户创建画像，列表可能不再只包含 3 个 demo profiles | Backlog |
| I6 | `IMPL-001` 到 `IMPL-004` 均只完成阶段范围 | 不得将完整 MVP、完整 AC1/AC2/AC3/AC4/AC9 标记为 Done | Tracked |
| I7 | Demo data、mock provider 和 rule-based logic 此前没有进入常规 Review 检查项 | 后续 Resource / Tutor / Quiz / Evaluator 容易退化为 hardcoded demo，影响真实 LLM / RAG / VectorStore 替换 | Mitigated：已写入 `docs/02-acceptance-criteria.md` 和 `tasks/README.md` |
| I8 | `IMPL-002` 到 `IMPL-004` 完成或开发时尚未应用 implementation boundary standard | 早期阶段可能存在 demo/mock/rule-based 边界遗漏 | Mitigated：Targeted Boundary Review 已补审，结论为 Pass |
| I9 | Planner 当前按 `Concept.id` 顺序生成路径，未显式使用 `concept_relations` 计算先修顺序 | 后续真实课程数据顺序变化时，学习路径顺序可能偏离先修关系 | Backlog |
| I10 | `AgentOrchestrator.run_learning_flow()` 先创建学习路径再创建 `agent_run` | 若 run 记录失败，可能出现有路径但无 run 的不一致状态 | Backlog |
| I11 | Resource / Tutor / Quiz / Evaluator 当前分别创建独立 `agent_run` | 若后续要展示统一学习闭环调用顺序，当前 run 结构还不够集中 | Backlog |
| I12 | 当前自动化测试仍缺少失败路径和多浏览器/移动视口覆盖 | 正向 smoke 已通过，但真实异常场景和跨环境稳定性仍可能滞后暴露 | Backlog |
| I13 | Windows 环境下 Playwright 默认依赖 `msedge` channel | 其他机器若未安装 Edge，需要设置 `PLAYWRIGHT_CHANNEL` 或先安装 Chromium | Backlog |

## 6. 下一步建议

1. 优先推进测试与基础设施后续项：`PLAN-002` 细化测试计划，`TEST-002` 补失败路径和多环境自动化覆盖，`CONFIG-001` 明确 Playwright 跨机器策略。
2. 后续涉及前后端闭环的实现任务仍必须先进入 Review，不得直接 Done。
3. Review & Test Agent 后续对所有 `IMPL-*` 任务都必须包含 `Implementation Boundary Check`。
4. 后续若启动真实数据库迁移，应保持 `APP_DATABASE_URL` 作为统一配置入口，不改变 `/api/v1` contract。
5. State Manager Agent 每轮结束后更新本文件，避免上下文漂移。

## 7. 需要用户裁决的问题

当前没有新的阻塞裁决问题。
