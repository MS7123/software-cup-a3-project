from tests.test_helper import AuthenticatedTestCase
from app.seed.demo_data import DEMO_CONCEPTS, DEMO_PROFILES, DEMO_RELATIONS


PROFILE_DIMENSION_KEYS = {
    "learning_goal",
    "foundation_level",
    "learning_preference",
    "available_time",
    "weak_points",
    "resource_preference",
}


class ProfileCourseApiTests(AuthenticatedTestCase):
    def test_student_profile_list_and_detail_return_demo_profiles(self) -> None:
        profiles = self.client.get("/api/v1/student-profiles", headers=self.headers).json()
        # After user registration, we expect 3 demo profiles for this user
        self.assertGreaterEqual(len(profiles), 1)
        for profile in profiles:
            self.assertTrue(profile["goal"])
            self.assertTrue(profile["level"])
            self.assertTrue(profile["preferences"])
            self.assertTrue(profile["time_budget"])
            self.assertTrue(PROFILE_DIMENSION_KEYS.issubset(set(profile["preferences"])))

        detail = self.client.get(f"/api/v1/student-profiles/{profiles[0]['id']}", headers=self.headers)
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
        response = self.client.post("/api/v1/student-profiles", headers=self.headers, json=payload)
        self.assertEqual(response.status_code, 200)
        created = response.json()
        self.assertGreater(created["id"], 0)
        self.assertEqual(created["goal"], payload["goal"])
        self.assertEqual(created["preferences"]["style"], payload["preferences"]["style"])
        self.assertTrue(PROFILE_DIMENSION_KEYS.issubset(set(created["preferences"])))

    def test_student_profile_create_from_dialogue_returns_six_dimension_profile(self) -> None:
        payload = {
            "dialogue": "我基础薄弱，想每天 1 小时复习二叉树遍历和 BFS/DFS，希望用例题和练习题准备小测"
        }
        response = self.client.post("/api/v1/student-profiles/from-dialogue", headers=self.headers, json=payload)
        self.assertEqual(response.status_code, 200)
        created = response.json()

        self.assertGreater(created["id"], 0)
        self.assertEqual(created["profile_type"], "exam_sprint")
        self.assertEqual(created["level"], "beginner")
        self.assertIn("二叉树遍历", created["preferences"]["weak_points"])
        self.assertIn("BFS/DFS", created["preferences"]["weak_points"])
        self.assertTrue(PROFILE_DIMENSION_KEYS.issubset(set(created["preferences"])))

        status_response = self.client.post("/api/v1/demo-data/load", headers=self.headers)
        course_id = status_response.json()["demo_data"]["course_id"]
        path_response = self.client.post(
            "/api/v1/learning-paths",
            headers=self.headers,
            json={
                "student_profile_id": created["id"],
                "course_id": course_id,
                "goal": created["goal"],
            },
        )
        self.assertEqual(path_response.status_code, 200)
        self.assertEqual(path_response.json()["learning_path"]["student_profile_id"], created["id"])

    def test_user_profile_can_be_deleted_but_demo_profile_is_protected(self) -> None:
        profiles = self.client.get("/api/v1/student-profiles", headers=self.headers).json()
        # Demo profile cannot be deleted
        demo_delete = self.client.delete(f"/api/v1/student-profiles/{profiles[0]['id']}", headers=self.headers)
        self.assertEqual(demo_delete.status_code, 409)

        # User-created profile can be deleted
        created = self.client.post(
            "/api/v1/student-profiles/from-dialogue",
            headers=self.headers,
            json={"dialogue": "我想用代码练习链表，每周 6 小时。"},
        ).json()
        self.assertEqual(created["preferences"]["profile_origin"], "user_dialogue")
        delete_response = self.client.delete(f"/api/v1/student-profiles/{created['id']}", headers=self.headers)
        self.assertEqual(delete_response.status_code, 204)

        missing = self.client.get(f"/api/v1/student-profiles/{created['id']}", headers=self.headers)
        self.assertEqual(missing.status_code, 404)

    def test_course_graph_returns_demo_course_concepts_and_relations(self) -> None:
        status_response = self.client.post("/api/v1/demo-data/load", headers=self.headers)
        self.assertEqual(status_response.status_code, 200)
        course_id = status_response.json()["demo_data"]["course_id"]

        graph_response = self.client.get(f"/api/v1/courses/{course_id}/graph", headers=self.headers)
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
        profile_response = self.client.get("/api/v1/student-profiles/999999", headers=self.headers)
        self.assertEqual(profile_response.status_code, 404)

        course_response = self.client.get("/api/v1/courses/999999/graph", headers=self.headers)
        self.assertEqual(course_response.status_code, 404)
