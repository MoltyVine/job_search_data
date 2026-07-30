"""OpenRouter chat-completions client (stdlib urllib — no extra deps).

Optional, opt-in backend for high-volume classification runs. Sends thread
text to OpenRouter (and whichever model provider you configure) over the
network — unlike the default ``agent`` backend, where message content never
leaves this session. See docs/CLASSIFICATION_CRITERIA.md and the root
README's Classification section before enabling it.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

API_KEY_ENV_VAR = "OPENROUTER_API_KEY"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterClient:
    def __init__(
        self,
        model: str,
        *,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        temperature: float = 0.1,
        timeout_s: float = 180.0,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get(API_KEY_ENV_VAR)
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.timeout_s = timeout_s

    def chat(self, system: str, user: str) -> str:
        if not self.api_key:
            raise RuntimeError(
                f"{API_KEY_ENV_VAR} is not set. Export it before using the "
                "openrouter classification backend."
            )
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenRouter unreachable at {self.base_url}: {exc}") from exc

        choices = body.get("choices") or []
        if not choices:
            raise RuntimeError(f"OpenRouter returned no choices: {body!r}")
        content = choices[0].get("message", {}).get("content")
        if not content:
            raise RuntimeError(f"OpenRouter returned no message content: {body!r}")
        return str(content)
