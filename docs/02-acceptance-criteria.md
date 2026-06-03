# 验收标准

最后更新：2026-06-03  
状态：MVP 边界已确认，验收标准聚焦数据结构课程学生端闭环。

## 总体验收原则

- 未经实际运行、测试或人工核验的功能不得标记为 Done。
- 验收优先依据可运行系统、测试结果、演示脚本和项目文档，而不是主观判断。
- 所有第三方代码和依赖必须可追溯来源、用途和 license。

## Implementation Boundary Check / 实现边界检查

- API handler / frontend 不应承载核心业务逻辑。
- Business logic 应通过 service / orchestrator 组织。
- External dependency、mock provider、demo provider 应通过 adapter / provider contract 接入。
- Demo / mock / rule-based 数据或逻辑应集中管理，避免散落 hardcoded response。
- 后续替换真实 LLM / RAG / VectorStore 时，应尽量保持 API request / response schema 稳定。

## MVP 验收标准

| 编号 | 对应需求 | 验收标准 | 当前状态 |
|---|---|---|---|
| AC1 | R1 | 用户能上传至少一种课程资料文件；系统能解析、切分并建立可查询知识库；失败时有明确错误提示 | Not Started |
| AC2 | R2 | 用户能创建、选择或编辑模拟学生画像；第一阶段至少提供基础薄弱型、考试冲刺型、算法实践型 3 个样例，且画像至少包含学习目标、基础水平、学习偏好和可用时间 | Not Started |
| AC3 | R3 | 系统能维护数据结构课程的章节、知识点和先修关系；至少支持一个完整演示知识点链路 | Not Started |
| AC4 | R4 | `Planner Agent` 能基于模拟学生画像和数据结构课程知识生成阶段化学习路径，并说明路径依据 | Not Started |
| AC5 | R5 | `Resource Agent` 能针对某个知识点生成学习资源，且资源能关联到学习路径节点 | Not Started |
| AC6 | R6 | `Tutor Agent` 能基于数据结构课程知识库上下文回答问题；回答中应包含资料依据或引用线索 | Not Started |
| AC7 | R7 | `Quiz Agent` 能生成数据结构题目、答案和解析；题目应绑定知识点和难度 | Not Started |
| AC8 | R8 | `Evaluator Agent` 能根据一次作答记录更新掌握度，并给出下一步建议 | Not Started |
| AC9 | R9 | 系统能记录一次完整 Agent run 的输入摘要、输出摘要、调用顺序、状态和关键决策依据 | Not Started |
| AC10 | R10 | 学生端界面能完成画像选择、学习路径查看、资源查看、问答、测验和 Agent 流程记录查看 | Not Started |
| AC11 | R11 | 后端提供清晰 API，数据库可迁移，长任务不阻塞请求，LLM 配置可替换 | Not Started |
| AC12 | R12 | 文档中列出使用的第三方依赖、license、用途和风险边界 | Partial |
| AC13 | R13 | 关键外部能力必须通过 adapter 封装；业务服务不得直接依赖具体 LLM SDK、向量库 SDK 或任务队列细节 | Partial |
| AC14 | R14 | 第一阶段验收不要求教师端、管理端、真实学生数据或 A6 校园事务流程；若出现相关入口，应标注为后续版本或演示占位 | Not Started |
| AC15 | R15 | 需求文档应记录架构影响分析，但不得要求 Requirement Agent 直接修改架构文档或 ADR | Confirmed |
| AC16 | R1-R13 | Demo data 必须集中隔离在 seed、fixture 或 demo data service 中，不得散落在 API handler、frontend、Agent prompt 或业务分支中 | Active |
| AC17 | R11, R13 | Mock provider 必须实现正式 adapter 契约；service / orchestrator 不得直接依赖具体 mock 类 | Active |
| AC18 | R4-R9, R13 | Rule-based `Planner` / `Tutor` / `Quiz` / `Evaluator` logic 必须隔离在 Agent、strategy 或 service 边界内，返回标准 domain result，不得写在 API handler 或 frontend | Active |
| AC19 | R11, R13 | 后续替换真实 LLM / RAG / VectorStore 时，不得破坏 `/api/v1` schema、service contract、adapter contract 和 `agent_runs` / `agent_run_steps` 记录结构 | Active |
| AC20 | R1-R13 | 每个后续 IMPL-* Review 必须包含 `Implementation Boundary Review` 结论，并能判定 `Pass`、`Needs Fix` 或 `Blocking` | Active |

## MVP Implementation Boundary Standard

本标准从 `IMPL-005` 起作为所有 IMPL-* 任务的常规 Review 检查项，并建议对 `IMPL-002` 到 `IMPL-004` 做一次边界补审。它不修改已 Accepted 的架构基线，不新增 ADR，不引入新技术栈。

### Demo Data 隔离

- Demo data 必须集中在 seed、fixture 或 `DemoDataService` 等明确边界内。
- Demo data 可以包含数据结构课程、5 个 MVP 知识点、3 个模拟学生画像、模拟资料 chunk。
- Demo data 不得散落在 API handler、frontend component、Agent prompt 或 service 的临时分支中。
- Demo data 必须通过明确入口加载，例如 `POST /api/v1/demo-data/load` 或 seed script。
- Demo data 加载应尽量幂等，不应依赖“全新空数据库”才能正常运行。

### Mock Provider 隔离

