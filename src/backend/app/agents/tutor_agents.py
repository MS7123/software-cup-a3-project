import time
from typing import Protocol

from app.adapters.protocols import LLMProvider
from app.adapters.llm_provider import LLMProviderError
from app.agents.rule_based_agents import RuleBasedTutorAgent, TutorAgentResult
from app.agents.tutor_prompts import build_tutor_messages
from app.schemas import KnowledgeSearchResult
from app.services.citation_service import source_ref_payload, validate_citations


class TutorAgent(Protocol):
    def answer(
        self,
        question: str,
        chunks: list[KnowledgeSearchResult],
        profile_summary: str = "",
        course_title: str = "",
    ) -> TutorAgentResult:
        raise NotImplementedError


class LLMBackedTutorAgent:
    def __init__(
        self,
        provider: LLMProvider,
        fallback_agent: RuleBasedTutorAgent | None = None,
        fallback_mode: str = "rule_based",
        provider_name: str = "openai_compatible",
        model: str = "",
    ) -> None:
        self.provider = provider
        self.fallback_agent = fallback_agent or RuleBasedTutorAgent()
        self.fallback_mode = fallback_mode if fallback_mode in {"rule_based", "error"} else "rule_based"
        self.provider_name = provider_name
        self.model = model

    def answer(
        self,
        question: str,
        chunks: list[KnowledgeSearchResult],
        profile_summary: str = "",
        course_title: str = "",
    ) -> TutorAgentResult:
        started = time.perf_counter()
        source_refs = [source_ref_payload(chunk) for chunk in chunks]
        if not chunks:
            fallback = self.fallback_agent.answer(question, chunks, profile_summary, course_title)
            return TutorAgentResult(
                answer=fallback.answer,
                source_refs=fallback.source_refs,
                input_summary=fallback.input_summary,
                output_summary="No RAG evidence was retrieved; returned the rule-based grounded limitation without calling LLM.",
                decision_basis=(
                    f"{fallback.decision_basis} "
                    "Fallback reason: No retrieved course chunks are available."
                ),
                execution_mode="rule_based_fallback",
                provider=self.provider_name,
                model=self.model,
                fallback_used=True,
                fallback_reason="No retrieved course chunks are available.",
                duration_ms=_elapsed_ms(started),
            )
        try:
            result = self.provider.generate(
                build_tutor_messages(question, chunks, profile_summary, course_title),
            )
            if chunks and _contradicts_retrieved_context(result.content):
                fallback = self.fallback_agent.answer(question, chunks, profile_summary, course_title)
                return TutorAgentResult(
                    answer=fallback.answer,
                    source_refs=fallback.source_refs,
                    input_summary=fallback.input_summary,
                    output_summary="LLM provider returned an ungrounded no-context answer, fell back to rule-based tutor answer.",
                    decision_basis=(
                        f"{fallback.decision_basis} "
                        "Fallback reason: LLM answer contradicted non-empty retrieved chunks."
                    ),
                    execution_mode="rule_based_fallback",
                    provider=self.provider_name,
                    model=self.model,
                    fallback_used=True,
                    fallback_reason="LLM answer contradicted non-empty retrieved chunks.",
                    duration_ms=_elapsed_ms(started),
                )
            grounded_answer = _ensure_grounded_citations(result.content, source_refs)
            provider = str(result.metadata.get("provider") or self.provider_name)
            model = str(result.metadata.get("model") or self.model)
            return TutorAgentResult(
                answer=grounded_answer,
                source_refs=source_refs,
                input_summary=f"使用真实 LLM 回答学生问题：{question}",
                output_summary="LLM provider 返回 grounded tutor answer，并通过引用白名单校验。",
                decision_basis=(
                    "通过 LLMProvider adapter 调用 OpenAI-compatible provider，并使用 KnowledgeBaseService "
                    "返回的 chunk 作为回答依据；缺失的内联引用仅从 Retriever source_ref 白名单补充。"
                ),
                execution_mode="llm",
                provider=provider,
                model=model,
                duration_ms=_elapsed_ms(started),
            )
        except Exception as exc:
            reason = _fallback_reason(exc)
            if self.fallback_mode == "error":
                raise LLMProviderError(reason) from exc
            fallback = self.fallback_agent.answer(question, chunks, profile_summary, course_title)
            return TutorAgentResult(
                answer=fallback.answer,
                source_refs=fallback.source_refs,
                input_summary=fallback.input_summary,
                output_summary="LLM provider 不可用，已回退到 rule-based tutor answer。",
                decision_basis=f"{fallback.decision_basis} Fallback reason: {reason}.",
                execution_mode="rule_based_fallback",
                provider=self.provider_name,
                model=self.model,
                fallback_used=True,
                fallback_reason=reason,
                duration_ms=_elapsed_ms(started),
            )


def _fallback_reason(exc: Exception) -> str:
    if isinstance(exc, LLMProviderError):
        return str(exc)
    if str(exc):
        return f"{type(exc).__name__}: {str(exc)[:240]}"
    return type(exc).__name__


def _contradicts_retrieved_context(answer: str) -> bool:
    normalized = answer.lower()
    no_context_markers = [
        "no retrieved course chunks",
        "no retrieved chunks",
        "no course chunks",
        "insufficient retrieved",
        "\u6ca1\u6709\u4efb\u4f55",
        "\u6ca1\u6709\u68c0\u7d22\u5230",
        "\u65e0\u6cd5\u4f9d\u636e\u8bfe\u7a0b\u6750\u6599",
        "\u8d44\u6599\u4e0d\u8db3",
        "\u7247\u6bb5\u4e0d\u8db3",
    ]
    return any(marker in normalized for marker in no_context_markers)


def _ensure_grounded_citations(answer: str, source_refs: list[dict]) -> str:
    citation_check = validate_citations(answer, source_refs)
    fake_refs = citation_check["fake_source_refs"]
    if fake_refs:
        raise ValueError(f"LLM answer cited unknown source refs: {', '.join(fake_refs[:3])}")
    if not citation_check["missing_citation"]:
        return answer

    verified_refs = citation_check["allowed_source_refs"]
    citations = " ".join(f"[{source_ref}]" for source_ref in verified_refs)
    return f"{answer.rstrip()}\n\n资料依据：{citations}"


def _elapsed_ms(started: float) -> int:
    return max(0, round((time.perf_counter() - started) * 1000))
