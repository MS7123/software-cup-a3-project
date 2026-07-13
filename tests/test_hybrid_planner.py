import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.adapters.llm_provider import LLMSettings
from app.adapters.protocols import LLMResult
from app.agents.planner_agents import (
    HybridPlannerAgent,
    PlannerConcept,
    PlannerContext,
    PlannerRelation,
    RuleBasedHybridPlannerAgent,
    build_planner_agent,
)
from app.db.session import get_engine
from app.main import create_app


class FakePlannerProvider:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.messages = []

    def generate(self, messages, response_schema=None) -> LLMResult:
        self.messages = messages
        return LLMResult(
            content=json.dumps(self.payload, ensure_ascii=False),
            metadata={"provider": "openai_compatible", "model": "planner-test-model"},
        )


class RaisingPlannerProvider:
    def generate(self, messages, response_schema=None) -> LLMResult:
        raise TimeoutError("planner timeout")


class RawPlannerProvider:
    def __init__(self, content: str) -> None:
        self.content = content

    def generate(self, messages, response_schema=None) -> LLMResult:
        return LLMResult(
            content=self.content,
            metadata={"provider": "openai_compatible", "model": "planner-test-model"},
        )


class HybridPlannerAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.concepts = [
            PlannerConcept(id=30, slug="foundation", name="基础", chapter="第一章", difficulty="basic"),
            PlannerConcept(id=10, slug="advanced", name="进阶", chapter="第二章", difficulty="medium"),
            PlannerConcept(id=20, slug="practice", name="实践", chapter="第三章", difficulty="basic"),
        ]
        self.relations = [PlannerRelation(source_concept_id=30, target_concept_id=10)]

    def test_rule_based_fallback_uses_topology_instead_of_concept_id(self) -> None:
        result = RuleBasedHybridPlannerAgent().plan(
            self.concepts,
            self.relations,
            PlannerContext(
                goal="掌握课程",
                profile_type="weak_foundation",
                foundation_level="beginner",
                learning_preference="step_by_step",
                available_time="每天一小时",
                weak_points=["基础"],
                resource_preference="讲解文档",
            ),
        )

        order = [item.concept_id for item in result.recommendations]
        self.assertNotEqual(order, [10, 20, 30])
        self.assertLess(order.index(30), order.index(10))
        self.assertEqual(result.execution_mode, "rule_based")

    def test_two_profiles_receive_different_resource_recommendations(self) -> None:
        planner = RuleBasedHybridPlannerAgent()
        code_result = planner.plan(
            self.concepts,
            self.relations,
            PlannerContext(
                goal="掌握课程",
                profile_type="algorithm_practice",
                foundation_level="intermediate",
                learning_preference="code_driven",
                available_time="每周六小时",
                weak_points=[],
                resource_preference="代码实操案例",
            ),
        )
        sprint_result = planner.plan(
            self.concepts,
            self.relations,
            PlannerContext(
                goal="掌握课程",
                profile_type="exam_sprint",
                foundation_level="intermediate",
                learning_preference="summary_first",
                available_time="每天两小时",
                weak_points=[],
                resource_preference="练习题",
            ),
        )

        self.assertNotEqual(
            code_result.recommendations[0].recommended_resource_type,
            sprint_result.recommendations[0].recommended_resource_type,
        )

    def test_llm_can_rank_only_real_concepts_when_prerequisites_remain_valid(self) -> None:
        provider = FakePlannerProvider(
            {
                "recommendations": [
                    {"concept_id": 20, "recommended_resource_type": "coding_case", "reason": "先实践", "priority": 1},
                    {"concept_id": 30, "recommended_resource_type": "guided_note", "reason": "再补基础", "priority": 2},
                    {"concept_id": 10, "recommended_resource_type": "practice_questions", "reason": "最后进阶", "priority": 3},
                ]
            }
        )
        result = HybridPlannerAgent(provider, provider_name="openai_compatible", model="planner-test-model").plan(
            self.concepts,
            self.relations,
            PlannerContext(
                goal="掌握课程",
                profile_type="algorithm_practice",
                foundation_level="intermediate",
                learning_preference="code_driven",
                available_time="每周六小时",
                weak_points=["实践"],
                resource_preference="代码实操案例",
            ),
        )

        self.assertEqual([item.concept_id for item in result.recommendations], [20, 30, 10])
        self.assertEqual(result.execution_mode, "llm")
        self.assertFalse(result.fallback_used)

    def test_sparse_llm_signals_are_completed_by_the_rule_layer(self) -> None:
        agent = HybridPlannerAgent(
            FakePlannerProvider(
                {
                    "recommendations": [
                        {
                            "concept_id": 20,
                            "recommended_resource_type": "coding_case",
                            "reason": "优先完成实践",
                            "priority": 1,
                        }
                    ]
                }
            )
        )
        result = agent.plan(
            self.concepts,
            self.relations,
            PlannerContext(
                goal="掌握课程",
                profile_type="algorithm_practice",
                foundation_level="intermediate",
                learning_preference="code_driven",
                available_time="每天一小时",
                weak_points=["实践"],
                resource_preference="代码实操案例",
            ),
        )

        self.assertEqual([item.concept_id for item in result.recommendations], [20, 30, 10])
        self.assertEqual([item.priority for item in result.recommendations], [1, 2, 3])
        self.assertEqual(result.execution_mode, "llm")
        self.assertFalse(result.fallback_used)

    def test_concatenated_valid_signal_objects_are_repaired_without_remote_retry(self) -> None:
        items = [
            {
                "concept_id": 20,
                "recommended_resource_type": "coding_case",
                "reason": "prioritize practice",
                "priority": 1,
            },
            {
                "concept_id": 30,
                "recommended_resource_type": "guided_note",
                "reason": "review foundation",
                "priority": 2,
            },
        ]
        content = "\n,\n".join(json.dumps(item) for item in items)

        result = HybridPlannerAgent(RawPlannerProvider(content)).plan(
            self.concepts,
            self.relations,
            PlannerContext(
                goal="master the course",
                profile_type="algorithm_practice",
                foundation_level="intermediate",
                learning_preference="code_driven",
                available_time="one hour daily",
                weak_points=["practice"],
                resource_preference="coding_case",
            ),
        )

        self.assertEqual(result.execution_mode, "llm")
        self.assertFalse(result.fallback_used)
        self.assertEqual([item.concept_id for item in result.recommendations], [20, 30, 10])
        self.assertIn("structure_repaired=concatenated_objects", result.warning_reason or "")

    def test_llm_prompt_uses_an_eight_node_rolling_window(self) -> None:
        concepts = [
            PlannerConcept(
                id=index,
                slug=f"concept-{index}",
                name=f"知识点 {index}",
                chapter=f"第 {((index - 1) // 3) + 1} 章",
                difficulty="basic",
            )
            for index in range(1, 26)
        ]
        provider = FakePlannerProvider(
            {
                "recommendations": [
                    {
                        "concept_id": 1,
                        "recommended_resource_type": "guided_note",
                        "reason": "优先学习",
                        "priority": 1,
                    }
                ]
            }
        )

        result = HybridPlannerAgent(provider).plan(
            concepts,
            [],
            PlannerContext(
                goal="掌握完整课程",
                profile_type="weak_foundation",
                foundation_level="beginner",
                learning_preference="step_by_step",
                available_time="每天一小时",
                weak_points=[],
                resource_preference="讲解文档",
            ),
        )

        prompt = provider.messages[1]["content"]
        window_payload = prompt.split("LLM 候选窗口：", 1)[1].split("\n先修约束：", 1)[0]
        self.assertEqual(len(json.loads(window_payload)), 8)
        self.assertEqual(len(result.recommendations), 25)

    def test_focused_goal_returns_at_most_eight_relevant_nodes_instead_of_full_course(self) -> None:
        concepts = [
            PlannerConcept(1, "stack", "栈", "第 3 章", "basic"),
            PlannerConcept(2, "queue", "队列", "第 3 章", "basic"),
            PlannerConcept(3, "tree-basics", "树的基本概念", "第 4 章", "basic"),
            PlannerConcept(4, "binary-tree", "二叉树", "第 4 章", "basic"),
            PlannerConcept(5, "binary-tree-traversal", "二叉树遍历", "第 4 章", "medium"),
            PlannerConcept(6, "graph-representation", "图的表示", "第 5 章", "basic"),
            PlannerConcept(7, "bfs-dfs", "BFS/DFS", "第 5 章", "medium"),
            PlannerConcept(8, "sorting-basics", "排序基础", "第 7 章", "basic"),
            PlannerConcept(9, "simple-sorts", "简单排序", "第 7 章", "basic"),
        ]
        relations = [
            PlannerRelation(3, 4),
            PlannerRelation(4, 5),
            PlannerRelation(2, 5),
            PlannerRelation(5, 6),
            PlannerRelation(6, 7),
            PlannerRelation(8, 9),
        ]
        provider = FakePlannerProvider(
            {
                "recommendations": [
                    {
                        "concept_id": 5,
                        "recommended_resource_type": "practice_questions",
                        "reason": "小测前优先复习二叉树遍历",
                        "priority": 1,
                    },
                    {
                        "concept_id": 7,
                        "recommended_resource_type": "practice_questions",
                        "reason": "随后巩固图搜索",
                        "priority": 2,
                    },
                ]
            }
        )

        result = HybridPlannerAgent(provider).plan(
            concepts,
            relations,
            PlannerContext(
                goal="巩固二叉树遍历和图搜索，为课程小测做准备",
                profile_type="exam_sprint",
                foundation_level="intermediate",
                learning_preference="summary_first",
                available_time="每天两小时",
                weak_points=["二叉树遍历", "BFS/DFS"],
                resource_preference="练习题",
            ),
        )

        selected = {item.concept_id for item in result.recommendations}
        self.assertLessEqual(len(selected), 8)
        self.assertTrue({5, 7}.issubset(selected))
        self.assertTrue({3, 4, 6}.issubset(selected))
        self.assertTrue(selected.isdisjoint({8, 9}))

    def test_unknown_duplicate_and_prerequisite_violating_signals_are_repaired(self) -> None:
        for recommendations in (
            [
                {"concept_id": 999, "recommended_resource_type": "guided_note", "reason": "unknown", "priority": 1},
                {"concept_id": 30, "recommended_resource_type": "guided_note", "reason": "基础", "priority": 2},
                {"concept_id": 10, "recommended_resource_type": "guided_note", "reason": "进阶", "priority": 3},
            ],
            [
                {"concept_id": 10, "recommended_resource_type": "guided_note", "reason": "错误提前", "priority": 1},
                {"concept_id": 30, "recommended_resource_type": "guided_note", "reason": "基础", "priority": 2},
                {"concept_id": 20, "recommended_resource_type": "guided_note", "reason": "实践", "priority": 3},
            ],
            [
                {"concept_id": 30, "recommended_resource_type": "guided_note", "reason": "重复一", "priority": 1},
                {"concept_id": 30, "recommended_resource_type": "guided_note", "reason": "重复二", "priority": 2},
                {"concept_id": 20, "recommended_resource_type": "guided_note", "reason": "实践", "priority": 3},
            ],
        ):
            with self.subTest(recommendations=recommendations):
                agent = HybridPlannerAgent(FakePlannerProvider({"recommendations": recommendations}))
                result = agent.plan(
                    self.concepts,
                    self.relations,
                    PlannerContext(
                        goal="掌握课程",
                        profile_type="weak_foundation",
                        foundation_level="beginner",
                        learning_preference="step_by_step",
                        available_time="每天一小时",
                        weak_points=[],
                        resource_preference="讲解文档",
                    ),
                )
                order = [item.concept_id for item in result.recommendations]
                self.assertEqual(set(order), {10, 20, 30})
                self.assertEqual(result.execution_mode, "llm")
                self.assertFalse(result.fallback_used)
                self.assertLess(order.index(30), order.index(10))
                self.assertTrue(result.warning_reason)

    def test_cycle_is_rejected_and_provider_timeout_uses_topological_fallback(self) -> None:
        context = PlannerContext(
            goal="掌握课程",
            profile_type="weak_foundation",
            foundation_level="beginner",
            learning_preference="step_by_step",
            available_time="每天一小时",
            weak_points=[],
            resource_preference="讲解文档",
        )
        with self.assertRaisesRegex(ValueError, "cycle"):
            RuleBasedHybridPlannerAgent().plan(
                self.concepts,
                [PlannerRelation(30, 10), PlannerRelation(10, 30)],
                context,
            )

        result = HybridPlannerAgent(RaisingPlannerProvider()).plan(self.concepts, self.relations, context)
        self.assertEqual(result.execution_mode, "rule_based_fallback")
        self.assertIn("TimeoutError", result.fallback_reason)
        order = [item.concept_id for item in result.recommendations]
        self.assertLess(order.index(30), order.index(10))

    def test_factory_uses_planner_specific_flag(self) -> None:
        settings = LLMSettings(
            provider="openai_compatible",
            base_url="https://example.invalid/v1",
            api_key="test-only-key",
            model="planner-test-model",
            enable_for_planner=True,
        )
        self.assertIsInstance(build_planner_agent(settings), HybridPlannerAgent)
        self.assertTrue(settings.can_call_remote("planner"))
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "openai_compatible",
                "LLM_BASE_URL": "https://example.invalid/v1",
                "LLM_API_KEY": "test-only-key",
                "LLM_MODEL": "planner-test-model",
                "LLM_ENABLE_FOR_PLANNER": "true",
            },
            clear=True,
        ):
            self.assertTrue(LLMSettings.from_env().enable_for_planner)


class HybridPlannerApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "hybrid-planner.sqlite3"
        self.database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["APP_DATABASE_URL"] = self.database_url

    def tearDown(self) -> None:
        get_engine().dispose()
        get_engine(self.database_url).dispose()
        get_engine.cache_clear()
        os.environ.pop("APP_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def test_path_api_adds_recommendation_fields_and_respects_prerequisites(self) -> None:
        with TestClient(create_app()) as client:
            demo = client.post("/api/v1/demo-data/load").json()["demo_data"]
            profile = client.get("/api/v1/student-profiles").json()[0]
            graph = client.get(f"/api/v1/courses/{demo['course_id']}/graph").json()
            response = client.post(
                "/api/v1/learning-paths",
                json={
                    "student_profile_id": profile["id"],
                    "course_id": demo["course_id"],
                    "goal": "掌握数据结构课程",
                },
            )
            self.assertEqual(response.status_code, 200)
            flow = response.json()
            path = flow["learning_path"]

            self.assertIn(path["execution_mode"], {"rule_based", "llm", "rule_based_fallback"})
            positions = {item["concept_id"]: item["order_index"] for item in path["items"]}
            for relation in graph["relations"]:
                if relation["relation_type"] == "prerequisite":
                    self.assertLess(positions[relation["source_concept_id"]], positions[relation["target_concept_id"]])
            for item in path["items"]:
                self.assertTrue(item["recommended_resource_type"])
                self.assertTrue(item["recommendation_reason"])
                self.assertGreater(item["priority"], 0)

            planner_step = next(step for step in flow["agent_run"]["steps"] if step["agent_type"] == "planner")
            self.assertIn("execution_mode=", planner_step["decision_basis"])
            self.assertEqual(planner_step["execution_metadata"]["execution_mode"], path["execution_mode"])
            self.assertEqual(planner_step["execution_metadata"]["provider"], path["provider"])
            self.assertEqual(planner_step["execution_metadata"]["model"], path["model"])

    def test_different_demo_profiles_produce_different_resource_plans(self) -> None:
        with TestClient(create_app()) as client:
            demo = client.post("/api/v1/demo-data/load").json()["demo_data"]
            profiles = client.get("/api/v1/student-profiles").json()
            resource_sequences = []
            for profile in (profiles[0], profiles[2]):
                flow = client.post(
                    "/api/v1/learning-paths",
                    json={
                        "student_profile_id": profile["id"],
                        "course_id": demo["course_id"],
                        "goal": "掌握数据结构课程",
                    },
                ).json()
                resource_sequences.append(
                    [item["recommended_resource_type"] for item in flow["learning_path"]["items"]]
                )

            self.assertNotEqual(resource_sequences[0], resource_sequences[1])

    def test_low_quiz_mastery_reorders_pending_path_with_an_explanation(self) -> None:
        with TestClient(create_app()) as client:
            demo = client.post("/api/v1/demo-data/load").json()["demo_data"]
            profile = client.get("/api/v1/student-profiles").json()[0]
            graph = client.get(f"/api/v1/courses/{demo['course_id']}/graph").json()
            hash_concept = next(concept for concept in graph["concepts"] if concept["slug"] == "hash-table")
            flow = client.post(
                "/api/v1/learning-paths",
                json={
                    "student_profile_id": profile["id"],
                    "course_id": demo["course_id"],
                    "goal": "掌握数据结构课程",
                },
            ).json()
            path = flow["learning_path"]
            before_item = next(item for item in path["items"] if item["concept_id"] == hash_concept["id"])

            quiz = client.post(
                "/api/v1/quizzes/generate",
                json={
                    "student_profile_id": profile["id"],
                    "concept_id": hash_concept["id"],
                    "difficulty": "basic",
                },
            ).json()
            attempt = client.post(
                f"/api/v1/quizzes/{quiz['id']}/attempts",
                json={"student_profile_id": profile["id"], "answers": {"answer": ""}},
            )
            self.assertEqual(attempt.status_code, 200)

            refreshed = client.get(f"/api/v1/learning-paths/{path['id']}").json()
            after_item = next(item for item in refreshed["items"] if item["concept_id"] == hash_concept["id"])
            self.assertLess(after_item["order_index"], before_item["order_index"])
            self.assertIn("掌握度偏低", after_item["recommendation_reason"])


if __name__ == "__main__":
    unittest.main()
