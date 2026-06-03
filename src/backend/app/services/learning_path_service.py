from app.schemas import LearningPathResponse


class LearningPathService:
    def create_path(self, profile_id: int, course_id: int, goal: str) -> LearningPathResponse:
        raise NotImplementedError
