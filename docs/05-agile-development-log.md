# 敏捷开发记录

最后更新：2026-06-06

本文档用于记录个人敏捷模式下的可演示增量、核心架构边界、验证结果和当前状态。它不恢复重多 Agent 流程，只作为后续开发和提交前回顾的轻量事实记录。

## 当前阶段

Phase 2：核心智能能力完善。

当前优先目标是补齐 A3 赛题中的核心智能能力差距，尤其是：

- 对话式学生画像构建。
- 学生画像不少于 6 个维度。
- 主学习闭环继续可演示。
- 保持现有 `FastAPI` / `React` / service / adapter / orchestrator / `agent_runs` 架构不变。

## 2026-06-06 增量：对话式学生画像构建

### 目标

让学生端能够通过自然语言描述生成结构化学生画像，并将该画像直接接入现有学习路径、资源生成、Tutor、Quiz、Evaluator 和 Agent trace 主流程。

该增量用于补齐 A3 赛题中“通过自然语言对话构建动态学生画像，画像不少于 6 个维度”的关键要求。

### 核心功能

- 新增自然语言画像构建入口：
  - `POST /api/v1/student-profiles/from-dialogue`
- 输入：
  - `dialogue`
  - 可选 `profile_type`
  - 可选 `user_id`
- 输出：
  - 复用现有 `StudentProfileResponse`
  - 不新增独立前端数据模型
- 前端新增画像描述输入框和生成按钮。
- 生成的新画像会自动选中，并可直接用于 `Create path`。
- 前端展示 6 维画像摘要。
- 3 个默认 seed 画像也补齐同一套 6 维字段。

### 画像维度

当前统一使用以下 6 个维度，存放在 `StudentProfile.preferences` 中：

| 字段 | 含义 |
|---|---|
| `learning_goal` | 学习目标 |
| `foundation_level` | 基础水平 |
| `learning_preference` | 学习偏好 |
| `available_time` | 可用学习时间 |
| `weak_points` | 当前薄弱点 |
| `resource_preference` | 资源偏好 |

保留原有字段：

- `goal`
- `level`
- `time_budget`
- `profile_type`
- `preferences.style`
- `preferences.resource`
- `preferences.pace`

### 架构边界

本轮没有修改数据库表结构。

新增画像构建逻辑集中在：

- `src/backend/app/services/profile_builder.py`

后端调用链：

```text
/api/v1/student-profiles/from-dialogue
-> ProfileService.create_profile_from_dialogue()
-> profile_builder.build_profile_from_dialogue()
-> ProfileService.create_profile()
-> StudentProfile
```

边界约束：

- API handler 只负责接收 request、调用 service、返回 response。
- 自然语言解析规则不写在 API handler。
- 前端不自行模拟画像构建结果。
- 画像维度标准化放在 service 边界内。
- 使用现有 `StudentProfile` 模型和 `preferences` JSON 字段，避免本轮引入数据库迁移。

### API / Schema 状态

本轮新增 API：

```text
POST /api/v1/student-profiles/from-dialogue
```

新增 schema：

```text
StudentProfileDialogueCreate
```

未修改已有 API 的 request / response contract。

### 测试与验证

已运行：

```text
python -m compileall -q src/backend tests
python -m unittest discover -s tests -v
npm run build
./scripts/verify.ps1
```

验证结果：

- 后端 25 个单元测试通过。
- 前端 production build 通过。
- `./scripts/verify.ps1` 通过。
- Playwright smoke 通过。
- 浏览器主流程已覆盖：

```text
自然语言构建画像
-> 6 维画像展示
-> 学习路径生成
-> 资源生成
-> Tutor 问答
-> Quiz 生成与作答
-> Evaluator 反馈
-> Agent trace 展示
```

### 当前状态

状态：已实现并通过 Builder 自测。

Ready for commit：Yes。

### 已知限制

- 当前自然语言画像构建是 rule-based extraction，不是真实 LLM 对话。
- 当前是单轮画像构建，不支持多轮追问和持续画像更新。
- 画像更新尚未由 Evaluator 自动回写。
- `weak_points` 主要基于关键词识别，后续应结合 Quiz / Evaluator 结果动态调整。

## 2026-06-06 增量：5 类个性化资源生成

### 目标

将 `Resource Agent` 从单一讲解资源扩展为至少 5 类个性化学习资源，并在学生端可切换生成，补齐 A3 赛题中“至少生成 5 种个性化学习资源”的关键要求。

### 核心功能

支持的资源类型：

| `resource_type` | 展示含义 |
|---|---|
| `guided_note` | 讲解文档 |
| `practice_questions` | 练习题 |
| `mind_map` | 思维导图 |
| `extended_reading` | 拓展阅读 |
| `coding_case` | 代码实操案例 |

前端 Resource 区域新增 5 个资源类型切换按钮。学生选择当前学习路径节点后，可以切换资源类型并生成对应内容。

