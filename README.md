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

当前分支处于个人敏捷开发模式下的 RAG Phase 5 演示增强阶段：

- Phase 2：核心智能能力已基本补齐，包括真实 LLM opt-in、画像构建、资源生成、评价反馈。
- Phase 3 / Phase 4：RAG reranking、citation quality、source panel 和 Agent trace 证据展示已完成。
- Phase 5：知识库管理最小闭环已完成，包括 document list、文件上传、PDF / Word 文本解析、删除、reindex 和 scope filter。

截至 2026-06-17，当前分支已具备以下可演示能力。

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
  - 前端可上传 `.txt`、`.md`、`.pdf`、`.docx` 资料。
  - 后端创建 `documents` / `document_chunks`。
  - `KnowledgeBaseService.search()` 基于真实导入 chunk 做 keyword retrieval。
  - Tutor / Resource response 保留真实 `source_refs`。
  - Agent trace 可展示具体 `document:{id}#chunk:{index}` 来源。
- RAG 检索与证据增强：
  - search metadata 包含 `matched_terms`。
  - search metadata 包含 `term_match_count`。
  - BFS/DFS 复合问题支持 anchor-aware coverage ranking，减少只召回 BFS 而漏掉 DFS chunk 的演示风险。
  - SQLite + Python cosine similarity 的 hybrid retrieval 已作为 opt-in 能力提供。
  - Rule-based reranking 已作为 opt-in 能力提供。
  - Tutor / Resource answer 可展示 grounded source panel、excerpt、score、retrieval mode 和 rerank reason。
  - Search UI 展示 `matched_terms`、`anchor_matches` 和 chunk 摘要，方便人工检查检索依据。
  - stack / queue、BFS / DFS 演示资料可用于手动检索验证。
- RAG Phase 5 知识库管理：
  - 页面可查看当前课程 document list。
  - 支持刷新 document list。
  - 支持删除非 seed document，删除后新检索不再召回旧 chunks。
  - 支持对单个 document 触发 reindex；embedding 未启用时返回 disabled result，不影响 keyword retrieval。
  - 支持 course/demo 与 private document 的最小 scope filter。
  - PDF 使用 `pypdf` 提取文本，Word 使用 `python-docx` 提取段落和表格文本。

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
- 默认向量检索：`SQLite + Python cosine similarity`
- 后续增强向量检索：`pgvector`
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
- `POST /api/v1/courses/{course_id}/documents/upload`
- `GET /api/v1/courses/{course_id}/documents`
- `GET /api/v1/documents/{document_id}`
- `DELETE /api/v1/documents/{document_id}`
- `POST /api/v1/documents/{document_id}/reindex`
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

- PPT 文件上传和解析。
- 扫描版 PDF OCR。
- pgvector / production-grade vector index 检索链路。
- 生产级 reranker 或 cross-encoder reranker。
- Tutor / Resource 对复杂真实课程资料的更强 grounded generation。
- 视频、动画或真实图片类资源生成。
- 长期学习历史压缩和跨 session 动态画像建模。
- 更完整的 mastery model，而不是单次 Quiz attempt 驱动的最小评价。

### 工程与部署

- PostgreSQL migration、pgvector 和正式数据库初始化脚本。
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

当前最近一次 Reviewer 验证结果会记录在 `docs/process/05-agile-development-log.md` 和 `reviews/` 下的 review log 中。

## 真实 LLM / RAG 演示配置

默认本地演示不依赖真实 LLM 或 embedding API。需要真实效果时，使用显式 opt-in；完整说明见 [deployment/README.md](deployment/README.md)。

### API Key 设置

DeepSeek Chat LLM：

```powershell
[Environment]::SetEnvironmentVariable('DEEPSEEK_API_KEY', '<your-deepseek-api-key>', 'User')
```

阿里云百炼 Chat / Embedding：

```powershell
[Environment]::SetEnvironmentVariable('ALIYUN_BAILIAN_API_KEY', '<your-aliyun-bailian-api-key>', 'User')
```

不要把真实 API key 写入仓库、`.env`、测试输出、前端 bundle 或 Agent trace。

### RAG 检索模式

| 模式 | 环境变量 | 是否需要 embedding API | 说明 |
|---|---|---:|---|
| Keyword | `RAG_RETRIEVAL_MODE=keyword` | 否 | 默认模式，最稳，使用 SQLite chunk 文本检索。 |
| Vector | `RAG_RETRIEVAL_MODE=vector` | 是 | 使用 SQLite `chunk_embeddings` + Python cosine similarity。 |
| Hybrid | `RAG_RETRIEVAL_MODE=hybrid` | 是 | keyword + vector 融合，推荐用于真实 RAG 演示。 |

手动启用 hybrid 示例：

```powershell
$env:RAG_RETRIEVAL_MODE='hybrid'
$env:RAG_EMBEDDING_ENABLED='true'
$env:RAG_VECTOR_STORE='sqlite_cosine'
$env:EMBEDDING_PROVIDER='openai_compatible'
$env:EMBEDDING_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
$env:EMBEDDING_MODEL='text-embedding-v3'
$env:EMBEDDING_API_KEY=$env:ALIYUN_BAILIAN_API_KEY
./scripts/run-local.ps1
```

