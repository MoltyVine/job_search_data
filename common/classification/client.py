"""Ollama HTTP client (stdlib urllib — no extra deps)."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any


class OllamaClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "llama3.1:8b",
        temperature: float = 0.1,
        timeout_s: float = 180.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout_s = timeout_s

    def reachable(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return 200 <= resp.status < 300
        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    def chat(self, system: str, user: str) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": self.temperature},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ollama unreachable at {self.base_url}: {exc}") from exc

        message = body.get("message") or {}
        content = message.get("content")
        if not content:
            raise RuntimeError(f"Ollama returned no message content: {body!r}")
        return str(content)


def ollama_reachable(base_url: str = "http://127.0.0.1:11434") -> bool:
    return OllamaClient(base_url=base_url).reachable()


def ensure_ollama_running(
    base_url: str = "http://127.0.0.1:11434",
    *,
    wait_s: float = 45.0,
) -> bool:
    """Return True if Ollama responds, starting ``ollama serve`` when installed but down."""
    if ollama_reachable(base_url):
        return True

    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        return False

    print(
        f"Ollama is installed but not reachable at {base_url}; starting `ollama serve`…",
        flush=True,
    )
    try:
        subprocess.Popen(
            [ollama_bin, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        print(f"Failed to start ollama serve: {exc}", flush=True)
        return False

    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        time.sleep(0.5)
        if ollama_reachable(base_url):
            print("Ollama is up.", flush=True)
            return True

    print(f"Ollama still not reachable after {wait_s:.0f}s.", flush=True)
    return False
