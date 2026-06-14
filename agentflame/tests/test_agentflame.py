from __future__ import annotations

import json
import threading
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from agentflame.analysis import AnalysisConfig, run_analysis
from agentflame.render import write_dashboard
from agentflame.session_history import parse_codex_session
from agentflame.tagging import LlamaCppTagger, TaggingError
from agentflame.util import command_process_chain


class FakeTagger:
    def __init__(self) -> None:
        self.calls = 0

    def tag(self, kind, text, hints=None):
        self.calls += 1
        if kind == "session":
            return "session"
        if kind == "prompt":
            return "debug"
        return "response"

    def save(self):
        return None

    def stats(self):
        return {"requests": self.calls, "cache_hits": 0, "llm_calls": self.calls, "llm_successes": self.calls, "failures": []}


class InvalidTagger(LlamaCppTagger):
    def _call_llm(self, prompt: str) -> str:
        return "two words"


class AgentFlameTests(unittest.TestCase):
    def test_command_process_chain_keeps_shell_wrapper_nesting(self) -> None:
        self.assertEqual(command_process_chain("bash -lc 'cargo test --manifest-path collector/Cargo.toml'"), ["bash", "cargo"])

    def test_parse_codex_session_and_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_path = root / "codex.jsonl"
            rows = [
                {
                    "type": "session_meta",
                    "timestamp": "2026-06-14T00:00:00Z",
                    "payload": {"id": "s1", "cwd": str(root), "model": "gpt-test"},
                },
                {
                    "type": "event_msg",
                    "timestamp": "2026-06-14T00:00:01Z",
                    "payload": {"type": "user_message", "message": "Fix the failing tests"},
                },
                {
                    "type": "response_item",
                    "timestamp": "2026-06-14T00:00:02Z",
                    "payload": {
                        "type": "function_call",
                        "name": "exec_command",
                        "call_id": "c1",
                        "arguments": json.dumps({"cmd": "cargo test --manifest-path collector/Cargo.toml"}),
                    },
                },
                {
                    "type": "response_item",
                    "timestamp": "2026-06-14T00:00:03Z",
                    "payload": {"type": "function_call_output", "call_id": "c1", "output": "Process exited with code 0"},
                },
                {
                    "type": "response_item",
                    "timestamp": "2026-06-14T00:00:04Z",
                    "payload": {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "The tests now pass."}],
                    },
                },
            ]
            session_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            parsed = parse_codex_session(session_path, root)
            self.assertIsNotNone(parsed)
            self.assertEqual(parsed.tools[0].effect, "test")
            self.assertEqual(parsed.tools[0].process_chain, ["cargo"])

            out = root / "out"
            payload = run_analysis(
                AnalysisConfig(project_root=root, out_dir=out, project_name="demo", codex_root=root, claude_root=root),
                FakeTagger(),
            )
            write_dashboard(out, payload)
            self.assertTrue((out / "agentflame.json").exists())
            self.assertTrue((out / "tags.json").exists() is False)
            self.assertTrue((out / "index.html").exists())
            self.assertEqual(payload["sessions"][0]["agent_sight_session_id"], "local:codex:codex:s1")
            self.assertTrue(any("call:llm/response" in row["stack"] for row in payload["summary"]["token"]["top"]))
            self.assertTrue(any("call:tool/shell;process:cargo;effect:test" in row["stack"] for row in payload["summary"]["system"]["top"]))
            self.assertGreater(payload["summary"]["system"]["unique_stacks"], 0)

    def test_llm_tagger_rejects_invalid_without_regex_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tagger = InvalidTagger(cache_path=Path(tmp) / "tags.json")
            with self.assertRaises(TaggingError):
                tagger.tag("prompt", "Fix a test")
            self.assertEqual(tagger.llm_successes, 0)

    def test_llm_tagger_uses_http_and_writes_cache(self) -> None:
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                _ = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                body = json.dumps({"choices": [{"message": {"content": "debug"}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp) / "tags.json"
                tagger = LlamaCppTagger(cache_path=cache, base_url=f"http://127.0.0.1:{server.server_port}")
                self.assertEqual(tagger.tag("prompt", "Fix a test"), "debug")
                tagger.save()
                saved = json.loads(cache.read_text(encoding="utf-8"))
                self.assertEqual(saved["stats"]["llm_successes"], 1)
                self.assertEqual(next(iter(saved["tags"].values()))["tag"], "debug")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
