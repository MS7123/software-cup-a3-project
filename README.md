# 中国软件杯 A3 参赛项目

本仓库是“中国软件杯”A3 赛题的主项目仓库。

赛题方向：

> A3 - 基于大模型的个性化资源生成与学习多智能体系统开发

项目目标是围绕数据结构课程构建一个可演示的个性化学习闭环：

```text
学生画像 -> 学习路径 -> 资源生成 -> Tutor -> Quiz -> Evaluator -> Agent trace -> 动态画像更新
```

当前仓库已经从调研资料库推进为可运行 MVP 工程。它适合本地演示、阶段评审和后续比赛材料制作，但仍不是生产级系统。

## 当前工作进度

当前分支处于个人敏捷开发模式下的 Phase 2 / Phase 3 交界：

- Phase 2：补齐核心智能能力，尤其是真实 LLM opt-in、画像构建、资源生成、评价反馈。
- Phase 3：优化演示体验，让评委能直观看到 Multi-Agent 协作、个性化和 Agent trace。

截至 2026-06-13，当前分支已具备以下可演示能力。

### 已完成的主流程能力

- demo data 加载、状态检查和一键重置。
- 3 个默认学生画像：基础薄弱型、考试冲刺型、算法实践型。
- 自然语言生成学生画像，并补齐 6 个画像维度：
  - `learning_goal`
  - `foundation_level`
  - `learning_preference`
  - `available_time`
  - `weak_points`
  - `resource_preference`
- 用户画像删除和关联学习数据清理。
- 数据结构课程知识点图：
  - 复杂度分析
  - 链表
  - 栈 / 队列
  - 二叉树遍历
  - BFS / DFS
- 学习路径生成。
- 5 类个性化学习资源生成：
  - `guided_note`：讲解文档
  - `practice_questions`：练习题
  - `mind_map`：思维导图
  - `extended_reading`：拓展阅读
  - `coding_case`：代码实操案例
- Tutor 问答。
- Quiz 生成与作答。
- Evaluator 评分、反馈、薄弱点和下一步建议。
- Quiz 作答后自动从 Agent trace 更新学生画像。
- Agent trace 时间线展示：
  - Input
  - Output
  - Decision
  - fallback 标记
- 资源卡片展示增强：
  - 练习题列表
  - 代码块展示
  - SVG 思维导图
  - 完整资源正文折叠区
  - grounded source 展示
- 真实 RAG 第一阶段闭环：
  - 前端 `Knowledge setup` 可粘贴 `text` / `markdown` 课程资料。
  - 后端创建 `documents` / `document_chunks`。
  - `KnowledgeBaseService.search()` 基于真实导入 chunk 做 keyword retrieval。
  - Tutor / Resource response 保留真实 `source_refs`。
  - Agent trace 可展示具体 `document:{id}#chunk:{index}` 来源。
- RAG keyword retrieval 小优化：
  - search metadata 包含 `matched_terms`。
  - search metadata 包含 `term_match_count`。
  - stack / queue、BFS / DFS 演示资料可用于手动检索验证。

### 已完成的 LLM 接入范围

当前真实 LLM 能力是显式 opt-in，不会影响默认离线演示。

已通过 `LLMProvider` adapter 接入或预留的 Agent：

- Tutor Agent：OpenAI-compatible LLM，可 fallback 到 rule-based。
- ProfileUpdater：可选 LLM 分析 Agent trace，失败时 fallback。
- Resource Agent：可选 LLM 生成 5 类学习资源，失败时 fallback。
- Evaluator Agent：可选 LLM 输出 JSON 评分、反馈、薄弱点和下一步建议，失败时 fallback。
- ImageGenerationProvider：仅预留 adapter contract，尚未接入真实生图模型。

默认 `verify.ps1`、`run-local.ps1 -SmokeOnly` 和 Playwright smoke 都强制关闭远端 LLM，保证无 API key、无网络时仍可演示。

### 当前技术栈

- Frontend：`React + Vite + TypeScript + Tailwind CSS`
- Backend：`FastAPI + Pydantic + SQLAlchemy`
- 当前演示数据库：`SQLite`
- 架构目标数据库：`PostgreSQL`
- Agent trace：`agent_runs` / `agent_run_steps`
- LLM 边界：OpenAI-compatible `LLMProvider`
- 当前验证：Python unit tests + frontend build + Playwright smoke

