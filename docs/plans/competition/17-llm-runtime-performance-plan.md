---
title: LLM 运行时性能与可靠性开发计划
date: 2026-07-13
status: development-complete-online-rebenchmark-pending
tags:
  - competition/a3
  - llm/performance
  - implementation-plan
---

# LLM 运行时性能与可靠性开发计划

最后更新：2026-07-13

> [!success] 开发状态
> **PERF-001～PERF-005 的代码开发已完成**。后端全量 **181 项测试通过**，**7 项真实星火测试按 opt-in 配置跳过**；前端 production build 与 Playwright 学习闭环通过。当前机器未配置 `XFYUN_SPARK_API_PASSWORD`，因此修改后的真实星火 p50/p95 复测仍是外部验收项，不能把历史数据冒充为修改后结果。

## 1. 历史真实基线

`data/demo.sqlite3` 中 2026-07-13 的真实星辰 MaaS Agent trace 给出修改前基线：

| Agent | 远端样本数 | 历史 p50 | 历史 p95 | 主要结果 |
|---|---:|---:|---:|---|
| ProfileBuilder | 1 | 5.4 秒 | 5.4 秒 | LLM 成功 |
| Tutor | 2 | 0.002 秒 | 13.8 秒 | 伪造引用与错误模型触发 fallback |
| Quiz | 1 | 9.8 秒 | 9.8 秒 | LLM 成功 |
| Resource | 1 | 33.9 秒 | 33.9 秒 | LLM 成功 |
| ProfileUpdater | 2 | 3.6 秒 | 50.9 秒 | LLM 成功但阻塞主链路 |
| Planner | 4 | 37.0 秒 | 90.5 秒 | timeout 或完整节点集合校验失败 |

历史统计可用以下命令复核：

```powershell
python scripts/report-llm-performance.py data/demo.sqlite3
```

一次客观题的确定性评分约 **20 ms**，但旧实现会在 HTTP 返回前同步执行 ProfileUpdater 和多条 active path 的 Planner，最终约 **125 秒**才向前端返回。

## 2. 根因与处理结果

| 根因 | 修改前 | 已实施方案 | 对用户体验的影响 |
|---|---|---|---|
| 同步后处理 | Quiz、Resource、Tutor 等待画像或路径更新 | 业务结果先返回，后处理进入 `Task` + FastAPI background task | 成绩、资源、回答不再等待后处理 |
| Planner 合同脆弱 | LLM 必须返回完整节点集合 | LLM 只返回少量排序信号，规则层补全、去重、修复先修关系 | 漏节点不再导致整条路径 fallback |
| Planner prompt 过大 | 一次发送完整 25 节点图 | 完整图保留，每轮最多发送 8 个合法候选 | 降低 prompt、输出长度和超时概率 |
| 统一调用预算 | 全部 purpose 使用 45 秒、1 次 retry | 每个 purpose 独立 timeout、max tokens、retry | Planner 最坏等待由约 90 秒降为单次 12 秒后 fallback |
| 性能不可解释 | 只有粗粒度 `duration_ms` | 增加 API、provider、retry、token 与 fallback 证据 | 可定位时间花费和降级原因 |

## 3. Planner 的 25 节点决策

### 3.1 已知客观事实

- 当前演示课程图包含 **25 个知识点节点**与 **27 条先修关系**。
- 当前较新的 active path 会覆盖全部 **25 个待学习节点**；旧演示路径仅有 5 个节点。
- 图中存在一定语义层级重叠，例如 `stack-queue` 与 `stack`、`queue`，`binary-tree-traversal` 与 `tree-basics`、`binary-tree`，以及 `bfs-dfs` 与图表示、最短路径等节点。
- Playwright 旧断言仍写成 24，本次已依据真实数据修正为 **25**。

### 3.2 分析结论

**不应把课程知识图永久缩减为 7～8 个节点。** 7～8 个节点适合作为一次 LLM 决策窗口或前端“近期学习阶段”，但作为完整课程图会导致知识覆盖、先修约束和 Quiz 后精细重规划能力下降。

