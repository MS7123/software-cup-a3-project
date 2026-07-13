# Backlog

最后更新：2026-06-05
维护角色：State Manager Agent / Task Manager

## 待规划任务

| Task ID | 任务 | 关联需求 | 关联验收标准 | 状态 | 说明 |
|---|---|---|---|---|---|
| PLAN-001 | 细化数据结构课程演示脚本 | R1-R10 | AC1-AC10 | Backlog | 需要 Requirement Agent 可建议内容，Task Manager 决定是否进入 Current |
| PLAN-003 | 设计开源依赖清单模板 | R12 | AC12 | Backlog | 随实现依赖逐步补全 |

## 待修复 / 待重构任务

| Task ID | 任务 | 来源 | 状态 | 说明 |
|---|---|---|---|---|
| REFACTOR-001 | Planner 根据 `concept_relations` 推导学习顺序 | IMPL-004 Review non-blocking issue | Backlog | 当前按 `Concept.id` 顺序生成路径，后续真实课程数据可能顺序不稳定 |
| REFACTOR-002 | 学习路径创建与 Agent run 记录的一致性处理 | IMPL-004 Review non-blocking issue | Backlog | 后续可考虑 transaction 或补偿逻辑，避免有 path 无 run |
| FIX-001 | 明确 `GET /student-profiles` 返回所有画像还是仅 demo 画像 | IMPL-003 Review remaining issue | Backlog | 当前 `ProfileService.list_demo_profiles()` 返回所有 `StudentProfile` |
| REFACTOR-003 | 聚合 Resource / Tutor / Quiz / Evaluator 的统一 learning-flow run | IMPL-005 Review non-blocking issue | Backlog | 当前 4 个能力分别创建独立 `agent_run`，后续若要展示统一调用顺序需做 run 聚合或 run list API |
| REFACTOR-004 | 抽离 Tutor agent strategy / factory | Architect Agent 真实 LLM 接入建议 | Backlog | 为 `RuleBasedTutorAgent` 和未来 `LLMTutorAgent` 提供统一 strategy / factory 边界 |
| TEST-002 | 补失败路径与多环境自动化测试覆盖 | IMPL-008 Review non-blocking issue | Backlog | 当前 Playwright smoke 已覆盖正向闭环，但仍缺失败路径、多浏览器和移动视口覆盖 |
| CONFIG-001 | 明确 Playwright channel 跨机器运行策略 | IMPL-008 Review non-blocking issue | Backlog | Windows 当前默认使用 `msedge`，其他机器需要 `PLAYWRIGHT_CHANNEL` 或 Chromium 安装策略 |

## 待实现任务

| Task ID | 任务 | 关联需求 | 关联验收标准 | 状态 | 说明 |
|---|---|---|---|---|---|
| COMP-001 | 构造完整高校专业课程知识库 | A3-课程知识库 | COMP-001-AC | Backlog | 目标效果与验收标准见 `docs/plans/competition/16-a3-requirements-gap-roadmap.md` |
| COMP-002 | 完成初始对话画像 LLM 接入 | A3-对话式画像 | COMP-002-AC | Done | 已完成 LLMProfileBuilderAgent、六维 schema、星火联机验证、历史证据和 rule-based fallback |
| COMP-003 | 完成 Hybrid 学习路径与主动资源推荐 | A3-学习路径与资源推送 | COMP-003-AC | Done | 已完成图谱硬约束、LLM 排序、主动推荐、动态重算、fallback 与星火联机验证 |
| COMP-004 | 完成 Quiz LLM 接入 | A3-个性化练习题 | COMP-004-AC | Done | 已完成五类题型、grounded 引用、Critic、确定性客观题评分、fallback 与星火闭环 |
| COMP-005 | 新增科大讯飞星辰 MaaS 比赛默认启动入口 | A3-大模型融合 | COMP-005-AC | Done | 已完成 MaaS `/v2` 比赛入口、七项 LLM purpose、密钥保护、自动端口与 SmokeOnly 验证 |
| COMP-006 | 启用并验证已经接入的 LLM 能力 | A3-大模型融合 | COMP-006-AC | Done | 已完成四项既有 Agent 的真实星火验收、引用白名单、断连重试兼容、无证据 no-op 与 opt-in 联机测试 |
| COMP-007 | 统一 LLM 配置与运行证据 | A3-Multi-Agent | COMP-007-AC | Current | 下一开发增量：统一 execution mode、provider、model、fallback、source refs 和耗时证据 |
| COMP-008 | 建立防幻觉与内容安全验证闭环 | A3-非功能要求 | COMP-008-AC | Backlog | 固化引用白名单、安全拦截和降级策略 |
| COMP-009 | 完成比赛交付文档与合规材料 | A3-文档及其他要求 | COMP-009-AC | Backlog | 开发说明、测试说明、依赖协议和 AI 工具说明 |
| COMP-010 | 冻结 7 分钟演示与初赛作品目录 | A3-初赛提交要求 | COMP-010-AC | Backlog | 固定演示数据、流程和比赛启动入口 |
| COMP-011 | 实现真实可验证的教学动画或视频资源 | A3-多模态资源/加分项 | COMP-011-AC | Backlog | P1，产物必须真实可播放或交互 |
| COMP-012 | 增强学习效果评估与掌握度模型 | A3-学习效果评估/加分项 | COMP-012-AC | Backlog | P1，评估结果驱动路径或推荐变化 |
| COMP-013 | 补齐失败路径、跨环境和移动端测试 | A3-非功能要求 | COMP-013-AC | Backlog | P1，覆盖 MaaS、RAG、浏览器和移动视口 |
| COMP-014 | 统一项目状态、需求和验收文档 | A3-配套文档 | COMP-014-AC | Backlog | P1，统一完成状态和证据链接 |
| COMP-015 | 正式数据库、向量检索和异步任务增强 | 工程增强 | COMP-015-AC | Backlog | P2，不得阻塞比赛交付 |
| COMP-016 | 认证、多用户隔离和长期学习历史 | 工程增强 | COMP-016-AC | Backlog | P2，不得阻塞比赛交付 |

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
- [x] `PLAN-004` 已完成，用于修正过期的“当前不可验收项”描述。
- [x] `PLAN-005` 已完成，用于补充 `.gitignore` 仓库卫生规则。
- [x] `PLAN-006` 已完成，用于明确 SQLite demo / PostgreSQL 正式配置路径边界。
- [x] `PLAN-002` 已从 `tasks/current.md` 移回 `tasks/backlog.md`，当前不再作为最高优先级。
- [x] Architect Agent 已产出真实 LLM 最小接入方案和任务拆分建议，已写入任务系统。
- [x] `PLAN-007` 不再单独执行，其配置、fallback、secret 和测试边界约束已并入 `IMPL-010`。
- [x] `IMPL-010` 已推进到 `tasks/current.md`。
- [x] `FIX-002` 已随 `IMPL-010` 修复并通过复测，不再保留为 Backlog。
- [x] `TEST-003` 已随 `IMPL-010` 补齐并通过复测，不再保留为 Backlog。
- [x] `IMPL-010` 已由 Review & Test Agent 复测通过，范围仅限 Tutor Agent 的 OpenAI-compatible LLMProvider 最小接入。
- [x] `PLAN-002` 已推进到 `tasks/current.md`，作为下一阶段测试计划任务。