Rerank 是本地 rule-based 重排序，默认关闭：

```powershell
$env:RAG_RERANK_ENABLED='true'
$env:RAG_RERANK_MAX_CANDIDATES='12'
$env:RAG_RERANK_TOP_CONTEXT='5'
$env:RAG_RERANK_CONTEXT_CHAR_LIMIT='3500'
```

### 便捷启动脚本

| 脚本 | 需要的 API key | 启动结果 |
|---|---|---|
| `./scripts/run-local.ps1` | 无 | 离线 rule-based Agent + keyword RAG，最适合评委本地快速启动。 |
| `./scripts/run-local-deepseek.ps1` | `DEEPSEEK_API_KEY` | Tutor / Resource / Evaluator / ProfileUpdater 使用 DeepSeek，RAG 仍默认 keyword。 |
| `./scripts/run-local-aliyun-flash.ps1` | `ALIYUN_BAILIAN_API_KEY` | 全部 LLM Agent 使用 Qwen Flash，RAG 仍默认 keyword。 |
| `./scripts/run-local-aliyun-hybrid.ps1` | `ALIYUN_BAILIAN_API_KEY` | Qwen Flash + 阿里云 `text-embedding-v3` + SQLite hybrid retrieval。 |
| `./scripts/run-local-deepseek-hybrid.ps1` | `DEEPSEEK_API_KEY` + `ALIYUN_BAILIAN_API_KEY` | DeepSeek 负责 Agent 输出，阿里云 embedding 负责 hybrid RAG。 |
| `./scripts/run-local-deepseek-rerank.ps1` | `DEEPSEEK_API_KEY` | DeepSeek + rule-based rerank，用于观察 source panel 中的 `rerank_score`。 |

推荐比赛演示组合：

- 无网络稳定演示：`./scripts/run-local.ps1`
- 真实 LLM 演示：`./scripts/run-local-deepseek.ps1`
- 真实 LLM + hybrid RAG：`./scripts/run-local-deepseek-hybrid.ps1`
- 阿里云全家桶：`./scripts/run-local-aliyun-hybrid.ps1`

## 演示流程建议

1. 运行 `./scripts/run-local.ps1`。
2. 打开 frontend 地址。
3. 点击 `Reset user demo data`，回到干净演示状态。
4. 在 `Knowledge setup` 粘贴一段 `text` / `markdown` 课程资料并导入，或上传 `.txt` / `.md` / `.pdf` / `.docx` 资料。
5. 查看 document list、`chunk_count`、parser、status 和 source panel。
6. 可选点击 `Reindex`，在默认无 embedding 配置时应看到 disabled result，keyword retrieval 仍可用。
7. 可选使用 `Search imported chunks` 验证检索命中。
8. 可选删除非 seed document，再次搜索确认旧资料不再被召回。
9. 输入自然语言学习目标，生成学生画像。
10. 查看 6 维画像。
11. 创建学习路径。
12. 切换 5 类资源并生成至少 2 类资源。
13. 向 Tutor 提问，并观察 grounded source。
14. 生成 Quiz 并提交答案。
15. 查看 Evaluator 反馈和自动画像更新。
16. 查看 Agent trace 时间线中的具体 grounded sources。

## 重要边界

- 当前 SQLite 只用于本地开发和比赛演示，不代表正式数据库方向。
- 当前真实资料导入支持 `text` / `markdown` 粘贴和 `.txt` / `.md` / `.pdf` / `.docx` 文件上传，但不支持 OCR 和 PPT。
- 当前 RAG 默认使用 SQLite keyword retrieval；SQLite cosine hybrid retrieval 已作为显式 opt-in 能力提供，不代表 pgvector 或生产级向量索引已完成。
- 当前知识库 private scope 使用 `owner_user_id` 最小实现，尚未接入正式认证 session。
- 默认 rule-based fallback 是演示稳定性保障，不等同于完整智能能力。
- 真实 LLM 需要显式配置 API key 和开关；默认验证不依赖网络。
- 生图接口目前只是 adapter contract 预留，不是已完成的图片生成能力。
- API handler 和 frontend 不承载核心业务逻辑；核心逻辑应保持在 service / agent / adapter 边界内。

## 相关文档

- [文档总入口](docs/README.md)
- [项目简介](docs/project/00-project-brief.md)
- [需求说明](docs/project/01-requirements.md)
- [验收标准](docs/project/02-acceptance-criteria.md)
- [架构设计](docs/architecture/03-architecture.md)
- [开发路线](docs/process/04-development-roadmap.md)
- [敏捷开发记录](docs/process/05-agile-development-log.md)
- [项目状态](docs/project/06-project-state.md)
- [Review 日志](reviews/review-log.md)
- [本地部署说明](deployment/README.md)
- [开源调研](docs/research/a3-open-source-research.md)
- [开源合规说明](docs/compliance/open-source-compliance.md)

## 合规原则

本项目可以参考开源项目的架构、技术栈和模块划分，但参赛作品主体应由团队在本届比赛期间自主设计与实现。第三方依赖、开源协议和参考来源应持续记录，避免复制 license 不兼容项目的核心代码。
