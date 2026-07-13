# Deployment and Local Demo

最后更新：2026-07-13

本文档覆盖当前比赛演示可运行的本地部署配置，包括默认离线启动、真实 LLM API 设置、embedding / 向量模型 API 设置、RAG 检索模式切换，以及各便捷启动脚本会得到什么效果。

当前后端默认使用 SQLite demo database；`PostgreSQL`、`Redis/RQ` 和生产级 `pgvector` 仍是后续增强目标，不是当前本地演示的必需条件。

## Current vs Target

- 当前本地演示数据库：`sqlite:///./data/demo.sqlite3`
- 当前用途：本地开发、比赛演示、`run-local.ps1` smoke
- 默认 RAG 检索：SQLite keyword retrieval
- 可选 RAG 检索：SQLite + Python cosine similarity hybrid retrieval
- 后续数据库方向：`PostgreSQL`
- 后续向量检索方向：`pgvector`
- 正式配置路径：后续统一通过环境变量 `APP_DATABASE_URL` 切换到 `postgresql+psycopg://...`
- 当前仓库状态：尚未提供 PostgreSQL migration、seed、运维脚本或生产级连接配置

## Prerequisites

- Python 3.11+
- Node.js 20.19+ 或 22.12+
- npm
- 可运行的 ASGI server：当前脚本使用 `python -m uvicorn app.main:app`
- Windows PowerShell

前端 browser smoke 默认在 Windows 使用 `msedge` channel。若机器没有 Microsoft Edge，可设置：

```powershell
$env:PLAYWRIGHT_CHANNEL='chromium'
```

## Environment Variables

示例配置见 [local.env.example](local.env.example)。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `APP_DATABASE_URL` | `sqlite:///./data/demo.sqlite3` | 当前演示数据库连接。SQLite 仅用于本地开发和比赛演示；正式环境应改为 `postgresql+psycopg://...`。 |
| `PYTHONPATH` | `src/backend` | 让 `uvicorn` 找到 `app.main:app`。 |
| `BACKEND_HOST` | `127.0.0.1` | 本地后端监听地址。 |
| `BACKEND_PORT` | `8000` | 本地后端监听端口。 |
| `FRONTEND_HOST` | `127.0.0.1` | Vite dev server 监听地址。 |
| `FRONTEND_PORT` | `5173` | Vite dev server 监听端口。 |
| `VITE_API_BASE_URL` | `/api/v1` | 前端 API base path。保持同源路径，避免浏览器 CORS 干扰本地演示。 |
| `VITE_PROXY_TARGET` | `http://127.0.0.1:8000` | Vite `/api` proxy 指向的后端地址。 |
| `PLAYWRIGHT_CHANNEL` | `msedge` on Windows | Playwright browser channel override。 |

## API Key 设置

### 设置原则

真实 API key 只放在当前 PowerShell session、Windows User-scope environment variable 或部署平台 secret 中。

禁止写入：

- `deployment/local.env.example`
- `.env`
- README / docs 示例中的真实值
- frontend bundle
- test output
- Agent trace
- Git commit

### 科大讯飞星辰 MaaS 比赛默认入口

比赛演示默认使用服务管控页面提供的科大讯飞星辰 MaaS OpenAI-compatible API。启动脚本读取 `XFYUN_SPARK_API_KEY`，并将其仅映射到当前进程的 `LLM_API_KEY`；仓库不保存真实凭据。

一次性写入 Windows User scope：

```powershell
[Environment]::SetEnvironmentVariable('XFYUN_SPARK_API_KEY', '<your-spark-api-key>', 'User')
```

比赛默认启动：

```powershell
./scripts/run-competition-spark.ps1
```

比赛入口从 frontend 端口 `5174` 开始检查；若端口已被占用，会依次寻找后续可用端口并在终端打印最终 URL。需要时仍可通过 `-FrontendPort` 指定自动查找的起始端口。

当前服务使用控制台给出的 `https://maas-api.cn-huabei-1.xf-yun.com/v2` 和 `/models` 实际返回的 model ID `xop3qwen1b7`。脚本启用 Tutor、Resource、Evaluator、ProfileUpdater 以及后续接入的 ProfileBuilder、Planner、Quiz；单次失败时回退 rule-based，缺少 APIKey 时在启动服务前直接失败。

### DeepSeek Chat LLM

