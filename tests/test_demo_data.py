import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_engine, get_session_factory
from app.main import create_app
from app.models import AgentRun, Concept, ConceptRelation, Document, DocumentChunk, LearningPath, StudentProfile
from app.seed.demo_data import DEMO_CHUNKS, DEMO_CONCEPTS, DEMO_PROFILES, DEMO_RELATIONS
from app.services.demo_data_service import DemoDataService
from tests.test_helper import AuthenticatedTestCase


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
        self.assertEqual(loaded.demo_data.chunk_count, len(DEMO_CHUNKS))

        after = service.get_status()
        self.assertTrue(after.is_loaded)
        self.assertEqual(set(after.concept_slugs), {concept["slug"] for concept in DEMO_CONCEPTS})

    def test_load_demo_data_is_idempotent(self) -> None:
        service = DemoDataService(database_url=self.database_url)
        service.load_demo_data()
        service.load_demo_data()

        session = get_session_factory(self.database_url)()
        try:
            self.assertEqual(len(session.scalars(select(Concept)).all()), len(DEMO_CONCEPTS))
            self.assertEqual(len(session.scalars(select(ConceptRelation)).all()), len(DEMO_RELATIONS))
            self.assertEqual(len(session.scalars(select(Document)).all()), 1)
            self.assertEqual(len(session.scalars(select(DocumentChunk)).all()), len(DEMO_CHUNKS))
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

            chunks = session.scalars(select(DocumentChunk)).all()
            self.assertEqual(len(chunks), len(DEMO_CHUNKS))
            for chunk in chunks:
                self.assertIsNotNone(chunk.concept_id)
                self.assertIsNotNone(chunk.source_ref)
                self.assertTrue(chunk.vector_ref.startswith("demo:"))
        finally:
            session.close()


class DemoDataHttpTests(AuthenticatedTestCase):
    def test_demo_data_http_endpoints_use_real_state(self) -> None:
        before = self.client.get("/api/v1/demo-data/status", headers=self.headers)
        self.assertEqual(before.status_code, 200)

        loaded = self.client.post("/api/v1/demo-data/load", headers=self.headers)
        self.assertEqual(loaded.status_code, 200)
        body = loaded.json()
        self.assertEqual(body["status"], "completed")
        self.assertTrue(body["demo_data"]["is_loaded"])
        self.assertEqual(body["demo_data"]["concept_count"], 5)

        after = self.client.get("/api/v1/demo-data/status", headers=self.headers)
        self.assertTrue(after.json()["is_loaded"])

    def test_reset_user_data_keeps_seed_data_and_removes_learning_process_records(self) -> None:
        demo = self.client.post("/api/v1/demo-data/load", headers=self.headers).json()["demo_data"]
        profile = self.client.post(
            "/api/v1/student-profiles/from-dialogue",
            headers=self.headers,
            json={"dialogue": "我想用代码练习链表和 BFS，每周 6 小时。"},
        ).json()
        learning_flow = self.client.post(
            "/api/v1/learning-paths",
            headers=self.headers,
            json={
                "student_profile_id": profile["id"],
                "course_id": demo["course_id"],
                "goal": "练习链表和 BFS",
            },
        ).json()
        path = learning_flow["learning_path"]
        run = learning_flow["agent_run"]

        reset = self.client.post("/api/v1/demo-data/reset-user-data", headers=self.headers)
        self.assertEqual(reset.status_code, 200)
        reset_body = reset.json()
        self.assertEqual(reset_body["status"], "completed")
        self.assertTrue(reset_body["demo_data"]["is_loaded"])

        profiles = self.client.get("/api/v1/student-profiles", headers=self.headers).json()
        self.assertEqual(len(profiles), 3)
        self.assertEqual(
            self.client.get(f"/api/v1/student-profiles/{profile['id']}", headers=self.headers).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(f"/api/v1/learning-paths/{path['id']}", headers=self.headers).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(f"/api/v1/agent-runs/{run['id']}", headers=self.headers).status_code,
            404,
        )
