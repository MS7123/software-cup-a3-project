---
title: LLM 运行时性能与可靠性开发计划
date: 2026-07-13
status: complete
tags:
  - competition/a3
  - llm/performance
  - implementation-plan
---

# LLM 运行时性能与可靠性开发计划

最后更新：2026-07-13

> [!success] 开发状态
> **PERF-001～PERF-005 的代码开发与真实星火复测均已完成**。后端全量 **186 项测试通过**，**10 项真实星火测试按 opt-in 配置跳过**；前端 production build 与 Playwright 学习闭环通过。真实凭据由 Windows User scope 的 `XFYUN_SPARK_API_KEY` 提供，未写入仓库或测试输出。

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
| 统一调用预算 | 全部 purpose 使用 45 秒、1 次 retry | 每个 purpose 独立 timeout、max tokens、retry | Planner 最坏等待由约 90 秒降为单次 18 秒后 fallback |
| 结构化输出波动 | MaaS Qwen 会返回字段合法但缺少外层 envelope 的对象序列 | 仅修复字段完整的 Planner signal object，随后继续执行 Pydantic 与拓扑校验 | 避免对可恢复输出进行远程重试或整条路径 fallback |
| 枚举表达差异 | ProfileBuilder 偶尔返回英文资源类型 | 确定性映射到既有中文 API contract | 画像构建不因同义枚举波动降级 |
| 性能不可解释 | 只有粗粒度 `duration_ms` | 增加 API、provider、retry、token 与 fallback 证据 | 可定位时间花费和降级原因 |

## 3. Planner 的 25 节点决策

### 3.1 已知客观事实

- 当前演示课程图包含 **25 个知识点节点**与 **27 条先修关系**。
- 课程知识图保留全部 **25 个知识点节点**；具体学习路径应按目标选择相关子图，而不是机械覆盖全部节点。
- 图中存在一定语义层级重叠，例如 `stack-queue` 与 `stack`、`queue`，`binary-tree-traversal` 与 `tree-basics`、`binary-tree`，以及 `bfs-dfs` 与图表示、最短路径等节点。
- Playwright 旧断言仍写成 24，本次已依据真实数据修正为 **25**。

### 3.2 分析结论

**不应缩减课程知识图，但也不应把完整知识图等同于每一条学习路径。** 对“巩固二叉树遍历和图搜索”这类聚焦目标，路径应限制在目标节点及必要基础节点内，最多 **8 个节点**；只有“掌握完整课程”等明确全课程目标才生成完整路径。

| 方案 | 课程覆盖 | LLM 延迟/稳定性 | 先修约束精度 | 结论 |
|---|---|---|---|---|
| 完整 25 节点全部交给 LLM | 高 | 差，历史出现 90.5 秒和漏节点 fallback | 高但合同脆弱 | 不采用 |
| 永久缩减课程图为 7～8 节点 | 低 | 好 | 粗粒度，难以表达细分薄弱点 | 不采用 |
| 25 节点知识图 + 最多 8 节点目标路径 | 高 | 较好，prompt 与页面路径都有明确上界 | 规则层为目标子图补齐必要基础 | **已采用** |

### 3.3 已实现边界

- 数据库与课程知识图继续保留 **25 个节点**，不会删除未被当前目标选中的知识点。
- 规则层先从目标文本识别目标知识点，并补齐学习这些目标所需的基础节点，形成最多 **8 个节点**的合法目标子图。
- 明确的全课程目标仍可使用完整候选集合；已有路径刷新保持原候选集合，避免后台更新意外改变用户已创建路径的范围。
- LLM 只接收本次目标子图中的合法候选节点。
- LLM 最多返回 **5 个个性化推荐信号**。
- 规则层忽略未知/重复项，修复先修顺序，并补全 LLM 未返回的目标子图节点，不再把无关课程节点补进聚焦路径。
- LLM 失败时回退到确定性拓扑排序，不再回退到裸 `Concept.id` 顺序。

## 4. 分用途调用预算

| Purpose | Timeout | Retry | Max tokens | 设计意图 |
|---|---:|---:|---:|---|
| Planner | 18 秒 | 0 | 600 | 覆盖真实星火约 11～14 秒尾延迟，并为结构化信号保留输出空间 |
| ProfileUpdater | 12 秒 | 0 | 700 | 后台短分析，不重复占用远端时间 |
| ProfileBuilder | 15 秒 | 0 | 900 | 六维画像结构化输出 |
| Evaluator | 15 秒 | 0 | 900 | 开放题结构化评分 |
| Tutor | 25 秒 | 0 | 800 | 检索 chunk 截断为每项 900 字符，回答限制为 450 个中文字符，减少输出长度并覆盖星火偶发 20 秒尾延迟 |
| Quiz | 20 秒 | 0 | 1400 | 结构化多题型输出 |
| Resource | 30 秒 | 0 | 1200 | 五类资源采用紧凑输出，降低尾延迟与 timeout fallback |

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
- [x] 全课程目标覆盖全部真实待学习节点；聚焦目标只包含目标节点和必要基础，并满足先修约束。
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
- [x] 使用修改后代码和真实星火密钥重新采样 p50/p95，并记录样本数与 fallback 数量。

## 6. 验证证据

### 6.1 自动化与构建

