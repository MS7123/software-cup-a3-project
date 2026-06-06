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

## 2026-06-03 Review & Test Agent Review: IMPL-004

范围：

- 查看当前 `git status --short`、`git diff --stat` 和 `git diff --`。
- 阅读 `tasks/current.md`，确认当前任务为 `IMPL-004: 实现学习路径与 Planner Agent 最小流程`。
- 阅读 `docs/02-acceptance-criteria.md`。
- 阅读 `docs/03-architecture.md`。
- 审查 `src/backend/app/services/learning_path_service.py`。
- 审查 `src/backend/app/agents/orchestrator.py`。
- 审查 `src/backend/app/services/agent_run_service.py`。
- 审查 `src/backend/app/api/v1/router.py`。
- 审查 `tests/test_learning_path_api.py`。

结论：

- 通过。
- 当前 `IMPL-004` 可以标记为 Done，范围限定为“学习路径与 Planner Agent 最小流程”。
- 不代表完整 MVP 产品功能 Done。

验证命令：

```powershell
$env:PYTHONPATH='src/backend'
python -m compileall -q src/backend tests
python -m unittest discover -s tests -v
```

验证结果：

- `python -m compileall -q src/backend tests`：通过。
- `python -m unittest discover -s tests -v`：通过，14 个测试全部通过。
- `tests/test_learning_path_api.py` 覆盖学习路径创建、Planner step 记录、路径详情、Agent run 详情和缺失输入 404。
- 本轮测试产生的 `__pycache__` 已清理。

Acceptance Criteria 覆盖：

- AC4：Partial / 当前任务范围通过。`POST /api/v1/learning-paths` 能基于学生画像、课程和目标生成阶段化学习路径；返回步骤、关联知识点、路径依据和 `Planner Agent` rationale。完整 AC4 中更完整的多 Agent 学习流程仍待后续任务扩展。
- AC9：Partial / 当前任务范围通过。已写入并返回 `agent_runs` / `agent_run_steps`，包含 `planner` 的调用顺序、状态、输入摘要、输出摘要和关键决策依据。完整 AC9 要求一次完整学习闭环至少展示 4 个 Agent，仍待后续 `Resource`、`Tutor`、`Quiz`、`Evaluator` 任务补齐。
- AC13：通过当前任务范围。API handler 调用 orchestrator / service，未直接拼学习路径或绕过 service 边界；service / orchestrator 未直接依赖具体 LLM、VectorStore、TaskQueue SDK。
- AC18：通过当前任务范围。Rule-based Planner 逻辑位于 `LearningPathService` / `AgentOrchestrator` 边界内，未写在 API handler 或 frontend。
- AC20：Implementation Boundary Review = Pass。

Blocking Issues：

- 无。

Non-blocking Issues：

- `AgentOrchestrator.run_learning_flow()` 先创建学习路径，再创建 `agent_run`。如果后续 run 记录失败，可能出现有路径但无 run 的不一致状态；当前测试未覆盖该失败路径。后续可考虑把路径创建和 run 记录放入同一 transaction 或增加补偿逻辑。
- 当前 Planner 路径生成按 concept id 顺序遍历知识点，尚未显式使用 `concept_relations` 计算先修顺序；seed data 当前顺序与演示链路一致，因此本任务范围可接受，后续若知识点顺序变化需补排序逻辑。
- `datetime.utcnow()` 触发 Python 3.13 deprecation warning，后续建议改为 timezone-aware UTC。
- 当前仓库仍缺少 `.gitignore`，后续运行测试仍可能生成 `__pycache__` / `.pyc`。

Missing Tests：

- 缺少 run 记录失败时路径/Agent run 一致性的测试。
- 缺少根据 `concept_relations` 而不是 concept id 生成学习顺序的测试。
- 缺少多次创建学习路径后 agent run / path 关联一致性的测试。
- 缺少 `GET /api/v1/agent-runs?student_profile_id=&agent_type=` 列表接口测试；该接口在架构文档中列出，但本轮尚未实现。

建议：

- Task Manager 可以将 `IMPL-004` 从 `Current` 移动到 `Done`，但 Done 说明必须限定为“学习路径与 Planner Agent 最小流程”。
- 不得将完整 AC4、AC9 或完整 MVP 产品功能标记为 Done。

## 2026-06-03 Targeted Boundary Review: IMPL-002 to IMPL-004

范围：

- 本次不是重新验收全部功能，也不要求大规模重构。
- 只针对 `IMPL-002` 到 `IMPL-004` 做轻量 implementation boundary review。
- 检查目标：是否存在明显 hardcoded demo、边界绕过或 API contract 风险。
- 阅读依据：`docs/02-acceptance-criteria.md`、`docs/03-architecture.md`、`docs/06-project-state.md`、`tasks/done.md`、本文件以及相关代码和测试。

结论：

- Pass。
- 允许进入 `IMPL-005`：Yes。
- 本结论只代表边界补审通过，不代表完整 MVP 或完整 AC1-AC13 已完成。

### Checklist

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | `src/backend/app/api/v1/router.py` 只调用 service / orchestrator 并做 HTTP 错误转换；`src/frontend` 仅有 `.gitkeep`，未发现 frontend hardcoded result。 |
| Service/orchestrator boundary | Pass | `ProfileService`、`CourseService`、`LearningPathService` 分别承载画像、课程图、学习路径逻辑；`AgentOrchestrator.run_learning_flow()` 通过 `LearningPathService` 和 `AgentRunService` 接入 Planner 最小流程。 |
| Adapter/provider boundary | N/A | `IMPL-002` 到 `IMPL-004` 未实现 mock LLM / RAG / VectorStore / TaskQueue provider；`tests/test_backend_contracts.py` 已禁止 service 直接 import `openai`、`chroma`、`redis`、`rq`、`fastapi`、`httpexception`。 |
| Hardcoded demo/mock risk | Pass | Demo data 集中在 `src/backend/app/seed/demo_data.py`，由 `DemoDataService` 加载；router 未写死 profiles / concepts / path；Planner 使用数据库中的 profile、course、concepts 生成路径。 |
| API contract stability | Pass | request / response schema 集中在 `src/backend/app/schemas.py`；后续替换 LLM / RAG / VectorStore 大概率可保持 `/api/v1` schema 和 `agent_runs` / `agent_run_steps` 结构稳定。 |

### Findings

1. 文件路径：`src/backend/app/services/learning_path_service.py`
   - 问题：Planner 当前按 `Concept.id` 顺序生成路径，未显式使用 `concept_relations` 计算先修顺序。
   - 影响：如果后续 seed data 或真实课程数据的插入顺序变化，路径顺序可能与先修关系不一致。
   - 最小修复建议：在后续 Planner 增强任务中基于 `concept_relations` 做拓扑排序或至少按 relation-derived order 排序。
   - 是否阻塞进入 `IMPL-005`：No。

2. 文件路径：`src/backend/app/services/profile_service.py`
   - 问题：`list_demo_profiles()` 当前返回所有 `StudentProfile`，不是只返回 demo profiles。
   - 影响：默认持久数据库中若已有用户创建画像，`GET /student-profiles` 可能不再只返回 3 个 demo profiles，和“demo profile list”的命名 / 预期不完全一致。
   - 最小修复建议：明确该 API 是“所有画像列表”还是“demo 画像列表”；若是 demo-only，则加过滤条件或 demo marker。
   - 是否阻塞进入 `IMPL-005`：No。

## 2026-06-03 Review & Test Agent Review: IMPL-005

范围：

- 阅读 `docs/02-acceptance-criteria.md`。
- 阅读 `docs/03-architecture.md`。
- 阅读 `tasks/current.md`，确认当前任务为 `IMPL-005: 实现资源生成、Tutor 问答、Quiz 和 Evaluator 最小闭环`。
- 阅读 `docs/06-project-state.md`。
- 阅读本文件已有 Review 记录。
- 审查 `src/backend/app/agents/rule_based_agents.py`。
- 审查 `src/backend/app/services/resource_service.py`。
- 审查 `src/backend/app/services/tutor_service.py`。
- 审查 `src/backend/app/services/assessment_service.py`。
- 审查 `src/backend/app/services/knowledge_base_service.py`。
- 审查 `src/backend/app/api/v1/router.py`。
- 审查 `src/backend/app/schemas.py`。
- 审查 `tests/test_learning_loop_api.py` 和 `tests/test_backend_contracts.py`。

结论：

- 功能验收：Pass。
- Implementation Boundary Check：Pass。
- 允许 State Manager 移入 Done：Yes。
- 通过范围限定为 `IMPL-005` 的“资源生成、Tutor 问答、Quiz 和 Evaluator 最小闭环”，不代表完整 MVP 前端闭环或完整 AC1-AC13 全部完成。

验证命令：

```powershell
$env:PYTHONPATH='src/backend'
python -m compileall -q src/backend tests
python -m unittest discover -s tests -v
```

验证结果：

- `python -m compileall -q src/backend tests`：通过。
- `python -m unittest discover -s tests -v`：通过，16 个测试全部通过。
- `tests/test_learning_loop_api.py` 覆盖 Resource / Tutor / Quiz / Evaluator 最小闭环、Agent run step 记录和缺失记录 404。
- 本轮测试产生的 `__pycache__` 已清理。

