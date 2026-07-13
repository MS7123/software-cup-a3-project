from dataclasses import dataclass
from typing import Any

from app.agents.rule_based_agents import QuizAgentResult, ResourceAgentResult


@dataclass(frozen=True)
class CriticResult:
    approved: bool
    output_summary: str
    decision_basis: str
    revision_instruction: str = ""


class RuleBasedCriticAgent:
    high_difficulty_terms = ("红黑树", "B+树", "动态规划优化", "复杂证明", "手写旋转")

    def review_resource(
        self,
        result: ResourceAgentResult,
        resource_type: str,
        profile_preferences: dict[str, Any] | None = None,
    ) -> CriticResult:
        preferences = profile_preferences or {}
        content = result.content
        if not result.source_refs:
            return CriticResult(
                approved=False,
                output_summary="资源审查未通过：缺少可追溯来源。",
                decision_basis="Resource Agent 输出必须由 Retriever 提供的 source_refs 支撑，避免无依据扩写。",
                revision_instruction="请显式说明资料不足，并降低事实性断言密度；补充基于当前学习节点的保守讲解。",
            )
        if resource_type == "coding_case" and "```" not in content:
            return CriticResult(
                approved=False,
                output_summary="资源审查未通过：代码实操案例缺少 fenced code block。",
                decision_basis="coding_case 类型必须提供可识别代码块，便于后续接入代码沙箱验证。",
                revision_instruction="请补充 ```python fenced code block、输入样例、预期输出和边界条件。",
            )
        if self._is_weak_foundation(preferences) and self._contains_high_difficulty(content):
            return CriticResult(
                approved=False,
                output_summary="资源审查未通过：内容难度高于当前学生画像。",
                decision_basis="学生画像显示基础薄弱，资源中出现高阶复杂结构或证明任务，需要降级讲解。",
                revision_instruction="请降级为基础概念、可视化例子和一步一步练习，避免高阶结构手写代码。",
            )
        return CriticResult(
            approved=True,
            output_summary="资源审查通过：内容类型、画像匹配和溯源证据满足要求。",
            decision_basis="Evaluator/Critic Agent 根据资源类型约束、学生画像和 source_refs 完成审查。",
        )

    def review_quiz(
        self,
        result: QuizAgentResult,
        difficulty: str,
        profile_preferences: dict[str, Any] | None = None,
        available_source_refs: set[str] | None = None,
    ) -> CriticResult:
        preferences = profile_preferences or {}
        text = " ".join([result.question, result.answer, result.explanation])
        cited_source_refs = {
            str(item.get("source_ref")) for item in result.source_refs if isinstance(item, dict) and item.get("source_ref")
        }
        if available_source_refs and (not cited_source_refs or not cited_source_refs.issubset(available_source_refs)):
            return CriticResult(
                approved=False,
                output_summary="测验审查未通过：题目缺少真实引用或包含引用白名单之外的来源。",
                decision_basis="Quiz source_refs 必须是 Retriever 本次返回来源的非空子集，禁止伪造引用。",
                revision_instruction="仅使用本次 Retriever 提供的 source_ref，并在解析中说明证据依据。",
            )
        if result.question_type == "multiple_choice" and len(result.options) < 2:
            return CriticResult(
                approved=False,
                output_summary="测验审查未通过：选择题选项不完整。",
                decision_basis="multiple_choice 必须包含至少两个可辨识选项和明确答案。",
                revision_instruction="补齐至少两个互斥选项，并确保 answer 对应其中一个选项标签。",
            )
        if result.question_type == "code_analysis" and "```" not in result.question:
            return CriticResult(
                approved=False,
                output_summary="测验审查未通过：代码分析题缺少 fenced code block。",
                decision_basis="code_analysis 必须包含可识别代码片段，才能形成可执行的分析对象。",
                revision_instruction="在题干中补充 fenced code block，并提出与代码执行或边界条件相关的问题。",
            )
        if self._is_weak_foundation(preferences) and (difficulty in {"hard", "advanced"} or self._contains_high_difficulty(text)):
            return CriticResult(
                approved=False,
                output_summary="测验审查未通过：题目难度与基础薄弱画像不匹配。",
                decision_basis="Evaluator/Critic Agent 发现题目超出当前学生基础水平，需要打回出题智能体降级。",
                revision_instruction="请将难度降为 easy，聚焦定义、遍历过程和一个简单应用场景。",
            )
        if not result.answer.strip() or not result.explanation.strip():
            return CriticResult(
                approved=False,
                output_summary="测验审查未通过：缺少答案或解析。",
                decision_basis="测验必须包含 question、answer、explanation，才能用于后续自动评估。",
                revision_instruction="请补齐标准答案和解析依据。",
            )
        return CriticResult(
            approved=True,
            output_summary="测验审查通过：题目难度、答案和解析满足当前画像约束。",
            decision_basis="Evaluator/Critic Agent 基于学生画像、难度约束和题目完整性完成审查。",
        )

    def _is_weak_foundation(self, preferences: dict[str, Any]) -> bool:
        text = " ".join(str(value) for value in preferences.values()).lower()
        return any(term in text for term in ("weak", "薄弱", "基础一般", "基础较弱", "基础差"))

    def _contains_high_difficulty(self, text: str) -> bool:
        return any(term in text for term in self.high_difficulty_terms)