DeepSeek 脚本读取 `DEEPSEEK_API_KEY`，并在启动时映射成后端实际使用的 `LLM_API_KEY`。

一次性写入 Windows User scope：

```powershell
[Environment]::SetEnvironmentVariable('DEEPSEEK_API_KEY', '<your-deepseek-api-key>', 'User')
```

只在当前 PowerShell 临时设置：

```powershell
$env:DEEPSEEK_API_KEY='<your-deepseek-api-key>'
```

DeepSeek 启动脚本默认配置：

| 变量 | 值 |
|---|---|
| `LLM_PROVIDER` | `openai_compatible` |
| `LLM_BASE_URL` | `https://api.deepseek.com` |
| `LLM_MODEL` | `deepseek-v4-flash` |
| `LLM_ENABLE_FOR_TUTOR` | `true` |
| `LLM_ENABLE_FOR_RESOURCE` | `true` |
| `LLM_ENABLE_FOR_EVALUATOR` | `true` |
| `LLM_ENABLE_FOR_PROFILE_UPDATER` | `true` |
| `LLM_FALLBACK_MODE` | `rule_based` |

启动：

```powershell
./scripts/run-local-deepseek.ps1
```

临时换模型：

```powershell
./scripts/run-local-deepseek.ps1 -Model deepseek-chat
```

### 阿里云百炼 Chat LLM

阿里云脚本读取 `ALIYUN_BAILIAN_API_KEY`，用于 Qwen Chat LLM，也可用于阿里云 embedding。

一次性写入 Windows User scope：

```powershell
[Environment]::SetEnvironmentVariable('ALIYUN_BAILIAN_API_KEY', '<your-aliyun-bailian-api-key>', 'User')
```

只在当前 PowerShell 临时设置：

```powershell
$env:ALIYUN_BAILIAN_API_KEY='<your-aliyun-bailian-api-key>'
```

阿里云 Flash 启动脚本默认配置：