### Implementation Boundary Check

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | `src/backend/app/api/v1/router.py` 只调用 `ResourceService`、`TutorService`、`AssessmentService` 并转换 `NotFoundError` 为 HTTP 404；未在 handler 中生成 resource / tutor answer / quiz / evaluation。`src/frontend` 未实现，无 frontend hardcoded result。 |
| Service/orchestrator boundary | Pass | `ResourceService`、`TutorService`、`AssessmentService` 负责业务编排、持久化和 agent run 记录；rule-based agent 逻辑集中在 `src/backend/app/agents/rule_based_agents.py`。 |
| Adapter/provider boundary | Pass | 当前任务未接入真实外部 LLM / VectorStore / TaskQueue SDK；`KnowledgeBaseService` 通过 service 边界封装 demo chunk search；`tests/test_backend_contracts.py` 禁止 service import `openai`、`chroma`、`redis`、`rq`、`fastapi`、`httpexception`。 |
| Hardcoded demo/mock risk | Pass | Rule-based 输出依赖 DB 中的 `path_item`、`concept`、`document_chunks` 和 request 输入；未发现 router / frontend 写死完整结果。 |
| API contract stability | Pass | 新增响应字段使用既有 schema 扩展：`agent_run_id` 被加入 `GeneratedResourceResponse`、`TutorAskResponse`、`QuizResponse`、`EvaluationResult`；后续替换真实 LLM / RAG / VectorStore 大概率不需要推翻 `/api/v1` contract。 |

Acceptance Criteria 覆盖：

- AC5：Pass for IMPL-005 scope。`POST /api/v1/resources/generate` 能针对 `path_item_id` 生成资源，关联 `learning_path_items`，并返回 `source_refs` 与 `agent_run_id`。
- AC6：Pass for IMPL-005 scope。`POST /api/v1/tutor/ask` 通过 `KnowledgeBaseService` 检索 demo chunks，返回带 source refs 的 grounded answer。
- AC7：Pass for IMPL-005 scope。`POST /api/v1/quizzes/generate` 生成题目、答案、解析、难度和 concept tags。
- AC8：Pass for IMPL-005 scope。`POST /api/v1/quizzes/{quiz_id}/attempts` 返回 score、feedback、mastery updates 和 `agent_run_id`。
- AC9：Partial / current scope pass。Resource、Tutor、Quiz、Evaluator 都写入各自 `agent_runs` / `agent_run_steps`，但完整 MVP 的统一多 Agent run 展示仍可后续增强。

Blocking Issues：

- 无。

Non-blocking Issues：

- Resource / Tutor / Quiz / Evaluator 当前分别创建独立 `agent_run`，不是一个统一 learning-flow run 下的 4 个连续 steps。当前 `IMPL-005` 范围可接受，但后续若要满足“完整学习闭环统一调用顺序展示”，应补统一 run 聚合或 agent run list API。
- `datetime.utcnow()` 仍触发 Python 3.13 deprecation warning，后续可替换为 timezone-aware UTC。

建议：

- Task Manager 可以将 `IMPL-005` 从 `Current` 移入 `Done`，但 Done 说明必须限定为“资源生成、Tutor 问答、Quiz 和 Evaluator 最小闭环”。
- 不得将完整 MVP 前端闭环、真实 RAG / LLM / VectorStore 或完整 AC1-AC13 全部标记为 Done。

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

## Review Output Template: Implementation Boundary Review

后续每个 IMPL-* Review 都必须包含本小节。该模板从 `IMPL-005` 起强制适用，并建议用于 `IMPL-002` 到 `IMPL-004` 的补审。

### Implementation Boundary Review

| 检查项 | 结论 | 证据 | 严重级别 |
|---|---|---|---|
| Demo data 是否集中在 seed / fixture / demo data service 中 | Pass / Needs Fix / Blocking | 文件、测试或代码引用 |  |
| Mock provider 是否实现正式 adapter / protocol 契约 | Pass / Needs Fix / Blocking | 文件、测试或代码引用 |  |
| Rule-based logic 是否隔离在 Agent / strategy / service 边界内 | Pass / Needs Fix / Blocking | 文件、测试或代码引用 |  |
| API handler 是否只负责 request / response、依赖注入、错误转换和调用 service | Pass / Needs Fix / Blocking | 文件、测试或代码引用 |  |
| Frontend 是否只消费 API、未硬编码核心 demo result | Pass / Needs Fix / Blocking | 文件、测试或代码引用 |  |
| Service / adapter / orchestrator 契约是否保持清晰 | Pass / Needs Fix / Blocking | 文件、测试或代码引用 |  |
| 替换真实 LLM / RAG / VectorStore 时是否不破坏现有契约 | Pass / Needs Fix / Blocking | 文件、测试或代码引用 |  |

Boundary 结论：

- `Pass` / `Needs Fix` / `Blocking`
- 是否允许任务进入 Done：
- 如需修复，建议拆分任务：

判定规则：

- `Pass`：边界清晰，允许进入 Done。
- `Needs Fix`：存在局部边界问题，修复后复测。
- `Blocking`：存在 hardcoded demo、handler 承载业务规则、frontend 模拟核心结果、service 直连 provider 或破坏 adapter 契约等问题，不得进入 Done。

## Implementation Boundary Check

- Controller/frontend business logic: Pass / Needs Fix / N/A
- Service/orchestrator boundary: Pass / Needs Fix / N/A
- Adapter/provider boundary: Pass / Needs Fix / N/A
- Hardcoded demo/mock risk: Pass / Needs Fix / N/A
- API contract stability: Pass / Needs Fix / N/A

Conclusion: Pass / Needs Fix / Blocking

## 2026-06-03 State Manager Update After IMPL-004 Review

依据：

- Review & Test Agent 已在本文件中明确给出 `IMPL-004` 通过结论。
- 通过范围限定为“学习路径与 Planner Agent 最小流程”。
- Targeted Boundary Review 对 `IMPL-002` 到 `IMPL-004` 的结论为 `Pass`。
- State Manager Agent / Task Manager 未执行测试，只引用 Review & Test Agent 已记录的测试和验收结果。

任务状态更新：

- `IMPL-004` 从 `tasks/current.md` 移入 `tasks/done.md`。
- `IMPL-005` 从 `tasks/backlog.md` 移入 `tasks/current.md`，作为下一阶段实现任务。
- `tasks/backlog.md` 保留 `IMPL-006` 及后续任务。

限制说明：

- 未将完整 AC4、AC9 或完整 MVP 产品功能标记为 Done。
- 未将 Resource / Tutor / Quiz / Evaluator、RAG、前端或部署标记为 Done。

## 2026-06-03 State Manager Update After IMPL-005 Review

依据：

- Review & Test Agent 已在本文件中明确给出 `IMPL-005` 通过结论。
- 通过范围限定为“资源生成、Tutor 问答、Quiz 和 Evaluator 最小闭环”。
- `Implementation Boundary Check` 结论为 `Pass`。
- State Manager Agent / Task Manager 未执行测试，只引用 Review & Test Agent 已记录的测试和验收结果。

任务状态更新：

- `IMPL-005` 从 `tasks/current.md` 移入 `tasks/done.md`。
- `IMPL-006` 从 `tasks/backlog.md` 移入 `tasks/current.md`，作为下一阶段实现任务。
- `tasks/backlog.md` 保留 `IMPL-007` 及后续任务，并新增 `REFACTOR-003` 跟踪统一 learning-flow run 聚合问题。

限制说明：

- 未将完整前端学习闭环、真实 RAG / VectorStore、真实 LLM provider、统一多 Agent run 聚合展示、部署配置或完整 MVP 产品功能标记为 Done。

## 2026-06-03 Review & Test Agent Review: IMPL-006

范围：

- 阅读 `docs/02-acceptance-criteria.md`。
- 阅读 `docs/03-architecture.md`。
- 阅读 `tasks/current.md`，确认当前任务为 `IMPL-006: 初始化前端学生端工程`。
- 阅读 `docs/06-project-state.md`。
- 阅读本文件已有 Review 记录。
- 查看当前 `git status --short` 和 `git diff`。
- 审查 `src/frontend/package.json`、`src/frontend/vite.config.ts`、`src/frontend/src/api/client.ts`、`src/frontend/src/api/types.ts`、`src/frontend/src/App.tsx`。

结论：

- 功能验收：Pass。
- Implementation Boundary Check：Pass。
- 允许 State Manager 移入 Done：Yes。
- 通过范围限定为 `IMPL-006` 的“前端学生端工程初始化和基础页面骨架”，不代表完整 MVP 产品、真实 RAG / LLM / VectorStore、部署配置或完整 AC1-AC13 全部完成。

验证命令：

```powershell
cd src/frontend
npm ci
npm run build
cd ../..
$env:PYTHONPATH='src/backend'
python -m compileall -q src/backend tests
python -m unittest discover -s tests -v
```

验证结果：

- `npm ci`：通过，安装 137 个 package，`found 0 vulnerabilities`。
- `npm run build`：通过，`tsc --noEmit && vite build` 成功，30 个 module transformed。
- `python -m compileall -q src/backend tests`：通过。
- `python -m unittest discover -s tests -v`：通过，16 个测试全部通过。
- 本轮验证产生的 `src/frontend/dist`、`src/frontend/node_modules` 和 `__pycache__` 已清理。

### Implementation Boundary Check

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | `src/frontend/src/App.tsx` 通过 `api` client 调用后端并展示返回结果；学习路径、资源、Tutor answer、Quiz、Evaluation、Agent run 均来自 API response，未在 frontend 拼完整业务结果。 |
| Service/orchestrator boundary | Pass | 当前任务是 frontend 初始化；后端业务仍通过既有 `/api/v1` service / orchestrator 入口承载，frontend 不直接调用数据库、provider 或 service 内部实现。 |
| Adapter/provider boundary | N/A | 当前任务未新增 mock LLM / RAG / VectorStore / TaskQueue provider；frontend 只通过 HTTP API contract 接入后端。 |
| Hardcoded demo/mock risk | Pass | `App.tsx` 仅包含 profile type 展示 label、默认目标/问题输入文案和 UI empty state；未硬编码 3 个画像列表、5 个知识点、学习路径、resource、quiz answer、evaluation result 或 agent steps。 |
| API contract stability | Pass | `src/frontend/src/api/client.ts` 集中封装 `/api/v1` endpoints；`src/frontend/src/api/types.ts` 与当前后端 Pydantic response schema 对齐，后续替换真实 LLM / RAG / VectorStore 大概率不需要推翻 frontend request / response contract。 |

