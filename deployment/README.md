# Deployment and Local Demo

最后更新：2026-06-04

本文档只覆盖当前 MVP 阶段可运行的本地开发和演示配置。当前后端默认使用 SQLite demo database；`PostgreSQL`、`Redis/RQ`、真实 `LLMProvider` 和真实 `VectorStore` 仍是架构目标，后续应通过独立任务补迁移、队列和真实外部能力配置。

## Current vs Target

- 当前本地演示数据库：`sqlite:///./data/demo.sqlite3`
- 当前用途：本地开发、比赛演示、`run-local.ps1` smoke
- 正式数据库方向：`PostgreSQL`
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

### LLM Provider Variables

当前本地 demo 默认不依赖真实 LLM。后续接入 OpenAI-compatible provider 时，应通过环境变量注入配置，并保留 rule-based fallback。

| 变量 | Demo 默认值 | 说明 |
|---|---|---|
| `LLM_PROVIDER` | `rule_based` | Provider 类型。后续真实接入可设为 `openai_compatible`。 |
| `LLM_ENABLE_FOR_TUTOR` | `false` | 第一批真实 LLM 只建议用于 `Tutor Agent`。 |
| `LLM_ENABLE_FOR_PROFILE_UPDATER` | `false` | 显式启用后，ProfileUpdater 会先用固定 JSON schema 分析 Agent trace，失败时回退到 rule-based。 |
| `LLM_BASE_URL` | 空 | OpenAI-compatible endpoint base URL。 |
| `LLM_API_KEY` | 空 | Secret，不得写入仓库、日志、frontend bundle 或 agent run 记录。 |
| `LLM_MODEL` | 空 | 模型名称。 |
| `LLM_TIMEOUT_SECONDS` | `20` | 单次请求超时。 |
| `LLM_MAX_RETRIES` | `0` | 最小 retry 次数，避免演示卡死。 |
| `LLM_FALLBACK_MODE` | `rule_based` | LLM 未配置、timeout 或失败时回退到 rule-based。 |
| `LLM_BYPASS_PROXY` | `false` | 为 `true` 时，LLM provider 调用绕过当前 shell 的 HTTP/HTTPS proxy。 |

默认 `verify.ps1`、`run-local.ps1 -SmokeOnly` 和 Playwright smoke 不应依赖真实 LLM 网络调用。需要验证真实 LLM 时，应使用显式 opt-in 的本地环境变量或独立手动验证路径。

DeepSeek OpenAI-compatible 本地显式 opt-in 示例：

```powershell
$env:LLM_PROVIDER='openai_compatible'
$env:LLM_ENABLE_FOR_TUTOR='true'
$env:LLM_ENABLE_FOR_PROFILE_UPDATER='true'
$env:LLM_BASE_URL='https://api.deepseek.com'
$env:LLM_MODEL='deepseek-v4-flash'
$env:LLM_API_KEY='<your-deepseek-api-key>'
$env:LLM_BYPASS_PROXY='true'
./scripts/run-local.ps1 -UseRemoteTutorLLM
```

阿里云百炼 Flash 一键启动脚本：

```powershell
[Environment]::SetEnvironmentVariable('ALIYUN_BAILIAN_API_KEY', '<your-aliyun-bailian-api-key>', 'User')
./scripts/run-local-aliyun-flash.ps1
```

该脚本默认使用：

- `LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`
- `LLM_MODEL=qwen3.5-flash`
- `LLM_ENABLE_FOR_TUTOR=true`
- `LLM_ENABLE_FOR_PROFILE_UPDATER=true`
- `LLM_FALLBACK_MODE=rule_based`

如需临时换模型：

```powershell
./scripts/run-local-aliyun-flash.ps1 -Model qwen3.5-plus
```

不要把真实 `LLM_API_KEY` 写入 `deployment/local.env.example`、`.env`、测试输出或 agent run 记录。

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
