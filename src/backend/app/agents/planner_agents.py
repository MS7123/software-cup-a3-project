import json
import re
import time
from dataclasses import dataclass, field, replace
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field, ValidationError

from app.adapters.llm_provider import LLMProviderError, LLMSettings, build_llm_provider
from app.adapters.protocols import LLMProvider
from app.services.content_safety_service import ContentSafetyService


ResourceType = Literal["guided_note", "practice_questions", "mind_map", "extended_reading", "coding_case"]


@dataclass(frozen=True)
class PlannerConcept:
    id: int
    slug: str
    name: str
    chapter: str
    difficulty: str


@dataclass(frozen=True)
class PlannerRelation:
    source_concept_id: int
    target_concept_id: int


@dataclass(frozen=True)
class PlannerContext:
    goal: str
    profile_type: str
    foundation_level: str
    learning_preference: str
    available_time: str
    weak_points: list[str]
    resource_preference: str
    completed_concept_ids: set[int] = field(default_factory=set)
    mastery_scores: dict[int, float] = field(default_factory=dict)


@dataclass(frozen=True)
class PlannerRecommendation:
    concept_id: int
    recommended_resource_type: str
    reason: str
    priority: int


@dataclass(frozen=True)
class PlannerResult:
    recommendations: list[PlannerRecommendation]
    execution_mode: str
    provider: str
    model: str
    fallback_used: bool
    fallback_reason: str | None
    duration_ms: int
    warning_reason: str | None = None


class PlannerOutputItem(BaseModel):
    concept_id: int
    recommended_resource_type: ResourceType
    reason: str = Field(min_length=1, max_length=300)
    priority: int = Field(ge=1)


class PlannerOutput(BaseModel):
    recommendations: list[PlannerOutputItem] = Field(min_length=1, max_length=5)


PLANNER_OUTPUT_SCHEMA: dict[str, Any] = PlannerOutput.model_json_schema()


class PlannerAgent(Protocol):
    def plan(
        self,
        concepts: list[PlannerConcept],
        relations: list[PlannerRelation],
        context: PlannerContext,
    ) -> PlannerResult:
        raise NotImplementedError


class RuleBasedHybridPlannerAgent:
    def plan(
        self,
        concepts: list[PlannerConcept],
        relations: list[PlannerRelation],
        context: PlannerContext,
    ) -> PlannerResult:
        started = time.perf_counter()
        ordered = _topological_order(concepts, relations, context)
        resource_type = _resource_type_for_context(context)
        recommendations = [
            PlannerRecommendation(
                concept_id=concept.id,
                recommended_resource_type=resource_type,
                reason=_rule_reason(concept, context, resource_type),
                priority=index,
            )
            for index, concept in enumerate(ordered, start=1)
        ]
        return PlannerResult(
            recommendations=recommendations,
            execution_mode="rule_based",
            provider="rule_based",
            model="",
            fallback_used=False,
            fallback_reason=None,
            duration_ms=_elapsed_ms(started),
        )


