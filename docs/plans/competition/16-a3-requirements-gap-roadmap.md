# A3 赛题差距与 AI 改造路线图

最后更新：2026-07-13

状态：待进入任务执行阶段

主要受众：开发团队
依据：[A3 赛题要求（官网原版）](../../competition/a3-official-requirements-original.md)、[A3 官方赛题要求整理](../../competition/a3-official-requirements.md)、[当前项目赛题对齐分析](../../competition/competition-fit.md)、当前仓库代码与测试状态。

## 1. 文档目标

本文档将官网要求与当前项目差距转换为**可实施、可测试、可验收**的开发任务，并明确 AI 接入边界：

1. **已经接入 LLM 的能力不重复开发**，只补齐科大讯飞星火比赛启动配置、真实调用验证和运行证据。
2. **应该接入但尚未接入 LLM 的能力必须完成开发**，包括初始画像构建、Hybrid 学习路径规划和 Quiz 生成。
3. **不适合交给 LLM 的确定性能力继续使用 rule-based**，包括 Router、状态机、先修约束、引用校验、安全底线和客观题评分。
4. 比赛主流程采用“**LLM 负责语义理解、个性化生成和开放式分析，规则负责约束、校验和故障降级**”的 Hybrid AI 架构。

本文档不修改已 Accepted 的 FastAPI、React、service、adapter 和 orchestrator 架构基线，不把“代码中存在 LLM 类”当作“比赛流程已经使用 LLM”的完成证据。

## 2. 赛题核心要求与当前结论

官网核心要求包括：

- 通过自然语言对话自动抽取特征，形成不少于 **6 个维度**的动态学生画像。
- 体现 **Multi-Agent** 角色分工与协作关系。
- 由大模型结合学生专业、课程内容、知识短板和学习需求，生成至少 **5 类**个性化资源。
- 根据学生进度、掌握情况和偏好形成动态学习路径与精准资源推送。
- 建立防幻觉、内容安全、合理响应时间和失败处理机制。
- 智能辅导与学习效果评估属于可选加分项，但当前项目已经具备相应基础，应纳入比赛闭环。

当前项目已经建立 Multi-Agent、RAG、五类资源接口、Tutor、Quiz、Evaluator、画像更新和 Agent trace 基础，但默认启动仍是 **rule-based**。在核心 AI 主链路和真实星火调用证据完成前，只能表述为“**已实现部分核心能力和离线 MVP 闭环**”，不能表述为“已完成赛题核心 AI 要求”。

## 3. 当前能力分类与处理原则

| 功能 | 当前实际状态 | 目标形态 | 路线图处理 |
|---|---|---|---|
| Tutor | 已有 `LLMBackedTutorAgent`，默认关闭 | LLM + RAG 主处理，规则 fallback | 不重复开发；通过星火比赛入口默认启用并完成联机验证 |
| 五类资源生成 | 已有 `LLMBackedResourceAgent`，默认关闭 | LLM + RAG + Critic | 不重复开发；验证五类资源具有真实内容与格式差异 |
| Evaluator | 已有 `LLMBackedEvaluatorAgent`，默认关闭 | 开放题 LLM rubric，客观题规则评分 | 不重复开发；默认启用并验证结构化评价 |
| 动态画像更新 | 已有 `LLMBackedProfileUpdaterAgent`，默认关闭 | LLM 分析 trace，规则校验和写入 | 不重复开发；默认启用并验证画像历史 |
| 初始对话画像 | 关键词和默认值规则 | LLM 结构化抽取 + schema + fallback | **必须完成新开发** |
| 学习路径规划 | 按 `Concept.id` 固定排序 | 知识图谱约束 + LLM 排序与解释 | **必须完成新开发** |
| Quiz 生成 | 固定题干模板 | LLM 生成 + schema + Critic + fallback | **必须完成新开发** |
| 主动资源推荐 | 尚无真正智能排序 | Planner 统一输出下一节点、资源类型和理由 | **纳入 Hybrid Planner 开发** |
| Router | 固定任务分发 | Rule-based | 保持现状，不进行 LLM 化 |
| Critic 与引用校验 | 确定性规则 | Rule-based 为主 | 保持并增强安全规则，不用 LLM 替代硬校验 |
| RAG retrieval | Keyword 为默认，Embedding/Hybrid 可选 | Keyword + optional vector/hybrid | 保留稳定基础，不要求每次检索调用 LLM |
| 客观题评分 | 规则比对 | Rule-based | 保持确定性评分 |
| 开放题评分 | 已有 LLM Evaluator | LLM rubric + 规则聚合 | 直接启用，不重复开发 |

