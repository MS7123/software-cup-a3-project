import type {
  AgentRun,
  ConceptGraph,
  DemoDataStatus,
  DocumentIngestionRequest,
  DocumentIngestionResponse,
  EvaluationResult,
  GeneratedResource,
  KnowledgeSearchResponse,
  LearningFlow,
  Quiz,
  StudentProfileDialogueCreate,
  StudentProfile,
  TutorAnswer
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  const text = await response.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

export const api = {
  getDemoStatus: () => request<DemoDataStatus>("/demo-data/status"),
  loadDemoData: () => request<{ demo_data: DemoDataStatus }>("/demo-data/load", { method: "POST" }),
  resetDemoUserData: () => request<{ demo_data: DemoDataStatus }>("/demo-data/reset-user-data", { method: "POST" }),
  listProfiles: () => request<StudentProfile[]>("/student-profiles"),
  getProfile: (profileId: number) => request<StudentProfile>(`/student-profiles/${profileId}`),
  createProfileFromDialogue: (payload: StudentProfileDialogueCreate) =>
    request<StudentProfile>("/student-profiles/from-dialogue", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  updateProfileFromTrace: (profileId: number) =>
    request<StudentProfile>(`/student-profiles/${profileId}/update-from-trace`, { method: "POST" }),
  deleteProfile: async (profileId: number) => {
    await request<void>(`/student-profiles/${profileId}`, { method: "DELETE" });
  },
  getCourseGraph: (courseId: number) => request<ConceptGraph>(`/courses/${courseId}/graph`),
  ingestCourseDocument: (courseId: number, payload: DocumentIngestionRequest) =>
    request<DocumentIngestionResponse>(`/courses/${courseId}/documents`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  searchKnowledge: (courseId: number, query: string, topK = 3) =>
    request<KnowledgeSearchResponse>("/knowledge/search", {
      method: "POST",
      body: JSON.stringify({ course_id: courseId, query, top_k: topK })
    }),
  createLearningPath: (studentProfileId: number, courseId: number, goal: string) =>
    request<LearningFlow>("/learning-paths", {
      method: "POST",
      body: JSON.stringify({ student_profile_id: studentProfileId, course_id: courseId, goal })
    }),
  generateResource: (pathItemId: number, resourceType: string) =>
    request<GeneratedResource>("/resources/generate", {
      method: "POST",
      body: JSON.stringify({ path_item_id: pathItemId, resource_type: resourceType })
    }),
  askTutor: (studentProfileId: number, courseId: number, question: string) =>
    request<TutorAnswer>("/tutor/ask", {
      method: "POST",
      body: JSON.stringify({ student_profile_id: studentProfileId, course_id: courseId, question })
    }),
  generateQuiz: (studentProfileId: number, conceptId: number, difficulty: string) =>
    request<Quiz>("/quizzes/generate", {
      method: "POST",
      body: JSON.stringify({ student_profile_id: studentProfileId, concept_id: conceptId, difficulty })
    }),
  submitAttempt: (quizId: number, studentProfileId: number, answers: Record<string, unknown>) =>
    request<EvaluationResult>(`/quizzes/${quizId}/attempts`, {
      method: "POST",
      body: JSON.stringify({ student_profile_id: studentProfileId, answers })
    }),
  getAgentRun: (runId: number) => request<AgentRun>(`/agent-runs/${runId}`)
};
