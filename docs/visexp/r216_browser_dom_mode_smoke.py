#!/usr/bin/env python3
"""R216: headless-browser DOM smoke for AgentFlame display modes.

This run exercises the frontend display-mode TypeScript module inside a real
headless browser. It intentionally stays below a production React UI claim: the
browser renders a temporary DOM harness, clicks raw/display/pending controls,
and checks the same reversible display-map membership contract as R215.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"
FRONTEND_MODULE = FRONTEND_DIR / "src" / "utils" / "agentflameDisplayModes.ts"
DEFAULT_R209_DIR = SCRIPT_DIR / "out" / "reversible-display-map-r209"
DEFAULT_R213_DIR = SCRIPT_DIR / "out" / "display-mode-drilldown-r213"
DEFAULT_R214_DIR = SCRIPT_DIR / "out" / "long-tail-control-r214"
DEFAULT_R215_DIR = SCRIPT_DIR / "out" / "frontend-renderer-mode-r215"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "browser-dom-mode-r216"

MODE_FIELDS = [
    "mode",
    "bucket_count",
    "total_support",
    "candidate_overlay_rows",
    "review_required_rows",
    "review_required_support",
    "active_merge_rows",
    "hidden_other_rows",
    "top_bucket",
    "top_bucket_support",
]

DOM_CHECK_FIELDS = [
    "check",
    "expected",
    "observed",
    "passed",
    "reason",
]

DISPLAY_FIXTURE_FIELDS = [
    "dimension",
    "raw_tag",
    "active_display_tag",
    "support",
    "requires_review",
    "candidate_display_tag",
]

DRILLDOWN_FIXTURE_FIELDS = [
    "dimension",
    "active_display_tag",
    "support",
    "raw_tag_count",
    "raw_tags",
    "review_required_rows",
    "review_required_support",
    "candidate_rows",
    "active_merge_rows",
]


BROWSER_ENTRY_TS = r"""
import {
  drilldownMembershipMatchesDisplayMap,
  renderAgentFlameModes,
} from './agentflameDisplayModes.js';

type Mode = 'raw' | 'display' | 'pending';

declare global {
  interface Window {
    AGENTFLAME_R216_FIXTURE: any;
  }
}

const fixture = window.AGENTFLAME_R216_FIXTURE;
const displayRows = fixture.displayRows;
const drilldownRows = fixture.drilldownRows;
const modes = renderAgentFlameModes(displayRows, drilldownRows);
let currentMode: Mode = 'display';

function corruptFirstDrilldownRawTag(rows: any[]) {
  const next = rows.map(row => ({ ...row }));
  const index = next.findIndex(row => typeof row.raw_tags === 'string' && row.raw_tags.includes('='));
  if (index < 0) throw new Error('fixture has no drilldown row to corrupt');
  next[index].raw_tags = next[index].raw_tags.replace(/^[^=;]+=/, '__wrong__=');
  return next;
}

function promoteCandidatesAsActive(rows: any[]) {
  return rows.map(row => {
    if (!row.candidate_display_tag) return { ...row };
    return { ...row, active_display_tag: row.candidate_display_tag };
  });
}

function bucketSignature(result: any): string {
  return result.buckets
    .map((bucket: any) => [
      bucket.dimension,
      bucket.displayTag,
      bucket.rawTags.map((raw: any) => `${raw.tag}=${raw.support}`).sort().join(';'),
    ].join('\u0001'))
    .sort()
    .join('\u0002');
}

function summarizeMode(result: any) {
  const top = result.buckets[0] ?? null;
  return {
    mode: result.mode,
    bucketCount: result.bucketCount,
    totalSupport: result.totalSupport,
    candidateOverlayRows: result.candidateOverlayRows,
    reviewRequiredRows: result.reviewRequiredRows,
    reviewRequiredSupport: result.reviewRequiredSupport,
    activeMergeRows: result.activeMergeRows,
    hiddenOtherRows: result.hiddenOtherRows,
    topBucket: top ? {
      dimension: top.dimension,
      displayTag: top.displayTag,
      support: top.support,
    } : null,
  };
}

function node(tag: string, attrs: Record<string, string> = {}, text = ''): HTMLElement {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    el.setAttribute(key, value);
  }
  if (text) el.textContent = text;
  return el;
}