class HybridPlannerAgent:
    def __init__(
        self,
        provider: LLMProvider,
        fallback_agent: PlannerAgent | None = None,
        fallback_mode: str = "rule_based",
        provider_name: str = "openai_compatible",
        model: str = "",
    ) -> None:
        self.provider = provider
        self.fallback_agent = fallback_agent or RuleBasedHybridPlannerAgent()
        self.fallback_mode = fallback_mode if fallback_mode in {"rule_based", "error"} else "rule_based"
        self.provider_name = provider_name
        self.model = model

    def plan(
        self,
        concepts: list[PlannerConcept],
        relations: list[PlannerRelation],
        context: PlannerContext,
    ) -> PlannerResult:
        started = time.perf_counter()
        try:
            safety_text = " ".join(
                [
                    context.goal,
                    context.profile_type,
                    context.foundation_level,
                    context.learning_preference,
                    context.available_time,
                    *context.weak_points,
                    context.resource_preference,
                ]
            )
            safety = ContentSafetyService().review_input(safety_text)
            if not safety.allowed:
                raise ValueError(f"Content safety blocked input: {safety.category}")
            eligible = [concept for concept in concepts if concept.id not in context.completed_concept_ids]
            if not eligible:
                return PlannerResult([], "llm", self.provider_name, self.model, False, None, _elapsed_ms(started))
            result = self.provider.generate(
                _build_planner_messages(eligible, relations, context),
                response_schema=PLANNER_OUTPUT_SCHEMA,
            )
            parsed = _parse_planner_output(result.content)
            recommendations, warning_reason = _compose_hybrid_recommendations(
                parsed.recommendations,
                concepts,
                relations,
                context,
            )
            _validate_recommendations(recommendations, concepts, relations, context.completed_concept_ids)
            return PlannerResult(
                recommendations=recommendations,
                execution_mode="llm",
                provider=str(result.metadata.get("provider") or self.provider_name),
                model=str(result.metadata.get("model") or self.model),
                fallback_used=False,
                fallback_reason=None,
                duration_ms=_elapsed_ms(started),
                warning_reason=warning_reason,
            )
        except Exception as exc:
            reason = _fallback_reason(exc)
            if self.fallback_mode == "error":
                raise LLMProviderError(reason) from exc
            fallback = self.fallback_agent.plan(concepts, relations, context)
            return replace(
                fallback,
                execution_mode="rule_based_fallback",
                provider=self.provider_name,
                model=self.model,
                fallback_used=True,
                fallback_reason=reason,
                duration_ms=_elapsed_ms(started),
            )


def build_planner_agent(settings: LLMSettings | None = None) -> PlannerAgent:
    resolved = settings or LLMSettings.from_env()
    provider = build_llm_provider(resolved, purpose="planner")
    if provider is None:
        return RuleBasedHybridPlannerAgent()
    return HybridPlannerAgent(
        provider,
        fallback_mode=resolved.fallback_mode,
        provider_name=resolved.provider,
        model=resolved.model,
    )


def _topological_order(
    concepts: list[PlannerConcept],
    relations: list[PlannerRelation],
    context: PlannerContext,
    preferred_priority: dict[int, tuple[int, int]] | None = None,
) -> list[PlannerConcept]:
    concept_by_id = {concept.id: concept for concept in concepts}
    pending_ids = set(concept_by_id) - context.completed_concept_ids
    indegree = {concept_id: 0 for concept_id in pending_ids}
    outgoing = {concept_id: [] for concept_id in pending_ids}
    for relation in relations:
        source = relation.source_concept_id
        target = relation.target_concept_id
        if target not in pending_ids:
            continue
        if source in context.completed_concept_ids:
            continue
        if source not in pending_ids or target not in concept_by_id:
            raise ValueError("Prerequisite relation references an unknown concept.")
        indegree[target] += 1
        outgoing[source].append(target)

    ordered: list[PlannerConcept] = []
    available = [concept_by_id[concept_id] for concept_id, degree in indegree.items() if degree == 0]
    while available:
        available.sort(
            key=lambda concept: (
                (preferred_priority or {}).get(concept.id, (10_000, 10_000)),
                _personalization_key(concept, context),
            )
        )
        concept = available.pop(0)
        ordered.append(concept)
        for target in outgoing[concept.id]:
            indegree[target] -= 1
            if indegree[target] == 0:
                available.append(concept_by_id[target])

    if len(ordered) != len(pending_ids):
        raise ValueError("Prerequisite graph contains a cycle.")
    return ordered


def _personalization_key(concept: PlannerConcept, context: PlannerContext) -> tuple:
    text = f"{concept.name} {concept.slug} {concept.chapter}".lower()
    weak_match = any(point.lower() in text or concept.name in point for point in context.weak_points)
    mastery = context.mastery_scores.get(concept.id)
    low_mastery = mastery is not None and mastery < 0.6
    goal_match = concept.name.lower() in context.goal.lower() or concept.slug.lower() in context.goal.lower()
    difficulty_rank = {"basic": 0, "medium": 1, "advanced": 2}.get(concept.difficulty, 1)
    if context.foundation_level in {"advanced", "practice_oriented"}:
        difficulty_rank = -difficulty_rank
    return (
        0 if low_mastery else 1,
        0 if weak_match else 1,
        0 if goal_match else 1,
        difficulty_rank,
        concept.slug,
    )


