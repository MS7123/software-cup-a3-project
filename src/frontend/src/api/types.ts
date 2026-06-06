export type ProfileType = "weak_foundation" | "exam_sprint" | "algorithm_practice" | string;

export interface DemoDataStatus {
  is_loaded: boolean;
  course_title: string;
  concept_slugs: string[];
  profile_types: ProfileType[];
  course_id: number | null;
  concept_count: number;
  profile_count: number;
  document_count: number;
  chunk_count: number;
}

export interface StudentProfile {
  id: number;
  user_id: number | null;
  profile_type: ProfileType;
  goal: string;
  level: string;
  preferences: Record<string, unknown>;
  time_budget: string;
  created_at: string | null;
}

export interface StudentProfileDialogueCreate {
  dialogue: string;
  profile_type?: ProfileType | null;
  user_id?: number | null;
}

export interface Concept {
  id: number;
  course_id: number;
  slug: string;
  name: string;
  chapter: string | null;
  description: string | null;
  difficulty: string;
}

export interface ConceptRelation {
  id: number;
  source_concept_id: number;
  target_concept_id: number;
  relation_type: string;
}

export interface ConceptGraph {
  course_id: number;
  course_title: string | null;
  concepts: Concept[];
  relations: ConceptRelation[];
}

export interface LearningPathItem {
  id: number;
  path_id: number;
  concept_id: number;
  order_index: number;
  title: string;
  objective: string;
  rationale: string | null;
  status: string;
}

export interface LearningPath {
  id: number;
  student_profile_id: number;
  course_id: number;
  goal: string;
  rationale: string | null;
  status: string;
  items: LearningPathItem[];
  created_at: string | null;
}

export interface AgentRunStep {
  id: number;
  agent_run_id: number;
  agent_type: string;
  step_order: number;
  status: string;
  input_summary: string;
  output_summary: string;
  decision_basis: string;
  duration_ms: number | null;
  error: string | null;
}

export interface AgentRun {
  id: number;
  run_type: string;
  status: string;
  input_summary: string | null;
  output_summary: string | null;
  final_summary: string | null;
  steps: AgentRunStep[];
}

export interface LearningFlow {
  learning_path: LearningPath;
  agent_run: AgentRun;
}

export interface GeneratedResource {
  id: number;
  path_item_id: number;
  resource_type: string;
  content: string;
  source_refs: Array<Record<string, unknown>>;
  agent_run_id: number | null;
}

export interface TutorAnswer {
  answer: string;
  source_refs: Array<Record<string, unknown>>;
  agent_run_id: number | null;
}

export interface QuizItem {
  id: number | null;
  question: string;
  answer: string;
  explanation: string;
  difficulty: string;
  concept_tags: string[];
}

export interface Quiz {
  id: number;
  student_profile_id: number;
  concept_id: number;
  difficulty: string;
  status: string;
  items: QuizItem[];
  agent_run_id: number | null;
}

export interface EvaluationResult {
  attempt_id: number | null;
  score: number;
  feedback: string;
  mastery_updates: Array<Record<string, unknown>>;
  agent_run_id: number | null;
}
