from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_user
from app.domain.exceptions import NotFoundError, ProtectedResourceError
from app.models import User
from app.schemas import (
    ConceptGraphResponse,
    AgentRunResponse,
    AttemptSubmitRequest,
    DemoDataLoadResponse,
    DemoDataStatusResponse,
    EvaluationResult,
    GeneratedResourceResponse,
    LearningFlowResponse,
    LearningPathCreate,
    LearningPathResponse,
    QuizGenerateRequest,
    QuizResponse,
    ResourceGenerateRequest,
    StudentProfileCreate,
    StudentProfileDialogueCreate,
    StudentProfileResponse,
    TutorAskRequest,
    TutorAskResponse,
)
from app.agents.orchestrator import AgentOrchestrator
from app.services.agent_run_service import AgentRunService
from app.services.assessment_service import AssessmentService
from app.services.course_service import CourseService
from app.services.demo_data_service import DemoDataService
from app.services.learning_path_service import LearningPathService
from app.services.profile_service import ProfileService
from app.services.profile_updater_service import ProfileUpdaterService
from app.services.resource_service import ResourceService
from app.services.tutor_service import TutorService
from app.api.v1.auth import auth_router

api_router = APIRouter()
api_router.include_router(auth_router)


# ── Demo Data ──────────────────────────────────────────────────────────────


@api_router.get("/demo-data/status", response_model=DemoDataStatusResponse)
def get_demo_data_status(_current_user: User = Depends(get_current_user)) -> DemoDataStatusResponse:
    return DemoDataService().get_status()


@api_router.post("/demo-data/load", response_model=DemoDataLoadResponse)
def load_demo_data(_current_user: User = Depends(get_current_user)) -> DemoDataLoadResponse:
    return DemoDataService().load_demo_data()


@api_router.post("/demo-data/reset-user-data", response_model=DemoDataLoadResponse)
def reset_demo_user_data(current_user: User = Depends(get_current_user)) -> DemoDataLoadResponse:
    return DemoDataService().reset_user_data(current_user.id)


# ── Student Profiles ───────────────────────────────────────────────────────


@api_router.get("/student-profiles", response_model=list[StudentProfileResponse])
def list_student_profiles(current_user: User = Depends(get_current_user)) -> list[StudentProfileResponse]:
    return ProfileService().list_profiles_for_user(current_user.id)


@api_router.post("/student-profiles", response_model=StudentProfileResponse)
def create_student_profile(
    payload: StudentProfileCreate,
    current_user: User = Depends(get_current_user),
) -> StudentProfileResponse:
    return ProfileService().create_profile(payload, current_user.id)


@api_router.post("/student-profiles/from-dialogue", response_model=StudentProfileResponse)
def create_student_profile_from_dialogue(
    payload: StudentProfileDialogueCreate,
    current_user: User = Depends(get_current_user),
) -> StudentProfileResponse:
    return ProfileService().create_profile_from_dialogue(payload, current_user.id)


