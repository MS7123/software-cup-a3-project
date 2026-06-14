## 变更记录：用户认证与数据持久化

### 变更概要（2026-06-14）

本次变更为系统添加了两项核心能力：

1. **用户认证系统**：基于 JWT 的用户注册、登录和鉴权，所有 API 受 Bearer token 保护。
2. **数据持久化与多用户隔离**：每次登录自动加载用户上次的学习进度（学习路径、资源、测验），新建路径时自动覆盖旧路径，不同用户的数据完全隔离。

### 认证架构

```
客户端                    后端
  │                        │
  │  POST /auth/register   │  创建用户，bcrypt 加密密码
  │────────────────────►   │  返回 JWT（7天过期）
  │                        │
  │  POST /auth/login      │  验证密码，签发 JWT
  │────────────────────►   │
  │                        │
  │  请求头带 Bearer JWT   │  get_current_user 依赖注入
  │────────────────────►   │  → 失败返回 401
```

**认证新增文件/模块：**

| 文件                                         | 说明                                                         |
| -------------------------------------------- | ------------------------------------------------------------ |
| `src/backend/app/core/auth.py`               | JWT 创建/验证、密码加密（bcrypt）、FastAPI `get_current_user` 依赖 |
| `src/backend/app/api/v1/auth.py`             | `POST /auth/register`、`POST /auth/login`、`GET /auth/me`    |
| `src/frontend/src/api/client.ts` (auth 对象) | `auth.register()`、`auth.login()`、`auth.logout()`、`auth.isAuthenticated()` |
| `src/frontend/src/App.tsx` (AuthPage)        | 登录/注册页面，自动切换                                      |

**环境变量：**

| 变量               | 默认值                                | 说明                           |
| ------------------ | ------------------------------------- | ------------------------------ |
| `AUTH_SECRET_KEY`  | `dev-secret-key-change-in-production` | JWT 签名密钥，生产环境必须更换 |
| `APP_DATABASE_URL` | `sqlite:///./data/demo.sqlite3`       | 数据库连接串                   |

### 数据持久化方案

**覆盖语义（Create-or-Replace）：**

用户创建新学习路径时，旧路径自动标记为 `completed`，新路径标记为 `active`。前端默认加载 `active` 路径。资源生成不删除旧记录——前端按 `resource_type` 匹配展示。

**新增 API：**

| 方法  | 路径                                                | 用途                               |
| ----- | --------------------------------------------------- | ---------------------------------- |
| `GET` | `/api/v1/student-profiles/{id}/learning-paths`      | 查某画像的所有学习路径（最新优先） |
| `GET` | `/api/v1/learning-paths/{id}/resources`             | 查某路径下所有已生成资源           |
| `GET` | `/api/v1/resources/path-item/{item_id}`             | 查某路径步骤的已生成资源           |
| `GET` | `/api/v1/quizzes?student_profile_id=X&concept_id=Y` | 查已有测验（按画像/知识点过滤）    |

**数据库模型变更：**

```diff
- User.name (String)
- User.role (String)
+ User.username (String, unique, indexed)
+ User.email (String, nullable)
+ User.hashed_password (String)
+ User.role (String, default="student")
```

### 前端自动加载逻辑

当用户登录或切换画像时，前端自动执行以下流程：

```
用户登录 → 列出画像（自动加载 3 个演示画像）
         → 选中画像 → 自动查询已有学习路径
                    → 选中路径步骤 → 自动查询已有资源
                    → 选中知识点 → 自动查询已有测验
         → 用户点"生成"按钮 → 覆盖旧数据/创建新数据
```

关键 `useEffect` 钩子：

- `selectedProfileId` 变化 → `api.listLearningPaths(profileId)` → 加载最近 `active` 路径
- `selectedItem?.id` 变化 → `api.listResourcesForPathItem(itemId)` → 加载匹配类型的资源
- `selectedConcept?.id` 变化 → `api.listQuizzes(profileId, conceptId)` → 加载最新测验

### PostgreSQL 支持

系统通过 SQLAlchemy 连接串统一管理数据库，支持 SQLite 和 PostgreSQL：

```powershell
# SQLite（轻量演示）
$env:APP_DATABASE_URL="sqlite:///./data/demo.sqlite3"

# PostgreSQL（正式部署）
$env:APP_DATABASE_URL="postgresql+pg8000://postgres:password@127.0.0.1:5432/softwarecup_a3"
```