function renderMode(mode: Mode) {
  currentMode = mode;
  const result = modes[mode];
  const root = document.getElementById('app');
  if (!root) throw new Error('missing app root');
  root.textContent = '';

  const shell = node('main', {
    'data-r216-ready': 'true',
    'data-current-mode': mode,
    'data-bucket-count': String(result.bucketCount),
    'data-total-support': String(result.totalSupport),
    'data-candidate-overlay-rows': String(result.candidateOverlayRows),
    'data-review-required-rows': String(result.reviewRequiredRows),
  });

  const header = node('section', { class: 'header' });
  header.appendChild(node('h1', {}, 'AgentFlame Display Modes'));
  const controls = node('div', { class: 'controls', role: 'group', 'aria-label': 'display mode' });
  for (const candidate of ['raw', 'display', 'pending'] as Mode[]) {
    const button = node('button', {
      type: 'button',
      'data-mode-button': candidate,
      'aria-pressed': String(candidate === mode),
    }, candidate);
    button.addEventListener('click', () => renderMode(candidate));
    controls.appendChild(button);
  }
  header.appendChild(controls);
  shell.appendChild(header);

  const stats = node('section', { class: 'stats' });
  const statPairs = [
    ['mode', mode],
    ['buckets', String(result.bucketCount)],
    ['support', String(result.totalSupport)],
    ['candidates', String(result.candidateOverlayRows)],
    ['review', String(result.reviewRequiredRows)],
    ['active merges', String(result.activeMergeRows)],
  ];
  for (const [label, value] of statPairs) {
    const item = node('div', { class: 'stat', 'data-stat': label });
    item.appendChild(node('span', { class: 'stat-label' }, label));
    item.appendChild(node('strong', { class: 'stat-value' }, value));
    stats.appendChild(item);
  }
  shell.appendChild(stats);

  const table = node('table', { class: 'buckets' });
  const thead = node('thead');
  const headRow = node('tr');
  for (const heading of ['rank', 'dimension', 'tag', 'support', 'raw tags', 'pending']) {
    headRow.appendChild(node('th', {}, heading));
  }
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = node('tbody');
  result.buckets.slice(0, 12).forEach((bucket: any, index: number) => {
    const row = node('tr', {
      'data-bucket-row': String(index + 1),
      'data-has-pending-overlay': String(bucket.hasPendingOverlay),
    });
    const cells = [
      String(index + 1),
      bucket.dimension,
      bucket.displayTag,
      String(bucket.support),
      String(bucket.rawTagCount),
      bucket.hasPendingOverlay ? 'pending' : '',
    ];
    for (const cell of cells) row.appendChild(node('td', {}, cell));
    tbody.appendChild(row);
  });
  table.appendChild(tbody);
  shell.appendChild(table);
  root.appendChild(shell);
}

