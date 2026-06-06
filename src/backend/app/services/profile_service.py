from sqlalchemy import select

from app.db.session import session_scope
from app.domain.exceptions import NotFoundError
from app.models import StudentProfile
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
