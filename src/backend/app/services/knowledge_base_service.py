from sqlalchemy import select

from app.db.session import session_scope
from app.models import Document, DocumentChunk
from app.schemas import KnowledgeSearchResult
from app.services.demo_data_service import DemoDataService


class KnowledgeBaseService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url

    def search(self, course_id: int, query: str, top_k: int) -> list[KnowledgeSearchResult]:
        DemoDataService(database_url=self.database_url).load_demo_data()
        normalized_query = query.lower()
        with session_scope(self.database_url) as session:
            chunks = session.scalars(
                select(DocumentChunk)
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(Document.course_id == course_id)
                .order_by(DocumentChunk.id)
            ).all()
            ranked: list[KnowledgeSearchResult] = []
            for chunk in chunks:
                haystack = f"{chunk.content} {chunk.source_ref or ''} {chunk.metadata_json}".lower()
                score = 1.0 if normalized_query and normalized_query in haystack else 0.5
                ranked.append(
                    KnowledgeSearchResult(
                        chunk_id=chunk.id,
                        content=chunk.content,
                        score=score,
                        source_ref=chunk.source_ref,
                        metadata=chunk.metadata_json,
                    )
                )
            ranked.sort(key=lambda item: item.score or 0, reverse=True)
            return ranked[:top_k]