def _resource_type_for_context(context: PlannerContext) -> str:
    combined = f"{context.learning_preference} {context.resource_preference} {context.profile_type}".lower()
    if any(marker in combined for marker in ("code", "代码", "编程", "algorithm_practice")):
        return "coding_case"
    if any(marker in combined for marker in ("mind", "思维导图", "visual")):
        return "mind_map"
    if any(marker in combined for marker in ("题", "quiz", "exam", "summary_first", "exam_sprint")):
        return "practice_questions"
    if any(marker in combined for marker in ("拓展", "extended")):
        return "extended_reading"
    return "guided_note"


def _rule_reason(concept: PlannerConcept, context: PlannerContext, resource_type: str) -> str:
    factors = [f"基础水平={context.foundation_level}", f"学习偏好={context.learning_preference}"]
    if context.mastery_scores.get(concept.id, 1.0) < 0.6:
        factors.append("近期测验掌握度偏低")
    if any(point in concept.name or concept.name in point for point in context.weak_points):
        factors.append("匹配画像薄弱点")
    return f"基于{'、'.join(factors)}推荐 {concept.name}，资源类型={resource_type}。"


def _build_planner_messages(
    concepts: list[PlannerConcept],
    relations: list[PlannerRelation],
    context: PlannerContext,
) -> list[dict[str, str]]:
    concept_payload = [concept.__dict__ for concept in concepts]
    pending_ids = {concept.id for concept in concepts}
    relation_payload = [
        relation.__dict__
        for relation in relations
        if relation.target_concept_id in pending_ids and relation.source_concept_id not in context.completed_concept_ids
    ]
    prerequisite_rules = [
        f"concept_id={relation.source_concept_id} 必须出现在 concept_id={relation.target_concept_id} 之前"
        for relation in relations
        if relation.target_concept_id in pending_ids and relation.source_concept_id not in context.completed_concept_ids
    ]
    valid_baseline = [concept.id for concept in _topological_order(concepts, relations, context)]
    context_payload = {
        "goal": context.goal[:300],
        "profile_type": context.profile_type,
        "foundation_level": context.foundation_level,
        "learning_preference": context.learning_preference,
        "available_time": context.available_time,
        "weak_points": context.weak_points[:5],
        "resource_preference": context.resource_preference,
        "mastery_scores": context.mastery_scores,
    }
    return [
        {
            "role": "system",
            "content": (
                "你是 Hybrid 学习路径 Planner。只从给定知识点中选择最值得优先关注的个性化信号，"
                "不要尝试输出完整路径；完整性和 prerequisite 由规则层负责。"
                "最多返回 5 个不重复节点，只返回 JSON object，不输出 Markdown。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"输出 schema：{json.dumps(PLANNER_OUTPUT_SCHEMA, ensure_ascii=False)}\n"
                f"学生上下文：{json.dumps(context_payload, ensure_ascii=False)}\n"
                f"合法候选：{json.dumps(concept_payload, ensure_ascii=False)}\n"
                f"先修约束：{json.dumps(relation_payload, ensure_ascii=False)}\n"
                f"先修约束的自然语言解释：{json.dumps(prerequisite_rules, ensure_ascii=False)}\n"
                f"合法拓扑基线（仅供理解约束）：{json.dumps(valid_baseline, ensure_ascii=False)}\n"
                "只返回 1 至 5 个最重要节点；priority 表示个性化优先信号；"
                "reason 用一句中文解释画像、目标或掌握度依据。"
            ),
        },
    ]


