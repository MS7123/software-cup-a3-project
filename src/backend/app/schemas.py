import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import (
    AgentRunStatus,
    AgentType,
    LearningPathItemStatus,
    LearningPathStatus,
    ProcessingStatus,
    ProfileType,
    RelationType,
)


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class StudentProfileBase(BaseModel):
    profile_type: ProfileType
    goal: str
    level: str
    preferences: dict[str, Any] = Field(default_factory=dict)
    time_budget: str


class StudentProfileCreate(StudentProfileBase):
    user_id: int | None = None


class StudentProfileDialogueCreate(BaseModel):
    dialogue: str = Field(min_length=1, max_length=8000)
    profile_type: ProfileType | None = None
    user_id: int | None = None


class StudentProfileResponse(StudentProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    created_at: datetime | None = None


class CourseCreate(BaseModel):
    title: str
    description: str | None = None
    is_demo: bool = False


class CourseResponse(CourseCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime | None = None


class ConceptCreate(BaseModel):
    slug: str
    name: str
    chapter: str | None = None
    description: str | None = None
    difficulty: str


class ConceptResponse(ConceptCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int


class ConceptRelationCreate(BaseModel):
    source_concept_id: int
    target_concept_id: int
    relation_type: RelationType


class ConceptRelationResponse(ConceptRelationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ConceptGraphResponse(BaseModel):
    course_id: int
    course_title: str | None = None
    concepts: list[ConceptResponse]
    relations: list[ConceptRelationResponse]


class DocumentCreate(BaseModel):
    title: str
    source_type: str
    visibility: str = "course"
    owner_user_id: int | None = None


class DocumentIngestionRequest(DocumentCreate):
    content: str = Field(min_length=1)


class DocumentResponse(DocumentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    status: ProcessingStatus
    created_at: datetime | None = None
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    parser_name: str | None = None


class StudentProfileHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    event_key: str
    trigger_type: str
    before_dimensions: dict[str, Any] = Field(default_factory=dict)
    after_dimensions: dict[str, Any] = Field(default_factory=dict)
    changed_dimensions: list[str] = Field(default_factory=list)
    reason: str
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    agent_run_id: int | None = None
    created_at: datetime | None = None


class DocumentManagementResponse(DocumentResponse):
    chunk_count: int = 0


class DocumentChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    concept_id: int | None = None
    content: str
    vector_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_ref: str | None = None


class DocumentIngestionResponse(BaseModel):
    document: DocumentResponse
    chunks: list[DocumentChunkResponse]
    chunk_count: int


class DocumentReindexResponse(BaseModel):
    document_id: int
    indexed: int
    skipped: int
    failed: int
    enabled: bool
    message: str


class KnowledgeSearchRequest(BaseModel):
    course_id: int
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    owner_user_id: int | None = None


class KnowledgeSearchResult(BaseModel):
    chunk_id: int | None = None
    content: str
    score: float | None = None
    source_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchResponse(BaseModel):
    results: list[KnowledgeSearchResult]


class LearningPathCreate(BaseModel):
    student_profile_id: int
    course_id: int
    goal: str = Field(min_length=1, max_length=1000)


class LearningPathItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    path_id: int
    concept_id: int
    order_index: int
    title: str
    objective: str
    rationale: str | None = None
    status: LearningPathItemStatus
    recommended_resource_type: str | None = None
    recommendation_reason: str | None = None
    priority: int | None = None


class LearningPathResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    course_id: int
    goal: str
    rationale: str | None = None
    status: LearningPathStatus
    items: list[LearningPathItemResponse] = Field(default_factory=list)
    created_at: datetime | None = None
    execution_mode: str | None = None
    provider: str | None = None
    model: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None
    planner_duration_ms: int | None = None


class ResourceGenerateRequest(BaseModel):
    path_item_id: int
    resource_type: str


class GeneratedResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    path_item_id: int
    resource_type: str
    content: str
    source_refs: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime | None = None
    agent_run_id: int | None = None
    safety_status: Literal["passed", "blocked", "degraded"] = "passed"
    safety_message: str | None = None
    postprocessing_task_id: int | None = None
    postprocessing_status: Literal["not_requested", "pending", "running", "completed", "failed"] = "not_requested"


class TutorAskRequest(BaseModel):
    student_profile_id: int
    course_id: int
    question: str = Field(min_length=1, max_length=4000)


class TutorAskResponse(BaseModel):
    answer: str
    source_refs: list[dict[str, Any]] = Field(default_factory=list)
    agent_run_id: int | None = None
    safety_status: Literal["passed", "blocked", "degraded"] = "passed"
    safety_message: str | None = None
    postprocessing_task_id: int | None = None
    postprocessing_status: Literal["not_requested", "pending", "running", "completed", "failed"] = "not_requested"


class QuizGenerateRequest(BaseModel):
    student_profile_id: int
    concept_id: int
    difficulty: str


class QuizItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    question: str
    answer: str
    explanation: str
    difficulty: str
    concept_tags: list[str] = Field(default_factory=list)
    question_type: str | None = None
    options: list[str] = Field(default_factory=list)
    source_refs: list[dict[str, Any]] = Field(default_factory=list)


class QuizResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_profile_id: int
    concept_id: int
    difficulty: str
    status: ProcessingStatus
    items: list[QuizItemResponse] = Field(default_factory=list)
    created_at: datetime | None = None
    agent_run_id: int | None = None
    execution_mode: str | None = None
    provider: str | None = None
    model: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None
    quiz_duration_ms: int | None = None
    safety_status: Literal["passed", "blocked", "degraded"] = "passed"
    safety_message: str | None = None


class AttemptSubmitRequest(BaseModel):
    student_profile_id: int
    answers: dict[str, Any] = Field(min_length=1, max_length=20)
    learning_path_id: int | None = Field(default=None, ge=1)
    run_postprocessing: bool = True

    @field_validator("answers")
    @classmethod
    def validate_answer_payload_size(cls, value: dict[str, Any]) -> dict[str, Any]:
        serialized = json.dumps(value, ensure_ascii=False, default=str)
        if len(serialized) > 12000:
            raise ValueError("answers payload exceeds the 12000-character safety limit")
        return value


class EvaluationResult(BaseModel):
    attempt_id: int | None = None
    score: float
    feedback: str
    mastery_updates: list[dict[str, Any]] = Field(default_factory=list)
    agent_run_id: int | None = None
    postprocessing_task_id: int | None = None
    postprocessing_status: Literal["not_requested", "pending", "running", "completed", "failed"] = "not_requested"


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_type: str
    status: ProcessingStatus
    result_ref: str | None = None
    error: str | None = None
    created_at: datetime | None = None


class AgentExecutionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execution_mode: Literal["llm", "rule_based", "rule_based_fallback"] = "rule_based"
    provider: str = "rule_based"
    model: str = ""
    fallback_used: bool = False
    fallback_reason: str | None = None
    source_refs: list[str] = Field(default_factory=list)
    duration_ms: int = Field(default=0, ge=0)


class AgentRunStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_run_id: int
    agent_type: AgentType | str
    step_order: int
    status: AgentRunStatus | str
    input_summary: str
    output_summary: str
    decision_basis: str
    duration_ms: int | None = None
    error: str | None = None
    execution_metadata: AgentExecutionMetadata = Field(default_factory=AgentExecutionMetadata)


class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_type: str
    student_profile_id: int | None = None
    course_id: int | None = None
    status: AgentRunStatus | str
    input_summary: str | None = None
    output_summary: str | None = None
    final_summary: str | None = None
    duration_ms: int | None = None
    error: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    steps: list[AgentRunStepResponse] = Field(default_factory=list)


class LearningFlowResponse(BaseModel):
    learning_path: LearningPathResponse
    agent_run: AgentRunResponse


class DemoDataStatusResponse(BaseModel):
    is_loaded: bool
    course_title: str = "数据结构"
    concept_slugs: list[str] = Field(default_factory=list)
    profile_types: list[ProfileType] = Field(default_factory=list)
    course_id: int | None = None
    concept_count: int = 0
    profile_count: int = 0
    document_count: int = 0
    chunk_count: int = 0


class DemoDataLoadResponse(BaseModel):
    status: ProcessingStatus
    message: str
    demo_data: DemoDataStatusResponse
