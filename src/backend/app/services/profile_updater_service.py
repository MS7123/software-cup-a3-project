import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select

from app.adapters.llm_provider import LLMSettings, build_llm_provider
from app.agents.profile_updater_agents import LLMBackedProfileUpdaterAgent
from app.db.session import session_scope
from app.domain.exceptions import NotFoundError
from app.models import AgentRun, AgentRunStep, StudentProfile
from app.schemas import StudentProfileResponse
from app.services.demo_data_service import DemoDataService
from app.services.profile_builder import normalize_profile_dimensions
from app.schemas import StudentProfileCreate


@dataclass(frozen=True)
class TraceEvidence:
    weak_points: list[str]
    resource_preference: str | None
    learning_preference: str | None
    foundation_level: str | None
    sources: list[dict[str, str | int]]
    analysis_method: str = "rule_based"
    reason: str | None = None
    fallback_reason: str | None = None


class ProfileUpdaterService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url

    def update_from_trace(self, profile_id: int, limit: int = 8) -> StudentProfileResponse:
        DemoDataService(database_url=self.database_url).get_status()
        with session_scope(self.database_url) as session:
            profile = session.get(StudentProfile, profile_id)
            if profile is None:
                raise NotFoundError("Student profile", profile_id)

            runs = session.scalars(
                select(AgentRun)
                .where(AgentRun.student_profile_id == profile_id)
                .order_by(AgentRun.id.desc())
                .limit(limit)
            ).all()
            run_ids = [run.id for run in runs]
            steps = []
            if run_ids:
                steps = session.scalars(
                    select(AgentRunStep)
                    .where(AgentRunStep.agent_run_id.in_(run_ids))
                    .order_by(AgentRunStep.agent_run_id.desc(), AgentRunStep.step_order)
                ).all()

            evidence = self._analyze_steps_with_optional_llm(steps)
            current_preferences = profile.preferences if isinstance(profile.preferences, dict) else {}
            next_preferences = dict(current_preferences)

            if evidence.weak_points:
                next_preferences["weak_points"] = "、".join(evidence.weak_points)
            if evidence.resource_preference:
                next_preferences["resource_preference"] = evidence.resource_preference
                next_preferences["resource"] = evidence.resource_preference
            if evidence.learning_preference:
                next_preferences["learning_preference"] = evidence.learning_preference
                next_preferences["style"] = evidence.learning_preference
            if evidence.foundation_level:
                next_preferences["foundation_level"] = evidence.foundation_level
                profile.level = evidence.foundation_level

            next_preferences["last_profile_update_reason"] = self._build_reason(evidence, len(steps))
            next_preferences["last_profile_update_sources"] = evidence.sources
            profile.preferences = next_preferences

            run = AgentRun(
                run_type="profile_update",
                student_profile_id=profile_id,
                course_id=None,
                status="completed",
                input_summary=f"Analyze recent {len(steps)} AgentRunStep records for profile adaptation.",
                output_summary="ProfileUpdater Agent refreshed dynamic student profile dimensions.",
                final_summary="ProfileUpdater Agent completed profile update from multi-agent trace.",
                completed_at=datetime.utcnow(),
            )
            session.add(run)
            session.flush()
            session.add(
                AgentRunStep(
                    agent_run_id=run.id,
                    agent_type="profile_updater",
                    step_order=1,
                    status="completed",
                    input_summary=f"steps={len(steps)}; sources={len(evidence.sources)}; method={evidence.analysis_method}",
                    output_summary=self._profile_update_summary(evidence),
                    decision_basis=next_preferences["last_profile_update_reason"],
                )
            )
            next_preferences["last_profile_update_agent_run_id"] = run.id
            profile.preferences = next_preferences

            normalized = normalize_profile_dimensions(
                StudentProfileCreate(
                    user_id=profile.user_id,
                    profile_type=profile.profile_type,
                    goal=profile.goal,
                    level=profile.level,
                    preferences=profile.preferences,
                    time_budget=profile.time_budget,
                )
            )
            profile.preferences = normalized.preferences
            session.flush()
            return StudentProfileResponse.model_validate(profile)

    def _analyze_steps(self, steps: list[AgentRunStep]) -> TraceEvidence:
        weak_points: list[str] = []
        sources: list[dict[str, str | int]] = []
        resource_preference: str | None = None
        learning_preference: str | None = None
        foundation_level: str | None = None

        for step in steps:
            text = " ".join([step.input_summary, step.output_summary, step.decision_basis]).lower()
            for label in self._concept_labels(text):
                if label not in weak_points:
                    weak_points.append(label)

            if step.agent_type == "resource":
                inferred_resource = self._resource_preference(text)
                if inferred_resource:
                    resource_preference = inferred_resource
                inferred_learning = self._learning_preference(text)
                if inferred_learning:
                    learning_preference = inferred_learning

            if step.agent_type == "tutor":
                for label in self._concept_labels(step.input_summary.lower()):
                    if label not in weak_points:
                        weak_points.append(label)

            if step.agent_type == "evaluator":
                score = self._score_from_text(text)
                if score is not None:
                    foundation_level = "intermediate" if score >= 0.8 else "beginner"

            if len(sources) < 8:
                sources.append(
                    {
                        "agent_run_id": step.agent_run_id,
                        "agent_type": step.agent_type,
                        "summary": step.output_summary[:120],
                    }
                )

        return TraceEvidence(
            weak_points=weak_points,
            resource_preference=resource_preference,
            learning_preference=learning_preference,
            foundation_level=foundation_level,
            sources=sources,
        )

    def _analyze_steps_with_optional_llm(self, steps: list[AgentRunStep]) -> TraceEvidence:
        rule_based = self._analyze_steps(steps)
        settings = LLMSettings.from_env()
        provider = build_llm_provider(settings, purpose="profile_updater")
        if provider is None or not steps:
            return rule_based

        try:
            analysis = LLMBackedProfileUpdaterAgent(provider).analyze(self._trace_payload(steps))
        except Exception as exc:
            return TraceEvidence(
                weak_points=rule_based.weak_points,
                resource_preference=rule_based.resource_preference,
                learning_preference=rule_based.learning_preference,
                foundation_level=rule_based.foundation_level,
                sources=rule_based.sources,
                analysis_method="rule_based",
                fallback_reason=self._fallback_reason(exc),
            )

        return TraceEvidence(
            weak_points=analysis.weak_points,
            resource_preference=analysis.resource_preference,
            learning_preference=analysis.learning_preference,
            foundation_level=analysis.foundation_level,
            sources=rule_based.sources,
            analysis_method="llm",
            reason=analysis.reason,
        )

    def _trace_payload(self, steps: list[AgentRunStep]) -> list[dict[str, str | int]]:
        payload = []
        for step in steps[:8]:
            payload.append(
                {
                    "agent_run_id": step.agent_run_id,
                    "agent_type": step.agent_type,
                    "input_summary": step.input_summary[:240],
                    "output_summary": step.output_summary[:360],
                    "decision_basis": step.decision_basis[:360],
                }
            )
        return payload

    def _concept_labels(self, text: str) -> list[str]:
        labels = []
        for keyword, label in [
            ("复杂度", "复杂度分析"),
            ("链表", "链表"),
            ("栈", "栈/队列"),
            ("队列", "栈/队列"),
            ("树", "二叉树遍历"),
            ("bfs", "BFS/DFS"),
            ("dfs", "BFS/DFS"),
            ("图", "BFS/DFS"),
        ]:
            if keyword in text and label not in labels:
                labels.append(label)
        return labels

    def _resource_preference(self, text: str) -> str | None:
        if "代码实操" in text or "coding_case" in text:
            return "代码实操案例"
        if "练习题" in text or "practice_questions" in text:
            return "练习题"
        if "思维导图" in text or "mind_map" in text:
            return "思维导图"
        if "拓展阅读" in text or "extended_reading" in text:
            return "拓展阅读"
        if "讲解文档" in text or "guided_note" in text:
            return "讲解文档"
        return None

    def _learning_preference(self, text: str) -> str | None:
        if "代码实操" in text or "coding_case" in text:
            return "code_driven"
        if "练习题" in text or "practice_questions" in text:
            return "worked_examples"
        if "讲解文档" in text or "guided_note" in text:
            return "step_by_step"
        return None

    def _score_from_text(self, text: str) -> float | None:
        match = re.search(r"评分\s+([0-9]+(?:\.[0-9]+)?)", text)
        if not match:
            return None
        return float(match.group(1))

    def _build_reason(self, evidence: TraceEvidence, step_count: int) -> str:
        if step_count == 0:
            return "暂无可分析的 Agent trace，画像保持当前状态。"
        if evidence.analysis_method == "llm":
            return f"LLM ProfileUpdater 基于最近 {step_count} 个 Agent step 更新画像：{evidence.reason}"
        parts = [f"基于最近 {step_count} 个 Agent step 更新画像"]
        if evidence.weak_points:
            parts.append(f"识别关注知识点：{'、'.join(evidence.weak_points)}")
        if evidence.resource_preference:
            parts.append(f"资源偏好调整为：{evidence.resource_preference}")
        if evidence.foundation_level:
            parts.append(f"基础水平调整为：{evidence.foundation_level}")
        if evidence.fallback_reason:
            parts.append(f"LLM 分析不可用，已回退到 rule-based：{evidence.fallback_reason}")
        return "；".join(parts)

    def _profile_update_summary(self, evidence: TraceEvidence) -> str:
        changes = []
        if evidence.weak_points:
            changes.append(f"weak_points={','.join(evidence.weak_points)}")
        if evidence.resource_preference:
            changes.append(f"resource_preference={evidence.resource_preference}")
        if evidence.learning_preference:
            changes.append(f"learning_preference={evidence.learning_preference}")
        if evidence.foundation_level:
            changes.append(f"foundation_level={evidence.foundation_level}")
        if not changes:
            changes.append("no dimension change; profile context preserved")
        return f"ProfileUpdater Agent method={evidence.analysis_method}; " + "; ".join(changes)

    def _fallback_reason(self, exc: Exception) -> str:
        if str(exc):
            return f"{type(exc).__name__}: {str(exc)[:160]}"
        return type(exc).__name__
