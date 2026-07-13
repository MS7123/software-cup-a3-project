# LLM 运行时性能与可靠性开发计划

最后更新：2026-07-13

## 1. 背景与基线

真实星辰 MaaS 演示已经证明七类 LLM Agent 能够运行，但当前同步调用链直接影响比赛体验。`data/demo.sqlite3` 中 2026-07-13 的 Agent trace 给出以下基线：

| 场景 | 远端耗时 | 结果 |
|---|---:|---|
| ProfileBuilder | 5.4 秒 | LLM 成功 |
| Tutor | 13.8 秒 | 因伪造引用安全降级 |
| Quiz 生成 | 9.8 秒 | LLM 成功 |
| Resource 生成 | 33.9 秒 | LLM 成功 |
| ProfileUpdater | 50.9 秒 | LLM 成功 |
| Planner | 15.2 秒 | 节点集合非法，规则降级 |
| Planner timeout | 90.5 秒 | 两次 45 秒等待后规则降级 |

一次客观题提交的确定性评分约为 20 ms，但 API 在返回前同步执行 ProfileUpdater 和两条 active path 的 Planner，最终约 125 秒才向前端返回。

## 2. 根因

### 2.1 同步后处理阻塞业务结果

客观题评分完成后，`AssessmentService.submit_attempt()` 同步执行动态画像更新和全部 active path 重规划。前端只能把整个时间显示为“正在评分”。

### 2.2 active path 累积放大调用数

`refresh_active_paths()` 对同一画像、课程的每条 active path 分别调用一次 Planner。当前演示库中单个画像最多存在 6 条 active path，调用次数会随重复建路继续增长。

### 2.3 所有 purpose 共用调用预算

比赛入口统一使用 45 秒 timeout 和 1 次 retry。一次 timeout 的最坏等待约为 90 秒；Planner、ProfileUpdater 等短结构化任务与 Resource 长文本生成没有独立预算。

### 2.4 Planner 输出合同过于脆弱

LLM 必须完整返回全部候选节点、连续 priority 和合法先修顺序。漏掉一个节点就触发整条路径 fallback，未充分利用“规则层构造完整合法路径、LLM 只提供个性化排序信号”的 Hybrid 边界。

### 2.5 缺少端到端性能证据

Agent step 已记录 `duration_ms`，但 API 总耗时、TTFT、token usage、实际 retry reason 和后台任务状态没有统一呈现。

## 3. 架构原则

- 客观题、固定答案题继续确定性评分，不为展示 AI 而调用 Evaluator LLM。
- 先返回不可逆的业务结果，再异步执行可重试的画像和路径后处理。
- 一次 Quiz 只允许重规划一条相关路径，不能按画像扫描并调用全部历史 active path。
- LLM 只提供个性化信号；节点真实性、完整路径、先修约束和数据库事务继续由规则层负责。
- 比赛演示使用 SQLite 兼容的 FastAPI background task；Redis/RQ 等生产队列仍属于 `COMP-015`。
- 后台失败不得撤销已保存成绩，必须通过 task 状态向前端说明。

## 4. 开发增量

### PERF-001：评测立即返回与单路径后台后处理

**目标：** 客观题成绩保存后立即返回；ProfileUpdater 和 Planner 在后台执行，并且最多重规划一条路径。

**主要工作：**

- 复用现有 `tasks` 表记录 `pending`、`running`、`completed`、`failed`。
- `EvaluationResult` 增加 additive `postprocessing_task_id` 和 `postprocessing_status`。
- Attempt 请求允许传入当前 `learning_path_id`；旧客户端省略时选择该画像、课程最新 active path。
- 新增 task 查询 API，前端轮询并展示画像/路径更新状态。
- 后台异常只更新 task error，不改变 Attempt、score 或 mastery。

**验收标准：**

- [x] `AssessmentService.submit_attempt()` 不同步调用 ProfileUpdater 或 Planner。
- [x] 客观题成绩、Attempt 和 mastery 在后台任务开始前已持久化。
- [x] 一次 Attempt 最多触发一次 Planner。
- [x] 后台失败时成绩仍可见，前端显示失败状态。
- [x] 既有未传 `learning_path_id` 的客户端继续工作。

