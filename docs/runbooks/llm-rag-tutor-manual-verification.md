# LLM + RAG Tutor 手动验证

最后更新：2026-06-13

本文档用于验证真实 `LLMProvider` 能基于真实导入的 RAG chunk 生成 Tutor answer，同时保留默认离线 fallback 能力。

## 验证目标

- 验证 `POST /api/v1/courses/{course_id}/documents` 导入的真实资料能进入 Tutor grounding context。
- 验证启用 `LLM_ENABLE_FOR_TUTOR=true` 后，`Tutor Agent` 仍保留真实 `source_refs`。
- 验证 `Agent trace` 能显示 LLM provider 使用情况或 fallback 原因。
- 验证无 API key 或 provider 失败时，本地演示不崩溃。

## 前置条件

- 已运行本地服务。
- 已通过 `POST /api/v1/demo-data/load` 或前端 `Load or refresh demo data` 加载课程。
- 已配置远程 OpenAI-compatible provider 时，仅通过 shell environment 或用户级环境变量注入 key。
- 不得把真实 API key 写入仓库、`.env`、测试输出、frontend bundle 或 agent trace。

## 推荐导入资料

标题：

```text
bfs-dfs-rag-note.md
```

类型：

```text
markdown
```

内容：

```markdown
# BFS and DFS

BFS uses a queue to expand graph nodes level by level. In an unweighted graph, the first time BFS reaches a node represents the fewest number of edges from the start node.

DFS uses a stack or recursion to go as deep as possible before backtracking. DFS is useful for traversal, connectivity checks, backtracking, and topological-style reasoning, but it does not guarantee shortest paths in an unweighted graph.

Stack and queue are easy to confuse: stack is last-in-first-out with push and pop, while queue is first-in-first-out with enqueue and dequeue.
```

## Rule-based 基线验证

1. 保持默认配置：

```powershell
$env:LLM_PROVIDER='rule_based'
$env:LLM_ENABLE_FOR_TUTOR='false'
```

2. 导入上面的资料。
3. 调用 Tutor：

```text
为什么 BFS 在无权图中第一次到达节点就代表最少边数？请和 DFS 对比。
```

4. 预期结果：

- response `source_refs` 至少包含 1 个 `document:{id}#chunk:{index}`。
- answer 明确基于课程资料，不声称使用远程 LLM。
- Agent trace 的 `decision_basis` 或 `output_summary` 包含 `Grounded sources: document:{id}#chunk:{index}`。

## LLM Tutor 验证

1. 使用已有阿里云 Flash 启动脚本：

```powershell
[Environment]::SetEnvironmentVariable('ALIYUN_BAILIAN_API_KEY', '<your-api-key>', 'User')
./scripts/run-local-aliyun-flash.ps1
```

2. 或手动设置 OpenAI-compatible provider：

```powershell
$env:LLM_PROVIDER='openai_compatible'
$env:LLM_ENABLE_FOR_TUTOR='true'
$env:LLM_FALLBACK_MODE='rule_based'
$env:LLM_BASE_URL='<provider-base-url>'
$env:LLM_MODEL='<provider-model>'
$env:LLM_API_KEY='<your-api-key>'
./scripts/run-local.ps1
```

3. 导入相同资料。
4. 使用同一问题调用 Tutor。
5. 查看 response 和 Agent trace。

## 评价标准

| ID | 标准 |
|---|---|
| LLM-RAG-AC1 | Tutor answer 保留真实 `source_refs` |
| LLM-RAG-AC2 | Agent trace 能看出使用 LLM provider 或 fallback |
| LLM-RAG-AC3 | answer 不扩写资料中不存在的关键结论 |
| LLM-RAG-AC4 | provider 失败时 fallback 仍返回 rule-based answer |
| LLM-RAG-AC5 | 默认无 key 本地演示不崩溃 |

## 失败判定

- response 没有 `source_refs`。
- trace 没有 LLM provider 或 fallback 线索。
- answer 声称资料包含实际未导入的内容。
- provider 失败后接口直接 500，且未按 `LLM_FALLBACK_MODE=rule_based` 回退。
- 日志、trace 或前端展示中出现真实 API key。