## 4. AI 接入判断标准

新功能进入任务系统前，按照下表判断是否需要接入大模型。

| 判断维度 | 倾向 rule-based | 倾向 LLM/Hybrid AI |
|---|---|---|
| 输入形式 | 固定字段、枚举、状态 | 开放自然语言、多轮上下文 |
| 输出形式 | 唯一正确值 | 多种合理答案或内容生成 |
| 语义复杂度 | 关键词和显式条件足够 | 存在隐含意图、否定、指代和上下文依赖 |
| 个性化深度 | 少量字段映射 | 需要综合画像、历史、目标和掌握度 |
| 确定性要求 | 必须可复现且不可越界 | 允许在规则边界内产生差异 |
| 错误风险 | 涉及事务、安全、权限或真实引用 | 内容质量问题可由 schema、Critic 和 fallback 控制 |
| 赛题证明价值 | 主要证明工程稳定性 | 能直接证明大模型理解、生成和分析能力 |

满足开放语义理解、个性化生成或复杂学习状态分析的功能优先采用 LLM；涉及真实数据约束、事务、安全和唯一正确结果的功能保持 rule-based；同时具备两类特征的功能采用 Hybrid AI。

## 5. 优先级定义

| 优先级 | 含义 | 执行原则 |
|---|---|---|
| P0 | 影响官网硬性要求、核心 AI 证据或初赛交付 | 必须完成并形成自动化与联机验收证据 |
| P1 | 影响个性化深度、多模态展示或可选加分项 | P0 主链路稳定后执行 |
| P2 | 生产化和长期工程增强 | 不得阻塞比赛 MVP 和提交材料 |

## 6. P0：完成赛题核心 AI 主链路

### COMP-001：构造完整高校专业课程知识库

**对应要求：** 至少自行构造一门完整高校专业课程的初始知识库或文档集。

**完成后效果：** 评委能够看到完整《数据结构》课程的章节、知识点、先修关系、讲义、题目和代码案例；Tutor、Resource、Planner 和 Quiz 能引用真实课程资料。

**主要工作：**

- 补齐复杂度、线性表、栈与队列、树、图、查找和排序等主要章节。
- 为章节建立知识点、学习目标、难度和先修关系。
- 为主要知识点准备讲义、例题、练习题、易错点和代码案例。
- 将资料导入现有 RAG 流程，记录课程来源和覆盖范围。

**验收标准：**

- [ ] 至少一门完整课程有章节目录、课程说明和知识点图。
- [ ] 每章都有可检索资料，主要知识点存在真实 `source_ref`。
- [ ] 知识点图包含可用于 Planner 校验的先修关系。
- [ ] 完成一次“课程导入 → 检索 → 资源生成”演示。

### COMP-002：完成初始对话画像 LLM 接入

**对应要求：** 通过自然语言对话自动抽取不少于 6 个维度的学生特征。

**当前差距：** `profile_builder.py` 依赖关键词和默认值，无法可靠理解否定、隐含偏好、多目标和多轮上下文。

**完成后效果：** 学生使用自然语言描述学习经历、目标和偏好后，由 **LLMProfileBuilderAgent** 输出结构化画像；模型失败时才回退到现有规则实现。

