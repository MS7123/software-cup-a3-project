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


class SequentialPlannerProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate(self, messages, response_schema=None) -> LLMResult:
        self.calls.append((messages, response_schema))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return LLMResult(content=json.dumps(response, ensure_ascii=False), metadata={"provider": "fake", "model": "planner-test"})


def _resolution():
    return {
        "course_scope": "focused",
        "target_concept_ids": [20],
        "optional_support_concept_ids": [],
        "purpose": "project_application",
        "action": "practice",
        "assessment_type": "none",
        "time_horizon": "short_term",
        "preferred_activities": ["coding"],
        "desired_outcome": "能够实现并解释实践节点",
        "confidence": 0.91,
    }


def _activities():
    return {"activities": [
        {"concept_id": 20, "node_role": "target", "activity_type": "coding", "objective": "完成代码实现", "estimated_minutes": 30, "success_criterion": "代码通过样例并能解释复杂度", "recommended_resource_type": "coding_case", "reason": "匹配代码实践目标", "priority": 1}
    ]}


class HybridPlannerAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.concepts = [
            PlannerConcept(30, "foundation", "基础", "第一章", "basic"),
            PlannerConcept(10, "advanced", "进阶", "第二章", "medium"),
            PlannerConcept(20, "practice", "实践", "第三章", "basic"),
        ]
        self.relations = [PlannerRelation(30, 10)]

    def test_rule_based_full_course_uses_topology(self) -> None:
        result = RuleBasedHybridPlannerAgent().plan(self.concepts, self.relations, self._context("系统掌握整门课程"))
        order = [item.concept_id for item in result.recommendations]
        self.assertLess(order.index(30), order.index(10))
        self.assertEqual(result.execution_mode, "rule_based")

    def test_two_llm_phases_return_valid_activity_without_expanding_nodes(self) -> None:
        provider = SequentialPlannerProvider([_resolution(), _activities()])
        result = HybridPlannerAgent(provider, provider_name="fake", model="planner-test").plan(
            self.concepts, self.relations, self._context("使用代码实践")
        )
        self.assertEqual(len(provider.calls), 2)
        self.assertEqual([item.concept_id for item in result.recommendations], [20])
        self.assertEqual(result.recommendations[0].activity_type, "coding")
        self.assertEqual(result.execution_mode, "llm")
        self.assertEqual([item.phase for item in result.phase_traces], ["goal_resolution", "constraint_validation", "activity_generation"])

    def test_activity_timeout_keeps_resolved_node_set_and_falls_back(self) -> None:
        provider = SequentialPlannerProvider([_resolution(), TimeoutError("activity timeout")])
        result = HybridPlannerAgent(provider).plan(self.concepts, self.relations, self._context("使用代码实践"))
        self.assertEqual([item.concept_id for item in result.recommendations], [20])
        self.assertEqual(result.execution_mode, "rule_based_fallback")
        self.assertIn("activity_generation", result.fallback_reason or "")

    def test_activity_with_wrong_node_role_is_rejected_and_falls_back(self) -> None:
        invalid = _activities()
        invalid["activities"][0]["node_role"] = "prerequisite"
        result = HybridPlannerAgent(SequentialPlannerProvider([_resolution(), invalid])).plan(
            self.concepts, self.relations, self._context("使用代码实践")
        )
        self.assertEqual(result.execution_mode, "rule_based_fallback")
        self.assertEqual(result.recommendations[0].node_role, "target")

    def test_rule_fallback_distributes_chinese_time_budget(self) -> None:
        result = RuleBasedHybridPlannerAgent().plan(
            self.concepts, self.relations, self._context("系统掌握整门课程")
        )
        self.assertLessEqual(sum(item.estimated_minutes for item in result.recommendations), 60)

    def test_factory_uses_planner_specific_flag(self) -> None:
        settings = LLMSettings(provider="openai_compatible", base_url="https://example.invalid/v1", api_key="test", model="test", enable_for_planner=True)
        self.assertIsInstance(build_planner_agent(settings), HybridPlannerAgent)
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai_compatible", "LLM_BASE_URL": "https://example.invalid/v1", "LLM_API_KEY": "test", "LLM_MODEL": "test", "LLM_ENABLE_FOR_PLANNER": "true"}, clear=True):
            self.assertTrue(LLMSettings.from_env().enable_for_planner)

    @staticmethod
    def _context(goal: str) -> PlannerContext:
        return PlannerContext(goal=goal, profile_type="practice", foundation_level="intermediate", learning_preference="code_driven", available_time="每天一小时", weak_points=[], resource_preference="代码实操案例")


class HybridPlannerApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "hybrid-planner.sqlite3"
        self.database_url = f"sqlite:///{database_path.as_posix()}"
        os.environ["APP_DATABASE_URL"] = self.database_url

    def tearDown(self) -> None:
        get_engine().dispose(); get_engine(self.database_url).dispose(); get_engine.cache_clear()
        os.environ.pop("APP_DATABASE_URL", None); self.temp_dir.cleanup()

    def test_focused_api_path_is_small_and_respects_hard_prerequisites(self) -> None:
        with TestClient(create_app()) as client:
            demo = client.post("/api/v1/demo-data/load").json()["demo_data"]
            profile = client.get("/api/v1/student-profiles").json()[0]
            graph = client.get(f"/api/v1/courses/{demo['course_id']}/graph").json()
            response = client.post("/api/v1/learning-paths", json={"student_profile_id": profile["id"], "course_id": demo["course_id"], "goal": "巩固 BFS/DFS，为课程小测做准备"})
            self.assertEqual(response.status_code, 200, response.text)
            flow = response.json(); path = flow["learning_path"]
            self.assertLessEqual(len(path["items"]), 8)
            positions = {item["concept_id"]: item["order_index"] for item in path["items"]}
            for relation in graph["relations"]:
                if relation["relation_type"] == "prerequisite" and relation["source_concept_id"] in positions and relation["target_concept_id"] in positions:
                    self.assertLess(positions[relation["source_concept_id"]], positions[relation["target_concept_id"]])
            planner_steps = [step for step in flow["agent_run"]["steps"] if step["agent_type"] == "planner"]
            self.assertEqual(len(planner_steps), 3)


if __name__ == "__main__":
    unittest.main()
