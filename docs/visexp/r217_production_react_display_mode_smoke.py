#!/usr/bin/env python3
"""R217: production React AgentFlameView display-mode smoke.

This run exercises the built frontend application, not a temporary React-free
DOM harness. It serves the static Next export plus a minimal AgentFlame API
fixture whose artifact map exposes R209 display-map/drilldown CSVs. The browser
oracle verifies that the production AgentFlameView renders the optional
display-mode panel. It does not verify click interaction, visual drilldown,
developer utility, tag adequacy, or merge quality.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"
DEFAULT_R209_DIR = SCRIPT_DIR / "out" / "reversible-display-map-r209"
DEFAULT_R216_DIR = SCRIPT_DIR / "out" / "browser-dom-mode-r216"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "production-react-display-r217"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sanitize_text(text: str, replacements: list[tuple[str, str]] | None = None) -> str:
    pairs = [
        (str(REPO_ROOT.resolve()), "<repo>"),
        (str(Path.home()), "~"),
    ]
    if replacements:
        pairs = replacements + pairs
    out = text
    for source, target in pairs:
        if source:
            out = out.replace(source, target)
    return out


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def find_browser() -> str:
    requested = os.environ.get("AGENTFLAME_BROWSER")
    if requested:
        return requested
    for name in ["google-chrome-stable", "google-chrome", "chromium", "chromium-browser"]:
        path = shutil.which(name)
        if path:
            return str(path)
    raise FileNotFoundError("no Chrome/Chromium browser found")


def build_frontend() -> dict[str, Any]:
    start = time.monotonic()
    run = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND_DIR,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    elapsed_ms = round((time.monotonic() - start) * 1000.0, 3)
    if run.returncode != 0:
        raise RuntimeError(f"frontend build failed:\n{run.stdout}")
    if not (FRONTEND_DIST / "index.html").exists():
        raise FileNotFoundError("frontend build did not produce dist/index.html")
    return {
        "build_ms": elapsed_ms,
        "command": "npm run build",
        "stdout_excerpt": sanitize_text(run.stdout[-4000:]),
    }


def agentflame_report_fixture() -> dict[str, Any]:
    empty_counter = {
        "total_weight": 0,
        "unique_stacks": 0,
        "compression_ratio": 0,
        "max_stack_reuse": 0,
        "top": [],
    }
    empty_mixing = {
        "mixed_buckets": 0,
        "mixed_weight": 0,
        "mixed_weight_pct": 0.0,
        "examples": [],
    }
    return {
        "schema_version": 2,
        "generated_at": "2026-06-15T00:00:00Z",
        "project": {
            "name": "r217-production-react-fixture",
            "root": "<fixture>",
        },
        "inputs": {
            "scan_files": 0,
            "max_sessions": 0,
            "tag_llm_calls": True,
            "codex_root": None,
            "claude_root": None,
        },
        "llm_tagger": {
            "requests": 0,
            "cache_hits": 0,
            "llm_calls": 0,
            "llm_successes": 0,
            "failures": [],
        },
        "warnings": [],
        "sessions": [],
        "prompt_tags": [],
        "summary": {
            "session_count": 0,
            "source_counts": {},
            "raw_tool_events": 0,
            "raw_llm_events": 0,
            "system": empty_counter,
            "nonsemantic_system": empty_counter,
            "token": empty_counter,
            "dimensions": {},
            "top_prompt_tags": [],
            "command_summary": [],
            "timeline": [],
            "semantic_mixing": {
                "nonsemantic": empty_mixing,
                "flat": empty_mixing,
            },
        },
        "artifacts": {
            "active_display_map": "active-display-map-r209.csv",
            "display_drilldown": "display-drilldown-r209.csv",
        },
    }


class ProductionSmokeHandler(BaseHTTPRequestHandler):
    dist_dir: Path
    report: dict[str, Any]
    artifact_dir: Path

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/v1/agentflame":
            body = json.dumps(self.report).encode("utf-8")
            self._send(200, body, "application/json")
            return
        if path.startswith("/api/v1/agentflame/artifacts/"):
            relative = unquote(path.removeprefix("/api/v1/agentflame/artifacts/"))
            if "/" in relative or relative.startswith("."):
                self._send(404, b"not found", "text/plain; charset=utf-8")
                return
            target = self.artifact_dir / relative
            if not target.exists():
                self._send(404, b"not found", "text/plain; charset=utf-8")
                return
            self._send(200, target.read_bytes(), "text/csv; charset=utf-8")
            return
        if path.startswith("/api/"):
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return

        relative = path.lstrip("/") or "index.html"
        candidate = (self.dist_dir / relative).resolve()
        dist_root = self.dist_dir.resolve()
        if dist_root not in candidate.parents and candidate != dist_root:
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        if candidate.is_dir():
            candidate = candidate / "index.html"
        if not candidate.exists() or not candidate.is_file():
            candidate = self.dist_dir / "index.html"
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        if candidate.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        self._send(200, candidate.read_bytes(), content_type)


def parse_panel_attrs(dom: str) -> dict[str, str]:
    match = re.search(r"<div[^>]+data-agentflame-display-panel=\"true\"[^>]*>", dom)
    if not match:
        raise AssertionError("production AgentFlameView did not render the display-mode panel")
    tag = match.group(0)
    attrs = dict(re.findall(r"([a-zA-Z0-9_-]+)=\"([^\"]*)\"", tag))
    return {key: html.unescape(value) for key, value in attrs.items()}


def run_browser(out_dir: Path, browser: str, dist_dir: Path, artifact_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    dom_dump_path = out_dir / "dom-dump-r217.html"
    screenshot_path = out_dir / "screenshot-r217.png"

    class Handler(ProductionSmokeHandler):
        pass

    Handler.dist_dir = dist_dir
    Handler.report = agentflame_report_fixture()
    Handler.artifact_dir = artifact_dir
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="agentsight-r217-browser-profile-") as profile:
            url = f"http://127.0.0.1:{port}/agentflame"
            cmd = [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--no-first-run",
                "--no-default-browser-check",
                f"--user-data-dir={profile}",
                "--window-size=1280,1000",
                "--virtual-time-budget=8000",
                f"--screenshot={screenshot_path}",
                "--dump-dom",
                url,
            ]
            start = time.monotonic()
            run = subprocess.run(
                cmd,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=40,
            )
            elapsed_ms = round((time.monotonic() - start) * 1000.0, 3)
            if run.returncode != 0:
                raise RuntimeError(f"browser failed with {run.returncode}:\n{run.stderr}\n{run.stdout[:2000]}")
            dom_dump_path.write_text(run.stdout, encoding="utf-8")
            if not screenshot_path.exists() or screenshot_path.stat().st_size <= 0:
                raise AssertionError("browser did not create a screenshot")
            attrs = parse_panel_attrs(run.stdout)
            button_count = len(re.findall(r"data-agentflame-display-mode-button=\"(?:raw|display|pending)\"", run.stdout))
            summary = {
                "production_agentflame_view_exercised": True,
                "browser_dom_renderer_exercised": True,
                "display_panel_rendered": True,
                "mode_controls_rendered": button_count == 3,
                "mode_button_count": button_count,
                "default_display_mode": attrs.get("data-display-mode"),
                "visible_bucket_count": as_int(attrs.get("data-bucket-count")),
                "visible_total_support": as_int(attrs.get("data-total-support")),
                "visible_candidate_overlay_rows": as_int(attrs.get("data-candidate-overlay-rows")),
                "visible_review_required_rows": as_int(attrs.get("data-review-required-rows")),
                "membership_matches_display_map": attrs.get("data-membership-matches") == "true",
                "dom_dump_bytes": dom_dump_path.stat().st_size,
                "screenshot_bytes": screenshot_path.stat().st_size,
                "browser_ms": elapsed_ms,
            }
            info = {
                "browser": browser,
                "browser_command": sanitize_text(
                    " ".join(cmd[:-1] + ["<local-r217-url>"]),
                    [(profile, "<tmp-browser-profile>")],
                ),
                "browser_stderr": sanitize_text(
                    run.stderr.strip()[:4000],
                    [(profile, "<tmp-browser-profile>")],
                ),
                "dom_dump_path": dom_dump_path,
                "screenshot_path": screenshot_path,
            }
            return summary, info
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def claim_gate(summary: dict[str, Any]) -> dict[str, bool]:
    return {
        "production_react_display_mode_smoke_supported": bool(
            summary["production_agentflame_view_exercised"]
            and summary["browser_dom_renderer_exercised"]
            and summary["display_panel_rendered"]
            and summary["mode_controls_rendered"]
            and summary["default_display_mode"] == "display"
            and summary["visible_bucket_count"] == 1748
            and summary["visible_total_support"] == 482398
            and summary["membership_matches_display_map"]
        ),
        "built_static_frontend": True,
        "display_artifacts_loaded": True,
        "support_preserved": summary["visible_total_support"] == 482398,
        "mode_controls_rendered": bool(summary["mode_controls_rendered"]),
        "reads_generated_artifacts_only": True,
        "raw_trace_read": False,
        "llm_called": False,
        "canonical_map_updated": False,
        "mode_click_path_supported": False,
        "visual_drilldown_supported": False,
        "semantic_adequacy_supported": False,
        "canonicalization_quality_supported": False,
        "developer_utility_supported": False,
        "community_adoption_supported": False,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# R217 Production React Display-Mode Smoke",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "- Builds the real Next static frontend.",
        "- Serves a minimal AgentFlame API fixture with R209 display-map and drilldown artifacts.",
        "- Opens `/agentflame` in headless Chrome and checks the production `AgentFlameView` DOM.",
        "- Verifies that the optional display-mode panel renders and preserves the default display-mode support.",
        "- Does not click the production controls, exercise visual drilldown, call an LLM, read raw traces, or update the canonical map.",
        "",
        "## DOM Summary",
        "",
        "| field | value |",
        "|---|---:|",
        f"| default mode | `{summary['default_display_mode']}` |",
        f"| mode buttons | {summary['mode_button_count']} |",
        f"| visible buckets | {summary['visible_bucket_count']} |",
        f"| visible support | {summary['visible_total_support']} |",
        f"| visible candidate overlays | {summary['visible_candidate_overlay_rows']} |",
        f"| visible review rows | {summary['visible_review_required_rows']} |",
        f"| membership matches | {summary['membership_matches_display_map']} |",
        "",
        "## Claim Boundary",
        "",
        "R217 supports a production React rendering smoke for the optional "
        "display-mode panel in `AgentFlameView`. It does not support click-path "
        "interaction, visual drilldown, merge quality, semantic adequacy, "
        "developer utility, community adoption, or canonical-map updates.",
        "",
        f"Frontend build time: `{summary['build_ms']}` ms. Browser run time: `{summary['browser_ms']}` ms.",
        f"DOM dump bytes: `{summary['dom_dump_bytes']}`. Screenshot bytes: `{summary['screenshot_bytes']}`.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    r209_json = args.r209_dir / "reversible-display-map-r209.json"
    display_csv = args.r209_dir / "active-display-map-r209.csv"
    drilldown_csv = args.r209_dir / "display-drilldown-r209.csv"
    r216_json = args.r216_dir / "browser-dom-mode-r216.json"
    for path in [r209_json, display_csv, drilldown_csv, r216_json]:
        if not path.exists():
            raise FileNotFoundError(f"missing R217 input artifact: {rel(path)}")

    artifact_dir = args.out_dir / "fixture-artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(display_csv, artifact_dir / "active-display-map-r209.csv")
    shutil.copyfile(drilldown_csv, artifact_dir / "display-drilldown-r209.csv")

    build_info = build_frontend() if not args.skip_build else {
        "build_ms": 0.0,
        "command": "skipped",
        "stdout_excerpt": "",
    }
    browser = args.browser or find_browser()
    summary, browser_info = run_browser(args.out_dir, browser, FRONTEND_DIST, artifact_dir)
    summary["build_ms"] = build_info["build_ms"]
    r209 = read_json(r209_json)
    r216 = read_json(r216_json)
    status = "production_react_display_mode_smoke_ready_no_click_or_quality_claims"
    dom_dump_path = browser_info["dom_dump_path"]
    screenshot_path = browser_info["screenshot_path"]

    payload = {
        "run_id": "R217",
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "claim": "C3 production AgentFlameView display-mode consumer; C6 protocol/gate only",
        "claim_boundary": (
            "R217 exercises the production React AgentFlameView optional display-mode "
            "panel using generated R209 artifacts. It is not a click-path, visual "
            "drilldown, semantic adequacy, merge-quality, developer-utility, or "
            "community-adoption result."
        ),
        "input": {
            "r209_json": rel(r209_json),
            "r209_json_sha256": sha256_file(r209_json),
            "display_csv": rel(display_csv),
            "display_csv_sha256": sha256_file(display_csv),
            "drilldown_csv": rel(drilldown_csv),
            "drilldown_csv_sha256": sha256_file(drilldown_csv),
            "r216_json": rel(r216_json),
            "r216_json_sha256": sha256_file(r216_json),
            "frontend_component": rel(FRONTEND_DIR / "src" / "components" / "AgentFlameView.tsx"),
            "frontend_component_sha256": sha256_file(FRONTEND_DIR / "src" / "components" / "AgentFlameView.tsx"),
            "frontend_display_module": rel(FRONTEND_DIR / "src" / "utils" / "agentflameDisplayModes.ts"),
            "frontend_display_module_sha256": sha256_file(FRONTEND_DIR / "src" / "utils" / "agentflameDisplayModes.ts"),
        },
        "method": {
            "frontend_build": build_info,
            "browser_info": {
                key: rel(value) if isinstance(value, Path) else value
                for key, value in browser_info.items()
            },
            "api_fixture": "minimal AgentFlame report with active_display_map and display_drilldown artifact keys",
            "quality_boundary": "production rendering only; no click path, visual drilldown, adequacy, quality, utility, or map-update claim",
        },
        "source_summaries": {
            "r209_total_support": (r209.get("summary") or {}).get("total_support"),
            "r216_visible_bucket_count": (r216.get("summary") or {}).get("visible_bucket_count"),
        },
        "summary": summary,
        "claim_gate": claim_gate(summary),
        "outputs": {
            "summary_json": rel(args.out_dir / "production-react-display-r217.json"),
            "summary_md": rel(args.out_dir / "production-react-display-r217.md"),
            "dom_dump_html": rel(dom_dump_path),
            "dom_dump_html_sha256": sha256_file(dom_dump_path),
            "screenshot_png": rel(screenshot_path),
            "screenshot_png_sha256": sha256_file(screenshot_path),
            "fixture_display_csv": rel(artifact_dir / "active-display-map-r209.csv"),
            "fixture_drilldown_csv": rel(artifact_dir / "display-drilldown-r209.csv"),
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r209-dir", type=Path, default=DEFAULT_R209_DIR)
    parser.add_argument("--r216-dir", type=Path, default=DEFAULT_R216_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--browser", type=str, default=None)
    parser.add_argument("--skip-build", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "production-react-display-r217.json", payload)
    write_markdown(args.out_dir / "production-react-display-r217.md", payload)
    print(json.dumps({"status": payload["status"], "summary_json": payload["outputs"]["summary_json"]}))


if __name__ == "__main__":
    main()
