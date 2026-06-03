# Review Log

最后更新：2026-06-03

## 2026-06-03 State Manager Review

范围：

- 阅读 `README.md`。
- 阅读 `docs/research/a3-open-source-research.md`。
- 阅读 `docs/research/a6-project-discussion-summary.md`。
- 阅读 `docs/compliance/open-source-compliance.md`。
- 阅读 `docs/00-project-brief.md`。
- 阅读 `docs/03-architecture.md`。
- 阅读 `docs/decisions/0001-architecture-baseline.md`。
- 检查 `docs/`、`tasks/`、`reviews/`、`src/`、`scripts/`、`deployment/`、`data/`。
- 检查是否存在依赖配置、测试配置和部署配置。

结论：

- 当前项目是调研和文档准备阶段，不是可运行工程阶段。
- `src/backend/` 和 `src/frontend/` 只有 `.gitkeep`，没有实现代码。
- 未发现依赖配置、测试配置或部署配置。
- A3 调研与合规边界已有文档证据。
- A6 讨论材料存在，但项目简介和 ADR 已明确当前仓库按 A3 推进。
- 架构基线已 Accepted，但尚未有任何实现。

风险：

- 如果不先冻结 MVP，后续实现容易范围过大。
- 如果新 Agent 没有先读 `docs/00-project-brief.md` 和 `docs/06-project-state.md`，可能误把 A6 讨论材料当作当前方向。
- 如果直接复用 AGPL 或无 license 项目代码，会带来参赛合规风险。

建议：

- 先完成用户裁决，再进入架构设计。
- 每个实现任务必须绑定 `docs/02-acceptance-criteria.md` 中的验收标准。
- 每轮实现结束后由 Review & Test Agent 更新本文件。

## 2026-06-03 Task Manager Update

范围：

- 阅读 `docs/01-requirements.md`。
- 阅读 `docs/02-acceptance-criteria.md`。
- 阅读 `docs/03-architecture.md`。
- 阅读 `docs/06-project-state.md`。
- 更新 `tasks/` 目录任务流转规则和当前任务队列。

结论：

- MVP 范围、需求优先级和架构细化已足够支持第一轮实现任务拆分。
- 当前没有实现任务通过 Review & Test Agent 验收，因此没有新增 Done 实现项。
- `IMPL-001` 已进入 Current，Implementation Agent 只能执行该任务。
- `tasks/review.md` 已建立，用于承接已完成但未验收的任务。

任务治理规则：

- Requirement Agent 只能建议新增任务。
- Architect Agent 只能建议拆分任务。
- Implementation Agent 只能执行 Current task。
- Review & Test Agent 只能给出验收结论。
- State Manager Agent / Task Manager 负责移动任务状态。
- State Manager Agent / Task Manager 不执行测试任务；测试执行和验收结论只由 Review & Test Agent 负责。

## 2026-06-03 Review & Test Agent Review: IMPL-001

范围：

- 查看当前 `git status --short` 和 `git diff`。
- 阅读 `docs/02-acceptance-criteria.md`。
- 阅读 `docs/03-architecture.md`。
- 阅读 `tasks/current.md`。
- 阅读 `docs/06-project-state.md`。
- 审查新增后端代码：`src/backend/app/`。
- 审查新增测试：`tests/test_backend_contracts.py`。
- 审查后端依赖配置：`pyproject.toml`。

结论：

- 通过，仅限 `IMPL-001` 的任务范围。
- 当前实现可以标记为完成“后端基础结构、数据模型和 API schema 骨架”。
- 当前实现不能标记为完整 MVP 功能 Done。

验证命令：

```powershell
$env:PYTHONPATH='src/backend'
python -m compileall -q src/backend tests
python -m unittest discover -s tests -v
python -m pip wheel . -w .build-review
```

验证结果：

- `python -m compileall -q src/backend tests`：通过。
- `python -m unittest discover -s tests -v`：通过，4 个测试通过。
- `python -m pip wheel . -w .build-review`：通过，wheel 构建成功。
- 审查产生的临时 `.build-review`、`build/`、`*.egg-info` 和 `__pycache__` 已清理。

Acceptance Criteria 覆盖：

- AC1-AC8、AC10：未满足，当前没有产品功能闭环。
- AC9：Partial。已有 `agent_runs` 和 `agent_run_steps` 模型字段，但没有写入逻辑。
- AC11：Partial。已有 FastAPI、schema、model 和 package 配置，但没有数据库迁移、真实数据库连接、队列和可替换 LLM 配置实现。
- AC13：通过当前骨架检查。外部能力通过 `LLMProvider`、`VectorStore`、`TaskQueue`、`DocumentParser` protocol 隔离，业务 service 未直接依赖具体 SDK。

