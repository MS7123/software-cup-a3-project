# Done Tasks

最后更新：2026-06-05
维护角色：State Manager Agent / Task Manager

规则：实现任务只有在 Review & Test Agent 明确给出“通过”结论后，才能由 Task Manager 移入本文件。State Manager Agent / Task Manager 不执行测试任务，不自行产生测试结论。

- [x] 建立 A3 项目仓库目录结构。
- [x] 建立 `docs/00-project-brief.md`。
- [x] 完成 A3 开源项目技术调研与技术路线建议。
- [x] 完成第三方开源项目使用边界说明。
- [x] 完成 A6 赛题讨论总结。
- [x] 建立 `docs/03-architecture.md`。
- [x] 建立 `docs/decisions/0001-architecture-baseline.md`。
- [x] 建立 `docs/01-requirements.md` 初稿。
- [x] 建立 `docs/02-acceptance-criteria.md` 初稿。
- [x] 建立 `docs/06-project-state.md`。
- [x] 建立任务状态文件：`tasks/backlog.md`、`tasks/current.md`、`tasks/done.md`、`tasks/blocked.md`。
- [x] 建立 `reviews/review-log.md`。
- [x] `PLAN-004`：更新 `docs/02-acceptance-criteria.md` 的过期“当前不可验收项”描述。
  - 完成范围：将“当前不可验收项”更新到 2026-06-04 当前事实，明确 `IMPL-001` 到 `IMPL-009` 的已通过范围，以及当前仍不可标记为完整 Done 的能力边界。
  - 维护来源：State Manager Agent / Task Manager 文档治理更新。
- [x] `PLAN-005`：添加 `.gitignore` 仓库卫生规则。
  - 完成范围：新增 Python、frontend、build、SQLite demo database 等常见本地产物忽略规则。
  - 维护来源：State Manager Agent / Task Manager 文档与仓库治理更新。
- [x] `PLAN-006`：明确 demo SQLite 与正式 PostgreSQL 配置路径。
  - 完成范围：在部署文档、示例环境变量和项目状态中明确 SQLite 仅用于 demo / local，正式数据库统一通过 `APP_DATABASE_URL` 切换到 `postgresql+psycopg://...`。
  - 维护来源：State Manager Agent / Task Manager 文档治理更新。

## 已通过 Review 的实现任务

- [x] `COMP-005`：新增科大讯飞星辰 MaaS 比赛默认启动入口。
  - 完成范围：复用现有 OpenAI-compatible adapter，配置 MaaS `/v2`、`xop3qwen1b7`、User/Process scope APIKey、七项 LLM purpose、rule-based fallback、环境恢复和前端自动可用端口。
  - 自动化证据：`tests/test_spark_competition_script.py` 覆盖配置、密钥保护顺序、全部 purpose、参数传递、端口占用、`-SmokeOnly` 和部署文档；既有提交为 `3ba978a`、`7347a27`、`6d2d789`。
  - 保留边界：`run-local.ps1` 继续作为离线 rule-based 开发入口，比赛脚本不保存或输出真实 APIKey。

- [x] `COMP-004`：完成 Quiz LLM 接入。
  - 完成范围：新增 LLMQuizAgent/factory、五类题型 schema、课程证据/画像/掌握度/最近错误上下文、Quiz metadata、Critic 引用与格式底线、客观题确定性评分、开放题 Evaluator 路由和安全 fallback。
  - 自动化证据：`tests/test_quiz_llm.py` 覆盖五类题型、画像差异、假引用、正文伪引用、非法 JSON、timeout、无检索、Critic 连续拒绝、API trace、确定性评分和 fallback 评价闭环；全量后端测试和前端生产构建通过。
  - 联机证据：星火 MaaS `xop3qwen1b7` 对两种画像均返回 grounded LLM Quiz 且题干指纹不同；真实 API 返回 `execution_mode=llm`、2 个 Retriever 引用，提交后确定性评分和掌握度更新成功。
  - 保留边界：RuleBasedCriticAgent、客观题确定性评分、开放题已有 Evaluator 和 RuleBasedQuizAgent fallback 均继续保留。

