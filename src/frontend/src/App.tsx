import { useEffect, useMemo, useState } from "react";
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
  StudentProfile,
  TutorAnswer
} from "./api/types";

type BusyAction =
  | "load-demo"
  | "reset-demo"
  | "build-profile"
  | "update-profile"
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

const profileDimensions = [
  ["learning_goal", "Goal"],
  ["foundation_level", "Level"],
  ["learning_preference", "Preference"],
  ["available_time", "Time"],
  ["weak_points", "Weak points"],
  ["resource_preference", "Resource"]
] as const;

const resourceOptions = [
  { type: "guided_note", label: "讲解" },
  { type: "practice_questions", label: "练习" },
  { type: "mind_map", label: "导图" },
  { type: "extended_reading", label: "拓展" },
  { type: "coding_case", label: "代码" }
] as const;

function labelProfile(type: string): string {
  return profileLabels[type] ?? type.replaceAll("_", " ");
}

function formatMetadataList(value: unknown): string {
  if (!Array.isArray(value) || value.length === 0) return "none";
  return value.map((item) => String(item)).join(", ");
}

function formatScore(value: unknown): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "n/a";
  return value.toFixed(2);
}

function excerpt(text: string, maxLength = 160): string {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (normalized.length <= maxLength) return normalized;
  return `${normalized.slice(0, maxLength - 1)}...`;
}

function documentDisplayName(document: {
  title: string;
  file_name?: string | null;
}): string {
  return document.file_name || document.title || "Imported document";
}