本次变更新增 `psycopg2-binary` 依赖（C 扩展驱动）和 `pg8000` 依赖（纯 Python 驱动，兼容中文 Windows 环境）。启动时自动建表，无需手动执行迁移脚本。

### 后端 Service 层变更

所有 Service 方法增加 `user_id` 参数，实现行级数据隔离：

| Service                 | 变更                                                         |
| ----------------------- | ------------------------------------------------------------ |
| `ProfileService`        | `get_profile`、`create_profile`、`delete_profile` 增加 `user_id` 参数 |
| `ProfileUpdaterService` | `update_from_trace` 增加 `user_id` 参数                      |
| `LearningPathService`   | `get_path`、`list_paths_for_profile` 增加 `user_id` 参数；`create_path` 自动标记旧路径为 `completed` |
| `AssessmentService`     | `generate_quiz`、`submit_attempt`、`list_quizzes` 增加 `user_id` 参数 |
| `TutorService`          | `ask` 增加 `user_id` 参数，验证画像归属                      |
| `ResourceService`       | `generate_resource` 增加 `user_id` 参数                      |
| `DemoDataService`       | `reset_user_data` 接受 `user_id`，仅清理该用户的非演示数据；新增 `ensure_user_demo_profiles` 为新用户自动创建演示画像 |

### 数据库时间戳兼容性

所有 `DateTime` 字段改为使用时区感知时间（`datetime.now(timezone.utc)`），兼容 PostgreSQL 的带时区时间戳类型。

### 测试覆盖率

当前 39 个后端测试全部通过：

```
$ python -m unittest discover -s tests -v
Ran 39 tests in 10.216s
OK
```

测试类型：单元测试（Agent、Provider、Service）+ 集成测试（API + 数据库）+ 认证流程测试。

### 手动启动命令

以下提供多种场景的启动方式，根据实际环境选择。

---

#### 场景 A：使用 SQLite（零配置，推荐首次运行）

无需安装/配置数据库，数据保存在 `data/demo.sqlite3` 文件。

```powershell
# ===== 终端 1：启动后端 =====
cd D:\softwarecup  # ← 替换为你的项目实际路径

$env:PYTHONPATH="src/backend"
$env:APP_DATABASE_URL="sqlite:///./data/demo.sqlite3"
$env:AUTH_SECRET_KEY="dev-secret-key-change-in-production"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# ===== 终端 2：启动前端 =====
cd D:\softwarecup\src\frontend  # ← 替换为你的项目实际路径
npx vite --host 127.0.0.1 --port 5173
```

> 启动后打开 http://127.0.0.1:5173 → 点击 Register → 创建账号即可使用。

---

#### 场景 B：使用 PostgreSQL

需要先安装并启动 PostgreSQL 服务（安装方法见下文 "PostgreSQL 安装指引"）。

**第一步：创建数据库（首次执行一次即可）**

```powershell
# 方法1：通过 psql 命令行（需将 psql 加入 PATH）
set PGPASSWORD=your_password
psql -h 127.0.0.1 -U postgres -c "CREATE DATABASE softwarecup_a3;"

# 方法2：通过 Python（推荐，不需要 psql）
python -c "
from sqlalchemy import create_engine, text
engine = create_engine(
    'postgresql+pg8000://postgres:your_password@127.0.0.1:5432/postgres',
    isolation_level='AUTOCOMMIT'
)
with engine.connect() as conn:
    conn.execute(text(\"CREATE DATABASE softwarecup_a3 ENCODING 'UTF8'\"))
print('Database created')
"
```

**第二步：启动后端**

