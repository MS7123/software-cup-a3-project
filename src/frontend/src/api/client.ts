import type {
  AgentRun,
  ConceptGraph,
  DemoDataStatus,
  EvaluationResult,
  GeneratedResource,
  LearningFlow,
  Quiz,
  StudentProfileDialogueCreate,
  StudentProfile,
  TutorAnswer,
  TokenResponse,
  UserInfo,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

// ── Token management ───────────────────────────────────────────────────────

const TOKEN_KEY = "a3_access_token";
const USER_KEY = "a3_user_info";

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function saveUserInfo(info: { user_id: number; username: string }): void {
  localStorage.setItem(USER_KEY, JSON.stringify(info));
}

function getUserInfo(): { user_id: number; username: string } | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

// ── HTTP helpers ───────────────────────────────────────────────────────────

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> ?? {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (response.status === 401) {
    // Token expired or invalid → force re-login
    clearToken();
    window.location.reload();
    throw new Error("Session expired. Please log in again.");
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }

  const text = await response.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

// ── Auth API ───────────────────────────────────────────────────────────────

export const auth = {
  isAuthenticated: (): boolean => !!getToken(),

  getUserInfo: () => getUserInfo(),

  register: async (username: string, password: string, email?: string): Promise<TokenResponse> => {
    const result = await request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password, email }),
    });
    setToken(result.access_token);
    saveUserInfo(result);
    return result;
  },

  login: async (username: string, password: string): Promise<TokenResponse> => {
    const result = await request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    setToken(result.access_token);
    saveUserInfo(result);
    return result;
  },

  me: () => request<UserInfo>("/auth/me"),

  logout: () => {
    clearToken();
    window.location.reload();
  },

  getHeaders: () => authHeaders(),
};

// ── App API ────────────────────────────────────────────────────────────────

export const api = {
  getDemoStatus: () => request<DemoDataStatus>("/demo-data/status"),
  loadDemoData: () => request<{ demo_data: DemoDataStatus }>("/demo-data/load", { method: "POST" }),
  resetDemoUserData: () => request<{ demo_data: DemoDataStatus }>("/demo-data/reset-user-data", { method: "POST" }),
  listProfiles: () => request<StudentProfile[]>("/student-profiles"),
  getProfile: (profileId: number) => request<StudentProfile>(`/student-profiles/${profileId}`),
  createProfileFromDialogue: (payload: StudentProfileDialogueCreate) =>
    request<StudentProfile>("/student-profiles/from-dialogue", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateProfileFromTrace: (profileId: number) =>
    request<StudentProfile>(`/student-profiles/${profileId}/update-from-trace`, { method: "POST" }),
  deleteProfile: async (profileId: number) => {
    await request<void>(`/student-profiles/${profileId}`, { method: "DELETE" });
  },
  getCourseGraph: (courseId: number) => request<ConceptGraph>(`/courses/${courseId}/graph`),
  createLearningPath: (studentProfileId: number, courseId: number, goal: string) =>
    request<LearningFlow>("/learning-paths", {
      method: "POST",
      body: JSON.stringify({ student_profile_id: studentProfileId, course_id: courseId, goal }),
    }),
  generateResource: (pathItemId: number, resourceType: string) =>
    request<GeneratedResource>("/resources/generate", {
      method: "POST",
      body: JSON.stringify({ path_item_id: pathItemId, resource_type: resourceType }),
    }),
  askTutor: (studentProfileId: number, courseId: number, question: string) =>
    request<TutorAnswer>("/tutor/ask", {
      method: "POST",
      body: JSON.stringify({ student_profile_id: studentProfileId, course_id: courseId, question }),
    }),
  generateQuiz: (studentProfileId: number, conceptId: number, difficulty: string) =>
    request<Quiz>("/quizzes/generate", {
      method: "POST",
      body: JSON.stringify({ student_profile_id: studentProfileId, concept_id: conceptId, difficulty }),
    }),
  submitAttempt: (quizId: number, studentProfileId: number, answers: Record<string, unknown>) =>
    request<EvaluationResult>(`/quizzes/${quizId}/attempts`, {
      method: "POST",
      body: JSON.stringify({ student_profile_id: studentProfileId, answers }),
    }),
  getAgentRun: (runId: number) => request<AgentRun>(`/agent-runs/${runId}`),

  // ── Data persistence (auto-load existing) ─────────────────────────────
  listLearningPaths: (profileId: number) =>
    request<LearningFlow["learning_path"][]>(`/student-profiles/${profileId}/learning-paths`),

  listPathResources: (pathId: number) =>
    request<GeneratedResource[]>(`/learning-paths/${pathId}/resources`),

  listResourcesForPathItem: (pathItemId: number) =>
    request<GeneratedResource[]>(`/resources/path-item/${pathItemId}`),

  listQuizzes: (studentProfileId: number, conceptId?: number) => {
    let path = `/quizzes?student_profile_id=${studentProfileId}`;
    if (conceptId !== undefined) path += `&concept_id=${conceptId}`;
    return request<Quiz[]>(path);
  },
};