| 变量 | 值 |
|---|---|
| `LLM_PROVIDER` | `openai_compatible` |
| `LLM_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `LLM_MODEL` | `qwen3.5-flash` |
| `LLM_ENABLE_FOR_TUTOR` | `true` |
| `LLM_ENABLE_FOR_RESOURCE` | `true` |
| `LLM_ENABLE_FOR_EVALUATOR` | `true` |
| `LLM_ENABLE_FOR_PROFILE_UPDATER` | `true` |
| `LLM_FALLBACK_MODE` | `rule_based` |
| `LLM_BYPASS_PROXY` | `true` |

启动：

```powershell
./scripts/run-local-aliyun-flash.ps1
```

临时换模型：

```powershell
./scripts/run-local-aliyun-flash.ps1 -Model qwen3.5-plus
```

### 通用 OpenAI-compatible LLM

如果不用现成脚本，也可以手动设置通用 provider：

```powershell
$env:LLM_PROVIDER='openai_compatible'
$env:LLM_BASE_URL='<provider-base-url>'
$env:LLM_API_KEY='<your-llm-api-key>'
$env:LLM_MODEL='<chat-model-name>'
$env:LLM_ENABLE_FOR_TUTOR='true'
$env:LLM_ENABLE_FOR_RESOURCE='true'
$env:LLM_ENABLE_FOR_EVALUATOR='true'
$env:LLM_ENABLE_FOR_PROFILE_UPDATER='true'
$env:LLM_ENABLE_FOR_PROFILE_BUILDER='true'
$env:LLM_ENABLE_FOR_PLANNER='true'
$env:LLM_TIMEOUT_SECONDS='20'
$env:LLM_MAX_RETRIES='0'
$env:LLM_FALLBACK_MODE='rule_based'
$env:LLM_BYPASS_PROXY='false'
./scripts/run-local.ps1 -UseRemoteTutorLLM
```

`-UseRemoteTutorLLM` 的名字是历史遗留；当前只要相关 `LLM_ENABLE_FOR_*` 为 `true`，Tutor、Resource、Evaluator、ProfileUpdater 都可以走真实 LLM。

### 向量模型 / Embedding API

当前默认向量检索不依赖 PostgreSQL、pgvector、Chroma 或 FAISS。启用 embedding 后，系统会：

```text
document chunks
-> embedding provider
-> chunk_embeddings table in SQLite
-> Python cosine similarity
-> hybrid ranking
```

阿里云 embedding 推荐配置：

```powershell
$env:RAG_EMBEDDING_ENABLED='true'
$env:RAG_VECTOR_STORE='sqlite_cosine'
$env:EMBEDDING_PROVIDER='openai_compatible'
$env:EMBEDDING_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
$env:EMBEDDING_MODEL='text-embedding-v3'
$env:EMBEDDING_API_KEY=$env:ALIYUN_BAILIAN_API_KEY
$env:EMBEDDING_TIMEOUT_SECONDS='10'
$env:EMBEDDING_MAX_RETRIES='0'
$env:EMBEDDING_BYPASS_PROXY='false'
```

通用 OpenAI-compatible embedding 配置：

```powershell
$env:RAG_EMBEDDING_ENABLED='true'
$env:RAG_VECTOR_STORE='sqlite_cosine'
$env:EMBEDDING_PROVIDER='openai_compatible'
$env:EMBEDDING_BASE_URL='<provider-base-url>'
$env:EMBEDDING_MODEL='<embedding-model-name>'
$env:EMBEDDING_API_KEY='<your-embedding-api-key>'
$env:EMBEDDING_TIMEOUT_SECONDS='10'
$env:EMBEDDING_MAX_RETRIES='0'
$env:EMBEDDING_BYPASS_PROXY='false'
```

启用 embedding 后，导入资料时会尝试写入 `chunk_embeddings`。也可以在页面的 document list 对单个 document 点击 `Reindex`。如果 embedding 未配置或失败，keyword retrieval 仍然可用。

## LLM Provider Variables

当前本地 demo 默认不依赖真实 LLM。后续接入 OpenAI-compatible provider 时，应通过环境变量注入配置，并保留 rule-based fallback。

| 变量 | Demo 默认值 | 说明 |
|---|---|---|
| `LLM_PROVIDER` | `rule_based` | Provider 类型。后续真实接入可设为 `openai_compatible`。 |
| `LLM_ENABLE_FOR_TUTOR` | `false` | 第一批真实 LLM 只建议用于 `Tutor Agent`。 |
| `LLM_ENABLE_FOR_RESOURCE` | `false` | 显式启用后，Resource Agent 会先用 LLM 生成 5 类学习资源，失败时回退到 rule-based。 |
| `LLM_ENABLE_FOR_EVALUATOR` | `false` | 显式启用后，Evaluator Agent 会用 LLM 生成评分反馈、薄弱点和下一步建议，失败时回退到 rule-based。 |
| `LLM_ENABLE_FOR_PROFILE_UPDATER` | `false` | 显式启用后，ProfileUpdater 会先用固定 JSON schema 分析 Agent trace，失败时回退到 rule-based。 |
| `LLM_ENABLE_FOR_PROFILE_BUILDER` | `false` | 显式启用后，初始对话画像由 LLM 结构化抽取六个维度，非法输出或远程失败时回退到现有规则构建器。 |
| `LLM_ENABLE_FOR_PLANNER` | `false` | 显式启用后，Hybrid Planner 由规则层保证知识图谱约束，LLM 对合法候选排序并生成推荐资源和理由；非法输出回退到确定性拓扑排序。 |
| `LLM_BASE_URL` | 空 | OpenAI-compatible endpoint base URL。 |
| `LLM_API_KEY` | 空 | Secret，不得写入仓库、日志、frontend bundle 或 agent run 记录。 |
| `LLM_MODEL` | 空 | 模型名称。 |
| `LLM_TIMEOUT_SECONDS` | `20` | 单次请求超时。 |
| `LLM_MAX_RETRIES` | `0` | 最小 retry 次数，避免演示卡死。 |
| `LLM_FALLBACK_MODE` | `rule_based` | LLM 未配置、timeout 或失败时回退到 rule-based。 |
| `LLM_BYPASS_PROXY` | `false` | 为 `true` 时，LLM provider 调用绕过当前 shell 的 HTTP/HTTPS proxy。 |

默认 `verify.ps1`、`run-local.ps1 -SmokeOnly` 和 Playwright smoke 不应依赖真实 LLM 网络调用。需要验证真实 LLM 时，应使用显式 opt-in 的本地环境变量或独立手动验证路径。

## RAG 检索模式设置

### 模式说明

| 模式 | 设置 | 是否需要 embedding API | 结果 |
|---|---|---:|---|
| Keyword | `RAG_RETRIEVAL_MODE=keyword` | 否 | 只使用 SQLite 中的 chunk 文本做关键词/anchor-aware 检索，默认最稳。 |
| Vector | `RAG_RETRIEVAL_MODE=vector` | 是 | 只使用 SQLite `chunk_embeddings` + Python cosine similarity；无 embedding 时会回退到 keyword。 |
| Hybrid | `RAG_RETRIEVAL_MODE=hybrid` | 是 | keyword + vector 加权融合，当前推荐的真实 RAG 演示模式。 |

默认配置：

```powershell
$env:RAG_RETRIEVAL_MODE='keyword'
$env:RAG_EMBEDDING_ENABLED='false'
$env:RAG_VECTOR_STORE='sqlite_cosine'
```

启用 hybrid retrieval：

```powershell
$env:RAG_RETRIEVAL_MODE='hybrid'
$env:RAG_EMBEDDING_ENABLED='true'
$env:RAG_VECTOR_STORE='sqlite_cosine'
$env:EMBEDDING_PROVIDER='openai_compatible'
$env:EMBEDDING_BASE_URL='<provider-base-url>'
$env:EMBEDDING_MODEL='<embedding-model>'
$env:EMBEDDING_API_KEY='<your-embedding-api-key>'
./scripts/run-local.ps1
```

`EMBEDDING_API_KEY` 不得写入仓库、日志、frontend bundle 或 agent run 记录。未配置 embedding provider 时，系统继续走 keyword retrieval。

### Rerank 设置

Rerank 是在 keyword/vector/hybrid 召回之后的轻量重排序，不是远程 rerank model。

默认关闭：

```powershell
$env:RAG_RERANK_ENABLED='false'
```

启用：

```powershell
$env:RAG_RERANK_ENABLED='true'
$env:RAG_RERANK_MAX_CANDIDATES='12'
$env:RAG_RERANK_TOP_CONTEXT='5'
$env:RAG_RERANK_CONTEXT_CHAR_LIMIT='3500'
```

启用后，source panel 中可以看到 `rerank_score` 和 `rerank_reasons`。

## 便捷启动脚本对照

| 脚本 | 需要的 API key | LLM 结果 | RAG 检索结果 | 适合场景 |
|---|---|---|---|---|
| `./scripts/run-local.ps1` | 无 | 全部 Agent 使用 rule-based fallback | `keyword` 默认检索 | 最稳的离线演示、无网络、评委本地快速启动 |
| `./scripts/run-competition-spark.ps1` | `XFYUN_SPARK_API_KEY` | 当前及后续 LLM Agent 默认使用讯飞 MaaS 服务，单次失败回退 rule-based | 默认 `keyword` | **比赛默认入口，frontend 从 `5174` 起自动选择可用端口** |
| `./scripts/run-local.ps1 -UseRemoteTutorLLM` | 手动设置 `LLM_*` | 按当前 shell 中 `LLM_ENABLE_FOR_*` 决定哪些 Agent 调 LLM | 默认仍是 `keyword`，除非手动设置 RAG 变量 | 自定义 provider 调试 |
| `./scripts/run-local-deepseek.ps1` | `DEEPSEEK_API_KEY` | Tutor / Resource / Evaluator / ProfileUpdater 全部使用 DeepSeek，失败回退 rule-based | 默认 `keyword` | 使用 DeepSeek 做真实 Agent 输出 |
| `./scripts/run-local-aliyun-flash.ps1` | `ALIYUN_BAILIAN_API_KEY` | Tutor / Resource / Evaluator / ProfileUpdater 全部使用 Qwen Flash，失败回退 rule-based | 默认 `keyword` | 使用阿里云 Qwen Flash 做真实 Agent 输出 |
| `./scripts/run-local-aliyun-hybrid.ps1` | `ALIYUN_BAILIAN_API_KEY` | 全部 Agent 使用 Qwen Flash | `hybrid`，阿里云 `text-embedding-v3` 写入 SQLite 后做 Python cosine similarity | 阿里云 Chat + embedding 一体演示 |
| `./scripts/run-local-deepseek-hybrid.ps1` | `DEEPSEEK_API_KEY` + `ALIYUN_BAILIAN_API_KEY` | 全部 Agent 使用 DeepSeek | `hybrid`，阿里云 `text-embedding-v3` 作为 embedding | DeepSeek 负责回答，阿里云负责向量召回 |
| `./scripts/run-local-deepseek-rerank.ps1` | `DEEPSEEK_API_KEY` | 全部 Agent 使用 DeepSeek | 默认 `keyword` + rule-based rerank，除非 shell 里另行启用 hybrid | 验证 rerank metadata、source panel 和 context budget |

所有脚本都基于 `run-local.ps1` 启动：

- FastAPI backend。
- Vite frontend。
- `POST /api/v1/demo-data/load` 加载 demo data，除非设置 `-SkipDemoLoad`。
- 默认 SQLite database：`sqlite:///./data/demo.sqlite3`。
- 默认 frontend：`http://127.0.0.1:5173`。
- 默认 backend：`http://127.0.0.1:8000`。

