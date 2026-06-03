# 中国软件杯 A3 参赛项目

本仓库是“中国软件杯”A3 赛题的主项目仓库，用于维护参赛作品的代码、文档、测试脚本、部署说明和项目状态。

赛题方向：

> A3 - 基于大模型的个性化资源生成与学习多智能体系统开发

## 当前定位

当前仓库已经不是单纯的调研资料库，而是一个可运行的 MVP 工程仓库。  
截至目前，项目已经完成：

- 后端最小学习闭环
- 前端学生端关键交互
- 基础自动化验证
- 本地部署与演示运行配置

但它还不是完整产品，也不是生产级系统。真实 `LLM`、真实 `RAG`、正式 `PostgreSQL`、任务队列、生产部署和完整测试矩阵仍未完成。

## 当前已实现功能

### 后端能力

当前后端基于 `FastAPI + Pydantic + SQLAlchemy`，已经实现：

- demo data 加载与状态检查
- 学生画像列表、详情、创建
- 课程知识点图查询
- 学习路径生成
- `Planner Agent` 最小流程
- 学习资源生成
- Tutor 问答
- Quiz 生成
- Evaluator 评分与反馈
- `agent_runs` / `agent_run_steps` 摘要记录

当前已提供的主要 API 包括：

- `POST /api/v1/demo-data/load`
- `GET /api/v1/demo-data/status`
- `GET /api/v1/student-profiles`
- `POST /api/v1/student-profiles`
- `GET /api/v1/student-profiles/{profile_id}`
- `GET /api/v1/courses/{course_id}/graph`
- `POST /api/v1/learning-paths`
- `GET /api/v1/learning-paths/{path_id}`
- `POST /api/v1/resources/generate`
- `POST /api/v1/tutor/ask`
- `POST /api/v1/quizzes/generate`
- `POST /api/v1/quizzes/{quiz_id}/attempts`
- `GET /api/v1/agent-runs/{run_id}`

### 前端能力

当前前端基于 `React + Vite + TypeScript + Tailwind CSS`，已经实现学生端 MVP 关键交互：

- 刷新 demo data
- 选择学生画像
- 查看课程知识点
- 生成学习路径
- 选择当前学习节点
- 生成学习资源
- 发起 Tutor 问答
- 生成测验并提交答案
- 查看评分、反馈和掌握度建议
- 查看 Agent run 摘要

### 自动化验证

当前仓库已经提供基础验证入口：

- `./scripts/verify.ps1`
  - Python compile check
  - backend unit tests
  - `pip check`
  - backend wheel build
  - frontend build
  - Playwright browser smoke

- `./scripts/frontend-smoke.ps1`
  - 启动临时 backend/frontend
  - 通过真实页面执行学生端闭环 smoke

### 本地部署与演示运行

当前已经补齐本地演示所需配置：

- [deployment/README.md](E:/study/obsidian/软件杯/software-cup-a3-project/deployment/README.md)
- [deployment/local.env.example](E:/study/obsidian/软件杯/software-cup-a3-project/deployment/local.env.example)
- [scripts/run-local.ps1](E:/study/obsidian/软件杯/software-cup-a3-project/scripts/run-local.ps1)

它们支持：

- 本地 backend/frontend 启动
- 自动加载 demo data
- 自定义端口运行
- `-SmokeOnly` 启动链路验证

## 本地部署与运行

详细说明见 [deployment/README.md](E:/study/obsidian/软件杯/software-cup-a3-project/deployment/README.md)。

### 依赖要求

- Python 3.11+
- Node.js 20.19+ 或 22.12+
- npm
- Windows PowerShell

### 安装依赖

在仓库根目录执行：

```powershell
python -m pip install -e .
cd src/frontend
npm ci
cd ../..
```

如果当前 Python 环境没有 `uvicorn`，需要额外安装可运行的 ASGI server。

### 启动本地演示

```powershell
./scripts/run-local.ps1
```

脚本会：

- 启动 backend
- 启动 frontend
- 加载 demo data
- 输出本地访问地址

### 只做启动链路验证

```powershell
./scripts/run-local.ps1 -SmokeOnly
```

### 执行完整基础验证

```powershell
./scripts/verify.ps1
```

## 当前项目状态

