# RAG Demo Runbook

最后更新：2026-06-15

面向角色：演示者 / Builder Agent / Reviewer Agent

本文档用于稳定演示当前项目的真实 RAG 第一阶段能力：

```text
真实课程资料导入
-> 后端切片入库
-> keyword retrieval 命中 chunk
-> Tutor grounded answer
-> source_ref 展示
-> Agent trace 展示具体来源
```

## 当前能力边界

### 已完成

- 支持前端 `Knowledge setup` 粘贴 `text` / `markdown` 资料。
- 支持 API 导入 `text` / `markdown` 资料。
- 支持写入 `documents` / `document_chunks`。
- 支持稳定来源标识：

```text
document:{document_id}#chunk:{chunk_index}
```

- 支持 `POST /api/v1/knowledge/search` 检索真实导入 chunk。
- Tutor / Resource response 保留真实 `source_refs`。
- Agent trace 显示具体 grounded sources。
- 默认离线可演示，不需要真实 LLM API key。

### 未完成

- 不支持 PDF / Word / PPT 文件上传解析。
- 不支持 multipart 文件上传。
- 当前检索是 keyword retrieval，不是 embedding / vector search。
- 默认 Tutor 可使用 rule-based fallback，不代表每次都调用真实 LLM。

## 推荐演示路径

### 1. 启动本地服务

在仓库根目录运行：

```powershell
cd E:\study\obsidian\软件杯\software-cup-a3-project
.\scripts\run-local.ps1
```

默认访问地址：

```text
Frontend: http://127.0.0.1:5173
Backend:  http://127.0.0.1:8000
Swagger:  http://127.0.0.1:8000/docs
```

### 2. 加载 demo data

在前端点击：

```text
Load or refresh demo data
```

预期结果：

- 页面显示 `Loaded`。
- 课程图谱出现。
- 默认 3 个学生画像出现。

### 3. 导入 RAG 资料

在前端 `Knowledge setup` 区域输入：

| 字段 | 推荐值 |
|---|---|
| title | `bfs-dfs-rag-note.md` |
| source_type | `markdown` |
| content | 使用 `data/samples/rag-manual/bfs-dfs-rag-note.md` 内容 |

点击：

```text
Import knowledge
```

预期结果：

- 显示 `Document #...`。
- 显示 chunk 数量。
- 显示至少 1 个 `document:{id}#chunk:{index}`。

### 4. 检索 imported chunks

在 `Search imported chunks` 输入：

```text
BFS 无权图 最短路径 queue DFS
```

预期结果：

- 检索结果显示 `document:{id}#chunk:{index}`。
- score 有值。
- 命中的 source_ref 应来自刚导入的 document。

### 5. Tutor 提问

在 Tutor 输入：

```text
为什么 BFS 在无权图中第一次到达节点就代表最少边数？请和 DFS 对比。
```

预期结果：

- Tutor answer 能解释：
  - BFS 按层扩展。
  - BFS 使用 queue。
  - 无权图中第一次到达节点对应最少边数。
  - DFS 更适合深度遍历 / 回溯，但不保证最短路径。
- Tutor answer 下方出现 grounded source。
- grounded source 包含 `document:{id}#chunk:{index}`。

### 6. 查看 Agent trace

找到最新 Tutor run，查看：

```text
Agent run trace
```

预期结果：

- 有 `tutor_answer` 或 Tutor 相关 step。
- `Output` / `Decision` 中出现：

```text
Grounded sources: document:{id}#chunk:{index}
```

## API 手动验证

如果前端不方便操作，可以用 PowerShell 调 API。

### 1. 加载 demo data

```powershell
$status = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/demo-data/load"

$courseId = $status.demo_data.course_id
$courseId
```

预期：

```text
1
```

### 2. 正确读取 UTF-8 文件

不要使用下面这种写法：

```powershell
$content = Get-Content -Raw -Encoding UTF8 "data/samples/rag-manual/bfs-dfs-rag-note.md"
```

在部分 PowerShell 版本或调用方式下，它可能把额外对象属性带进 JSON，导致后端收到的 `content` 不是纯字符串。

推荐使用：

```powershell
$content = [System.IO.File]::ReadAllText(
  (Resolve-Path "data/samples/rag-manual/bfs-dfs-rag-note.md"),
  [System.Text.Encoding]::UTF8
)
```

### 3. 导入资料

```powershell
$payload = [ordered]@{
  title = "bfs-dfs-rag-note.md"
  source_type = "markdown"
  content = $content
}

$body = $payload | ConvertTo-Json -Depth 5

$doc = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/courses/$courseId/documents" `
  -ContentType "application/json; charset=utf-8" `
  -Body ([System.Text.Encoding]::UTF8.GetBytes($body))

$doc.document.id
$doc.chunk_count
$doc.chunks[0].source_ref
```

预期：

```text
document_id 为数字
chunk_count >= 1
source_ref 形如 document:{id}#chunk:0
```

### 4. 检索资料

```powershell
$searchBody = @{
  course_id = $courseId
  query = "BFS 无权图 最短路径 queue DFS"
  top_k = 3
} | ConvertTo-Json -Depth 5

$search = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/knowledge/search" `
  -ContentType "application/json; charset=utf-8" `
  -Body ([System.Text.Encoding]::UTF8.GetBytes($searchBody))

$search.results | Select-Object chunk_id, score, source_ref
```

