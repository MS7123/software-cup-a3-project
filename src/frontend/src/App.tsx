import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import rehypeKatex from "rehype-katex";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import "katex/dist/katex.min.css";

import { api } from "./api/client";
import type {
  AgentRun,
  Concept,
  ConceptGraph,
  DemoDataStatus,
  DocumentIngestionResponse,
  DocumentReindexResponse,
  EvaluationResult,
  GeneratedResource,
  KnowledgeSearchResult,
  LearningFlow,
  LearningPathItem,
  ManagedDocument,
  Quiz,
  StudentProfile
} from "./api/types";

type BusyAction =
  | "load-demo"
  | "reset-demo"
  | "build-profile"
  | "delete-profile"
  | "import-knowledge"
  | "upload-knowledge"
  | "refresh-documents"
  | "delete-document"
  | "reindex-document"
  | "search-knowledge"
  | "create-path"
  | "generate-resource"
  | "ask-tutor"
  | "generate-quiz"
  | "submit-attempt"
  | "sync-profile";

type StepKey = "profile" | "kb" | "path" | "resource" | "tutor" | "quiz" | "assess";

type TutorMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sourceRefs?: Array<Record<string, unknown>>;
};

type TrackerStep = {
  label: string;
  detail: string;
  status: "done" | "active" | "pending";
};

const profileLabels: Record<string, string> = {
  weak_foundation: "基础薄弱型",
  exam_sprint: "考试冲刺型",
  algorithm_practice: "算法训练型"
};

const profileDimensions = [
  ["learning_goal", "学习目标"],
  ["foundation_level", "知识基础"],
  ["learning_preference", "认知风格"],
  ["available_time", "可用时间"],
  ["weak_points", "易错短板"],
  ["resource_preference", "资源偏好"]
] as const;

const resourceOptions = [
  { type: "guided_note", label: "讲解文档" },
  { type: "practice_questions", label: "练习题库" },
  { type: "mind_map", label: "思维导图" },
  { type: "extended_reading", label: "拓展阅读" },
  { type: "coding_case", label: "代码实操" },
  { type: "teaching_video", label: "教学动画" }
] as const;

const stepFlow: Array<{ key: StepKey; label: string; desc: string }> = [
  { key: "profile", label: "学生画像", desc: "通过自然语言对话抽取特征，形成六维动态画像" },
  { key: "kb", label: "知识库", desc: "导入课程资料，检索可追溯证据片段" },
  { key: "path", label: "学习路径", desc: "根据画像、课程图谱和目标规划学习顺序" },
  { key: "resource", label: "资源生成", desc: "生成文档、题库、思维导图、拓展阅读和实操案例" },
  { key: "tutor", label: "教师答疑", desc: "基于证据进行个性化答疑" },
  { key: "quiz", label: "智能测验", desc: "生成当前节点练习题并收集作答" },
  { key: "assess", label: "学习评估", desc: "评估学习效果并触发画像回写" }
];

const agentRoster = [
  { id: "profile", name: "画像顾问", role: "对话抽取特征，维护动态学生画像" },
  { id: "retriever", name: "资料管理员", role: "检索课程资料，输出可追溯证据" },
  { id: "planner", name: "学习规划师", role: "结合画像和掌握度重排学习路径" },
  { id: "resource", name: "资源设计师", role: "生成多类型个性化学习资源" },
  { id: "tutor", name: "答疑教师", role: "基于证据进行多轮答疑引导" },
  { id: "evaluator", name: "测评教师", role: "分析作答表现并回写画像建议" }
];

const stepAgents: Record<StepKey, { lead: string; support: string[] }> = {
  profile: { lead: "profile", support: [] },
  kb: { lead: "retriever", support: ["profile"] },
  path: { lead: "planner", support: ["profile", "evaluator"] },
  resource: { lead: "resource", support: ["retriever", "profile"] },
  tutor: { lead: "tutor", support: ["retriever"] },
  quiz: { lead: "evaluator", support: ["resource"] },
  assess: { lead: "evaluator", support: ["planner", "profile"] }
};

const agentTypeLabels: Record<string, string> = {
  planner: "学习规划师",
  resource: "资源设计师",
  tutor: "答疑教师",
  quiz: "出题老师",
  evaluator: "测评教师",
  profile_updater: "画像顾问",
  retriever: "资料管理员"
};

const runTypeLabels: Record<string, string> = {
  planner: "学习路径规划",
  resource: "学习资源生成",
  tutor: "教师答疑辅导",
  quiz: "练习测验生成",
  evaluator: "学习效果评估",
  profile_update: "学生画像更新"
};

const statusLabels: Record<string, string> = {
  completed: "已完成",
  success: "已完成",
  running: "执行中",
  failed: "失败",
  pending: "等待中",
  queued: "排队中"
};

function labelProfile(type: string): string {
  return profileLabels[type] ?? type.replaceAll("_", " ");
}

function toErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return "请求失败，请检查后端服务是否正常运行。";
}

function formatScore(value: unknown): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "暂无";
  return value.toFixed(2);
}

function formatList(value: unknown): string {
  if (!Array.isArray(value) || value.length === 0) return "暂无";
  return value.map((item) => String(item)).join("、");
}

function resourceLabel(type: string): string {
  return resourceOptions.find((item) => item.type === type)?.label ?? type;
}

function documentDisplayName(document: { title: string; file_name?: string | null }): string {
  return document.file_name || document.title || "未命名资料";
}

function resultDisplayName(result: KnowledgeSearchResult): string {
  return String(result.metadata?.filename ?? result.metadata?.source_title ?? result.source_ref ?? "知识来源");
}

