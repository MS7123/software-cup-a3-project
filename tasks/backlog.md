# Backlog

最后更新：2026-06-03  
维护角色：State Manager Agent / Task Manager

## 待规划任务

| Task ID | 任务 | 关联需求 | 关联验收标准 | 状态 | 说明 |
|---|---|---|---|---|---|
| PLAN-001 | 细化数据结构课程演示脚本 | R1-R10 | AC1-AC10 | Backlog | 需要 Requirement Agent 可建议内容，Task Manager 决定是否进入 Current |
| PLAN-002 | 编写测试计划 | R1-R13 | AC1-AC13 | Backlog | 由 Review & Test Agent 负责；State Manager 只记录任务状态 |
| PLAN-003 | 设计开源依赖清单模板 | R12 | AC12 | Backlog | 随实现依赖逐步补全 |
| PLAN-004 | 更新 `docs/02-acceptance-criteria.md` 的过期“当前不可验收项”描述 | R1-R13 | AC1-AC13 | Backlog | Review & Test Agent 指出该段仍写着仓库无实现代码、测试配置、依赖配置，已与当前事实不符 |

## 待实现任务

| Task ID | 任务 | 关联需求 | 关联验收标准 | 状态 | 说明 |
|---|---|---|---|---|---|
| IMPL-005 | 实现资源生成、Tutor 问答、Quiz 和 Evaluator 最小闭环 | R5, R6, R7, R8, R9 | AC5, AC6, AC7, AC8, AC9 | Backlog | 依赖 IMPL-004 |
| IMPL-006 | 初始化前端学生端工程 | R10 | AC10 | Backlog | 建议后端基础 API 稳定后开始 |
| IMPL-007 | 实现学生端 MVP 页面 | R10 | AC10 | Backlog | 依赖 IMPL-003 至 IMPL-005 |
| IMPL-008 | 添加自动化测试与基础验证脚本 | R1-R13 | AC1-AC13 | Backlog | 依赖首批后端实现 |
| IMPL-009 | 添加部署配置 | R11 | AC11 | Backlog | 依赖前后端工程初始化 |

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
