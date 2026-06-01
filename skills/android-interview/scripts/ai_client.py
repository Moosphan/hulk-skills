from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from ai_schemas import AIConfig


class AIClientError(RuntimeError):
    pass


class BaseAIClient:
    provider_name = "base"

    def __init__(self, config: AIConfig) -> None:
        self.config = config

    def complete_json(self, *, role: str, action: str, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class UnavailableAIClient(BaseAIClient):
    provider_name = "none"

    def complete_json(self, *, role: str, action: str, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise AIClientError("AI client is unavailable. Configure --ai-provider and credentials, or use --ai-mode off/assist.")


class FixtureAIClient(BaseAIClient):
    provider_name = "fixture"

    def complete_json(self, *, role: str, action: str, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.config.fixture_dir:
            raise AIClientError("Fixture provider requires --ai-fixture-dir.")
        path = Path(self.config.fixture_dir) / f"{role}-{action}.json"
        if not path.exists():
            raise AIClientError(f"AI fixture not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))


class OpenAICompatibleClient(BaseAIClient):
    provider_name = "openai-compatible"

    def __init__(self, config: AIConfig) -> None:
        super().__init__(config)
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = config.model or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        if not self.api_key:
            raise AIClientError("OPENAI_API_KEY is not set.")

    def complete_json(self, *, role: str, action: str, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise AIClientError(f"AI HTTP error {exc.code}: {detail}") from exc
        except Exception as exc:  # noqa: BLE001 - surface provider failures as mode-handled errors.
            raise AIClientError(f"AI request failed: {exc}") from exc

        try:
            content = raw["choices"][0]["message"]["content"]
            data = json.loads(content)
        except Exception as exc:  # noqa: BLE001
            raise AIClientError(f"AI response was not valid JSON: {raw}") from exc
        return data if isinstance(data, dict) else {"value": data}


def build_ai_client(config: AIConfig) -> BaseAIClient:
    if not config.enabled:
        return UnavailableAIClient(config)
    if config.provider == "fixture":
        return FixtureAIClient(config)
    if config.provider in {"auto", "openai-compatible"}:
        try:
            return OpenAICompatibleClient(config)
        except AIClientError:
            if config.provider == "openai-compatible" or config.required:
                raise
    return UnavailableAIClient(config)