export function App() {
  const [status, setStatus] = useState<DemoDataStatus | null>(null);
  const [profiles, setProfiles] = useState<StudentProfile[]>([]);
  const [graph, setGraph] = useState<ConceptGraph | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null);
  const [selectedPathItemId, setSelectedPathItemId] = useState<number | null>(null);
  const [profileDialogue, setProfileDialogue] = useState(
    "我最近在学习二叉树遍历和图搜索，递归边界容易出错。每天可以投入 1 小时，希望系统多给我图解、例题和代码实操。"
  );
  const [goal, setGoal] = useState("巩固二叉树遍历和图搜索，为课程小测做准备");
  const [knowledgeTitle, setKnowledgeTitle] = useState("数据结构学习笔记.md");
  const [knowledgeSourceType, setKnowledgeSourceType] = useState<"text" | "markdown">("markdown");
  const [knowledgeContent, setKnowledgeContent] = useState(
    "# 广度优先搜索与深度优先搜索\n广度优先搜索通常使用队列逐层扩展节点，适合求无权图最短路径；深度优先搜索通常使用递归或栈深入遍历，适合连通性判断、回溯和拓扑类问题。"
  );
  const [knowledgeQuery, setKnowledgeQuery] = useState("广度优先 搜索 队列 最短路径 深度优先");
  const [knowledgeFile, setKnowledgeFile] = useState<File | null>(null);
  const [knowledgeImportResult, setKnowledgeImportResult] = useState<DocumentIngestionResponse | null>(null);
  const [knowledgeReindexResult, setKnowledgeReindexResult] = useState<DocumentReindexResponse | null>(null);
  const [knowledgeDocuments, setKnowledgeDocuments] = useState<ManagedDocument[]>([]);
  const [knowledgeSearchResults, setKnowledgeSearchResults] = useState<KnowledgeSearchResult[]>([]);
  const [knowledgeError, setKnowledgeError] = useState<string | null>(null);
  const [flow, setFlow] = useState<LearningFlow | null>(null);
  const [resource, setResource] = useState<GeneratedResource | null>(null);
  const [resourceType, setResourceType] = useState<(typeof resourceOptions)[number]["type"]>("guided_note");
  const [question, setQuestion] = useState("我应该如何区分广度优先搜索和深度优先搜索？");
  const [tutorMessages, setTutorMessages] = useState<TutorMessage[]>([]);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [attemptText, setAttemptText] = useState("");
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [autoProfileUpdate, setAutoProfileUpdate] = useState<string | null>(null);
  const [autoProfileUpdateEnabled, setAutoProfileUpdateEnabled] = useState(true);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [busy, setBusy] = useState<BusyAction | null>(null);
  const [booting, setBooting] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [traceOpen, setTraceOpen] = useState(false);
  const [debugOpen, setDebugOpen] = useState(false);
  const [activeStep, setActiveStep] = useState<StepKey>("profile");
  const [profileDraft, setProfileDraft] = useState("");
  const chatScrollRef = useRef<HTMLDivElement | null>(null);

  const latestProfile = profiles[0] ?? null;
  const pathItems = flow?.learning_path.items ?? [];
  const selectedItem = pathItems.find((item) => item.id === selectedPathItemId) ?? pathItems[0] ?? null;
  const selectedConcept = useMemo<Concept | null>(() => {
    if (!graph) return null;
    if (selectedItem) return graph.concepts.find((concept) => concept.id === selectedItem.concept_id) ?? null;
    return graph.concepts[0] ?? null;
  }, [graph, selectedItem]);

  const canCreatePath = Boolean(selectedProfileId && status?.course_id);
  const canUseLoop = Boolean(selectedProfileId && status?.course_id && selectedConcept);
  const stepInfo = stepFlow.find((step) => step.key === activeStep) ?? stepFlow[0];
  const profileQuickReplies = [
    "我这学期数据结构最吃力，图搜索和递归容易混淆，每天能学 1 小时。",
    "我想备考人工智能课程，希望多给我图解、例题和代码实操。",
    "我基础一般，喜欢先看案例再总结概念，希望学习路径更细一些。"
  ];

  async function runTask(action: BusyAction, task: () => Promise<void>) {
    setBusy(action);
    setError(null);
    try {
      await task();
    } catch (err) {
      const message = toErrorMessage(err);
      setError(message);
      if (action.includes("knowledge") || action.includes("document")) setKnowledgeError(message);
    } finally {
      setBusy(null);
    }
  }

  async function refreshBaseData() {
    const nextStatus = await api.getDemoStatus();
    setStatus(nextStatus);
    const nextProfiles = await api.listProfiles();
    setProfiles(nextProfiles);
    setSelectedProfileId((current) =>
      current && nextProfiles.some((profile) => profile.id === current) ? current : nextProfiles[0]?.id ?? null
    );
    if (nextStatus.course_id) {
      setGraph(await api.getCourseGraph(nextStatus.course_id));
      setKnowledgeDocuments(await api.listCourseDocuments(nextStatus.course_id));
    } else {
      setGraph(null);
      setKnowledgeDocuments([]);
    }
  }

  async function appendRun(runId: number | null) {
    if (!runId) return;
    const run = await api.getAgentRun(runId);
    setRuns((current) => [run, ...current.filter((item) => item.id !== run.id)].slice(0, 10));
  }

  function resetLoopOutputs() {
    setResource(null);
    setTutorMessages([]);
    setQuiz(null);
    setAttemptText("");
    setEvaluation(null);
    setAutoProfileUpdate(null);
  }

  function replaceOrAppendProfile(nextProfile: StudentProfile) {
    setProfiles((current) => [nextProfile, ...current.filter((profile) => profile.id !== nextProfile.id)]);
    setSelectedProfileId(nextProfile.id);
    setFlow(null);
    setSelectedPathItemId(null);
    setRuns([]);
    resetLoopOutputs();
  }

  function refreshSelectedProfile(nextProfile: StudentProfile) {
    setProfiles((current) => current.map((profile) => (profile.id === nextProfile.id ? nextProfile : profile)));
    setSelectedProfileId(nextProfile.id);
  }

  async function refreshKnowledgeDocuments() {
    if (!status?.course_id) return;
    setKnowledgeError(null);
    setKnowledgeDocuments(await api.listCourseDocuments(status.course_id));
  }

  async function submitQuizAttempt() {
    if (!quiz || !selectedProfileId || !attemptText.trim()) return;
    setBusy("submit-attempt");
    setError(null);
    setAutoProfileUpdate(null);
    try {
      const nextEvaluation = await api.submitAttempt(quiz.id, selectedProfileId, { answer: attemptText });
      setEvaluation(nextEvaluation);
      await appendRun(nextEvaluation.agent_run_id);
      setActiveStep("assess");
      if (!autoProfileUpdateEnabled) {
        setAutoProfileUpdate("自动画像更新已关闭，可稍后手动同步。");
        return;
      }
      setBusy("sync-profile");
      const nextProfile = await api.updateProfileFromTrace(selectedProfileId);
      refreshSelectedProfile(nextProfile);
      setAutoProfileUpdate(String(nextProfile.preferences.last_profile_update_reason ?? "画像已根据最新学习轨迹更新。"));
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  useEffect(() => {
    let active = true;
    setBooting(true);
    refreshBaseData()
      .catch((err) => {
        if (active) setError(toErrorMessage(err));
      })
      .finally(() => {
        if (active) setBooting(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (activeStep !== "tutor") return;
    chatScrollRef.current?.scrollTo({
      top: chatScrollRef.current.scrollHeight,
      behavior: "smooth"
    });
  }, [tutorMessages, busy, activeStep]);

  const profileStep = (
    <div className="content-grid profile-content-grid">
      <Panel title="对话式学生画像" kicker="画像随学随新">
        <div className="profile-onboarding">
          <div className="onboarding-messages">
            <article className="onboarding-bubble onboarding-bubble-guide">
              <span>学习管家</span>
              <p>同学你好，我是你的专属学习管家。这学期哪门课程最让你头疼？你希望我用什么方式帮你学？</p>
            </article>
            {(profileDialogue || profileDraft) ? (
              <article className="onboarding-bubble onboarding-bubble-user">
                <span>你的回复</span>
                <p>{profileDraft || profileDialogue}</p>
              </article>
            ) : null}
          </div>
          <div className="quick-reply-row" aria-label="快捷回复">
            {profileQuickReplies.map((reply) => (
              <button key={reply} className="pill-button" type="button" onClick={() => setProfileDraft(reply)}>
                {reply}
              </button>
            ))}
          </div>
          <div className="onboarding-composer">
            <input
              className="onboarding-input"
              data-testid="profile-dialogue"
              value={profileDraft}
              onChange={(event) => setProfileDraft(event.target.value)}
              aria-label="画像对话内容"
              placeholder="例如：我基础一般，图搜索总出错，每天晚上能学 1 小时..."
            />
            <button
              className="chat-send-button onboarding-send"
              data-testid="build-profile-button"
              disabled={!profileDraft.trim() || busy !== null}
              onClick={() =>
                void runTask("build-profile", async () => {
                  const submitted = profileDraft.trim();
                  setProfileDialogue(submitted);
                  const nextProfile = await api.createProfileFromDialogue({ dialogue: submitted });
                  replaceOrAppendProfile(nextProfile);
                  setProfileDraft("");
                })
              }
            >
              {busy === "build-profile" ? "分析中" : "生成画像"}
            </button>
          </div>
        </div>
        <div className="profile-summary-stack">
          {latestProfile ? (
            <article className="profile-current-card" data-testid="profile-option">
              <div>
                <p className="eyebrow">最新画像</p>
                <strong>{labelProfile(latestProfile.profile_type)}</strong>
                <span>{latestProfile.goal}</span>
              </div>
              {latestProfile.id !== selectedProfileId ? (
                <button
                  className="small-button"
                  onClick={() => {
                    setSelectedProfileId(latestProfile.id);
                    setFlow(null);
                    setSelectedPathItemId(null);
                    resetLoopOutputs();
                  }}
                >
                  使用此画像
                </button>
              ) : null}
            </article>
          ) : null}
          {busy === "build-profile" ? (
            <ProfileSkeleton />
          ) : latestProfile ? (
            <ProfileDimensionList profile={latestProfile} />
          ) : (
            <EmptyState text="请先通过对话生成一个学生画像。" />
          )}
        </div>
      </Panel>
    </div>
  );

  const knowledgeStep = (
    <div className="knowledge-step">
      <KnowledgePanel
        status={status}
        busy={busy}
        knowledgeTitle={knowledgeTitle}
        setKnowledgeTitle={setKnowledgeTitle}
        knowledgeSourceType={knowledgeSourceType}
        setKnowledgeSourceType={setKnowledgeSourceType}
        knowledgeContent={knowledgeContent}
        setKnowledgeContent={setKnowledgeContent}
        knowledgeFile={knowledgeFile}
        setKnowledgeFile={setKnowledgeFile}
        knowledgeImportResult={knowledgeImportResult}
        knowledgeReindexResult={knowledgeReindexResult}
        knowledgeDocuments={knowledgeDocuments}
        knowledgeError={knowledgeError}
        knowledgeQuery={knowledgeQuery}
        setKnowledgeQuery={setKnowledgeQuery}
        knowledgeSearchResults={knowledgeSearchResults}
        onRunTask={runTask}
        onImport={async () => {
          if (!status?.course_id) return;
          setKnowledgeError(null);
          setKnowledgeReindexResult(null);
          const result = await api.ingestCourseDocument(status.course_id, {
            title: knowledgeTitle,
            source_type: knowledgeSourceType,
            content: knowledgeContent
          });
          setKnowledgeImportResult(result);
          setKnowledgeSearchResults([]);
          await refreshKnowledgeDocuments();
        }}
        onUpload={async () => {
          if (!status?.course_id || !knowledgeFile) return;
          setKnowledgeError(null);
          setKnowledgeReindexResult(null);
          const result = await api.uploadCourseDocument(status.course_id, knowledgeFile, {
            title: knowledgeTitle.trim() || knowledgeFile.name,
            visibility: "course"
          });
          setKnowledgeImportResult(result);
          setKnowledgeSearchResults([]);
          await refreshKnowledgeDocuments();
        }}
        onRefresh={refreshKnowledgeDocuments}
        onDelete={async (documentId) => {
          await api.deleteDocument(documentId);
          setKnowledgeImportResult(null);
          setKnowledgeReindexResult(null);
          setKnowledgeSearchResults([]);
          await refreshKnowledgeDocuments();
        }}
        onReindex={async (documentId) => {
          setKnowledgeReindexResult(await api.reindexDocument(documentId));
        }}
        onSearch={async () => {
          if (!status?.course_id) return;
          const result = await api.searchKnowledge(status.course_id, knowledgeQuery, 4);
          setKnowledgeSearchResults(result.results);
        }}
      />
    </div>
  );

  const pathStep = (
    <Panel title="路径规划" kicker="学习规划师">
      <input className="field" value={goal} onChange={(event) => setGoal(event.target.value)} aria-label="学习目标" />
      <button
        className="primary-button mt-3"
        data-testid="create-path-button"
        disabled={!canCreatePath || busy !== null}
        onClick={() =>
          void runTask("create-path", async () => {
            if (!selectedProfileId || !status?.course_id) return;
            const nextFlow = await api.createLearningPath(selectedProfileId, status.course_id, goal);
            setFlow(nextFlow);
            setSelectedPathItemId(nextFlow.learning_path.items[0]?.id ?? null);
            await appendRun(nextFlow.agent_run.id);
            resetLoopOutputs();
          })
        }
      >
        {busy === "create-path" ? "正在规划学习路径" : "生成个性化学习路径"}
      </button>
      {busy === "create-path" ? <AgentLoading testId="planner-loading" title="学习规划师正在编排路径" detail="系统正在结合画像、课程图谱和学习目标排序。" /> : null}
      <div className="path-grid">
        {pathItems.map((item) => (
          <PathItemCard
            key={item.id}
            item={item}
            concept={graph?.concepts.find((concept) => concept.id === item.concept_id) ?? null}
            selected={item.id === selectedItem?.id}
            onSelect={() => setSelectedPathItemId(item.id)}
          />
        ))}
        {pathItems.length === 0 ? <EmptyState text="生成学习路径后，这里会展示按顺序排列的学习节点。" /> : null}
      </div>
    </Panel>
  );

  const resourceStep = (
    <div className="content-grid resource-layout">
      <Panel title="资源生成" kicker="资源设计师">
        <NodeSummary item={selectedItem} concept={selectedConcept} />
        <div className="resource-tabs">
          {resourceOptions.map((option) => (
            <button
              key={option.type}
              className={`resource-tab ${resourceType === option.type ? "resource-tab-active" : ""}`}
              data-testid={`resource-type-${option.type}`}
              onClick={() => setResourceType(option.type)}
            >
              {option.label}
            </button>
          ))}
        </div>
        <button
          className="primary-button mt-3"
          data-testid="generate-resource-button"
          disabled={!selectedItem || busy !== null}
          onClick={() =>
            void runTask("generate-resource", async () => {
              if (!selectedItem) return;
              const backendResourceType = resourceType === "teaching_video" ? "guided_note" : resourceType;
              const nextResource = await api.generateResource(selectedItem.id, backendResourceType);
              setResource(resourceType === "teaching_video" ? { ...nextResource, resource_type: "teaching_video" } : nextResource);
              await appendRun(nextResource.agent_run_id);
            })
          }
        >
          {busy === "generate-resource" ? "正在生成学习资源" : "生成选中类型资源"}
        </button>
        {busy === "generate-resource" ? (
          <StatusTracker
            testId="resource-loading"
            steps={[
              { label: "检索课程资料", detail: "资料管理员正在获取相关证据片段", status: "done" },
              { label: "组织资源结构", detail: "资源设计师正在匹配画像与知识短板", status: "active" },
              { label: "流式生成内容", detail: "即将输出文档、图解与实操材料", status: "pending" }
            ]}
          />
        ) : null}
      </Panel>
      {resource ? <ResourceOutputBlock resource={resource} /> : <EmptyState text="请选择路径节点和资源类型后生成内容。" />}
    </div>
  );

  const tutorStep = (
    <section className="tutor-workspace" aria-label="教师答疑">
      <div className="chat-shell">
        <div className="chat-heading">
          <div>
            <p className="eyebrow">答疑教师</p>
            <h2>教师答疑</h2>
          </div>
        </div>
        <div className="chat-messages" ref={chatScrollRef}>
          <article className="chat-message chat-message-assistant">
            <span>答疑教师</span>
            <p>我会结合你的学生画像和课程知识库，用可追溯证据解释问题。可以直接输入你的困惑。</p>
          </article>
          {tutorMessages.map((message) => (
            <article
              className={`chat-message ${message.role === "user" ? "chat-message-user" : "chat-message-assistant chat-message-rich"}`}
              key={message.id}
            >
              <span>{message.role === "user" ? "学生提问" : "辅导答复"}</span>
              {message.role === "assistant" ? <TypewriterMarkdown text={message.content} /> : <p>{message.content}</p>}
              {message.role === "assistant" ? <SourceEvidence sourceRefs={message.sourceRefs ?? []} /> : null}
            </article>
          ))}
          {busy === "ask-tutor" ? (
            <article className="chat-message chat-message-assistant">
              <span>答疑教师</span>
              <StatusTracker
                compact
                testId="tutor-loading"
                steps={[
                  { label: "检索证据", detail: "已锁定课程资料与相关知识点", status: "done" },
                  { label: "组织解释", detail: "答疑教师正在按你的画像调整讲解方式", status: "active" },
                  { label: "流式生成", detail: "回答即将逐字呈现", status: "pending" }
                ]}
              />
            </article>
          ) : null}
        </div>
        <div className="chat-composer">
          <textarea
            className="field chat-input resize-none"
            data-testid="tutor-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            aria-label="辅导问题"
            placeholder="输入你想追问的知识点、代码问题或解题思路..."
          />
          <button
            className="chat-send-button"
            data-testid="ask-tutor-button"
            disabled={!canUseLoop || !question.trim() || busy !== null}
            onClick={() =>
              void runTask("ask-tutor", async () => {
                if (!selectedProfileId || !status?.course_id) return;
                const submittedQuestion = question.trim();
                const messageStamp = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
                setQuestion("");
                setTutorMessages((current) => [
                  ...current,
                  { id: `user-${messageStamp}`, role: "user", content: submittedQuestion }
                ]);
                const nextAnswer = await api.askTutor(selectedProfileId, status.course_id, submittedQuestion);
                setTutorMessages((current) => [
                  ...current,
                  {
                    id: `assistant-${messageStamp}`,
                    role: "assistant",
                    content: nextAnswer.answer,
                    sourceRefs: nextAnswer.source_refs
                  }
                ]);
                await appendRun(nextAnswer.agent_run_id);
              })
            }
          >
            {busy === "ask-tutor" ? "生成中" : "发送"}
          </button>
        </div>
        <p className="ai-disclaimer">* 教师团队生成内容仅供参考，请注意甄别事实（已开启内容安全与防幻觉过滤机制）*</p>
      </div>
    </section>
  );

  const quizStep = (
    <Panel title="练习测验" kicker="出题与评估">
      <button
        className="primary-button"
        data-testid="generate-quiz-button"
        disabled={!selectedConcept || !selectedProfileId || busy !== null}
        onClick={() =>
          void runTask("generate-quiz", async () => {
            if (!selectedConcept || !selectedProfileId) return;
            const nextQuiz = await api.generateQuiz(selectedProfileId, selectedConcept.id, "medium");
            setQuiz(nextQuiz);
            await appendRun(nextQuiz.agent_run_id);
          })
        }
      >
        {busy === "generate-quiz" ? "正在生成测验" : "生成当前节点测验"}
      </button>
      {busy === "generate-quiz" ? <AgentLoading testId="quiz-loading" title="出题老师正在生成测验" detail="题目会结合当前概念和学生画像。" /> : null}
      {quiz ? (
        <div className="quiz-box">
          {quiz.items.map((item, index) => (
            <article key={index} className="quiz-question" data-testid="quiz-question">
              <strong>第 {index + 1} 题</strong>
              <p>{item.question}</p>
            </article>
          ))}
          <textarea
            className="field min-h-28 resize-none"
            data-testid="quiz-answer"
            value={attemptText}
            onChange={(event) => setAttemptText(event.target.value)}
            aria-label="作答内容"
            placeholder="在这里输入你的作答思路"
          />
          <label className="setting-toggle">
            <input
              data-testid="auto-profile-update-toggle"
              type="checkbox"
              checked={autoProfileUpdateEnabled}
              disabled={busy !== null}
              onChange={(event) => setAutoProfileUpdateEnabled(event.target.checked)}
            />
            <span>
              <strong>评估后自动更新学生画像</strong>
              <small>测评教师完成评分后，画像顾问会读取学习轨迹并回写画像。</small>
            </span>
          </label>
          <button className="primary-button" data-testid="submit-answer-button" disabled={!attemptText.trim() || busy !== null} onClick={() => void submitQuizAttempt()}>
            {busy === "submit-attempt" ? "正在提交作答" : busy === "sync-profile" ? "正在更新画像" : "提交作答并评估"}
          </button>
          {busy === "submit-attempt" ? <AgentLoading testId="evaluator-loading" title="测评教师正在评分" detail="系统正在比较评分规则和作答内容。" /> : null}
          {busy === "sync-profile" ? <AgentLoading testId="profile-update-loading" title="画像顾问正在更新画像" detail="系统正在分析最新学习轨迹。" /> : null}
        </div>
      ) : (
        <EmptyState text="生成测验后，这里会展示当前节点的练习题。" />
      )}
    </Panel>
  );

  const assessStep = (
    <Panel title="学习效果评估" kicker="画像回写">
      {evaluation ? (
        <div className="space-y-4">
          <Metric label="综合得分" value={`${Math.round(evaluation.score * 100)}%`} />
          <p className="feedback" data-testid="evaluator-feedback">{evaluation.feedback}</p>
          {autoProfileUpdate ? <p className="profile-update-note" data-testid="auto-profile-update">{autoProfileUpdate}</p> : null}
          <div className="update-list">
            {evaluation.mastery_updates.map((update, index) => (
              <article key={index} className="update-card">
                <strong>概念 {String(update.concept_id ?? "未知")}</strong>
                <span>掌握度：{String(update.mastery_score ?? "暂无")}</span>
                <p>{String(update.evidence ?? "暂无证据说明")}</p>
              </article>
            ))}
          </div>
        </div>
      ) : (
        <EmptyState text="提交作答后，这里会展示得分、反馈、掌握度变化和画像更新原因。" />
      )}
    </Panel>
  );

  const stepContent: Record<StepKey, ReactNode> = {
    profile: profileStep,
    kb: knowledgeStep,
    path: pathStep,
    resource: resourceStep,
    tutor: tutorStep,
    quiz: quizStep,
    assess: assessStep
  };

  return (
    <main className="app-shell">
      <header className="top-bar">
        <div>
          <p className="eyebrow">第十五届中国软件杯 A 组赛题演示</p>
          <h1>个性化学习资源生成与教师协同工作台</h1>
        </div>
        <div className="top-actions">
          <button
            className="icon-button"
            type="button"
            aria-label="打开设置与调试"
            title="设置与调试"
            onClick={() => setDebugOpen(true)}
          >
            ⚙
          </button>
        </div>
      </header>

      <section className="app-main">
        <StepFlow activeStep={activeStep} onSelect={setActiveStep} />
        <MultiAgentOverview activeStep={activeStep} />

        <div className="toolbar">
          <div>
            <p className="eyebrow">当前步骤</p>
            <h2>{stepInfo.label}</h2>
            <span>{stepInfo.desc}</span>
          </div>
          <button className="ghost-button" onClick={() => setTraceOpen(true)}>
            打开执行追踪浮层
          </button>
        </div>

        <div className="step-body">{stepContent[activeStep]}</div>
      </section>

      <button className="floating-trace-button" onClick={() => setTraceOpen(true)}>执行追踪</button>
      <TraceOverlay open={traceOpen} onClose={() => setTraceOpen(false)} runs={runs} />
      <footer className="app-footer-badge">Powered by 科大讯飞星火大模型</footer>
      <DebugModal
        open={debugOpen}
        busy={busy}
        booting={booting}
        error={error}
        onClose={() => setDebugOpen(false)}
        onLoadDemo={() =>
          void runTask("load-demo", async () => {
            await api.loadDemoData();
            await refreshBaseData();
          })
        }
        onResetDemo={() =>
          void runTask("reset-demo", async () => {
            await api.resetDemoUserData();
            await refreshBaseData();
            setFlow(null);
            setSelectedPathItemId(null);
            setRuns([]);
            resetLoopOutputs();
          })
        }
      />
    </main>
  );
}

function DebugModal(props: {
  open: boolean;
  busy: BusyAction | null;
  booting: boolean;
  error: string | null;
  onClose: () => void;
  onLoadDemo: () => void;
  onResetDemo: () => void;
}) {
  if (!props.open) return null;

  return (
    <div className="modal-overlay">
      <button className="modal-backdrop" aria-label="关闭设置与调试" onClick={props.onClose} />
      <section className="modal-card" role="dialog" aria-modal="true" aria-label="设置与调试">
        <div className="modal-header">
          <div>
            <p className="eyebrow">设置 / 调试</p>
            <h2>演示数据控制</h2>
          </div>
          <button className="icon-button" type="button" aria-label="关闭设置与调试" onClick={props.onClose}>
            ×
          </button>
        </div>
        <div className="modal-body">
          <button
            className="action-button w-full"
            data-testid="load-demo-button"
            disabled={props.busy !== null}
            onClick={props.onLoadDemo}
          >
            {props.busy === "load-demo" ? "正在加载演示数据" : "加载或刷新演示数据"}
          </button>
          <button
            className="danger-button w-full"
            data-testid="reset-demo-button"
            disabled={props.busy !== null}
            onClick={props.onResetDemo}
          >
            {props.busy === "reset-demo" ? "正在重置" : "重置用户演示数据"}
          </button>
          <StatusLine busy={props.booting} error={props.error} />
        </div>
      </section>
    </div>
  );
}

function KnowledgePanel(props: {
  status: DemoDataStatus | null;
  busy: BusyAction | null;
  knowledgeTitle: string;
  setKnowledgeTitle: (value: string) => void;
  knowledgeSourceType: "text" | "markdown";
  setKnowledgeSourceType: (value: "text" | "markdown") => void;
  knowledgeContent: string;
  setKnowledgeContent: (value: string) => void;
  knowledgeFile: File | null;
  setKnowledgeFile: (value: File | null) => void;
  knowledgeImportResult: DocumentIngestionResponse | null;
  knowledgeReindexResult: DocumentReindexResponse | null;
  knowledgeDocuments: ManagedDocument[];
  knowledgeError: string | null;
  knowledgeQuery: string;
  setKnowledgeQuery: (value: string) => void;
  knowledgeSearchResults: KnowledgeSearchResult[];
  onRunTask: (action: BusyAction, task: () => Promise<void>) => Promise<void>;
  onImport: () => Promise<void>;
  onUpload: () => Promise<void>;
  onSearch: () => Promise<void>;
  onRefresh: () => Promise<void>;
  onDelete: (documentId: number) => Promise<void>;
  onReindex: (documentId: number) => Promise<void>;
}) {
  const [createOpen, setCreateOpen] = useState(false);

  return (
    <section className="kb-workspace">
      <aside className="kb-sidebar" data-testid="document-management">
        <div className="kb-sidebar-header">
          <div>
            <p className="eyebrow">资料管理器</p>
            <h2>课程资料</h2>
          </div>
          <button className="small-button" data-testid="refresh-documents-button" disabled={!props.status?.course_id || props.busy !== null} onClick={() => void props.onRunTask("refresh-documents", props.onRefresh)}>
            刷新
          </button>
        </div>
        <div className="kb-document-list" data-testid="document-list">
          {props.knowledgeDocuments.map((document) => (
            <article key={document.id} className="kb-document-row" data-testid="document-row">
              <div>
                <strong>{documentDisplayName(document)}</strong>
                <span>{document.chunk_count} 个片段 / {document.status}</span>
                <small>{document.parser_name ?? "默认解析器"}</small>
              </div>
              <div className="kb-document-actions">
                <button className="document-reindex-button" data-testid="reindex-document-button" disabled={props.busy !== null} onClick={() => void props.onRunTask("reindex-document", () => props.onReindex(document.id))}>
                  重建
                </button>
                <button className="document-delete-button" data-testid="delete-document-button" disabled={props.busy !== null} onClick={() => void props.onRunTask("delete-document", () => props.onDelete(document.id))}>
                  删除
                </button>
              </div>
            </article>
          ))}
          {props.knowledgeDocuments.length === 0 ? <p className="document-empty">暂无课程资料。</p> : null}
        </div>
      </aside>

      <section className="kb-main">
        <div className="kb-main-header">
          <div>
            <p className="eyebrow">资料管理员</p>
            <h2>知识库检索</h2>
          </div>
          <button className="primary-button" type="button" onClick={() => setCreateOpen(true)}>
            + 录入资料
          </button>
        </div>

        <div className="kb-search-hero">
          <input
            className="field kb-search-input"
            data-testid="knowledge-query"
            value={props.knowledgeQuery}
            onChange={(event) => props.setKnowledgeQuery(event.target.value)}
            aria-label="知识检索问题"
            placeholder="输入一个知识点、问题或学习目标，检索课程知识库"
          />
          <button
            className="primary-button"
            data-testid="search-knowledge-button"
            disabled={!props.status?.course_id || !props.knowledgeQuery.trim() || props.busy !== null}
            onClick={() => void props.onRunTask("search-knowledge", props.onSearch)}
          >
            {props.busy === "search-knowledge" ? "正在检索" : "检索知识库"}
          </button>
        </div>

        <div className="knowledge-search-results" data-testid="knowledge-search-results">
          {props.knowledgeSearchResults.map((result, index) => (
            <article key={index} className="knowledge-search-result">
              <strong>{resultDisplayName(result)}</strong>
              <span>相似度 {formatScore(result.score)} / 来源 {String(result.source_ref ?? "暂无")}</span>
              <p className="knowledge-search-excerpt">{result.content}</p>
            </article>
          ))}
          {props.knowledgeSearchResults.length === 0 ? <EmptyState text="输入问题后检索课程知识库，结果会作为资源生成和答疑证据。" /> : null}
        </div>
      </section>

      {createOpen ? (
        <div className="modal-overlay">
          <button className="modal-backdrop" aria-label="关闭资料录入" onClick={() => setCreateOpen(false)} />
          <section className="modal-card kb-create-modal" role="dialog" aria-modal="true" aria-label="新建资料">
            <div className="modal-header">
              <div>
                <p className="eyebrow">资料接入</p>
                <h2>新建资料</h2>
              </div>
              <button className="icon-button" type="button" aria-label="关闭资料录入" onClick={() => setCreateOpen(false)}>
                ×
              </button>
            </div>
            <div className="modal-body">
              <input className="field" data-testid="knowledge-title" value={props.knowledgeTitle} onChange={(event) => props.setKnowledgeTitle(event.target.value)} aria-label="资料标题" placeholder="资料标题" />
              <select className="field" data-testid="knowledge-source-type" value={props.knowledgeSourceType} onChange={(event) => props.setKnowledgeSourceType(event.target.value as "text" | "markdown")} aria-label="资料类型">
                <option value="markdown">标记文本</option>
                <option value="text">纯文本</option>
              </select>
              <textarea className="field min-h-36 resize-none" data-testid="knowledge-content" value={props.knowledgeContent} onChange={(event) => props.setKnowledgeContent(event.target.value)} aria-label="资料内容" placeholder="粘贴课程讲义、知识点说明或案例材料" />
              <input
                className="field"
                data-testid="knowledge-file"
                type="file"
                accept=".txt,.md,.markdown,.pdf,.docx,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(event) => {
                  const file = event.target.files?.[0] ?? null;
                  props.setKnowledgeFile(file);
                  if (file) props.setKnowledgeTitle(file.name);
                }}
                aria-label="上传资料文件"
              />
              <div className="modal-actions">
                <button className="action-button w-full" data-testid="upload-knowledge-button" disabled={!props.status?.course_id || !props.knowledgeFile || props.busy !== null} onClick={() => void props.onRunTask("upload-knowledge", props.onUpload)}>
                  {props.busy === "upload-knowledge" ? "正在上传资料" : "上传选中文件"}
                </button>
                <button className="primary-button w-full" data-testid="import-knowledge-button" disabled={!props.status?.course_id || !props.knowledgeTitle.trim() || !props.knowledgeContent.trim() || props.busy !== null} onClick={() => void props.onRunTask("import-knowledge", props.onImport)}>
                  {props.busy === "import-knowledge" ? "正在导入资料" : "导入文本资料"}
                </button>
              </div>
              {props.knowledgeImportResult ? (
                <div className="knowledge-result" data-testid="knowledge-import-result">
                  <p>{documentDisplayName(props.knowledgeImportResult.document)}</p>
                  <p>已导入 / {props.knowledgeImportResult.chunk_count} 个片段 / {props.knowledgeImportResult.document.parser_name ?? "默认解析器"}</p>
                </div>
              ) : null}
              {props.knowledgeReindexResult ? (
                <div className="knowledge-result" data-testid="knowledge-reindex-result">
                  <p>重建完成：已索引 {props.knowledgeReindexResult.indexed}，跳过 {props.knowledgeReindexResult.skipped}，失败 {props.knowledgeReindexResult.failed}</p>
                  <span>{props.knowledgeReindexResult.message}</span>
                </div>
              ) : null}
              {props.knowledgeError ? <p className="error-note">{props.knowledgeError}</p> : null}
            </div>
          </section>
        </div>
      ) : null}
    </section>
  );
}

function StepFlow({ activeStep, onSelect }: { activeStep: StepKey; onSelect: (key: StepKey) => void }) {
  return (
    <section className="step-flow" aria-label="学习闭环步骤">
      <div className="step-flow-head">
        <div>
          <p className="eyebrow">学习闭环</p>
          <strong>七步个性化学习流程</strong>
        </div>
        <span>当前视图：{stepFlow.find((step) => step.key === activeStep)?.label}</span>
      </div>
      <ol>
        {stepFlow.map((step, index) => (
          <li key={step.key}>
            <button className={activeStep === step.key ? "step-active" : ""} onClick={() => onSelect(step.key)} aria-current={activeStep === step.key ? "step" : undefined}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              {step.label}
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}

function MultiAgentOverview({ activeStep }: { activeStep: StepKey }) {
  const active = stepAgents[activeStep];
  const activeIds = new Set([active.lead, ...active.support]);
  return (
    <section className="agent-overview">
      <div className="section-heading">
        <div>
          <p className="eyebrow">教学团队协作编排</p>
          <h2>当前步骤由主导角色牵引，协作角色按需补充能力</h2>
        </div>
        <span className="orchestration-badge">
          主导：{agentRoster.find((agent) => agent.id === active.lead)?.name} / 协作：{active.support.length} 个
        </span>
      </div>
      <div className="agent-grid">
        {agentRoster.map((agent) => {
          const isLead = active.lead === agent.id;
          const isActive = activeIds.has(agent.id);
          return (
            <article key={agent.id} className={`agent-card ${isLead ? "agent-lead" : isActive ? "agent-support" : ""}`}>
              <span>{isLead ? "主导" : isActive ? "协作" : "待命"}</span>
              <h3>{agent.name}</h3>
              <p>{agent.role}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function PathItemCard({ item, concept, selected, onSelect }: { item: LearningPathItem; concept: Concept | null; selected: boolean; onSelect: () => void }) {
  return (
    <button className={`path-card ${selected ? "path-card-active" : ""}`} data-testid="path-item-card" onClick={onSelect}>
      <span>第 {item.order_index} 步</span>
      <strong>{item.title}</strong>
      <p>{item.objective}</p>
      <small>{concept?.name ?? `概念 ${item.concept_id}`}</small>
    </button>
  );
}

function NodeSummary({ item, concept }: { item: LearningPathItem | null; concept: Concept | null }) {
  if (!item) return <EmptyState text="请选择或生成一个学习节点。" />;
  return (
    <div className="node-summary" data-testid="current-node">
      <p className="eyebrow">当前节点</p>
      <strong>{item.title}</strong>
      <span>{item.objective}</span>
      <small>{concept?.name ?? `概念 ${item.concept_id}`}</small>
    </div>
  );
}

function ProfileDimensionList({ profile }: { profile: StudentProfile }) {
  const dimensionIcons: Record<string, string> = {
    learning_goal: "🎯",
    foundation_level: "📊",
    learning_preference: "🧠",
    available_time: "⏱️",
    weak_points: "🩹",
    resource_preference: "📚"
  };

  return (
    <div className="modern-profile-card" data-testid="profile-dimensions">
      <div className="modern-profile-header">
        <span className="pulse-dot" aria-hidden="true" />
        <h3>六维动态学生画像</h3>
      </div>
      <div className="modern-dimension-grid">
        {profileDimensions.map(([key, label]) => {
          const value = formatPreference(profile, key);
          return (
            <article key={key} className="modern-dimension-item">
              <span className="dimension-label">
                <span aria-hidden="true">{dimensionIcons[key] ?? "•"}</span>
                {label}
              </span>
              {key === "foundation_level" ? (
                <p className="dimension-value">
                  <span className="status-badge">{value}</span>
                </p>
              ) : (
                <p className="dimension-value">{value}</p>
              )}
            </article>
          );
        })}
      </div>
      {profile.preferences.last_profile_update_reason ? (
        <footer className="modern-profile-footer" data-testid="profile-update-reason">
          <span aria-hidden="true">✨</span>
          <p>{String(profile.preferences.last_profile_update_reason)}</p>
        </footer>
      ) : null}
    </div>
  );
}

function ProfileSkeleton() {
  return (
    <div className="modern-profile-card profile-skeleton-card" data-testid="profile-skeleton" aria-live="polite">
      <div className="modern-profile-header">
        <span className="pulse-dot" aria-hidden="true" />
        <h3>画像顾问正在扫描六维特征</h3>
      </div>
      <div className="modern-dimension-grid">
        {profileDimensions.map(([key, label]) => (
          <article key={key} className="modern-dimension-item skeleton-dimension">
            <span className="dimension-label">{label}</span>
            <i />
            <b />
          </article>
        ))}
      </div>
      <footer className="modern-profile-footer">
        <span aria-hidden="true">✨</span>
        <p>正在从对话中抽取学习目标、基础水平、偏好与短板。</p>
      </footer>
    </div>
  );
}

function formatPreference(profile: StudentProfile, key: string): string {
  const value = profile.preferences[key];
  if (value === undefined || value === null || value === "") {
    if (key === "learning_goal") return profile.goal;
    if (key === "foundation_level") return profile.level;
    if (key === "available_time") return profile.time_budget;
    return "等待学习过程更新";
  }
  return String(value);
}

function TraceOverlay({ open, onClose, runs }: { open: boolean; onClose: () => void; runs: AgentRun[] }) {
  if (!open) return null;
  return (
    <div className="trace-overlay">
      <button className="trace-backdrop" aria-label="关闭执行追踪" onClick={onClose} />
      <aside className="trace-drawer">
        <div className="trace-header">
          <div>
            <p className="eyebrow">执行追踪</p>
            <h2>教学团队协作记录</h2>
          </div>
          <button className="small-button" onClick={onClose}>关闭</button>
        </div>
        <div className="trace-list">
          {runs.map((run) => <RunCard key={run.id} run={run} />)}
          {runs.length === 0 ? <EmptyState text="执行学习路径、资源生成、辅导或测验后，这里会显示教学团队协作记录。" /> : null}
        </div>
      </aside>
    </div>
  );
}

function RunCard({ run }: { run: AgentRun }) {
  return (
    <article className="run-timeline-card" data-testid="run-card">
      <div className="run-card-header">
        <h3>{runTypeLabels[run.run_type] ?? run.run_type}</h3>
        <span>{statusLabels[run.status] ?? run.status}</span>
      </div>
      <p>{run.final_summary ?? run.output_summary ?? run.input_summary ?? "暂无摘要"}</p>
      <div className="timeline-steps">
        {run.steps.map((step) => (
          <div key={step.id} className="timeline-step">
            <strong>{step.step_order}. {agentTypeLabels[step.agent_type] ?? step.agent_type}</strong>
            <span>输入摘要</span>
            <p>{step.input_summary}</p>
            <span>输出摘要</span>
            <p>{step.output_summary}</p>
            <span>决策依据</span>
            <p>{step.decision_basis}</p>
          </div>
        ))}
      </div>
    </article>
  );
}

function ResourceOutputBlock({ resource }: { resource: GeneratedResource }) {
  return (
    <article className="resource-card" data-testid="output-block">
      <ResourceHeader title={resourceLabel(resource.resource_type)} />
      {resource.resource_type === "teaching_video" ? <VideoPlayerCard title="个性化教学视频/动画讲解" /> : null}
      {resource.resource_type === "mind_map" ? <MindMapDiagram text={resource.content} /> : null}
      {resource.resource_type === "coding_case" ? <CodeCaseCard code={extractFencedCode(resource.content) || resource.content} /> : null}
      {resource.resource_type !== "mind_map" && resource.resource_type !== "coding_case" && resource.resource_type !== "teaching_video" ? <TypewriterMarkdown text={resource.content} /> : null}
      {resource.resource_type === "teaching_video" ? <VideoScriptBlock text={resource.content} /> : null}
      <FullResourceText text={resource.content} />
      <SourceEvidence sourceRefs={resource.source_refs} />
    </article>
  );
}

function VideoPlayerCard({ title }: { title: string }) {
  return (
    <article className="video-player-card" data-testid="video-player-card">
      <div className="video-cover">
        <button className="video-play-button" type="button" aria-label="播放多模态讲解">
          ▶
        </button>
        <span className="video-duration">03:28</span>
      </div>
      <div className="video-meta">
        <strong>{title}</strong>
        <span>视频/动画占位 · 生成后可替换为 SeeDance 等多模态内容</span>
      </div>
    </article>
  );
}

function VideoScriptBlock({ text }: { text: string }) {
  return (
    <div className="video-script-block">
      <p className="eyebrow">视频脚本 / 动画分镜</p>
      <TypewriterMarkdown text={text} />
    </div>
  );
}

function CodeCaseCard({ code }: { code: string }) {
  const [tab, setTab] = useState<"code" | "output">("code");
  const [copied, setCopied] = useState(false);

  async function copyCode() {
    try {
      await navigator.clipboard?.writeText(code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      setCopied(false);
    }
  }

  return (
    <article className="code-case-card" data-testid="coding-case-card">
      <div className="code-case-toolbar">
        <div className="window-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <div className="code-tabs">
          <button className={tab === "code" ? "code-tab-active" : ""} type="button" onClick={() => setTab("code")}>代码</button>
          <button className={tab === "output" ? "code-tab-active" : ""} type="button" onClick={() => setTab("output")}>运行输出</button>
        </div>
        <button className="copy-button" type="button" onClick={() => void copyCode()}>
          {copied ? "已复制" : "复制"}
        </button>
      </div>
      {tab === "code" ? (
        <pre className="code-case-block">{code}</pre>
      ) : (
        <div className="run-output-placeholder">
          <strong>运行输出预览</strong>
          <p>接入在线沙箱后，这里会展示测试结果、复杂度分析与调试建议。</p>
        </div>
      )}
    </article>
  );
}

function OutputBlock({ title, text, sourceRefs }: { title: string; text: string; sourceRefs: Array<Record<string, unknown>> }) {
  return (
    <article className="resource-card" data-testid="output-block">
      <ResourceHeader title={title} />
      <MarkdownBlock text={text} />
      <SourceEvidence sourceRefs={sourceRefs} />
    </article>
  );
}

function MarkdownBlock({ text }: { text: string }) {
  return (
    <div className="markdown-body" data-testid="markdown-body">
      <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>{text}</ReactMarkdown>
    </div>
  );
}

function TypewriterMarkdown({ text }: { text: string }) {
  const [visibleText, setVisibleText] = useState("");

  useEffect(() => {
    setVisibleText("");
    if (!text) return;
    let index = 0;
    const timer = window.setInterval(() => {
      index += Math.max(1, Math.ceil(text.length / 120));
      setVisibleText(text.slice(0, index));
      if (index >= text.length) window.clearInterval(timer);
    }, 18);
    return () => window.clearInterval(timer);
  }, [text]);

  return <MarkdownBlock text={visibleText || " "} />;
}

function MindMapDiagram({ text }: { text: string }) {
  const lines = text.split("\n").map((line) => line.trim()).filter(Boolean);
  const center = lines[0]?.replace(/^#+\s*/, "") || "知识主题";
  const nodes = lines.filter((line) => line.startsWith("-") || line.startsWith("分支")).slice(0, 8);
  return (
    <div className="mind-map-diagram" data-testid="mind-map-card">
      <div className="mind-map-center">{center}</div>
      <div className="mind-map-nodes">
        {(nodes.length ? nodes : ["核心概念", "适用场景", "易错点", "练习建议"]).map((node, index) => (
          <span key={index}>{node.replace(/^[-\s分支:：]+/, "")}</span>
        ))}
      </div>
    </div>
  );
}

function extractFencedCode(content: string): string {
  const match = content.match(/```(?:python|py|ts|js)?\s*([\s\S]*?)```/i);
  return match?.[1]?.trim() ?? "";
}

function FullResourceText({ text }: { text: string }) {
  return (
    <details className="full-resource-text">
      <summary>完整资源正文</summary>
      <pre>{text}</pre>
    </details>
  );
}

function ResourceHeader({ title }: { title: string }) {
  return (
    <div className="resource-header">
      <h3>{title}</h3>
    </div>
  );
}

function SourceEvidence({ sourceRefs }: { sourceRefs: Array<Record<string, unknown>> }) {
  return (
    <details className="source-evidence" data-testid="source-panel">
      <summary>
        <span>查看溯源证据</span>
        <small>{sourceRefs.length ? `${Math.min(sourceRefs.length, 5)} 条参考来源` : "暂无来源"}</small>
      </summary>
      <SourcePanel sourceRefs={sourceRefs} />
    </details>
  );
}

function SourcePanel({ sourceRefs }: { sourceRefs: Array<Record<string, unknown>> }) {
  const visibleSources = sourceRefs.slice(0, 5);
  return (
    <div className="source-panel">
      <p className="source-panel-title">可追溯来源</p>
      {visibleSources.length === 0 ? (
        <p className="source-panel-empty" data-testid="source-empty">暂无来源返回</p>
      ) : (
        <div className="source-panel-list">
          {visibleSources.map((source, index) => (
            <details className="source-detail" data-testid="source-detail" key={`${String(source.source_ref ?? source.chunk_id ?? "source")}-${index}`}>
              <summary>
                <span>{String(source.source_ref ?? source.chunk_id ?? "来源")}</span>
                <small>
                  分数 {formatScore(source.rerank_score ?? source.score)}
                  {source.retrieval_mode ? ` / 检索方式 ${String(source.retrieval_mode)}` : ""}
                </small>
              </summary>
              {source.source_title ? <p className="source-title">{String(source.source_title)}</p> : null}
              {source.excerpt ? <p className="source-excerpt">{String(source.excerpt)}</p> : null}
              <p className="source-meta">命中词 {formatList(source.matched_terms)} / 锚点 {formatList(source.anchor_matches)}</p>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}

function AgentLoading({ testId, title, detail }: { testId: string; title: string; detail: string }) {
  return (
    <div className="agent-loading" data-testid={testId} aria-live="polite">
      <span className="agent-loading-dot" />
      <div>
        <p>{title}</p>
        <span>{detail}</span>
      </div>
    </div>
  );
}

function StatusTracker({ testId, steps, compact = false }: { testId: string; steps: TrackerStep[]; compact?: boolean }) {
  return (
    <div className={`status-tracker ${compact ? "status-tracker-compact" : ""}`} data-testid={testId} aria-live="polite">
      {steps.map((step) => (
        <div key={step.label} className={`tracker-step tracker-${step.status}`}>
          <span className="tracker-node">{step.status === "done" ? "✓" : step.status === "active" ? "⚙" : "✨"}</span>
          <div>
            <strong>{step.label}</strong>
            <p>{step.detail}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function Panel({ title, kicker, children }: { title: string; kicker: string; children: ReactNode }) {
  return (
    <section className="panel">
      <p className="eyebrow">{kicker}</p>
      <h2>{title}</h2>
      <div className="panel-body">{children}</div>
    </section>
  );
}

function Metric({ label, value, dark = false }: { label: string; value: string; dark?: boolean }) {
  return (
    <div className={`metric ${dark ? "metric-dark" : ""}`}>
      <p>{label}</p>
      <strong>{value}</strong>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="empty-state">{text}</p>;
}

function StatusLine({ busy, error }: { busy: boolean; error: string | null }) {
  if (busy) return <p className="status-line">正在加载初始数据...</p>;
  if (error) return <p className="error-note">{error}</p>;
  return null;
}