### 推荐启动组合

| 目标 | 推荐命令 | 说明 |
|---|---|---|
| 比赛默认演示 | `./scripts/run-competition-spark.ps1` | 使用科大讯飞星辰 MaaS 启用当前及后续 LLM Agent。 |
| 无网络稳定演示 | `./scripts/run-local.ps1` | 所有核心流程可跑，输出是 rule-based。 |
| 真实 LLM 演示但不启用向量 | `./scripts/run-local-deepseek.ps1` | 回答更自然，但检索仍是 keyword。 |
| 真实 LLM + hybrid RAG | `./scripts/run-local-deepseek-hybrid.ps1` | 当前最完整的 RAG 演示组合。 |
| 阿里云全家桶 | `./scripts/run-local-aliyun-hybrid.ps1` | Chat 与 embedding 都使用阿里云百炼。 |
| 检查 rerank 展示 | `./scripts/run-local-deepseek-rerank.ps1` | 重点观察 source panel 中的 rerank 信息。 |

## Install Dependencies

在仓库根目录执行：

```powershell
python -m pip install -e .
cd src/frontend
npm ci
cd ../..
```

如果当前 Python 环境没有 `uvicorn`，需要在本地环境安装 ASGI server 后再启动后端。该项属于运行环境准备，不改变后端 service / adapter 边界。