### 架构边界

本轮没有修改数据库表结构。

资源类型分派集中在：

- `src/backend/app/agents/rule_based_agents.py`

后端调用链保持不变：

```text
POST /api/v1/resources/generate
-> ResourceService.generate_resource()
-> RuleBasedResourceAgent.generate()
-> GeneratedResource
-> AgentRunService
```

边界约束：

- API request / response schema 不变。
- 前端只传 `resource_type`，不模拟资源内容。
- 资源生成逻辑仍在 Agent 边界内，不写入 API handler。
- 资源内容基于学习路径节点、知识点资料 chunk 和学生画像偏好生成。
- 每次资源生成仍记录 `resource_generation` agent run。

### 测试与验证

已运行：

```text
python -m unittest tests.test_learning_loop_api -v
npm run build
python -m compileall -q src/backend tests
./scripts/verify.ps1
```

验证结果：

- 后端 26 个单元测试通过。
- 新增测试覆盖 5 类资源均可生成。
- 前端 production build 通过。
- Playwright smoke 通过。
- 浏览器主流程已覆盖生成 `guided_note` 和 `coding_case` 两类资源。

### 当前状态

状态：已实现并通过 Builder 自测。

Ready for commit：Yes。

### 已知限制

- 当前 5 类资源仍为 rule-based generation，不是真实 LLM 生成。
- 思维导图当前为文本结构，不是可视化图谱。
- 视频/动画类资源尚未实现；后续可先做脚本或分镜。
- 资源类型没有新增独立枚举 schema，仍使用现有字符串 `resource_type`。

## 2026-06-06 增量：基于 Agent trace 更新动态学生画像

### 目标

新增独立 `ProfileUpdater` 最小闭环，通过分析学生最近的 Agent trace 更新画像，使画像从“一次性构建”推进为“随学习过程动态调整”。

### 核心功能

- 新增画像更新入口：
  - `POST /api/v1/student-profiles/{profile_id}/update-from-trace`
- 后端读取该学生最近的 `agent_runs` 和 `agent_run_steps`。
- 基于 trace 中的 Resource、Tutor、Evaluator 证据更新画像。
- 前端新增 `Update profile from learning trace` 按钮。
- 更新后前端刷新 6 维画像，并展示 `last_profile_update_reason`。

### 更新字段

当前最小版会更新或补充：

| 字段 | 来源 |
|---|---|
| `weak_points` | Tutor 问题、Resource/Evaluator trace 中出现的知识点 |
| `resource_preference` | Resource Agent 生成过的资源类型 |
| `learning_preference` | Resource Agent 生成类型推断 |
| `foundation_level` | Evaluator step 中的评分摘要 |
| `last_profile_update_reason` | 本次画像更新解释 |
| `last_profile_update_sources` | 参与更新的 Agent step 摘要 |

### 架构边界

本轮没有修改数据库表结构。

新增画像更新逻辑集中在：

- `src/backend/app/services/profile_updater_service.py`

后端调用链：

```text
POST /api/v1/student-profiles/{profile_id}/update-from-trace
-> ProfileUpdaterService.update_from_trace()
-> agent_runs / agent_run_steps
-> StudentProfile.preferences
```

边界约束：

- 不把画像更新逻辑写入 Evaluator。
- 不把画像更新逻辑写入 API handler。
- 前端只触发更新并展示后端返回的画像。
- 当前仍使用 rule-based trace analysis，后续可替换为 LLM-backed ProfileUpdater。
- 继续使用 `preferences` JSON 字段，避免本轮引入数据库迁移。

### 测试与验证

已运行：

```text
python -m unittest tests.test_learning_loop_api -v
npm run build
python -m compileall -q src/backend tests
./scripts/verify.ps1
```

验证结果：

- 后端 26 个单元测试通过。
- 前端 production build 通过。
- `./scripts/verify.ps1` 通过。
- Playwright smoke 通过。
- 浏览器主流程已覆盖：

```text
自然语言构建画像
-> 学习路径生成
-> 资源生成
-> Tutor 问答
-> Quiz 作答
-> Evaluator 反馈
-> 从 Agent trace 更新画像
-> 展示画像更新理由
```

### 当前状态

状态：已实现并通过 Builder 自测。

Ready for commit：Yes。

### 已知限制

- 当前 ProfileUpdater 是 rule-based trace analysis，不是真实 LLM 分析。
- 只读取最近若干条 Agent run，不支持长周期学习历史建模。
- 对知识点和资源偏好的识别依赖关键词。
- 当前由前端按钮触发，尚未自动在每轮学习后执行。

## 2026-06-06 增量：画像删除与学习数据清理

### 目标

补齐学生画像的新建/删除生命周期，避免自然语言构建画像后在演示过程中持续累积，同时清理该画像关联的学习数据和 Agent trace。

### 核心功能

- Demo seed 画像写入来源标记：
  - `preferences.profile_origin = "demo"`
  - `preferences.demo_profile_key = ...`
