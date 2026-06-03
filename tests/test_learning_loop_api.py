import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.db.session import get_engine
from app.main import create_app


class LearningLoopApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "learning-loop-test.sqlite3"
        self.database_url = f"sqlite:///{self.database_path.as_posix()}"
        os.environ["APP_DATABASE_URL"] = self.database_url

    def tearDown(self) -> None:
        get_engine().dispose()
        get_engine(self.database_url).dispose()
        get_engine.cache_clear()
        os.environ.pop("APP_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def test_resource_tutor_quiz_evaluator_minimum_loop_records_agent_steps(self) -> None:
        with TestClient(create_app()) as client:
            demo = client.post("/api/v1/demo-data/load").json()["demo_data"]
            profile = client.get("/api/v1/student-profiles").json()[0]
            graph = client.get(f"/api/v1/courses/{demo['course_id']}/graph").json()

            learning_flow = client.post(
                "/api/v1/learning-paths",
                json={
                    "student_profile_id": profile["id"],
                    "course_id": demo["course_id"],
                    "goal": "准备数据结构小测",
                },
            ).json()
            path_item = learning_flow["learning_path"]["items"][0]

            resource = client.post(
                "/api/v1/resources/generate",
                json={"path_item_id": path_item["id"], "resource_type": "讲义"},
            )
            self.assertEqual(resource.status_code, 200)
            resource_body = resource.json()
            self.assertEqual(resource_body["path_item_id"], path_item["id"])
            self.assertTrue(resource_body["content"])
            self.assertTrue(resource_body["source_refs"])
            self.assertIsNotNone(resource_body["agent_run_id"])

            tutor = client.post(
                "/api/v1/tutor/ask",
                json={
                    "student_profile_id": profile["id"],
                    "course_id": demo["course_id"],
                    "question": "复杂度分析有什么用？",
                },
            )
            self.assertEqual(tutor.status_code, 200)
            tutor_body = tutor.json()
            self.assertTrue(tutor_body["answer"])
            self.assertTrue(tutor_body["source_refs"])
            self.assertIsNotNone(tutor_body["agent_run_id"])

            concept_id = graph["concepts"][0]["id"]
            quiz = client.post(
                "/api/v1/quizzes/generate",
                json={"student_profile_id": profile["id"], "concept_id": concept_id, "difficulty": "basic"},
            )
            self.assertEqual(quiz.status_code, 200)
            quiz_body = quiz.json()
            self.assertEqual(quiz_body["concept_id"], concept_id)
            self.assertEqual(quiz_body["difficulty"], "basic")
            self.assertTrue(quiz_body["items"])
            self.assertTrue(quiz_body["items"][0]["answer"])
            self.assertTrue(quiz_body["items"][0]["explanation"])
            self.assertTrue(quiz_body["items"][0]["concept_tags"])
            self.assertIsNotNone(quiz_body["agent_run_id"])

            attempt = client.post(
                f"/api/v1/quizzes/{quiz_body['id']}/attempts",
                json={"student_profile_id": profile["id"], "answers": {"answer": quiz_body["items"][0]["answer"]}},
            )
            self.assertEqual(attempt.status_code, 200)
            attempt_body = attempt.json()
            self.assertGreaterEqual(attempt_body["score"], 0.0)
            self.assertTrue(attempt_body["feedback"])
            self.assertTrue(attempt_body["mastery_updates"])
            self.assertIsNotNone(attempt_body["agent_run_id"])

            agent_run_ids = [
                resource_body["agent_run_id"],
                tutor_body["agent_run_id"],
                quiz_body["agent_run_id"],
                attempt_body["agent_run_id"],
            ]
            expected_agents = ["resource", "tutor", "quiz", "evaluator"]
            for run_id, expected_agent in zip(agent_run_ids, expected_agents, strict=True):
                run = client.get(f"/api/v1/agent-runs/{run_id}")
                self.assertEqual(run.status_code, 200)
                run_body = run.json()
                self.assertEqual(run_body["status"], "completed")
                self.assertEqual(run_body["steps"][0]["agent_type"], expected_agent)
                self.assertEqual(run_body["steps"][0]["step_order"], 1)
                self.assertTrue(run_body["steps"][0]["input_summary"])
                self.assertTrue(run_body["steps"][0]["output_summary"])
                self.assertTrue(run_body["steps"][0]["decision_basis"])

    def test_loop_endpoints_return_404_for_missing_records(self) -> None:
        with TestClient(create_app()) as client:
            resource = client.post("/api/v1/resources/generate", json={"path_item_id": 999999, "resource_type": "讲义"})
            self.assertEqual(resource.status_code, 404)

            tutor = client.post(
                "/api/v1/tutor/ask",
                json={"student_profile_id": 999999, "course_id": 999999, "question": "x"},
            )
            self.assertEqual(tutor.status_code, 404)

            quiz = client.post(
                "/api/v1/quizzes/generate",
                json={"student_profile_id": 999999, "concept_id": 999999, "difficulty": "basic"},
            )
            self.assertEqual(quiz.status_code, 404)

            attempt = client.post(
                "/api/v1/quizzes/999999/attempts",
                json={"student_profile_id": 999999, "answers": {"answer": "x"}},
            )
            self.assertEqual(attempt.status_code, 404)