function resultDisplayName(result: KnowledgeSearchResult): string {
  return String(result.metadata?.filename ?? result.metadata?.source_title ?? result.source_ref ?? "Knowledge source");
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
  const [profileDialogue, setProfileDialogue] = useState(
    "我基础薄弱，想每天 1 小时复习二叉树遍历和 BFS/DFS，希望用例题和练习题准备小测"
  );
  const [goal, setGoal] = useState("Review tree traversal and graph search for a short quiz");
  const [knowledgeTitle, setKnowledgeTitle] = useState("bfs-dfs-note.md");
  const [knowledgeSourceType, setKnowledgeSourceType] = useState<"text" | "markdown">("markdown");
  const [knowledgeContent, setKnowledgeContent] = useState(
    "# BFS and DFS\nBFS uses a queue to expand nodes level by level, so in an unweighted graph the first time a node is reached represents the fewest edges. DFS uses a stack or recursion to go deep first, which is better for traversal and backtracking but does not guarantee shortest paths."
  );
  const [knowledgeQuery, setKnowledgeQuery] = useState("BFS shortest path queue DFS");
  const [knowledgeFile, setKnowledgeFile] = useState<File | null>(null);
  const [knowledgeImportResult, setKnowledgeImportResult] = useState<DocumentIngestionResponse | null>(null);
  const [knowledgeReindexResult, setKnowledgeReindexResult] = useState<DocumentReindexResponse | null>(null);
  const [knowledgeDocuments, setKnowledgeDocuments] = useState<ManagedDocument[]>([]);
  const [knowledgeSearchResults, setKnowledgeSearchResults] = useState<KnowledgeSearchResult[]>([]);
  const [knowledgeError, setKnowledgeError] = useState<string | null>(null);
  const [flow, setFlow] = useState<LearningFlow | null>(null);
  const [resource, setResource] = useState<GeneratedResource | null>(null);
  const [resourceType, setResourceType] = useState<(typeof resourceOptions)[number]["type"]>("guided_note");
  const [question, setQuestion] = useState("How are BFS and DFS different in data structures?");
  const [answer, setAnswer] = useState<TutorAnswer | null>(null);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [attemptText, setAttemptText] = useState("");
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [autoProfileUpdate, setAutoProfileUpdate] = useState<string | null>(null);
  const [autoProfileUpdateEnabled, setAutoProfileUpdateEnabled] = useState(true);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [busy, setBusy] = useState<BusyAction | null>(null);
  const [booting, setBooting] = useState(true);
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
      const message = toErrorMessage(err);
      setError(message);
      if (
        action === "import-knowledge" ||
        action === "upload-knowledge" ||
        action === "search-knowledge" ||
        action === "refresh-documents" ||
        action === "delete-document" ||
        action === "reindex-document"
      ) {
        setKnowledgeError(message);
      }
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
      const nextGraph = await api.getCourseGraph(nextStatus.course_id);
      setGraph(nextGraph);
      const nextDocuments = await api.listCourseDocuments(nextStatus.course_id);
      setKnowledgeDocuments(nextDocuments);
    } else {
      setGraph(null);
      setKnowledgeDocuments([]);
    }
  }

  async function appendRun(runId: number | null) {
    if (!runId) return;
    const run = await api.getAgentRun(runId);
    setRuns((current) => [run, ...current.filter((item) => item.id !== run.id)].slice(0, 8));
  }

  function replaceOrAppendProfile(nextProfile: StudentProfile) {
    setProfiles((current) => [nextProfile, ...current.filter((profile) => profile.id !== nextProfile.id)]);
    setSelectedProfileId(nextProfile.id);
    resetLoopOutputs();
    setFlow(null);
    setSelectedPathItemId(null);
    setRuns([]);
  }

  function refreshSelectedProfile(nextProfile: StudentProfile) {
    setProfiles((current) => current.map((profile) => (profile.id === nextProfile.id ? nextProfile : profile)));
    setSelectedProfileId(nextProfile.id);
  }

  async function deleteProfile(profileId: number) {
    await api.deleteProfile(profileId);
    const nextProfiles = await api.listProfiles();
    setProfiles(nextProfiles);
    setSelectedProfileId(nextProfiles[0]?.id ?? null);
    resetLoopOutputs();
    setFlow(null);
    setSelectedPathItemId(null);
    setRuns([]);
  }

  function resetLoopOutputs() {
    setResource(null);
    setAnswer(null);
    setQuiz(null);
    setAttemptText("");
    setEvaluation(null);
    setAutoProfileUpdate(null);
  }

  async function importKnowledge() {
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
  }

  async function uploadKnowledgeFile() {
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
  }

  async function refreshKnowledgeDocuments() {
    if (!status?.course_id) return;
    setKnowledgeError(null);
    const documents = await api.listCourseDocuments(status.course_id);
    setKnowledgeDocuments(documents);
  }

  async function deleteKnowledgeDocument(documentId: number) {
    if (!status?.course_id) return;
    setKnowledgeError(null);
    await api.deleteDocument(documentId);
    setKnowledgeSearchResults([]);
    setKnowledgeImportResult(null);
    setKnowledgeReindexResult(null);
    await refreshKnowledgeDocuments();
  }

  async function reindexKnowledgeDocument(documentId: number) {
    setKnowledgeError(null);
    const result = await api.reindexDocument(documentId);
    setKnowledgeReindexResult(result);
  }

  async function searchKnowledge() {
    if (!status?.course_id) return;
    setKnowledgeError(null);
    const result = await api.searchKnowledge(status.course_id, knowledgeQuery, 3);
    setKnowledgeSearchResults(result.results);
  }

  async function submitQuizAttempt() {
    if (!quiz || !selectedProfileId || !attemptText.trim()) return;

    setBusy("submit-attempt");
    setError(null);
    setAutoProfileUpdate(null);
    try {
      const nextEvaluation = await api.submitAttempt(quiz.id, selectedProfileId, {
        answer: attemptText
      });
      setEvaluation(nextEvaluation);
      await appendRun(nextEvaluation.agent_run_id);

      if (!autoProfileUpdateEnabled) {
        setAutoProfileUpdate("Auto profile update is off. Use manual trace update when you want to sync the profile.");
        return;
      }

      setBusy("sync-profile");
      const nextProfile = await api.updateProfileFromTrace(selectedProfileId);
      refreshSelectedProfile(nextProfile);
      setAutoProfileUpdate(String(nextProfile.preferences.last_profile_update_reason ?? "Profile updated from trace."));
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  useEffect(() => {
    let active = true;
    setBooting(true);
    setError(null);

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
              data-testid="load-demo-button"
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
            <button
              className="danger-button mt-3 w-full"
              data-testid="reset-demo-button"
              disabled={busy !== null}
              onClick={() =>
                void runTask("reset-demo", async () => {
                  await api.resetDemoUserData();
                  await refreshBaseData();
                  resetLoopOutputs();
                  setFlow(null);
                  setSelectedPathItemId(null);
                  setRuns([]);
                })
              }
            >
              {busy === "reset-demo" ? "Resetting demo" : "Reset user demo data"}
            </button>
            <StatusLine busy={booting} error={error} />
          </Panel>

          <Panel title="Knowledge setup" kicker="RAG import">
            <div className="space-y-3">
              <input
                className="field"
                data-testid="knowledge-title"
                value={knowledgeTitle}
                onChange={(event) => setKnowledgeTitle(event.target.value)}
                aria-label="Knowledge document title"
              />
              <select
                className="field"
                data-testid="knowledge-source-type"
                value={knowledgeSourceType}
                onChange={(event) => setKnowledgeSourceType(event.target.value as "text" | "markdown")}
                aria-label="Knowledge source type"
              >
                <option value="markdown">markdown</option>
                <option value="text">text</option>
              </select>
              <textarea
                className="field min-h-36 resize-none"
                data-testid="knowledge-content"
                value={knowledgeContent}
                onChange={(event) => setKnowledgeContent(event.target.value)}
                aria-label="Knowledge content"
              />
              <div className="file-upload-box">
                <input
                  className="field"
                  data-testid="knowledge-file"
                  type="file"
                  accept=".txt,.md,.markdown,.pdf,.docx,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={(event) => {
                    const file = event.target.files?.[0] ?? null;
                    setKnowledgeFile(file);
                    if (file) setKnowledgeTitle(file.name);
                  }}
                  aria-label="Knowledge file upload"
                />
                <button
                  className="action-button w-full"
                  data-testid="upload-knowledge-button"
                  disabled={!status?.course_id || !knowledgeFile || busy !== null}
                  onClick={() =>
                    void runTask("upload-knowledge", async () => {
                      await uploadKnowledgeFile();
                    })
                  }
                >
                  {busy === "upload-knowledge" ? "Uploading file" : "Upload selected file"}
                </button>
              </div>
              <button
                className="action-button w-full"
                data-testid="import-knowledge-button"
                disabled={!status?.course_id || !knowledgeTitle.trim() || !knowledgeContent.trim() || busy !== null}
                onClick={() =>
                  void runTask("import-knowledge", async () => {
                    await importKnowledge();
                  })
                }
              >
                {busy === "import-knowledge" ? "Importing knowledge" : "Import knowledge"}
              </button>
              {knowledgeImportResult ? (
                <div className="knowledge-result" data-testid="knowledge-import-result">
                  <p>{documentDisplayName(knowledgeImportResult.document)}</p>
                  <p>
                    Imported / {knowledgeImportResult.chunk_count} chunks / {knowledgeImportResult.document.source_type} /{" "}
                    {knowledgeImportResult.document.parser_name ?? "parser n/a"}
                  </p>
                </div>
              ) : null}
              {knowledgeReindexResult ? (
                <div className="knowledge-result" data-testid="knowledge-reindex-result">
                  <p>
                    Reindex complete: indexed {knowledgeReindexResult.indexed}, skipped {knowledgeReindexResult.skipped}, failed{" "}
                    {knowledgeReindexResult.failed}
                  </p>
                  <span>{knowledgeReindexResult.message}</span>
                </div>
              ) : null}
              <div className="document-management" data-testid="document-management">
                <div className="document-management-header">
                  <strong>Documents</strong>
                  <button
                    className="small-button"
                    data-testid="refresh-documents-button"
                    disabled={!status?.course_id || busy !== null}
                    onClick={() =>
                      void runTask("refresh-documents", async () => {
                        await refreshKnowledgeDocuments();
                      })
                    }
                  >
                    {busy === "refresh-documents" ? "Refreshing" : "Refresh"}
                  </button>
                </div>
                {knowledgeDocuments.length > 0 ? (
                  <div className="document-list" data-testid="document-list">
                    {knowledgeDocuments.map((document) => (
                      <div className="document-row" data-testid="document-row" key={document.id}>
                        <div>
                          <p>{documentDisplayName(document)}</p>
                          <span>
                            {document.source_type} / {document.chunk_count} chunks / {document.status}
                            {document.visibility ? ` / ${document.visibility}` : ""}
                          </span>
                          <span className="hidden">
                            #{document.id} / {document.source_type} / {document.chunk_count} chunks / {document.status}
                          </span>
                        </div>
                        <div className="document-actions">
                          <button
                            className="document-reindex-button"
                            data-testid="reindex-document-button"
                            disabled={busy !== null || document.status === "deleted"}
                            onClick={() =>
                              void runTask("reindex-document", async () => {
                                await reindexKnowledgeDocument(document.id);
                              })
                            }
                          >
                            {busy === "reindex-document" ? "Indexing" : "Reindex"}
                          </button>
                          <button
                            className="document-delete-button"
                            data-testid="delete-document-button"
                            disabled={busy !== null || document.status === "deleted" || document.source_type === "seed"}
                            onClick={() =>
                              void runTask("delete-document", async () => {
                                await deleteKnowledgeDocument(document.id);
                              })
                            }
                          >
                            {busy === "delete-document" ? "Deleting" : "Delete"}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="document-empty" data-testid="document-empty">No documents loaded for this course.</p>
                )}
              </div>
              <div className="knowledge-search-box">
                <input
                  className="field"
                  data-testid="knowledge-query"
                  value={knowledgeQuery}
                  onChange={(event) => setKnowledgeQuery(event.target.value)}
                  aria-label="Knowledge search query"
                />
                <button
                  className="primary-button w-full"
                  data-testid="search-knowledge-button"
                  disabled={!status?.course_id || !knowledgeQuery.trim() || busy !== null}
                onClick={() =>
                    void runTask("search-knowledge", async () => {
                      await searchKnowledge();
                    })
                  }
                >
                  {busy === "search-knowledge" ? "Searching" : "Search imported chunks"}
                </button>
                {knowledgeSearchResults.length > 0 ? (
                  <div className="knowledge-search-results" data-testid="knowledge-search-results">
                    {knowledgeSearchResults.map((result) => (
                      <div key={result.chunk_id ?? result.source_ref} className="knowledge-search-result">
                        <p>{resultDisplayName(result)}</p>
                        <span>
                          score {formatScore(result.score)} · mode {String(result.metadata?.retrieval_mode ?? "n/a")} ·
                          vector {formatScore(result.metadata?.vector_score)} · rerank {formatScore(result.metadata?.rerank_score)} · matched{" "}
                          {formatMetadataList(result.metadata?.matched_terms)} · anchors{" "}
                          {formatMetadataList(result.metadata?.anchor_matches)}
                        </span>
                        <p className="knowledge-search-excerpt">{String(result.metadata?.excerpt ?? excerpt(result.content))}</p>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
              {knowledgeError ? <p className="error-note">{knowledgeError}</p> : null}
            </div>
          </Panel>

          <Panel title="Student profile" kicker="Persona">
            <div className="space-y-3">
              <textarea
                className="field min-h-28 resize-none"
                data-testid="profile-dialogue"
                value={profileDialogue}
                onChange={(event) => setProfileDialogue(event.target.value)}
                aria-label="Profile dialogue"
              />
              <button
                className="action-button w-full"
                data-testid="build-profile-button"
                disabled={!profileDialogue.trim() || busy !== null}
                onClick={() =>
                  void runTask("build-profile", async () => {
                    const nextProfile = await api.createProfileFromDialogue({ dialogue: profileDialogue });
                    replaceOrAppendProfile(nextProfile);
                  })
                }
              >
                {busy === "build-profile" ? "Building profile" : "Build profile from dialogue"}
              </button>
              {profiles.map((profile) => {
                const isDemoProfile = profile.preferences.profile_origin === "demo";
                return (
                  <div
                    key={profile.id}
                    className={`profile-option ${profile.id === selectedProfileId ? "profile-option-active" : ""}`}
                    data-testid="profile-option"
                  >
                    <button
                      className="profile-select-button"
                      onClick={() => {
                        setSelectedProfileId(profile.id);
                        resetLoopOutputs();
                      }}
                    >
                      <span className="block text-sm font-semibold">{labelProfile(profile.profile_type)}</span>
                      <span className="mt-1 block text-xs text-slate-500">
                        {profile.level} / {profile.time_budget}
                      </span>
                      <span className="mt-1 block text-xs font-semibold text-moss">
                        {profileDimensions.filter(([key]) => profile.preferences[key] !== undefined).length} profile dimensions
                      </span>
                      <span className="mt-2 line-clamp-3 block text-xs leading-5 text-slate-600">{profile.goal}</span>
                    </button>
                    {!isDemoProfile ? (
                      <button
                        className="profile-delete-button"
                        data-testid="delete-profile-button"
                        disabled={busy !== null}
                        onClick={() => void runTask("delete-profile", () => deleteProfile(profile.id))}
                      >
                        Delete
                      </button>
                    ) : null}
                  </div>
                );
              })}
              {profiles.length === 0 ? <EmptyState text="Load demo data to fetch profiles from the backend." /> : null}
              {selectedProfile ? <ProfileDimensionList profile={selectedProfile} /> : null}
              <button
                className="action-button w-full"
                data-testid="update-profile-button"
                disabled={!selectedProfileId || runs.length === 0 || busy !== null}
                onClick={() =>
                  void runTask("update-profile", async () => {
                    const nextProfile = await api.updateProfileFromTrace(selectedProfileId as number);
                    refreshSelectedProfile(nextProfile);
                  })
                }
              >
                {busy === "update-profile" ? "Updating profile" : "Update profile from learning trace"}
              </button>
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
                data-testid="create-path-button"
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
              {busy === "create-path" ? (
                <AgentLoading
                  testId="planner-loading"
                  title="Planner Agent is creating a learning path..."
                  detail="It is matching the selected profile, course graph, and goal into ordered path items."
                />
              ) : null}
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
              <div className="mt-4 grid grid-cols-5 gap-2" data-testid="resource-type-options">
                {resourceOptions.map((option) => (
                  <button
                    key={option.type}
                    className={`resource-tab ${resourceType === option.type ? "resource-tab-active" : ""}`}
                    data-testid={`resource-type-${option.type}`}
                    onClick={() => {
                      setResourceType(option.type);
                      setResource(null);
                    }}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <button
                className="action-button mt-4"
                data-testid="generate-resource-button"
                disabled={!selectedItem || busy !== null}
                onClick={() =>
                  void runTask("generate-resource", async () => {
                    const nextResource = await api.generateResource(selectedItem!.id, resourceType);
                    setResource(nextResource);
                    await appendRun(nextResource.agent_run_id);
                  })
                }
              >
                {busy === "generate-resource" ? "Generating resource" : "Generate selected resource"}
              </button>
              {busy === "generate-resource" ? (
                <AgentLoading
                  testId="resource-loading"
                  title="Resource Agent is generating a grounded asset..."
                  detail="It is retrieving course chunks and formatting the selected resource type."
                />
              ) : null}
              {resource ? (
                <ResourceOutputBlock resource={resource} />
              ) : (
                <EmptyState text="The generated resource will appear here after the backend Resource Agent responds." />
              )}
            </Panel>

            <Panel title="Tutor" kicker="Grounded Q&A">
              <textarea
                className="field min-h-28 resize-none"
                data-testid="tutor-question"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                aria-label="Tutor question"
              />
              <button
                className="action-button mt-3"
                data-testid="ask-tutor-button"
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
              {busy === "ask-tutor" ? (
                <AgentLoading
                  testId="tutor-loading"
                  title="Retrieving grounded context and waiting for Tutor response..."
                  detail="Slow LLM calls will fall back to a rule-based answer with the same source refs."
                />
              ) : null}
              {answer ? (
                <OutputBlock title="Tutor answer" text={answer.answer} sourceRefs={answer.source_refs} />
              ) : (
                <EmptyState text="Tutor answers are grounded by backend document chunks and include returned source refs." />
              )}
            </Panel>
          </div>

          <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
            <Panel title="Quiz attempt" kicker="Quiz Agent">
              <button
                className="action-button"
                data-testid="generate-quiz-button"
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
              {busy === "generate-quiz" ? (
                <AgentLoading
                  testId="quiz-loading"
                  title="Quiz Agent is preparing an assessment item..."
                  detail="It is grounding the question in the selected concept and course chunks."
                />
              ) : null}

              {quiz?.items[0] ? (
                <div className="mt-4 space-y-3">
                  <div className="rounded-md border border-slate-200 bg-white p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-moss">Question</p>
                    <p className="mt-2 text-sm font-semibold leading-6 text-slate-900" data-testid="quiz-question">
                      {quiz.items[0].question}
                    </p>
                    <p className="mt-3 text-xs text-slate-500">{quiz.items[0].concept_tags.join(" / ")}</p>
                  </div>
                  <textarea
                    className="field min-h-28 resize-none"
                    data-testid="quiz-answer"
                    value={attemptText}
                    onChange={(event) => setAttemptText(event.target.value)}
                    aria-label="Quiz answer"
                    placeholder="Type your answer and submit it to the evaluator."
                  />
                  <label className="setting-toggle" data-testid="auto-profile-update-control">
                    <input
                      type="checkbox"
                      data-testid="auto-profile-update-toggle"
                      checked={autoProfileUpdateEnabled}
                      disabled={busy !== null}
                      onChange={(event) => setAutoProfileUpdateEnabled(event.target.checked)}
                    />
                    <span>
                      <strong>Auto-update profile after evaluation</strong>
                      <small>ProfileUpdater syncs the student profile from the latest agent trace when enabled.</small>
                    </span>
                  </label>
                  <button
                    className="primary-button"
                    data-testid="submit-answer-button"
                    disabled={!attemptText.trim() || busy !== null}
                    onClick={() => void submitQuizAttempt()}
                  >
                    {busy === "submit-attempt" ? "Submitting answer" : busy === "sync-profile" ? "Updating profile" : "Submit answer"}
                  </button>
                  {busy === "submit-attempt" ? (
                    <AgentLoading
                      testId="evaluator-loading"
                      title="Evaluator Agent is scoring the attempt..."
                      detail="It is comparing the answer with the quiz rubric and returning feedback."
                    />
                  ) : null}
                  {busy === "sync-profile" ? (
                    <AgentLoading
                      testId="profile-update-loading"
                      title="ProfileUpdater is updating the student profile..."
                      detail="It is analyzing the latest learning trace after evaluation."
                    />
                  ) : null}
                </div>
              ) : (
                <EmptyState text="Generate a quiz after selecting a path node or concept." />
              )}
            </Panel>

            <Panel title="Evaluator feedback" kicker="Mastery">
              {evaluation ? (
                <div className="space-y-4">
                  <Metric label="Score" value={`${Math.round(evaluation.score * 100)}%`} />
                  <p className="rounded-md bg-white p-4 text-sm leading-6 text-slate-700" data-testid="evaluator-feedback">
                    {evaluation.feedback}
                  </p>
                  {autoProfileUpdate ? (
                    <p className="rounded-md bg-moss/10 p-3 text-xs font-semibold leading-5 text-slate-700" data-testid="auto-profile-update">
                      {autoProfileUpdate}
                    </p>
                  ) : null}
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
    <button className={`path-card ${selected ? "path-card-active" : ""}`} data-testid="path-item-card" onClick={onSelect}>
      <span className="text-xs font-semibold uppercase tracking-[0.16em] text-moss">Step {item.order_index}</span>
      <span className="mt-2 block text-left text-base font-semibold text-slate-950">{item.title}</span>
      <span className="mt-2 block text-left text-sm leading-6 text-slate-600">{item.objective}</span>
      <span className="mt-3 block text-left text-xs text-slate-500">{concept?.name ?? `Concept ${item.concept_id}`}</span>
    </button>
  );
}

function NodeSummary({ item, concept }: { item: LearningPathItem | null; concept: Concept | null }) {
  if (!item) return <EmptyState text="Select or create a path node before generating resources." />;

  return (
    <div className="rounded-md border border-slate-200 bg-white p-4" data-testid="current-node">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-moss">Current node</p>
      <p className="mt-2 text-sm font-semibold text-slate-950">{item.title}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{item.objective}</p>
      <p className="mt-3 text-xs text-slate-500">{concept?.name ?? `Concept ${item.concept_id}`}</p>
    </div>
  );
}

function ProfileDimensionList({ profile }: { profile: StudentProfile }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4" data-testid="profile-dimensions">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-moss">6-dimension profile</p>
      <div className="mt-3 grid gap-2">
        {profileDimensions.map(([key, label]) => (
          <div key={key} className="rounded-md bg-slate-50 px-3 py-2">
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-slate-500">{label}</p>
            <p className="mt-1 text-xs leading-5 text-slate-700">{formatPreference(profile, key)}</p>
          </div>
        ))}
      </div>
      {profile.preferences.last_profile_update_reason ? (
        <p className="mt-3 rounded-md bg-signal/10 p-3 text-xs leading-5 text-slate-700" data-testid="profile-update-reason">
          {String(profile.preferences.last_profile_update_reason)}
        </p>
      ) : null}
    </div>
  );
}

function formatPreference(profile: StudentProfile, key: string): string {
  const value = profile.preferences[key];
  if (value === undefined || value === null || value === "") {
    if (key === "learning_goal") return profile.goal;
    if (key === "foundation_level") return profile.level;
    if (key === "available_time") return profile.time_budget;
    return "待学习过程更新";
  }
  return String(value);
}

function RunCard({ run }: { run: AgentRun }) {
  return (
    <article className="run-timeline-card" data-testid="run-card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-950">{run.run_type}</h3>
        <span className="rounded-full bg-moss/15 px-3 py-1 text-xs font-semibold text-moss">{run.status}</span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">{run.final_summary ?? run.output_summary ?? run.input_summary}</p>
      <div className="timeline-steps">
        {run.steps.map((step) => (
          <div key={step.id} className="timeline-step">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              {step.step_order}. {agentTone[step.agent_type] ?? step.agent_type}
            </p>
            <p className="mt-2 text-xs font-semibold text-slate-500">Input</p>
            <p className="text-sm leading-5 text-slate-700">{step.input_summary}</p>
            <p className="mt-2 text-xs font-semibold text-slate-500">Output</p>
            <p className="text-sm leading-5 text-slate-700">{step.output_summary}</p>
            <p className="mt-2 text-xs font-semibold text-slate-500">Decision</p>
            <p className="text-xs leading-5 text-slate-500">{step.decision_basis}</p>
            {step.decision_basis.toLowerCase().includes("fallback") ? (
              <span className="mt-2 inline-flex rounded-full bg-signal/10 px-2 py-1 text-[0.68rem] font-semibold text-signal">
                Fallback
              </span>
            ) : null}
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

function OutputBlock({ title, text, sourceRefs }: { title: string; text: string; sourceRefs: Array<Record<string, unknown>> }) {
  return (
    <article className="mt-4 rounded-md border border-slate-200 bg-white p-4" data-testid="output-block">
      <h3 className="text-sm font-semibold text-slate-950">{title}</h3>
      <MarkdownBlock text={text} />
      <SourcePanel sourceRefs={sourceRefs} />
    </article>
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

function MarkdownBlock({ text }: { text: string }) {
  return (
    <div className="markdown-body" data-testid="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          h1: ({ children }) => <h3>{children}</h3>,
          h2: ({ children }) => <h3>{children}</h3>,
          h3: ({ children }) => <h4>{children}</h4>,
          p: ({ children }) => <p>{children}</p>,
          ul: ({ children }) => <ul>{children}</ul>,
          ol: ({ children }) => <ol>{children}</ol>,
          li: ({ children }) => <li>{children}</li>,
          code: ({ children }) => <code>{children}</code>,
          pre: ({ children }) => <pre>{children}</pre>,
          strong: ({ children }) => <strong>{children}</strong>
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}

function ResourceOutputBlock({ resource }: { resource: GeneratedResource }) {
  const lines = resource.content
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  const title = resource.resource_type;

  if (resource.resource_type === "mind_map") {
    const center = extractMindMapCenter(lines);
    const nodes = extractMindMapNodes(lines);
    return (
      <article className="resource-card resource-card-map" data-testid="output-block">
        <ResourceHeader title="Mind map" />
        <MindMapDiagram center={center} nodes={nodes} />
        <FullResourceText text={resource.content} />
        <SourcePanel sourceRefs={resource.source_refs} />
      </article>
    );
  }

  if (resource.resource_type === "coding_case") {
    const code = extractFencedCode(resource.content);
    const tasks = extractNumberedItems(lines).slice(0, 5);
    return (
      <article className="resource-card resource-card-code" data-testid="output-block">
        <ResourceHeader title="Coding case" />
        {code ? (
          <pre className="code-case-block" data-testid="coding-case-card">{code}</pre>
        ) : (
          <div className="missing-structured-block" data-testid="coding-case-card">模型未返回 Python 代码块，以下保留完整资源正文。</div>
        )}
        <div className="resource-chip-row">
          {tasks.map((task, index) => (
            <span key={index} className="resource-chip">{task}</span>
          ))}
        </div>
        <FullResourceText text={resource.content} />
        <SourcePanel sourceRefs={resource.source_refs} />
      </article>
    );
  }

  if (resource.resource_type === "practice_questions") {
    const questions = extractPracticeQuestions(lines);
    return (
      <article className="resource-card resource-card-practice" data-testid="output-block">
        <ResourceHeader title="Practice questions" />
        <ol className="practice-list" data-testid="practice-card">
          {(questions.length ? questions : extractQuestionLikeLines(lines)).map((line, index) => (
            <li key={index}>{line.replace(/^题目\s*\d+[:：]\s*/, "")}</li>
          ))}
        </ol>
        <FullResourceText text={resource.content} />
        <SourcePanel sourceRefs={resource.source_refs} />
      </article>
    );
  }

  if (resource.resource_type === "extended_reading") {
    return (
      <article className="resource-card resource-card-reading" data-testid="output-block">
        <ResourceHeader title="Extended reading" />
        <div data-testid="reading-card">
          <MarkdownBlock text={resource.content} />
        </div>
        <SourcePanel sourceRefs={resource.source_refs} />
      </article>
    );
  }

  return (
    <article className="resource-card resource-card-note" data-testid="output-block">
      <ResourceHeader title={title} />
      <MarkdownBlock text={resource.content} />
      <SourcePanel sourceRefs={resource.source_refs} />
    </article>
  );
}

function extractMindMapCenter(lines: string[]): string {
  const center = lines.find((line) => line.startsWith("中心主题"));
  return center?.replace(/^中心主题[:：]\s*/, "") || lines.find((line) => !line.startsWith("#")) || "Mind map";
}

function extractMindMapNodes(lines: string[]): string[] {
  const branchNodes = lines
    .filter((line) => line.startsWith("分支"))
    .map((line) => line.replace(/^分支[:：]\s*/, ""));
  if (branchNodes.length) return branchNodes.slice(0, 8);
  return lines
    .filter((line) => line.startsWith("-") || line.startsWith("  -"))
    .map((line) => line.replace(/^-+\s*/, "").replace(/^-\s*/, ""))
    .slice(0, 8);
}

function extractFencedCode(content: string): string {
  const match = content.match(/```(?:python|py)?\s*([\s\S]*?)```/i);
  return match?.[1]?.trim() ?? "";
}

function extractNumberedItems(lines: string[]): string[] {
  return lines.filter((line) => /^\d+[.、]/.test(line)).map((line) => line.replace(/^\d+[.、]\s*/, ""));
}

function extractPracticeQuestions(lines: string[]): string[] {
  const questions = lines
    .filter((line) => /^题目\s*\d+[:：]/.test(line))
    .map((line) => line.replace(/^题目\s*\d+[:：]\s*/, ""));
  if (questions.length) return questions.slice(0, 8);
  return extractNumberedItems(lines);
}

function extractQuestionLikeLines(lines: string[]): string[] {
  const useful = lines.filter((line) => /题|答案|解析|选择|填空|简答|应用/.test(line));
  return useful.length ? useful : lines;
}

function MindMapDiagram({ center, nodes }: { center: string; nodes: string[] }) {
  const safeNodes = nodes.length ? nodes : ["定义", "表示方法", "复杂度", "易错点"];
  const height = Math.max(220, 84 + safeNodes.length * 54);
  const centerY = height / 2;
  return (
    <div className="mind-map-diagram" data-testid="mind-map-card">
      <svg viewBox={`0 0 720 ${height}`} role="img" aria-label="Mind map diagram">
        <rect x="28" y={centerY - 34} width="220" height="68" rx="8" className="mind-map-svg-center" />
        <text x="138" y={centerY - 4} textAnchor="middle" className="mind-map-svg-title">
          {truncateSvgText(center, 14)}
        </text>
        <text x="138" y={centerY + 18} textAnchor="middle" className="mind-map-svg-subtitle">中心主题</text>
        {safeNodes.map((node, index) => {
          const y = 42 + index * 54;
          return (
            <g key={index}>
              <path d={`M 248 ${centerY} C 330 ${centerY}, 315 ${y + 22}, 398 ${y + 22}`} className="mind-map-svg-link" />
              <rect x="398" y={y} width="292" height="44" rx="8" className="mind-map-svg-node" />
              <text x="414" y={y + 27} className="mind-map-svg-node-text">{truncateSvgText(node, 24)}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function truncateSvgText(text: string, maxLength: number): string {
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}...` : text;
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
      <h3 className="text-sm font-semibold text-slate-950">{title}</h3>
    </div>
  );
}

function SourcePanel({ sourceRefs }: { sourceRefs: Array<Record<string, unknown>> }) {
  const visibleSources = sourceRefs.slice(0, 5);
  return (
    <div className="source-panel" data-testid="source-panel">
      <p className="source-panel-title">Grounded sources</p>
      {visibleSources.length === 0 ? (
        <p className="source-panel-empty" data-testid="source-empty">No source returned</p>
      ) : (
        <div className="source-panel-list">
          {visibleSources.map((source, index) => (
            <details className="source-detail" data-testid="source-detail" key={`${String(source.source_ref ?? source.chunk_id ?? "source")}-${index}`}>
              <summary>
                <span>{String(source.source_ref ?? source.chunk_id ?? "source")}</span>
                <small>
                  score {formatScore(source.rerank_score ?? source.score)}
                  {source.retrieval_mode ? ` · ${String(source.retrieval_mode)}` : ""}
                </small>
              </summary>
              {source.source_title ? <p className="source-title">{String(source.source_title)}</p> : null}
              {source.excerpt ? <p className="source-excerpt">{String(source.excerpt)}</p> : null}
              <p className="source-meta">
                matched {formatMetadataList(source.matched_terms)} · anchors {formatMetadataList(source.anchor_matches)}
                {Array.isArray(source.rerank_reasons) && source.rerank_reasons.length
                  ? ` · rerank ${formatMetadataList(source.rerank_reasons)}`
                  : ""}
              </p>
            </details>
          ))}
        </div>
      )}
    </div>
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
