# 需求说明

最后更新：2026-06-03  
状态：MVP 边界已确认，需求优先级按数据结构课程学生端闭环整理。

## 项目方向

项目面向中国软件杯 A3 赛题：

> 基于大模型的个性化资源生成与学习多智能体系统开发

当前建议产品方向为：

> 面向大学课程学习的个性化资源生成与学习多智能体系统。

系统应围绕学生画像、课程知识库、知识图谱、学习路径规划、资源生成、测验评价和学习反馈形成闭环，避免停留在“AI 聊天 + 上传 PDF”的普通知识库形态。

## 已确认 MVP 决策

- 参赛方向：A3。
- MVP 演示课程：数据结构。
- MVP 知识点范围：复杂度分析、链表、栈/队列、二叉树遍历、BFS/DFS。
- 第一阶段用户范围：学生端。
- 数据范围：模拟学生画像、模拟课程资料、模拟测验记录。
- 学生画像样例：第一阶段控制在 3 个，分别为基础薄弱型、考试冲刺型、算法实践型；后续版本再增加。
- 展示重点：`Multi-Agent` 协作流程优先于完整教学管理功能。
- 展示粒度：展示 Agent 摘要，不要求暴露每个 Agent 的完整输入输出。
- 架构边界：Requirement Agent 不调整已 Accepted 的架构基线，只提供需求侧架构影响分析。

## 核心需求

| 编号 | 需求 | 当前优先级 | 状态 | 依据 |
|---|---|---|---|---|
| R1 | 支持数据结构课程资料的模拟数据导入、解析样例、切分样例和知识库构建，知识点范围限定为复杂度分析、链表、栈/队列、二叉树遍历、BFS/DFS | 高 | Not Started | 用户确认 MVP 使用数据结构和模拟课程资料 |
| R2 | 支持学生填写或选择学习目标、基础水平、学习风格和时间约束，形成模拟学生画像；第一阶段提供基础薄弱型、考试冲刺型、算法实践型 3 个样例 | 高 | Not Started | 用户确认第一阶段只做学生端闭环和模拟画像 |
| R3 | 支持复杂度分析、链表、栈/队列、二叉树遍历、BFS/DFS 的知识点、章节、先修关系和相关关系建模 | 高 | Not Started | 用户确认 MVP 演示课程为数据结构 |
| R4 | `Planner Agent` 根据学生画像、知识库和知识点关系生成阶段化学习路径 | 高 | Not Started | 用户确认展示优先突出 Multi-Agent 协作流程 |
| R5 | `Resource Agent` 生成讲义、例题、总结、练习或复习资源 | 高 | Not Started | `docs/research/a3-open-source-research.md` |
| R6 | `Tutor Agent` 基于数据结构课程资料上下文回答学生问题，并尽量给出引用或依据 | 高 | Not Started | 用户确认 MVP 演示课程为数据结构 |
| R7 | `Quiz Agent` 生成数据结构小测题目、答案和解析 | 高 | Not Started | 用户确认学生端学习闭环 |
| R8 | `Evaluator Agent` 根据学生作答更新掌握度，并给出补救建议 | 高 | Not Started | 用户确认学生端学习闭环 |
| R9 | 记录 Agent 执行过程、输入摘要、输出摘要、调用顺序和关键决策，用于演示可解释性 | 高 | Not Started | 用户确认比赛展示优先突出 Multi-Agent 协作流程，且展示摘要即可 |
| R10 | 提供学生端界面展示学习路径、资源、问答、测验、掌握度和 Agent 流程记录 | 高 | Not Started | 用户确认第一阶段只做学生端闭环 |
| R11 | 提供后端 API、数据库、向量检索、任务队列和 LLM 接入封装 | 中 | Not Started | `README.md` |
| R12 | 保持开源合规，不复制高风险或无 license 项目的核心代码 | 高 | Partial | `docs/compliance/open-source-compliance.md` |
| R13 | 按已接受架构基线推进：前后端分离、adapter 隔离 LLM / VectorStore / TaskQueue | 高 | Partial | `docs/architecture/03-architecture.md`, `docs/architecture/0001-architecture-baseline.md` |
| R14 | 第一阶段排除教师端、管理端、真实学生数据和 A6 校园事务流程 | 高 | Confirmed | 用户确认第一阶段只做学生端闭环 |
| R15 | 在需求文档中记录需求侧架构影响，但不修改已 Accepted 的架构基线 | 高 | Confirmed | 用户确认 Requirement Agent 不能调整架构基线 |

## 技术路线约束

- 前端暂定：`React + Vite + TypeScript + Tailwind CSS`
- 后端暂定：`FastAPI + Pydantic + SQLAlchemy`
- 数据库暂定：`PostgreSQL`
- 向量库第一阶段暂定：`Chroma`，后续可切换 `pgvector`
- 异步任务暂定：`Redis + RQ` 或 `Celery`
- Agent 编排暂定：轻量自研 `AgentOrchestrator`，必要时引入 `LangGraph`
- LLM 接入暂定：统一封装 OpenAI-compatible API

## 待用户裁决

当前暂无已知需求裁决项阻塞 Architect Agent。架构基线不得由 Requirement Agent 修改。

## 需求侧架构影响分析

> 本节不是架构变更，也不修改 `docs/architecture/03-architecture.md` 或 ADR。它只说明需求对后续 Architect Agent 的影响。

- 知识点范围已收敛到 5 类，课程知识模型第一阶段不需要覆盖完整数据结构课程，但应保留后续扩展到排序、查找、图论进阶等知识点的空间。
- 因为展示重点是 `Multi-Agent` 协作摘要，Agent run 记录至少需要支持：Agent 名称、调用顺序、输入摘要、输出摘要、状态、关键决策依据和最终整合结果。
- 因为不展示完整输入输出，日志模型应避免把完整 prompt、完整学生输入或长篇生成内容作为唯一展示依据；摘要字段应可独立读取。
- 因为使用模拟课程资料和模拟学生画像，第一阶段数据层需要支持 seed data 或固定样例数据，但不得把模拟数据设计成只能一次性硬编码演示。
- 因为只做学生端闭环，权限和管理端能力可降级为后续扩展点；第一阶段不应因教师端、班级管理或真实数据接入增加实现范围。
