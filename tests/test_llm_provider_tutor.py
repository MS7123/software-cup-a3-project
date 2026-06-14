import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import URLError

from fastapi.testclient import TestClient

from app.adapters.llm_provider import LLMProviderError, LLMSettings, OpenAICompatibleLLMProvider
from app.adapters.protocols import LLMResult
from app.db.session import get_engine
from app.main import create_app
from app.agents.rule_based_agents import RuleBasedTutorAgent
from app.agents.tutor_agents import LLMBackedTutorAgent
from app.agents.tutor_factory import build_tutor_agent
from app.schemas import KnowledgeSearchResult


class FakeProvider:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def generate(self, messages, response_schema=None) -> LLMResult:
        if self.fail:
            raise RuntimeError("provider unavailable")
        return LLMResult(content="这是来自模拟 LLM provider 的回答。", metadata={"provider": "fake"})


class OpenAICompatibleHandler(BaseHTTPRequestHandler):
    request_payload: dict | None = None
    auth_header: str | None = None

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        OpenAICompatibleHandler.auth_header = self.headers.get("Authorization")
        OpenAICompatibleHandler.request_payload = json.loads(self.rfile.read(length).decode("utf-8"))
        body = {
            "choices": [
                {
                    "message": {
                        "content": "这是来自本地 fake OpenAI-compatible endpoint 的回答。"
                    }
                }
            ]
        }
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args) -> None:
        return


class OpenAICompatibleErrorHandler(BaseHTTPRequestHandler):
    request_path: str | None = None

    def do_POST(self) -> None:
        OpenAICompatibleErrorHandler.request_path = self.path
        body = {"error": {"message": "Model Not Found", "code": "model_not_found"}}
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args) -> None:
        return