Blocking Issues：

- 无针对 `IMPL-001` 的 blocking issue。

Non-blocking Issues：

- `docs/02-acceptance-criteria.md` 的“当前不可验收项”仍写着仓库尚无实现代码、测试配置、依赖配置；当前改动已经新增 `pyproject.toml`、`src/backend/app/` 和 `tests/`，后续应更新该段，避免误导新 Agent。
- `DemoDataService.load_demo_data()` 只是占位，返回 `pending` 且 `is_loaded=False`，不能被理解为真实 seed data 加载能力。
- service 层目前主要是 `NotImplementedError`，符合本轮骨架任务，但后续实现业务逻辑时必须补 API 行为测试。

Missing Tests：

- 缺少 `/api/v1/demo-data/status` 和 `/api/v1/demo-data/load` 的 HTTP 层响应测试。
- 缺少 service 方法签名完整性测试。
- 缺少 SQLAlchemy metadata 字段约束、外键关系和 enum 值测试。
- 缺少 package 安装后 import 路径验证测试。

建议：

- Task Manager 可以将 `IMPL-001` 从 `Current` 移动到 `Done`，但 Done 说明必须限定为“后端基础结构、数据模型和 API schema 骨架”。
- 不得将任何完整 MVP 产品功能标记为 Done。

## 2026-06-03 Review & Test Agent Review: IMPL-002

范围：

- 先查看当前 `git status --short`、`git diff --stat` 和 `git diff --`。
- 阅读 `docs/02-acceptance-criteria.md`。
- 阅读 `docs/03-architecture.md`。
- 阅读 `tasks/current.md`。
- 阅读 `docs/06-project-state.md`。
- 审查 demo data 加载实现：`src/backend/app/db/session.py`、`src/backend/app/seed/demo_data.py`、`src/backend/app/services/demo_data_service.py`。
- 审查新增测试：`tests/test_demo_data.py`。

结论：

- 不通过。
- 当前功能不能标记为 Done。
- 主要原因是完整测试套件未通过，`test_demo_data_http_endpoints_use_real_state` 在 Windows 上清理临时 SQLite 文件时触发 `PermissionError: [WinError 32]`，说明测试或应用仍持有数据库文件句柄。

验证命令：

```powershell
$env:PYTHONPATH='src/backend'
python -m compileall -q src/backend tests
python -m unittest discover -s tests -v
```

验证结果：

- `python -m compileall -q src/backend tests`：通过。
- `python -m unittest discover -s tests -v`：失败。共运行 7 个测试，6 个通过，1 个 error。
- 失败测试：`test_demo_data_http_endpoints_use_real_state (test_demo_data.DemoDataTests)`。
- 失败位置：`tests/test_demo_data.py` 的 `tearDown()` 调用 `self.temp_dir.cleanup()` 时无法删除 `demo-test.sqlite3`。
- 错误：`PermissionError: [WinError 32] 另一个程序正在使用此文件，进程无法访问。`
- 本轮测试产生的 `__pycache__` 已清理。

Acceptance Criteria 覆盖：

- AC1：Partial。已有模拟课程资料 chunk 和 source_ref，能加载到数据库；但不支持用户上传真实课程资料，也没有解析失败错误提示。
- AC2：Partial。seed data 包含 3 个模拟学生画像，且字段包含目标、基础水平、偏好和时间预算；但还没有用户创建、选择或编辑画像的正式 API。
- AC3：Partial。seed data 包含数据结构课程、5 个知识点和关系；但测试未通过，不能验收为 Done。
- AC13：未发现本轮引入具体 LLM SDK、向量库 SDK 或任务队列 SDK 到业务 service 中。

Blocking Issues：

- 完整测试套件失败。根据 `docs/02-acceptance-criteria.md` 的总体验收原则，未经实际测试通过的功能不得标记为 Done。

Non-blocking Issues：

- 当前仓库没有 `.gitignore`，测试运行会生成 `__pycache__` 和 `.pyc` 文件；如果后续直接 `git add .`，可能把缓存文件提交进仓库。
- `docs/02-acceptance-criteria.md` 的“当前不可验收项”仍写着仓库尚无实现代码、测试配置、依赖配置，描述已过期。
- `src/backend/app/db/session.py` 使用 `sqlite:///./data/demo.sqlite3` 作为默认数据库 URL，偏离 ADR 中第一阶段业务数据库为 `PostgreSQL` 的方向；作为本地 demo persistence 可以接受，但后续需要明确这是开发/演示默认值，并补正式 PostgreSQL 配置路径。

