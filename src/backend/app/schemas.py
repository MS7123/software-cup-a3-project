from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

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
    dialogue: str = Field(min_length=1)
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
    goal: str


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


class TutorAskRequest(BaseModel):
    student_profile_id: int
    course_id: int
    question: str


class TutorAskResponse(BaseModel):
    answer: str
    source_refs: list[dict[str, Any]] = Field(default_factory=list)
    agent_run_id: int | None = None


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


class AttemptSubmitRequest(BaseModel):
    student_profile_id: int
    answers: dict[str, Any]


class EvaluationResult(BaseModel):
    attempt_id: int | None = None
    score: float
    feedback: str
    mastery_updates: list[dict[str, Any]] = Field(default_factory=list)
    agent_run_id: int | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_type: str
    status: ProcessingStatus
    result_ref: str | None = None
    error: str | None = None
    created_at: datetime | None = None


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