## 主要 API

当前已提供的主要 API：

- `GET /api/v1/demo-data/status`
- `POST /api/v1/demo-data/load`
- `POST /api/v1/demo-data/reset-user-data`
- `GET /api/v1/student-profiles`
- `POST /api/v1/student-profiles`
- `POST /api/v1/student-profiles/from-dialogue`
- `GET /api/v1/student-profiles/{profile_id}`
- `DELETE /api/v1/student-profiles/{profile_id}`
- `POST /api/v1/student-profiles/{profile_id}/update-from-trace`
- `GET /api/v1/courses/{course_id}/graph`
- `POST /api/v1/courses/{course_id}/documents`
- `GET /api/v1/documents/{document_id}/chunks`
- `POST /api/v1/knowledge/search`
- `POST /api/v1/learning-paths`
- `GET /api/v1/learning-paths/{path_id}`
- `POST /api/v1/resources/generate`
- `POST /api/v1/tutor/ask`
- `POST /api/v1/quizzes/generate`
- `POST /api/v1/quizzes/{quiz_id}/attempts`
- `GET /api/v1/agent-runs/{run_id}`

## 待完成工作

以下内容仍未完成，不能在比赛材料中表述为已交付。

### 核心能力

- PDF / Word / PPT 等文件上传和解析。
- embedding / VectorStore / hybrid retrieval 检索链路。
- Tutor / Resource 对复杂真实课程资料的更强 grounded generation。
- 视频、动画或真实图片类资源生成。
- 长期学习历史压缩和跨 session 动态画像建模。
- 更完整的 mastery model，而不是单次 Quiz attempt 驱动的最小评价。

### 工程与部署

- PostgreSQL migration 和正式数据库初始化脚本。
- Redis/RQ 或等价任务队列。
- 生产级配置、日志、安全和运维脚本。
- CI/CD。
- 依赖 license 清单和提交材料中的开源合规表。

### 测试与演示材料

- 失败路径 UI 自动化测试。
- 多浏览器 / 移动视口测试。
- 真实外部 LLM endpoint 的手动验收记录。
- 7 分钟演示脚本。
- PPT、系统说明书、测试说明书、AI Coding 使用说明。

## 本地部署教程

完整部署说明见 [deployment/README.md](deployment/README.md)。下面是最短可运行路径。

### 1. 环境要求

- Windows PowerShell
- Python 3.11+
- Node.js 20.19+ 或 22.12+
- npm
- 可运行的 ASGI server：当前脚本使用 `python -m uvicorn app.main:app`

如果当前机器没有 Microsoft Edge，可设置 Playwright 使用 Chromium：

```powershell
$env:PLAYWRIGHT_CHANNEL='chromium'
```

### 2. 安装依赖

在仓库根目录执行：

```powershell
python -m pip install -e .
python -m pip install uvicorn
cd src/frontend
npm ci
cd ../..
```

### 3. 启动本地演示

```powershell
./scripts/run-local.ps1
```

脚本会自动：

- 设置本地 demo 环境变量。
- 启动 FastAPI backend。
- 加载 demo data。
- 启动 Vite frontend。
- 打印 backend/frontend 访问地址。

默认访问：

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`

停止演示时，在运行脚本的 PowerShell 中按 `Ctrl+C`。

### 4. 自定义端口

```powershell
./scripts/run-local.ps1 -BackendPort 8010 -FrontendPort 5175
```

### 5. 只验证启动链路

```powershell
./scripts/run-local.ps1 -SmokeOnly
```

该命令用于快速确认 backend、frontend 和 demo data load 是否能启动，不会进入长时间运行状态。

### 6. 执行完整验证

```powershell
./scripts/verify.ps1
```

该脚本覆盖：

- Python compile check
- backend unit tests
- `pip check`
- backend wheel build
- frontend dependency install
- frontend production build
- Playwright browser smoke

当前最近一次 Reviewer 验证结果：`47` 个后端测试通过，frontend build 通过，Playwright 主流程 smoke 通过。

## 真实 LLM 演示配置

默认本地演示不依赖真实 LLM。需要真实 LLM 效果时，使用显式 opt-in。

### 阿里云百炼 Flash

先配置用户级 API key：

```powershell
[Environment]::SetEnvironmentVariable('ALIYUN_BAILIAN_API_KEY', '<your-aliyun-bailian-api-key>', 'User')
```

然后启动：

```powershell
./scripts/run-local-aliyun-flash.ps1
```

该脚本默认设置：

- `LLM_PROVIDER=openai_compatible`
- `LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `LLM_MODEL=qwen3.5-flash`
- `LLM_ENABLE_FOR_TUTOR=true`
- `LLM_ENABLE_FOR_RESOURCE=true`
- `LLM_ENABLE_FOR_EVALUATOR=true`
- `LLM_ENABLE_FOR_PROFILE_UPDATER=true`
- `LLM_FALLBACK_MODE=rule_based`
- `LLM_BYPASS_PROXY=true`