- Mock LLM、mock VectorStore、mock TaskQueue、mock DocumentParser 必须实现正式 adapter / protocol 契约。
- Service 和 orchestrator 只能依赖 `LLMProvider`、`VectorStore`、`TaskQueue`、`DocumentParser` 抽象。
- Mock provider 不得通过分散的 `if demo_mode` 分支嵌入业务 service。
- 替换真实 provider 时，不应修改 API schema、domain service 公共契约和 Agent run 记录结构。

### Rule-based Logic 隔离

- Rule-based `Planner` / `Tutor` / `Quiz` / `Evaluator` 允许用于 MVP，但必须放在 Agent implementation、strategy 或 service 边界内。
- `AgentOrchestrator` 负责编排调用顺序和记录 run / step，不应堆积大量具体生成规则。
- Rule-based 输出必须使用与未来 LLM 输出一致的 domain result，例如 `LearningPathResult`、`TutorAnswer`、`QuizResult`、`EvaluationResult`。
- Rule-based 逻辑必须使用数据库中的 profile、concept、relation、chunk，不得只按固定字符串返回固定结果。

### API Handler 和 Frontend 禁止事项

- API handler 不得直接写 demo data、调用 mock provider、调用具体 LLM / VectorStore SDK、拼学习路径、生成 Quiz 或计算掌握度。
- API handler 只负责 request / response、依赖注入、错误转换和调用 service。
- Frontend 不得硬编码 3 个画像、5 个知识点、学习路径、Quiz 答案或 Agent steps。
- Frontend 不得模拟 `Planner` / `Tutor` / `Quiz` / `Evaluator` 结果；核心数据必须来自 API。

### Allowed / Not Allowed

| 允许的实现方式 | 不允许的实现方式 | 原因 |
|---|---|---|
| Demo data 集中在 seed 文件和 `DemoDataService` | API handler 里写死 demo profiles / concepts | Handler 会变成不可复用 demo script |
| Mock LLM 实现 `LLMProvider` 契约 | Service 直接调用 `MockLLMProvider` 具体类 | 后续替换真实 LLM 会改业务层 |
| Rule-based Planner 返回标准 `LearningPath` 结构 | Planner 直接返回前端展示用固定 JSON | 会绑定 UI，破坏 domain contract |
| Tutor 基于 `KnowledgeBaseService.search()` 的 chunk 生成回答 | Tutor 根据问题关键词直接返回硬编码答案 | 无法替换真实 RAG |
| Quiz 基于 `concept_id`、`difficulty` 生成题目 | Frontend 或 handler 按知识点名称拼题目 | 逻辑位置错误，后续不可测试 |
| Evaluator 通过 `AssessmentService` 更新 mastery | API handler 直接修改 mastery score | 绕过领域规则和测试边界 |
| Agent steps 由 `AgentRunService` 统一记录 | 每个 Agent 自己随意写日志字段 | Review 无法稳定检查 AC9 |
| Demo SQLite 明确为 dev/demo 配置 | 把 SQLite 当成正式数据库方向 | ADR 已明确业务数据库方向为 `PostgreSQL` |
| Frontend 从 API 获取 demo data | Frontend 本地维护一份 demo data | 前后端状态会漂移 |
| 使用配置或依赖注入切换 mock / real provider | 用分散的 `if DEMO_MODE` 分支切换 | 分支污染业务代码 |

## 数据结构 MVP 场景验收

Given 学生选择数据结构课程并选择一个模拟学生画像  
When 学生输入学习目标，例如“我想复习树和二叉树，准备小测”  
Then 系统应启动一次可追踪的 `Multi-Agent` 学习流程。

Given 系统加载 MVP 演示数据  
When 学生选择模拟画像  
Then 系统应提供基础薄弱型、考试冲刺型、算法实践型 3 个可选画像。

Given 系统加载 MVP 演示课程数据  
When 评委查看可选知识点  
Then 系统应至少包含复杂度分析、链表、栈/队列、二叉树遍历、BFS/DFS。

Given `Planner Agent` 已收到学生画像和课程知识点关系  
When 它生成学习路径  
Then 输出应包含阶段化步骤、关联知识点、推荐学习顺序和依据说明。

Given `Resource Agent` 接收到学习路径中的某个数据结构知识点  
When 它生成学习资源  
Then 输出应包含面向该学生水平的讲解、例题或练习，并能关联到路径节点。

Given `Quiz Agent` 接收到目标知识点和学生水平  
When 它生成测验  
Then 题目应覆盖该知识点，包含答案、解析、难度和知识点标签。

Given `Evaluator Agent` 接收到学生作答  
When 它完成评价  
Then 系统应展示掌握度变化、错误原因、薄弱知识点和下一步建议。

Given 评委查看演示页面  
When 一次学习闭环完成  
Then 页面或日志应能展示至少 4 个 Agent 的调用顺序、输入摘要、输出摘要和最终整合结果。

And 页面不要求展示每个 Agent 的完整输入输出。

Given Architect Agent 阅读需求文档  
When 评估后续架构任务  
Then 应能看到需求侧架构影响分析，但不应将其视为已修改的架构基线。

## 当前不可验收项

截至 2026-06-03，仓库已有后端基础结构和部分测试，但完整 MVP 产品功能仍不能标记为 Done。`IMPL-001` 到 `IMPL-004` 的阶段性通过仅代表对应任务范围内的能力通过，不代表完整 AC1-AC13 或完整学生端闭环已完成。