| 方案 | 课程覆盖 | LLM 延迟/稳定性 | 先修约束精度 | 结论 |
|---|---|---|---|---|
| 完整 25 节点全部交给 LLM | 高 | 差，历史出现 90.5 秒和漏节点 fallback | 高但合同脆弱 | 不采用 |
| 永久缩减为 7～8 节点 | 低 | 好 | 粗粒度，难以表达细分薄弱点 | 不采用 |
| 25 节点完整图 + 8 节点滚动窗口 | 高 | 较好，prompt 有明确上界 | 规则层保持完整约束 | **已采用** |

### 3.3 已实现边界

- 数据库、课程图和最终合法路径继续保留 **25 个节点**。
- 规则层先根据先修关系、已完成节点、掌握度和画像形成合法候选顺序。
- 每轮只把前 **8 个候选节点**交给 LLM。
- LLM 最多返回 **5 个个性化推荐信号**。
- 规则层忽略未知/重复项，修复先修顺序，并补全 LLM 未返回的真实节点。
- LLM 失败时回退到确定性拓扑排序，不再回退到裸 `Concept.id` 顺序。

## 4. 分用途调用预算

| Purpose | Timeout | Retry | Max tokens | 设计意图 |
|---|---:|---:|---:|---|
| Planner | 12 秒 | 0 | 600 | 快速结构化排序，失败立即拓扑 fallback |
| ProfileUpdater | 12 秒 | 0 | 700 | 后台短分析，不重复占用远端时间 |
| ProfileBuilder | 15 秒 | 0 | 900 | 六维画像结构化输出 |
| Evaluator | 15 秒 | 0 | 900 | 开放题结构化评分 |
| Tutor | 20 秒 | 0 | 1200 | 中等长度 grounded answer |
| Quiz | 20 秒 | 0 | 1400 | 结构化多题型输出 |
| Resource | 30 秒 | 0 | 2000 | 五类资源中最长的文本生成 |

默认不对 timeout、普通 HTTP 4xx、非法 JSON 重试；只允许对连接重置、`RemoteDisconnected`、HTTP 429/5xx 等明确瞬态故障执行配置允许的有限重试。

## 5. 开发增量与验收

### PERF-001：评测立即返回与单路径后台后处理

- [x] `AssessmentService.submit_attempt()` 不同步调用 ProfileUpdater 或 Planner。
- [x] 客观题成绩、Attempt 和 mastery 在后台任务开始前持久化。
- [x] 一次 Attempt 最多触发一次 Planner。
- [x] 后台失败时成绩仍可见，前端显示失败状态。
- [x] 旧客户端省略 `learning_path_id` 时继续工作。

### PERF-002：Hybrid Planner 有限信号合同

- [x] LLM 漏掉非优先节点不会导致整条路径 fallback。
- [x] 未知、重复和违反先修关系的信号由规则层忽略或修复，并记录 warning reason。
- [x] 最终路径包含全部真实待学习节点并满足先修约束。
- [x] 两组画像对同一课程产生合法且可观察的资源推荐差异。
- [x] 每次 LLM prompt 最多包含 8 个候选节点，输出最多包含 5 个信号。

### PERF-003：分用途 LLM 调用预算与选择性重试

- [x] timeout 后不再无条件重复等待相同时长。
- [x] 仅明确瞬态错误允许有限重试。
- [x] payload 显式携带 purpose 对应的 `max_tokens`。
- [x] 比赛入口继续默认启用七项 LLM purpose。
- [x] 比赛脚本与部署文档公开全部 purpose 预算环境变量，但不保存密钥。

### PERF-004：Resource/Tutor 及时反馈

- [x] Resource 与 Tutor 主结果返回后再更新画像。
- [x] 两类响应提供 additive `postprocessing_task_id` 和 `postprocessing_status`。
- [x] 前端轮询后台状态并明确显示成功、失败或仍在进行。
- [x] Critic 最多触发一次 LLM 重生成，连续拒绝后进入 rule-based safety fallback。
- [x] 不伪装成未实现的 token streaming；内容通过引用和安全校验后完整展示。

### PERF-005：性能可观测性与回归预算