- [x] `COMP-003`：完成 Hybrid 学习路径与主动资源推荐。
  - 完成范围：新增 Hybrid Planner agent/factory、`LLM_ENABLE_FOR_PLANNER`、知识图谱拓扑约束、画像与掌握度排序、资源类型/理由/优先级、Quiz/画像/节点完成后的幂等重算，以及结构化校验和 rule-based fallback。
  - 自动化证据：`tests/test_hybrid_planner.py` 的 9 项测试覆盖真实节点、先修关系、未知/重复节点、环、timeout、配置开关、画像差异和 Quiz 后重排；相关回归 20 项、全量后端测试及前端生产构建均通过。
  - 联机证据：科大讯飞星辰 MaaS `xop3qwen1b7` 返回合法规划，`execution_mode=llm`、`fallback_used=false` 且先修关系有效；违规排序会被规则层拒绝并生成合法拓扑 fallback。
  - 保留边界：知识点真实性、先修硬约束、无环/去重/schema 校验与 fallback 继续由规则层负责，LLM 不得绕过确定性约束。

- [x] `COMP-002`：完成初始对话画像 LLM 接入。
  - 完成范围：新增 `LLMProfileBuilderAgent`、独立 factory、六维 Pydantic schema、`LLM_ENABLE_FOR_PROFILE_BUILDER`、规则 fallback，以及画像 history/Agent run 的 execution mode、provider、model、耗时和 fallback reason 证据。
  - 自动化证据：`tests/test_profile_builder_llm.py` 覆盖配置开关、六维合法输出、否定表达输入、字段别名、非法 JSON、timeout、HTTP error、API contract、LLM history 和 fallback history。
  - 联机证据：科大讯飞星火 MaaS `xop3qwen1b7` 返回 6 个合法维度，`execution_mode=llm`、`fallback_used=false`；真实 API 建档后 Agent run 记录与运行配置一致。
  - 保留边界：`build_profile_from_dialogue()` 继续作为离线 rule-based fallback，REST 请求和响应 contract 未发生破坏性变化。

- [x] `IMPL-001`：初始化后端基础结构、数据模型和 API schema 骨架。
  - Review 结论：通过，仅限 `IMPL-001` 的任务范围。
  - Review 来源：`reviews/review-log.md` 的 `2026-06-03 Review & Test Agent Review: IMPL-001`。
  - 已验证范围：后端 package 基础结构、SQLAlchemy model、`Pydantic` schema、API 占位契约、service / adapter protocol 隔离、后端契约测试和 wheel 构建。
  - 明确非 Done：完整 MVP 功能、demo data 真实加载、学生画像 API 行为、学习路径、Agent 实际执行、RAG、Quiz、Evaluator、前端页面、部署配置。
- [x] `IMPL-002`：实现 demo data 加载能力。
  - Review 结论：通过，仅限 `IMPL-002` 的任务范围。
  - Review 来源：`reviews/review-log.md` 的 `2026-06-03 Review & Test Agent Retest: IMPL-002`。
  - 已验证范围：数据结构课程 seed data、5 个 MVP 知识点、3 个模拟学生画像、模拟课程资料 chunk、source_ref、数据库加载能力、demo data HTTP 状态/加载接口。
  - 明确非 Done：完整 AC1、完整 AC2、完整 AC3、真实用户上传、文件解析失败提示、用户创建/选择/编辑画像 API、正式课程知识点管理 API、完整 MVP 产品功能。
- [x] `IMPL-003`：实现学生画像与课程知识点 API。
  - Review 结论：通过，仅限 `IMPL-003` 的任务范围。
  - Review 来源：`reviews/review-log.md` 的 `2026-06-03 Review & Test Agent Retest: IMPL-003`。
  - 已验证范围：学生画像列表、详情和创建 API；课程知识点图查询 API；3 个 seed 画像可返回；数据结构课程、5 个 MVP 知识点和知识点关系可查询；HTTP 错误码转换位于 API layer；service 层不直接依赖 FastAPI。
  - 明确非 Done：完整 AC2、完整 AC3、前端选择/编辑体验、完整课程知识点维护能力、完整 MVP 产品功能。
- [x] `IMPL-004`：实现学习路径与 `Planner Agent` 最小流程。
  - Review 结论：通过，仅限 `IMPL-004` 的任务范围。
  - Review 来源：`reviews/review-log.md` 的 `2026-06-03 Review & Test Agent Review: IMPL-004`。
  - 已验证范围：学习路径创建 API、路径详情 API、Planner 最小流程、`agent_runs` / `agent_run_steps` 摘要记录、Agent run 详情 API。
  - 明确非 Done：完整 AC4、完整 AC9、完整多 Agent 学习闭环、Resource / Tutor / Quiz / Evaluator、RAG、前端页面、完整 MVP 产品功能。
