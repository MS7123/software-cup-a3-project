import os
import unittest

from app.db.session import get_engine
from tests.test_helper import AuthenticatedTestCase


RESOURCE_TYPES = [
    "guided_note",
    "practice_questions",
    "mind_map",
    "extended_reading",
    "coding_case",
]


class LearningLoopApiTests(AuthenticatedTestCase):
    def test_resource_tutor_quiz_evaluator_minimum_loop_records_agent_steps(self) -> None:
        demo = self.client.post("/api/v1/demo-data/load", headers=self.headers).json()["demo_data"]
        profiles = self.client.get("/api/v1/student-profiles", headers=self.headers).json()
        profile = profiles[0]
        graph = self.client.get(f"/api/v1/courses/{demo['course_id']}/graph", headers=self.headers).json()

        learning_flow = self.client.post(
            "/api/v1/learning-paths",
            headers=self.headers,
            json={
                "student_profile_id": profile["id"],
                "course_id": demo["course_id"],
                "goal": "准备数据结构小测",
            },
        ).json()
        path_item = learning_flow["learning_path"]["items"][0]

        resource = self.client.post(
            "/api/v1/resources/generate",
            headers=self.headers,
            json={"path_item_id": path_item["id"], "resource_type": "guided_note"},
        )
        self.assertEqual(resource.status_code, 200)
        resource_body = resource.json()
        self.assertEqual(resource_body["path_item_id"], path_item["id"])
        self.assertTrue(resource_body["content"])
        self.assertTrue(resource_body["source_refs"])
        self.assertIsNotNone(resource_body["agent_run_id"])

        tutor = self.client.post(
            "/api/v1/tutor/ask",
            headers=self.headers,
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
        quiz = self.client.post(
            "/api/v1/quizzes/generate",
            headers=self.headers,
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

        attempt = self.client.post(
            f"/api/v1/quizzes/{quiz_body['id']}/attempts",
            headers=self.headers,
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
            run = self.client.get(f"/api/v1/agent-runs/{run_id}", headers=self.headers)
            self.assertEqual(run.status_code, 200)
            run_body = run.json()
            self.assertEqual(run_body["status"], "completed")
            self.assertEqual(run_body["steps"][0]["agent_type"], expected_agent)
            self.assertEqual(run_body["steps"][0]["step_order"], 1)
            self.assertTrue(run_body["steps"][0]["input_summary"])
            self.assertTrue(run_body["steps"][0]["output_summary"])
            self.assertTrue(run_body["steps"][0]["decision_basis"])

        profile_update = self.client.post(
            f"/api/v1/student-profiles/{profile['id']}/update-from-trace",
            headers=self.headers,
        )
        self.assertEqual(profile_update.status_code, 200)
        updated_profile = profile_update.json()
        preferences = updated_profile["preferences"]
        self.assertIn("last_profile_update_reason", preferences)
        self.assertIn("last_profile_update_sources", preferences)
        self.assertTrue(preferences["last_profile_update_sources"])
        self.assertIn("Agent step", preferences["last_profile_update_reason"])

    def test_resource_agent_generates_five_competition_resource_types(self) -> None:
        demo = self.client.post("/api/v1/demo-data/load", headers=self.headers).json()["demo_data"]
        profiles = self.client.get("/api/v1/student-profiles", headers=self.headers).json()
        profile = profiles[0]
        learning_flow = self.client.post(
            "/api/v1/learning-paths",
            headers=self.headers,
            json={
                "student_profile_id": profile["id"],
                "course_id": demo["course_id"],
                "goal": "准备数据结构小测",
            },
        ).json()
        path_item = learning_flow["learning_path"]["items"][0]

        for resource_type in RESOURCE_TYPES:
            response = self.client.post(
                "/api/v1/resources/generate",
                headers=self.headers,
                json={"path_item_id": path_item["id"], "resource_type": resource_type},
            )
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(body["path_item_id"], path_item["id"])
            self.assertEqual(body["resource_type"], resource_type)
            self.assertTrue(body["source_refs"])
            self.assertIsNotNone(body["agent_run_id"])

    def test_deleting_user_profile_removes_related_learning_records_and_runs(self) -> None:
        demo = self.client.post("/api/v1/demo-data/load", headers=self.headers).json()["demo_data"]
        profile = self.client.post(
            "/api/v1/student-profiles/from-dialogue",
            headers=self.headers,
            json={"dialogue": "我想用代码练习链表和 BFS，每周 6 小时。"},
        ).json()
        graph = self.client.get(f"/api/v1/courses/{demo['course_id']}/graph", headers=self.headers).json()
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
        planner_run_id = learning_flow["agent_run"]["id"]
        path_item = path["items"][0]

        resource = self.client.post(
            "/api/v1/resources/generate",
            headers=self.headers,
            json={"path_item_id": path_item["id"], "resource_type": "coding_case"},
        ).json()
        quiz = self.client.post(
            "/api/v1/quizzes/generate",
            headers=self.headers,
            json={"student_profile_id": profile["id"], "concept_id": graph["concepts"][0]["id"], "difficulty": "basic"},
        ).json()
        attempt = self.client.post(
            f"/api/v1/quizzes/{quiz['id']}/attempts",
            headers=self.headers,
            json={"student_profile_id": profile["id"], "answers": {"answer": quiz["items"][0]["answer"]}},
        ).json()

        delete_response = self.client.delete(f"/api/v1/student-profiles/{profile['id']}", headers=self.headers)
        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(
            self.client.get(f"/api/v1/student-profiles/{profile['id']}", headers=self.headers).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(f"/api/v1/learning-paths/{path['id']}", headers=self.headers).status_code,
            404,
        )
        for run_id in [planner_run_id, resource["agent_run_id"], quiz["agent_run_id"], attempt["agent_run_id"]]:
            self.assertEqual(
                self.client.get(f"/api/v1/agent-runs/{run_id}", headers=self.headers).status_code,
                404,
            )

    def test_loop_endpoints_return_404_for_missing_records(self) -> None:
        resource = self.client.post(
            "/api/v1/resources/generate",
            headers=self.headers,
            json={"path_item_id": 999999, "resource_type": "讲义"},
        )
        self.assertEqual(resource.status_code, 404)

        tutor = self.client.post(
            "/api/v1/tutor/ask",
            headers=self.headers,
            json={"student_profile_id": 999999, "course_id": 999999, "question": "x"},
        )
        self.assertEqual(tutor.status_code, 404)

        quiz = self.client.post(
            "/api/v1/quizzes/generate",
            headers=self.headers,
            json={"student_profile_id": 999999, "concept_id": 999999, "difficulty": "basic"},
        )
        self.assertEqual(quiz.status_code, 404)

        attempt = self.client.post(
            "/api/v1/quizzes/999999/attempts",
            headers=self.headers,
            json={"student_profile_id": 999999, "answers": {"answer": "x"}},
        )
        self.assertEqual(attempt.status_code, 404)

        profile_update = self.client.post(
            "/api/v1/student-profiles/999999/update-from-trace",
            headers=self.headers,
        )
        self.assertEqual(profile_update.status_code, 404)


if __name__ == "__main__":
    unittest.main()
