from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.enums import ProcessingStatus, ProfileType
from app.db.base import Base
from app.db.session import get_engine, session_scope
from app.models import Concept, ConceptRelation, Course, Document, DocumentChunk, StudentProfile
from app.schemas import DemoDataLoadResponse, DemoDataStatusResponse
from app.seed.demo_data import (
    DEMO_CHUNKS,
    DEMO_CONCEPTS,
    DEMO_COURSE,
    DEMO_DOCUMENT,
    DEMO_PROFILES,
    DEMO_RELATIONS,
)


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
        for profile_data in DEMO_PROFILES:
            profile = session.scalar(
                select(StudentProfile).where(StudentProfile.profile_type == profile_data["profile_type"])
            )
            if profile is None:
                session.add(StudentProfile(**profile_data))

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
            for profile_type in session.scalars(select(StudentProfile.profile_type).order_by(StudentProfile.id)).all()
            if profile_type in {profile.value for profile in DEMO_PROFILE_TYPES}
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

    def _count(self, session: Session, statement: Select[tuple[int]]) -> int:
        return int(session.scalar(statement) or 0)