Acceptance Criteria 覆盖：

- AC10：Partial / current scope pass。前端工程可 build，基础学生端 console 能覆盖画像选择、学习路径查看、资源查看、问答、测验、评价和 Agent run 摘要展示的模块边界；但尚未做浏览器端联调、E2E 自动化或完整演示验收。
- AC13：Pass for current scope。frontend 没有直接访问 provider、数据库、向量库、Redis 或 LLM SDK。
- AC16：Pass for current scope。frontend 未维护本地 demo data 副本。
- AC18：Pass for current scope。frontend 未实现 Planner / Tutor / Quiz / Evaluator rule-based logic。
- AC20：Implementation Boundary Check = Pass。

Blocking Issues：

- 无。

Non-blocking Issues：

- 当前未运行真实浏览器 E2E；`npm run build` 只能证明 TypeScript 和生产构建通过，不能证明所有按钮在实际后端启动后完成端到端交互。
- `App.tsx` 默认选择 `flow.learning_path.items[0]` 作为当前资源/测验节点，当前作为骨架可接受；后续正式前端任务需要补路径节点选择交互。
- 后端测试仍出现 `datetime.utcnow()` deprecation warning 和 `StarletteDeprecationWarning`，不是本轮 frontend 初始化的阻塞项。

Missing Tests：

- 缺少 frontend unit / component test，例如 API client mock、loading/error state、空数据状态。
- 缺少 Playwright 或等价 E2E，覆盖 demo data load、profile selection、learning path generation、resource/tutor/quiz/evaluator 和 agent run trace。
- 缺少前后端联调 smoke test，验证 Vite proxy `/api` 与本地 FastAPI 服务同时运行时的实际交互。

建议：

- Task Manager 可以将 `IMPL-006` 从 `Current` 移入 `Done`，但 Done 说明必须限定为“前端学生端工程初始化和基础页面骨架”。
- 不得将完整 AC10、完整学生端闭环、部署配置、真实 RAG / LLM / VectorStore 或完整 MVP 产品功能标记为 Done。

## 2026-06-03 State Manager Update After IMPL-006 Review

依据：

- Review & Test Agent 已在本文件中明确给出 `IMPL-006` 通过结论。
- 通过范围限定为“前端学生端工程初始化和基础页面骨架”。
- `Implementation Boundary Check` 结论为 `Pass`。
- State Manager Agent / Task Manager 未执行测试，只引用 Review & Test Agent 已记录的测试和验收结果。

任务状态更新：

- `IMPL-006` 从 `tasks/current.md` 移入 `tasks/done.md`。
- `IMPL-007` 从 `tasks/backlog.md` 移入 `tasks/current.md`，作为下一阶段实现任务。
- `tasks/backlog.md` 保留 `IMPL-008` 及后续任务，并新增 `TEST-001` 跟踪前后端联调 smoke test 和 browser E2E 缺口。

限制说明：

- 未将完整学生端 MVP 页面、浏览器联调、E2E 自动化、部署配置、真实 RAG / LLM / VectorStore 或完整 MVP 产品功能标记为 Done。

## 2026-06-03 Review & Test Agent Review: IMPL-007

范围：

- 阅读 `docs/02-acceptance-criteria.md`。
- 阅读 `docs/03-architecture.md`。
- 阅读 `tasks/current.md`，确认当前任务为 `IMPL-007: 实现学生端 MVP 页面`。
- 阅读 `docs/06-project-state.md`。
- 阅读本文件已有 Review 记录。
- 查看当前 `git status --short` 和 `git diff`。
- 审查 `src/frontend/src/App.tsx`、`src/frontend/src/styles.css`、`src/frontend/src/api/client.ts`、`src/frontend/src/api/types.ts`。
- 使用 Playwright 对临时后端 + Vite 前端执行 browser smoke。

结论：

- 功能验收：Pass。
- Implementation Boundary Check：Pass。
- 允许 State Manager 移入 Done：Yes。
- 通过范围限定为 `IMPL-007` 的“学生端 MVP 页面关键交互”，不代表部署配置、真实 RAG / LLM / VectorStore 或完整 AC1-AC13 全部完成。

验证命令：

