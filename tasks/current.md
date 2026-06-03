# Current Tasks

最后更新：2026-06-04  
维护角色：State Manager Agent / Task Manager

## 当前批准执行

### PLAN-004: 更新 `docs/02-acceptance-criteria.md` 的过期“当前不可验收项”描述

- 状态：Current
- 负责人角色：State Manager Agent / Task Manager
- 关联需求：R1-R13
- 关联验收标准：AC1-AC13
- 前置依赖：
  - `IMPL-001` 到 `IMPL-009` 的状态已由 Review & Test Agent 结论更新到任务与项目状态文件。
- 输入依据：
  - `docs/02-acceptance-criteria.md`
  - `docs/06-project-state.md`
  - `reviews/review-log.md`
  - `tasks/backlog.md`
- 预期输出：
  - 将 `docs/02-acceptance-criteria.md` 中与当前仓库事实不符的“当前不可验收项”描述更新为最新状态。
  - 保持与 `docs/06-project-state.md`、`reviews/review-log.md`、`tasks/done.md` 一致。
  - 不修改需求优先级，不扩大已完成范围，不把 Partial 写成 Done。
- Done 条件：
  - 任务实现完成后先进入 `tasks/review.md`，不得直接进入 `tasks/done.md`。
  - State Manager Agent / Task Manager 完成文档事实校准后，再决定是否推进 `PLAN-005`。
  - 不涉及代码功能验收，不得借此修改已通过任务的 Done 边界。
- Review 要求：
  - 若只做文档事实修正，由 State Manager Agent / Task Manager 自行维护状态流转记录。

## 当前不允许执行

- 不允许 Implementation Agent 执行 `tasks/backlog.md` 中未移入 Current 的任务。
- 不允许直接重写需求优先级或扩大已完成范围。
- 不允许直接引入大型开源项目代码。
- 不允许把未经过 Review 和验证的任务标记为 Done。
