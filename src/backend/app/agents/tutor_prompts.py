from app.schemas import KnowledgeSearchResult


def build_tutor_messages(
    question: str,
    chunks: list[KnowledgeSearchResult],
    profile_summary: str,
    course_title: str,
) -> list[dict[str, str]]:
    context = "\n".join(
        f"[{index}] source={chunk.source_ref or chunk.chunk_id or 'unknown'} content={chunk.content}"
        for index, chunk in enumerate(chunks, start=1)
    )
    if not context:
        context = "No retrieved course chunks are available."

    return [
        {
            "role": "system",
            "content": (
                "You are a data structures tutor. Answer in Chinese. "
                "Use only the provided course chunks as factual evidence. "
                "When retrieved chunks are present, do not say no course chunks are available. "
                "If chunks partly answer the question, answer the supported parts and list only the missing parts. "
                "If the chunks are insufficient, say what is missing instead of inventing facts. "
                "Only cite source refs listed in the retrieved chunks. "
                "Use citations after key claims, for example [document:4#chunk:3]. "
                "Do not invent source refs. "
                "Use the student profile to adapt difficulty, practice style, and time-budget advice. "
                "Return exactly three Markdown sections: "
                "1. Direct answer; 2. Based on your current profile; 3. Grounded next step. "
                "Keep the answer concise and avoid a generic opening."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Course: {course_title}\n"
                f"Student profile: {profile_summary}\n"
                f"Question: {question}\n"
                f"Retrieved chunks:\n{context}"
            ),
        },
    ]