```powershell
cd src/frontend
npm ci
npm run build
cd ../..
$env:PYTHONPATH='src/backend'
python -m compileall -q src/backend tests
python -m unittest discover -s tests -v
python -m playwright install chromium
python C:\Users\32544\.agents\skills\webapp-testing\scripts\with_server.py --server "powershell -NoProfile -Command `$env:PYTHONPATH='src/backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000" --port 8000 --server "powershell -NoProfile -Command cd src/frontend; npm run dev -- --port 5173" --port 5173 --timeout 45 -- python .review_tmp_impl007_smoke.py
```

验证结果：

- `npm ci`：通过，安装 137 个 package，`found 0 vulnerabilities`。
- `npm run build`：通过，`tsc --noEmit && vite build` 成功，30 个 module transformed。
- `python -m compileall -q src/backend tests`：通过。
- `python -m unittest discover -s tests -v`：通过，16 个测试全部通过。
- Playwright browser smoke：通过。临时启动 FastAPI `127.0.0.1:8000` 和 Vite `127.0.0.1:5173` 后，完成 demo data refresh、profile display、course graph display、learning path generation、path node selection、resource generation、Tutor Q&A、Quiz generation/submission、Evaluator feedback 和 Agent run trace 检查。
- 首次 browser smoke 因本机缺少 Playwright Chromium 未运行，已执行 `python -m playwright install chromium` 后复测通过。
- 本轮验证产生的临时 smoke 脚本、`src/frontend/dist`、`src/frontend/node_modules`、`data/demo.sqlite3` 和 `__pycache__` 已清理。

### Implementation Boundary Check

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | `src/frontend/src/App.tsx` 通过 `api` client 发起 demo data、profile、course graph、learning path、resource、tutor、quiz、attempt、agent run 请求；页面只做状态管理、选择交互和展示，没有在 frontend 生成学习路径、resource、quiz answer、evaluation result 或 agent steps。 |
| Service/orchestrator boundary | Pass | 当前 frontend 仍通过 `/api/v1` 访问后端能力；学习路径由 `api.createLearningPath()` 触发，资源/Tutor/Quiz/Evaluator 分别通过后端 endpoint 返回结果，没有绕过 service/orchestrator。 |
| Adapter/provider boundary | N/A | 当前任务未新增 mock LLM / RAG / VectorStore / TaskQueue provider；frontend 只依赖 HTTP API client，不直接接入外部 provider。 |
| Hardcoded demo/mock risk | Pass | `profileLabels` 和 `agentTone` 仅为展示 label；默认 goal/question 只是可编辑输入初值。未硬编码 3 个画像列表、5 个知识点、学习路径、resource、quiz answer、evaluator feedback 或 agent steps。 |
| API contract stability | Pass | `src/frontend/src/api/client.ts` 集中封装 `/api/v1` endpoints，`src/frontend/src/api/types.ts` 与当前后端 schema 对齐；后续替换真实 LLM / RAG / VectorStore 大概率不需要推翻 frontend request / response contract。 |

Acceptance Criteria 覆盖：

- AC10：Pass for IMPL-007 scope。页面已覆盖画像选择、学习路径查看、当前节点选择、资源查看、Tutor 问答、Quiz 提交、评价反馈和 Agent run 摘要展示，并经 browser smoke 走通关键交互。
- AC13：Pass for current scope。frontend 未直接访问 provider、数据库、向量库、Redis 或 LLM SDK。
- AC16：Pass for current scope。frontend 未维护本地 demo data 副本。
- AC18：Pass for current scope。frontend 未实现 Planner / Tutor / Quiz / Evaluator rule-based logic。
- AC20：Implementation Boundary Check = Pass。

Blocking Issues：

- 无。

Non-blocking Issues：

- `src/frontend/src/App.tsx` 的 `PathItemCard` 使用 `Step {item.order_index + 1}`。Browser smoke 观察到后端返回的 path item 已显示为阶段 1-5，但 UI step label 显示为 `STEP 2` 到 `STEP 6`，存在步骤编号偏移。当前不影响关键交互闭环，但会影响演示观感。
- 后端测试仍出现 `datetime.utcnow()` deprecation warning 和 `StarletteDeprecationWarning`，不是本轮 frontend 页面任务的阻塞项。
- 当前 browser smoke 是临时脚本，不是持久化测试套件；后续仍应纳入正式 E2E。

Missing Tests：

- 缺少提交到仓库的 Playwright E2E 测试，用于持续覆盖 IMPL-007 smoke 流程。
- 缺少 frontend component/unit tests 覆盖 loading/error/empty state、profile/path node selection reset 行为。
- 缺少 UI step numbering 的断言，当前 off-by-one 问题未被自动测试捕获。

建议：

- Task Manager 可以将 `IMPL-007` 从 `Current` 移入 `Done`，但 Done 说明必须限定为“学生端 MVP 页面关键交互”。
- 建议后续小修 `PathItemCard` step label，避免展示 `STEP 2` 到 `STEP 6`。
- 不得将部署配置、真实 RAG / LLM / VectorStore、正式 E2E 测试套件或完整 MVP 产品功能标记为 Done。

## 2026-06-03 State Manager Update After IMPL-007 Review

依据：

- Review & Test Agent 已在本文件中明确给出 `IMPL-007` 通过结论。
- 通过范围限定为“学生端 MVP 页面关键交互”。
- `Implementation Boundary Check` 结论为 `Pass`。
- State Manager Agent / Task Manager 未执行测试，只引用 Review & Test Agent 已记录的测试和验收结果。

任务状态更新：

- `IMPL-007` 从 `tasks/current.md` 移入 `tasks/done.md`。
- `IMPL-008` 从 `tasks/backlog.md` 移入 `tasks/current.md`，作为下一阶段实现任务。
- `tasks/backlog.md` 保留 `IMPL-009` 及后续任务，并新增 `FIX-002` 跟踪学生端步骤标签 off-by-one 问题。

限制说明：

- 未将正式 E2E 测试套件、部署配置、真实 RAG / LLM / VectorStore 或完整 MVP 产品功能标记为 Done。

## 2026-06-03 Review & Test Agent Review: IMPL-008

范围：

- 阅读 `docs/02-acceptance-criteria.md`。
- 阅读 `docs/03-architecture.md`。
- 阅读 `tasks/current.md`，确认当前任务为 `IMPL-008: 添加自动化测试与基础验证脚本`。
- 阅读 `docs/06-project-state.md`。
- 阅读本文件已有 Review 记录。
- 查看当前 `git status --short` 和 `git diff`。
- 审查 `scripts/verify.ps1` 和 `scripts/frontend-smoke.ps1`。
- 运行 `./scripts/verify.ps1`。

结论：

- 功能验收：Needs Fix。
- Implementation Boundary Check：Pass。
- 允许 State Manager 移入 Done：No。
- 原因：自动化入口可运行，且没有破坏 service / adapter / frontend 边界；但当前 `frontend-smoke.ps1` 只通过 HTTP 直接调用 `/api/v1` 验证学习闭环，前端部分仅检查 Vite 页面包含 React root，未驱动浏览器或前端 UI 完成学生端关键流程，因此没有满足本任务“补最小前端 E2E / smoke 测试，覆盖当前学生端关键闭环”的要求。

验证命令：

```powershell
./scripts/verify.ps1
```

验证结果：

- `Python compile check`：通过。
- `Backend unit tests`：通过，16 个测试全部通过。
- `Python dependency check`：通过，`No broken requirements found`。
- `Backend wheel build`：通过。
- `Frontend dependency install`：通过，安装 137 个 package，`found 0 vulnerabilities`。
- `Frontend production build`：通过，`tsc --noEmit && vite build` 成功，30 个 module transformed。
- `Frontend/backend smoke`：通过。输出 `FrontendStatus = 200`、`Profiles = 3`、`Concepts = 5`、`PathItems = 5`、`AgentRunsChecked = 5`。
- 本轮验证产生的 `src/frontend/node_modules` 已由 Review & Test Agent 清理；`.build-verify`、`dist`、`__pycache__` 等脚本自身已清理。

### Implementation Boundary Check

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | `scripts/frontend-smoke.ps1` 通过 `/api/v1` 调用现有 backend contract；未修改 router 或 frontend 业务代码，也未在测试中向生产 frontend 注入业务结果。 |
| Service/orchestrator boundary | Pass | smoke 通过 `POST /learning-paths`、`POST /resources/generate`、`POST /tutor/ask`、`POST /quizzes/generate`、`POST /quizzes/{id}/attempts` 验证既有 service/orchestrator 输出，没有绕过 service 直接写数据库。 |
| Adapter/provider boundary | N/A | 当前任务只新增验证脚本，未新增 mock LLM / RAG / VectorStore / TaskQueue provider。 |
| Hardcoded demo/mock risk | Pass | 脚本使用 `POST /api/v1/demo-data/load` 加载 demo data，并使用 API 返回的 profile、course、path item、quiz 等 id 继续流程；没有在生产代码散落 demo data。 |
| API contract stability | Pass | `scripts/frontend-smoke.ps1` 只依赖既有 `/api/v1` request / response contract；没有为测试便利修改 schema、service contract 或 frontend API client。 |

Acceptance Criteria 覆盖：

- AC1-AC13：Partial / test infrastructure scope only。`verify.ps1` 能复用地运行 backend unit、dependency check、wheel build、frontend build 和 smoke 验证，但不代表完整产品 AC1-AC13 全部完成。
- AC10：Needs Fix for IMPL-008 scope。已有前端 build 与前端服务 root 检查，但缺少浏览器或 UI-level smoke 来覆盖画像选择、路径生成、资源、Tutor、Quiz、Evaluator、Agent trace 的页面交互。
- AC20：Pass。Review 已包含 Implementation Boundary Check。

Blocking Issues：

- 无架构或边界类 Blocking issue。

Non-blocking Issues：

- `scripts/verify.ps1` 默认运行 `npm ci` 后会留下 `src/frontend/node_modules`，脚本清理逻辑清掉了 build artifact 和 `dist`，但没有清理 `node_modules`；由于仓库仍缺少 `.gitignore`，运行验证后会污染 `git status`。本轮 Review 已手动清理。
- `scripts/frontend-smoke.ps1` 的 `Stop-PortOwner` 会强制停止默认端口 `8123` / `5174` 的占用进程；默认端口冲突概率低，但后续可以改为先失败提示或只清理本脚本启动的进程。
- smoke 只检查 frontend HTML root，没有检查 React hydrate 后的 DOM、按钮、状态切换或 console error。

Missing Tests：

- 缺少正式浏览器/UI-level smoke 或 Playwright E2E，用于覆盖 IMPL-007 已验证过的学生端页面关键交互。
- 缺少 frontend UI 断言，例如 profile/path node selection、resource/tutor/quiz/evaluator 的页面结果展示。
- 缺少对已知 `PathItemCard` step numbering off-by-one 的自动化断言。

建议：

- 在 `scripts/frontend-smoke.ps1` 中加入 Playwright 或等价浏览器驱动，复用 IMPL-007 的关键路径：load demo data、选择 profile、create path、选择 path node、generate resource、ask tutor、generate quiz、submit answer、检查 evaluator 和 agent run trace。
- 或新增独立 `scripts/frontend-e2e.ps1` / `tests/e2e`，并由 `scripts/verify.ps1` 默认调用。
- 在完成最小 UI smoke 前，不建议 State Manager 将 `IMPL-008` 移入 Done。

## 2026-06-04 Review & Test Agent Retest: IMPL-008

范围：

- 用户反馈已修改后，重新复测 `IMPL-008`。
- 查看当前 `git status --short` 和 `git diff`。
- 复查 `scripts/verify.ps1`、`scripts/frontend-smoke.ps1`。
- 复查新增前端 smoke 配置与测试：`src/frontend/playwright.config.ts`、`src/frontend/tests/student-loop.spec.ts`。
- 复查 `src/frontend/package.json`、`src/frontend/vite.config.ts`、`src/frontend/src/App.tsx` 中与 smoke test 相关的改动。
- 运行 `./scripts/verify.ps1`。

结论：

- 功能验收：Pass。
- Implementation Boundary Check：Pass。
- 允许 State Manager 移入 Done：Yes。
- 通过范围限定为 `IMPL-008` 的“自动化测试与基础验证脚本”，不代表部署配置、真实 RAG / LLM / VectorStore 或完整 MVP 产品功能全部完成。

验证命令：

```powershell
./scripts/verify.ps1
```

验证结果：

- `Python compile check`：通过。
- `Backend unit tests`：通过，16 个测试全部通过。
- `Python dependency check`：通过，`No broken requirements found`。
- `Backend wheel build`：通过。
- `Frontend dependency install`：通过，安装 140 个 package，`found 0 vulnerabilities`。
- `Frontend production build`：通过，`tsc --noEmit && vite build` 成功，30 个 module transformed。
- `Frontend/backend smoke`：通过。`npm run test:smoke -- --workers=1` 执行 Playwright，`tests/student-loop.spec.ts` 1 个测试通过。
- smoke 输出：`FrontendStatus = 200`、`BrowserSmoke = Passed`、`BackendPort = 8123`、`FrontendPort = 5174`。
- 脚本清理验证通过：未残留 `src/frontend/node_modules`、`src/frontend/dist`、`src/frontend/test-results`、`src/frontend/playwright-report`、`.build-verify`、`data/demo.sqlite3` 或 `__pycache__`。

### Implementation Boundary Check

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | `src/frontend/tests/student-loop.spec.ts` 通过真实 UI 操作按钮、输入框和页面断言完成学习闭环；生产 frontend 只新增 `data-testid` 和 step label 修正，未在 frontend 硬编码业务结果。 |
| Service/orchestrator boundary | Pass | `scripts/frontend-smoke.ps1` 启动临时 FastAPI 和 Vite，Playwright 通过页面触发既有 `/api/v1` contract；后端仍经 service / orchestrator 处理 learning path、resource、tutor、quiz、evaluation、agent run。 |
| Adapter/provider boundary | N/A | 当前任务只新增验证脚本和 Playwright smoke，未新增 mock LLM / RAG / VectorStore / TaskQueue provider。 |
| Hardcoded demo/mock risk | Pass | smoke 通过 UI 点击 `load-demo-button` 触发 `/demo-data/load`，后续使用页面展示与 API 返回结果；测试中没有把 demo profiles、concepts、path、quiz answer、evaluator result 或 agent steps 写入生产逻辑。 |
| API contract stability | Pass | `VITE_PROXY_TARGET` 只改变 Vite dev proxy target，frontend API path 仍保持 `/api/v1`；测试依赖既有 request / response schema，没有要求修改 API contract。 |

Acceptance Criteria 覆盖：

- AC10：Pass for IMPL-008 scope。Playwright smoke 已覆盖 demo data load、profile selection、learning path creation、path node selection、resource generation、Tutor Q&A、Quiz generation、answer submission、Evaluator feedback 和 Agent run trace rendering。
- AC11：Partial / test infrastructure scope。`verify.ps1` 覆盖 backend compile、unit tests、dependency check、wheel build、frontend build 和 smoke 验证；不代表数据库迁移、正式 PostgreSQL、队列和真实 LLM 配置已完成。
- AC20：Pass。已执行 Implementation Boundary Check。

Blocking Issues：

- 无。

Non-blocking Issues：

- Playwright 配置在 Windows 默认使用 `msedge` channel；当前环境验证通过，但若其他机器未安装 Edge，需要设置 `PLAYWRIGHT_CHANNEL` 或先安装 Playwright Chromium。
- `scripts/frontend-smoke.ps1` 使用固定默认端口 `8123` / `5174`，端口被占用时会失败并提示，而不是自动换端口；当前作为可复用 smoke 入口可接受。
- 后端测试仍出现 `datetime.utcnow()` deprecation warning 和 `StarletteDeprecationWarning`，不是本轮测试脚本任务的阻塞项。

Missing Tests：

- 尚未有覆盖失败路径的 frontend E2E，例如后端不可用、demo data load 失败、quiz submit 失败。
- 尚未有多浏览器或移动视口测试；当前 smoke 只覆盖默认 Chromium/Edge headless。

建议：

- Task Manager 可以将 `IMPL-008` 从 `Current` 移入 `Done`，但 Done 说明必须限定为“自动化测试与基础验证脚本”。
- 不得将部署配置、真实 RAG / LLM / VectorStore、完整生产级测试矩阵或完整 MVP 产品功能标记为 Done。

## 2026-06-04 State Manager Update After IMPL-008 Retest

依据：

- Review & Test Agent 已在本文件中明确给出 `IMPL-008` 复测通过结论。
- 通过范围限定为“自动化测试与基础验证脚本”。
- `Implementation Boundary Check` 结论为 `Pass`。
- State Manager Agent / Task Manager 未执行测试，只引用 Review & Test Agent 已记录的测试和验收结果。

任务状态更新：

- `IMPL-008` 从 `tasks/current.md` 移入 `tasks/done.md`。
- `IMPL-009` 从 `tasks/backlog.md` 移入 `tasks/current.md`，作为下一阶段实现任务。
- `tasks/backlog.md` 移除已被复测覆盖的旧测试缺口项，并新增 `TEST-002`、`CONFIG-001` 跟踪 IMPL-008 Review 留下的非阻塞问题。

限制说明：

- 未将部署配置、真实 RAG / LLM / VectorStore、完整生产级测试矩阵或完整 MVP 产品功能标记为 Done。

## 2026-06-04 Review & Test Agent Review: IMPL-009

范围：

- 阅读 `docs/02-acceptance-criteria.md`。
- 阅读 `docs/03-architecture.md`。
- 阅读 `tasks/current.md`，确认当前任务为 `IMPL-009: 添加部署配置`。
- 阅读 `docs/06-project-state.md`。
- 阅读本文件已有 Review 记录。
- 查看当前 `git status --short` 和 `git diff`。
- 审查 `deployment/README.md`、`deployment/local.env.example`、`scripts/run-local.ps1`。
- 运行 `./scripts/verify.ps1`。
- 运行 `./scripts/run-local.ps1 -SmokeOnly -BackendPort 8231 -FrontendPort 5231`。

结论：

- 功能验收：Pass。
- Implementation Boundary Check：Pass。
- 允许 State Manager 移入 Done：Yes。
- 通过范围限定为 `IMPL-009` 的“本地部署与演示运行配置”，不代表生产级部署、数据库迁移、Redis/RQ、真实 LLMProvider、真实 VectorStore 或完整 MVP 产品功能全部完成。

验证命令：

```powershell
./scripts/verify.ps1
./scripts/run-local.ps1 -SmokeOnly -BackendPort 8231 -FrontendPort 5231
```

验证结果：

- `./scripts/verify.ps1`：通过。
  - Python compile check：通过。
  - Backend unit tests：通过，16 个测试全部通过。
  - `pip check`：通过，`No broken requirements found`。
  - Backend wheel build：通过。
  - Frontend `npm ci`：通过，安装 140 个 package，`found 0 vulnerabilities`。
  - Frontend production build：通过。
  - Playwright browser smoke：通过，`tests/student-loop.spec.ts` 1 个测试通过。
- `./scripts/run-local.ps1 -SmokeOnly -BackendPort 8231 -FrontendPort 5231`：通过。
  - 输出 `BackendUrl = http://127.0.0.1:8231`。
  - 输出 `FrontendUrl = http://127.0.0.1:5231`。
  - 输出 `DatabaseUrl = sqlite:///./data/demo.sqlite3`。
  - 输出 `DemoDataLoaded = True`。
