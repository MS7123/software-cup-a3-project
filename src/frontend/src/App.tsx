import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { api } from "./api/client";
import type {
  AgentRun,
  Concept,
  ConceptGraph,
  DemoDataStatus,
  EvaluationResult,
  GeneratedResource,
  LearningFlow,
  Quiz,
  StudentProfile,
  TutorAnswer
} from "./api/types";

const profileLabels: Record<string, string> = {
  weak_foundation: "基础薄弱型",
  exam_sprint: "考试冲刺型",
  algorithm_practice: "算法实践型"
};

function labelProfile(type: string): string {
  return profileLabels[type] ?? type;
}

function firstSourceRef(sourceRefs: Array<Record<string, unknown>>): string {
  const source = sourceRefs[0];
  if (!source) return "暂无引用";
  return String(source.source_ref ?? source.chunk_id ?? "source");
}

export function App() {
  const [status, setStatus] = useState<DemoDataStatus | null>(null);
  const [profiles, setProfiles] = useState<StudentProfile[]>([]);
  const [graph, setGraph] = useState<ConceptGraph | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null);
  const [goal, setGoal] = useState("复习树与图遍历，准备一次小测");
  const [flow, setFlow] = useState<LearningFlow | null>(null);
  const [resource, setResource] = useState<GeneratedResource | null>(null);
  const [question, setQuestion] = useState("二叉树遍历和 BFS/DFS 的区别是什么？");
  const [answer, setAnswer] = useState<TutorAnswer | null>(null);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [attemptText, setAttemptText] = useState("");
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedProfile = profiles.find((profile) => profile.id === selectedProfileId) ?? null;
  const selectedItem = flow?.learning_path.items[0] ?? null;
  const selectedConcept = useMemo<Concept | null>(() => {
    if (!graph || !selectedItem) return graph?.concepts[0] ?? null;
    return graph.concepts.find((concept) => concept.id === selectedItem.concept_id) ?? null;
  }, [graph, selectedItem]);

  async function runTask(taskName: string, task: () => Promise<void>) {
    setBusy(taskName);
    setError(null);
    try {
      await task();
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败");
    } finally {
      setBusy(null);
    }
  }

  async function refreshBaseData() {
    const nextStatus = await api.getDemoStatus();
    setStatus(nextStatus);
    const nextProfiles = await api.listProfiles();
    setProfiles(nextProfiles);
    setSelectedProfileId((current) => current ?? nextProfiles[0]?.id ?? null);
    if (nextStatus.course_id) {
      setGraph(await api.getCourseGraph(nextStatus.course_id));
    }
  }

  async function appendRun(runId: number | null) {
    if (!runId) return;
    const run = await api.getAgentRun(runId);
    setRuns((current) => [run, ...current.filter((item) => item.id !== run.id)].slice(0, 6));
  }

  useEffect(() => {
    void runTask("初始化", refreshBaseData);
  }, []);

  const canCreateFlow = Boolean(selectedProfileId !== null && status?.course_id);
  const canUseLoop = Boolean(selectedProfileId && status?.course_id && selectedConcept);

  return (
    <main className="min-h-screen bg-paper text-ink">
      <section className="border-b border-ink/10 bg-[radial-gradient(circle_at_top_left,#e9dfc7,transparent_28rem)]">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 py-8 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-moss">A3 Student Console</p>
            <h1 className="mt-4 max-w-3xl font-display text-5xl leading-tight text-ink md:text-6xl">
              数据结构学习闭环工作台
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-graphite/80">
              学生端只消费后端 `/api/v1` 契约，展示画像、路径、资源、问答、测验和 Agent run 摘要。
            </p>
          </div>
          <div className="grid content-end gap-3 sm:grid-cols-2">
            <Metric label="Demo data" value={status?.is_loaded ? "Loaded" : "Pending"} />
            <Metric label="Concepts" value={String(status?.concept_count ?? 0)} />
            <Metric label="Profiles" value={String(status?.profile_count ?? 0)} />
            <Metric label="Chunks" value={String(status?.chunk_count ?? 0)} />
          </div>
        </div>
      </section>

      <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[320px_1fr] lg:px-8">
        <aside className="space-y-5">
          <Panel title="数据入口" kicker="Demo contract">
            <button
              className="w-full rounded-md bg-ink px-4 py-3 text-sm font-semibold text-paper transition hover:bg-graphite disabled:cursor-not-allowed disabled:opacity-55"
              disabled={busy !== null}
              onClick={() =>
                void runTask("加载 demo data", async () => {
                  await api.loadDemoData();
                  await refreshBaseData();
                })
              }
            >
              {busy === "加载 demo data" ? "加载中..." : "加载 / 刷新 demo data"}
            </button>
            {error ? <p className="mt-3 rounded-md bg-signal/10 p-3 text-sm text-signal">{error}</p> : null}
          </Panel>

          <Panel title="学生画像" kicker="Profile">
            <div className="space-y-3">
              {profiles.map((profile) => (
                <button
                  key={profile.id}
                  className={`w-full rounded-md border p-3 text-left transition ${
                    profile.id === selectedProfileId
                      ? "border-signal bg-signal/10"
                      : "border-ink/10 bg-white/45 hover:border-moss"
                  }`}
                  onClick={() => setSelectedProfileId(profile.id)}
                >
                  <span className="block text-sm font-semibold">{labelProfile(profile.profile_type)}</span>
                  <span className="mt-1 block text-xs text-graphite/70">{profile.level} · {profile.time_budget}</span>
                </button>
              ))}
            </div>
          </Panel>
        </aside>

        <section className="space-y-5">
          <Panel title="学习路径" kicker="Planner output">
            <div className="grid gap-3 md:grid-cols-[1fr_auto]">
              <input
                className="rounded-md border border-ink/10 bg-white/70 px-4 py-3 text-sm outline-none focus:border-signal"
                value={goal}
                onChange={(event) => setGoal(event.target.value)}
                aria-label="学习目标"
              />
              <button
                className="rounded-md bg-signal px-5 py-3 text-sm font-semibold text-white transition hover:bg-signal/90 disabled:cursor-not-allowed disabled:opacity-55"
                disabled={!canCreateFlow || busy !== null}
                onClick={() =>
                  void runTask("生成路径", async () => {
                    const nextFlow = await api.createLearningPath(selectedProfileId as number, status?.course_id as number, goal);
                    setFlow(nextFlow);
                    await appendRun(nextFlow.agent_run.id);
                  })
                }
              >
                {busy === "生成路径" ? "生成中..." : "生成路径"}
              </button>
            </div>
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {(flow?.learning_path.items ?? []).map((item) => (
                <div key={item.id} className="rounded-md border border-ink/10 bg-white/55 p-4">
                  <p className="text-xs font-semibold text-moss">Step {item.order_index + 1}</p>
                  <h3 className="mt-1 text-base font-semibold">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-graphite/75">{item.objective}</p>
                </div>
              ))}
              {!flow ? <EmptyState text="生成学习路径后，这里会显示后端返回的 path items。" /> : null}
            </div>
          </Panel>

          <div className="grid gap-5 xl:grid-cols-2">
            <Panel title="资源生成" kicker="Resource Agent">
              <button
                className="rounded-md bg-ink px-4 py-2.5 text-sm font-semibold text-paper disabled:cursor-not-allowed disabled:opacity-55"
                disabled={!selectedItem || busy !== null}
                onClick={() =>
                  void runTask("生成资源", async () => {
                    const nextResource = await api.generateResource(selectedItem!.id, "guided_note");
                    setResource(nextResource);
                    await appendRun(nextResource.agent_run_id);
                  })
                }
              >
                生成当前节点资源
              </button>
              {resource ? (
                <Output title={resource.resource_type} text={resource.content} footnote={firstSourceRef(resource.source_refs)} />
              ) : (
                <EmptyState text="选择路径节点后，从后端生成学习资源。" />
              )}
            </Panel>

            <Panel title="Tutor 问答" kicker="Grounded answer">
              <textarea
                className="h-24 w-full resize-none rounded-md border border-ink/10 bg-white/70 p-3 text-sm outline-none focus:border-signal"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                aria-label="Tutor 问题"
              />
              <button
                className="mt-3 rounded-md bg-ink px-4 py-2.5 text-sm font-semibold text-paper disabled:cursor-not-allowed disabled:opacity-55"
                disabled={!canUseLoop || busy !== null}
                onClick={() =>
                  void runTask("Tutor 回答", async () => {
                    const nextAnswer = await api.askTutor(selectedProfileId as number, status?.course_id as number, question);
                    setAnswer(nextAnswer);
                    await appendRun(nextAnswer.agent_run_id);
                  })
                }
              >
                提问
              </button>
              {answer ? <Output title="Answer" text={answer.answer} footnote={firstSourceRef(answer.source_refs)} /> : null}
            </Panel>
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            <Panel title="Quiz" kicker="Quiz Agent">
              <button
                className="rounded-md bg-ink px-4 py-2.5 text-sm font-semibold text-paper disabled:cursor-not-allowed disabled:opacity-55"
                disabled={!canUseLoop || busy !== null}
                onClick={() =>
                  void runTask("生成 Quiz", async () => {
                    const nextQuiz = await api.generateQuiz(selectedProfileId as number, selectedConcept!.id, "medium");
                    setQuiz(nextQuiz);
                    setAttemptText("");
                    await appendRun(nextQuiz.agent_run_id);
                  })
                }
              >
                生成测验
              </button>
              {quiz?.items[0] ? (
                <div className="mt-4 space-y-3">
                  <p className="text-sm font-semibold">{quiz.items[0].question}</p>
                  <textarea
                    className="h-24 w-full resize-none rounded-md border border-ink/10 bg-white/70 p-3 text-sm outline-none focus:border-signal"
                    value={attemptText}
                    onChange={(event) => setAttemptText(event.target.value)}
                    aria-label="测验作答"
                  />
                  <button
                    className="rounded-md bg-signal px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-55"
                    disabled={!attemptText || busy !== null}
                    onClick={() =>
                      void runTask("提交作答", async () => {
                        const nextEvaluation = await api.submitAttempt(quiz.id, selectedProfileId as number, {
                          answer: attemptText
                        });
                        setEvaluation(nextEvaluation);
                        await appendRun(nextEvaluation.agent_run_id);
                      })
                    }
                  >
                    提交作答
                  </button>
                </div>
              ) : (
                <EmptyState text="从当前知识点生成测验题。" />
              )}
            </Panel>

            <Panel title="Evaluator" kicker="Mastery signal">
              {evaluation ? (
                <div className="space-y-4">
                  <Metric label="Score" value={`${Math.round(evaluation.score * 100)}%`} />
                  <p className="rounded-md bg-white/60 p-4 text-sm leading-6 text-graphite/80">{evaluation.feedback}</p>
                </div>
              ) : (
                <EmptyState text="提交作答后展示后端 evaluator 返回的评分和掌握度建议。" />
              )}
            </Panel>
          </div>

          <Panel title="Agent runs" kicker="Trace">
            <div className="space-y-3">
              {runs.map((run) => (
                <div key={run.id} className="rounded-md border border-ink/10 bg-white/55 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-semibold">{run.run_type}</p>
                    <span className="rounded-full bg-moss/15 px-3 py-1 text-xs font-semibold text-moss">{run.status}</span>
                  </div>
                  <p className="mt-2 text-sm text-graphite/70">{run.final_summary ?? run.output_summary ?? run.input_summary}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {run.steps.map((step) => (
                      <span key={step.id} className="rounded-full border border-ink/10 px-3 py-1 text-xs text-graphite">
                        {step.step_order}. {step.agent_type}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
              {runs.length === 0 ? <EmptyState text="执行路径、资源、问答或测验后，这里会展示 agent run 摘要。" /> : null}
            </div>
          </Panel>
        </section>
      </div>
    </main>
  );
}

function Panel({ title, kicker, children }: { title: string; kicker: string; children: ReactNode }) {
  return (
    <section className="rounded-md border border-ink/10 bg-chalk/55 p-5 shadow-panel backdrop-blur">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-moss">{kicker}</p>
      <h2 className="mt-1 font-display text-2xl text-ink">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-ink/10 bg-white/55 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-moss">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function Output({ title, text, footnote }: { title: string; text: string; footnote: string }) {
  return (
    <article className="mt-4 rounded-md border border-ink/10 bg-white/60 p-4">
      <h3 className="text-sm font-semibold">{title}</h3>
      <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-graphite/80">{text}</p>
      <p className="mt-3 text-xs font-semibold text-moss">Source: {footnote}</p>
    </article>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="rounded-md border border-dashed border-ink/20 p-4 text-sm leading-6 text-graphite/60">{text}</p>;
}