def _compose_hybrid_recommendations(
    signals: list[PlannerOutputItem],
    concepts: list[PlannerConcept],
    relations: list[PlannerRelation],
    context: PlannerContext,
) -> tuple[list[PlannerRecommendation], str | None]:
    eligible = {concept.id: concept for concept in concepts if concept.id not in context.completed_concept_ids}
    signal_by_id: dict[int, PlannerOutputItem] = {}
    signal_order: dict[int, tuple[int, int]] = {}
    ignored_unknown: list[int] = []
    ignored_duplicate: list[int] = []
    for index, signal in enumerate(signals):
        if signal.concept_id not in eligible:
            ignored_unknown.append(signal.concept_id)
            continue
        if signal.concept_id in signal_by_id:
            ignored_duplicate.append(signal.concept_id)
            continue
        signal_by_id[signal.concept_id] = signal
        signal_order[signal.concept_id] = (signal.priority, index)

    ordered = _topological_order(concepts, relations, context, preferred_priority=signal_order)
    default_resource_type = _resource_type_for_context(context)
    recommendations: list[PlannerRecommendation] = []
    for priority, concept in enumerate(ordered, start=1):
        signal = signal_by_id.get(concept.id)
        recommendations.append(
            PlannerRecommendation(
                concept_id=concept.id,
                recommended_resource_type=(
                    signal.recommended_resource_type if signal is not None else default_resource_type
                ),
                reason=(
                    signal.reason if signal is not None else _rule_reason(concept, context, default_resource_type)
                ),
                priority=priority,
            )
        )

    warnings: list[str] = []
    if ignored_unknown:
        warnings.append(f"ignored_unknown_concept_ids={sorted(set(ignored_unknown))}")
    if ignored_duplicate:
        warnings.append(f"ignored_duplicate_concept_ids={sorted(set(ignored_duplicate))}")
    missing_count = len(eligible) - len(signal_by_id)
    if missing_count > 0:
        warnings.append(f"rule_completed_missing_nodes={missing_count}")
    signaled_output_order = [item.concept_id for item in recommendations if item.concept_id in signal_by_id]
    requested_order = [
        concept_id
        for concept_id, _ in sorted(signal_order.items(), key=lambda item: item[1])
    ]
    if signaled_output_order != requested_order:
        warnings.append("rule_repaired_prerequisite_order=true")
    return recommendations, "; ".join(warnings) or None


def _parse_planner_output(content: str) -> PlannerOutput:
    raw = _extract_json_object(content)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Planner response contained invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Planner response must be a JSON object.")
    return PlannerOutput.model_validate(payload)


def _validate_recommendations(
    recommendations: list[PlannerRecommendation],
    concepts: list[PlannerConcept],
    relations: list[PlannerRelation],
    completed_ids: set[int],
) -> None:
    expected_ids = {concept.id for concept in concepts} - completed_ids
    actual_ids = [item.concept_id for item in recommendations]
    if len(actual_ids) != len(set(actual_ids)):
        raise ValueError("Planner output contains duplicate concepts.")
    if set(actual_ids) != expected_ids:
        raise ValueError("Planner output contains unknown or missing concepts.")
    if [item.priority for item in recommendations] != list(range(1, len(recommendations) + 1)):
        raise ValueError("Planner priorities must be consecutive and match output order.")
    positions = {concept_id: index for index, concept_id in enumerate(actual_ids)}
    for relation in relations:
        if relation.target_concept_id not in expected_ids or relation.source_concept_id in completed_ids:
            continue
        if positions[relation.source_concept_id] >= positions[relation.target_concept_id]:
            raise ValueError("Planner output violates a prerequisite relation.")


def _extract_json_object(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        return stripped[start : end + 1]
    raise ValueError("Planner response did not contain a JSON object.")


def _fallback_reason(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return "ValidationError: planner response schema validation failed"
    if isinstance(exc, LLMProviderError):
        return str(exc)[:240]
    if isinstance(exc, ValueError):
        return f"ValueError: {str(exc)[:200]}"
    return f"{type(exc).__name__}: planner request failed"


def _elapsed_ms(started: float) -> int:
    return max(0, int((time.perf_counter() - started) * 1000))