- 本轮验证产生的 `src/frontend/node_modules`、`data/demo.sqlite3` 和 `__pycache__` 已清理；未发现残留项目内 backend/frontend 测试进程。

### Implementation Boundary Check

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | `scripts/run-local.ps1` 只启动 backend/frontend、检查端口、设置环境变量和请求 demo data load；未修改 router 或 frontend 业务逻辑。 |
| Service/orchestrator boundary | Pass | demo data 通过 `POST /api/v1/demo-data/load` 进入既有 `DemoDataService`；脚本不直接写数据库、不拼 learning path、不生成 quiz/evaluation。 |
| Adapter/provider boundary | N/A | 当前任务只新增本地部署文档和 PowerShell 启动脚本，未新增 mock LLM / RAG / VectorStore / TaskQueue provider。 |
| Hardcoded demo/mock risk | Pass | `deployment/README.md` 明确 SQLite 仅用于本地开发和比赛演示；demo data 未写入部署脚本，仍通过后端 API 加载。 |
| API contract stability | Pass | 前端仍使用 `/api/v1`；`VITE_PROXY_TARGET` 仅配置 Vite dev proxy，不改变 request / response schema。 |

Acceptance Criteria 覆盖：

- AC11：Partial / current scope pass。已补本地演示运行说明、环境变量样例、frontend proxy 配置说明和 `run-local.ps1`；但数据库迁移、正式 PostgreSQL 配置、Redis/RQ、真实 LLMProvider 和真实 VectorStore 仍未完成。
- AC13：Pass for current scope。部署层没有让业务 service 直接依赖具体外部 SDK。
- AC20：Pass。已执行 Implementation Boundary Check。

Blocking Issues：

- 无。

Non-blocking Issues：

- `deployment/local.env.example` 第 2 行写明“current scripts read process environment variables”，但 `scripts/run-local.ps1` 当前主要通过参数接收 host、port 和 database URL，并不会自动读取 `BACKEND_PORT`、`FRONTEND_PORT` 等环境变量。实际运行不受影响，因为 README 同时给出了参数用法；建议后续统一文档表述或让脚本显式读取环境变量默认值。
- `deployment/README.md` 把 `uvicorn` 作为前置条件说明，但 `pyproject.toml` 当前未声明 `uvicorn` 依赖。当前环境验证通过；后续若希望一条 `python -m pip install -e .` 后即可运行本地 demo，应把 ASGI server 依赖纳入 dev/deploy extras 或文档明确安装命令。
- `run-local.ps1 -SmokeOnly` 会留下默认 `data/demo.sqlite3`；本轮 Review 已手动清理。后续可考虑为 smoke 增加临时数据库参数或清理提示。

Missing Tests：

- 缺少对 `run-local.ps1` 的持久化自动化测试；当前由 Review & Test Agent 手动运行 `-SmokeOnly` 验证。
- 缺少非 Windows 环境部署脚本或说明；当前明确为 Windows PowerShell。
- 缺少生产级部署测试，例如 PostgreSQL、Redis/RQ、真实 provider 配置和迁移验证。

建议：

- Task Manager 可以将 `IMPL-009` 从 `Current` 移入 `Done`，但 Done 说明必须限定为“本地部署与演示运行配置”。
- 不得将生产级部署、数据库迁移、Redis/RQ、真实 LLMProvider、真实 VectorStore 或完整 MVP 产品功能标记为 Done。

## 2026-06-04 State Manager Update After IMPL-009 Review

依据：

- Review & Test Agent 已在本文件中明确给出 `IMPL-009` 通过结论。
- 通过范围限定为“本地部署与演示运行配置”。
- `Implementation Boundary Check` 结论为 `Pass`。
- State Manager Agent / Task Manager 未执行测试，只引用 Review & Test Agent 已记录的测试和验收结果。

任务状态更新：

- `IMPL-009` 从 `tasks/current.md` 移入 `tasks/done.md`。
- 当前已无新的 `IMPL-*` 待实现任务，转入文档与仓库治理阶段。
- `PLAN-004` 从 `tasks/backlog.md` 移入 `tasks/current.md`，用于修正 `docs/02-acceptance-criteria.md` 的过期描述。

限制说明：

- 未将生产级部署、数据库迁移、Redis/RQ、真实 LLMProvider、真实 VectorStore 或完整 MVP 产品功能标记为 Done。

## 2026-06-04 State Manager Update After PLAN-004 to PLAN-006

依据：

- `PLAN-004`、`PLAN-005`、`PLAN-006` 属于 State Manager / Task Manager 可直接维护的文档与仓库治理任务，不涉及功能代码验收。
- 当前项目事实已由 `docs/06-project-state.md`、`reviews/review-log.md` 和 `tasks/done.md` 明确记录，可作为文档校准依据。

任务状态更新：

- `PLAN-004` 已完成：更新 `docs/02-acceptance-criteria.md` 中过期的“当前不可验收项”描述。
- `PLAN-005` 已完成：新增 `.gitignore`，补充 Python、frontend、build 和 demo database ignore 规则。
- `PLAN-006` 已完成：在部署文档、示例环境变量和项目状态中明确 SQLite 仅用于 demo / local，正式数据库统一通过 `APP_DATABASE_URL` 切换到 PostgreSQL。
- 当前任务推进到 `PLAN-002`：编写测试计划。

限制说明：

- 本次更新不新增任何功能通过结论，不扩大既有 Done 范围。

## 2026-06-04 State Manager Reprioritization After Architect LLM Plan

依据：