- [x] API 响应记录 `X-Process-Time-Ms`、`Server-Timing` 和安全 request id。
- [x] Agent trace 记录 provider duration、retry count、安全 token usage 与 fallback reason。
- [x] 不记录 API key、完整 prompt、完整模型输出或 chain-of-thought。
- [x] `report-llm-performance.py` 可从 SQLite trace 生成各 Agent 的 p50/p95 与 fallback 汇总。
- [x] 自动化回归证明 Tutor 的模拟慢画像后处理不计入主响应处理时间。
- [ ] 使用修改后代码和真实星火密钥重新采样 p50/p95；当前机器未配置外部密钥。

## 6. 验证证据

### 6.1 自动化与构建

| 验证项 | 结果 | 说明 |
|---|---|---|
| 后端全量 | **181 passed** | 7 项真实星火测试按 opt-in 配置跳过 |
| Planner 专项 | **11 passed** | 含稀疏信号、未知/重复项、先修修复和 8 节点窗口 |
| Resource/Tutor 后处理 | **5 passed** | 含慢后处理与 API timing 边界 |
| Provider/预算专项 | **15 passed** | 含 max tokens、timeout 不重试、瞬态断连重试 |
| 前端 production build | **passed** | TypeScript 与 Vite 构建通过 |
| Playwright 学习闭环 | **1 passed** | 真实 backend/frontend，25 节点断言已对齐 |
| `git diff --check` | **passed** | 仅有 Windows line-ending 提示 |

### 6.2 修改后受控性能证据

- PERF-001 的真实 Uvicorn socket 探针注入 **6000 ms** 后处理延迟，评分 HTTP 响应为 **97 ms**，task 随后从 `running` 转为 `completed`。
- PERF-004 的自动化测试向 Tutor ProfileUpdater 注入 **500 ms** 延迟，API `X-Process-Time-Ms` 明确不包含该后台时间。
- Provider 测试证明 Planner timeout 预算为 **12 秒、0 次 retry**，不会再次形成历史上的两次 45 秒等待。

### 6.3 修改后真实联机复测命令

外部密钥可用后执行：

```powershell
$env:RUN_SPARK_ONLINE_TESTS = "true"
./scripts/verify-spark-existing-agents.ps1
python scripts/report-llm-performance.py data/demo.sqlite3
```

验收时必须区分新旧 trace，并至少记录 Planner、Resource、Tutor、Quiz、ProfileUpdater 的样本数、p50、p95 和 fallback reason。

## 7. 完成判定

### 7.1 已完成的开发目标

- [x] 客观题首屏结果不等待远端后处理。
- [x] 一次 Quiz 最多触发一次路径重规划。
- [x] Planner 不再因漏掉完整节点集合而直接 fallback。
- [x] Resource、Tutor、Quiz、画像和路径均有独立超时或明确 fallback。
- [x] API 与 Agent trace 能解释总耗时、远端耗时、重试和降级原因。
- [x] 25 节点课程图保留，LLM 单次工作集收敛到 8 节点。

### 7.2 尚未完成的外部验收

> [!warning] 真实联机复测待办
> 当前开发增量已完成，但“修改后真实星火 p50/p95”没有密钥就无法产生。本项完成前，可以标记为“性能开发完成”，不能声称“修改后真实联机性能验收完成”。

## 8. 中断恢复检查点

若 Codex 会话或额度中断，下次从以下状态继续：

- 分支：`codex/a3-competition-post-comp008`
- 已完成提交：
  - `f8730bc`：Quiz 评分先返回、画像/单路径后台更新。
  - `44df54b`：Planner 稀疏信号与容错补全。
  - `6e5fc2e`：Planner 8 节点滚动窗口。
  - `bbecd19`：分用途 timeout、max tokens 与选择性重试。
  - `2688171`：Resource/Tutor 画像后台后处理。
  - `c4d61d6`：API/LLM 安全性能证据与 p50/p95 报告。
- 后端全量：`python -m unittest discover -s tests -q`，结果 181 passed、7 skipped。
- 前端构建：在 `src/frontend` 执行 `npm run build`，结果通过。
- 浏览器闭环：真实本地服务下 `npm run test:smoke`，结果 1 passed。
- 唯一外部待办：配置 `XFYUN_SPARK_API_PASSWORD` 后执行修改后真实联机复测并回填 p50/p95。
