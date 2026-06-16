import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.main import create_app
from app.models import Course


SAMPLE_DIR = Path(__file__).resolve().parents[1] / "data" / "samples" / "rag-import"


class DocumentUploadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "document-upload.sqlite3"
        self.database_url = f"sqlite:///{self.database_path.as_posix()}"
        self.previous_database_url = os.environ.get("APP_DATABASE_URL")
        self.previous_embedding_enabled = os.environ.get("RAG_EMBEDDING_ENABLED")
        os.environ["APP_DATABASE_URL"] = self.database_url
        os.environ["RAG_EMBEDDING_ENABLED"] = "false"
        Base.metadata.create_all(get_engine(self.database_url))
        self.course_id = self._seed_course("Upload Course")

    def tearDown(self) -> None:
        get_engine().dispose()
        get_engine(self.database_url).dispose()
        get_engine.cache_clear()
        if self.previous_database_url is None:
            os.environ.pop("APP_DATABASE_URL", None)
        else:
            os.environ["APP_DATABASE_URL"] = self.previous_database_url
        if self.previous_embedding_enabled is None:
            os.environ.pop("RAG_EMBEDDING_ENABLED", None)
        else:
            os.environ["RAG_EMBEDDING_ENABLED"] = self.previous_embedding_enabled
        self.temp_dir.cleanup()

    def test_upload_text_markdown_pdf_and_docx_create_documents(self) -> None:
        with TestClient(create_app()) as client:
            cases = [
                ("note.txt", b"BFS queue and DFS stack upload text.", "text/plain", "plain_text", "text"),
                ("note.md", b"# BFS and DFS\nBFS queue, DFS stack.", "text/markdown", "markdown", "markdown"),
                (
                    "rag-import-bfs-dfs-test.pdf",
                    (SAMPLE_DIR / "rag-import-bfs-dfs-test.pdf").read_bytes(),
                    "application/pdf",
                    "pdf",
                    "pdf",
                ),
                (
                    "rag-import-bfs-dfs-test.docx",
                    (SAMPLE_DIR / "rag-import-bfs-dfs-test.docx").read_bytes(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "docx",
                    "docx",
                ),
            ]

            for filename, content, content_type, parser_name, source_type in cases:
                response = client.post(
                    f"/api/v1/courses/{self.course_id}/documents/upload",
                    files={"file": (filename, content, content_type)},
                    data={"title": filename},
                )
                self.assertEqual(response.status_code, 200, response.text)
                payload = response.json()
                self.assertGreaterEqual(payload["chunk_count"], 1)
                self.assertEqual(payload["document"]["parser_name"], parser_name)
                self.assertEqual(payload["document"]["source_type"], source_type)
                self.assertEqual(payload["document"]["file_name"], filename)
                self.assertEqual(payload["document"]["visibility"], "course")

    def test_upload_unsupported_and_oversized_files_return_400(self) -> None:
        with TestClient(create_app()) as client:
            unsupported = client.post(
                f"/api/v1/courses/{self.course_id}/documents/upload",
                files={"file": ("bad.exe", b"not a document", "application/octet-stream")},
            )
            self.assertEqual(unsupported.status_code, 400)
            self.assertIn("Unsupported document", unsupported.text)

            too_large = client.post(
                f"/api/v1/courses/{self.course_id}/documents/upload",
                files={"file": ("large.txt", b"x" * (1024 * 1024 + 1), "text/plain")},
            )
            self.assertEqual(too_large.status_code, 400)
            self.assertIn("too large", too_large.text)

    def test_json_paste_ingestion_still_works(self) -> None:
        with TestClient(create_app()) as client:
            response = client.post(
                f"/api/v1/courses/{self.course_id}/documents",
                json={
                    "title": "paste.md",
                    "source_type": "markdown",
                    "content": "# Paste path\nBFS queue and DFS stack.",
                },
            )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["document"]["source_type"], "markdown")

    def _seed_course(self, title: str) -> int:
        session = get_session_factory(self.database_url)()
        try:
            course = Course(title=title, description="docs", is_demo=False)
            session.add(course)
            session.commit()
            return course.id
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