截至目前，`IMPL-001` 到 `IMPL-009` 已全部通过 `Review & Test Agent` 验收，但都只在各自任务范围内成立。

当前状态可以概括为：

- 已完成可演示的 student-side MVP 闭环
- 已完成基础自动化验证
- 已完成本地部署与演示运行配置
- 未完成生产级能力和真实智能化能力

### 已完成的阶段任务

- `IMPL-001` 后端基础结构、数据模型、API schema 骨架
- `IMPL-002` demo data 加载能力
- `IMPL-003` 学生画像与课程知识点 API
- `IMPL-004` 学习路径与 `Planner Agent` 最小流程
- `IMPL-005` Resource / Tutor / Quiz / Evaluator 最小闭环
- `IMPL-006` 前端学生端工程初始化
- `IMPL-007` 学生端 MVP 页面关键交互
- `IMPL-008` 自动化测试与基础验证脚本
- `IMPL-009` 本地部署与演示运行配置

### 当前仍是 Partial 的方向

- 真实课程资料上传、解析、切分
- 真实 `RAG` / `VectorStore`
- 真实 `LLMProvider`
- 正式 `PostgreSQL`
- 任务队列（如 `Redis/RQ`）
- 统一 learning-flow trace 聚合
- 失败路径和多环境自动化测试
- 生产级部署

更完整的状态说明见：

- [docs/06-project-state.md](E:/study/obsidian/软件杯/software-cup-a3-project/docs/06-project-state.md)
- [reviews/review-log.md](E:/study/obsidian/软件杯/software-cup-a3-project/reviews/review-log.md)

## 当前技术路线

当前实际落地和中长期方向如下：

- 前端：`React + Vite + TypeScript + Tailwind CSS`
- 后端：`FastAPI + Pydantic + SQLAlchemy`
- 当前演示数据库：`SQLite`
- 架构目标数据库：`PostgreSQL`
- 当前 Agent 编排：轻量 `AgentOrchestrator`
- 当前智能能力：集中管理的 rule-based demo logic
- 中长期 `LLM` 接入：统一 `LLMProvider` adapter
- 中长期检索：真实 `RAG` + `VectorStore`
- 中长期异步任务：`Redis + RQ` 或等价队列

## 后续工作计划

下面是当前的大方向计划，不是细粒度任务列表。

### 1. 真实 LLM 接入

目标：

- 用真实 `LLMProvider` 替换当前 rule-based 资源生成、Tutor、Quiz、Evaluator 逻辑
- 保持现有 `/api/v1` request / response schema 尽量稳定
- 保持 service / adapter / provider 边界不变

### 2. 真实 RAG 能力

目标：

- 支持真实课程资料上传、解析、chunking
- 建立真实知识库检索链路
- 接入真实 `VectorStore`
- 让 Tutor 回答和资源生成从 demo chunk 检索过渡到真实检索

### 3. 数据与基础设施升级

目标：

- 从 demo `SQLite` 过渡到正式 `PostgreSQL`
- 增加数据库迁移机制
- 引入 `Redis/RQ` 或等价队列，承载异步任务
- 完善运行配置与环境变量管理

### 4. 自动化测试增强

目标：

- 补失败路径自动化测试
- 补多浏览器 / 移动视口测试
- 将本地 smoke 和前端 E2E 进一步稳定化
- 减少环境依赖差异带来的验证不一致

### 5. 部署与演示能力完善

目标：

- 增加更完整的部署脚本
- 补生产级或准生产级运行说明
- 补比赛演示脚本和演示材料

## 相关文档

- [项目简介](docs/00-project-brief.md)
- [需求说明](docs/01-requirements.md)
- [验收标准](docs/02-acceptance-criteria.md)
- [架构设计](docs/03-architecture.md)
- [项目状态](docs/06-project-state.md)
- [Review 日志](reviews/review-log.md)
- [开源调研](docs/research/a3-open-source-research.md)
- [开源合规说明](docs/compliance/open-source-compliance.md)
- [本地部署说明](deployment/README.md)

## 合规原则

本项目可以参考多个开源项目的架构、技术栈和模块划分，但参赛作品主体应由团队在本届比赛期间自主设计与实现。第三方依赖、开源协议和参考来源将在文档中持续记录。
