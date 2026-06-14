from sqlalchemy import select, update

from app.db.session import session_scope
from app.domain.exceptions import NotFoundError
from app.models import Concept, Course, LearningPath, LearningPathItem, StudentProfile
from app.schemas import LearningPathItemResponse, LearningPathResponse
from app.services.demo_data_service import DemoDataService


class LearningPathService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url

    def create_path(self, profile_id: int, course_id: int, goal: str) -> LearningPathResponse:
        DemoDataService(database_url=self.database_url).load_demo_data()
        with session_scope(self.database_url) as session:
            profile = session.get(StudentProfile, profile_id)
            if profile is None:
                raise NotFoundError("Student profile", profile_id)
            course = session.get(Course, course_id)
            if course is None:
                raise NotFoundError("Course", course_id)

            # 覆盖语义：将之前活跃的学习路径标记为 completed
            old_active_paths = session.scalars(
                select(LearningPath).where(
                    LearningPath.student_profile_id == profile_id,
                    LearningPath.status == "active",
                )
            ).all()
            for old_path in old_active_paths:
                old_path.status = "completed"

            concepts = session.scalars(
                select(Concept).where(Concept.course_id == course.id).order_by(Concept.id)
            ).all()
            rationale = self._build_rationale(profile, course, goal)
            path = LearningPath(
                student_profile_id=profile.id,
                course_id=course.id,
                goal=goal,
                rationale=rationale,
                status="active",
            )
            session.add(path)
            session.flush()

            items: list[LearningPathItem] = []
            for index, concept in enumerate(concepts, start=1):
                item = LearningPathItem(
                    path_id=path.id,
                    concept_id=concept.id,
                    order_index=index,
                    title=f"阶段 {index}: {concept.name}",
                    objective=f"围绕“{concept.name}”完成概念理解、例题复盘和关键操作掌握。",
                    rationale=f"该步骤关联 {concept.chapter or '数据结构'}，难度为 {concept.difficulty}，用于支撑目标：{goal}",
                    status="pending" if index > 1 else "in_progress",
                )
                session.add(item)
                items.append(item)
            session.flush()
            return self._to_path_response(path, items)

    def get_path(self, path_id: int, user_id: int | None = None) -> LearningPathResponse:
        with session_scope(self.database_url) as session:
            path = session.get(LearningPath, path_id)
            if path is None:
                raise NotFoundError("Learning path", path_id)
            if user_id is not None:
                profile = session.get(StudentProfile, path.student_profile_id)
                if profile is None or (profile.user_id is not None and profile.user_id != user_id):
                    raise NotFoundError("Learning path", path_id)
            items = session.scalars(
                select(LearningPathItem).where(LearningPathItem.path_id == path.id).order_by(LearningPathItem.order_index)
            ).all()
            return self._to_path_response(path, items)

    def list_paths_for_profile(self, profile_id: int, user_id: int | None = None) -> list[LearningPathResponse]:
        """Return all learning paths for a given student profile, newest first."""
        with session_scope(self.database_url) as session:
            profile = session.get(StudentProfile, profile_id)
            if profile is None:
                raise NotFoundError("Student profile", profile_id)
            if user_id is not None and profile.user_id is not None and profile.user_id != user_id:
                raise NotFoundError("Student profile", profile_id)

            paths = session.scalars(
                select(LearningPath)
                .where(LearningPath.student_profile_id == profile_id)
                .order_by(LearningPath.id.desc())
            ).all()

            result = []
            for path in paths:
                items = session.scalars(
                    select(LearningPathItem).where(LearningPathItem.path_id == path.id).order_by(LearningPathItem.order_index)
                ).all()
                result.append(self._to_path_response(path, items))
            return result

    def list_resources_for_path_item(self, path_item_id: int) -> list[dict]:
        """Return generated resources for a specific path item."""
        from app.models import GeneratedResource
        from app.schemas import GeneratedResourceResponse
        with session_scope(self.database_url) as session:
            resources = session.scalars(
                select(GeneratedResource).where(GeneratedResource.path_item_id == path_item_id).order_by(GeneratedResource.id)
            ).all()
            return [GeneratedResourceResponse.model_validate(r).model_dump() for r in resources]

    def _build_rationale(self, profile: StudentProfile, course: Course, goal: str) -> str:
        preference = profile.preferences.get("style", "default") if isinstance(profile.preferences, dict) else "default"
        return (
            f"Planner Agent 根据学生画像 {profile.profile_type}、基础水平 {profile.level}、"
            f"学习偏好 {preference}、可用时间 {profile.time_budget}，结合课程“{course.title}”"
            f"的 MVP 知识点先修顺序，为目标“{goal}”生成阶段化路径。"
        )

    def _to_path_response(self, path: LearningPath, items: list[LearningPathItem]) -> LearningPathResponse:
        return LearningPathResponse(
            id=path.id,
            student_profile_id=path.student_profile_id,
            course_id=path.course_id,
            goal=path.goal,
            rationale=path.rationale,
            status=path.status,
            items=[LearningPathItemResponse.model_validate(item) for item in items],
            created_at=path.created_at,
        )