- 自然语言创建的画像写入：
  - `preferences.profile_origin = "user_dialogue"`
- 手动创建画像默认写入：
  - `preferences.profile_origin = "user_created"`
- 新增删除 API：
  - `DELETE /api/v1/student-profiles/{profile_id}`
- Demo 画像不可删除，删除时返回 `409 Conflict`。
- 用户画像可删除。
- 前端只对非 demo 画像显示删除按钮。
- 删除当前用户画像后，前端切回 demo 画像，并清空当前学习闭环状态。

### 数据清理范围

删除用户画像时同步清理：

- `learning_paths`
- `learning_path_items`
- `generated_resources`
- `quizzes`
- `quiz_items`
- `attempts`
- `mastery_records`
- `agent_runs`
- `agent_run_steps`

保留：

- demo course
- demo concepts
- demo document chunks
- 3 个 demo profiles

### 架构边界

- 删除逻辑集中在 `ProfileService.delete_profile()`。
- API handler 只负责错误转换。
- 没有新增数据库字段，通过 `preferences` JSON 记录画像来源。
- Demo profile 匹配从单纯 `profile_type` 改为优先使用 `demo_profile_key`，避免用户画像与 demo 画像混淆。

### 测试与验证

已运行：

```text
python -m unittest tests.test_profile_course_api tests.test_learning_loop_api -v
npm run build
python -m compileall -q src/backend tests
./scripts/verify.ps1
```

验证结果：

- 后端 28 个单元测试通过。
- 新增测试覆盖 demo 画像不可删除。
- 新增测试覆盖用户画像可删除。
- 新增测试覆盖删除用户画像后关联 learning path 和 agent run 不再可查询。
- Playwright smoke 覆盖：新建画像 -> 完整学习闭环 -> 删除用户画像 -> 回到 3 个 demo 画像。

### 当前状态

状态：已实现并通过 Builder 自测。

Ready for commit：Yes。

### 已知限制

- 批量清理所有用户画像的 demo reset API 已在后续增量补齐。
- 删除是物理删除，不保留审计历史。
- 仍未引入正式 session 概念；清理粒度是按 student profile。

### 后续候选增量

下一轮建议从以下候选中选择一个：

1. Demo reset API：一键清理所有用户画像和学习过程数据，保留 seed 数据。
2. LLM-backed ProfileUpdater：用固定 JSON schema 分析 Agent trace，失败时 fallback 到当前 rule-based updater。
3. Resource Agent 接入 LLM generation，保留当前 5 类资源 fallback。
4. Tutor / Resource 增强来源引用与防幻觉提示。

## 2026-06-06 增量：Demo reset API

### 目标

新增一键重置演示数据能力，清理所有用户创建画像和学习过程数据，保留 demo seed 数据，方便比赛演示中快速回到干净初始状态。

### 核心功能

- 新增重置 API：
  - `POST /api/v1/demo-data/reset-user-data`
- 重置前会先确保 demo seed 数据存在。
- 删除所有非 demo 学生画像。
- 删除学习过程数据和 Agent trace。
- 前端 Session setup 区域新增 `Reset user demo data` 按钮。
- 重置后前端刷新课程、画像、知识点数据，并清空当前学习闭环输出。

### 数据清理范围

清理：

- user-created / user-dialogue student profiles
- `learning_paths`
- `learning_path_items`
- `generated_resources`
- `quizzes`
- `quiz_items`
- `attempts`
- `mastery_records`
- `agent_runs`
- `agent_run_steps`

保留：

- demo course
- demo concepts
- demo document chunks
- 3 个 demo profiles

### 架构边界

- 重置逻辑集中在 `DemoDataService.reset_user_data()`。
- API handler 只负责暴露 demo reset endpoint。
- 前端只触发 reset 并刷新状态，不硬编码清理结果。
- Demo 数据识别继续基于 `preferences.profile_origin = "demo"`。

### API / Schema 状态

本轮新增 API：

```text
POST /api/v1/demo-data/reset-user-data
```

复用现有 `DemoDataLoadResponse`，没有新增数据库表或 schema 迁移。

### 测试与验证

已运行：

```text
python -m unittest tests.test_demo_data tests.test_profile_course_api tests.test_learning_loop_api -v
npm run build
python -m compileall -q src/backend tests
./scripts/verify.ps1
```

验证结果：

- 后端 29 个单元测试通过。
- 前端 production build 通过。
- `./scripts/verify.ps1` 通过。
- Playwright smoke 覆盖：新建画像 -> 完整学习闭环 -> reset user demo data -> 回到 3 个 demo 画像，用户画像删除按钮消失。

### 当前状态

状态：已实现并通过 Builder 自测。

Ready for commit：Yes。

### 已知限制

- reset 是物理删除，不保留审计历史。
- 当前没有按 session 粒度选择性 reset。
- 仍未引入正式 session 概念。
