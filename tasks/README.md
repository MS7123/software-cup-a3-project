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
- 所有 `IMPL-*` Review 都必须包含 `Implementation Boundary Check`。
- 如果缺少 `Implementation Boundary Check`，任务不得移入 Done。
- 如果 `Implementation Boundary Check` 发现 Blocking，Task Manager 应创建 `FIX-*` 或 `REFACTOR-*` 任务。
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

## Implementation Boundary Rules

从 `IMPL-005` 起，所有 IMPL-* 任务都必须接受 implementation boundary review。该规则用于防止 MVP 的 demo data、mock provider 和 rule-based logic 变成不可复用的 hardcoded demo。

### 任务描述要求

每个 IMPL-* 任务在进入 `Current` 前，应明确说明：

- 是否涉及 demo data。
- 是否涉及 mock provider。
- 是否涉及 rule-based `Planner` / `Tutor` / `Quiz` / `Evaluator` logic。
- 涉及的逻辑应位于哪个 service、adapter、Agent、strategy 或 orchestrator 边界。
- 是否需要保持未来替换真实 LLM / RAG / VectorStore 的契约稳定。

### 边界规则

- Demo data 必须集中在 seed、fixture 或 demo data service 中，不得散落在 API handler、frontend、Agent prompt 或业务分支中。
- Mock provider 必须实现正式 adapter / protocol 契约；service 和 orchestrator 不得直接依赖具体 mock 类。
- Rule-based logic 必须隔离在 Agent、strategy 或 service 边界内，并返回标准 domain result。
- API handler 只负责 request / response、依赖注入、错误转换和调用 service，不得承载核心业务规则。
- Frontend 只能消费 API，不得硬编码核心 demo data、学习路径、Quiz 答案或 Agent steps。
- 替换真实 LLM / RAG / VectorStore 时，不得破坏 `/api/v1` schema、service contract、adapter contract 和 `agent_runs` / `agent_run_steps` 记录结构。

### Review 要求

Review & Test Agent 必须在每个 IMPL-* Review 中增加 `Implementation Boundary Review` 小节，并给出整体结论：

- `Pass`：边界清晰，允许进入 Done。
- `Needs Fix`：有局部边界问题，修复后复测。
- `Blocking`：存在 hardcoded demo、handler 承载业务规则、frontend 模拟核心结果、service 直连 provider 或破坏 adapter 契约等问题，不得进入 Done。

Task Manager 只能在 Review & Test Agent 明确给出 `Pass` 后移动任务到 `Done`。如结论为 `Needs Fix` 或 `Blocking`，应拆分 `FIX-*`、`REFACTOR-*` 或 `BLOCKER-FIX-*` 任务，不得把修复工作混入未批准的后续 IMPL 任务。
