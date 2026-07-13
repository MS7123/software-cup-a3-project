from sqlalchemy import select

from app.db.session import session_scope
from app.domain.exceptions import ConflictError, NotFoundError
from app.models import Concept, Course, LearningPath, LearningPathItem, StudentProfile
from app.schemas import LearningPathItemResponse, LearningPathResponse
from app.services.demo_data_service import DemoDataService
from app.services.profile_updater_service import ProfileUpdaterService


class LearningPathService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url

    def validate_inputs(self, profile_id: int, course_id: int) -> None:
        DemoDataService(database_url=self.database_url).load_demo_data()
        with session_scope(self.database_url) as session:
            self._get_profile_and_course(session, profile_id, course_id)

    def create_path(self, profile_id: int, course_id: int, goal: str) -> LearningPathResponse:
        DemoDataService(database_url=self.database_url).load_demo_data()
        with session_scope(self.database_url) as session:
            profile, course = self._get_profile_and_course(session, profile_id, course_id)
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

    @staticmethod
    def _get_profile_and_course(session, profile_id: int, course_id: int) -> tuple[StudentProfile, Course]:
        profile = session.get(StudentProfile, profile_id)
        if profile is None:
            raise NotFoundError("Student profile", profile_id)
        course = session.get(Course, course_id)
        if course is None:
            raise NotFoundError("Course", course_id)
        return profile, course

    def get_path(self, path_id: int) -> LearningPathResponse:
        with session_scope(self.database_url) as session:
            path = session.get(LearningPath, path_id)
            if path is None:
                raise NotFoundError("Learning path", path_id)
            items = session.scalars(
                select(LearningPathItem).where(LearningPathItem.path_id == path.id).order_by(LearningPathItem.order_index)
            ).all()
            return self._to_path_response(path, items)

    def complete_item(self, item_id: int) -> LearningPathResponse:
        with session_scope(self.database_url) as session:
            item = session.get(LearningPathItem, item_id)
            if item is None:
                raise NotFoundError("Learning path item", item_id)
            if item.status == "completed":
                raise ConflictError(f"Learning path item {item_id} is already completed.")
            path = session.get(LearningPath, item.path_id)
            if path is None:
                raise NotFoundError("Learning path", item.path_id)
            item.status = "completed"
            next_item = session.scalar(
                select(LearningPathItem).where(
                    LearningPathItem.path_id == path.id,
                    LearningPathItem.status == "pending",
                    LearningPathItem.order_index > item.order_index,
                ).order_by(LearningPathItem.order_index)
            )
            if next_item is not None:
                next_item.status = "in_progress"
                path.status = "active"
            else:
                path.status = "completed"
            session.flush()
            items = session.scalars(
                select(LearningPathItem).where(LearningPathItem.path_id == path.id).order_by(LearningPathItem.order_index)
            ).all()
            response = self._to_path_response(path, items)
            profile_id = path.student_profile_id

        ProfileUpdaterService(database_url=self.database_url).update_from_trace(
            profile_id, trigger_type="path_item_completed", event_key=f"path_item:{item_id}:completed"
        )
        return response

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
