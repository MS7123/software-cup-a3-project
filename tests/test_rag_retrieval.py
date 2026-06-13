import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.main import create_app
from app.models import Concept, Course, Document, LearningPath, LearningPathItem, StudentProfile


class RagRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "rag-retrieval.sqlite3"
        self.database_url = f"sqlite:///{self.database_path.as_posix()}"
        os.environ["APP_DATABASE_URL"] = self.database_url
        Base.metadata.create_all(get_engine(self.database_url))
        self.course_id, self.profile_id, self.path_item_id = self._seed_minimum_learning_records()

    def tearDown(self) -> None:
        get_engine().dispose()
        get_engine(self.database_url).dispose()
        get_engine.cache_clear()
        os.environ.pop("APP_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def test_knowledge_search_hits_imported_document_without_demo_seed(self) -> None:
        with TestClient(create_app()) as client:
            document = self._ingest_bfs_document(client)
            search = client.post(
                "/api/v1/knowledge/search",
                json={"course_id": self.course_id, "query": "BFS 最短路径 queue", "top_k": 3},
            )
            self.assertEqual(search.status_code, 200)
            results = search.json()["results"]
            self.assertTrue(results)
            self.assertEqual(results[0]["source_ref"], f"document:{document['id']}#chunk:0")
            self.assertEqual(results[0]["metadata"]["retrieval_mode"], "keyword")

            session = get_session_factory(self.database_url)()
            try:
                demo_documents = session.scalars(select(Document).where(Document.source_type == "demo")).all()
                self.assertEqual(demo_documents, [])
            finally:
                session.close()

    def test_tutor_and_resource_preserve_real_document_source_refs(self) -> None:
        with TestClient(create_app()) as client:
            document = self._ingest_bfs_document(client)
            expected_source_ref = f"document:{document['id']}#chunk:0"

            tutor = client.post(
                "/api/v1/tutor/ask",
                json={
                    "student_profile_id": self.profile_id,
                    "course_id": self.course_id,
                    "question": "BFS 为什么适合无权图最短路径？",
                },
            )
            self.assertEqual(tutor.status_code, 200)
            tutor_body = tutor.json()
            self.assertTrue(tutor_body["answer"])
            self.assertEqual(tutor_body["source_refs"][0]["source_ref"], expected_source_ref)

            resource = client.post(
                "/api/v1/resources/generate",
                json={"path_item_id": self.path_item_id, "resource_type": "guided_note"},
            )
            self.assertEqual(resource.status_code, 200)
            resource_body = resource.json()
            self.assertTrue(resource_body["content"])
            self.assertEqual(resource_body["source_refs"][0]["source_ref"], expected_source_ref)

    def test_search_returns_empty_results_without_matching_chunks_or_demo_seed(self) -> None:
        with TestClient(create_app()) as client:
            search = client.post(
                "/api/v1/knowledge/search",
                json={"course_id": self.course_id, "query": "AVL rotation", "top_k": 3},
            )
            self.assertEqual(search.status_code, 200)
            self.assertEqual(search.json()["results"], [])

    def _ingest_bfs_document(self, client: TestClient) -> dict:
        response = client.post(
            f"/api/v1/courses/{self.course_id}/documents",
            json={
                "title": "bfs-real-note.md",
                "source_type": "markdown",
                "content": (
                    "# bfs-dfs\n"
                    "BFS 使用 queue 按层扩展，适合无权图最短路径。"
                    "bfs-dfs 是当前学习路径节点的概念 slug。"
                ),
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["document"]

    def _seed_minimum_learning_records(self) -> tuple[int, int, int]:
        session = get_session_factory(self.database_url)()
        try:
            course = Course(title="Real RAG Course", description="真实 RAG 测试课程", is_demo=False)
            session.add(course)
            session.flush()

            concept = Concept(
                course_id=course.id,
                slug="bfs-dfs",
                name="BFS 与 DFS",
                chapter="Graph",
                description="图遍历",
                difficulty="basic",
            )
            session.add(concept)
            profile = StudentProfile(
                profile_type="weak_foundation",
                goal="掌握 BFS",
                level="beginner",
                preferences={"learning_preference": "step_by_step"},
                time_budget="每天 1 小时",
            )
            session.add(profile)
            session.flush()

            path = LearningPath(
                student_profile_id=profile.id,
                course_id=course.id,
                goal="学习 BFS",
                rationale="test",
                status="active",
            )
            session.add(path)
            session.flush()

            item = LearningPathItem(
                path_id=path.id,
                concept_id=concept.id,
                order_index=1,
                title="BFS",
                objective="理解 BFS 与无权图最短路径",
                rationale="test",
                status="pending",
            )
            session.add(item)
            session.commit()
            return course.id, profile.id, item.id
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
