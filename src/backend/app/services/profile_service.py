from sqlalchemy import delete, select

from app.db.session import session_scope
from app.domain.exceptions import NotFoundError, ProtectedResourceError
from app.models import (
    AgentRun,
    AgentRunStep,
    Attempt,
    GeneratedResource,
    LearningPath,
    LearningPathItem,
    MasteryRecord,
    Quiz,
    QuizItem,
    StudentProfile,
)
from app.schemas import StudentProfileCreate, StudentProfileDialogueCreate, StudentProfileResponse
from app.services.profile_builder import build_profile_from_dialogue, normalize_profile_dimensions
from app.services.demo_data_service import DemoDataService


class ProfileService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url

    def get_profile(self, profile_id: int) -> StudentProfileResponse:
        DemoDataService(database_url=self.database_url).load_demo_data()
        with session_scope(self.database_url) as session:
            profile = session.get(StudentProfile, profile_id)
            if profile is None:
                raise NotFoundError("Student profile", profile_id)
            return StudentProfileResponse.model_validate(profile)

    def list_demo_profiles(self) -> list[StudentProfileResponse]:
        DemoDataService(database_url=self.database_url).load_demo_data()
        with session_scope(self.database_url) as session:
            profiles = session.scalars(select(StudentProfile).order_by(StudentProfile.id)).all()
            return [StudentProfileResponse.model_validate(profile) for profile in profiles]

    def create_profile(self, payload: StudentProfileCreate) -> StudentProfileResponse:
        DemoDataService(database_url=self.database_url).get_status()
        normalized_payload = normalize_profile_dimensions(payload)
        with session_scope(self.database_url) as session:
            profile = StudentProfile(**normalized_payload.model_dump())
            session.add(profile)
            session.flush()
            return StudentProfileResponse.model_validate(profile)

    def create_profile_from_dialogue(self, payload: StudentProfileDialogueCreate) -> StudentProfileResponse:
        return self.create_profile(build_profile_from_dialogue(payload))

    def delete_profile(self, profile_id: int) -> None:
        DemoDataService(database_url=self.database_url).get_status()
        with session_scope(self.database_url) as session:
            profile = session.get(StudentProfile, profile_id)
            if profile is None:
                raise NotFoundError("Student profile", profile_id)
            preferences = profile.preferences if isinstance(profile.preferences, dict) else {}
            if preferences.get("profile_origin") == "demo":
                raise ProtectedResourceError("Demo student profiles cannot be deleted.")

            path_ids = [
                row[0]
                for row in session.execute(select(LearningPath.id).where(LearningPath.student_profile_id == profile_id)).all()
            ]
            item_ids: list[int] = []
            if path_ids:
                item_ids = [
                    row[0]
                    for row in session.execute(select(LearningPathItem.id).where(LearningPathItem.path_id.in_(path_ids))).all()
                ]
            quiz_ids = [
                row[0]
                for row in session.execute(select(Quiz.id).where(Quiz.student_profile_id == profile_id)).all()
            ]
            run_ids = [
                row[0]
                for row in session.execute(select(AgentRun.id).where(AgentRun.student_profile_id == profile_id)).all()
            ]

            if item_ids:
                session.execute(delete(GeneratedResource).where(GeneratedResource.path_item_id.in_(item_ids)))
            if path_ids:
                session.execute(delete(LearningPathItem).where(LearningPathItem.path_id.in_(path_ids)))
                session.execute(delete(LearningPath).where(LearningPath.id.in_(path_ids)))
            if quiz_ids:
                session.execute(delete(QuizItem).where(QuizItem.quiz_id.in_(quiz_ids)))
                session.execute(delete(Attempt).where(Attempt.quiz_id.in_(quiz_ids)))
                session.execute(delete(Quiz).where(Quiz.id.in_(quiz_ids)))
            session.execute(delete(Attempt).where(Attempt.student_profile_id == profile_id))
            session.execute(delete(MasteryRecord).where(MasteryRecord.student_profile_id == profile_id))
            if run_ids:
                session.execute(delete(AgentRunStep).where(AgentRunStep.agent_run_id.in_(run_ids)))
                session.execute(delete(AgentRun).where(AgentRun.id.in_(run_ids)))
            session.delete(profile)
