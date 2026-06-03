import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_engine, get_session_factory
from app.main import create_app
from app.models import Concept, ConceptRelation, Document, DocumentChunk, StudentProfile
from app.seed.demo_data import DEMO_CHUNKS, DEMO_CONCEPTS, DEMO_PROFILES, DEMO_RELATIONS
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
        self.assertEqual(loaded.demo_data.chunk_count, len(DEMO_CHUNKS))

        after = service.get_status()
        self.assertTrue(after.is_loaded)
        self.assertEqual(set(after.concept_slugs), {concept["slug"] for concept in DEMO_CONCEPTS})
        self.assertEqual(
            {profile.value for profile in after.profile_types},
            {str(profile["profile_type"]) for profile in DEMO_PROFILES},
        )

    def test_load_demo_data_is_idempotent(self) -> None:
        service = DemoDataService(database_url=self.database_url)
        service.load_demo_data()
        service.load_demo_data()

        session = get_session_factory(self.database_url)()
        try:
            self.assertEqual(len(session.scalars(select(Concept)).all()), len(DEMO_CONCEPTS))
            self.assertEqual(len(session.scalars(select(ConceptRelation)).all()), len(DEMO_RELATIONS))
            self.assertEqual(len(session.scalars(select(StudentProfile)).all()), len(DEMO_PROFILES))
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
            self.assertEqual(body["demo_data"]["concept_count"], 5)
            self.assertEqual(body["demo_data"]["profile_count"], 3)
            self.assertGreaterEqual(body["demo_data"]["chunk_count"], 5)

            after = client.get("/api/v1/demo-data/status")
            self.assertTrue(after.json()["is_loaded"])
