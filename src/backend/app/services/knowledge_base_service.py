import re

from sqlalchemy import select

from app.db.session import session_scope
from app.models import Document, DocumentChunk
from app.schemas import KnowledgeSearchResult


class KnowledgeBaseService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url

    def search(self, course_id: int, query: str, top_k: int) -> list[KnowledgeSearchResult]:
        query_terms = self._query_terms(query)
        if not query_terms:
            return []
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
                matched_terms = self._matched_terms(haystack, query_terms)
                score = self._score_from_matches(matched_terms, query_terms, haystack)
                if score <= 0:
                    continue
                metadata = {
                    **(chunk.metadata_json if isinstance(chunk.metadata_json, dict) else {}),
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.id,
                    "source_ref": chunk.source_ref,
                    "score": score,
                    "retrieval_mode": "keyword",
                    "matched_terms": matched_terms[:12],
                    "term_match_count": len(matched_terms),
                }
                ranked.append(
                    KnowledgeSearchResult(
                        chunk_id=chunk.id,
                        content=chunk.content,
                        score=score,
                        source_ref=chunk.source_ref,
                        metadata=metadata,
                    )
                )
            ranked.sort(key=lambda item: item.score or 0, reverse=True)
            return ranked[:top_k]

    def _query_terms(self, query: str) -> list[str]:
        normalized = query.strip().lower()
        if not normalized:
            return []
        raw_terms = re.findall(r"[\w#:+\-/]+", normalized, flags=re.UNICODE)
        terms: list[str] = []
        for term in raw_terms:
            if len(term) < 2:
                continue
            terms.append(term)
            if re.fullmatch(r"[\u4e00-\u9fff]+", term) and len(term) > 2:
                terms.extend(term[index : index + 2] for index in range(0, len(term) - 1))
        if not terms:
            compact = re.sub(r"\s+", "", normalized)
            if compact:
                terms.append(compact)
                if len(compact) > 2:
                    terms.extend(compact[index : index + 2] for index in range(0, len(compact) - 1))
        return list(dict.fromkeys(terms))

    def _score(self, haystack: str, query_terms: list[str]) -> float:
        matched_terms = self._matched_terms(haystack, query_terms)
        return self._score_from_matches(matched_terms, query_terms, haystack)

    def _matched_terms(self, haystack: str, query_terms: list[str]) -> list[str]:
        return [term for term in query_terms if term in haystack]

    def _score_from_matches(self, matched_terms: list[str], query_terms: list[str], haystack: str) -> float:
        matched = len(matched_terms)
        if matched == 0 or not query_terms:
            return 0.0
        phrase_bonus = 0.5 if " ".join(query_terms) in haystack else 0.0
        coverage = matched / len(query_terms)
        density_bonus = min(0.25, matched * 0.03)
        return round(coverage + phrase_bonus + density_bonus, 4)