@api_router.get("/student-profiles/{profile_id}", response_model=StudentProfileResponse)
def get_student_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
) -> StudentProfileResponse:
    try:
        return ProfileService().get_profile(profile_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@api_router.delete("/student-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
) -> None:
    try:
        ProfileService().delete_profile(profile_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProtectedResourceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@api_router.post("/student-profiles/{profile_id}/update-from-trace", response_model=StudentProfileResponse)
def update_student_profile_from_trace(
    profile_id: int,
    current_user: User = Depends(get_current_user),
) -> StudentProfileResponse:
    try:
        return ProfileUpdaterService().update_from_trace(profile_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ── Course / Knowledge Graph ───────────────────────────────────────────────


@api_router.get("/courses/{course_id}/graph", response_model=ConceptGraphResponse)
def get_course_graph(
    course_id: int,
    _current_user: User = Depends(get_current_user),
) -> ConceptGraphResponse:
    try:
        return CourseService().get_concept_graph(course_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ── Learning Path ──────────────────────────────────────────────────────────


@api_router.get("/student-profiles/{profile_id}/learning-paths", response_model=list[LearningPathResponse])
def list_learning_paths(
    profile_id: int,
    current_user: User = Depends(get_current_user),
) -> list[LearningPathResponse]:
    """List all learning paths for a profile (newest first)."""
    try:
        return LearningPathService().list_paths_for_profile(profile_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@api_router.post("/learning-paths", response_model=LearningFlowResponse)
def create_learning_path(
    payload: LearningPathCreate,
    current_user: User = Depends(get_current_user),
) -> LearningFlowResponse:
    try:
        result = AgentOrchestrator().run_learning_flow(
            payload.student_profile_id,
            payload.course_id,
            payload.goal,
            current_user.id,
        )
        return LearningFlowResponse(
            learning_path=LearningPathService().get_path(result.learning_path_id, current_user.id),
            agent_run=AgentRunService().get_run(result.agent_run_id),
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@api_router.get("/learning-paths/{path_id}", response_model=LearningPathResponse)
def get_learning_path(
    path_id: int,
    current_user: User = Depends(get_current_user),
) -> LearningPathResponse:
    try:
        return LearningPathService().get_path(path_id, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@api_router.get("/learning-paths/{path_id}/resources", response_model=list[GeneratedResourceResponse])
def list_path_resources(
    path_id: int,
    current_user: User = Depends(get_current_user),
) -> list[GeneratedResourceResponse]:
    """List generated resources for all items in this learning path."""
    try:
        path = LearningPathService().get_path(path_id, current_user.id)
        resources: list[GeneratedResourceResponse] = []
        for item in path.items:
            item_resources = LearningPathService().list_resources_for_path_item(item.id)
            resources.extend(item_resources)
        return resources
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ── Agent Runs ─────────────────────────────────────────────────────────────


@api_router.get("/agent-runs/{run_id}", response_model=AgentRunResponse)
def get_agent_run(
    run_id: int,
    _current_user: User = Depends(get_current_user),
) -> AgentRunResponse:
    try:
        return AgentRunService().get_run(run_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ── Resource Generation ────────────────────────────────────────────────────


@api_router.post("/resources/generate", response_model=GeneratedResourceResponse)
def generate_resource(
    payload: ResourceGenerateRequest,
    current_user: User = Depends(get_current_user),
) -> GeneratedResourceResponse:
    try:
        return ResourceService().generate_resource(payload.path_item_id, payload.resource_type, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@api_router.get("/resources/path-item/{path_item_id}", response_model=list[GeneratedResourceResponse])
def list_resources_for_path_item(
    path_item_id: int,
    _current_user: User = Depends(get_current_user),
) -> list[GeneratedResourceResponse]:
    """List existing generated resources for a specific path item."""
    return ResourceService().list_resources_for_path_item(path_item_id)


# ── Tutor ──────────────────────────────────────────────────────────────────


@api_router.post("/tutor/ask", response_model=TutorAskResponse)
def ask_tutor(
    payload: TutorAskRequest,
    current_user: User = Depends(get_current_user),
) -> TutorAskResponse:
    try:
        return TutorService().ask(payload.student_profile_id, payload.course_id, payload.question, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ── Quiz & Evaluation ──────────────────────────────────────────────────────


@api_router.get("/quizzes", response_model=list[QuizResponse])
def list_quizzes(
    student_profile_id: int = Query(...),
    concept_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
) -> list[QuizResponse]:
    """List quizzes for a profile, optionally filtered by concept."""
    return AssessmentService().list_quizzes(student_profile_id, concept_id, current_user.id)


@api_router.post("/quizzes/generate", response_model=QuizResponse)
def generate_quiz(
    payload: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
) -> QuizResponse:
    try:
        return AssessmentService().generate_quiz(
            payload.student_profile_id,
            payload.concept_id,
            payload.difficulty,
            current_user.id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@api_router.post("/quizzes/{quiz_id}/attempts", response_model=EvaluationResult)
def submit_quiz_attempt(
    quiz_id: int,
    payload: AttemptSubmitRequest,
    current_user: User = Depends(get_current_user),
) -> EvaluationResult:
    try:
        return AssessmentService().submit_attempt(quiz_id, payload.student_profile_id, payload.answers, current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
