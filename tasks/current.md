# Current Tasks

最后更新：2026-06-04  
维护角色：State Manager Agent / Task Manager

## 当前批准执行

### IMPL-009: 添加部署配置

- 状态：Current
- 负责人角色：Implementation Agent
- 关联需求：R11
- 关联验收标准：AC11
- 前置依赖：
  - `IMPL-001` 已由 Review & Test Agent 验收通过。
  - `IMPL-002` 已由 Review & Test Agent 验收通过。
  - `IMPL-003` 已由 Review & Test Agent 验收通过。
  - `IMPL-004` 已由 Review & Test Agent 验收通过。
  - `IMPL-005` 已由 Review & Test Agent 验收通过。
  - `IMPL-006` 已由 Review & Test Agent 验收通过。
  - `IMPL-007` 已由 Review & Test Agent 验收通过。
  - `IMPL-008` 已由 Review & Test Agent 验收通过。
- 输入依据：
  - `docs/01-requirements.md`
  - `docs/02-acceptance-criteria.md`
  - `docs/03-architecture.md`
  - `tasks/done.md`
  - `reviews/review-log.md`
- 预期输出：
  - 增加本地运行、演示运行和必要环境变量的部署配置。
  - 明确前后端启动方式、依赖准备、数据库/代理/端口等运行说明。
  - 尽量保持当前 `scripts/verify.ps1`、frontend proxy、backend entrypoint 的使用方式稳定。
  - 不为了部署方便破坏现有 service / adapter / frontend 边界。
  - 保持 `Implementation Boundary Check`：部署层不把 demo/mock 逻辑写进生产业务代码。
- Done 条件：
  - 任务实现完成后先进入 `tasks/review.md`，不得直接进入 `tasks/done.md`。
  - Review & Test Agent 必须负责测试和验证，并明确结论：部署配置和运行说明可用，能支持当前阶段前后端项目启动或构建验证，且没有为部署便利破坏边界。
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