### PERF-002：重构 Hybrid Planner 个性化合同

**目标：** LLM 返回少量优先节点、资源偏好和理由，规则层据此构造完整合法拓扑路径。

**验收标准：**

- [ ] LLM 漏掉非优先节点不会导致整条路径 fallback。
- [ ] 未知节点被规则层忽略并记录原因。
- [ ] 最终路径仍包含全部真实待学习节点并满足先修约束。
- [ ] 两组画像对同一课程产生可观察的合法差异。

### PERF-003：分用途 LLM 调用预算与选择性重试

**目标：** 为 Planner、ProfileUpdater、Evaluator、Quiz、Tutor 和 Resource 设置独立 timeout、max tokens 和 retry policy。

**验收标准：**

- [ ] timeout 后不再无条件重复等待同样时长。
- [ ] 仅快速瞬态错误允许有限重试。
- [ ] payload 显式携带 purpose 对应的 `max_tokens`。
- [ ] 默认比赛入口仍启用七项 LLM purpose。

### PERF-004：Resource/Tutor 渐进式体验

**目标：** Resource 完成后不再同步更新画像；Tutor/Resource 提供可见进度或安全 streaming 体验。

**验收标准：**

- [ ] Resource 内容完成后立即返回，画像更新进入后台。
- [ ] Critic 拒绝不会无上限重复完整生成。
- [ ] streaming 内容在最终展示前仍经过引用和安全校验。

### PERF-005：性能可观测性与回归预算

**目标：** 可以回答一次请求“时间花在哪里、是否重试、是否 fallback”。

**验收标准：**

- [ ] 记录 API 总耗时、provider duration、重试次数和安全 token usage。
- [ ] 不记录 API key、完整 prompt、完整模型输出或 chain-of-thought。
- [ ] 自动化性能回归证明客观题响应不等待模拟慢后处理。
- [ ] 真实联机验收记录 p50/p95 和 fallback reason。

## 5. 推荐顺序

```text
PERF-001 评测立即返回与单路径后台后处理
    -> PERF-002 Hybrid Planner 合同
    -> PERF-003 分用途调用预算
    -> PERF-004 Resource/Tutor 渐进式体验
    -> PERF-005 性能证据与回归预算
```

## 6. 对外完成标准

只有同时满足以下条件，才能将性能改造标记为完成：

- 客观题成绩首屏返回不等待任何远端后处理。
- 一次 Quiz 最多触发一次路径重规划。
- Planner fallback 不再主要由“漏掉完整节点集合”造成。
- Resource、Tutor、Quiz、画像和路径均有明确的超时与降级状态。
- 真实 Agent trace 和自动化测试均能证明改造效果。

## 7. PERF-001 实施与验收证据

完成日期：2026-07-13

- 后端将 `ProfileUpdaterService.update_from_trace()` 和 `LearningPathService.refresh_active_paths()` 移入 `quiz_postprocessing` background task。
- Attempt 请求增加可选 `learning_path_id` 和 `run_postprocessing`；响应增加 additive task id/status；新增 `GET /api/v1/tasks/{task_id}`。
- 前端先展示成绩，再轮询任务并显示 `pending`、`running`、`completed` 或 `failed`，完成后刷新画像和当前路径。
- 专项测试 `tests/test_quiz_postprocessing.py` 共 6 项通过，覆盖同步边界、单路径刷新、失败不撤销成绩、错误脱敏、task API 和关闭后台更新。
- 后端全量测试 169 项通过、7 项 opt-in 星火联机测试按配置跳过；前端 production build 与 Playwright 学习闭环 1 项通过。
- 真实 Uvicorn socket 探针将 ProfileUpdater 与 Planner 分别人为延迟 3 秒，总后台延迟 6000 ms；评分响应为 97 ms，响应时 task 为 `running`，随后转为 `completed`。

`PERF-001` 已完成；`PERF-002` 至 `PERF-005` 继续按本计划推进，不能据此把第 6 节整体性能改造标记为完成。
