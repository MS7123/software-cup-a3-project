# ADR 0001: A3 参赛项目架构基线

日期：2026-06-03

## 状态

Accepted

## 背景

本项目面向中国软件杯 A3 赛题，需要在有限比赛周期内完成一个体现 `Multi-Agent`、`Personalization`、`Knowledge Grounding` 和学习资源生成闭环的工程化作品。

已有调研文档建议参考多个开源项目的产品形态、模块边界和技术路线，但合规文档明确要求参赛主体必须自主设计与实现，不能直接复制高风险开源项目代码。

## 决策

采用以下架构基线：

- 前端：`React + Vite + TypeScript + Tailwind CSS`
- 后端：`FastAPI + Pydantic + SQLAlchemy`
- 数据库：`PostgreSQL`
- 向量库：第一阶段 `Chroma`，通过 adapter 隔离
- 异步任务：第一阶段 `Redis + RQ`
- Agent 编排：第一阶段轻量自研 `AgentOrchestrator`
- LLM 接入：统一封装 OpenAI-compatible API

架构按以下模块边界推进：

- `Frontend`
- `API Layer`
- `Domain Services`
- `Agent Orchestration`
- `Infrastructure Adapters`
- `Persistence`
- `Background Worker`

## 理由

- 该组合与现有调研结论一致，学习成本和工程完整性平衡较好。
- Python 后端更适合文档解析、RAG、Agent 编排和学习评价模型。
- `FastAPI + Pydantic` 能清晰表达接口契约，便于多 Agent 协作开发。
- `PostgreSQL` 统一保存业务数据、学习记录、任务状态和 Agent 日志。
- 第一阶段使用 `Chroma` 能降低向量检索落地难度。
- 自研轻量 `AgentOrchestrator` 能避免过早绑定复杂框架，保留后续升级空间。

## 替代方案

### 使用 `Next.js` 全栈

暂不采用。原因是 AI pipeline 和数据处理主要在 Python 生态内更直接，且全栈框架可能模糊前后端与服务边界。

### 使用 `Streamlit`

不作为最终主架构。它适合快速原型，但不利于展示完整工程架构、任务队列、权限预留和复杂交互。

### 直接引入 `LangGraph`

暂缓。当前 MVP 的 Agent 状态流转还可以用轻量 orchestrator 控制；如果后续出现复杂状态图、多轮工具调用和回退路径，再新增 ADR 评估引入。

### 第一阶段使用 `Neo4j + OpenSearch`

暂不采用。该方案技术深度更高，但部署和维护成本超出当前阶段需要。知识点关系先用 `PostgreSQL` 表表达。

## 影响

- Implementation Agent 必须按 adapter 方式封装 LLM、向量库和任务队列。
- 业务模块不得直接依赖具体 LLM SDK、`Chroma` SDK 或 Redis/RQ 细节。
- 新增技术栈、替换向量库、引入 `LangGraph`、引入图数据库必须新增 ADR。
- 第一阶段验收以完整学习闭环为优先，而不是功能数量。

## 禁止事项

- 不复制 `AGPL-3.0`、`GPL-3.0` 或无 license 项目的核心代码进入参赛主体。
- 不让前端直接访问数据库、向量库、Redis 或 LLM API。
- 不在 API handler 中直接写复杂业务逻辑。
- 不把 Agent prompt 当作唯一状态来源；关键状态必须落库。