当前 `pyproject.toml` 还没有声明 `uvicorn` 依赖；若希望新环境一条命令即可启动本地 demo，后续应补 dev/deploy 依赖或明确独立安装命令。

## Local Demo Run

从仓库根目录执行：

```powershell
./scripts/run-local.ps1
```

脚本会：

- 设置本地演示环境变量。
- 检查 `BACKEND_PORT` 和 `FRONTEND_PORT` 是否空闲。
- 启动 FastAPI backend。
- 调用 `POST /api/v1/demo-data/load` 加载集中管理的 demo data。
- 启动 Vite frontend，并通过 `VITE_PROXY_TARGET` 代理 `/api` 到 backend。
- 打印 backend/frontend URL。
- 保持运行直到按 `Ctrl+C`。

可自定义端口：

```powershell
./scripts/run-local.ps1 -BackendPort 8010 -FrontendPort 5175
```

显式启用远程 Tutor LLM：

```powershell
./scripts/run-local.ps1 -UseRemoteTutorLLM
```

只验证启动链路并自动退出：

```powershell
./scripts/run-local.ps1 -SmokeOnly
```

## Verification

完整验证入口仍保持为：

```powershell
./scripts/verify.ps1
```

该命令覆盖 Python compile、backend unit tests、`pip check`、backend wheel build、frontend build 和 Playwright browser smoke。`IMPL-009` 的部署脚本可额外用：

```powershell
./scripts/run-local.ps1 -SmokeOnly
```

## Boundary Notes

- 部署脚本只编排进程、端口和环境变量，不实现学习路径、Quiz、Evaluator 或 Agent 决策逻辑。
- Demo data 仍通过 `POST /api/v1/demo-data/load` 进入 `DemoDataService`，没有写入部署脚本或前端组件。
- 前端继续通过 `/api/v1` contract 调用后端；Vite proxy 只处理本地开发的网络转发。
- SQLite 是当前演示配置，不代表架构基线从 `PostgreSQL` 改为 SQLite。
- 正式 `PostgreSQL` 配置路径已经统一约定为 `APP_DATABASE_URL`；后续切换数据库时，不应改动 `/api/v1` contract、service contract 或 frontend API path。
- 真实 LLM 接入应通过 `LLMProvider` adapter，不应让 API handler、frontend 或 service 直接依赖具体 provider SDK。
