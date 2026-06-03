# Current Tasks

最后更新：2026-06-03  
维护角色：State Manager Agent / Task Manager

## 当前批准执行

### IMPL-005: 实现资源生成、Tutor 问答、Quiz 和 Evaluator 最小闭环

- 状态：Current
- 负责人角色：Implementation Agent
- 关联需求：R5, R6, R7, R8, R9
- 关联验收标准：AC5, AC6, AC7, AC8, AC9
- 前置依赖：
  - `IMPL-001` 已由 Review & Test Agent 验收通过。
  - `IMPL-002` 已由 Review & Test Agent 验收通过。
  - `IMPL-003` 已由 Review & Test Agent 验收通过。
  - `IMPL-004` 已由 Review & Test Agent 验收通过。
- 输入依据：
  - `docs/01-requirements.md`
  - `docs/02-acceptance-criteria.md`
  - `docs/03-architecture.md`
  - `tasks/done.md`
  - `reviews/review-log.md`
- 预期输出：
  - 实现 Resource 最小流程：针对学习路径节点生成资源，并关联到 `learning_path_items`。
  - 实现 Tutor 最小问答：基于数据结构 demo chunk / source_ref 返回有依据的回答。
  - 实现 Quiz 最小生成：针对知识点和难度生成题目、答案、解析和知识点标签。
  - 实现 Evaluator 最小评价：提交答案后返回评分、反馈和掌握度更新建议。
  - 将 Resource / Tutor / Quiz / Evaluator 的步骤写入 `agent_runs` / `agent_run_steps` 摘要记录。
  - 遵守 `Implementation Boundary Check`：rule-based logic 不得写在 API handler 或 frontend，demo/mock 数据集中管理，adapter/provider contract 保持稳定。
  - API handler 仍应通过 service 层访问业务逻辑，不直接绕过既有 service / adapter 边界。
- Done 条件：
  - 任务实现完成后先进入 `tasks/review.md`，不得直接进入 `tasks/done.md`。
  - Review & Test Agent 必须负责测试和验证，并明确结论：Resource / Tutor / Quiz / Evaluator 最小闭环可用；生成资源、问答、测验、评价输出满足当前阶段验收；Agent run 摘要记录至少覆盖 Planner 外的新增 Agent steps。
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