**主要工作：**

- 新增 `LLMProfileBuilderAgent` 和 factory，输入对话文本与允许使用的用户上下文。
- 输出 `learning_goal`、`foundation_level`、`learning_preference`、`available_time`、`weak_points`、`resource_preference` 等不少于 6 个维度。
- 使用 JSON schema/Pydantic 校验必填字段、枚举、长度和列表数量。
- 新增 `LLM_ENABLE_FOR_PROFILE_BUILDER`，默认离线为 `false`，比赛入口为 `true`。
- 保留现有 `build_profile_from_dialogue()` 作为 `rule_based_fallback`。
- 在画像历史和 Agent trace 中记录执行模式、更新原因和证据摘要，不记录完整 prompt。
- 保持现有画像 API contract，避免前端破坏性改造。

**验收标准：**

- [ ] 星火配置完整时 factory 构造 LLM-backed ProfileBuilder。
- [ ] 复杂自然语言输入能生成不少于 6 个合法维度。
- [ ] 否定表达和隐含偏好不会被简单关键词反向误判。
- [ ] 非法 JSON、超时或 HTTP 错误时回退规则实现并记录原因。
- [ ] 初始画像历史能区分 `llm` 与 `rule_based_fallback`。

### COMP-003：完成 Hybrid 学习路径与主动资源推荐

**对应要求：** 根据专业、进度、掌握情况和学习偏好生成动态路径并精准推送资源。

**当前差距：** 路径主要按 `Concept.id` 排序，画像信息主要出现在说明文案中，尚未形成真实决策差异。

**完成后效果：** 规则层根据知识点图产生合法候选集合，**LLM Planner** 根据画像和学习历史排序候选节点，输出下一节点、推荐资源类型、理由和优先级。

**主要工作：**

- 新增 LLM/Hybrid Planner agent、factory 和 `LLM_ENABLE_FOR_PLANNER`。
- 规则层读取知识点、先修关系、已完成节点、测验掌握度和画像，执行拓扑排序并生成合法候选集合。
- LLM 只能对合法候选排序和解释，不得创建不存在的知识点或绕过先修约束。
- 对 LLM 输出执行 schema、未知节点、重复节点、环和先修关系校验。
- LLM 输出无效时回退到确定性拓扑排序，不再使用裸 `Concept.id` 顺序。
- 在路径节点中提供推荐资源类型、业务级推荐理由和优先级；保持 `/api/v1` 现有字段兼容，仅做可选字段扩展。
- Quiz、画像或路径节点完成后重新计算下一步推荐，重复事件保持幂等。

**验收标准：**

- [ ] Planner 输出仅包含真实知识点且不违反先修关系。
- [ ] 两个不同画像对同一课程目标产生可观察的顺序或资源差异。
- [ ] Quiz 暴露薄弱点后，下一节点或推荐资源发生可解释变化。
- [ ] 路径包含步骤、顺序、推荐资源、理由和优先级。
- [ ] LLM 失败时生成合法拓扑路径并记录 fallback reason。

### COMP-004：完成 Quiz LLM 接入

**对应要求：** 生成不同类型、符合学生水平和知识短板的个性化练习题。

**当前差距：** `RuleBasedQuizAgent` 使用固定题干模板，不能证明题型、错误模式和学习历史驱动的个性化生成。

**完成后效果：** **LLMQuizAgent** 根据课程资料、画像、掌握度、目标难度和最近错误生成结构化题目，现有规则 Quiz 仅作为 fallback。

**主要工作：**

- 新增 `LLMQuizAgent`、factory 和 `LLM_ENABLE_FOR_QUIZ`。
- 支持选择、填空、简答、应用和代码分析等题型。
- 使用 schema 返回题干、题型、答案、解析、难度、知识点标签和引用来源。
- 继续使用 `RuleBasedCriticAgent` 检查答案与解析完整性、难度适配、代码块和引用。
- 客观题继续确定性判分；开放题交给已有 `LLMBackedEvaluatorAgent`，最终掌握度由规则聚合。
- 对检索为空、非法 JSON、超时和 provider 错误执行明确 fallback。