| 验证项 | 结果 | 说明 |
|---|---|---|
| 后端全量 | **190 passed** | 10 项真实星火测试按 opt-in 配置跳过 |
| Planner 专项 | **13 passed** | 含稀疏信号、未知/重复项、先修修复、结构 envelope 修复、8 节点窗口和聚焦目标范围 |
| Resource/Tutor 后处理 | **5 passed** | 含慢后处理与 API timing 边界 |
| Provider/预算专项 | **15 passed** | 含 max tokens、timeout 不重试、瞬态断连重试 |
| 前端 production build | **passed** | TypeScript 与 Vite 构建通过 |
| Playwright 学习闭环 | **1 passed** | 真实 backend/frontend，25 节点断言已对齐 |
| `git diff --check` | **passed** | 仅有 Windows line-ending 提示 |

### 6.2 修改后受控性能证据

- PERF-001 的真实 Uvicorn socket 探针注入 **6000 ms** 后处理延迟，评分 HTTP 响应为 **97 ms**，task 随后从 `running` 转为 `completed`。
- PERF-004 的自动化测试向 Tutor ProfileUpdater 注入 **500 ms** 延迟，API `X-Process-Time-Ms` 明确不包含该后台时间。
- Provider 测试证明 Planner timeout 预算为 **18 秒、0 次 retry**，不会再次形成历史上的两次 45 秒等待。

### 6.3 修改后真实星火性能证据

2026-07-13 使用 MaaS `xop3qwen1b7`、`temperature=0.0`（结构化请求）和比赛入口的 purpose budget 采样。p95 按 nearest-rank 计算；单样本 Agent 只作为成功延迟证据，不作为稳定分位数结论。

| Agent | 样本数 | p50 | p95 | Fallback | 验收结果 |
|---|---:|---:|---:|---:|---|
| ProfileBuilder | 2 | 6.481 秒 | 8.810 秒 | 0 | 六维画像 schema 合法 |
| Planner | 3 | 11.497 秒 | 13.270 秒 | 0 | 完整课程样本保留全图；默认聚焦目标返回 7 个相关节点 |
| Quiz | 4 | 8.586 秒 | 13.856 秒 | 0 | grounded 结构化 Quiz 全中文且答案格式合法 |
| Resource | 7 | 12.355 秒 | 21.911 秒 | 0 | 五类资源及两画像差异均通过 |
| Tutor | 2 | 10.295 秒 | 10.604 秒 | 0 | 引用白名单通过 |
| Evaluator | 1 | 11.610 秒 | 11.610 秒 | 0 | 结构化评分合法 |
| ProfileUpdater | 1 | 5.610 秒 | 5.610 秒 | 0 | 使用真实学习 trace 更新 |

调优前的受控复测中，Resource 的 `guided_note`、`coding_case` 曾在 30 秒 timeout，Planner 曾在约 12～15 秒返回 5 个合法 signal object 但缺少 `recommendations` 外壳。将 Resource 限制为 **1200 tokens / 900 中文字符**，并增加 Planner 的受控 envelope 修复后，上表的最终样本全部走 LLM，未触发 fallback。

2026-07-13 用户场景复测中，默认目标“巩固二叉树遍历和图搜索，为课程小测做准备”走星火 LLM，在 **13.025 秒**内返回栈、队列、树基础、二叉树、二叉树遍历、图表示、BFS/DFS 共 **7 个节点**，无 fallback；默认 Tutor 问题在 **6.469 秒**内返回 415 字中文 grounded answer；Quiz 两个中文样本 p50 **8.300 秒**、p95 **9.682 秒**，无 fallback。

### 6.4 修改后真实联机复测命令

已有 Agent 的完整联机验收：

```powershell
./scripts/verify-spark-existing-agents.ps1 -BypassProxy
```

新 Agent 的 p50/p95 复测使用 `tests/test_spark_new_agents_performance_online.py`。该测试需要把 User scope 的 `XFYUN_SPARK_API_KEY` 映射为进程内 `LLM_API_KEY`，并启用对应 purpose；普通全量测试不会调用外部服务。

## 7. 完成判定

### 7.1 已完成的开发目标

- [x] 客观题首屏结果不等待远端后处理。
- [x] 一次 Quiz 最多触发一次路径重规划。
- [x] Planner 不再因漏掉完整节点集合而直接 fallback。
- [x] Resource、Tutor、Quiz、画像和路径均有独立超时或明确 fallback。
- [x] API 与 Agent trace 能解释总耗时、远端耗时、重试和降级原因。
- [x] 25 节点课程图保留，LLM 单次工作集收敛到 8 节点。

### 7.2 真实联机完成证据

> [!success] 真实联机复测完成
> Planner、ProfileBuilder、Quiz、五类 Resource、画像差异、Tutor、Evaluator 与 ProfileUpdater 均有真实星火成功样本。最终验收样本 fallback 数为 0；客观题同步评分仍保持确定性执行，远端画像与路径更新不阻塞成绩响应。

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
- 本轮收口增量已提交至当前分支最新提交：Planner 结构 envelope 修复、ProfileBuilder 资源枚举归一化、Resource 输出预算调优、真实星火性能测试与证据回填。
- 后端全量：`python -m unittest discover -s tests -q`，结果 190 passed、10 skipped。
- 前端构建：在 `src/frontend` 执行 `npm run build`，结果通过。
- 浏览器闭环：真实本地服务下 `npm run test:smoke`，结果 1 passed。
- 真实星火：ProfileBuilder、Planner、Quiz、Resource、Tutor、Evaluator、ProfileUpdater 均已复测；最终验收样本 fallback 数为 0。