function runDomChecks() {
  const checks: Array<{check: string; expected: string; observed: string; passed: boolean; reason: string}> = [];
  const root = () => document.querySelector('[data-r216-ready="true"]') as HTMLElement | null;
  for (const mode of ['raw', 'display', 'pending'] as Mode[]) {
    const button = document.querySelector(`[data-mode-button="${mode}"]`) as HTMLButtonElement | null;
    if (!button) {
      checks.push({ check: `click_${mode}`, expected: mode, observed: 'missing_button', passed: false, reason: 'mode button missing' });
      continue;
    }
    button.click();
    const active = root();
    checks.push({
      check: `click_${mode}`,
      expected: mode,
      observed: active?.getAttribute('data-current-mode') ?? 'missing_root',
      passed: active?.getAttribute('data-current-mode') === mode,
      reason: 'mode button updates rendered DOM mode',
    });
  }

  const membershipMatches = drilldownMembershipMatchesDisplayMap(displayRows, drilldownRows);
  const pendingMembershipEqualsDisplay = bucketSignature(modes.pending) === bucketSignature(modes.display);
  const wrongDrilldownRejected =
    !drilldownMembershipMatchesDisplayMap(displayRows, corruptFirstDrilldownRawTag(drilldownRows));
  const candidatePromotionRejected =
    !drilldownMembershipMatchesDisplayMap(promoteCandidatesAsActive(displayRows), drilldownRows);

  checks.push({
    check: 'membership_matches_display_map',
    expected: 'true',
    observed: String(membershipMatches),
    passed: membershipMatches,
    reason: 'drilldown raw membership matches active display rows',
  });
  checks.push({
    check: 'pending_membership_equals_display',
    expected: 'true',
    observed: String(pendingMembershipEqualsDisplay),
    passed: pendingMembershipEqualsDisplay,
    reason: 'pending overlays do not change active membership',
  });
  checks.push({
    check: 'wrong_drilldown_rejected',
    expected: 'true',
    observed: String(wrongDrilldownRejected),
    passed: wrongDrilldownRejected,
    reason: 'corrupted raw membership is rejected',
  });
  checks.push({
    check: 'candidate_promotion_rejected',
    expected: 'true',
    observed: String(candidatePromotionRejected),
    passed: candidatePromotionRejected,
    reason: 'candidate display tags cannot become active membership without review',
  });

  renderMode('pending');
  const active = root();
  const result = {
    status: checks.every(check => check.passed) ? 'ok' : 'failed',
    currentModeAfterChecks: currentMode,
    modeButtons: document.querySelectorAll('[data-mode-button]').length,
    renderedRows: document.querySelectorAll('[data-bucket-row]').length,
    domReady: Boolean(active),
    visibleBucketCount: Number(active?.getAttribute('data-bucket-count') ?? 0),
    visibleTotalSupport: Number(active?.getAttribute('data-total-support') ?? 0),
    visibleCandidateOverlayRows: Number(active?.getAttribute('data-candidate-overlay-rows') ?? 0),
    visibleReviewRequiredRows: Number(active?.getAttribute('data-review-required-rows') ?? 0),
    membershipMatches,
    pendingMembershipEqualsDisplay,
    wrongDrilldownRejected,
    candidatePromotionRejected,
    modes: {
      raw: summarizeMode(modes.raw),
      display: summarizeMode(modes.display),
      pending: summarizeMode(modes.pending),
    },
    checks,
  };
  const resultScript = document.getElementById('r216-result');
  if (!resultScript) throw new Error('missing result script');
  resultScript.textContent = JSON.stringify(result);
  document.documentElement.setAttribute('data-r216-status', result.status);
}

renderMode('display');
setTimeout(runDomChecks, 0);

export {};
"""


INDEX_CSS = """
:root {
  color-scheme: light;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f6f7f9;
  color: #1c2430;
}
body {
  margin: 0;
  padding: 32px;
}
main {
  max-width: 1160px;
  margin: 0 auto;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}
h1 {
  font-size: 28px;
  margin: 0;
  font-weight: 700;
  letter-spacing: 0;
}
.controls {
  display: inline-flex;
  border: 1px solid #c6ccd5;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}
button {
  appearance: none;
  border: 0;
  border-right: 1px solid #c6ccd5;
  background: #fff;
  color: #2c3747;
  font: inherit;
  font-size: 14px;
  min-width: 88px;
  padding: 9px 14px;
}
button:last-child {
  border-right: 0;
}
button[aria-pressed="true"] {
  background: #26384f;
  color: #fff;
}
.stats {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  margin: 24px 0;
}
.stat {
  background: #fff;
  border: 1px solid #d8dde5;
  border-radius: 8px;
  padding: 12px;
}
.stat-label {
  display: block;
  color: #5c6778;
  font-size: 12px;
}
.stat-value {
  display: block;
  margin-top: 6px;
  font-size: 20px;
}
table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border: 1px solid #d8dde5;
  border-radius: 8px;
  overflow: hidden;
}
th, td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid #e5e8ef;
  font-size: 13px;
}
th {
  color: #536071;
  background: #edf1f5;
  font-weight: 600;
}
tr:last-child td {
  border-bottom: 0;
}
td:nth-child(4),
td:nth-child(5) {
  font-variant-numeric: tabular-nums;
}
"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def find_browser() -> str:
    requested = os.environ.get("AGENTFLAME_BROWSER")
    if requested:
        return requested
    if shutil.which("google-chrome-stable"):
        return str(shutil.which("google-chrome-stable"))
    for name in ["google-chrome", "chromium", "chromium-browser", "firefox"]:
        path = shutil.which(name)
        if path:
            return str(path)
    raise FileNotFoundError("no headless browser found; set AGENTFLAME_BROWSER or install Chrome/Chromium")


def html_script_json(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, separators=(",", ":"))
    return text.replace("</", "<\\/")


def extract_browser_result(dom: str) -> dict[str, Any]:
    match = re.search(
        r'<script id="r216-result" type="application/json">(.*?)</script>',
        dom,
        re.DOTALL,
    )
    if not match:
        raise AssertionError("R216 browser DOM did not include a result script")
    text = html.unescape(match.group(1)).strip()
    if not text:
        raise AssertionError("R216 browser DOM result script is empty")
    return json.loads(text)