Missing Tests：

- 缺少对 `concept_relations` 的数量和具体先修链路断言。
- 缺少对 chunk 与 concept 关联正确性的断言。
- 缺少对重复加载后 relation 不重复的幂等性断言。
- 缺少 `load_demo_data()` 部分缺失数据、损坏数据或异常路径的错误处理测试。
- 缺少默认数据库路径 `data/demo.sqlite3` 不存在或目录不可写时的测试。
- 缺少 `.gitignore` / 生成文件不进入版本控制的仓库卫生检查。

建议：

- 修复 Windows 下 HTTP endpoint 测试的 SQLite 文件句柄释放问题后，再重新提交 Review。
- 在修复前不要将 `IMPL-002` 移入 Done。

## 2026-06-03 Review & Test Agent Retest: IMPL-002

范围：

- 用户反馈已修改后，重新执行验证。
- 查看当前 `git status --short` 和 `git diff --stat`。
- 重新运行编译检查和单元测试。

结论：

- 通过。
- 当前 `IMPL-002` 可以标记为 Done，范围限定为“demo data 加载能力”。
- 不代表完整 MVP 产品功能 Done。

验证命令：

```powershell
$env:PYTHONPATH='src/backend'
python -m compileall -q src/backend tests
python -m unittest discover -s tests -v
```

验证结果：

- `python -m compileall -q src/backend tests`：通过。
- `python -m unittest discover -s tests -v`：通过，8 个测试全部通过。
- 已确认此前失败的 `test_demo_data_http_endpoints_use_real_state` 通过。
- 本轮测试产生的 `__pycache__` 已清理。

Acceptance Criteria 覆盖：

- AC1：Partial。`IMPL-002` 已提供模拟课程资料 chunk、source_ref 和数据库加载能力；但真实用户上传、文件解析和失败提示仍未实现，不能把完整 AC1 标记为 Done。
- AC2：Partial。已提供 3 个模拟学生画像，包含学习目标、基础水平、学习偏好和可用时间；但用户创建、选择或编辑画像 API 仍未完成。
- AC3：Partial。已提供数据结构课程、5 个 MVP 知识点、先修/相关关系和演示链路 seed data；正式课程知识点管理 API 仍未完成。

Remaining Issues：

- 当前仓库仍缺少 `.gitignore`，后续运行测试仍可能生成 `__pycache__` / `.pyc`。
- `docs/02-acceptance-criteria.md` 的“当前不可验收项”描述仍过期。
- 默认 SQLite demo database 仍应在后续配置中明确为开发/演示用途，并补正式 PostgreSQL 配置路径。

建议：

- Task Manager 可以将 `IMPL-002` 从 `Current` 移动到 `Done`，但 Done 说明必须限定为“demo data 加载能力”。
- 不得将完整 AC1、AC2、AC3 或完整 MVP 产品功能标记为 Done。

## 2026-06-03 Review & Test Agent Review: IMPL-003

范围：

- 查看当前 `git status --short`、`git diff --stat` 和 `git diff --`。
- 阅读 `tasks/current.md`，确认当前任务为 `IMPL-003: 实现学生画像与课程知识点 API`。
- 阅读 `docs/02-acceptance-criteria.md`。
- 阅读 `docs/03-architecture.md`。
- 审查 `src/backend/app/api/v1/router.py`。
- 审查 `src/backend/app/services/profile_service.py`。
- 审查 `src/backend/app/services/course_service.py`。
- 审查 `tests/test_profile_course_api.py`。

结论：

- 不通过。
- 当前功能不能标记为 Done。
- 功能测试通过，但存在明确架构边界违规：domain service 直接依赖 FastAPI 的 `HTTPException` 和 `status`，并在 service 层执行 HTTP error code 转换。

验证命令：

```powershell
$env:PYTHONPATH='src/backend'
python -m compileall -q src/backend tests
python -m unittest discover -s tests -v
```

验证结果：

- `python -m compileall -q src/backend tests`：通过。
- `python -m unittest discover -s tests -v`：通过，12 个测试全部通过。
- 本轮测试产生的 `__pycache__` 已清理。

Acceptance Criteria 覆盖：

