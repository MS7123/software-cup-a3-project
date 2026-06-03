# Backlog

最后更新：2026-06-04  
维护角色：State Manager Agent / Task Manager

## 待规划任务

| Task ID | 任务 | 关联需求 | 关联验收标准 | 状态 | 说明 |
|---|---|---|---|---|---|
| PLAN-001 | 细化数据结构课程演示脚本 | R1-R10 | AC1-AC10 | Backlog | 需要 Requirement Agent 可建议内容，Task Manager 决定是否进入 Current |
| PLAN-002 | 编写测试计划 | R1-R13 | AC1-AC13 | Backlog | 由 Review & Test Agent 负责；State Manager 只记录任务状态 |
| PLAN-003 | 设计开源依赖清单模板 | R12 | AC12 | Backlog | 随实现依赖逐步补全 |
| PLAN-004 | 更新 `docs/02-acceptance-criteria.md` 的过期“当前不可验收项”描述 | R1-R13 | AC1-AC13 | Backlog | Review & Test Agent 指出该段仍写着仓库无实现代码、测试配置、依赖配置，已与当前事实不符 |
| PLAN-005 | 添加 `.gitignore` 仓库卫生规则 | R11 | AC11 | Backlog | Review 多次指出测试可能生成 `__pycache__` / `.pyc` |
| PLAN-006 | 明确 demo SQLite 与正式 PostgreSQL 配置路径 | R11, R13 | AC11, AC13 | Backlog | 默认 SQLite 可用于 dev/demo，但需补正式 PostgreSQL 配置说明 |

## 待实现任务

| Task ID | 任务 | 关联需求 | 关联验收标准 | 状态 | 说明 |
|---|---|---|---|---|---|

## 待修复 / 待重构任务

| Task ID | 任务 | 来源 | 状态 | 说明 |
|---|---|---|---|---|
| REFACTOR-001 | Planner 根据 `concept_relations` 推导学习顺序 | IMPL-004 Review non-blocking issue | Backlog | 当前按 `Concept.id` 顺序生成路径，后续真实课程数据可能顺序不稳定 |
| REFACTOR-002 | 学习路径创建与 Agent run 记录的一致性处理 | IMPL-004 Review non-blocking issue | Backlog | 后续可考虑 transaction 或补偿逻辑，避免有 path 无 run |
| FIX-001 | 明确 `GET /student-profiles` 返回所有画像还是仅 demo 画像 | IMPL-003 Review remaining issue | Backlog | 当前 `ProfileService.list_demo_profiles()` 返回所有 `StudentProfile` |
| REFACTOR-003 | 聚合 Resource / Tutor / Quiz / Evaluator 的统一 learning-flow run | IMPL-005 Review non-blocking issue | Backlog | 当前 4 个能力分别创建独立 `agent_run`，后续若要展示统一调用顺序需做 run 聚合或 run list API |
| TEST-002 | 补失败路径与多环境自动化测试覆盖 | IMPL-008 Review non-blocking issue | Backlog | 当前 Playwright smoke 已覆盖正向闭环，但仍缺失败路径、多浏览器和移动视口覆盖 |
| CONFIG-001 | 明确 Playwright channel 跨机器运行策略 | IMPL-008 Review non-blocking issue | Backlog | Windows 当前默认使用 `msedge`，其他机器需要 `PLAYWRIGHT_CHANNEL` 或 Chromium 安装策略 |

## 已裁决事项

- [x] MVP 范围：A3、数据结构、学生端闭环、模拟数据。
- [x] 需求优先级：优先突出 `Multi-Agent` 协作流程。
- [x] 数据结构 MVP 知识点：复杂度分析、链表、栈/队列、二叉树遍历、BFS/DFS。
- [x] Agent 流程展示粒度：展示摘要即可。
- [x] Requirement Agent 不调整已 Accepted 的架构基线，只记录架构影响分析。
- [x] 学生画像样例数量和类型：基础薄弱型、考试冲刺型、算法实践型。
- [x] Architect Agent 已完成数据结构 MVP 架构细化，当前不需要新增 ADR。
- [x] `IMPL-001` 已由 Review & Test Agent 验收通过，范围仅限后端骨架。
- [x] `IMPL-002` 已推进到 `tasks/current.md`。
- [x] `IMPL-002` 已由 Review & Test Agent 复测通过，范围仅限 demo data 加载能力。
- [x] `IMPL-003` 已推进到 `tasks/current.md`。
- [x] `IMPL-003` 已由 Review & Test Agent 复测通过，范围仅限学生画像与课程知识点 API。
- [x] `IMPL-004` 已推进到 `tasks/current.md`。
- [x] `IMPL-004` 已由 Review & Test Agent 验收通过，范围仅限学习路径与 `Planner Agent` 最小流程。
- [x] `IMPL-005` 已推进到 `tasks/current.md`。
- [x] `IMPL-005` 已由 Review & Test Agent 验收通过，范围仅限资源生成、Tutor 问答、Quiz 和 Evaluator 最小闭环。
- [x] `IMPL-006` 已推进到 `tasks/current.md`。
- [x] `IMPL-006` 已由 Review & Test Agent 验收通过，范围仅限前端学生端工程初始化和基础页面骨架。
- [x] `IMPL-007` 已推进到 `tasks/current.md`。
- [x] `IMPL-007` 已由 Review & Test Agent 验收通过，范围仅限学生端 MVP 页面关键交互。
- [x] `IMPL-008` 已推进到 `tasks/current.md`。
- [x] `IMPL-008` 已由 Review & Test Agent 复测通过，范围仅限自动化测试与基础验证脚本。
- [x] `IMPL-009` 已推进到 `tasks/current.md`。
- [x] `IMPL-009` 已由 Review & Test Agent 验收通过，范围仅限本地部署与演示运行配置。
- [x] `PLAN-004` 已推进到 `tasks/current.md`。