def mode_rows(browser_result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mode in ["raw", "display", "pending"]:
        result = browser_result["modes"][mode]
        top = result.get("topBucket") or {}
        rows.append(
            {
                "mode": mode,
                "bucket_count": result["bucketCount"],
                "total_support": result["totalSupport"],
                "candidate_overlay_rows": result["candidateOverlayRows"],
                "review_required_rows": result["reviewRequiredRows"],
                "review_required_support": result["reviewRequiredSupport"],
                "active_merge_rows": result["activeMergeRows"],
                "hidden_other_rows": result["hiddenOtherRows"],
                "top_bucket": f"{top.get('dimension', '')}:{top.get('displayTag', '')}",
                "top_bucket_support": top.get("support", 0),
            }
        )
    return rows


def dom_check_rows(browser_result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "check": row["check"],
            "expected": row["expected"],
            "observed": row["observed"],
            "passed": bool(row["passed"]),
            "reason": row["reason"],
        }
        for row in browser_result["checks"]
    ]


def compile_browser_harness(
    display_rows: list[dict[str, str]],
    drilldown_rows: list[dict[str, str]],
    module_path: Path,
    tmp: Path,
) -> tuple[Path, dict[str, Any]]:
    tsc = FRONTEND_DIR / "node_modules" / ".bin" / "tsc"
    if not tsc.exists():
        raise FileNotFoundError(f"missing TypeScript compiler: {rel(tsc)}")
    src = tmp / "src"
    build = tmp / "build"
    src.mkdir()
    build.mkdir()
    shutil.copyfile(module_path, src / "agentflameDisplayModes.ts")
    (src / "r216_browser_entry.ts").write_text(BROWSER_ENTRY_TS, encoding="utf-8")
    fixture_payload = {
        "displayRows": [
            {field: row.get(field, "") for field in DISPLAY_FIXTURE_FIELDS}
            for row in display_rows
        ],
        "drilldownRows": [
            {field: row.get(field, "") for field in DRILLDOWN_FIXTURE_FIELDS}
            for row in drilldown_rows
        ],
    }
    index_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AgentFlame R216 Browser DOM Smoke</title>
  <style>{INDEX_CSS}</style>
</head>
<body>
  <div id="app"></div>
  <script>window.AGENTFLAME_R216_FIXTURE = {html_script_json(fixture_payload)};</script>
  <script id="r216-result" type="application/json"></script>
  <script type="module" src="./r216_browser_entry.js"></script>
