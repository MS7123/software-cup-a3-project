from app.agents.tutor_factory import build_tutor_agent
from app.domain.exceptions import NotFoundError
from app.models import Course, StudentProfile
from app.db.session import session_scope
from app.schemas import TutorAskResponse
from app.services.agent_run_service import AgentRunService
from app.services.knowledge_base_service import KnowledgeBaseService


class TutorService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url
        self.agent = build_tutor_agent()

    def ask(self, profile_id: int, course_id: int, question: str) -> TutorAskResponse:
        with session_scope(self.database_url) as session:
            profile = session.get(StudentProfile, profile_id)
            course = session.get(Course, course_id)
            if profile is None:
                raise NotFoundError("Student profile", profile_id)
            if course is None:
                raise NotFoundError("Course", course_id)

        chunks = KnowledgeBaseService(database_url=self.database_url).search(course_id, question, top_k=2)
        profile_summary = f"type={profile.profile_type}; level={profile.level}; goal={profile.goal}; time_budget={profile.time_budget}"
        result = self.agent.answer(question, chunks, profile_summary, course.title)
        run_service = AgentRunService(database_url=self.database_url)
        run = run_service.start_run("tutor_answer", profile_id, course_id, input_summary=result.input_summary)
        run_service.record_step(
            run.id,
            "tutor",
            result.input_summary,
            result.output_summary,
            result.decision_basis,
            "completed",
        )
        run_service.complete_run(run.id, f"Tutor Agent 已回答 profile {profile_id} 的问题。")
        return TutorAskResponse(answer=result.answer, source_refs=result.source_refs, agent_run_id=run.id)
