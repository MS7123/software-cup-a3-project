import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.db.session import get_engine
from app.main import create_app
from app.seed.demo_data import DEMO_CONCEPTS, DEMO_PROFILES, DEMO_RELATIONS


class ProfileCourseApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "api-test.sqlite3"
        self.database_url = f"sqlite:///{self.database_path.as_posix()}"
        os.environ["APP_DATABASE_URL"] = self.database_url

    def tearDown(self) -> None:
        get_engine().dispose()
        get_engine(self.database_url).dispose()
        get_engine.cache_clear()
        os.environ.pop("APP_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def test_student_profile_list_and_detail_return_demo_profiles(self) -> None:
        with TestClient(create_app()) as client:
            response = client.get("/api/v1/student-profiles")
            self.assertEqual(response.status_code, 200)
            profiles = response.json()

            self.assertEqual(len(profiles), len(DEMO_PROFILES))
            self.assertEqual(
                {profile["profile_type"] for profile in profiles},
                {str(profile["profile_type"]) for profile in DEMO_PROFILES},
            )
            for profile in profiles:
                self.assertTrue(profile["goal"])
                self.assertTrue(profile["level"])
                self.assertTrue(profile["preferences"])
                self.assertTrue(profile["time_budget"])

            detail = client.get(f"/api/v1/student-profiles/{profiles[0]['id']}")
            self.assertEqual(detail.status_code, 200)
            self.assertEqual(detail.json()["id"], profiles[0]["id"])

    def test_student_profile_create_returns_created_profile(self) -> None:
        payload = {
            "profile_type": "weak_foundation",
            "goal": "重点复习链表和栈队列",
            "level": "beginner",
            "preferences": {"style": "worked_examples"},
            "time_budget": "每天 45 分钟",
        }
        with TestClient(create_app()) as client:
            response = client.post("/api/v1/student-profiles", json=payload)
            self.assertEqual(response.status_code, 200)
            created = response.json()
            self.assertGreater(created["id"], 0)
            self.assertEqual(created["goal"], payload["goal"])
            self.assertEqual(created["preferences"], payload["preferences"])

    def test_course_graph_returns_demo_course_concepts_and_relations(self) -> None:
        with TestClient(create_app()) as client:
            status_response = client.post("/api/v1/demo-data/load")
            self.assertEqual(status_response.status_code, 200)
            course_id = status_response.json()["demo_data"]["course_id"]

            graph_response = client.get(f"/api/v1/courses/{course_id}/graph")
            self.assertEqual(graph_response.status_code, 200)
            graph = graph_response.json()

            self.assertEqual(graph["course_title"], "数据结构")
            self.assertEqual(len(graph["concepts"]), len(DEMO_CONCEPTS))
            self.assertEqual(len(graph["relations"]), len(DEMO_RELATIONS))
            self.assertEqual(
                {concept["slug"] for concept in graph["concepts"]},
                {concept["slug"] for concept in DEMO_CONCEPTS},
            )
            for concept in graph["concepts"]:
                self.assertIn("chapter", concept)
                self.assertTrue(concept["name"])
                self.assertTrue(concept["difficulty"])

    def test_missing_profile_and_course_return_404(self) -> None:
        with TestClient(create_app()) as client:
            profile_response = client.get("/api/v1/student-profiles/999999")
            self.assertEqual(profile_response.status_code, 404)

            course_response = client.get("/api/v1/courses/999999/graph")
            self.assertEqual(course_response.status_code, 404)
