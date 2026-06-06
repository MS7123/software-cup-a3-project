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

### 后续候选增量

下一轮建议从以下候选中选择一个：

1. 资源生成扩展到至少 5 类。
2. Evaluator 展示薄弱点、掌握度变化和后续资源建议。
3. Tutor / Resource 增强来源引用与防幻觉提示。
4. 画像多轮更新：根据测验结果回写 `weak_points` 和 `foundation_level`。
