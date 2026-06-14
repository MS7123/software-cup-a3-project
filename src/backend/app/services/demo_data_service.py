from sqlalchemy import Select, delete, func, select
from sqlalchemy.orm import Session

from app.core.enums import ProcessingStatus, ProfileType
from app.db.base import Base
from app.db.session import get_engine, session_scope
from app.models import (
    AgentRun,
    AgentRunStep,
    Attempt,
    Concept,
    ConceptRelation,
    Course,
    Document,
    DocumentChunk,
    GeneratedResource,
    LearningPath,
    LearningPathItem,
    MasteryRecord,
    Quiz,
    QuizItem,
    StudentProfile,
)
from app.schemas import DemoDataLoadResponse, DemoDataStatusResponse, StudentProfileCreate
from app.seed.demo_data import (
    DEMO_CHUNKS,
    DEMO_CONCEPTS,
    DEMO_COURSE,
    DEMO_DOCUMENT,
    DEMO_PROFILES,
    DEMO_RELATIONS,
)
from app.services.profile_builder import normalize_profile_dimensions


DEMO_CONCEPT_SLUGS = [
    "complexity-analysis",
    "linked-list",
    "stack-queue",
    "binary-tree-traversal",
    "bfs-dfs",
]

DEMO_PROFILE_TYPES = [
    ProfileType.weak_foundation,
    ProfileType.exam_sprint,
    ProfileType.algorithm_practice,
]


