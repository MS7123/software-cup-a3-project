# Project Documentation Index

最后更新：2026-06-17

本文档是 `docs/` 的阅读入口。当前文档按用途分层，避免所有计划、状态、架构和比赛资料混在顶层。

## 1. 推荐阅读顺序

| 顺序 | 文档 | 用途 |
|---:|---|---|
| 1 | [项目简介](project/00-project-brief.md) | 理解项目方向、A3 赛题定位和 MVP 主线 |
| 2 | [需求说明](project/01-requirements.md) | 理解功能需求和边界 |
| 3 | [验收标准](project/02-acceptance-criteria.md) | 理解什么算可验收，尤其是 implementation boundary |
| 4 | [架构设计](architecture/03-architecture.md) | 理解 FastAPI / React / service / adapter / agent trace 架构 |
| 5 | [开发路线](process/04-development-roadmap.md) | 理解轻量个人敏捷模式和阶段划分 |
| 6 | [当前项目状态](project/06-project-state.md) | 理解历史状态、已知问题和待办 |
| 7 | [敏捷开发记录](process/05-agile-development-log.md) | 查看最近每轮增量、验证和风险 |

## 2. 目录结构

```text
docs/
├─ README.md
├─ project/          项目定义、需求、验收、状态
├─ architecture/     架构设计和架构决策
├─ process/          开发路线和敏捷开发记录
├─ plans/            阶段计划和后续增量计划
│  ├─ rag/           RAG 专项计划
│  ├─ demo/          演示体验和短期增量计划
│  └─ competition/   赛题要求差距和比赛交付计划
├─ runbooks/         手动验证和演示操作手册
├─ competition/      比赛对齐材料
├─ compliance/       开源合规材料
└─ research/         调研和赛题讨论材料
```

## 3. Project

| 文档 | 说明 |
|---|---|
| [00-project-brief.md](project/00-project-brief.md) | 项目简介，明确 A3 方向和 MVP 主线 |
| [01-requirements.md](project/01-requirements.md) | 需求说明 |
| [02-acceptance-criteria.md](project/02-acceptance-criteria.md) | 验收标准和边界检查 |
| [06-project-state.md](project/06-project-state.md) | 当前状态、已知问题和历史任务记录 |

## 4. Architecture

| 文档 | 说明 |
|---|---|
| [03-architecture.md](architecture/03-architecture.md) | 系统架构、模块边界、API/service/adapter 分层 |
| [0001-architecture-baseline.md](architecture/0001-architecture-baseline.md) | 架构基线 ADR |

## 5. Process

| 文档 | 说明 |
|---|---|
| [04-development-roadmap.md](process/04-development-roadmap.md) | 个人敏捷开发原则、阶段划分、Builder / Reviewer 边界 |
| [05-agile-development-log.md](process/05-agile-development-log.md) | 每轮可演示增量、测试和风险记录 |

## 6. Plans

### RAG Plans

| 文档 | 阶段 | 说明 |
|---|---|---|
| [07-rag-implementation-plan.md](plans/rag/07-rag-implementation-plan.md) | Phase 1 | 真实 RAG 最小实现规划 |
| [09-rag-retrieval-coverage-plan.md](plans/rag/09-rag-retrieval-coverage-plan.md) | Retrieval coverage | BFS/DFS 等检索覆盖优化 |
| [11-sqlite-vector-retrieval-plan.md](plans/rag/11-sqlite-vector-retrieval-plan.md) | Phase 2 | SQLite + Python cosine hybrid retrieval |
| [12-rag-phase-roadmap.md](plans/rag/12-rag-phase-roadmap.md) | Overall | RAG Phase 1-5 总路线 |
| [13-rag-reranking-plan.md](plans/rag/13-rag-reranking-plan.md) | Phase 3 | Rule-based reranking |
| [14-rag-citation-quality-plan.md](plans/rag/14-rag-citation-quality-plan.md) | Phase 4 | Citation quality 和 source panel |
| [15-rag-knowledge-management-plan.md](plans/rag/15-rag-knowledge-management-plan.md) | Phase 5 | Knowledge management、upload、scope、reindex |

### Demo Plans

| 文档 | 说明 |
|---|---|
| [08-next-demo-increments-plan.md](plans/demo/08-next-demo-increments-plan.md) | 后续短期演示增量计划 |
| [10-demo-ux-and-agent-tuning-plan.md](plans/demo/10-demo-ux-and-agent-tuning-plan.md) | Demo UX、Markdown、Agent loading 和 Tutor tuning |

### Competition Plans

| 文档 | 说明 |
|---|---|
| [16-a3-requirements-gap-roadmap.md](plans/competition/16-a3-requirements-gap-roadmap.md) | 针对新版官网要求的未完成项、优先级、预期效果和验收标准 |

## 7. Runbooks

| 文档 | 说明 |
|---|---|
| [rag-demo-runbook.md](runbooks/rag-demo-runbook.md) | RAG demo 操作手册 |
| [llm-rag-tutor-manual-verification.md](runbooks/llm-rag-tutor-manual-verification.md) | LLM + RAG Tutor 手动验证方案 |

## 8. Competition / Compliance / Research

| 目录 | 文档 | 说明 |
|---|---|---|
| `competition/` | [a3-official-requirements.md](competition/a3-official-requirements.md) | 官方赛题要求整理、检查表和项目对应关系 |
| `competition/` | [a3-official-requirements-original.md](competition/a3-official-requirements-original.md) | 官网赛题要求原版复制 |
| `competition/` | [competition-fit.md](competition/competition-fit.md) | A3 比赛目标对齐与开发主线冻结 |
| `compliance/` | [open-source-compliance.md](compliance/open-source-compliance.md) | 开源合规说明 |
| `research/` | [a3-open-source-research.md](research/a3-open-source-research.md) | A3 开源调研 |
| `research/` | [a6-project-discussion-summary.md](research/a6-project-discussion-summary.md) | A6 赛题讨论总结，非当前主线 |

## 9. 维护规则

- 顶层只保留 `README.md` 作为入口。
- 新的 RAG 阶段计划放入 `docs/plans/rag/`。
- 新的演示体验或短期增量计划放入 `docs/plans/demo/`。
- 新的赛题差距和比赛交付计划放入 `docs/plans/competition/`。
- 手动测试、演示脚本、运行手册放入 `docs/runbooks/`。
- 项目状态和开发记录分别维护在 `project/06-project-state.md` 和 `process/05-agile-development-log.md`。
- 不恢复旧的 Requirement -> Architect -> Implementation -> Review -> State 重流程。