class LLMProviderTutorTests(unittest.TestCase):
    def test_openai_compatible_provider_uses_contract_without_exposing_key(self) -> None:
        server = HTTPServer(("127.0.0.1", 0), OpenAICompatibleHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            settings = LLMSettings(
                provider="openai_compatible",
                base_url=f"http://127.0.0.1:{server.server_port}",
                api_key="test-secret",
                model="deepseek-v4-flash",
                timeout_seconds=2,
                max_retries=0,
                fallback_mode="rule_based",
                enable_for_tutor=True,
                bypass_proxy=True,
            )
            result = OpenAICompatibleLLMProvider(settings).generate([{"role": "user", "content": "hello"}])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertIn("fake OpenAI-compatible", result.content)
        self.assertEqual(result.metadata["provider"], "openai_compatible")
        self.assertEqual(result.metadata["model"], "deepseek-v4-flash")
        self.assertNotIn("test-secret", str(result.metadata))
        self.assertEqual(OpenAICompatibleHandler.auth_header, "Bearer test-secret")
        self.assertEqual(OpenAICompatibleHandler.request_payload["model"], "deepseek-v4-flash")

    def test_provider_error_summary_includes_http_status_and_safe_message(self) -> None:
        server = HTTPServer(("127.0.0.1", 0), OpenAICompatibleErrorHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            settings = LLMSettings(
                provider="openai_compatible",
                base_url=f"http://127.0.0.1:{server.server_port}/chat/completions",
                api_key="test-secret",
                model="wrong-model",
                timeout_seconds=2,
                max_retries=0,
                fallback_mode="rule_based",
                enable_for_tutor=True,
                bypass_proxy=True,
            )
            with self.assertRaises(LLMProviderError) as context:
                OpenAICompatibleLLMProvider(settings).generate([{"role": "user", "content": "hello"}])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        message = str(context.exception)
        self.assertIn("HTTP 404", message)
        self.assertIn("Model Not Found", message)
        self.assertNotIn("test-secret", message)
        self.assertEqual(OpenAICompatibleErrorHandler.request_path, "/chat/completions")

    def test_llm_tutor_fallback_includes_url_error_reason(self) -> None:
        class UrlErrorProvider:
            def generate(self, messages, response_schema=None) -> LLMResult:
                raise URLError("network unreachable")

        agent = LLMBackedTutorAgent(UrlErrorProvider())
        result = agent.answer("你是谁？", [_chunk()])
        self.assertIn("Fallback reason", result.decision_basis)
        self.assertIn("network unreachable", result.decision_basis)
        self.assertNotIn("Bearer", result.decision_basis)

    def test_tutor_factory_defaults_to_rule_based_without_remote_config(self) -> None:
        agent = build_tutor_agent(LLMSettings(provider="rule_based"))
        self.assertIsInstance(agent, RuleBasedTutorAgent)

    def test_llm_tutor_agent_uses_provider_answer(self) -> None:
        agent = LLMBackedTutorAgent(FakeProvider())
        result = agent.answer("BFS 和 DFS 有什么不同？", [_chunk()])
        self.assertIn("模拟 LLM provider", result.answer)
        self.assertTrue(result.source_refs)
        self.assertIn("LLMProvider adapter", result.decision_basis)

    def test_llm_tutor_agent_falls_back_when_provider_fails(self) -> None:
        agent = LLMBackedTutorAgent(FakeProvider(fail=True))
        result = agent.answer("复杂度分析有什么用？", [_chunk()])
        self.assertIn("根据课程资料", result.answer)
        self.assertIn("Fallback reason", result.decision_basis)
        self.assertIn("rule-based", result.output_summary)

    def test_llm_tutor_agent_raises_when_fallback_mode_is_error(self) -> None:
        agent = LLMBackedTutorAgent(FakeProvider(fail=True), fallback_mode="error")
        with self.assertRaises(LLMProviderError) as context:
            agent.answer("复杂度分析有什么用？", [_chunk()])

        self.assertIn("provider unavailable", str(context.exception))

    def test_tutor_api_records_fallback_step_when_provider_fails(self) -> None:
        server = HTTPServer(("127.0.0.1", 0), OpenAICompatibleErrorHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(temp_dir.name) / "llm-fallback-api-test.sqlite3"
        database_url = f"sqlite:///{database_path.as_posix()}"
        env_keys = [
            "APP_DATABASE_URL",
            "AUTH_SECRET_KEY",
            "LLM_PROVIDER",
            "LLM_BASE_URL",
            "LLM_API_KEY",
            "LLM_MODEL",
            "LLM_TIMEOUT_SECONDS",
            "LLM_MAX_RETRIES",
            "LLM_FALLBACK_MODE",
            "LLM_ENABLE_FOR_TUTOR",
            "LLM_BYPASS_PROXY",
        ]
        previous_env = {key: os.environ.get(key) for key in env_keys}
        try:
            os.environ["APP_DATABASE_URL"] = database_url
            os.environ["AUTH_SECRET_KEY"] = "test-secret-key"
            os.environ["LLM_PROVIDER"] = "openai_compatible"
            os.environ["LLM_BASE_URL"] = f"http://127.0.0.1:{server.server_port}"
            os.environ["LLM_API_KEY"] = "integration-secret"
            os.environ["LLM_MODEL"] = "deepseek-v4-flash"
            os.environ["LLM_TIMEOUT_SECONDS"] = "2"
            os.environ["LLM_MAX_RETRIES"] = "0"
            os.environ["LLM_FALLBACK_MODE"] = "rule_based"
            os.environ["LLM_ENABLE_FOR_TUTOR"] = "true"
            os.environ["LLM_BYPASS_PROXY"] = "true"

            with TestClient(create_app()) as client:
                # Register a test user for auth
                auth_resp = client.post(
                    "/api/v1/auth/register",
                    json={"username": "testuser", "password": "testpass123"},
                )
                token = auth_resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                demo = client.post("/api/v1/demo-data/load", headers=headers).json()["demo_data"]
                profile = client.get("/api/v1/student-profiles", headers=headers).json()[0]
                tutor = client.post(
                    "/api/v1/tutor/ask",
                    headers=headers,
                    json={
                        "student_profile_id": profile["id"],
                        "course_id": demo["course_id"],
                        "question": "复杂度分析有什么用？",
                    },
                )

                self.assertEqual(tutor.status_code, 200)
                tutor_body = tutor.json()
                self.assertEqual(set(tutor_body.keys()), {"answer", "source_refs", "agent_run_id"})
                self.assertIn("根据课程资料", tutor_body["answer"])
                self.assertTrue(tutor_body["source_refs"])

                run = client.get(f"/api/v1/agent-runs/{tutor_body['agent_run_id']}", headers=headers)
                self.assertEqual(run.status_code, 200)
                run_body = run.json()
                self.assertEqual(run_body["status"], "completed")
                self.assertEqual(run_body["steps"][0]["agent_type"], "tutor")
                self.assertIn("回退到 rule-based", run_body["steps"][0]["output_summary"])
                self.assertIn("Fallback reason", run_body["steps"][0]["decision_basis"])
                self.assertIn("HTTP 404", run_body["steps"][0]["decision_basis"])
                self.assertNotIn("integration-secret", json.dumps(run_body, ensure_ascii=False))
        finally:
            get_engine().dispose()
            get_engine(database_url).dispose()
            get_engine.cache_clear()
            for key, value in previous_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            temp_dir.cleanup()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


def _chunk() -> KnowledgeSearchResult:
    return KnowledgeSearchResult(
        chunk_id=1,
        content="BFS 适合按层遍历，DFS 适合沿路径深入搜索。",
        score=1.0,
        source_ref="demo.md#graph-search",
        metadata={"concept_slug": "bfs-dfs"},
    )


if __name__ == "__main__":
    unittest.main()
