from dataclasses import dataclass
from typing import Any

from app.schemas import KnowledgeSearchResult


@dataclass(frozen=True)
class ResourceAgentResult:
    content: str
    source_refs: list[dict[str, Any]]
    input_summary: str
    output_summary: str
    decision_basis: str


@dataclass(frozen=True)
class TutorAgentResult:
    answer: str
    source_refs: list[dict[str, Any]]
    input_summary: str
    output_summary: str
    decision_basis: str


@dataclass(frozen=True)
class QuizAgentResult:
    question: str
    answer: str
    explanation: str
    concept_tags: list[str]
    input_summary: str
    output_summary: str
    decision_basis: str


@dataclass(frozen=True)
class EvaluatorAgentResult:
    score: float
    feedback: str
    mastery_updates: list[dict[str, Any]]
    input_summary: str
    output_summary: str
    decision_basis: str


class RuleBasedResourceAgent:
    def generate(
        self,
        concept_name: str,
        objective: str,
        resource_type: str,
        chunks: list[KnowledgeSearchResult],
    ) -> ResourceAgentResult:
        source_refs = self._source_refs(chunks)
        evidence = chunks[0].content if chunks else "暂无可用资料片段。"
        content = (
            f"【{resource_type}】{concept_name}\n"
            f"学习目标：{objective}\n"
            f"核心讲解：{evidence}\n"
            f"练习建议：先复述概念，再完成 1 道基础题和 1 道应用题。"
        )
        return ResourceAgentResult(
            content=content,
            source_refs=source_refs,
            input_summary=f"为知识点 {concept_name} 生成 {resource_type} 资源。",
            output_summary=f"生成包含讲解、依据和练习建议的 {resource_type}。",
            decision_basis="基于学习路径节点目标和课程资料 chunk 生成资源，避免无依据扩写。",
        )

    def _source_refs(self, chunks: list[KnowledgeSearchResult]) -> list[dict[str, Any]]:
        return [
            {"chunk_id": chunk.chunk_id, "source_ref": chunk.source_ref, "score": chunk.score}
            for chunk in chunks
        ]


class RuleBasedTutorAgent:
    def answer(self, question: str, chunks: list[KnowledgeSearchResult]) -> TutorAgentResult:
        source_refs = [
            {"chunk_id": chunk.chunk_id, "source_ref": chunk.source_ref, "score": chunk.score}
            for chunk in chunks
        ]
        if chunks:
            evidence = chunks[0].content
            answer = f"根据课程资料：{evidence} 针对你的问题“{question}”，建议先抓住资料中的定义和适用场景，再做一个小例子验证理解。"
        else:
            answer = f"暂未检索到足够资料回答“{question}”，建议先加载数据结构 demo data 或补充课程资料。"
        return TutorAgentResult(
            answer=answer,
            source_refs=source_refs,
            input_summary=f"回答学生问题：{question}",
            output_summary="返回基于课程资料片段的回答和引用线索。",
            decision_basis="优先使用 KnowledgeBaseService 返回的 chunk 和 source_ref 形成 grounded answer。",
        )


class RuleBasedQuizAgent:
    def generate(self, concept_name: str, difficulty: str, chunk: KnowledgeSearchResult | None) -> QuizAgentResult:
        context = chunk.content if chunk else f"{concept_name} 是当前数据结构 MVP 知识点。"
        question = f"【{difficulty}】请说明{concept_name}的核心思想，并结合一个数据结构场景说明其作用。"
        answer = f"应围绕{concept_name}的定义、适用场景和基本操作说明。"
        explanation = f"解析依据：{context}"
        return QuizAgentResult(
            question=question,
            answer=answer,
            explanation=explanation,
            concept_tags=[concept_name],
            input_summary=f"为知识点 {concept_name} 生成 {difficulty} 难度题目。",
            output_summary="生成 1 道包含答案、解析和知识点标签的小测题。",
            decision_basis="题目绑定 concept_id 和 difficulty，并使用课程资料 chunk 作为解析依据。",
        )


class RuleBasedEvaluatorAgent:
    def evaluate(self, expected_answer: str, answers: dict[str, Any], concept_id: int) -> EvaluatorAgentResult:
        submitted_text = " ".join(str(value) for value in answers.values()).strip()
        expected_terms = {term for term in expected_answer.replace("，", " ").replace("。", " ").split() if term}
        matched_terms = {term for term in expected_terms if term in submitted_text}
        score = 1.0 if submitted_text and matched_terms else (0.6 if submitted_text else 0.0)
        if score >= 1.0:
            feedback = "回答覆盖了关键点，建议继续做应用题巩固。"
        elif score > 0:
            feedback = "回答有一定相关性，但关键概念或应用场景不完整，建议回看讲解并补充例子。"
        else:
            feedback = "未检测到有效作答，建议先复习该知识点的定义和基本应用。"
        mastery_score = min(1.0, max(0.0, score))
        return EvaluatorAgentResult(
            score=score,
            feedback=feedback,
            mastery_updates=[
                {
                    "concept_id": concept_id,
                    "mastery_score": mastery_score,
                    "evidence": {"matched_terms": sorted(matched_terms), "submitted_length": len(submitted_text)},
                }
            ],
            input_summary=f"评价 concept_id={concept_id} 的一次作答。",
            output_summary=f"评分 {score:.2f}，生成反馈和掌握度更新建议。",
            decision_basis="基于标准答案关键词覆盖和作答是否为空做 MVP rule-based 评价。",
        )
