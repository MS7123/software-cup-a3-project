from sqlalchemy import select

from app.agents.resource_factory import build_resource_agent
from app.db.session import session_scope
from app.domain.exceptions import NotFoundError
from app.models import Concept, GeneratedResource, LearningPath, LearningPathItem, StudentProfile
from app.schemas import GeneratedResourceResponse
from app.services.agent_run_service import AgentRunService
from app.services.citation_service import source_ref_summary
from app.services.demo_data_service import DemoDataService
from app.services.knowledge_base_service import KnowledgeBaseService


class ResourceService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url
        self.agent = build_resource_agent()

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
            owner_user_id = profile.user_id if profile is not None else None

        resource_query = f"{concept_name} {concept_slug} {objective}"
        chunks = KnowledgeBaseService(database_url=self.database_url).search(
            course_id,
            resource_query,
            top_k=5,
            owner_user_id=owner_user_id,
        )
        result = self.agent.generate(concept_name, objective, resource_type, chunks, profile_preferences)

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

        run_service = AgentRunService(database_url=self.database_url)
        run = run_service.start_run(
            "resource_generation",
            profile_id,
            course_id,
            input_summary=result.input_summary,
        )
        run_service.record_step(
            run.id,
            "resource",
            result.input_summary,
            f"{result.output_summary} {source_ref_summary(result.source_refs)}",
            f"{result.decision_basis} {source_ref_summary(result.source_refs)}",
            "completed",
        )
        run_service.complete_run(run.id, f"Resource Agent generated resource {response.id} for path_item {path_item_id_value}.")
        response.agent_run_id = run.id
        return response

    def list_resources_for_path_item(self, path_item_id: int) -> list[GeneratedResourceResponse]:
        with session_scope(self.database_url) as session:
            resources = session.scalars(
                select(GeneratedResource).where(GeneratedResource.path_item_id == path_item_id).order_by(GeneratedResource.id)
            ).all()
            return [GeneratedResourceResponse.model_validate(resource) for resource in resources]
