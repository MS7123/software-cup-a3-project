from typing import Any

from sqlalchemy import select

from app.agents.critic_agents import RuleBasedCriticAgent
from app.agents.evaluator_factory import build_evaluator_agent
from app.agents.router_agent import RuleBasedRouterAgent
from app.agents.rule_based_agents import RuleBasedQuizAgent
from app.db.session import session_scope
from app.domain.exceptions import NotFoundError
from app.models import Attempt, Concept, MasteryRecord, Quiz, QuizItem, StudentProfile
from app.schemas import EvaluationResult, QuizItemResponse, QuizResponse
from app.services.agent_run_service import AgentRunService
from app.services.demo_data_service import DemoDataService
from app.services.knowledge_base_service import KnowledgeBaseService


class AssessmentService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url
        self.quiz_agent = RuleBasedQuizAgent()
        self.evaluator_agent = build_evaluator_agent()
        self.router_agent = RuleBasedRouterAgent()
        self.critic_agent = RuleBasedCriticAgent()

    def generate_quiz(self, profile_id: int, concept_id: int, difficulty: str) -> QuizResponse:
        DemoDataService(database_url=self.database_url).get_status()

        with session_scope(self.database_url) as session:
            profile = session.get(StudentProfile, profile_id)
            concept = session.get(Concept, concept_id)
            if profile is None:
                raise NotFoundError("Student profile", profile_id)
            if concept is None:
                raise NotFoundError("Concept", concept_id)

            profile_id_value = profile.id
            concept_id_value = concept.id
            concept_name = concept.name
            concept_slug = concept.slug
            course_id = concept.course_id
            owner_user_id = profile.user_id
            profile_preferences = profile.preferences if isinstance(profile.preferences, dict) else {}
            profile_preferences = {
                **profile_preferences,
                "foundation_level": profile.level,
                "learning_goal": profile.goal,
                "available_time": profile.time_budget,
                "profile_type": profile.profile_type,
            }

        route = self.router_agent.route_quiz_generation(difficulty, concept_name, profile_preferences)
        effective_difficulty = str(route.constraints.get("effective_difficulty") or difficulty)
        run_service = AgentRunService(database_url=self.database_url)
        run = run_service.start_run(
            "quiz_generation",
            profile_id_value,
            course_id,
            input_summary=route.to_log_summary(),
        )
        run_service.record_step(
            run.id,
            "router",
            input_summary=f"requested_difficulty={difficulty}; concept={concept_name}",
            output_summary=route.to_log_summary(),
            decision_basis=f"Router Agent dispatches quiz task with constraints: {route.constraints}",
            status="completed",
        )
        chunks = KnowledgeBaseService(database_url=self.database_url).search(
            course_id,
            concept_slug,
            top_k=1,
            owner_user_id=owner_user_id,
        )
        run_service.record_step(
            run.id,
            "retriever",
            input_summary=f"query={concept_slug}; top_k=1",
            output_summary=f"Retriever Agent returned {len(chunks)} chunk for Quiz Agent.",
            decision_basis="Only Retriever Agent can call KnowledgeBaseService.search for quiz grounding.",
            status="completed",
        )
        result = self.quiz_agent.generate(concept_name, effective_difficulty, chunks[0] if chunks else None)
        run_service.record_step(
            run.id,
            "quiz",
            result.input_summary,
            result.output_summary,
            result.decision_basis,
            "completed",
        )
        critic = self.critic_agent.review_quiz(result, effective_difficulty, profile_preferences)
        run_service.record_step(
            run.id,
            "evaluator",
            input_summary=f"review quiz difficulty={effective_difficulty}",
            output_summary=critic.output_summary,
            decision_basis=critic.decision_basis,
            status="completed" if critic.approved else "failed",
        )
        if not critic.approved:
            effective_difficulty = "easy"
            result = self.quiz_agent.generate(concept_name, effective_difficulty, chunks[0] if chunks else None)
            run_service.record_step(
                run.id,
                "quiz",
                result.input_summary,
                f"Quiz Agent regenerated after Critic feedback. {result.output_summary}",
                f"Revision instruction: {critic.revision_instruction}. {result.decision_basis}",
                "completed",
            )
            second_critic = self.critic_agent.review_quiz(result, effective_difficulty, profile_preferences)
            run_service.record_step(
                run.id,
                "evaluator",
                input_summary="review regenerated quiz",
                output_summary=second_critic.output_summary,
                decision_basis=second_critic.decision_basis,
                status="completed" if second_critic.approved else "failed",
            )

        with session_scope(self.database_url) as session:
            quiz = Quiz(
                concept_id=concept_id_value,
                student_profile_id=profile_id_value,
                difficulty=effective_difficulty,
                status="completed",
            )
            session.add(quiz)
            session.flush()
            item = QuizItem(
                quiz_id=quiz.id,
                question=result.question,
                answer=result.answer,
                explanation=result.explanation,
                difficulty=effective_difficulty,
                concept_tags=result.concept_tags,
            )
            session.add(item)
            session.flush()
            response = self._to_quiz_response(quiz, [item])

        run_service.complete_run(run.id, f"Multi-agent quiz flow generated quiz {response.id} for concept {concept_id_value}.")
        response.agent_run_id = run.id
        return response

    def submit_attempt(
        self,
        quiz_id: int,
        profile_id: int,
        answers: dict[str, Any],
    ) -> EvaluationResult:
        DemoDataService(database_url=self.database_url).get_status()

        with session_scope(self.database_url) as session:
            quiz = session.get(Quiz, quiz_id)
            profile = session.get(StudentProfile, profile_id)
            if quiz is None:
                raise NotFoundError("Quiz", quiz_id)
            if profile is None:
                raise NotFoundError("Student profile", profile_id)
            item = session.scalar(select(QuizItem).where(QuizItem.quiz_id == quiz.id).order_by(QuizItem.id))
            if item is None:
                raise NotFoundError("Quiz item", quiz_id)
            concept = session.get(Concept, quiz.concept_id)
            if concept is None:
                raise NotFoundError("Concept", quiz.concept_id)

            quiz_id_value = quiz.id
            profile_id_value = profile.id
            expected_answer = item.answer
            concept_id_value = concept.id
            course_id = concept.course_id

        result = self.evaluator_agent.evaluate(expected_answer, answers, concept_id_value)

        with session_scope(self.database_url) as session:
            attempt = Attempt(
                quiz_id=quiz_id_value,
                student_profile_id=profile_id_value,
                answers=answers,
                score=result.score,
                feedback=result.feedback,
            )
            session.add(attempt)
            session.flush()
            attempt_id = attempt.id
            for update in result.mastery_updates:
                session.add(
                    MasteryRecord(
                        student_profile_id=profile_id_value,
                        concept_id=update["concept_id"],
                        mastery_score=update["mastery_score"],
                        evidence=update["evidence"],
                    )
                )

        run_service = AgentRunService(database_url=self.database_url)
        run = run_service.start_run(
            "attempt_evaluation",
            profile_id_value,
            course_id,
            input_summary=result.input_summary,
        )
        run_service.record_step(
            run.id,
            "evaluator",
            result.input_summary,
            result.output_summary,
            result.decision_basis,
            "completed",
        )
        run_service.complete_run(run.id, f"Evaluator Agent evaluated attempt {attempt_id}.")
        return EvaluationResult(
            attempt_id=attempt_id,
            score=result.score,
            feedback=result.feedback,
            mastery_updates=result.mastery_updates,
            agent_run_id=run.id,
        )

    def _to_quiz_response(self, quiz: Quiz, items: list[QuizItem], agent_run_id: int | None = None) -> QuizResponse:
        return QuizResponse(
            id=quiz.id,
            student_profile_id=quiz.student_profile_id,
            concept_id=quiz.concept_id,
            difficulty=quiz.difficulty,
            status=quiz.status,
            items=[QuizItemResponse.model_validate(item) for item in items],
            created_at=quiz.created_at,
            agent_run_id=agent_run_id,
        )