**验收标准：**

- [ ] 星火配置完整时 Quiz factory 构造 LLM-backed Agent。
- [ ] 不同画像或薄弱点生成不同题型、难度或题目内容。
- [ ] 题目符合 schema，并能被 Critic、提交 API 和 Evaluator 正常处理。
- [ ] 题目引用来自真实课程资料，不生成伪造 `source_ref`。
- [ ] fallback 题目仍可完成后续评价闭环。

### COMP-005：新增科大讯飞星火比赛默认启动入口

**对应要求：** 在系统中融合大模型，并按官网要求优先使用科大讯飞相关工具形成可运行作品。

**完成后效果：** 使用一个明确的比赛启动命令，即可默认启用星火大模型和全部 LLM 能力；离线开发入口保持稳定。

**实现约束：**

- 新增 `scripts/run-competition-spark.ps1`，内部复用 `scripts/run-local.ps1`。
- 复用现有 `OpenAICompatibleLLMProvider`，不重复开发星火专用 adapter。
- 默认 `LLM_BASE_URL=https://maas-api.cn-huabei-1.xf-yun.com/v2`，与服务管控页面显示一致。
- 默认 `LLM_MODEL=xop3qwen1b7`，以该服务 `/models` 实际返回结果为准，并允许通过脚本参数覆盖。
- 从进程环境变量或用户级环境变量 `XFYUN_SPARK_API_KEY` 读取 MaaS APIKey。
- 缺少密钥时立即失败并给出安全配置方法，不静默进入全 rule-based 模式。
- 设置 `LLM_PROVIDER=openai_compatible`、合理 timeout/retry 和 `LLM_FALLBACK_MODE=rule_based`。
- 默认启用 Tutor、Resource、Evaluator、ProfileUpdater、ProfileBuilder、Planner 和 Quiz。
- 脚本退出后恢复调用前环境变量，不泄露或持久化密钥。
- `run-local.ps1` 继续作为离线开发和自动测试入口，默认保持 rule-based。

