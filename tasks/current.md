# Current Tasks

最后更新：2026-06-03  
维护角色：State Manager Agent / Task Manager

## 当前批准执行

### IMPL-006: 初始化前端学生端工程

- 状态：Current
- 负责人角色：Implementation Agent
- 关联需求：R10
- 关联验收标准：AC10
- 前置依赖：
  - `IMPL-001` 已由 Review & Test Agent 验收通过。
  - `IMPL-002` 已由 Review & Test Agent 验收通过。
  - `IMPL-003` 已由 Review & Test Agent 验收通过。
  - `IMPL-004` 已由 Review & Test Agent 验收通过。
  - `IMPL-005` 已由 Review & Test Agent 验收通过。
- 输入依据：
  - `docs/01-requirements.md`
  - `docs/02-acceptance-criteria.md`
  - `docs/03-architecture.md`
  - `tasks/done.md`
  - `reviews/review-log.md`
- 预期输出：
  - 初始化前端学生端工程目录、依赖配置和运行入口。
  - 建立与当前后端 `/api/v1` 契约兼容的基础页面骨架与 API client 组织方式。
  - 预留学生画像、学习路径、资源、问答、测验结果的页面或模块边界，但不越权实现未进入 Current 的功能任务。
  - 前端不得硬编码核心业务结果；应消费后端 API 或为后续接线保留明确 adapter 边界。
  - 保持 `Implementation Boundary Check`：frontend 不承载核心业务逻辑，不绕过 API contract。
- Done 条件：
  - 任务实现完成后先进入 `tasks/review.md`，不得直接进入 `tasks/done.md`。
  - Review & Test Agent 必须负责测试和验证，并明确结论：前端工程可运行、基础页面骨架可访问、与当前后端契约对齐、没有前端 hardcoded 核心结果。
  - Review & Test Agent 必须填写 `Implementation Boundary Check`，且结论不得为 `Blocking`。
  - State Manager Agent / Task Manager 不运行测试命令，只根据 Review & Test Agent 的结论移动任务状态。
- Review 要求：
  - Review & Test Agent 在 `reviews/review-log.md` 写明“通过”或“不通过”。
  - 只有明确“通过”后，Task Manager 才能移动到 `tasks/done.md`。

## 当前不允许执行

- 不允许 Implementation Agent 执行 `tasks/backlog.md` 中未移入 Current 的任务。
- 不允许直接实现前端页面。
- 不允许直接引入大型开源项目代码。
- 不允许把未经过 Review 和验证的任务标记为 Done。
