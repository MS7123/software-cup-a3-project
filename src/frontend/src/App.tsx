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
  LearningPathItem,
  Quiz,
  StudentProfile,
  TutorAnswer
} from "./api/types";

type BusyAction =
  | "boot"
  | "load-demo"
  | "create-path"
  | "generate-resource"
  | "ask-tutor"
  | "generate-quiz"
  | "submit-attempt";

const profileLabels: Record<string, string> = {
  weak_foundation: "Foundation repair",
  exam_sprint: "Exam sprint",
  algorithm_practice: "Algorithm practice"
};

const agentTone: Record<string, string> = {
  planner: "Path design",
  resource: "Learning asset",
  tutor: "Grounded answer",
  quiz: "Assessment item",
  evaluator: "Mastery signal"
};

function labelProfile(type: string): string {
  return profileLabels[type] ?? type.replaceAll("_", " ");
}

function sourceLabel(sourceRefs: Array<Record<string, unknown>>): string {
  const source = sourceRefs[0];
  if (!source) return "No source returned";
  return String(source.source_ref ?? source.chunk_id ?? "source");
}

function toErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return "Request failed";
}

export function App() {
  const [status, setStatus] = useState<DemoDataStatus | null>(null);
  const [profiles, setProfiles] = useState<StudentProfile[]>([]);
  const [graph, setGraph] = useState<ConceptGraph | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null);
  const [selectedPathItemId, setSelectedPathItemId] = useState<number | null>(null);
  const [goal, setGoal] = useState("Review tree traversal and graph search for a short quiz");
  const [flow, setFlow] = useState<LearningFlow | null>(null);
  const [resource, setResource] = useState<GeneratedResource | null>(null);
  const [question, setQuestion] = useState("How are BFS and DFS different in data structures?");
  const [answer, setAnswer] = useState<TutorAnswer | null>(null);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [attemptText, setAttemptText] = useState("");
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [busy, setBusy] = useState<BusyAction | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedProfile = profiles.find((profile) => profile.id === selectedProfileId) ?? null;
  const pathItems = flow?.learning_path.items ?? [];
  const selectedItem = pathItems.find((item) => item.id === selectedPathItemId) ?? pathItems[0] ?? null;
  const selectedConcept = useMemo<Concept | null>(() => {
    if (!graph) return null;
    if (selectedItem) {
      return graph.concepts.find((concept) => concept.id === selectedItem.concept_id) ?? null;
    }
    return graph.concepts[0] ?? null;
  }, [graph, selectedItem]);

  const canCreatePath = Boolean(selectedProfileId && status?.course_id);
  const canUseLoop = Boolean(selectedProfileId && status?.course_id && selectedConcept);

  async function runTask(action: BusyAction, task: () => Promise<void>) {
    setBusy(action);
    setError(null);
    try {
      await task();
    } catch (err) {
      setError(toErrorMessage(err));
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
      const nextGraph = await api.getCourseGraph(nextStatus.course_id);
      setGraph(nextGraph);
    } else {
      setGraph(null);
    }
  }

  async function appendRun(runId: number | null) {
    if (!runId) return;
    const run = await api.getAgentRun(runId);
    setRuns((current) => [run, ...current.filter((item) => item.id !== run.id)].slice(0, 8));
  }

  function resetLoopOutputs() {
    setResource(null);
    setAnswer(null);
    setQuiz(null);
    setAttemptText("");
    setEvaluation(null);
  }

  useEffect(() => {
    void runTask("boot", refreshBaseData);
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="border-b border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#19352e_54%,#b9432f_100%)]">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 py-8 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.26em] text-emerald-200">A3 Student Console</p>
            <h1 className="mt-4 max-w-3xl font-display text-5xl leading-tight text-white md:text-6xl">
              Data structures learning loop
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-200">
              A student-facing workspace for profile selection, path planning, resources, tutor answers, quiz attempts,
              evaluator feedback, and agent run review. All domain output is loaded from the backend API.
            </p>
          </div>
          <div className="grid content-end gap-3 sm:grid-cols-2">
            <Metric label="Demo data" value={status?.is_loaded ? "Loaded" : "Pending"} dark />
            <Metric label="Profiles" value={String(status?.profile_count ?? 0)} dark />
            <Metric label="Concepts" value={String(status?.concept_count ?? 0)} dark />
            <Metric label="Agent runs" value={String(runs.length)} dark />
          </div>
        </div>
      </section>

      <div className="mx-auto grid max-w-7xl gap-5 px-5 py-6 lg:grid-cols-[340px_1fr] lg:px-8">
        <aside className="space-y-5">
          <Panel title="Session setup" kicker="Demo contract">
            <button
              className="action-button w-full"
              disabled={busy !== null}
              onClick={() =>
                void runTask("load-demo", async () => {
                  await api.loadDemoData();
                  await refreshBaseData();
                })
              }
            >
              {busy === "load-demo" ? "Loading demo data" : "Load or refresh demo data"}
            </button>
            <StatusLine busy={busy === "boot"} error={error} />
          </Panel>

          <Panel title="Student profile" kicker="Persona">
            <div className="space-y-3">
              {profiles.map((profile) => (
                <button
                  key={profile.id}
                  className={`profile-option ${profile.id === selectedProfileId ? "profile-option-active" : ""}`}
                  onClick={() => {
                    setSelectedProfileId(profile.id);
                    resetLoopOutputs();
                  }}
                >
                  <span className="block text-sm font-semibold">{labelProfile(profile.profile_type)}</span>
                  <span className="mt-1 block text-xs text-slate-500">
                    {profile.level} / {profile.time_budget}
                  </span>
                  <span className="mt-2 line-clamp-3 block text-xs leading-5 text-slate-600">{profile.goal}</span>
                </button>
              ))}
              {profiles.length === 0 ? <EmptyState text="Load demo data to fetch profiles from the backend." /> : null}
            </div>
          </Panel>

          <Panel title="Course graph" kicker="Concepts">
            <div className="space-y-2">
              {(graph?.concepts ?? []).map((concept) => (
                <div
                  key={concept.id}
                  className={`rounded-md border px-3 py-2 text-sm ${
                    concept.id === selectedConcept?.id ? "border-signal bg-signal/10" : "border-slate-200 bg-white"
                  }`}
                >
                  <p className="font-semibold text-slate-900">{concept.name}</p>
                  <p className="text-xs text-slate-500">{concept.difficulty}</p>
                </div>
              ))}
              {!graph ? <EmptyState text="Course graph is loaded from /api/v1 after demo data is available." /> : null}
            </div>
          </Panel>
        </aside>

        <section className="space-y-5">
          <Panel title="Learning path" kicker="Planner">
            <div className="grid gap-3 md:grid-cols-[1fr_auto]">
              <input
                className="field"
                value={goal}
                onChange={(event) => setGoal(event.target.value)}
                aria-label="Learning goal"
              />
              <button
                className="primary-button"
                disabled={!canCreatePath || busy !== null}
                onClick={() =>
                  void runTask("create-path", async () => {
                    const nextFlow = await api.createLearningPath(selectedProfileId as number, status?.course_id as number, goal);
                    setFlow(nextFlow);
                    setSelectedPathItemId(nextFlow.learning_path.items[0]?.id ?? null);
                    resetLoopOutputs();
                    await appendRun(nextFlow.agent_run.id);
                  })
                }
              >
                {busy === "create-path" ? "Creating path" : "Create path"}
              </button>
            </div>
            <div className="mt-4 grid gap-3 xl:grid-cols-2">
              {pathItems.map((item) => (
                <PathItemCard
                  key={item.id}
                  item={item}
                  concept={graph?.concepts.find((concept) => concept.id === item.concept_id) ?? null}
                  selected={item.id === selectedItem?.id}
                  onSelect={() => {
                    setSelectedPathItemId(item.id);
                    resetLoopOutputs();
                  }}
                />
              ))}
              {pathItems.length === 0 ? (
                <EmptyState text="Create a learning path to receive ordered path items from the backend." />
              ) : null}
            </div>
          </Panel>

          <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
            <Panel title="Resource" kicker="Resource Agent">
              <NodeSummary item={selectedItem} concept={selectedConcept} />
              <button
                className="action-button mt-4"
                disabled={!selectedItem || busy !== null}
                onClick={() =>
                  void runTask("generate-resource", async () => {
                    const nextResource = await api.generateResource(selectedItem!.id, "guided_note");
                    setResource(nextResource);
                    await appendRun(nextResource.agent_run_id);
                  })
                }
              >
                {busy === "generate-resource" ? "Generating resource" : "Generate resource for selected node"}
              </button>
              {resource ? (
                <OutputBlock title={resource.resource_type} text={resource.content} source={sourceLabel(resource.source_refs)} />
              ) : (
                <EmptyState text="The generated resource will appear here after the backend Resource Agent responds." />
              )}
            </Panel>

            <Panel title="Tutor" kicker="Grounded Q&A">
              <textarea
                className="field min-h-28 resize-none"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                aria-label="Tutor question"
              />
              <button
                className="action-button mt-3"
                disabled={!canUseLoop || busy !== null}
                onClick={() =>
                  void runTask("ask-tutor", async () => {
                    const nextAnswer = await api.askTutor(selectedProfileId as number, status?.course_id as number, question);
                    setAnswer(nextAnswer);
                    await appendRun(nextAnswer.agent_run_id);
                  })
                }
              >
                {busy === "ask-tutor" ? "Asking tutor" : "Ask tutor"}
              </button>
              {answer ? (
                <OutputBlock title="Tutor answer" text={answer.answer} source={sourceLabel(answer.source_refs)} />
              ) : (
                <EmptyState text="Tutor answers are grounded by backend document chunks and include returned source refs." />
              )}
            </Panel>
          </div>

          <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
            <Panel title="Quiz attempt" kicker="Quiz Agent">
              <button
                className="action-button"
                disabled={!canUseLoop || busy !== null}
                onClick={() =>
                  void runTask("generate-quiz", async () => {
                    const nextQuiz = await api.generateQuiz(selectedProfileId as number, selectedConcept!.id, "medium");
                    setQuiz(nextQuiz);
                    setAttemptText("");
                    setEvaluation(null);
                    await appendRun(nextQuiz.agent_run_id);
                  })
                }
              >
                {busy === "generate-quiz" ? "Generating quiz" : "Generate quiz for selected concept"}
              </button>

              {quiz?.items[0] ? (
                <div className="mt-4 space-y-3">
                  <div className="rounded-md border border-slate-200 bg-white p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-moss">Question</p>
                    <p className="mt-2 text-sm font-semibold leading-6 text-slate-900">{quiz.items[0].question}</p>
                    <p className="mt-3 text-xs text-slate-500">{quiz.items[0].concept_tags.join(" / ")}</p>
                  </div>
                  <textarea
                    className="field min-h-28 resize-none"
                    value={attemptText}
                    onChange={(event) => setAttemptText(event.target.value)}
                    aria-label="Quiz answer"
                    placeholder="Type your answer and submit it to the evaluator."
                  />
                  <button
                    className="primary-button"
                    disabled={!attemptText.trim() || busy !== null}
                    onClick={() =>
                      void runTask("submit-attempt", async () => {
                        const nextEvaluation = await api.submitAttempt(quiz.id, selectedProfileId as number, {
                          answer: attemptText
                        });
                        setEvaluation(nextEvaluation);
                        await appendRun(nextEvaluation.agent_run_id);
                      })
                    }
                  >
                    {busy === "submit-attempt" ? "Submitting answer" : "Submit answer"}
                  </button>
                </div>
              ) : (
                <EmptyState text="Generate a quiz after selecting a path node or concept." />
              )}
            </Panel>

            <Panel title="Evaluator feedback" kicker="Mastery">
              {evaluation ? (
                <div className="space-y-4">
                  <Metric label="Score" value={`${Math.round(evaluation.score * 100)}%`} />
                  <p className="rounded-md bg-white p-4 text-sm leading-6 text-slate-700">{evaluation.feedback}</p>
                  <div className="space-y-2">
                    {evaluation.mastery_updates.map((update, index) => (
                      <div key={index} className="rounded-md border border-slate-200 bg-white p-3 text-sm text-slate-700">
                        <p className="font-semibold">Concept {String(update.concept_id ?? "unknown")}</p>
                        <p className="mt-1">Mastery: {String(update.mastery_score ?? "n/a")}</p>
                        <p className="mt-1 text-xs text-slate-500">{String(update.evidence ?? "No evidence returned")}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <EmptyState text="Submit an answer to display score, feedback, and mastery update suggestions." />
              )}
            </Panel>
          </div>

          <Panel title="Agent run trace" kicker="Explainability">
            <div className="grid gap-3 lg:grid-cols-2">
              {runs.map((run) => (
                <RunCard key={run.id} run={run} />
              ))}
              {runs.length === 0 ? (
                <EmptyState text="Planner, Resource, Tutor, Quiz, and Evaluator runs will be listed here after actions complete." />
              ) : null}
            </div>
          </Panel>
        </section>
      </div>
    </main>
  );
}

function PathItemCard({
  item,
  concept,
  selected,
  onSelect
}: {
  item: LearningPathItem;
  concept: Concept | null;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button className={`path-card ${selected ? "path-card-active" : ""}`} onClick={onSelect}>
      <span className="text-xs font-semibold uppercase tracking-[0.16em] text-moss">Step {item.order_index + 1}</span>
      <span className="mt-2 block text-left text-base font-semibold text-slate-950">{item.title}</span>
      <span className="mt-2 block text-left text-sm leading-6 text-slate-600">{item.objective}</span>
      <span className="mt-3 block text-left text-xs text-slate-500">{concept?.name ?? `Concept ${item.concept_id}`}</span>
    </button>
  );
}

function NodeSummary({ item, concept }: { item: LearningPathItem | null; concept: Concept | null }) {
  if (!item) return <EmptyState text="Select or create a path node before generating resources." />;

  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-moss">Current node</p>
      <p className="mt-2 text-sm font-semibold text-slate-950">{item.title}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{item.objective}</p>
      <p className="mt-3 text-xs text-slate-500">{concept?.name ?? `Concept ${item.concept_id}`}</p>
    </div>
  );
}

function RunCard({ run }: { run: AgentRun }) {
  return (
    <article className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-950">{run.run_type}</h3>
        <span className="rounded-full bg-moss/15 px-3 py-1 text-xs font-semibold text-moss">{run.status}</span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">{run.final_summary ?? run.output_summary ?? run.input_summary}</p>
      <div className="mt-4 space-y-2">
        {run.steps.map((step) => (
          <div key={step.id} className="rounded-md bg-slate-50 p-3">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              {step.step_order}. {agentTone[step.agent_type] ?? step.agent_type}
            </p>
            <p className="mt-1 text-sm text-slate-700">{step.output_summary}</p>
            <p className="mt-1 text-xs text-slate-500">{step.decision_basis}</p>
          </div>
        ))}
      </div>
    </article>
  );
}

function Panel({ title, kicker, children }: { title: string; kicker: string; children: ReactNode }) {
  return (
    <section className="rounded-md border border-slate-200 bg-slate-100 p-5 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-moss">{kicker}</p>
      <h2 className="mt-1 font-display text-2xl text-slate-950">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function Metric({ label, value, dark = false }: { label: string; value: string; dark?: boolean }) {
  return (
    <div className={`rounded-md border p-4 ${dark ? "border-white/15 bg-white/10" : "border-slate-200 bg-white"}`}>
      <p className={`text-xs font-semibold uppercase tracking-[0.16em] ${dark ? "text-emerald-200" : "text-moss"}`}>{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${dark ? "text-white" : "text-slate-950"}`}>{value}</p>
    </div>
  );
}

function OutputBlock({ title, text, source }: { title: string; text: string; source: string }) {
  return (
    <article className="mt-4 rounded-md border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-semibold text-slate-950">{title}</h3>
      <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{text}</p>
      <p className="mt-3 text-xs font-semibold text-moss">Source: {source}</p>
    </article>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="rounded-md border border-dashed border-slate-300 p-4 text-sm leading-6 text-slate-500">{text}</p>;
}

function StatusLine({ busy, error }: { busy: boolean; error: string | null }) {
  if (busy) return <p className="mt-3 rounded-md bg-white p-3 text-sm text-slate-600">Loading initial data...</p>;
  if (error) return <p className="mt-3 rounded-md bg-signal/10 p-3 text-sm text-signal">{error}</p>;
  return null;
}
