import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_engine, get_session_factory
from app.main import create_app
from app.models import AgentRun, Concept, ConceptRelation, Document, DocumentChunk, LearningPath, StudentProfile
from app.seed.demo_data import DEMO_CHAPTERS, DEMO_CHUNKS, DEMO_CONCEPTS, DEMO_PROFILES, DEMO_RELATIONS
from app.services.demo_data_service import DemoDataService


class DemoDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "demo-test.sqlite3"
        self.database_url = f"sqlite:///{self.database_path.as_posix()}"
        os.environ["APP_DATABASE_URL"] = self.database_url

    def tearDown(self) -> None:
        get_engine().dispose()
        get_engine(self.database_url).dispose()
        get_engine.cache_clear()
        os.environ.pop("APP_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def test_status_reflects_load_state(self) -> None:
        service = DemoDataService(database_url=self.database_url)

        before = service.get_status()
        self.assertFalse(before.is_loaded)
        self.assertEqual(before.concept_count, 0)
        self.assertEqual(before.profile_count, 0)
        self.assertEqual(before.chunk_count, 0)

        loaded = service.load_demo_data()
        self.assertEqual(loaded.status, "completed")
        self.assertTrue(loaded.demo_data.is_loaded)
        self.assertEqual(loaded.demo_data.concept_count, len(DEMO_CONCEPTS))
        self.assertEqual(loaded.demo_data.profile_count, len(DEMO_PROFILES))
        self.assertGreater(loaded.demo_data.chunk_count, len(DEMO_CHUNKS))

        after = service.get_status()
        self.assertTrue(after.is_loaded)
        self.assertEqual(set(after.concept_slugs), {concept["slug"] for concept in DEMO_CONCEPTS})
        self.assertEqual(
            {profile.value for profile in after.profile_types},
            {str(profile["profile_type"]) for profile in DEMO_PROFILES},
        )

    def test_course_corpus_has_teaching_depth_for_every_chapter(self) -> None:
        corpus_dir = Path(__file__).resolve().parents[1] / "data" / "course-corpus" / "data-structures"
        for chapter in DEMO_CHAPTERS:
            content = (corpus_dir / chapter["filename"]).read_text(encoding="utf-8")
            self.assertGreaterEqual(len(content), 1800, chapter["filename"])
            self.assertGreaterEqual(content.count("## "), 6, chapter["filename"])
            self.assertIn("练习题", content, chapter["filename"])
            self.assertIn("参考答案", content, chapter["filename"])

    def test_load_demo_data_is_idempotent(self) -> None:
        service = DemoDataService(database_url=self.database_url)
        service.load_demo_data()
        service.load_demo_data()

        session = get_session_factory(self.database_url)()
        try:
            self.assertEqual(len(session.scalars(select(Concept)).all()), len(DEMO_CONCEPTS))
            self.assertEqual(len(session.scalars(select(ConceptRelation)).all()), len(DEMO_RELATIONS))
            self.assertEqual(len(session.scalars(select(StudentProfile)).all()), len(DEMO_PROFILES))
            self.assertEqual(len(session.scalars(select(Document)).all()), len(DEMO_CHAPTERS) + 1)
            self.assertGreater(len(session.scalars(select(DocumentChunk)).all()), len(DEMO_CHUNKS))
        finally:
            session.close()

    def test_seed_relations_and_chunks_are_linked_to_concepts(self) -> None:
        DemoDataService(database_url=self.database_url).load_demo_data()

        session = get_session_factory(self.database_url)()
        try:
            concepts_by_slug = {
                concept.slug: concept
                for concept in session.scalars(select(Concept)).all()
            }
            for source_slug, target_slug, relation_type in DEMO_RELATIONS:
                relation = session.scalar(
                    select(ConceptRelation).where(
                        ConceptRelation.source_concept_id == concepts_by_slug[source_slug].id,
                        ConceptRelation.target_concept_id == concepts_by_slug[target_slug].id,
                        ConceptRelation.relation_type == relation_type,
                    )
                )
                self.assertIsNotNone(relation)

            legacy_document = session.scalar(select(Document).where(Document.title == "数据结构 MVP 模拟课程资料"))
            chunks = session.scalars(
                select(DocumentChunk).where(DocumentChunk.document_id == legacy_document.id)
            ).all()
            self.assertEqual(len(chunks), len(DEMO_CHUNKS))
            for chunk in chunks:
                self.assertIsNotNone(chunk.concept_id)
                self.assertIsNotNone(chunk.source_ref)
                self.assertTrue(chunk.vector_ref.startswith("demo:"))
        finally:
            session.close()

    def test_demo_data_http_endpoints_use_real_state(self) -> None:
        with TestClient(create_app()) as client:
            before = client.get("/api/v1/demo-data/status")
            self.assertEqual(before.status_code, 200)
            self.assertFalse(before.json()["is_loaded"])

            loaded = client.post("/api/v1/demo-data/load")
            self.assertEqual(loaded.status_code, 200)
            body = loaded.json()
            self.assertEqual(body["status"], "completed")
            self.assertTrue(body["demo_data"]["is_loaded"])
            self.assertEqual(body["demo_data"]["concept_count"], len(DEMO_CONCEPTS))
            self.assertEqual(body["demo_data"]["profile_count"], 3)
            self.assertGreaterEqual(body["demo_data"]["chunk_count"], len(DEMO_CHAPTERS) * 3)

            after = client.get("/api/v1/demo-data/status")
            self.assertTrue(after.json()["is_loaded"])

    def test_reset_user_data_keeps_seed_data_and_removes_learning_process_records(self) -> None:
        with TestClient(create_app()) as client:
            demo = client.post("/api/v1/demo-data/load").json()["demo_data"]
            profile = client.post(
                "/api/v1/student-profiles/from-dialogue",
                json={"dialogue": "我想用代码练习链表和 BFS，每周 6 小时。"},
            ).json()
            learning_flow = client.post(
                "/api/v1/learning-paths",
                json={
                    "student_profile_id": profile["id"],
                    "course_id": demo["course_id"],
                    "goal": "练习链表和 BFS",
                },
            ).json()
            path = learning_flow["learning_path"]
            run = learning_flow["agent_run"]

            reset = client.post("/api/v1/demo-data/reset-user-data")
            self.assertEqual(reset.status_code, 200)
            reset_body = reset.json()
            self.assertEqual(reset_body["status"], "completed")
            self.assertTrue(reset_body["demo_data"]["is_loaded"])
            self.assertEqual(reset_body["demo_data"]["profile_count"], len(DEMO_PROFILES))

            profiles = client.get("/api/v1/student-profiles").json()
            self.assertEqual(len(profiles), len(DEMO_PROFILES))
            self.assertEqual(client.get(f"/api/v1/student-profiles/{profile['id']}").status_code, 404)
            self.assertEqual(client.get(f"/api/v1/learning-paths/{path['id']}").status_code, 404)
            self.assertEqual(client.get(f"/api/v1/agent-runs/{run['id']}").status_code, 404)

            session = get_session_factory(self.database_url)()
            try:
                self.assertEqual(len(session.scalars(select(Concept)).all()), len(DEMO_CONCEPTS))
                self.assertEqual(len(session.scalars(select(StudentProfile)).all()), len(DEMO_PROFILES))
                self.assertGreater(len(session.scalars(select(DocumentChunk)).all()), len(DEMO_CHUNKS))
                self.assertEqual(len(session.scalars(select(LearningPath)).all()), 0)
                self.assertEqual(len(session.scalars(select(AgentRun)).all()), 0)
            finally:
                session.close()
