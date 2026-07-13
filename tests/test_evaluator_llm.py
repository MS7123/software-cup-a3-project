import unittest

from app.adapters.llm_provider import LLMSettings
from app.adapters.protocols import LLMResult
from app.agents.evaluator_agents import LLMBackedEvaluatorAgent
from app.agents.evaluator_factory import build_evaluator_agent
from app.agents.rule_based_agents import RuleBasedEvaluatorAgent


class FakeEvaluatorProvider:
    def __init__(self, fail: bool = False, content: str | None = None) -> None:
        self.fail = fail
        self.content = content

    def generate(self, messages, response_schema=None) -> LLMResult:
        if self.fail:
            raise RuntimeError("evaluator provider unavailable")
        return LLMResult(
            content=self.content or """
            {
              "score": 0.72,
              "feedback": "你的回答能区分 BFS 和 DFS 的遍历方向，但缺少复杂度和适用场景说明。",
              "weak_points": ["复杂度分析", "适用场景"],
              "misconceptions": ["只描述遍历顺序，没有说明队列和递归栈的差异"],
              "next_action": "补做一道 BFS/DFS 场景选择题，并说明时间复杂度。"
            }
            """,
            metadata={"provider": "fake"},
        )


class EvaluatorLLMTests(unittest.TestCase):
    def test_evaluator_factory_defaults_to_rule_based_without_remote_config(self) -> None:
        agent = build_evaluator_agent(LLMSettings(provider="rule_based"))
        self.assertIsInstance(agent, RuleBasedEvaluatorAgent)

    def test_llm_evaluator_uses_json_feedback(self) -> None:
        agent = LLMBackedEvaluatorAgent(FakeEvaluatorProvider())
        result = agent.evaluate(
            "应说明 BFS 使用队列，DFS 使用递归或栈，并比较适用场景。",
            {"answer": "BFS 按层，DFS 一条路走到底。"},
            5,
        )

        self.assertAlmostEqual(result.score, 0.72)
        self.assertIn("复杂度", result.feedback)
        self.assertEqual(result.mastery_updates[0]["concept_id"], 5)
        self.assertEqual(result.mastery_updates[0]["evidence"]["analysis_method"], "llm")
        self.assertIn("LLM Evaluator", result.output_summary)

    def test_llm_evaluator_falls_back_when_provider_fails(self) -> None:
        agent = LLMBackedEvaluatorAgent(FakeEvaluatorProvider(fail=True))
        result = agent.evaluate("应围绕链表定义说明。", {"answer": "链表由节点组成。"}, 2)

        self.assertGreaterEqual(result.score, 0.0)
        self.assertIn("Fallback reason", result.decision_basis)
        self.assertIn("evaluator provider unavailable", result.decision_basis)
        self.assertIn("rule-based", result.output_summary)

    def test_llm_evaluator_rejects_invalid_json_and_falls_back_safely(self) -> None:
        agent = LLMBackedEvaluatorAgent(FakeEvaluatorProvider(content="not-json"))

        result = agent.evaluate("应围绕链表定义说明。", {"answer": "链表由节点组成。"}, 2)

        self.assertGreaterEqual(result.score, 0.0)
        self.assertLessEqual(result.score, 1.0)
        self.assertIn("rule-based", result.output_summary)
        self.assertIn("Fallback reason:", result.decision_basis)
        self.assertIn("JSON object", result.decision_basis)


if __name__ == "__main__":
    unittest.main()