预期：

- `results` 非空。
- `source_ref` 指向刚导入的 document。
- `metadata.retrieval_mode` 为 `keyword`。

### 5. Tutor 提问

先选一个学生画像：

```powershell
$profiles = Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/api/v1/student-profiles"

$profileId = $profiles[0].id
```

调用 Tutor：

```powershell
$tutorBody = @{
  student_profile_id = $profileId
  course_id = $courseId
  question = "为什么 BFS 在无权图中第一次到达节点就代表最少边数？请和 DFS 对比。"
} | ConvertTo-Json -Depth 5

$tutor = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/tutor/ask" `
  -ContentType "application/json; charset=utf-8" `
  -Body ([System.Text.Encoding]::UTF8.GetBytes($tutorBody))

$tutor.answer
$tutor.source_refs
$tutor.agent_run_id
```

预期：

- `answer` 不为空。
- `source_refs` 至少包含 1 个真实 `document:{id}#chunk:{index}`。
- `agent_run_id` 不为空。

### 6. 查询 Agent trace

```powershell
$run = Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/api/v1/agent-runs/$($tutor.agent_run_id)"

$run.steps | Select-Object step_name, status, output_summary, decision_basis
```

预期：

```text
output_summary 或 decision_basis 包含 Grounded sources: document:{id}#chunk:{index}
```

## PowerShell 中文乱码问题

### 问题现象

在 Windows PowerShell / CMD 中，可能看到：

```text
??????
鎴戝熀纭€
涓轰粈涔?
```

这通常是终端显示编码问题，不一定代表：

- 文件内容坏了。
- API 导入失败。
- 后端返回错误。
- RAG 没有命中。

### 演示时不要依赖中文终端输出

RAG 演示检查优先看这些稳定字段：

| 字段 | 判断方式 |
|---|---|
| `document.id` | 是数字 |
| `chunk_count` | 大于等于 1 |
| `source_ref` | 形如 `document:{id}#chunk:{index}` |
| `results.length` | 大于 0 |
| `agent_run_id` | 是数字 |
| `decision_basis` | 包含 `Grounded sources:` |

### 推荐设置 PowerShell 编码

在当前 PowerShell 会话先运行：

```powershell
chcp 65001
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

如果仍然乱码，不要继续在终端里判断中文正文，改用文件方式检查。

### 将 API 输出写入 UTF-8 文件

```powershell
$json = $tutor | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText(
  (Join-Path (Get-Location) "data/samples/rag-manual/tutor-output.json"),
  $json,
  [System.Text.Encoding]::UTF8
)
```

然后用 VS Code / Obsidian / Typora 打开：

```text
data/samples/rag-manual/tutor-output.json
```

这样比直接看 PowerShell 输出更稳定。

### 只检查结构化字段

如果终端中文乱码，可以只输出结构化字段：

```powershell
[pscustomobject]@{
  DocumentId = $doc.document.id
  ChunkCount = $doc.chunk_count
  FirstSourceRef = $doc.chunks[0].source_ref
  SearchHitCount = $search.results.Count
  TutorRunId = $tutor.agent_run_id
  TutorSourceRef = $tutor.source_refs[0].source_ref
}
```

只要这些字段正确，RAG 链路就基本成立。

## 通过标准

| ID | 标准 |
|---|---|
| RAG-DEMO-AC1 | 能导入 `text` / `markdown` 资料 |
| RAG-DEMO-AC2 | 导入后返回 `document_id` 和 `chunk_count` |
| RAG-DEMO-AC3 | `knowledge/search` 能命中真实导入 chunk |
| RAG-DEMO-AC4 | Tutor answer 保留真实 `source_refs` |
| RAG-DEMO-AC5 | Agent trace 显示具体 `Grounded sources` |
| RAG-DEMO-AC6 | 无 LLM API key 时仍能完成演示 |
| RAG-DEMO-AC7 | 终端中文乱码时，仍能通过结构化字段验证链路 |

## 失败判定

| 现象 | 结论 | 处理 |
|---|---|---|
| 导入接口返回 400 `content should be string` | PowerShell 读取内容方式错误 | 使用 `[System.IO.File]::ReadAllText()` |
| 搜索结果为空 | query 未命中或资料未导入到当前 course | 重新导入资料，换 BFS/queue/DFS 关键词 |
| Tutor 没有 `source_refs` | retrieval 没命中或 course/profile 不匹配 | 先单独跑 `/knowledge/search` |
| Agent trace 没有 `Grounded sources` | trace 来源未写入或查看了旧 run | 查看最新 `agent_run_id` |
| 中文正文乱码但 source_ref 正常 | 终端编码问题 | 用 UTF-8 文件或结构化字段检查 |
| `document:...#chunk:...` 不出现 | RAG 链路未成立 | 不通过，需要修复 |

## 推荐演示话术

```text
这里我们导入的是一段真实课程资料，不是写死在 Tutor 里的答案。
系统会把资料保存为 document，再切成 document_chunks。
后续 Tutor 和 Resource 回答时，会先检索这些 chunks，并在回答和 Agent trace 中保留 source_ref。
当前版本使用的是本地 keyword retrieval，默认不需要联网和 API key；如果启用 LLMProvider，可以让真实大模型基于同样的检索结果回答。
```

