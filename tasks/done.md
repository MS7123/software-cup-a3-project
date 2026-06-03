# Done Tasks

最后更新：2026-06-03  
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

## 已通过 Review 的实现任务

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