- [x] `IMPL-005`：实现资源生成、Tutor 问答、Quiz 和 Evaluator 最小闭环。
  - Review 结论：通过，仅限 `IMPL-005` 的任务范围。
  - Review 来源：`reviews/review-log.md` 的 `2026-06-03 Review & Test Agent Review: IMPL-005`。
  - 已验证范围：资源生成 API、Tutor 问答 API、Quiz 生成 API、提交作答与评价 API、对应 `agent_runs` / `agent_run_steps` 记录、最小 learning loop API 测试、Implementation Boundary Check。
  - 明确非 Done：完整前端学习闭环、真实 RAG / VectorStore、真实 LLM provider、统一多 Agent run 聚合展示、部署配置、完整 MVP 产品功能。
- [x] `IMPL-006`：初始化前端学生端工程。
  - Review 结论：通过，仅限 `IMPL-006` 的任务范围。
  - Review 来源：`reviews/review-log.md` 的 `2026-06-03 Review & Test Agent Review: IMPL-006`。
  - 已验证范围：Vite + React + TypeScript 前端工程、`/api/v1` typed client、基础学生端页面骨架、前端 build 验证、Implementation Boundary Check。
  - 明确非 Done：完整学生端 MVP 页面、浏览器联调、E2E 自动化、真实 RAG / LLM / VectorStore、部署配置、完整 MVP 产品功能。
- [x] `IMPL-007`：实现学生端 MVP 页面。
  - Review 结论：通过，仅限 `IMPL-007` 的任务范围。
  - Review 来源：`reviews/review-log.md` 的 `2026-06-03 Review & Test Agent Review: IMPL-007`。
  - 已验证范围：学生端 MVP 页面关键交互、加载/错误/空状态、节点切换、browser smoke、Implementation Boundary Check。
  - 明确非 Done：正式 E2E 测试套件、部署配置、真实 RAG / LLM / VectorStore、完整 MVP 产品功能。
- [x] `IMPL-008`：添加自动化测试与基础验证脚本。
  - Review 结论：通过，仅限 `IMPL-008` 的任务范围。
  - Review 来源：`reviews/review-log.md` 的 `2026-06-04 Review & Test Agent Retest: IMPL-008`。
  - 已验证范围：`scripts/verify.ps1` 统一验证入口、`scripts/frontend-smoke.ps1`、Playwright smoke、frontend build、backend unit tests、`pip check`、wheel build、清理验证产物、Implementation Boundary Check。
  - 明确非 Done：部署配置、真实 RAG / LLM / VectorStore、失败路径和多环境完整测试矩阵、完整 MVP 产品功能。
- [x] `IMPL-009`：添加部署配置。
  - Review 结论：通过，仅限 `IMPL-009` 的任务范围。
  - Review 来源：`reviews/review-log.md` 的 `2026-06-04 Review & Test Agent Review: IMPL-009`。
  - 已验证范围：`deployment/README.md`、`deployment/local.env.example`、`scripts/run-local.ps1`、本地 backend/frontend 启动 smoke、demo data load、Implementation Boundary Check。
  - 明确非 Done：生产级部署、数据库迁移、Redis/RQ、真实 LLMProvider、真实 VectorStore、完整 MVP 产品功能。
- [x] `IMPL-010`：接入 OpenAI-compatible `LLMProvider` 并用于 `Tutor Agent`。
  - Review 结论：通过，仅限 `IMPL-010` 的任务范围。
  - Review 来源：`reviews/review-log.md` 的 `2026-06-05 Review & Test Agent Retest: IMPL-010`。
  - 已验证范围：OpenAI-compatible `LLMProvider` adapter、Tutor agent strategy / factory、`LLM_FALLBACK_MODE=rule_based/error` 行为、provider failure fallback、Tutor API 层 `agent_run_steps` fallback 摘要记录、secret 不进入 response / metadata / agent run、本地 smoke 默认不依赖远程 LLM、Implementation Boundary Check。
  - 明确非 Done：真实外部 LLM key 联网验收、真实 RAG / VectorStore、Resource / Quiz / Evaluator 的 LLM 接入、生产级部署、数据库迁移、Redis/RQ、完整 MVP 产品功能。