- Architect Agent 已在 `docs/03-architecture.md` 中给出“真实 LLM 最小接入方案”和任务拆分建议。
- 用户明确要求：将架构建议的任务移入任务系统，并将目前的 `Current` 移回 `Backlog`。

任务状态更新：

- `PLAN-002` 从 `tasks/current.md` 移回 `tasks/backlog.md`，不再作为当前最高优先级。
- 新增 `PLAN-007`、`IMPL-010`、`REFACTOR-004` 到 `tasks/backlog.md`。
- `PLAN-007` 从 `tasks/backlog.md` 移入 `tasks/current.md`，作为真实 LLM 接入前的当前准备任务。

限制说明：

- 本次仅调整任务优先级与任务清单，不新增任何功能通过结论。
- `IMPL-010` 尚未进入 `Current`，不得由 Implementation Agent 直接执行。

## 2026-06-04 State Manager Reprioritization To Direct IMPL-010

依据：

- 用户明确要求采用“加速做法”：不单独执行 `PLAN-007`，直接推进 `IMPL-010`。
- 但 `PLAN-007` 中的配置、secret、fallback 和测试边界约束必须继续生效。

任务状态更新：

- `PLAN-007` 不再作为独立 `Current` 任务执行。
- `PLAN-007` 的关键约束已并入 `IMPL-010` 的任务说明与 Done 条件。
- `IMPL-010` 从 `tasks/backlog.md` 移入 `tasks/current.md`，作为新的当前实现任务。

限制说明：

- 本次仍未新增任何功能通过结论。
- `IMPL-010` 的 Review 必须同时检查真实 LLM 接入结果和原 `PLAN-007` 约束是否被满足。

## 2026-06-04 Review & Test Agent Review: IMPL-010

结论：Needs Fix。

审查范围：

- 当前任务：`tasks/current.md` 中的 `IMPL-010: 接入 OpenAI-compatible LLMProvider 并用于 Tutor Agent`。
- 代码范围：`src/backend/app/adapters/llm_provider.py`、`src/backend/app/agents/tutor_agents.py`、`src/backend/app/agents/tutor_factory.py`、`src/backend/app/agents/tutor_prompts.py`、`src/backend/app/services/tutor_service.py`、`src/backend/app/agents/rule_based_agents.py`、`tests/test_llm_provider_tutor.py`。
- 配置与脚本范围：`deployment/README.md`、`deployment/local.env.example`、`scripts/frontend-smoke.ps1`、`scripts/run-local.ps1`。
- 文档与任务范围：`docs/02-acceptance-criteria.md`、`docs/03-architecture.md`、`docs/06-project-state.md`、`tasks/backlog.md`、`tasks/current.md`、`tasks/done.md`。

验证命令与结果：

- `./scripts/verify.ps1`：通过。覆盖 Python compile、20 个 backend unit tests、`pip check`、backend wheel build、frontend `npm ci`、frontend production build、Playwright smoke。
- `./scripts/run-local.ps1 -SmokeOnly -BackendPort 8241 -FrontendPort 5241`：通过。输出 `DemoDataLoaded=True`、`RemoteTutorLLM=False`，确认默认本地演示不依赖远程 LLM。
- `Select-String` 检查 `LLM_API_KEY` / provider SDK 关键字：未发现真实 key；具体 provider HTTP 调用仅位于 `src/backend/app/adapters/llm_provider.py`。

Acceptance Criteria 覆盖：

- AC6：Partial。Tutor 已接入 `LLMBackedTutorAgent` 与 OpenAI-compatible provider adapter，并保留 rule-based fallback；真实 RAG / VectorStore 不在本任务完成范围。
- AC11：Partial。新增 LLM adapter、配置和本地运行脚本保护；数据库迁移、任务队列和生产部署仍未完成。
- AC13：Pass in current scope。`TutorService` 通过 factory 获取 agent，API handler / frontend 未直接调用 provider SDK 或读取 API key。
- AC20：Pass。已执行 Implementation Boundary Check。
- 原 `PLAN-007` 并入约束：Needs Fix。默认 smoke 不依赖真实 LLM、secret 未入仓库、provider 失败 fallback 均有覆盖；但 `LLM_FALLBACK_MODE` 配置已暴露却未参与运行行为。

Implementation Boundary Check：

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | API / frontend 未新增 LLM 业务结果硬编码；frontend smoke 强制 `LLM_PROVIDER=rule_based` 只保证本地稳定 |
| Service/orchestrator boundary | Pass | `TutorService` 通过 `build_tutor_agent()` 获取 strategy，未直接实例化 provider SDK |
| Adapter/provider boundary | Pass | `OpenAICompatibleLLMProvider` 位于 `app/adapters/llm_provider.py`，实现 `LLMProvider.generate()` contract |
| Hardcoded demo/mock risk | Pass | Fake provider 仅在 `tests/test_llm_provider_tutor.py`；真实 demo 默认通过配置关闭远程 LLM |
| API contract stability | Pass | `/api/v1/tutor/ask` request / response schema 未变，新增 LLM metadata 未进入 API response |

Blocking Issues：

- 无。

Non-blocking Issues：

- `src/backend/app/adapters/llm_provider.py`：`LLMSettings.fallback_mode` 从环境变量读取，但当前 `build_llm_provider()`、`LLMBackedTutorAgent` 和 `TutorService` 都未使用该值。影响：配置契约与运行行为不一致，设置 `LLM_FALLBACK_MODE=error` 时仍会 fallback。最小修复：要么实现 `rule_based` / `error` 两种策略并测试，要么从文档和配置中移除 `error` 策略承诺，仅声明固定 rule-based fallback。是否阻塞进入 Done：是，阻塞 `IMPL-010` 标记 Done，但不属于架构级 Blocking。
- `docs/06-project-state.md` 原描述称“无配置、未显式启用”也会写入 fallback 摘要；实际 factory 在未配置时直接返回 `RuleBasedTutorAgent`，不会记录 LLM fallback reason。影响：状态文档强于实现事实。已由 State Manager Update 修正为当前真实行为。

Missing Tests：

- 缺少通过 `/api/v1/tutor/ask` 触发 provider failure 后再读取 `agent_runs` / `agent_run_steps` 的集成测试；当前只能证明 `LLMBackedTutorAgent` 单元层 fallback。
- 缺少 `LLM_FALLBACK_MODE=error` 或等价策略的行为测试；如果项目决定只支持固定 rule-based fallback，则应删除该配置承诺并补文档测试。
- 未进行真实外部 LLM 网络调用验证；按当前任务约束，默认验证不应依赖真实 key 或网络，因此不作为阻塞。

建议：

- 先完成 `FIX-002`：明确并实现 `LLM_FALLBACK_MODE` 语义，或移除该配置承诺。
- 再完成 `TEST-003`：补 Tutor API 层 fallback / agent step 记录集成测试。
- 修复后重新运行 `./scripts/verify.ps1` 和 `./scripts/run-local.ps1 -SmokeOnly`。

最终结论：

- 功能验收：Needs Fix。
- Implementation Boundary Check：Pass。
- 是否允许 State Manager 移入 Done：No。

## 2026-06-04 State Manager Update After IMPL-010 Review

依据：

- Review & Test Agent 已在本文件中明确给出 `IMPL-010` 结论为 `Needs Fix`。
- `Implementation Boundary Check` 为 `Pass`，但配置契约存在可证实缺口，未达到移入 Done 条件。

任务状态更新：

- `IMPL-010` 保持在 `tasks/current.md`，不得移入 `tasks/done.md`。
- 从 `tasks/backlog.md` 移除重复残留的 `IMPL-010` 待实现行，避免同一任务同时位于 Current 和 Backlog。
- 新增 `FIX-002`：补齐 `LLM_FALLBACK_MODE` 的真实行为或移除该配置承诺。
- 新增 `TEST-003`：增加 Tutor API 层的 LLM fallback / agent step 记录测试。

限制说明：

- 本次未新增任何功能 Done 结论。
- 未将真实 LLM 接入、完整 RAG / VectorStore、生产部署或完整 MVP 产品功能标记为 Done。

## 2026-06-05 Review & Test Agent Retest: IMPL-010

结论：Pass。

审查范围：

- 当前任务：`tasks/current.md` 中的 `IMPL-010: 接入 OpenAI-compatible LLMProvider 并用于 Tutor Agent`。
- 修复范围：`FIX-002` 与 `TEST-003`，即 `LLM_FALLBACK_MODE` 行为和 Tutor API 层 fallback / agent step 记录测试。
- 代码范围：`src/backend/app/adapters/llm_provider.py`、`src/backend/app/agents/tutor_agents.py`、`src/backend/app/agents/tutor_factory.py`、`src/backend/app/agents/tutor_prompts.py`、`src/backend/app/services/tutor_service.py`、`tests/test_llm_provider_tutor.py`。

验证命令与结果：

- `./scripts/verify.ps1`：通过。覆盖 Python compile、24 个 backend unit tests、`pip check`、backend wheel build、frontend dependency install、frontend production build、Playwright smoke。
- `./scripts/run-local.ps1 -SmokeOnly -BackendPort 8242 -FrontendPort 5242`：通过。输出 `DemoDataLoaded=True`、`RemoteTutorLLM=False`，确认默认本地演示不依赖远程 LLM。
- 关键字检查：未发现真实 API key；具体 OpenAI-compatible HTTP 调用仅位于 `src/backend/app/adapters/llm_provider.py`。

Acceptance Criteria 覆盖：

- AC6：Pass in current scope。Tutor Agent 已通过 demo chunk 上下文生成 grounded answer，并可切换到 OpenAI-compatible provider；完整真实 RAG / VectorStore 仍未 Done。
- AC11：Pass in current scope。已有可替换 LLMProvider adapter、配置、timeout、retry、fallback 与默认 smoke 保护；数据库迁移、任务队列和生产部署仍未 Done。
- AC13：Pass。业务 service / API handler / frontend 未直接依赖具体 provider SDK 或读取 API key。
- AC20：Pass。已完成 Implementation Boundary Check。
- AC21-AC24：Pass in current scope。第一批只接入 Tutor，schema 稳定，provider 走 adapter，默认 smoke 不依赖真实 key 或网络，provider failure fallback / error 行为已有测试。

