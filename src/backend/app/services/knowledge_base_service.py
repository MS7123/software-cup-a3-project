from app.schemas import KnowledgeSearchResult


class KnowledgeBaseService:
    def search(self, course_id: int, query: str, top_k: int) -> list[KnowledgeSearchResult]:
        raise NotImplementedError
