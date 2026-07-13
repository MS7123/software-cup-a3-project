import unittest
import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.agents.planner_agents import (
    GoalResolutionError,
    LearningIntent,
    PlannerConcept,
    PlannerContext,
    PlannerRelation,
    resolve_goal_deterministically,
    select_minimal_path,
)
from app.db.session import get_engine, session_scope
from app.main import create_app
from app.models import LearningPath


class SemanticPlannerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.concepts = [
            PlannerConcept(1, "stack", "栈", "线性结构", "basic"),
            PlannerConcept(2, "queue", "队列", "线性结构", "basic"),
            PlannerConcept(3, "graph-representation", "图的表示", "图", "basic"),
            PlannerConcept(4, "bfs-dfs", "BFS/DFS", "图", "medium"),
            PlannerConcept(5, "shortest-path", "最短路径", "图", "medium"),
            PlannerConcept(6, "hash-table", "哈希表", "查找", "medium"),
        ]
        self.context = PlannerContext(
            goal="",
            profile_type="exam_sprint",
            foundation_level="intermediate",
            learning_preference="summary_first",
            available_time="每天两小时",
            weak_points=[],
            resource_preference="练习题",
        )

    def test_bfs_dfs_synonyms_resolve_to_same_target_and_quiz_intent(self) -> None:
        target_sets = []
        for goal in ("图搜索", "深度搜索和广度搜索", "BFS/DFS", "广搜和深搜"):
            resolution = resolve_goal_deterministically(goal, self.concepts)
            target_sets.append(set(resolution.target_concept_ids))
        self.assertTrue(all(targets == {4} for targets in target_sets))

        quiz = resolve_goal_deterministically("巩固 BFS/DFS，为课程小测做准备", self.concepts)
        self.assertEqual(quiz.learning_intent.purpose, "assessment_preparation")
        self.assertEqual(quiz.learning_intent.assessment_type, "course_quiz")

    def test_unknown_goal_is_rejected_instead_of_expanding_to_full_course(self) -> None:
        with self.assertRaises(GoalResolutionError):
            resolve_goal_deterministically("把这个再弄扎实一点", self.concepts)

    def test_minimal_path_adds_only_unsatisfied_hard_prerequisites(self) -> None:
        intent = LearningIntent(
            purpose="concept_learning",
            action="learn",
            assessment_type="none",
            time_horizon="short_term",
            preferred_activities=["explanation"],
            desired_outcome="掌握 BFS 与 DFS",
        )
        selected = select_minimal_path(
            self.concepts,
            [PlannerRelation(3, 4, "prerequisite"), PlannerRelation(2, 4, "related")],
            target_concept_ids=[4],
            optional_support_concept_ids=[],
            context=self.context,
            learning_intent=intent,
        )
        self.assertEqual([item.concept.id for item in selected], [3, 4])
        self.assertEqual([item.node_role for item in selected], ["prerequisite", "target"])

        mastered_context = PlannerContext(**{**self.context.__dict__, "mastery_scores": {3: 0.8}})
        selected = select_minimal_path(
            self.concepts,
            [PlannerRelation(3, 4, "prerequisite")],
            target_concept_ids=[4],
            optional_support_concept_ids=[],
            context=mastered_context,
            learning_intent=intent,
        )
        self.assertEqual([item.concept.id for item in selected], [4])


class SemanticPlannerApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        path = Path(self.temp_dir.name) / "semantic-planner.sqlite3"
        self.database_url = f"sqlite:///{path.as_posix()}"
        os.environ["APP_DATABASE_URL"] = self.database_url

    def tearDown(self) -> None:
        get_engine().dispose()
        get_engine(self.database_url).dispose()
        get_engine.cache_clear()
        os.environ.pop("APP_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def test_unknown_goal_returns_422_without_creating_path(self) -> None:
        with TestClient(create_app()) as client:
            demo = client.post("/api/v1/demo-data/load").json()["demo_data"]
            profile = client.get("/api/v1/student-profiles").json()[0]
            response = client.post("/api/v1/learning-paths", json={
                "student_profile_id": profile["id"], "course_id": demo["course_id"], "goal": "把这个再弄扎实一点"
            })
            self.assertEqual(response.status_code, 422)
            self.assertIn("知识点", response.json()["detail"])
        with session_scope(self.database_url) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(LearningPath)), 0)

    def test_path_persists_intent_targets_and_activity_fields(self) -> None:
        with TestClient(create_app()) as client:
            demo = client.post("/api/v1/demo-data/load").json()["demo_data"]
            profile = client.get("/api/v1/student-profiles").json()[0]
            response = client.post("/api/v1/learning-paths", json={
                "student_profile_id": profile["id"], "course_id": demo["course_id"],
                "goal": "巩固广搜和深搜，为课程小测做准备"
            })
            self.assertEqual(response.status_code, 200, response.text)
            path = response.json()["learning_path"]
            self.assertEqual(path["learning_intent"]["purpose"], "assessment_preparation")
            self.assertTrue(path["target_concept_ids"])
            self.assertLessEqual(len(path["items"]), 8)
            for item in path["items"]:
                self.assertIn(item["node_role"], {"target", "prerequisite"})
                self.assertTrue(item["activity_type"])
                self.assertGreaterEqual(item["estimated_minutes"], 5)
                self.assertTrue(item["success_criterion"])


if __name__ == "__main__":
    unittest.main()