科大讯飞官方 HTTP API 依据：[推理服务 HTTP 协议](https://www.xfyun.cn/doc/spark/%E6%8E%A8%E7%90%86%E6%9C%8D%E5%8A%A1-http.html)。该服务使用 OpenAI-compatible `chat/completions` 和 Bearer APIKey，可复用当前 adapter。

**比赛入口默认开关：**

```text
LLM_ENABLE_FOR_TUTOR=true
LLM_ENABLE_FOR_RESOURCE=true
LLM_ENABLE_FOR_EVALUATOR=true
LLM_ENABLE_FOR_PROFILE_UPDATER=true
LLM_ENABLE_FOR_PROFILE_BUILDER=true
LLM_ENABLE_FOR_PLANNER=true
LLM_ENABLE_FOR_QUIZ=true
```

**验收标准：**

- [ ] 缺少 `XFYUN_SPARK_API_KEY` 时脚本在启动服务前明确失败。
- [ ] 配置完整时所有 factory 选择对应 LLM-backed Agent。
- [ ] `-SmokeOnly` 能验证后端、前端和星火配置，不泄露密钥。
- [ ] 单次远程调用失败时业务可按配置降级，且 trace 明确记录原因。
- [ ] `run-local.ps1` 的默认离线行为和现有自动化测试不受影响。

### COMP-006：启用并验证已经接入的 LLM 能力

**定位：** Tutor、Resource、Evaluator 和 ProfileUpdater 已经具备 LLM 实现，本任务禁止重复开发这些 Agent，只完成星火启用、兼容性修正和验收证据。

**主要工作：**

- 通过比赛启动入口默认启用四项已有能力。
- 为星火返回格式补充必要的兼容性测试；仅在真实不兼容时修改公共 adapter。
- 验证五类 Resource 输出具有资源类型差异和画像差异，而不是五份普通讲义。
- 验证 Tutor 只基于 RAG 检索资料回答，资料不足时明确说明限制。
- 验证 Evaluator 返回合法结构化评分、反馈和掌握度建议。
- 验证 ProfileUpdater 根据真实 Agent trace 更新画像并写入历史。
- 验证所有失败路径保留 fallback reason。

**验收标准：**

- [ ] 五类资源均由星火真实生成并通过 Critic。
- [ ] Tutor 的主要事实断言能够追溯到真实 `source_ref`。
- [ ] Evaluator 非法 JSON 会被拒绝或安全 fallback。
- [ ] ProfileUpdater 无新证据时不会伪造画像变化。
- [ ] 自动化测试证明上述能力没有被重新实现为第二套重复架构。

### COMP-007：统一 LLM 配置与运行证据

**完成后效果：** 开发者和评委能够判断每一步实际使用了星火还是 rule-based fallback，而不暴露敏感信息或模型隐式推理过程。

**主要工作：**

- 在 `LLMSettings` 增加 ProfileBuilder、Planner 和 Quiz 三个 purpose 开关。
- Agent trace 记录 `execution_mode`、`provider`、`model`、`fallback_used`、`fallback_reason`、`source_refs` 和响应耗时。
- 优先复用现有 Agent run 数据结构或 metadata；只有现有结构无法表达时才进行最小 additive schema 变更。
- 前端默认展示业务结果；技术 trace 保持折叠或演示模式可见。
- 禁止记录 API key、完整 prompt、完整上下文和 chain-of-thought。

**验收标准：**

- [ ] 每个核心 Agent run 能区分 `llm`、`rule_based` 和 `rule_based_fallback`。
- [ ] provider/model 与实际启动配置一致。
- [ ] fallback reason 能定位 timeout、HTTP、解析、检索为空或安全拦截。
- [ ] 数据库、API、日志和前端均不包含密钥。

### COMP-008：建立防幻觉与内容安全验证闭环

**对应要求：** 具备防幻觉与内容安全过滤机制。

**完成后效果：** 当资料不足、检索为空、输入越界、模型输出非法或服务失败时，系统能够拒绝编造、说明限制并安全降级。

**主要工作：**

- 固化“资料不足不编造”策略和真实引用白名单。
- 增加 fake source、unsupported claim、Prompt injection、敏感内容和危险代码测试。
- 对生成资源执行确定性格式与安全检查，必要时再调用模型辅助审核，但模型审核不得替代硬规则。
- 为拒答、拦截、降级和 fallback 提供清晰提示。

**验收标准：**

- [ ] 无检索结果时不生成伪造来源。
- [ ] 输出引用均来自当前请求实际检索结果。
- [ ] 恶意或越界输入触发安全拒答或降级。
- [ ] LLM 失败时页面不白屏，并显示明确状态。
- [ ] 有可提交的防幻觉与安全测试记录。

### COMP-009：完成比赛交付文档与合规材料

**主要工作：**

- 编写系统开发说明书和测试说明书。
- 记录依赖名称、版本、来源、license 和使用位置。
- 编写 AI Coding 工具和科大讯飞星火 API 使用说明。
- 用架构图和流程图说明 Multi-Agent、RAG、LLM、规则边界、fallback 和安全策略。
- 明确哪些能力已完成、部分完成、默认启用或仅为 fallback。

**验收标准：**

- [ ] 文档覆盖需求、设计、开发、测试、部署和优化。
- [ ] 第三方依赖和 AI 工具有完整来源与协议说明。
- [ ] 文档与当前代码、配置和演示行为一致。
- [ ] 不宣传尚未完成或仅存在接口占位的能力。

### COMP-010：冻结 7 分钟演示与初赛作品目录

**完成后效果：** 评委在 7 分钟内看到“课程资料 → 星火画像 → Hybrid 路径 → 五类资源 → Tutor → Quiz → Evaluator → 画像更新 → Multi-Agent trace”的完整闭环。

**主要工作：**

- 固定 `run-competition-spark.ps1` 为比赛演示默认入口。
- 编写 7 分钟脚本和时间分配表。
- 固定课程资料、两组对比画像、问题、Quiz 和 reset 流程。
- 制作 PPT，覆盖价值、架构、AI/rule-based 边界、核心功能和创新点。
- 建立源码、数据、配置、运行说明和测试证据的提交目录。

**验收标准：**

- [ ] 视频不超过 7 分钟并覆盖核心 AI 主链路。
- [ ] trace 能证明关键步骤实际调用星火而非全部 fallback。
- [ ] 两组画像产生可观察的路径、资源和题目差异。
- [ ] 提交文件能在常规环境按说明启动。
- [ ] 现场演示连续跑通两次，失败演练能够安全降级。

## 7. Rule-based 保留边界

以下能力不得为了“增加 AI 数量”而改造成 LLM 决策：

- Router 的 API 意图到 Agent 的确定性分发。
- 数据库事务、幂等处理和学习节点状态机。
- 课程先修关系、候选知识点集合和路径环校验。
- Pydantic/JSON schema 校验。
- RAG 文档权限、课程范围和引用真实性检查。
- Critic 的格式、安全、难度和来源底线。
- 客观题、数值题、固定答案题和代码单元测试评分。
- API 权限、参数校验、错误码和 secret 管理。
- 离线 fallback、自动化测试和无网络 smoke 模式。

LLM 可以提供建议、排序、内容和开放式分析，但不能直接绕过上述约束或决定数据库事务是否提交。

## 8. P1：增强评分与加分项

### COMP-011：实现真实可验证的教学动画或视频资源

**完成后效果：** 至少一个知识点存在真实可播放或可交互的教学动画/视频，不把脚本、封面或分镜伪装成已生成视频。

**验收标准：**

- [ ] 产物真实可播放或交互。
- [ ] 内容与画像、路径节点或薄弱点有明确关系。
- [ ] 生成失败时显示真实状态和替代材料。
- [ ] 资源卡片展示类型、状态和来源。

### COMP-012：增强学习效果评估与掌握度模型

**完成后效果：** 系统区分初始、学习后和测验后的掌握状态，并据此调整路径、推荐或题目难度。

**验收标准：**

- [ ] 评价包含分项得分、薄弱点和真实证据。
- [ ] LLM 只输出 rubric 分析，最终掌握度由规则聚合并限制范围。
- [ ] 评估能触发路径或资源推荐变化。
- [ ] 前端展示掌握度变化和下一步调整。

### COMP-013：补齐失败路径、跨环境和移动端测试

**验收标准：**

- [ ] 覆盖星火 timeout、HTTP error、非法 JSON、RAG 无命中和资源生成失败。
- [ ] 覆盖空状态、错误状态、重复操作和恢复流程。
- [ ] 至少验证一种桌面浏览器和一种移动视口。
- [ ] 结果写入测试说明书。

### COMP-014：统一项目状态、需求和验收文档

**验收标准：**

- [ ] README、需求、状态、任务和比赛文档无明显矛盾。
- [ ] 每项官网硬性要求都有对应状态和证据。
- [ ] 已完成、部分完成、已接入未启用、默认启用和 fallback 明确区分。
- [ ] 关键结论能链接到代码、测试或运行记录。

## 9. P2：生产化增强，不阻塞比赛交付

### COMP-015：正式数据库、向量检索和异步任务增强

为生产部署提供 PostgreSQL、`pgvector` 和任务队列支持，同时保持 SQLite 离线演示可用。所有增强均为 opt-in，不改变 `/api/v1` contract，不把外部服务变成比赛现场启动前置条件。

### COMP-016：认证、多用户隔离和长期学习历史

支持真实用户、长期学习历史和更严格的数据隔离。该任务需要单独设计认证、数据所有权和隐私保护方案，不阻塞当前比赛 MVP。

## 10. 推荐执行顺序

```text
COMP-001 完整课程知识库
    -> COMP-002 LLM 初始画像
    -> COMP-003 Hybrid Planner 与主动推荐
    -> COMP-004 LLM Quiz
    -> COMP-005 星火比赛默认启动入口
    -> COMP-006 启用并验证已有 LLM 能力
    -> COMP-007 统一配置与运行证据
    -> COMP-008 防幻觉与内容安全
    -> COMP-009 比赛文档与合规材料
    -> COMP-010 7 分钟演示与提交目录
    -> COMP-011 至 COMP-014 P1 增强
    -> COMP-015 至 COMP-016 P2 生产化增强
```

COMP-002 至 COMP-004 可在接口边界明确后并行开发；COMP-005 可并行准备，但最终必须启用新增的三个 purpose 开关。COMP-006 不得在 COMP-005 之前重复实现已有 Agent。

## 11. 自动化与联机测试矩阵

| 场景 | 自动化要求 | 联机要求 |
|---|---|---|
| 星火配置 | 完整配置构造 LLM-backed factory；缺少密钥脚本失败 | 使用真实星火完成健康验证 |
| 初始画像 | schema、6 维、非法 JSON、fallback | 复杂自然语言得到合理画像 |
| Planner | 未知节点、重复、环、先修约束、拓扑 fallback | 两组画像产生可观察差异 |
| Quiz | 多题型 schema、Critic、fallback | 星火生成题目可提交并评价 |
| Resource | 五类格式 contract 和引用校验 | 五类输出内容与格式明显不同 |
| Tutor | 无检索结果、伪造引用、provider failure | 回答可追溯真实课程资料 |
| Evaluator | JSON 解析、分数范围、fallback | 开放题反馈与 rubric 一致 |
| ProfileUpdater | 幂等、无证据不更新、fallback | Quiz 后画像历史产生可解释变化 |
| Agent trace | secret 检查、模式和 fallback 字段 | 证明主链路实际调用星火 |
| 离线兼容 | 现有 rule-based 测试和 `run-local.ps1` 继续通过 | 不要求外部网络 |

## 12. P0 完成判定

只有同时满足以下条件，项目才可以对外表述为“**完成赛题核心 AI 接入**”：

- [ ] 有一门完整高校专业课程知识库和真实 RAG 来源。
- [ ] 初始对话画像由 LLM 主处理，包含不少于 6 个维度并保留规则 fallback。
- [ ] 动态画像更新默认使用星火并有前后差异、原因和证据。
- [ ] Planner 由知识图谱硬约束和 LLM 排序共同驱动，不再按裸 `Concept.id` 生成主路径。
- [ ] Quiz 由 LLM 主生成，符合 schema、Critic 和真实引用要求。
- [ ] Tutor、Resource、Evaluator、ProfileUpdater 没有重复开发，并通过比赛入口默认启用。
- [ ] 至少 5 类个性化资源由星火真实生成并稳定展示。
- [ ] Quiz 或学习行为能够触发下一节点或资源推荐变化。
- [ ] Agent trace 能核验 provider、model、执行模式、耗时和 fallback，不包含 secret 或完整 prompt。
- [ ] 防幻觉、安全和失败路径有自动化及联机验证记录。
- [ ] `run-competition-spark.ps1` 是比赛默认入口，`run-local.ps1` 继续支持离线开发。
- [ ] 系统开发说明书、测试说明书、依赖协议清单、AI 工具说明、PPT 和 7 分钟以内视频形成可提交目录。

在清单全部完成前，对外表述必须使用“已完成部分核心能力”“已具备 LLM 可选接入”或“完成离线 MVP 演示闭环”，不能把可选配置、fallback 模板或未验证接口表述为已完成的 AI 能力。
