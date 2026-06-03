# Task Management Rules

最后更新：2026-06-03  
维护角色：State Manager Agent / Task Manager

## 权限边界

- State Manager Agent / Task Manager 拥有 `tasks/` 目录的正式维护权。
- Requirement Agent 只能建议新增任务，不能直接修改 `tasks/current.md`、`tasks/done.md`。
- Architect Agent 只能建议拆分任务，不能直接修改 `tasks/current.md`、`tasks/done.md`。
- Implementation Agent 只能执行 `tasks/current.md` 中的任务，不能移动任务状态。
- Review & Test Agent 只能在 `reviews/review-log.md` 中给出验收结论，不能移动任务。
- State Manager Agent / Task Manager 不负责执行测试任务，不运行测试命令，不替代 Review & Test Agent 给出“通过/不通过”验收结论。

## 状态流转

```text
Backlog -> Current -> Review -> Done
Backlog -> Current -> Blocked
Blocked -> Backlog / Current
```

## 移动规则

- 新需求、建议任务和待拆分任务进入 `tasks/backlog.md`。
- 当前批准执行的任务进入 `tasks/current.md`。
- 已实现但等待 Review & Test Agent 验收的任务进入 `tasks/review.md`。
- 只有 Review & Test Agent 明确给出“通过”结论后，Task Manager 才能将任务移入 `tasks/done.md`。
- 阶段任务移入 Done 后，Task Manager 应从 Backlog 中选择依赖已满足、验收标准明确、架构依据充分的下一阶段实现任务移入 Current。
- 缺少需求、验收标准、架构决策、依赖条件，或同一问题连续两次修复失败的任务进入 `tasks/blocked.md`。
- 未经验证的实现任务不得标记为 Done。
- State Manager Agent / Task Manager 只能引用 Review & Test Agent 已写入 `reviews/review-log.md` 的测试和验收结论，不自行补测。

## 任务字段

每个可执行任务应包含：

- `Task ID`
- `状态`
- `负责人角色`
- `关联需求`
- `关联验收标准`
- `输入依据`
- `预期输出`
- `Done 条件`
- `Review 要求`
