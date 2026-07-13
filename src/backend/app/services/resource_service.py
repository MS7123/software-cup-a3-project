from sqlalchemy import select

from app.agents.critic_agents import RuleBasedCriticAgent
from app.agents.router_agent import RuleBasedRouterAgent
from app.agents.resource_factory import build_resource_agent
from app.db.session import session_scope
from app.domain.exceptions import NotFoundError
from app.models import Concept, GeneratedResource, LearningPath, LearningPathItem, StudentProfile
from app.schemas import GeneratedResourceResponse
from app.services.agent_run_service import AgentRunService
from app.services.citation_service import source_ref_summary
from app.services.demo_data_service import DemoDataService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.profile_updater_service import ProfileUpdaterService


class ResourceService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url
        self.agent = build_resource_agent()
        self.router_agent = RuleBasedRouterAgent()
        self.critic_agent = RuleBasedCriticAgent()

    def generate_resource(self, path_item_id: int, resource_type: str) -> GeneratedResourceResponse:
        DemoDataService(database_url=self.database_url).get_status()

        with session_scope(self.database_url) as session:
            path_item = session.get(LearningPathItem, path_item_id)
            if path_item is None:
                raise NotFoundError("Learning path item", path_item_id)
            path = session.get(LearningPath, path_item.path_id)
            concept = session.get(Concept, path_item.concept_id)
            if path is None:
                raise NotFoundError("Learning path", path_item.path_id)
            if concept is None:
                raise NotFoundError("Concept", path_item.concept_id)

            path_item_id_value = path_item.id
            objective = path_item.objective
            profile_id = path.student_profile_id
            course_id = path.course_id
            concept_name = concept.name
            concept_slug = concept.slug
            profile = session.get(StudentProfile, profile_id)
            profile_preferences = profile.preferences if profile is not None and isinstance(profile.preferences, dict) else {}
            if profile is not None:
                profile_preferences = {
                    **profile_preferences,
                    "foundation_level": profile.level,
                    "learning_goal": profile.goal,
                    "available_time": profile.time_budget,
                    "profile_type": profile.profile_type,
                }
            owner_user_id = profile.user_id if profile is not None else None

        route = self.router_agent.route_resource_generation(resource_type, concept_name, objective, profile_preferences)
        run_service = AgentRunService(database_url=self.database_url)
        run = run_service.start_run(
            "resource_generation",
            profile_id,
            course_id,
            input_summary=route.to_log_summary(),
        )
        run_service.record_step(
            run.id,
            "router",
            input_summary=f"resource_type={resource_type}; concept={concept_name}; objective={objective}",
            output_summary=route.to_log_summary(),
            decision_basis=f"Router Agent only dispatches JSON-style task constraints: {route.constraints}",
            status="completed",
        )

        resource_query = f"{concept_name} {concept_slug} {objective}"
        chunks = KnowledgeBaseService(database_url=self.database_url).search(
            course_id,
            resource_query,
            top_k=5,
            owner_user_id=owner_user_id,
        )
        run_service.record_step(
            run.id,
            "retriever",
            input_summary=f"query={resource_query}; top_k=5",
            output_summary=f"Retriever Agent returned {len(chunks)} chunks for Resource Agent.",
            decision_basis="Only Retriever Agent can call KnowledgeBaseService.search and expose source_refs.",
            status="completed",
        )
        result = self.agent.generate(concept_name, objective, resource_type, chunks, profile_preferences)
        run_service.record_step(
            run.id,
            "resource",
            result.input_summary,
            f"{result.output_summary} {source_ref_summary(result.source_refs)}",
            f"{result.decision_basis} {source_ref_summary(result.source_refs)}",
            "completed",
        )
        critic = self.critic_agent.review_resource(result, resource_type, profile_preferences)
        run_service.record_step(
            run.id,
            "evaluator",
            input_summary=f"review resource_type={resource_type}; source_refs={len(result.source_refs)}",
            output_summary=critic.output_summary,
            decision_basis=critic.decision_basis,
            status="completed" if critic.approved else "failed",
        )
        if not critic.approved:
            revised_objective = f"{objective}\nCritic revision: {critic.revision_instruction}"
            result = self.agent.generate(concept_name, revised_objective, resource_type, chunks, profile_preferences)
            run_service.record_step(
                run.id,
                "resource",
                result.input_summary,
                f"Resource Agent regenerated after Critic feedback. {result.output_summary} {source_ref_summary(result.source_refs)}",
                f"Revision instruction: {critic.revision_instruction}. {result.decision_basis}",
                "completed",
            )
            second_critic = self.critic_agent.review_resource(result, resource_type, profile_preferences)
            run_service.record_step(
                run.id,
                "evaluator",
                input_summary="review regenerated resource",
                output_summary=second_critic.output_summary,
                decision_basis=second_critic.decision_basis,
                status="completed" if second_critic.approved else "failed",
            )

        with session_scope(self.database_url) as session:
            resource = GeneratedResource(
                path_item_id=path_item_id_value,
                resource_type=resource_type,
                content=result.content,
                source_refs=result.source_refs,
            )
            session.add(resource)
            session.flush()
            response = GeneratedResourceResponse.model_validate(resource)

        run_service.complete_run(run.id, f"Multi-agent resource flow generated resource {response.id} for path_item {path_item_id_value}.")
        ProfileUpdaterService(database_url=self.database_url).update_from_trace(
            profile_id, trigger_type="resource", event_key=f"resource:{run.id}"
        )
        response.agent_run_id = run.id
        return response

    def list_resources_for_path_item(self, path_item_id: int) -> list[GeneratedResourceResponse]:
        with session_scope(self.database_url) as session:
            resources = session.scalars(
                select(GeneratedResource).where(GeneratedResource.path_item_id == path_item_id).order_by(GeneratedResource.id)
            ).all()
            return [GeneratedResourceResponse.model_validate(resource) for resource in resources]
