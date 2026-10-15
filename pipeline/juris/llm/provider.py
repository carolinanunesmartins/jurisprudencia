"""LLM access (SPEC §7). `generate_json(prompt_id, system, input)` returns the parsed JSON answer.

ReplayProvider answers from fixtures keyed by sha256 of the canonical request, so tests and
`make classify-replay` never call the network. AnthropicProvider is HUMAN-run only (needs
LLM_API_KEY) and records every answer as a replay fixture, so a live run can be replayed.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Protocol

import httpx

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class MissingFixture(LookupError):
    pass


class Truncated(RuntimeError):
    """The answer hit max_tokens. Not retried: the same request would be cut again."""


class ApiError(RuntimeError):
    """The API refused the request; the message is the API's own (it never contains the key)."""

    def __init__(self, status: int, message: str):
        super().__init__(f"API error {status}: {message}")
        self.status = status


def api_error(resp: httpx.Response) -> ApiError:
    try:
        err = resp.json().get("error") or {}
        message = f"{err.get('type', '?')}: {err.get('message', '')}"
    except ValueError:
        message = resp.text[:500]
    return ApiError(resp.status_code, message)


def tokens_used(provider: object) -> int:
    """Input + output tokens billed so far (0 for providers that do not bill)."""
    usage: dict[str, int] = getattr(provider, "usage", {})
    return sum(v for k, v in usage.items() if k.endswith("tokens"))


class LlmProvider(Protocol):
    model: str

    def generate_json(self, prompt_id: str, system: str, input: str) -> dict[str, Any]: ...


def request_key(prompt_id: str, system: str, input: str) -> str:
    canonical = json.dumps(
        {"prompt_id": prompt_id, "system": system, "input": input},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_json_text(text: str) -> dict[str, Any]:
    """The model's text as JSON; tolerates a fenced block around it. Raises ValueError."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("answer is not a JSON object")
    return value


class ReplayProvider:
    def __init__(self, fixtures: Path, model: str = "replay"):
        self.fixtures = fixtures
        self.model = model

    def generate_json(self, prompt_id: str, system: str, input: str) -> dict[str, Any]:
        path = self.fixtures / f"{request_key(prompt_id, system, input)}.json"
        if not path.exists():
            raise MissingFixture(path.name)
        return json.loads(path.read_text(encoding="utf-8"))["answer"]


class AnthropicProvider:
    """Temperature 0; the instructions are sent as a cached system block (SPEC §7)."""

    def __init__(
        self,
        api_key: str,
        model: str,
        record: Path | None = None,
        client: httpx.Client | None = None,
        max_tokens: int = 1200,  # a full 7-question answer is ~1 000 tokens; typical ~400
        workspace_id: str | None = None,  # needed only for keys not scoped to a workspace
    ):
        self.model = model
        self.record = record
        self.max_tokens = max_tokens
        self.usage: dict[str, int] = {}
        self._client = client or httpx.Client(timeout=120)
        self._headers = {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        if workspace_id:
            self._headers["anthropic-workspace-id"] = workspace_id

    def generate_json(self, prompt_id: str, system: str, input: str) -> dict[str, Any]:
        body = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": 0,
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": "user", "content": input}],
        }
        resp = self._client.post(ANTHROPIC_URL, headers=self._headers, json=body)
        if resp.is_error:
            raise api_error(resp)
        data = resp.json()
        for k, v in (data.get("usage") or {}).items():
            if isinstance(v, int):
                self.usage[k] = self.usage.get(k, 0) + v
        if data.get("stop_reason") == "max_tokens":
            raise Truncated(f"answer cut at {self.max_tokens} tokens")
        text = "".join(
            b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
        )
        answer = parse_json_text(text)
        if self.record is not None:
            self.record.mkdir(parents=True, exist_ok=True)
            fixture = {"prompt_id": prompt_id, "model": self.model, "answer": answer}
            path = self.record / f"{request_key(prompt_id, system, input)}.json"
            path.write_text(json.dumps(fixture, ensure_ascii=False, indent=1), encoding="utf-8")
        return answer
