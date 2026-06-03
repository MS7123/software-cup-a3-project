from typing import Any

from app.schemas import EvaluationResult, QuizResponse


class AssessmentService:
    def generate_quiz(self, profile_id: int, concept_id: int, difficulty: str) -> QuizResponse:
        raise NotImplementedError

    def submit_attempt(
        self,
        quiz_id: int,
        profile_id: int,
        answers: dict[str, Any],
    ) -> EvaluationResult:
        raise NotImplementedError