临时换模型：

```powershell
./scripts/run-local-aliyun-flash.ps1 -Model qwen3.5-plus
```

### 通用 OpenAI-compatible Provider

```powershell
$env:LLM_PROVIDER='openai_compatible'
$env:LLM_BASE_URL='<provider-base-url>'
$env:LLM_MODEL='<model-name>'
$env:LLM_API_KEY='<your-api-key>'
$env:LLM_ENABLE_FOR_TUTOR='true'
$env:LLM_ENABLE_FOR_RESOURCE='true'
$env:LLM_ENABLE_FOR_EVALUATOR='true'
$env:LLM_ENABLE_FOR_PROFILE_UPDATER='true'
$env:LLM_FALLBACK_MODE='rule_based'
./scripts/run-local.ps1 -UseRemoteTutorLLM
```

不要把真实 `LLM_API_KEY` 写入仓库、`.env`、测试输出、前端 bundle 或 Agent trace。

## 演示流程建议

1. 运行 `./scripts/run-local.ps1`。
2. 打开 frontend 地址。
3. 点击 `Reset user demo data`，回到干净演示状态。
4. 在 `Knowledge setup` 粘贴一段 `text` / `markdown` 课程资料并导入。
5. 查看 `document_id`、`chunk_count` 和 `source_ref`。
6. 可选使用 `Search imported chunks` 验证检索命中。
7. 输入自然语言学习目标，生成学生画像。
8. 查看 6 维画像。
9. 创建学习路径。
10. 切换 5 类资源并生成至少 2 类资源。
11. 向 Tutor 提问，并观察 grounded source。
12. 生成 Quiz 并提交答案。
13. 查看 Evaluator 反馈和自动画像更新。
14. 查看 Agent trace 时间线中的具体 grounded sources。

## 重要边界

- 当前 SQLite 只用于本地开发和比赛演示，不代表正式数据库方向。
- 当前真实资料导入仅支持 `text` / `markdown` 粘贴，不代表完整文件上传解析平台。
- 当前 RAG 使用 SQLite keyword retrieval，不代表 embedding / VectorStore / pgvector 已完成。
- 默认 rule-based fallback 是演示稳定性保障，不等同于完整智能能力。
- 真实 LLM 需要显式配置 API key 和开关；默认验证不依赖网络。
- 生图接口目前只是 adapter contract 预留，不是已完成的图片生成能力。
- API handler 和 frontend 不承载核心业务逻辑；核心逻辑应保持在 service / agent / adapter 边界内。

## 相关文档

- [项目简介](docs/00-project-brief.md)
- [需求说明](docs/01-requirements.md)
- [验收标准](docs/02-acceptance-criteria.md)
- [架构设计](docs/03-architecture.md)
- [开发路线](docs/04-development-roadmap.md)
- [敏捷开发记录](docs/05-agile-development-log.md)
- [项目状态](docs/06-project-state.md)
- [Review 日志](reviews/review-log.md)
- [本地部署说明](deployment/README.md)
- [开源调研](docs/research/a3-open-source-research.md)
- [开源合规说明](docs/compliance/open-source-compliance.md)

## 合规原则

本项目可以参考开源项目的架构、技术栈和模块划分，但参赛作品主体应由团队在本届比赛期间自主设计与实现。第三方依赖、开源协议和参考来源应持续记录，避免复制 license 不兼容项目的核心代码。