class DemoDataService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url

    def get_status(self) -> DemoDataStatusResponse:
        self._ensure_tables()
        with session_scope(self.database_url) as session:
            return self._build_status(session)

    def load_demo_data(self) -> DemoDataLoadResponse:
        self._ensure_tables()
        with session_scope(self.database_url) as session:
            self._load_course_graph(session)
            self._load_profiles(session)
            self._load_document_chunks(session)
            session.flush()
            status = self._build_status(session)
        return DemoDataLoadResponse(
            status=ProcessingStatus.completed,
            message="Demo data loaded successfully." if status.is_loaded else "Demo data load finished with missing records.",
            demo_data=status,
        )

    def ensure_user_demo_profiles(self, user_id: int) -> None:
        """Create demo profiles for a user if they don't already have them."""
        self._ensure_tables()
        with session_scope(self.database_url) as session:
            self._load_course_graph(session)
            self._load_document_chunks(session)
            self._load_profiles_for_user(session, user_id)
            session.flush()

    def reset_user_data(self, user_id: int | None = None) -> DemoDataLoadResponse:
        self.load_demo_data()
        with session_scope(self.database_url) as session:
            # Find all profiles belonging to this user (or all non-demo profiles)
            if user_id is not None:
                profiles = session.scalars(
                    select(StudentProfile).where(StudentProfile.user_id == user_id).order_by(StudentProfile.id)
                ).all()
            else:
                profiles = session.scalars(
                    select(StudentProfile).order_by(StudentProfile.id)
                ).all()

            profile_ids = [p.id for p in profiles if p.id]

            if profile_ids:
                path_ids = [
                    row[0]
                    for row in session.execute(
                        select(LearningPath.id).where(LearningPath.student_profile_id.in_(profile_ids))
                    ).all()
                ]
                item_ids: list[int] = []
                if path_ids:
                    item_ids = [
                        row[0]
                        for row in session.execute(
                            select(LearningPathItem.id).where(LearningPathItem.path_id.in_(path_ids))
                        ).all()
                    ]
                quiz_ids = [
                    row[0]
                    for row in session.execute(
                        select(Quiz.id).where(Quiz.student_profile_id.in_(profile_ids))
                    ).all()
                ]
                run_ids = [
                    row[0]
                    for row in session.execute(
                        select(AgentRun.id).where(AgentRun.student_profile_id.in_(profile_ids))
                    ).all()
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
                session.execute(delete(Attempt).where(Attempt.student_profile_id.in_(profile_ids)))
                session.execute(delete(MasteryRecord).where(MasteryRecord.student_profile_id.in_(profile_ids)))
                if run_ids:
                    session.execute(delete(AgentRunStep).where(AgentRunStep.agent_run_id.in_(run_ids)))
                    session.execute(delete(AgentRun).where(AgentRun.id.in_(run_ids)))

                # Delete non-demo profiles
                for profile in profiles:
                    prefs = profile.preferences if isinstance(profile.preferences, dict) else {}
                    if prefs.get("profile_origin") != "demo":
                        session.delete(profile)

            session.flush()
            status = self._build_status(session)
        return DemoDataLoadResponse(
            status=ProcessingStatus.completed,
            message="Demo user data reset successfully.",
            demo_data=status,
        )

    def _ensure_tables(self) -> None:
        Base.metadata.create_all(get_engine(self.database_url))

    def _load_course_graph(self, session: Session) -> Course:
        course = session.scalar(
            select(Course).where(Course.title == DEMO_COURSE["title"], Course.is_demo.is_(True))
        )
        if course is None:
            course = Course(**DEMO_COURSE)
            session.add(course)
            session.flush()

        concepts_by_slug: dict[str, Concept] = {}
        for concept_data in DEMO_CONCEPTS:
            concept = session.scalar(
                select(Concept).where(
                    Concept.course_id == course.id,
                    Concept.slug == concept_data["slug"],
                )
            )
            if concept is None:
                concept = Concept(course_id=course.id, **concept_data)
                session.add(concept)
                session.flush()
            concepts_by_slug[concept.slug] = concept

        for source_slug, target_slug, relation_type in DEMO_RELATIONS:
            source = concepts_by_slug[source_slug]
            target = concepts_by_slug[target_slug]
            relation = session.scalar(
                select(ConceptRelation).where(
                    ConceptRelation.source_concept_id == source.id,
                    ConceptRelation.target_concept_id == target.id,
                    ConceptRelation.relation_type == relation_type,
                )
            )
            if relation is None:
                session.add(
                    ConceptRelation(
                        source_concept_id=source.id,
                        target_concept_id=target.id,
                        relation_type=relation_type,
                    )
                )
        return course

    def _load_profiles(self, session: Session) -> None:
        """Load demo profiles without user association (legacy / non-auth mode)."""
        for profile_data in DEMO_PROFILES:
            normalized_profile = normalize_profile_dimensions(StudentProfileCreate(**profile_data))
            existing = self._find_demo_profile(session, profile_data)
            if existing is None:
                session.add(StudentProfile(**normalized_profile.model_dump()))
            else:
                existing.preferences = {
                    **normalized_profile.preferences,
                    **(existing.preferences if isinstance(existing.preferences, dict) else {}),
                }

    def _load_profiles_for_user(self, session: Session, user_id: int) -> None:
        """Load demo profiles and associate them with the given user."""
        for profile_data in DEMO_PROFILES:
            normalized_profile = normalize_profile_dimensions(StudentProfileCreate(**profile_data))
            demo_key = profile_data["preferences"].get("demo_profile_key")
            # Check if this user already has this demo profile
            existing = session.scalar(
                select(StudentProfile).where(
                    StudentProfile.user_id == user_id,
                    StudentProfile.profile_type == profile_data["profile_type"],
                )
            )
            if existing is not None:
                # Update existing demo profile preferences
                existing.preferences = {
                    **normalized_profile.preferences,
                    **(existing.preferences if isinstance(existing.preferences, dict) else {}),
                }
            else:
                profile_dict = normalized_profile.model_dump()
                profile_dict["user_id"] = user_id
                session.add(StudentProfile(**profile_dict))

    def _load_document_chunks(self, session: Session) -> None:
        course = self._get_demo_course(session)
        if course is None:
            course = self._load_course_graph(session)

        document = session.scalar(
            select(Document).where(Document.course_id == course.id, Document.title == DEMO_DOCUMENT["title"])
        )
        if document is None:
            document = Document(course_id=course.id, **DEMO_DOCUMENT)
            session.add(document)
            session.flush()

        concepts_by_slug = {
            concept.slug: concept
            for concept in session.scalars(select(Concept).where(Concept.course_id == course.id)).all()
        }
        for chunk_data in DEMO_CHUNKS:
            concept = concepts_by_slug[chunk_data["concept_slug"]]
            chunk = session.scalar(
                select(DocumentChunk).where(
                    DocumentChunk.document_id == document.id,
                    DocumentChunk.source_ref == chunk_data["source_ref"],
                )
            )
            if chunk is None:
                session.add(
                    DocumentChunk(
                        document_id=document.id,
                        concept_id=concept.id,
                        content=chunk_data["content"],
                        vector_ref=f"demo:{concept.slug}",
                        metadata_json={"course": DEMO_COURSE["title"], "concept_slug": concept.slug},
                        source_ref=chunk_data["source_ref"],
                    )
                )

    def _build_status(self, session: Session) -> DemoDataStatusResponse:
        course = self._get_demo_course(session)
        if course is None:
            return DemoDataStatusResponse(
                is_loaded=False,
                concept_slugs=[],
                profile_types=[],
            )

        concept_slugs = [
            slug
            for slug in session.scalars(
                select(Concept.slug).where(Concept.course_id == course.id).order_by(Concept.id)
            ).all()
        ]
        profile_types = [
            ProfileType(profile_type)
            for profile_type in self._demo_profile_types(session)
        ]
        document_count = self._count(
            session,
            select(func.count()).select_from(Document).where(Document.course_id == course.id),
        )
        chunk_count = self._count(
            session,
            select(func.count())
            .select_from(DocumentChunk)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.course_id == course.id),
        )
        is_loaded = (
            set(DEMO_CONCEPT_SLUGS).issubset(set(concept_slugs))
            and {profile.value for profile in DEMO_PROFILE_TYPES}.issubset({profile.value for profile in profile_types})
            and document_count >= 1
            and chunk_count >= len(DEMO_CHUNKS)
        )
        return DemoDataStatusResponse(
            is_loaded=is_loaded,
            course_id=course.id,
            concept_slugs=concept_slugs,
            profile_types=profile_types,
            concept_count=len(concept_slugs),
            profile_count=len(profile_types),
            document_count=document_count,
            chunk_count=chunk_count,
        )

    def _get_demo_course(self, session: Session) -> Course | None:
        return session.scalar(select(Course).where(Course.title == DEMO_COURSE["title"], Course.is_demo.is_(True)))

    def _find_demo_profile(self, session: Session, profile_data: dict) -> StudentProfile | None:
        expected_key = profile_data["preferences"].get("demo_profile_key")
        profiles = session.scalars(
            select(StudentProfile).where(StudentProfile.profile_type == profile_data["profile_type"]).order_by(StudentProfile.id)
        ).all()
        for profile in profiles:
            preferences = profile.preferences if isinstance(profile.preferences, dict) else {}
            if preferences.get("demo_profile_key") == expected_key:
                return profile
        for profile in profiles:
            preferences = profile.preferences if isinstance(profile.preferences, dict) else {}
            if not preferences.get("profile_origin") and profile.goal == profile_data["goal"]:
                return profile
        return None

    def _demo_profile_types(self, session: Session) -> list[str]:
        profile_types: list[str] = []
        for profile in session.scalars(select(StudentProfile).order_by(StudentProfile.id)).all():
            preferences = profile.preferences if isinstance(profile.preferences, dict) else {}
            if preferences.get("profile_origin") == "demo" and preferences.get("demo_profile_key"):
                profile_types.append(profile.profile_type)
        return profile_types

    def _count(self, session: Session, statement: Select[tuple[int]]) -> int:
        return int(session.scalar(statement) or 0)
