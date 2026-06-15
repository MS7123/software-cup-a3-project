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
                "Cite source refs inline using the source value shown for each chunk. "
                "Keep the answer concise and include practical next-step advice."
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
