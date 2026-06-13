import re


class PlainTextDocumentParser:
    parser_name = "plain_text"

    def parse_content(self, content: str) -> list[str]:
        normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []
        return [normalized]


class MarkdownDocumentParser(PlainTextDocumentParser):
    parser_name = "markdown"

    def parse_content(self, content: str) -> list[str]:
        normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []
        without_fences = re.sub(r"```[\s\S]*?```", lambda match: match.group(0).strip(), normalized)
        sections = [section.strip() for section in re.split(r"\n(?=#{1,6}\s+)", without_fences) if section.strip()]
        return sections or [normalized]


def build_document_parser(source_type: str) -> PlainTextDocumentParser:
    normalized = source_type.strip().lower()
    if normalized in {"markdown", "md", "text/markdown"}:
        return MarkdownDocumentParser()
    if normalized in {"text", "txt", "plain_text", "text/plain"}:
        return PlainTextDocumentParser()
    raise ValueError(f"Unsupported document source_type: {source_type}")
