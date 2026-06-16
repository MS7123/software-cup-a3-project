from io import BytesIO
import re

from docx import Document as DocxDocument
from pypdf import PdfReader


class UnsupportedDocumentTypeError(ValueError):
    pass


class PlainTextDocumentParser:
    parser_name = "plain_text"

    def parse_content(self, content: str) -> list[str]:
        normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []
        return [normalized]

    def parse_bytes(self, content: bytes, filename: str | None = None) -> list[str]:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Text file must be UTF-8 encoded.") from exc
        return self.parse_content(text)


class MarkdownDocumentParser(PlainTextDocumentParser):
    parser_name = "markdown"

    def parse_content(self, content: str) -> list[str]:
        normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []
        without_fences = re.sub(r"```[\s\S]*?```", lambda match: match.group(0).strip(), normalized)
        sections = [section.strip() for section in re.split(r"\n(?=#{1,6}\s+)", without_fences) if section.strip()]
        return sections or [normalized]


class PdfDocumentParser(PlainTextDocumentParser):
    parser_name = "pdf"

    def parse_bytes(self, content: bytes, filename: str | None = None) -> list[str]:
        reader = PdfReader(BytesIO(content))
        sections: list[str] = []
        for index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                sections.append(f"[Page {index}]\n{text}")
        if not sections:
            raise ValueError("No extractable text found. OCR is not supported in the current demo mode.")
        return sections


class WordDocumentParser(PlainTextDocumentParser):
    parser_name = "docx"

    def parse_bytes(self, content: bytes, filename: str | None = None) -> list[str]:
        document = DocxDocument(BytesIO(content))
        sections: list[str] = []
        current: list[str] = []

        def flush() -> None:
            if current:
                text = "\n".join(item for item in current if item.strip()).strip()
                if text:
                    sections.append(text)
                current.clear()

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            style = paragraph.style.name.lower() if paragraph.style and paragraph.style.name else ""
            if style.startswith("heading") and current:
                flush()
            current.append(text)
        flush()

        for table in document.tables:
            rows: list[str] = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                if any(cells):
                    rows.append(" | ".join(cells))
            if rows:
                sections.append("\n".join(rows))

        if not sections:
            raise ValueError("No extractable text found in the Word document.")
        return sections


def build_document_parser(source_type: str) -> PlainTextDocumentParser:
    normalized = source_type.strip().lower()
    if normalized in {"markdown", "md", "text/markdown"}:
        return MarkdownDocumentParser()
    if normalized in {"text", "txt", "plain_text", "text/plain"}:
        return PlainTextDocumentParser()
    if normalized in {"pdf", "application/pdf"}:
        return PdfDocumentParser()
    if normalized in {
        "docx",
        "word",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }:
        return WordDocumentParser()
    raise UnsupportedDocumentTypeError(f"Unsupported document source_type: {source_type}")


def infer_source_type(filename: str, content_type: str | None = None) -> str:
    normalized_type = (content_type or "").strip().lower()
    if normalized_type in {
        "text/plain",
        "text/markdown",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }:
        return normalized_type

    suffix = filename.rsplit(".", 1)[-1].strip().lower() if "." in filename else ""
    if suffix in {"txt", "text"}:
        return "text"
    if suffix in {"md", "markdown"}:
        return "markdown"
    if suffix == "pdf":
        return "pdf"
    if suffix == "docx":
        return "docx"
    raise UnsupportedDocumentTypeError(f"Unsupported document file type: {filename}")
