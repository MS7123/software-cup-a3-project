import json
import http.client
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.adapters.protocols import LLMProvider, LLMResult


class LLMProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMSettings:
    provider: str = "rule_based"
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    timeout_seconds: float = 20.0
    max_retries: int = 0
    fallback_mode: str = "rule_based"
    enable_for_tutor: bool = False
    enable_for_profile_updater: bool = False
    enable_for_resource: bool = False
    enable_for_evaluator: bool = False
    enable_for_profile_builder: bool = False
    enable_for_planner: bool = False
    enable_for_quiz: bool = False
    bypass_proxy: bool = False

    @classmethod
    def from_env(cls) -> "LLMSettings":
        return cls(
            provider=os.getenv("LLM_PROVIDER", "rule_based").strip() or "rule_based",
            base_url=os.getenv("LLM_BASE_URL", "").strip(),
            api_key=os.getenv("LLM_API_KEY", "").strip(),
            model=os.getenv("LLM_MODEL", "").strip(),
            timeout_seconds=_float_from_env("LLM_TIMEOUT_SECONDS", 20.0),
            max_retries=max(0, _int_from_env("LLM_MAX_RETRIES", 0)),
            fallback_mode=os.getenv("LLM_FALLBACK_MODE", "rule_based").strip() or "rule_based",
            enable_for_tutor=_bool_from_env("LLM_ENABLE_FOR_TUTOR", False),
            enable_for_profile_updater=_bool_from_env("LLM_ENABLE_FOR_PROFILE_UPDATER", False),
            enable_for_resource=_bool_from_env("LLM_ENABLE_FOR_RESOURCE", False),
            enable_for_evaluator=_bool_from_env("LLM_ENABLE_FOR_EVALUATOR", False),
            enable_for_profile_builder=_bool_from_env("LLM_ENABLE_FOR_PROFILE_BUILDER", False),
            enable_for_planner=_bool_from_env("LLM_ENABLE_FOR_PLANNER", False),
            enable_for_quiz=_bool_from_env("LLM_ENABLE_FOR_QUIZ", False),
            bypass_proxy=_bool_from_env("LLM_BYPASS_PROXY", False),
        )

    def can_call_remote(self, purpose: str = "tutor") -> bool:
        if purpose == "profile_updater":
            enabled = self.enable_for_profile_updater
        elif purpose == "resource":
            enabled = self.enable_for_resource
        elif purpose == "evaluator":
            enabled = self.enable_for_evaluator
        elif purpose == "profile_builder":
            enabled = self.enable_for_profile_builder
        elif purpose == "planner":
            enabled = self.enable_for_planner
        elif purpose == "quiz":
            enabled = self.enable_for_quiz
        else:
            enabled = self.enable_for_tutor
        return (
            self.provider == "openai_compatible"
            and enabled
            and bool(self.base_url)
            and bool(self.api_key)
            and bool(self.model)
        )


class OpenAICompatibleLLMProvider:
    def __init__(self, settings: LLMSettings, purpose: str = "tutor") -> None:
        if not settings.can_call_remote(purpose):
            raise LLMProviderError("LLM provider is not fully configured.")
        self.settings = settings
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if settings.bypass_proxy else None

    def generate(
        self,
        messages: list[dict[str, str]],
        response_schema: type[Any] | None = None,
    ) -> LLMResult:
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": 0.2,
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            _chat_completions_url(self.settings.base_url),
            data=body,
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        last_error: Exception | None = None
        for attempt in range(self.settings.max_retries + 1):
            try:
                if self._opener is None:
                    response_context = urllib.request.urlopen(request, timeout=self.settings.timeout_seconds)
                else:
                    response_context = self._opener.open(request, timeout=self.settings.timeout_seconds)
                with response_context as response:
                    raw = response.read().decode("utf-8")
                parsed = json.loads(raw)
                content = _extract_content(parsed)
                return LLMResult(
                    content=content,
                    metadata={
                        "provider": "openai_compatible",
                        "model": self.settings.model,
                        "attempt": attempt + 1,
                        "response_schema_requested": response_schema is not None,
                    },
                )
            except urllib.error.HTTPError as exc:
                last_error = LLMProviderError(_http_error_summary(exc))
                if attempt < self.settings.max_retries:
                    time.sleep(0.2)
            except urllib.error.URLError as exc:
                last_error = LLMProviderError(_url_error_summary(exc))
                if attempt < self.settings.max_retries:
                    time.sleep(0.2)
            except (
                TimeoutError,
                ConnectionResetError,
                http.client.RemoteDisconnected,
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as exc:
                last_error = exc
                if attempt < self.settings.max_retries:
                    time.sleep(0.2)
        if isinstance(last_error, LLMProviderError):
            raise last_error
        raise LLMProviderError(f"LLM provider request failed: {type(last_error).__name__}") from last_error


def build_llm_provider(settings: LLMSettings | None = None, purpose: str = "tutor") -> LLMProvider | None:
    resolved = settings or LLMSettings.from_env()
    if resolved.provider != "openai_compatible":
        return None
    if not resolved.can_call_remote(purpose):
        return None
    return OpenAICompatibleLLMProvider(resolved, purpose=purpose)


def _chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{base_url.rstrip('/')}/chat/completions"


def _extract_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("LLM response has no choices.")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ValueError("LLM response has no message.")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LLM response content is empty.")
    return content.strip()


def _http_error_summary(error: urllib.error.HTTPError) -> str:
    raw = ""
    try:
        raw = error.read().decode("utf-8", errors="replace")
    except Exception:
        raw = ""
    detail = _sanitize_error_body(raw)
    if detail:
        return f"LLM provider request failed: HTTP {error.code}: {detail}"
    return f"LLM provider request failed: HTTP {error.code}"


def _sanitize_error_body(raw: str) -> str:
    if not raw:
        return ""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw.strip()[:240]
    error = parsed.get("error")
    if isinstance(error, dict):
        message = str(error.get("message") or error.get("type") or error)
        code = error.get("code")
        if code:
            message = f"{message} (code={code})"
        return message[:240]
    return str(parsed)[:240]


def _url_error_summary(error: urllib.error.URLError) -> str:
    reason = getattr(error, "reason", error)
    reason_text = str(reason)
    if not reason_text:
        reason_text = type(reason).__name__
    return f"LLM provider request failed: URLError: {reason_text[:240]}"


def _bool_from_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _float_from_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _int_from_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default
