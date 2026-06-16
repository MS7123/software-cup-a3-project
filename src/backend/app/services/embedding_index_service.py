import hashlib
import json
from dataclasses import dataclass

from sqlalchemy import select

from app.adapters.protocols import EmbeddingProvider
from app.db.base import Base
from app.db.session import get_engine, session_scope
from app.models import ChunkEmbedding, Document, DocumentChunk


@dataclass(frozen=True)
class EmbeddingIndexResult:
    indexed: int
    skipped: int
    failed: int


class EmbeddingIndexService:
    def __init__(
        self,
        database_url: str | None = None,
        provider: EmbeddingProvider | None = None,
        provider_name: str = "configured",
        model: str = "configured",
    ) -> None:
        self.database_url = database_url
        self.provider = provider
        self.provider_name = provider_name
        self.model = model

    def index_course(self, course_id: int) -> EmbeddingIndexResult:
        if self.provider is None:
            return EmbeddingIndexResult(indexed=0, skipped=0, failed=0)

        Base.metadata.create_all(get_engine(self.database_url))
        indexed = 0
        skipped = 0
        failed = 0

        with session_scope(self.database_url) as session:
            chunks = session.scalars(
                select(DocumentChunk)
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(Document.course_id == course_id)
                .order_by(DocumentChunk.id)
            ).all()

            for chunk in chunks:
                content_hash = self.content_hash(chunk.content)
                existing = session.scalar(
                    select(ChunkEmbedding).where(
                        ChunkEmbedding.chunk_id == chunk.id,
                        ChunkEmbedding.provider == self.provider_name,
                        ChunkEmbedding.model == self.model,
                        ChunkEmbedding.content_hash == content_hash,
                    )
                )
                if existing is not None:
                    skipped += 1
                    continue

                try:
                    result = self.provider.embed(chunk.content)
                except Exception:
                    failed += 1
                    continue

                vector = [float(value) for value in result.vector]
                if not vector:
                    failed += 1
                    continue

                session.add(
                    ChunkEmbedding(
                        chunk_id=chunk.id,
                        provider=str(result.metadata.get("provider") or self.provider_name),
                        model=str(result.metadata.get("model") or self.model),
                        embedding_json=json.dumps(vector),
                        dimension=len(vector),
                        content_hash=content_hash,
                    )
                )
                indexed += 1

        return EmbeddingIndexResult(indexed=indexed, skipped=skipped, failed=failed)

    @staticmethod
    def content_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
