from fastapi import APIRouter, HTTPException, status

from app.domain.exceptions import NotFoundError
from app.schemas import (
    ConceptGraphResponse,
    DemoDataLoadResponse,
    DemoDataStatusResponse,
    StudentProfileCreate,
    StudentProfileResponse,
)
from app.services.course_service import CourseService
from app.services.demo_data_service import DemoDataService
from app.services.profile_service import ProfileService

api_router = APIRouter()


@api_router.get("/demo-data/status", response_model=DemoDataStatusResponse)
def get_demo_data_status() -> DemoDataStatusResponse:
    return DemoDataService().get_status()


@api_router.post("/demo-data/load", response_model=DemoDataLoadResponse)
def load_demo_data() -> DemoDataLoadResponse:
    return DemoDataService().load_demo_data()


@api_router.get("/student-profiles", response_model=list[StudentProfileResponse])
def list_student_profiles() -> list[StudentProfileResponse]:
    return ProfileService().list_demo_profiles()


@api_router.post("/student-profiles", response_model=StudentProfileResponse)
def create_student_profile(payload: StudentProfileCreate) -> StudentProfileResponse:
    return ProfileService().create_profile(payload)


@api_router.get("/student-profiles/{profile_id}", response_model=StudentProfileResponse)
def get_student_profile(profile_id: int) -> StudentProfileResponse:
    try:
        return ProfileService().get_profile(profile_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@api_router.get("/courses/{course_id}/graph", response_model=ConceptGraphResponse)
def get_course_graph(course_id: int) -> ConceptGraphResponse:
    try:
        return CourseService().get_concept_graph(course_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