- AC2：Partial。已新增 `GET /api/v1/student-profiles`、`GET /api/v1/student-profiles/{profile_id}`、`POST /api/v1/student-profiles`，测试覆盖 3 个 seed 画像返回和画像创建；但由于架构违规，不能验收为 Done。
- AC3：Partial。已新增 `GET /api/v1/courses/{course_id}/graph`，测试覆盖数据结构课程、5 个 MVP 知识点和关系返回；但由于架构违规，不能验收为 Done。
- AC13：不通过。虽然没有直接依赖 LLM、VectorStore 或 TaskQueue SDK，但 service 层直接依赖 FastAPI，违反 `docs/03-architecture.md` 中 API Layer 负责错误码转换、domain service 不承担 HTTP 层职责的边界。

Blocking Issues：

- `src/backend/app/services/profile_service.py` 在 service 层 import `HTTPException` / `status`，并在 profile 不存在时直接 raise HTTP 404。
- `src/backend/app/services/course_service.py` 在 service 层 import `HTTPException` / `status`，并在 course 不存在时直接 raise HTTP 404。
- 这会把 domain service 绑定到 FastAPI，后续 CLI、worker、测试或其他入口复用 service 时会携带 HTTP 语义，不符合架构文档中 API Layer 负责错误码转换的边界。

Non-blocking Issues：

- `ProfileService.list_demo_profiles()` 当前返回所有 `StudentProfile`，如果默认数据库中已有用户创建的画像，列表会不再只有 3 个 demo profiles；当前测试使用隔离数据库，没有覆盖默认持久库累积数据场景。
- 当前仓库仍缺少 `.gitignore`，后续运行测试仍可能生成 `__pycache__` / `.pyc`。
- `docs/02-acceptance-criteria.md` 的“当前不可验收项”描述仍过期。

Missing Tests：

- 缺少 service 层不 import FastAPI / HTTPException 的架构边界测试。
- 缺少默认持久数据库中已有自定义 profile 时，`GET /student-profiles` 的预期行为测试。
- 缺少创建 profile 后再 list profiles 的行为测试。
- 缺少请求体校验失败时统一错误结构的测试。

建议：

- 将 service 层改为抛出 domain exception，例如 `NotFoundError`，或返回 `None` / result object。
- 在 `router.py` 或 API error handler 中把 domain exception 转换为 `HTTPException` / HTTP status code。
- 增加架构边界测试，确保 `src/backend/app/services/*.py` 不 import `fastapi`。
- 修复后重新提交 Review；在此之前不要将 `IMPL-003` 移入 Done。

## 2026-06-03 Review & Test Agent Retest: IMPL-003

范围：

- 用户反馈已修改后，重新检查 service 层架构边界。
- 重新运行编译检查和完整单元测试。
- 确认 `tests/test_backend_contracts.py` 已加入 service 层不得 import `fastapi` / `httpexception` 的架构边界测试。

结论：

- 通过。
- 当前 `IMPL-003` 可以标记为 Done，范围限定为“学生画像与课程知识点 API”。
- 不代表完整 MVP 产品功能 Done。

验证命令：

```powershell
$env:PYTHONPATH='src/backend'
python -m compileall -q src/backend tests
python -m unittest discover -s tests -v
```

验证结果：

- `python -m compileall -q src/backend tests`：通过。
- `python -m unittest discover -s tests -v`：通过，12 个测试全部通过。
- `src/backend/app/services/*.py` 未再直接 import `fastapi` 或 `HTTPException`。
- 404 转换已移动到 `src/backend/app/api/v1/router.py`。
- 本轮测试产生的 `__pycache__` 已清理。

Acceptance Criteria 覆盖：

- AC2：Partial。`IMPL-003` 已提供学生画像列表、详情和创建 API；能返回 seed data 中 3 个模拟画像，画像响应包含学习目标、基础水平、学习偏好和可用时间。完整 AC2 中更完整的前端选择/编辑体验仍未完成。
- AC3：Partial。`IMPL-003` 已提供课程知识点图查询 API，能返回数据结构课程、5 个 MVP 知识点和知识点关系。完整课程知识点维护能力仍未完成。
- AC13：通过当前任务范围。HTTP 错误码转换位于 API layer，domain service 使用 `NotFoundError`，未直接依赖 FastAPI。

Remaining Issues：