```powershell
cd D:\softwarecup  # ← 替换为你的项目实际路径

$env:PYTHONPATH="src/backend"

# ── 方案 B1：pg8000 驱动（纯 Python，兼容性好，推荐 Windows）──
$env:APP_DATABASE_URL="postgresql+pg8000://postgres:your_password@127.0.0.1:5432/softwarecup_a3"

# ── 方案 B2：psycopg2 驱动（C 扩展，性能更好，推荐 Linux/macOS）──
$env:APP_DATABASE_URL="postgresql://postgres:your_password@127.0.0.1:5432/softwarecup_a3"

$env:AUTH_SECRET_KEY="dev-secret-key-change-in-production"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**第三步：启动前端**

```powershell
cd D:\softwarecup\src\frontend  # ← 替换为你的项目实际路径
npx vite --host 127.0.0.1 --port 5173
```

> ⚠️ 请将上述命令中的 `your_password` 替换为你 PostgreSQL 的 `postgres` 用户实际密码。
>
> ⚠️ `AUTH_SECRET_KEY` 在生产环境应使用足够长的随机字符串，可通过以下命令生成：
>
> ```powershell
> python -c "import secrets; print(secrets.token_hex(32))"
> ```
>
> ⚠️ 密码若包含特殊字符（如 @ # $ %），需进行 URL 百分号编码：
>
> ```
> @ → %40    # → %23    $ → %24    % → %25
> 例如密码 p@ss#123 → postgresql://postgres:p%40ss%23123@127.0.0.1:5432/softwarecup_a3
> ```

---

#### 场景 C：使用一键脚本（默认 SQLite）

```powershell
# 默认使用 SQLite 启动
./scripts/run-local.ps1

# 仅验证启动（不保持运行）
./scripts/run-local.ps1 -SmokeOnly

# 指定自定义端口
./scripts/run-local.ps1 -BackendPort 8010 -FrontendPort 5175

# 切换为 PostgreSQL（先设环境变量再运行脚本）
$env:APP_DATABASE_URL="postgresql+pg8000://postgres:your_password@127.0.0.1:5432/softwarecup_a3"
./scripts/run-local.ps1
```

---

### PostgreSQL 安装指引（新电脑）

**Windows 安装：**

1. 下载安装包：https://www.postgresql.org/download/windows/
2. 运行安装程序，安装时**记下 `postgres` 用户的密码**
3. 安装完成后，将 `C:\Program Files\PostgreSQL\版本号\bin` 添加到系统 PATH
4. 验证安装：`pg_isready`

**macOS 安装：**

```bash
brew install postgresql@16
brew services start postgresql@16
createdb softwarecup_a3
```

**Linux 安装（Ubuntu/Debian）：**

```bash
sudo apt update && sudo apt install postgresql postgresql-client
sudo systemctl start postgresql
sudo -u postgres createdb softwarecup_a3
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'your_password';"
```

**安装 Python 数据库驱动：**

```bash
# 任选其一或二者都装（SQLAlchemy 会根据连接串自动选择）
pip install pg8000          # 纯 Python，兼容性好，推荐 Windows
pip install psycopg2-binary # C 扩展，性能更好，推荐 Linux/macOS
```

---

### 完整环境变量参考

| 变量                   | 默认值                                | 说明                                               |
| ---------------------- | ------------------------------------- | -------------------------------------------------- |
| `PYTHONPATH`           | 无（必须设为 `src/backend`）          | Python 模块搜索路径                                |
| `APP_DATABASE_URL`     | `sqlite:///./data/demo.sqlite3`       | 数据库连接串                                       |
| `AUTH_SECRET_KEY`      | `dev-secret-key-change-in-production` | JWT 签名密钥，生产务必更换                         |
| `BACKEND_HOST`         | `127.0.0.1`                           | 后端监听地址                                       |
| `BACKEND_PORT`         | `8000`                                | 后端监听端口                                       |
| `FRONTEND_HOST`        | `127.0.0.1`                           | 前端监听地址                                       |
| `FRONTEND_PORT`        | `5173`                                | 前端监听端口                                       |
| `LLM_PROVIDER`         | `rule_based`                          | LLM 类型：`rule_based`(离线) / `openai_compatible` |
| `LLM_ENABLE_FOR_TUTOR` | `false`                               | 是否启用真实 LLM Tutor                             |

**数据库连接串格式大全：**

```
# SQLite 文件存储（零配置）
sqlite:///./data/demo.sqlite3

# PostgreSQL + pg8000 驱动（纯 Python，推荐 Windows）
postgresql+pg8000://postgres:password@127.0.0.1:5432/softwarecup_a3

# PostgreSQL + psycopg2 驱动（C 扩展，推荐 Linux/macOS）
postgresql://postgres:password@127.0.0.1:5432/softwarecup_a3

# 不同主机 / 端口 / 数据库名
postgresql+pg8000://postgres:password@192.168.1.100:5433/my_database

# 密码含特殊字符时进行 URL 编码
# @ → %40   # → %23   $ → %24   % → %25
postgresql+pg8000://postgres:p%40ss%23123@127.0.0.1:5432/softwarecup_a3
```