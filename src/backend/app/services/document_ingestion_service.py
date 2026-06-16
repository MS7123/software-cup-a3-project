import os

from sqlalchemy import select

from app.adapters.embedding_provider import EmbeddingSettings, build_embedding_provider
from app.adapters.document_parser import build_document_parser
from app.core.enums import ProcessingStatus
from app.db.base import Base
from app.db.session import get_engine, session_scope
from app.domain.exceptions import NotFoundError
from app.models import Course, Document, DocumentChunk
from app.schemas import DocumentChunkResponse, DocumentIngestionRequest, DocumentIngestionResponse, DocumentResponse
from app.services.chunking_service import ChunkingService
from app.services.embedding_index_service import EmbeddingIndexService


class DocumentIngestionService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url
        self.chunker = ChunkingService()

    def ingest(self, course_id: int, payload: DocumentIngestionRequest) -> DocumentIngestionResponse:
        Base.metadata.create_all(get_engine(self.database_url))
        parser = build_document_parser(payload.source_type)
        sections = parser.parse_content(payload.content)
        chunks = self.chunker.chunk(sections)
        if not chunks:
            raise ValueError("Document content produced no chunks.")

        with session_scope(self.database_url) as session:
            course = session.get(Course, course_id)
            if course is None:
                raise NotFoundError("Course", course_id)

            document = Document(
                course_id=course_id,
                title=payload.title.strip(),
                source_type=payload.source_type.strip().lower(),
                status=ProcessingStatus.completed,
            )
            session.add(document)
            session.flush()

            chunk_models: list[DocumentChunk] = []
            for index, chunk in enumerate(chunks):
                source_ref = f"document:{document.id}#chunk:{index}"
                model = DocumentChunk(
                    document_id=document.id,
                    concept_id=None,
                    content=chunk.content,
                    vector_ref=None,
                    metadata_json={
                        "chunk_index": index,
                        "filename": payload.title.strip(),
                        "parser": parser.parser_name,
                        "char_start": chunk.char_start,
                        "char_end": chunk.char_end,
                        "document_id": document.id,
                        "source_ref": source_ref,
                        "retrieval_mode": "keyword",
                    },
                    source_ref=source_ref,
                )
                session.add(model)
                chunk_models.append(model)
            session.flush()

            document_response = DocumentResponse.model_validate(document)
            chunk_responses = [self._chunk_response(chunk) for chunk in chunk_models]

        self._maybe_index_embeddings(course_id)
        return DocumentIngestionResponse(
            document=document_response,
            chunks=chunk_responses,
            chunk_count=len(chunk_responses),
        )

    def list_chunks(self, document_id: int) -> list[DocumentChunkResponse]:
        Base.metadata.create_all(get_engine(self.database_url))
        with session_scope(self.database_url) as session:
            document = session.get(Document, document_id)
            if document is None:
                raise NotFoundError("Document", document_id)
            chunks = session.scalars(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.id)
            ).all()
            return [self._chunk_response(chunk) for chunk in chunks]

    def _chunk_response(self, chunk: DocumentChunk) -> DocumentChunkResponse:
        return DocumentChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            concept_id=chunk.concept_id,
            content=chunk.content,
            vector_ref=chunk.vector_ref,
            metadata=chunk.metadata_json,
            source_ref=chunk.source_ref,
        )

    def _maybe_index_embeddings(self, course_id: int) -> None:
        if os.getenv("RAG_EMBEDDING_ENABLED", "").strip().lower() not in {"1", "true", "yes", "on"}:
            return
        settings = EmbeddingSettings.from_env()
        provider = build_embedding_provider(settings)
        if provider is None:
            return
        EmbeddingIndexService(
            database_url=self.database_url,
            provider=provider,
            provider_name=settings.provider or "configured",
            model=settings.model or "configured",
        ).index_course(course_id)