</body>
</html>
"""
    (build / "index.html").write_text(index_html, encoding="utf-8")
    tsc_cmd = [
        str(tsc),
        "--target",
        "ES2020",
        "--module",
        "ES2020",
        "--moduleResolution",
        "node",
        "--strict",
        "--skipLibCheck",
        "--lib",
        "ES2020,DOM",
        "--outDir",
        str(build),
        str(src / "agentflameDisplayModes.ts"),
        str(src / "r216_browser_entry.ts"),
    ]
    start = time.monotonic()
    run = subprocess.run(
        tsc_cmd,
        cwd=FRONTEND_DIR,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    tsc_ms = round((time.monotonic() - start) * 1000.0, 3)
    if run.returncode != 0:
        raise RuntimeError(f"R216 tsc failed:\n{run.stdout}")
    return build, {
        "tsc_ms": tsc_ms,
        "tsc_command": sanitize_text(" ".join(tsc_cmd), [(str(tmp.resolve()), "<tmp>")]),
        "tsc_stdout": run.stdout.strip(),
    }


def run_browser(build_dir: Path, out_dir: Path, browser: str) -> tuple[dict[str, Any], dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    dom_dump_path = out_dir / "dom-dump-r216.html"
    screenshot_path = out_dir / "screenshot-r216.png"
    handler = partial(QuietHandler, directory=str(build_dir))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="agentsight-r216-browser-profile-") as profile:
            url = f"http://127.0.0.1:{port}/index.html"
            cmd = [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--no-first-run",
                "--no-default-browser-check",
                f"--user-data-dir={profile}",
                "--window-size=1280,900",
                "--virtual-time-budget=5000",
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
                timeout=30,
            )
            browser_ms = round((time.monotonic() - start) * 1000.0, 3)
            if run.returncode != 0:
                raise RuntimeError(f"R216 browser failed with {run.returncode}:\n{run.stderr}\n{run.stdout[:2000]}")
            dom_dump_path.write_text(run.stdout, encoding="utf-8")
            browser_result = extract_browser_result(run.stdout)
            if not screenshot_path.exists() or screenshot_path.stat().st_size <= 0:
                raise AssertionError("R216 browser did not create a screenshot")
            command_text = " ".join(cmd[:-1] + ["<local-r216-url>"])
            return browser_result, {
                "browser_ms": browser_ms,
                "browser": browser,
                "browser_command": sanitize_text(
                    command_text,
                    [(profile, "<tmp-browser-profile>")],
                ),
                "browser_stderr": sanitize_text(
                    run.stderr.strip()[:4000],
                    [(profile, "<tmp-browser-profile>")],
                ),
                "dom_dump_path": dom_dump_path,
                "dom_dump_bytes": dom_dump_path.stat().st_size,
                "screenshot_path": screenshot_path,
                "screenshot_bytes": screenshot_path.stat().st_size,
                "url": url,
            }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def summarize(
    browser_result: dict[str, Any],
    r213: dict[str, Any],
    r214: dict[str, Any],
    r215: dict[str, Any],
    compile_info: dict[str, Any],
    browser_info: dict[str, Any],
) -> dict[str, Any]:
    raw = browser_result["modes"]["raw"]
    display = browser_result["modes"]["display"]
    pending = browser_result["modes"]["pending"]
    checks = browser_result.get("checks") or []
    mode_clicks_verified = all(
        row.get("passed") for row in checks if str(row.get("check", "")).startswith("click_")
    )
    return {
        "compiled_frontend_module": True,
        "browser_dom_renderer_exercised": True,
        "production_agentflame_view_exercised": False,
        "visual_drilldown_exercised": False,
        "dom_ready": bool(browser_result.get("domReady")),
        "mode_buttons": as_int(browser_result.get("modeButtons")),
        "rendered_rows": as_int(browser_result.get("renderedRows")),
        "mode_clicks_verified": bool(mode_clicks_verified),
        "current_mode_after_checks": browser_result.get("currentModeAfterChecks"),
        "visible_bucket_count": as_int(browser_result.get("visibleBucketCount")),
        "visible_total_support": as_int(browser_result.get("visibleTotalSupport")),
        "visible_candidate_overlay_rows": as_int(browser_result.get("visibleCandidateOverlayRows")),
        "visible_review_required_rows": as_int(browser_result.get("visibleReviewRequiredRows")),
        "total_support": raw["totalSupport"],
        "raw_bucket_count": raw["bucketCount"],
        "display_bucket_count": display["bucketCount"],
        "pending_bucket_count": pending["bucketCount"],
        "candidate_overlay_rows": pending["candidateOverlayRows"],
        "review_required_rows": pending["reviewRequiredRows"],
        "review_required_support": pending["reviewRequiredSupport"],
        "active_merge_rows": display["activeMergeRows"],
        "hidden_other_rows": max(
            as_int(raw["hiddenOtherRows"]),
            as_int(display["hiddenOtherRows"]),
            as_int(pending["hiddenOtherRows"]),
        ),
        "membership_matches_display_map": bool(browser_result["membershipMatches"]),
        "pending_membership_equals_display": bool(browser_result["pendingMembershipEqualsDisplay"]),
        "wrong_drilldown_rejected": bool(browser_result["wrongDrilldownRejected"]),
        "candidate_promotion_rejected": bool(browser_result["candidatePromotionRejected"]),
        "r213_display_bucket_count": (r213.get("summary") or {}).get("display_bucket_count"),
        "r214_pending_candidate_rows": (r214.get("summary") or {}).get("pending_candidate_rows"),
        "r215_display_bucket_count": (r215.get("summary") or {}).get("display_bucket_count"),
        "tsc_ms": compile_info["tsc_ms"],
        "browser_ms": browser_info["browser_ms"],
        "dom_dump_bytes": browser_info["dom_dump_bytes"],
        "screenshot_bytes": browser_info["screenshot_bytes"],
    }


def claim_gate(summary: dict[str, Any], r209_summary: dict[str, Any]) -> dict[str, bool]:
    return {
        "browser_dom_mode_smoke_supported": bool(
            summary["compiled_frontend_module"]
            and summary["browser_dom_renderer_exercised"]
            and summary["dom_ready"]
            and summary["mode_buttons"] == 3
            and summary["mode_clicks_verified"]
            and summary["membership_matches_display_map"]
            and summary["pending_membership_equals_display"]
            and summary["wrong_drilldown_rejected"]
            and summary["candidate_promotion_rejected"]
            and summary["total_support"] == r209_summary.get("total_support")
        ),
        "support_preserved": summary["total_support"] == r209_summary.get("total_support"),
        "pending_membership_unchanged": bool(summary["pending_membership_equals_display"]),
        "negative_fixtures_rejected": bool(
            summary["wrong_drilldown_rejected"] and summary["candidate_promotion_rejected"]
        ),
        "mode_controls_exercised": bool(summary["mode_clicks_verified"]),
        "browser_dom_harness_supported": True,
        "reads_generated_artifacts_only": True,
        "raw_trace_read": False,
        "llm_called": False,
        "canonical_map_updated": False,
        "production_agentflame_view_supported": False,
        "visual_drilldown_supported": False,
        "semantic_adequacy_supported": False,
        "canonicalization_quality_supported": False,
        "developer_utility_supported": False,
        "community_adoption_supported": False,
    }


def write_markdown(
    path: Path,
    payload: dict[str, Any],
    modes: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> None:
    summary = payload["summary"]
    lines = [
        "# R216 Browser DOM Display-Mode Smoke",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "- Compiles `frontend/src/utils/agentflameDisplayModes.ts` as a browser ES module.",
        "- Runs a temporary headless-browser DOM harness over R209 display-map/drilldown rows.",
        "- Programmatically clicks raw/display/pending mode controls and verifies rendered DOM state.",
        "- Saves a DOM dump and screenshot for visual inspection.",
        "- Does not read or mutate raw Codex/Claude traces.",
        "- Does not call an LLM or update the canonical display map.",
        "- Does not exercise the production React `AgentFlameView` or any human task workflow.",
        "",
        "## Mode Summary",
        "",
        "| mode | buckets | support | candidates | review rows | review support | active merges | hidden other |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in modes:
        lines.append(
            f"| `{row['mode']}` | {row['bucket_count']} | {row['total_support']} | "
            f"{row['candidate_overlay_rows']} | {row['review_required_rows']} | "
            f"{row['review_required_support']} | {row['active_merge_rows']} | {row['hidden_other_rows']} |"
        )
    lines.extend(
        [
            "",
            "## DOM Checks",
            "",
            "| check | observed | pass | reason |",
            "|---|---|---|---|",
        ]
    )
    for row in checks:
        lines.append(f"| `{row['check']}` | {row['observed']} | {row['passed']} | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "R216 supports a browser-DOM harness smoke for the frontend display-mode "
            "module: a real headless browser renders the raw/display/pending DOM, "
            "the mode controls update visible state, pending candidates remain an "
            "overlay, and corrupted membership fixtures are rejected. It does not "
            "support semantic adequacy, merge quality, developer utility, the "
            "production React view, or a visual drilldown/user-study claim.",
            "",
            f"TypeScript compile time: `{summary['tsc_ms']}` ms. Browser run time: `{summary['browser_ms']}` ms.",
            f"DOM dump bytes: `{summary['dom_dump_bytes']}`. Screenshot bytes: `{summary['screenshot_bytes']}`.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_payload(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    r209_json = args.r209_dir / "reversible-display-map-r209.json"
    display_csv = args.r209_dir / "active-display-map-r209.csv"
    drilldown_csv = args.r209_dir / "display-drilldown-r209.csv"
    r213_json = args.r213_dir / "display-mode-drilldown-r213.json"
    r214_json = args.r214_dir / "long-tail-control-r214.json"
    r215_json = args.r215_dir / "frontend-renderer-mode-r215.json"
    for path in [r209_json, display_csv, drilldown_csv, r213_json, r214_json, r215_json, FRONTEND_MODULE]:
        if not path.exists():
            raise FileNotFoundError(f"missing R216 input artifact: {rel(path)}")

    r209 = read_json(r209_json)
    r213 = read_json(r213_json)
    r214 = read_json(r214_json)
    r215 = read_json(r215_json)
    display_rows = read_csv(display_csv)
    drilldown_rows = read_csv(drilldown_csv)
    browser = args.browser or find_browser()
    with tempfile.TemporaryDirectory(prefix="agentsight-r216-") as tmp_text:
        tmp = Path(tmp_text)
        build_dir, compile_info = compile_browser_harness(display_rows, drilldown_rows, FRONTEND_MODULE, tmp)
        browser_result, browser_info = run_browser(build_dir, args.out_dir, browser)

    modes = mode_rows(browser_result)
    checks = dom_check_rows(browser_result)
    summary = summarize(browser_result, r213, r214, r215, compile_info, browser_info)
    r209_summary = r209.get("summary") or {}
    status = "browser_dom_mode_smoke_ready_no_quality_claims"
    dom_dump_path = browser_info["dom_dump_path"]
    screenshot_path = browser_info["screenshot_path"]

    payload = {
        "run_id": "R216",
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "claim": "C3 browser DOM display-mode consumer; C6 protocol/gate only",
        "claim_boundary": (
            "R216 compiles the frontend TypeScript display-mode consumer as a browser "
            "ES module and exercises it in a temporary headless-browser DOM harness. "
            "It is not a production React view, semantic adequacy, merge-quality, or "
            "developer-utility result."
        ),
        "input": {
            "r209_json": rel(r209_json),
            "r209_json_sha256": sha256_file(r209_json),
            "display_csv": rel(display_csv),
            "display_csv_sha256": sha256_file(display_csv),
            "drilldown_csv": rel(drilldown_csv),
            "drilldown_csv_sha256": sha256_file(drilldown_csv),
            "r213_json": rel(r213_json),
            "r213_json_sha256": sha256_file(r213_json),
            "r214_json": rel(r214_json),
            "r214_json_sha256": sha256_file(r214_json),
            "r215_json": rel(r215_json),
            "r215_json_sha256": sha256_file(r215_json),
            "frontend_module": rel(FRONTEND_MODULE),
            "frontend_module_sha256": sha256_file(FRONTEND_MODULE),
        },
        "method": {
            "frontend_module": rel(FRONTEND_MODULE),
            "compile": "TypeScript module compiled as ES2020 browser modules with frontend node_modules/.bin/tsc",
            "execute": "temporary DOM harness served over localhost and executed by headless browser",
            "browser": browser,
            "dom_checks": [
                "raw/display/pending buttons update rendered DOM mode",
                "visible pending summary exposes candidate and review overlays",
                "active display drilldown membership matches R209 rows",
                "corrupted drilldown and candidate-as-active fixtures are rejected",
            ],
            "quality_boundary": "browser DOM harness only; no production React view, adequacy, quality, utility, or human-task claim",
            "compile_info": compile_info,
            "browser_info": {
                key: rel(value) if isinstance(value, Path) else value
                for key, value in browser_info.items()
                if key not in {"url"}
            },
        },
        "summary": summary,
        "claim_gate": claim_gate(summary, r209_summary),
        "outputs": {
            "summary_json": rel(args.out_dir / "browser-dom-mode-r216.json"),
            "summary_md": rel(args.out_dir / "browser-dom-mode-r216.md"),
            "mode_summary_csv": rel(args.out_dir / "mode-summary-r216.csv"),
            "dom_checks_csv": rel(args.out_dir / "dom-checks-r216.csv"),
            "dom_dump_html": rel(dom_dump_path),
            "dom_dump_html_sha256": sha256_file(dom_dump_path),
            "screenshot_png": rel(screenshot_path),
            "screenshot_png_sha256": sha256_file(screenshot_path),
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    return payload, modes, checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r209-dir", type=Path, default=DEFAULT_R209_DIR)
    parser.add_argument("--r213-dir", type=Path, default=DEFAULT_R213_DIR)
    parser.add_argument("--r214-dir", type=Path, default=DEFAULT_R214_DIR)
    parser.add_argument("--r215-dir", type=Path, default=DEFAULT_R215_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--browser", type=str, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, modes, checks = build_payload(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "browser-dom-mode-r216.json", payload)
    write_markdown(args.out_dir / "browser-dom-mode-r216.md", payload, modes, checks)
    write_csv(args.out_dir / "mode-summary-r216.csv", modes, MODE_FIELDS)
    write_csv(args.out_dir / "dom-checks-r216.csv", checks, DOM_CHECK_FIELDS)
    print(json.dumps({"status": payload["status"], "summary_json": payload["outputs"]["summary_json"]}))


if __name__ == "__main__":
    main()