Implementation Boundary Check：

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | API handler / frontend 未硬编码 LLM 结果；frontend 仍通过 `/api/v1/tutor/ask` 消费 schema |
| Service/orchestrator boundary | Pass | `TutorService` 通过 `build_tutor_agent()` 获取 strategy，未直接调用 OpenAI-compatible HTTP / SDK |
| Adapter/provider boundary | Pass | `OpenAICompatibleLLMProvider` 位于 `app/adapters/llm_provider.py`，实现 `LLMProvider.generate()` contract |
| Hardcoded demo/mock risk | Pass | fake provider / fake endpoint 仅在 `tests/test_llm_provider_tutor.py`；默认 smoke 通过配置关闭远程 LLM |
| API contract stability | Pass | `/api/v1/tutor/ask` request / response schema 未变；fallback 信息写入 `agent_run_steps`，未进入 API response |

Blocking Issues：

- 无。

Non-blocking Issues：

- 未进行真实外部 LLM key 联网验收；按当前任务约束，默认验证不应依赖真实 key 或网络，因此不阻塞。
- `LLM_BYPASS_PROXY` 是本轮新增配置，用于本地 fake endpoint 测试和显式代理绕过场景；当前仅 backend adapter 使用，不影响 `/api/v1` schema。

Missing Tests：

- 真实外部 provider 的手动 opt-in 验证尚未执行。
- 仍缺生产级多环境矩阵、移动视口和失败路径系统测试计划；已留给 `PLAN-002` / `TEST-002`。

最终结论：

- 功能验收：Pass。
- Implementation Boundary Check：Pass。
- 是否允许 State Manager 移入 Done：Yes。

## 2026-06-05 State Manager Update After IMPL-010 Retest

依据：

- Review & Test Agent 已在本文件中明确给出 `IMPL-010` 复测通过结论。
- 通过范围限定为 Tutor Agent 的 OpenAI-compatible LLMProvider 最小接入、fallback 策略、API schema 稳定和默认 smoke 稳定性。
- `Implementation Boundary Check` 结论为 `Pass`。

任务状态更新：

- `IMPL-010` 从 `tasks/current.md` 移入 `tasks/done.md`。
- `FIX-002` 和 `TEST-003` 已随 `IMPL-010` 修复并复测通过，从 `tasks/backlog.md` 移除。
- `PLAN-002` 从 `tasks/backlog.md` 移入 `tasks/current.md`，作为下一阶段测试计划任务。

限制说明：

- 未将真实外部 LLM key 联网验收、完整 RAG / VectorStore、Resource / Quiz / Evaluator 的 LLM 接入、生产部署、数据库迁移、Redis/RQ 或完整 MVP 产品功能标记为 Done。

## 2026-06-06 Lightweight Reviewer Agent Review: Agile Demo Increments

结论：Pass。

对应提交：

- `7b3e37a Improve demo profile lifecycle`
- 分支：`codex/agile-profile-dialogue`

审查范围：

- 5 类个性化资源生成：`guided_note`、`practice_questions`、`mind_map`、`extended_reading`、`coding_case`。
- 基于 `agent_runs` / `agent_run_steps` 的动态学生画像更新。
- 用户画像删除与关联学习数据清理。
- Demo reset API：清理用户画像和学习过程数据，保留 seed demo data。
- 前端主流程：资源类型切换、画像更新、画像删除、reset user demo data。
- 轻量敏捷日志：`docs/05-agile-development-log.md`。

主要文件：

- `src/backend/app/agents/rule_based_agents.py`
- `src/backend/app/api/v1/router.py`
- `src/backend/app/services/resource_service.py`
- `src/backend/app/services/profile_updater_service.py`
- `src/backend/app/services/profile_service.py`
- `src/backend/app/services/demo_data_service.py`
- `src/frontend/src/App.tsx`
- `src/frontend/src/api/client.ts`
- `src/frontend/tests/student-loop.spec.ts`
- `tests/test_demo_data.py`
- `tests/test_learning_loop_api.py`
- `tests/test_profile_course_api.py`

验证命令与结果：

- `git diff --check`：通过，仅有 Windows 工作区 CRLF 提示，无 whitespace error。
- `python -m unittest tests.test_demo_data tests.test_profile_course_api tests.test_learning_loop_api -v`：通过，15 个目标测试全部通过。
- `python -m compileall -q src/backend tests`：通过。
- `npm ci`：最终通过，0 vulnerabilities。首次失败原因是本项目 Vite / esbuild 进程占用 `node_modules` 下 native binary；停止残留进程后重跑通过。
- `npm run build`：通过，TypeScript check 与 Vite production build 成功。
- `python -m unittest discover -s tests -v`：通过，29 个 backend tests 全部通过。
- `./scripts/verify.ps1`：通过，覆盖 Python compile、backend unit tests、`pip check`、backend wheel build、frontend dependency install、frontend production build、Playwright smoke。

功能验收分析：

- 资源生成：Pass。后端测试覆盖 5 类资源均可通过 `/api/v1/resources/generate` 生成，并保留 `source_refs` 与 `agent_run_id`；前端 smoke 覆盖 `guided_note` 与 `coding_case` 两类实际切换。
- 动态画像更新：Pass in current scope。`ProfileUpdaterService` 从最近 Agent trace 中提取弱点、资源偏好、学习偏好和更新原因，并写回 `StudentProfile.preferences`；当前为 rule-based trace analysis，不等同于真实 LLM 长期画像建模。
- 用户画像删除：Pass。demo profiles 通过 `profile_origin = "demo"` 保护，用户画像可删除；测试覆盖删除后 profile、learning path 和相关 agent runs 不再可查询。
- Demo reset：Pass。`POST /api/v1/demo-data/reset-user-data` 清理用户画像、学习路径、资源、quiz、attempt、mastery、agent runs 和 steps，保留 demo course、concepts、document chunks 与 3 个 seed profiles。
- 前端演示流程：Pass。Playwright smoke 覆盖“自然语言建画像 -> 学习路径 -> 资源生成 -> Tutor -> Quiz -> Evaluator -> 更新画像 -> reset 回到 3 个 demo profiles”。

Implementation Boundary Check：

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | API handler 只转发 service 调用和错误转换；frontend 只触发 API、刷新状态和展示结果 |
| Service/orchestrator boundary | Pass | 资源生成在 `RuleBasedResourceAgent`，画像更新在 `ProfileUpdaterService`，画像删除在 `ProfileService`，reset 在 `DemoDataService` |
| Adapter/provider boundary | N/A | 本轮未新增外部 provider；仍为 rule-based demo capability |
| Hardcoded demo/mock risk | Pass | demo profile 通过 seed preferences 标记，reset/delete 通过 profile origin 管理；未在 frontend 模拟核心结果 |
| API contract stability | Pass | 新增 endpoint，但既有 `/api/v1/resources/generate`、profile list/detail、learning loop schema 未破坏 |

发现的问题：

Blocking Issues：

- 无。

Fix Before Merge：

- 无。

Non-blocking Issues / Residual Risks：

- `npm ci` 在 review 中曾因本地 Vite / esbuild 进程占用 `node_modules` native binary 失败；这是本地验证环境问题，不是代码问题。后续人工验证前应先停止旧的 `run-local.ps1` / Vite 进程，避免依赖安装被 Windows 锁文件阻塞。
- `ProfileUpdaterService` 当前是 rule-based trace analysis，关键词识别对中文表达、同义词和长期学习趋势不稳；它满足当前可演示闭环，但不能标记为真实 LLM-backed dynamic learner modeling。
- Demo reset 和 delete 都是物理删除，不保留审计历史；适合比赛演示重置，不适合作为生产级学习记录治理方案。
- Demo reset 当前清理全局学习过程数据，而不是按 session 粒度选择性清理；这与当前单人 demo 目标匹配，但后续多用户或多 session 场景需要重新设计。
- Resource 5 类生成仍为 rule-based content templates；满足 A3 类型展示要求的最小演示版本，但不代表 Resource Agent 已具备真实 LLM 生成能力。

Missing Tests：

- 尚未覆盖移动视口、多浏览器和失败路径 UI 自动化。
- 尚未覆盖 reset/delete 在并发请求或半失败事务下的行为。
- 尚未覆盖 ProfileUpdater 的长周期、多轮、多 concept 混合历史稳定性。
- 尚未进行真实 LLM / RAG 参与资源生成或画像更新的 opt-in 验证。

最终建议：

- 允许保留并提交本轮增量。
- 通过范围限定为“个人敏捷模式下的可演示增量”：资源类型扩展、trace 驱动画像更新、用户画像生命周期和 demo reset。
- 不应把完整 RAG、生产级数据治理、真实 LLM Resource/ProfileUpdater 或完整测试矩阵标记为 Done。

## 2026-06-06 Lightweight Reviewer Agent Review: LLM-backed ProfileUpdater

结论：Pass。

审查范围：

- `LLMSettings` 新增 `LLM_ENABLE_FOR_PROFILE_UPDATER` 与按用途启用远端调用。
- `ProfileUpdaterService` 支持可选 LLM-backed trace analysis，provider 不可用时回退到 rule-based updater。
- 新增 `LLMBackedProfileUpdaterAgent`，使用固定 JSON schema 解析画像更新结果。
- 默认 smoke / local demo 保持离线安全，显式启用才调用远端 ProfileUpdater LLM。
- 新增 Aliyun Bailian Flash 本地启动脚本和部署文档说明。
- 新增 `tests/test_profile_updater_llm.py` 覆盖 LLM 成功和失败 fallback。

