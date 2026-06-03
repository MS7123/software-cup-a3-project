# Current Tasks

最后更新：2026-06-03  
维护角色：State Manager Agent / Task Manager

## 当前批准执行

### IMPL-008: 添加自动化测试与基础验证脚本

- 状态：Current
- 负责人角色：Implementation Agent
- 关联需求：R1-R13
- 关联验收标准：AC1-AC13
- 前置依赖：
  - `IMPL-001` 已由 Review & Test Agent 验收通过。
  - `IMPL-002` 已由 Review & Test Agent 验收通过。
  - `IMPL-003` 已由 Review & Test Agent 验收通过。
  - `IMPL-004` 已由 Review & Test Agent 验收通过。
  - `IMPL-005` 已由 Review & Test Agent 验收通过。
  - `IMPL-006` 已由 Review & Test Agent 验收通过。
  - `IMPL-007` 已由 Review & Test Agent 验收通过。
- 输入依据：
  - `docs/01-requirements.md`
  - `docs/02-acceptance-criteria.md`
  - `docs/03-architecture.md`
  - `tasks/done.md`
  - `reviews/review-log.md`
- 预期输出：
  - 将当前 backend unit tests、frontend build、browser smoke 或等价验证沉淀为可复用脚本/测试入口。
  - 尽量把临时 review 验证转成仓库内可持续执行的自动化检查。
  - 补最小前端 E2E / smoke 测试，覆盖当前学生端关键闭环。
  - 保持现有 API contract，不为测试方便而破坏 service / adapter / frontend 边界。
  - 保持 `Implementation Boundary Check`：测试层不把 demo/mock 逻辑散落进生产代码。
- Done 条件：
  - 任务实现完成后先进入 `tasks/review.md`，不得直接进入 `tasks/done.md`。
  - Review & Test Agent 必须负责测试和验证，并明确结论：自动化验证入口可运行，能稳定覆盖当前阶段关键后端/前端行为，且没有为通过测试而破坏边界。
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
