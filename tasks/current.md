# Current Tasks

最后更新：2026-06-03  
维护角色：State Manager Agent / Task Manager

## 当前批准执行

### IMPL-004: 实现学习路径与 `Planner Agent` 最小流程

- 状态：Current
- 负责人角色：Implementation Agent
- 关联需求：R4, R9
- 关联验收标准：AC4, AC9
- 前置依赖：
  - `IMPL-001` 已由 Review & Test Agent 验收通过。
  - `IMPL-002` 已由 Review & Test Agent 验收通过。
  - `IMPL-003` 已由 Review & Test Agent 验收通过。
- 输入依据：
  - `docs/01-requirements.md`
  - `docs/02-acceptance-criteria.md`
  - `docs/03-architecture.md`
  - `tasks/done.md`
  - `reviews/review-log.md`
- 预期输出：
  - 实现学习路径创建或生成接口，能够基于学生画像、课程和目标生成阶段化学习路径。
  - 实现 `Planner Agent` 最小流程或等价 orchestrator 调用，输出学习步骤、关联知识点和路径依据。
  - 写入或返回 `agent_runs` / `agent_run_steps` 摘要记录，至少体现 `Planner Agent` 调用顺序、输入摘要、输出摘要和关键决策依据。
  - 生成结果应绑定 seed data 中的数据结构课程、3 个模拟画像和 5 个 MVP 知识点范围。
  - API handler 仍应通过 service 层访问业务逻辑，不直接绕过既有 service / adapter 边界。
- Done 条件：
  - 任务实现完成后先进入 `tasks/review.md`，不得直接进入 `tasks/done.md`。
  - Review & Test Agent 必须负责测试和验证，并明确结论：学习路径 API 可用；`Planner Agent` 最小流程可执行；路径包含阶段化步骤、关联知识点和依据说明；Agent run 摘要记录满足 AC9 的当前阶段范围。
  - State Manager Agent / Task Manager 不运行测试命令，只根据 Review & Test Agent 的结论移动任务状态。
- Review 要求：
  - Review & Test Agent 在 `reviews/review-log.md` 写明“通过”或“不通过”。
  - 只有明确“通过”后，Task Manager 才能移动到 `tasks/done.md`。

## 当前不允许执行

- 不允许 Implementation Agent 执行 `tasks/backlog.md` 中未移入 Current 的任务。
- 不允许直接实现前端页面。
- 不允许直接引入大型开源项目代码。
- 不允许把未经过 Review 和验证的任务标记为 Done。
