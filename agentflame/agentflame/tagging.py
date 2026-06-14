from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable

from .util import clean_space, now_iso, short_hash


class TaggingError(RuntimeError):
    pass


class LlamaCppTagger:
    """LLM-only one-word tagger backed by llama.cpp server.

    The tagger never falls back to regex or heuristics. If the local LLM endpoint
    is unavailable, or if repeated model output violates the one-word contract,
    tagging fails so callers know the artifact is incomplete.
    """

    def __init__(
        self,
        cache_path: Path,
        base_url: str = "http://127.0.0.1:8080",
        model: str = "local",
        timeout_s: int = 30,
        max_uncached: int = -1,
    ) -> None:
        self.cache_path = cache_path
        self.base_url = base_url.rstrip("/")
        self.model = model or "local"
        self.timeout_s = timeout_s
        self.max_uncached = max_uncached
        self.requests = 0
        self.cache_hits = 0
        self.llm_calls = 0
        self.llm_successes = 0
        self.failures: list[str] = []
        self.cache: dict[str, dict[str, Any]] = {}
        if cache_path.exists():
            try:
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
                tags = payload.get("tags") if isinstance(payload, dict) else None
                if isinstance(tags, dict):
                    self.cache = {str(k): v for k, v in tags.items() if isinstance(v, dict)}
                elif isinstance(payload, dict):
                    # Backward-compatible shape for early experiments.
                    self.cache = {str(k): {"tag": str(v)} for k, v in payload.items()}
            except Exception:
                self.cache = {}

    def save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "created_by": "agentflame",
            "updated_at": now_iso(),
            "llm": {
                "provider": "llama.cpp",
                "base_url": self.base_url,
                "model": self.model,
            },
            "stats": self.stats(),
            "tags": self.cache,
        }
        self.cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def stats(self) -> dict[str, Any]:
        return {
            "requests": self.requests,
            "cache_hits": self.cache_hits,
            "llm_calls": self.llm_calls,
            "llm_successes": self.llm_successes,
            "failures": self.failures[:8],
        }

    def tag(self, kind: str, text: str, hints: Iterable[str] = ()) -> str:
        self.requests += 1
        joined_hints = " ".join(hints)
        source = clean_space(f"{joined_hints} {text}", limit=1800)
        source_hash = short_hash(source, 24)
        key = short_hash(f"v1\nllama.cpp\n{self.base_url}\n{self.model}\n{kind}\n{source}", 32)
        if key in self.cache:
            tag = str(self.cache[key].get("tag") or "")
            if self._valid(tag):
                self.cache_hits += 1
                return tag
        if self.max_uncached >= 0 and self.llm_calls >= self.max_uncached:
            raise TaggingError(
                f"LLM tag budget exhausted after {self.llm_calls} uncached calls; "
                "increase --max-uncached-tags or reuse an existing tag cache."
            )
        tag = self._tag_with_retries(kind, source)
        self.cache[key] = {
            "tag": tag,
            "kind": kind,
            "source_hash": source_hash,
            "created_at": now_iso(),
            "llm": {
                "provider": "llama.cpp",
                "base_url": self.base_url,
                "model": self.model,
            },
        }
        return tag

    def _tag_with_retries(self, kind: str, source: str) -> str:
        last = ""
        for attempt in range(2):
            prompt = self._prompt(kind, source, invalid_previous=last if attempt else "")
            raw = self._call_llm(prompt)
            tag = self._sanitize(raw)
            if self._valid(tag):
                self.llm_successes += 1
                return tag
            last = raw
        detail = clean_space(last, 200)
        self.failures.append(f"invalid_output kind={kind} output={detail}")
        raise TaggingError(f"LLM returned invalid one-word tag for {kind}: {detail!r}")

    def _prompt(self, kind: str, source: str, invalid_previous: str = "") -> str:
        retry = ""
        if invalid_previous:
            retry = f"\nPrevious invalid answer: {invalid_previous!r}\nReturn only one valid word now.\n"
        return (
            "You label local AI coding-agent session fragments.\n"
            "Return exactly one lowercase English word, 3 to 14 letters.\n"
            "No spaces, punctuation, quotes, markdown, or explanation.\n"
            "Choose the most specific action or topic word. Do not use generic words like task, work, misc, thing.\n"
            f"{retry}\n"
            f"Fragment kind: {kind}\n"
            f"Fragment:\n{source[:1600]}\n\n"
            "Tag:"
        )

    def _call_llm(self, prompt: str) -> str:
        self.llm_calls += 1
        errors: list[str] = []
        for endpoint, body in (
            (
                "/v1/chat/completions",
                {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You output exactly one lowercase English word."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0,
                    "max_tokens": 8,
                    "stream": False,
                },
            ),
            (
                "/completion",
                {
                    "prompt": prompt,
                    "temperature": 0,
                    "n_predict": 8,
                    "stream": False,
                },
            ),
        ):
            try:
                payload = self._post_json(endpoint, body)
                text = self._extract_text(payload)
                if text:
                    return text
                errors.append(f"{endpoint}: empty response")
            except Exception as exc:
                errors.append(f"{endpoint}: {type(exc).__name__}: {exc}")
        detail = "; ".join(errors)
        self.failures.append(detail)
        raise TaggingError(
            f"Could not tag with llama.cpp server at {self.base_url}. "
            "Start llama-server or pass --llama-url. Details: "
            f"{detail}"
        )

    def _post_json(self, endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            raise TaggingError(f"HTTP {exc.code}: {clean_space(text, 200)}") from exc

    def _extract_text(self, payload: dict[str, Any]) -> str:
        if isinstance(payload.get("content"), str):
            return str(payload["content"])
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    return message["content"]
                if isinstance(first.get("text"), str):
                    return first["text"]
        return ""

    def _sanitize(self, text: str) -> str:
        text = (text or "").strip().lower()
        text = re.sub(r"^[\"'`*_>\s]+|[\"'`*_.\s]+$", "", text)
        match = re.fullmatch(r"[a-z][a-z0-9]{2,15}", text)
        if match:
            return text[:16]
        words = re.findall(r"\b[a-z][a-z0-9]{2,15}\b", text)
        return words[-1][:16] if len(words) == 1 else ""

    def _valid(self, tag: str) -> bool:
        return bool(re.fullmatch(r"[a-z][a-z0-9]{2,15}", tag or "")) and tag not in {
            "task",
            "work",
            "misc",
            "thing",
            "stuff",
            "other",
        }
