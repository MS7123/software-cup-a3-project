# Current Tasks

最后更新：2026-06-03  
维护角色：State Manager Agent / Task Manager

## 当前批准执行

### IMPL-007: 实现学生端 MVP 页面

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
  - `IMPL-006` 已由 Review & Test Agent 验收通过。
- 输入依据：
  - `docs/01-requirements.md`
  - `docs/02-acceptance-criteria.md`
  - `docs/03-architecture.md`
  - `tasks/done.md`
  - `reviews/review-log.md`
- 预期输出：
  - 在现有前端骨架上实现学生端 MVP 页面，覆盖画像选择、学习路径查看、资源查看、Tutor 问答、Quiz 提交、评价反馈和 Agent run 摘要展示。
  - 补基础交互状态：loading、error、empty state、当前节点选择，不停留在纯骨架或默认第一项展示。
  - 与当前后端 `/api/v1` 契约保持一致，不在 frontend 硬编码核心业务结果。
  - 为后续浏览器联调和 E2E 验证保留稳定页面结构与 API adapter 边界。
  - 保持 `Implementation Boundary Check`：frontend 不承载核心业务逻辑，不绕过 API contract。
- Done 条件：
  - 任务实现完成后先进入 `tasks/review.md`，不得直接进入 `tasks/done.md`。
  - Review & Test Agent 必须负责测试和验证，并明确结论：学生端 MVP 页面在当前阶段范围内可用，关键交互完成，且没有 frontend hardcoded 核心结果。
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
