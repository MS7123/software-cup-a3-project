# Current Tasks

最后更新：2026-07-13
维护角色：State Manager Agent / Task Manager

## 当前批准执行

### PLAN-002: 编写测试计划

- 状态：Current
- 负责人角色：Review & Test Agent
- 关联需求：R1-R13
- 关联验收标准：AC1-AC13, AC20-AC24
- 前置依赖：
  - `IMPL-001` 到 `IMPL-010` 已在当前范围内通过 Review & Test Agent。
  - `PLAN-004`、`PLAN-005`、`PLAN-006` 已完成，基础文档事实与仓库卫生边界已对齐。
- 输入依据：
  - `docs/01-requirements.md`
  - `docs/02-acceptance-criteria.md`
  - `docs/03-architecture.md`
  - `docs/06-project-state.md`
  - `reviews/review-log.md`
  - `tasks/backlog.md`
- 预期输出：
  - 形成当前阶段可执行的测试计划，覆盖 backend、frontend、browser smoke、LLM provider fallback、失败路径和跨环境验证。
  - 明确哪些测试已存在，哪些测试仍缺失，哪些测试应进入后续 `TEST-*` / `CONFIG-*` 任务。
  - 与 `docs/06-project-state.md`、`reviews/review-log.md`、`tasks/backlog.md` 中的缺口保持一致。
- Done 条件：
  - 输出应能指导后续 `TEST-002` 和相关验证工作，而不是停留在泛泛描述。
  - 不得借此修改已通过任务的 Done 边界。
  - 不得把测试计划本身写成任何新功能 Done 结论。
- Review 要求：
  - 由 Review & Test Agent 维护测试计划内容；State Manager Agent / Task Manager 负责记录任务状态。

## 当前不允许执行

- 不允许 Implementation Agent 执行 `tasks/backlog.md` 中未移入 Current 的任务。
- 不允许直接重写需求优先级或扩大已完成范围。
- 不允许直接引入大型开源项目代码。
- 不允许把未经过 Review 和验证的任务标记为 Done。