- `ProfileService.list_demo_profiles()` 当前返回所有 `StudentProfile`，如果默认数据库中已有用户创建的画像，列表可能不再只包含 3 个 demo profiles；后续应明确列表 API 是返回所有画像还是仅 demo 画像。
- 当前仓库仍缺少 `.gitignore`，后续运行测试仍可能生成 `__pycache__` / `.pyc`。
- `docs/02-acceptance-criteria.md` 的“当前不可验收项”描述仍过期。

建议：

- Task Manager 可以将 `IMPL-003` 从 `Current` 移动到 `Done`，但 Done 说明必须限定为“学生画像与课程知识点 API”。
- 不得将完整 AC2、AC3 或完整 MVP 产品功能标记为 Done。

## 2026-06-03 State Manager Update After IMPL-001 Review

依据：

- Review & Test Agent 已在本文件中明确给出 `IMPL-001` 通过结论。
- 通过范围仅限“后端基础结构、数据模型和 API schema 骨架”。
- State Manager Agent / Task Manager 未执行测试，只引用 Review & Test Agent 已记录的测试和验收结果。

任务状态更新：

- `IMPL-001` 从 `tasks/current.md` 移入 `tasks/done.md`。
- `tasks/current.md` 当前置为空，不自动批准下一项实现任务。
- `tasks/backlog.md` 标记 `IMPL-002` 和 `IMPL-003` 的 `IMPL-001` 依赖已解除。
- 新增 `PLAN-004`：更新 `docs/02-acceptance-criteria.md` 中已过期的“当前不可验收项”描述。

限制说明：

- 未将完整 MVP、demo data 真实加载、学生画像 API、学习路径、Agent 实际执行、RAG、Quiz、Evaluator、前端或部署标记为 Done。

## 2026-06-03 Task Manager Progression After IMPL-001

依据：

- 用户要求：阶段任务完成后，Task Manager 应继续推进下一阶段任务，将 Backlog 中的下一阶段待实现任务移入 Current。
- `IMPL-001` 已由 Review & Test Agent 验收通过，并已移入 Done。
- `IMPL-002` 的前置依赖 `IMPL-001` 已满足，且需求、验收标准和架构依据明确。

任务状态更新：

- `IMPL-002` 从 `tasks/backlog.md` 移入 `tasks/current.md`。
- `tasks/backlog.md` 保留 `IMPL-003` 及后续任务。
- State Manager Agent / Task Manager 仍不执行测试；`IMPL-002` 完成后必须由 Review & Test Agent 验收。

## 2026-06-03 State Manager Update After IMPL-002 Retest

依据：

- Review & Test Agent 已在本文件中明确给出 `IMPL-002` 复测通过结论。
- 通过范围限定为“demo data 加载能力”。
- State Manager Agent / Task Manager 未执行测试，只引用 Review & Test Agent 已记录的测试和验收结果。

任务状态更新：

- `IMPL-002` 从 `tasks/current.md` 移入 `tasks/done.md`。
- `IMPL-003` 从 `tasks/backlog.md` 移入 `tasks/current.md`，作为下一阶段实现任务。
- `tasks/backlog.md` 保留 `IMPL-004` 及后续任务，并更新 `IMPL-004` 依赖为 `IMPL-001`、`IMPL-002`、`IMPL-003`。

限制说明：

- 未将完整 AC1、AC2、AC3 或完整 MVP 产品功能标记为 Done。
- 未将真实用户上传、文件解析失败提示、用户创建/选择/编辑画像 API、正式课程知识点管理 API、学习路径、Agent 实际执行、RAG、Quiz、Evaluator、前端或部署标记为 Done。

## 2026-06-03 State Manager Update After IMPL-003 Retest

依据：

- Review & Test Agent 已在本文件中明确给出 `IMPL-003` 复测通过结论。
- 通过范围限定为“学生画像与课程知识点 API”。
- State Manager Agent / Task Manager 未执行测试，只引用 Review & Test Agent 已记录的测试和验收结果。

任务状态更新：

- `IMPL-003` 从 `tasks/current.md` 移入 `tasks/done.md`。
- `IMPL-004` 从 `tasks/backlog.md` 移入 `tasks/current.md`，作为下一阶段实现任务。
- `tasks/backlog.md` 保留 `IMPL-005` 及后续任务。

限制说明：

- 未将完整 AC2、AC3 或完整 MVP 产品功能标记为 Done。
- 未将前端选择/编辑体验、完整课程知识点维护能力、学习路径、Agent 实际执行闭环、RAG、Quiz、Evaluator、前端或部署标记为 Done。