主要文件：

- `src/backend/app/adapters/llm_provider.py`
- `src/backend/app/agents/profile_updater_agents.py`
- `src/backend/app/services/profile_updater_service.py`
- `tests/test_profile_updater_llm.py`
- `scripts/run-local.ps1`
- `scripts/frontend-smoke.ps1`
- `scripts/run-local-aliyun-flash.ps1`
- `deployment/README.md`
- `deployment/local.env.example`
- `docs/05-agile-development-log.md`

验证命令与结果：

- `python -m unittest tests.test_profile_updater_llm tests.test_learning_loop_api tests.test_llm_provider_tutor tests.test_backend_contracts -v`：通过，18 个目标测试全部通过。
- `python -m compileall -q src/backend tests`：通过。
- `git diff --check`：通过，仅有 Windows 工作区 CRLF 提示，无 whitespace error。
- `npm ci`：最终通过，0 vulnerabilities。首次失败原因是本项目 Vite / esbuild 残留进程占用 `node_modules` native binary；停止项目相关进程后重跑通过。
- `npm run build`：通过，TypeScript check 与 Vite production build 成功。
- `python -m unittest discover -s tests -v`：通过，31 个 backend tests 全部通过。
- `./scripts/verify.ps1`：通过，覆盖 Python compile、backend unit tests、`pip check`、backend wheel build、frontend dependency install、frontend production build、Playwright smoke。

功能验收分析：

- LLM-backed ProfileUpdater：Pass in current scope。开启 `LLM_ENABLE_FOR_PROFILE_UPDATER=true` 且 provider 配置完整时，`ProfileUpdaterService` 会通过 `LLMProvider` 调用 `LLMBackedProfileUpdaterAgent`，解析固定 JSON 字段并写回 `StudentProfile.preferences`。
- Fallback：Pass。新增测试覆盖 provider exception 时回退到 rule-based updater，并把 fallback reason 写入 `last_profile_update_reason`。
- 默认演示稳定性：Pass。`scripts/frontend-smoke.ps1` 和未显式 `-UseRemoteTutorLLM` 的 `scripts/run-local.ps1` 都强制 `LLM_PROVIDER=rule_based`、`LLM_ENABLE_FOR_TUTOR=false`、`LLM_ENABLE_FOR_PROFILE_UPDATER=false`。
- API contract：Pass。画像更新仍使用既有 `POST /api/v1/student-profiles/{profile_id}/update-from-trace`，未新增 response schema 或数据库迁移。
- Aliyun local script：Pass in documentation scope。`scripts/run-local-aliyun-flash.ps1` 通过 `ALIYUN_BAILIAN_API_KEY` 环境变量读取 secret，不把 key 写入仓库；该脚本未在默认 smoke 中执行。

Implementation Boundary Check：

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | 本轮未把 LLM prompt、JSON parsing 或画像分析写入 API handler / frontend |
| Service/orchestrator boundary | Pass | `ProfileUpdaterService` 负责读取 trace、选择 LLM 或 fallback、写回画像 |
| Adapter/provider boundary | Pass | 远端调用继续通过 `LLMProvider` / `OpenAICompatibleLLMProvider`，按 `purpose="profile_updater"` 启用 |
| Hardcoded demo/mock risk | Pass | fake provider 仅位于 `tests/test_profile_updater_llm.py`，默认 demo 不依赖真实 LLM |
| API contract stability | Pass | 既有 update-from-trace endpoint 不变，新增配置不影响 `/api/v1` schema |

发现的问题：

Blocking Issues：

- 无。

Fix Before Merge：

- 无。

Non-blocking Issues / Residual Risks：

- 未执行真实 Aliyun Bailian / external LLM 联网验收；当前只验证 adapter contract、fake provider success 和 fallback，符合默认验证不依赖真实 key 的原则。
- 当前 JSON schema 是 prompt-level 约束和本地解析校验，不是 provider 原生 structured output；provider 若返回非 JSON 会 fallback。
- `ProfileUpdaterService` 仍只分析最近若干 Agent step，不支持长期学习历史压缩或跨 session 画像建模。
- `npm ci` 在 review 中再次遇到本项目 Vite / esbuild 残留进程锁文件；这是 Windows 本地验证流程风险，人工验证前应停止旧的 `run-local.ps1` / Vite 进程。

Missing Tests：

- 未覆盖真实 Aliyun endpoint 的手动 opt-in smoke。
- 未覆盖 LLM 返回字段过长、恶意内容或不受控知识点标签时的更细粒度清洗策略。
- 未覆盖 `run-local-aliyun-flash.ps1 -SmokeOnly` 的自动化测试，因为它需要真实 API key。
- 未覆盖多轮长期 profile update 的稳定性。

最终建议：

- 允许提交本轮增量。
- 通过范围限定为“可选 LLM-backed ProfileUpdater + 默认离线 fallback + Aliyun Flash 本地 opt-in runbook”。
- 不应将真实外部 LLM 服务可用性、生产级画像建模、完整 RAG 或长期学习历史建模标记为 Done。

## 2026-06-06 Lightweight Reviewer Agent Review: Resource/Evaluator LLM and Demo Presentation

## Review Conclusion

Result: Pass

Allowed to commit: Yes

## Scope Reviewed

- Documents read: `docs/04-development-roadmap.md`, `docs/00-project-brief.md`, `docs/02-acceptance-criteria.md`, `docs/06-project-state.md`, `docs/05-agile-development-log.md`
- Diff / files reviewed: Resource/Evaluator LLM agents and factories, `LLMSettings`, Resource/Assessment services, image generation protocol reservation, local/smoke scripts, deployment config, frontend resource cards and Agent trace timeline, Playwright smoke, backend tests
- Builder claimed: optional LLM-backed Resource and Evaluator with rule-based fallback; grounded source display; automatic profile update after evaluation; resource-specific cards including SVG mind map; image-generation adapter contract reservation
- Tests reported: targeted backend tests, 39-test backend suite, frontend build, `scripts/verify.ps1`, Playwright smoke

## Findings

### Blocking

- None.

### Fix Before Merge

- None.

### Optional

- File: `src/frontend/src/App.tsx`
- Issue: Quiz submission and automatic profile update are two sequential API calls in one frontend task. If profile update fails after evaluation succeeds, the evaluation remains valid but the page also displays a global error.
- Impact: The core evaluation is not lost, but an unstable ProfileUpdater provider can make the demo look like the quiz submission failed.
- Minimal fix: In a later UI increment, catch profile-update failure separately and show a non-blocking profile update warning while preserving the successful evaluation state.

- File: `src/frontend/src/App.tsx`
- Issue: Resource card parsing and SVG mind-map layout depend on the LLM following the requested text markers such as `中心主题`, `分支`, fenced code blocks, and `题目 n`.
- Impact: Non-conforming provider output may produce a simplified card, although the full resource text remains available and the page does not crash.
- Minimal fix: Keep the current full-text fallback; add one malformed-output component test when frontend component testing is introduced.

- File: `src/backend/app/adapters/protocols.py`
- Issue: `ImageGenerationProvider` is only a contract reservation and has no provider, factory, config, API field, or runtime use.
- Impact: No current runtime risk, but it must not be presented as implemented image generation capability.
- Minimal fix: Keep it explicitly documented as reserved infrastructure until a real Resource Agent visual-spec flow is implemented.

## Implementation Boundary Check

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | Frontend only sequences existing APIs and renders returned resource content; LLM prompts, evaluation, fallback, and persistence remain in backend Agent/service boundaries |
| Service/orchestrator boundary | Pass | `ResourceService` and `AssessmentService` call `build_resource_agent()` / `build_evaluator_agent()` and retain persistence plus Agent run recording |
| Adapter/provider boundary | Pass | Resource and Evaluator remote calls use the existing `LLMProvider`; image generation is represented only by an adapter protocol |
| Hardcoded demo/mock risk | Pass | Fake providers exist only in tests; default smoke forces all remote LLM feature flags off; frontend does not fabricate resource or evaluation results |
| API contract stability | Pass | Existing Resource and Quiz attempt endpoints and response schemas remain unchanged; only opt-in environment flags were added |

## Competition Fit Check

- Current phase: Phase 2, with a directly related Phase 3 presentation increment
- Does this change advance the phase goal? Yes
- Does this change improve A3 requirements fit? Yes
- The change adds real-LLM paths for Resource and Evaluator while preserving fallback, strengthens five resource-type differentiation, improves grounded-source and Agent trace presentation, and closes the evaluation-to-profile-update demo loop.

## Test Assessment

- Tests run by Builder: targeted Resource/Evaluator/API tests, frontend build, backend compile, 39-test suite, `scripts/verify.ps1`
- Tests run by Reviewer, if any:
  - `python -m unittest tests.test_evaluator_llm tests.test_resource_llm tests.test_learning_loop_api tests.test_backend_contracts -v`: 16 tests passed
  - `python -m unittest discover -s tests -v`: 39 tests passed
  - `python -m compileall -q src/backend tests`: passed
  - `npm run build`: passed
  - `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1`: passed, including dependency check, wheel build, frontend build, and Playwright smoke
  - `git diff --check`: passed with Windows CRLF notices only
- Missing but necessary tests: No additional test is required before this merge. Real Aliyun endpoint quality remains an explicit manual opt-in check because default verification must not require a secret or network.
- Is verification sufficient for this change? Yes

## Final Recommendation

建议提交本轮增量。Resource/Evaluator 的真实 LLM 路径保持在 Agent factory 和 `LLMProvider` 边界内，默认离线演示、fallback 和现有 API contract 均未被破坏。最重要的后端、前端构建和 Playwright 主流程均已由 Reviewer 复跑通过。通过范围不包括真实远端 provider 可用性、真实生图能力或生产级长期 mastery 建模。
