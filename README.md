# 中国软件杯 A3 参赛项目

本仓库用于存放“中国软件杯”A3 赛题参赛作品的完整代码、文档、调研材料和部署资料。

赛题方向：

> A3 - 基于大模型的个性化资源生成与学习多智能体系统开发

## 仓库定位

本仓库不是单纯的调研资料库，而是后续参赛项目的主仓库。当前阶段已完成开源项目技术调研，后续将在此基础上继续补充系统设计、前后端代码、Agent 编排、数据库设计、测试脚本、部署配置和参赛文档。

## 目录结构

```text
.
├── src/
│   ├── backend/          # 后端服务代码
│   └── frontend/         # 前端应用代码
├── docs/
│   ├── research/         # 开源项目调研与技术路线分析
│   ├── design/           # 系统设计、架构设计、数据库设计
│   ├── competition/      # 参赛说明、演示脚本、提交材料
│   └── compliance/       # 开源协议与第三方依赖合规说明
├── data/
│   └── samples/          # 演示数据、课程资料样例
├── deployment/           # Docker、部署脚本和环境配置
└── scripts/              # 开发、测试、数据处理辅助脚本
```

## 已完成内容

- [A3 开源项目技术调研与技术路线建议](docs/research/a3-open-source-research.md)
- [第三方开源项目使用边界](docs/compliance/open-source-compliance.md)

## 初步技术路线

暂定方向：

- 前端：`React + Vite + TypeScript + Tailwind CSS`
- 后端：`FastAPI + Pydantic + SQLAlchemy`
- 数据库：`PostgreSQL`
- 向量库：第一阶段使用 `Chroma`，后续可切换 `pgvector`
- 异步任务：`Redis + RQ` 或 `Celery`
- Agent 编排：轻量自研 `AgentOrchestrator`，必要时引入 `LangGraph`
- LLM 接入：统一封装 OpenAI-compatible API

## 合规原则

本项目可以参考多个开源项目的架构、技术栈和模块划分，但参赛作品主体应由团队在本届比赛期间自主设计与实现。第三方依赖、开源协议和参考来源将在文档中持续记录。

