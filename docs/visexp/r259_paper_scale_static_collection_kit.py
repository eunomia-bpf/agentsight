#!/usr/bin/env python3
"""R259: paper-scale static collection kit and export smoke.

R258 produces a sendable paper-scale tarball. R259 turns the same C5/C6
materials into static browser forms, verifies that representative pages load in
headless Chrome, and checks that synthetic CSV exports preserve the R195 return
shape. It creates no real participant responses or human labels.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_DIR = SCRIPT_DIR / "out"
RUN_ID = "R259"
DEFAULT_OUT_DIR = OUT_DIR / "human-evidence-paper-scale-static-kit-r259"

R249_DIR = OUT_DIR / "user-task-paper-r249"
R249_MANIFEST = R249_DIR / "manifest.json"
R249_TEMPLATE = R249_DIR / "responses" / "user-task-response-template-r249-paper.csv"
R249_ASSIGNMENTS = R249_DIR / "user-task-assignments-r249-paper.csv"
R252_DIR = OUT_DIR / "tag-adequacy-paper-r252"
R252_MANIFEST = R252_DIR / "manifest.json"
R258_JSON = OUT_DIR / "human-evidence-paper-scale-bundle-r258" / "human-evidence-paper-scale-bundle-r258.json"

LABEL_SHEETS = [
    {
        "key": "r124_labeler_1",
        "group": "r124",
        "title": "R124 tag adequacy labeler 1",
        "source": R252_DIR / "labeler-packets" / "L01" / "r124-labeler-1.csv",
        "output_name": "r124-labeler-1.csv",
        "label_field": "label",
        "notes_field": "notes",
        "labels": ["adequate", "generic_noisy", "misleading"],
        "visible_fields": ["row_id", "fragment_level", "redacted_preview", "candidate_tag", "rubric"],
    },
    {
        "key": "r124_labeler_2",
        "group": "r124",
        "title": "R124 tag adequacy labeler 2",
        "source": R252_DIR / "labeler-packets" / "L02" / "r124-labeler-2.csv",
        "output_name": "r124-labeler-2.csv",
        "label_field": "label",
        "notes_field": "notes",
        "labels": ["adequate", "generic_noisy", "misleading"],
        "visible_fields": ["row_id", "fragment_level", "redacted_preview", "candidate_tag", "rubric"],
    },
    {
        "key": "r190_labeler_1",
        "group": "r190",
        "title": "R190 merge-risk labeler 1",
        "source": R252_DIR / "labeler-packets" / "L01" / "r190-labeler-1.csv",
        "output_name": "r190-labeler-1.csv",
        "label_field": "audit_label",
        "notes_field": "audit_notes",
        "labels": ["acceptable", "overmerge", "undermerge", "unclear"],
        "visible_fields": [
            "audit_id",
            "audit_type",
            "dimension",
            "raw_tag",
            "canonical_tag",
            "reason",
            "support",
            "risk_reasons",
            "raw_top_processes",
            "raw_top_effects",
            "raw_top_paths",
        ],
    },
    {
        "key": "r190_labeler_2",
        "group": "r190",
        "title": "R190 merge-risk labeler 2",
        "source": R252_DIR / "labeler-packets" / "L02" / "r190-labeler-2.csv",
        "output_name": "r190-labeler-2.csv",
        "label_field": "audit_label",
        "notes_field": "audit_notes",
        "labels": ["acceptable", "overmerge", "undermerge", "unclear"],
        "visible_fields": [
            "audit_id",
            "audit_type",
            "dimension",
            "raw_tag",
            "canonical_tag",
            "reason",
            "support",
            "risk_reasons",
            "raw_top_processes",
            "raw_top_effects",
            "raw_top_paths",
        ],
    },
    {
        "key": "r203_labeler_1",
        "group": "r203",
        "title": "R203 long-tail promotion labeler 1",
        "source": R252_DIR / "labeler-packets" / "L01" / "r203-labeler-1.csv",
        "output_name": "r203-labeler-1.csv",
        "label_field": "promotion_label",
        "notes_field": "promotion_notes",
        "labels": ["promote", "keep_raw", "reject", "split", "unclear"],
        "visible_fields": [
            "promotion_id",
            "dimension",
            "raw_tag",
            "canonical_tag",
            "governance_action",
            "governance_reasons",
            "support",
            "top_processes",
            "top_effects",
            "regenerated_tag",
            "proposed_action",
        ],
    },
    {
        "key": "r203_labeler_2",
        "group": "r203",
        "title": "R203 long-tail promotion labeler 2",
        "source": R252_DIR / "labeler-packets" / "L02" / "r203-labeler-2.csv",
        "output_name": "r203-labeler-2.csv",
        "label_field": "promotion_label",
        "notes_field": "promotion_notes",
        "labels": ["promote", "keep_raw", "reject", "split", "unclear"],
        "visible_fields": [
            "promotion_id",
            "dimension",
            "raw_tag",
            "canonical_tag",
            "governance_action",
            "governance_reasons",
            "support",
            "top_processes",
            "top_effects",
            "regenerated_tag",
            "proposed_action",
        ],
    },
]

FORBIDDEN_OUTPUT_TOKENS = [
    "user-task-answer-key.csv",
    "answer_json",
    "expected_response",
    "correct_response",
    "score_user_task_results.py",
]


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


def sha256_file(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def js_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def page_shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root {{
  color-scheme: light;
  --bg: #f7f7f4;
  --panel: #ffffff;
  --ink: #1d1f23;
  --muted: #5d6673;
  --line: #d8dadd;
  --accent: #2764c5;
  --warn: #8a4b08;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
header {{
  position: sticky;
  top: 0;
  z-index: 5;
  padding: 14px 18px;
  border-bottom: 1px solid var(--line);
  background: rgba(255,255,255,0.96);
}}
main {{ padding: 18px; max-width: 1500px; margin: 0 auto; }}
h1 {{ margin: 0 0 4px; font-size: 22px; }}
h2 {{ margin: 24px 0 8px; font-size: 18px; }}
p {{ margin: 6px 0; }}
a {{ color: var(--accent); }}
.muted {{ color: var(--muted); }}
.warn {{ color: var(--warn); font-weight: 650; }}
.toolbar {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-top: 10px; }}
button {{
  appearance: none;
  border: 1px solid #174d9d;
  background: var(--accent);
  color: white;
  border-radius: 6px;
  padding: 8px 11px;
  font-weight: 650;
  cursor: pointer;
}}
button.secondary {{ background: #fff; color: var(--accent); }}
table {{
  width: 100%;
  border-collapse: collapse;
  background: var(--panel);
  border: 1px solid var(--line);
}}
th, td {{
  border-bottom: 1px solid var(--line);
  border-right: 1px solid var(--line);
  padding: 7px;
  vertical-align: top;
}}
th {{ position: sticky; top: 92px; background: #f0f2f5; z-index: 3; text-align: left; }}
td.readonly {{ max-width: 320px; overflow-wrap: anywhere; }}
textarea, input, select {{
  width: 100%;
  min-width: 120px;
  border: 1px solid #c7ccd2;
  border-radius: 4px;
  padding: 6px;
  font: inherit;
  background: white;
}}
textarea {{ min-height: 62px; resize: vertical; }}
pre.packet {{
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: #ffffff;
  border: 1px solid var(--line);
  padding: 14px;
  border-radius: 6px;
}}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
.card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 12px; }}
.status {{ margin-left: 8px; color: var(--muted); }}
@media (max-width: 800px) {{
  main {{ padding: 12px; }}
  th {{ top: 116px; }}
  th, td {{ padding: 6px; }}
}}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def export_script(rows: list[dict[str, str]], fields: list[str], filename: str, mutators: list[dict[str, str]]) -> str:
    return f"""<script>
const ROWS = {js_json(rows)};
const FIELDS = {js_json(fields)};
const OUTPUT_NAME = {js_json(filename)};
const MUTATORS = {js_json(mutators)};

function csvEscape(value) {{
  const s = String(value ?? "");
  if (/[",\\n\\r]/.test(s)) return '"' + s.replaceAll('"', '""') + '"';
  return s;
}}

function rowsFromForm() {{
  return ROWS.map((row, i) => {{
    const next = {{...row}};
    for (const m of MUTATORS) {{
      const el = document.getElementById(`${{m.field}}-${{i}}`);
      next[m.field] = el ? el.value : "";
    }}
    return next;
  }});
}}

function validateRows() {{
  let missing = 0;
  let badJson = 0;
  const rows = rowsFromForm();
  for (const row of rows) {{
    for (const m of MUTATORS) {{
      const value = row[m.field] || "";
      if (m.required && value.trim() === "") missing += 1;
      if (m.kind === "json" && value.trim() !== "") {{
        try {{ JSON.parse(value); }} catch (err) {{ badJson += 1; }}
      }}
    }}
  }}
  const status = document.getElementById("status");
  if (status) status.textContent = `missing required cells: ${{missing}}; invalid JSON cells: ${{badJson}}`;
  return {{missing, badJson}};
}}

function exportCsv() {{
  const result = validateRows();
  if (result.badJson > 0) {{
    alert("Fix invalid JSON before export.");
    return;
  }}
  const rows = rowsFromForm();
  const lines = [FIELDS.map(csvEscape).join(",")];
  for (const row of rows) lines.push(FIELDS.map((field) => csvEscape(row[field] ?? "")).join(","));
  const blob = new Blob([lines.join("\\n") + "\\n"], {{type: "text/csv;charset=utf-8"}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = OUTPUT_NAME;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}}

document.addEventListener("input", validateRows);
document.addEventListener("change", validateRows);
document.addEventListener("DOMContentLoaded", validateRows);
</script>
"""


def participant_page(participant_id: str, packet_md: str, rows: list[dict[str, str]], fields: list[str]) -> str:
    mutators = [
        {"field": "response_json", "required": "true", "kind": "json"},
        {"field": "task_time_seconds", "required": "true", "kind": "number"},
        {"field": "confidence", "required": "true", "kind": "number"},
        {"field": "notes", "required": "", "kind": "text"},
    ]
    row_html = []
    for index, row in enumerate(rows):
        row_html.append(
            "<tr>"
            f"<td>{html.escape(row['order_index'])}</td>"
            f"<td>{html.escape(row['task_id'])}</td>"
            f"<td>{html.escape(row['condition'])}</td>"
            f"<td>{html.escape(row['packet_id'])}</td>"
            f"<td><textarea id=\"response_json-{index}\">{{}}</textarea></td>"
            f"<td><input id=\"task_time_seconds-{index}\" inputmode=\"decimal\" placeholder=\"seconds\"></td>"
            f"<td><select id=\"confidence-{index}\"><option value=\"\"></option>"
            + "".join(f"<option value=\"{n}\">{n}</option>" for n in range(1, 6))
            + "</select></td>"
            f"<td><textarea id=\"notes-{index}\"></textarea></td>"
            "</tr>"
        )
    body = f"""<header>
<h1>R259 paper-scale participant form {html.escape(participant_id)}</h1>
<p class="muted">Static local form. Export the CSV after completing every row.</p>
<div class="toolbar">
<button onclick="exportCsv()">Export {html.escape(participant_id)} CSV</button>
<button class="secondary" onclick="validateRows()">Validate</button>
<span id="status" class="status"></span>
</div>
</header>
<main>
<p class="warn">This form records only participant responses. It contains no hidden solution data.</p>
<h2>Task Packet</h2>
<pre class="packet">{html.escape(packet_md)}</pre>
<h2>Responses</h2>
<table>
<thead><tr><th>Order</th><th>Task</th><th>Condition</th><th>Packet</th><th>response_json</th><th>seconds</th><th>confidence</th><th>notes</th></tr></thead>
<tbody>{''.join(row_html)}</tbody>
</table>
</main>
{export_script(rows, fields, f"user-task-r249-responses-{participant_id}.csv", mutators)}
"""
    return page_shell(f"R259 participant {participant_id}", body)


def labeler_page(config: dict[str, Any], rows: list[dict[str, str]], fields: list[str]) -> str:
    label_field = config["label_field"]
    notes_field = config["notes_field"]
    mutators = [
        {"field": label_field, "required": "true", "kind": "text"},
        {"field": notes_field, "required": "", "kind": "text"},
    ]
    visible_fields = [field for field in config["visible_fields"] if field in fields]
    label_options = "".join(
        f"<option value=\"{html.escape(label)}\">{html.escape(label)}</option>"
        for label in config["labels"]
    )
    rows_html = []
    for index, row in enumerate(rows):
        cells = [f"<td class=\"readonly\">{html.escape(row.get(field, ''))}</td>" for field in visible_fields]
        cells.append(
            f"<td><select id=\"{html.escape(label_field)}-{index}\"><option value=\"\"></option>{label_options}</select></td>"
        )
        cells.append(f"<td><textarea id=\"{html.escape(notes_field)}-{index}\"></textarea></td>")
        rows_html.append("<tr>" + "".join(cells) + "</tr>")
    header_cells = "".join(f"<th>{html.escape(field)}</th>" for field in visible_fields)
    body = f"""<header>
<h1>{html.escape(config['title'])}</h1>
<p class="muted">Static local form. Export filename: <code>{html.escape(config['output_name'])}</code>.</p>
<div class="toolbar">
<button onclick="exportCsv()">Export R195 CSV</button>
<button class="secondary" onclick="validateRows()">Validate</button>
<span id="status" class="status"></span>
</div>
</header>
<main>
<p class="warn">Fill the label column independently. Leave notes blank unless a row needs explanation.</p>
<table>
<thead><tr>{header_cells}<th>{html.escape(label_field)}</th><th>{html.escape(notes_field)}</th></tr></thead>
<tbody>{''.join(rows_html)}</tbody>
</table>
</main>
{export_script(rows, fields, config["output_name"], mutators)}
"""
    return page_shell(config["title"], body)


def merge_page(fields: list[str]) -> str:
    body = f"""<header>
<h1>R259 paper-scale participant response merge</h1>
<p class="muted">Select returned P01-P12 CSV files, then export one R195-ready C5 file.</p>
<div class="toolbar">
<input id="files" type="file" multiple accept=".csv,text/csv">
<button onclick="mergeFiles()">Read selected CSVs</button>
<button class="secondary" onclick="exportMerged()">Export completed C5 CSV</button>
<span id="status" class="status"></span>
</div>
</header>
<main>
<p class="warn">This page only combines returned participant files. It does not score or infer any answer.</p>
<table>
<thead><tr><th>participant</th><th>rows</th><th>file</th><th>status</th></tr></thead>
<tbody id="summary"></tbody>
</table>
</main>
<script>
const FIELDS = {js_json(fields)};
const OUTPUT_NAME = "user-task-response-template-r249-paper.csv";
let MERGED_ROWS = [];

function csvEscape(value) {{
  const s = String(value ?? "");
  if (/[",\\n\\r]/.test(s)) return '"' + s.replaceAll('"', '""') + '"';
  return s;
}}

function parseCsv(text) {{
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;
  for (let i = 0; i < text.length; i++) {{
    const ch = text[i];
    if (quoted) {{
      if (ch === '"') {{
        if (text[i + 1] === '"') {{ cell += '"'; i += 1; }} else {{ quoted = false; }}
      }} else {{
        cell += ch;
      }}
    }} else if (ch === '"') {{
      quoted = true;
    }} else if (ch === ",") {{
      row.push(cell); cell = "";
    }} else if (ch === "\\n") {{
      row.push(cell); rows.push(row); row = []; cell = "";
    }} else if (ch !== "\\r") {{
      cell += ch;
    }}
  }}
  if (cell !== "" || row.length) {{ row.push(cell); rows.push(row); }}
  return rows.filter((r) => r.length > 1 || r[0] !== "");
}}

function objectsFromCsv(text) {{
  const records = parseCsv(text);
  if (records.length === 0) return {{rows: [], error: "empty file"}};
  const header = records[0];
  const headerOk = FIELDS.length === header.length && FIELDS.every((field, i) => field === header[i]);
  if (!headerOk) return {{rows: [], error: "header mismatch"}};
  const rows = records.slice(1).map((record) => {{
    const row = {{}};
    FIELDS.forEach((field, i) => row[field] = record[i] ?? "");
    return row;
  }});
  return {{rows, error: ""}};
}}

function renderSummary(items) {{
  const tbody = document.getElementById("summary");
  tbody.innerHTML = items.map((item) => `<tr><td>${{item.participant}}</td><td>${{item.rows}}</td><td>${{item.file}}</td><td>${{item.status}}</td></tr>`).join("");
  const status = document.getElementById("status");
  const total = MERGED_ROWS.length;
  const participants = new Set(MERGED_ROWS.map((row) => row.participant_id)).size;
  status.textContent = `merged rows: ${{total}}; participants: ${{participants}}`;
}}

async function mergeFiles() {{
  const input = document.getElementById("files");
  const files = Array.from(input.files || []);
  const items = [];
  MERGED_ROWS = [];
  for (const file of files) {{
    const text = await file.text();
    const parsed = objectsFromCsv(text);
    if (parsed.error) {{
      items.push({{participant: "", rows: 0, file: file.name, status: parsed.error}});
      continue;
    }}
    MERGED_ROWS.push(...parsed.rows);
    const participantSet = new Set(parsed.rows.map((row) => row.participant_id));
    items.push({{participant: Array.from(participantSet).join(";"), rows: parsed.rows.length, file: file.name, status: "ok"}});
  }}
  renderSummary(items);
}}

function exportMerged() {{
  if (MERGED_ROWS.length === 0) {{
    alert("Read participant CSVs first.");
    return;
  }}
  const lines = [FIELDS.map(csvEscape).join(",")];
  for (const row of MERGED_ROWS) lines.push(FIELDS.map((field) => csvEscape(row[field] ?? "")).join(","));
  const blob = new Blob([lines.join("\\n") + "\\n"], {{type: "text/csv;charset=utf-8"}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = OUTPUT_NAME;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}}
</script>
"""
    return page_shell("R259 C5 merge", body)


def decode_const(html_text: str, name: str) -> Any:
    marker = f"const {name} = "
    start = html_text.find(marker)
    if start < 0:
        raise ValueError(f"missing JS const {name}")
    payload = html_text[start + len(marker) :]
    value, _ = json.JSONDecoder().raw_decode(payload)
    return value


def form_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return {
        "path": rel(path),
        "rows": decode_const(text, "ROWS") if "const ROWS =" in text else None,
        "fields": decode_const(text, "FIELDS"),
        "output_name": decode_const(text, "OUTPUT_NAME"),
        "mutators": decode_const(text, "MUTATORS") if "const MUTATORS =" in text else None,
        "sha256": sha256_file(path),
    }


def csv_info(path: Path) -> dict[str, Any]:
    rows, fields = read_csv(path)
    return {
        "path": rel(path),
        "sha256": sha256_file(path),
        "row_count": len(rows),
        "fields": fields,
    }


def file_url(path: Path) -> str:
    return "file://" + quote(str(path.resolve()))


def find_browser(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    for candidate in ["google-chrome", "chromium", "chromium-browser"]:
        found = shutil.which(candidate)
        if found:
            return found
    return None


def browser_dump(browser: str | None, page: Path, expected: str) -> dict[str, Any]:
    if not browser:
        return {
            "page": rel(page),
            "expected": expected,
            "ran": False,
            "status": "skipped_no_browser",
            "returncode": None,
            "expected_found": False,
            "stdout_bytes": 0,
            "stderr_tail": "",
        }
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--dump-dom",
        file_url(page),
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, timeout=30)
    expected_found = expected in proc.stdout
    return {
        "page": rel(page),
        "expected": expected,
        "ran": True,
        "cmd": cmd,
        "returncode": proc.returncode,
        "expected_found": expected_found,
        "stdout_bytes": len(proc.stdout.encode("utf-8")),
        "stderr_tail": proc.stderr[-2000:],
        "status": "ok" if proc.returncode == 0 and expected_found else "fail",
    }


def leak_scan(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in FORBIDDEN_OUTPUT_TOKENS:
            if token in text:
                hits.append({"path": rel(path) or str(path), "token": token})
    return {
        "status": "ok" if not hits else "fail",
        "forbidden_tokens": FORBIDDEN_OUTPUT_TOKENS,
        "hits": hits,
    }


def export_rows(rows: list[dict[str, str]], mutators: list[dict[str, str]] | None) -> list[dict[str, str]]:
    exported: list[dict[str, str]] = []
    for row in rows:
        next_row = dict(row)
        for mutator in mutators or []:
            field = mutator["field"]
            if field == "response_json":
                next_row[field] = json.dumps(
                    {
                        "r259_export_smoke": True,
                        "task_id": row.get("task_id", ""),
                        "condition": row.get("condition", ""),
                    },
                    sort_keys=True,
                )
            elif field == "task_time_seconds":
                next_row[field] = "1.0"
            elif field == "confidence":
                next_row[field] = "3"
            elif field.endswith("notes") or field == "notes":
                next_row[field] = "r259_synthetic_export_smoke_not_human_evidence"
            else:
                next_row[field] = ""
        exported.append(next_row)
    return exported


def build_kit(out_dir: Path) -> dict[str, Any]:
    r249 = read_json(R249_MANIFEST)
    r252 = read_json(R252_MANIFEST)
    r258 = read_json(R258_JSON)
    template_rows, template_fields = read_csv(R249_TEMPLATE)
    assignment_rows, assignment_fields = read_csv(R249_ASSIGNMENTS)

    forms: dict[str, list[dict[str, Any]]] = {
        "participant_forms": [],
        "labeler_forms": [],
        "coordinator_forms": [],
    }

    participant_dir = out_dir / "participants"
    labeler_dir = out_dir / "labelers"
    coordinator_dir = out_dir / "coordinator"
    participant_ids = [f"P{i:02d}" for i in range(1, 13)]

    for participant_id in participant_ids:
        rows = [row for row in template_rows if row["participant_id"] == participant_id]
        packet_md_path = R249_DIR / "participants" / f"{participant_id}.md"
        packet_md = packet_md_path.read_text(encoding="utf-8")
        html_path = participant_dir / f"{participant_id}.html"
        write_text(html_path, participant_page(participant_id, packet_md, rows, template_fields))
        forms["participant_forms"].append(
            {
                "participant_id": participant_id,
                "html_path": rel(html_path),
                "packet_md": rel(packet_md_path),
                "output_name": f"user-task-r249-responses-{participant_id}.csv",
                "row_count": len(rows),
                "sha256": sha256_file(html_path),
            }
        )

    for config in LABEL_SHEETS:
        rows, fields = read_csv(config["source"])
        html_path = labeler_dir / f"{config['output_name'].removesuffix('.csv')}.html"
        write_text(html_path, labeler_page(config, rows, fields))
        forms["labeler_forms"].append(
            {
                "key": config["key"],
                "group": config["group"],
                "title": config["title"],
                "html_path": rel(html_path),
                "source": rel(config["source"]),
                "output_name": config["output_name"],
                "row_count": len(rows),
                "label_field": config["label_field"],
                "notes_field": config["notes_field"],
                "sha256": sha256_file(html_path),
            }
        )

    merge_html = coordinator_dir / "c5-merge.html"
    write_text(merge_html, merge_page(template_fields))
    forms["coordinator_forms"].append(
        {
            "key": "c5_merge",
            "html_path": rel(merge_html),
            "output_name": "user-task-response-template-r249-paper.csv",
            "row_count": len(template_rows),
            "sha256": sha256_file(merge_html),
        }
    )

    index = render_index(forms, r249, r252, r258)
    index_path = out_dir / "index.html"
    write_text(index_path, index)

    manifest = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "status": "static_collection_kit_ready_no_outcomes",
        "generated_at": now_iso(),
        "source_command": "python3 docs/visexp/r259_paper_scale_static_collection_kit.py",
        "source_artifacts": {
            "r249_manifest": rel(R249_MANIFEST),
            "r249_response_template": rel(R249_TEMPLATE),
            "r249_assignments": rel(R249_ASSIGNMENTS),
            "r252_manifest": rel(R252_MANIFEST),
            "r258_summary": rel(R258_JSON),
        },
        "forms": forms,
        "counts": {
            "participant_forms": len(forms["participant_forms"]),
            "participant_response_rows": len(template_rows),
            "assignment_rows": len(assignment_rows),
            "assignment_fields": assignment_fields,
            "labeler_forms": len(forms["labeler_forms"]),
            "labeler_rows_total": sum(form["row_count"] for form in forms["labeler_forms"]),
            "coordinator_forms": len(forms["coordinator_forms"]),
        },
        "claim_boundary": (
            "R259 generates static collection forms and synthetic export checks only. "
            "It creates no real participant responses, no human labels, and no weak-accept evidence."
        ),
        "claim_gate": {
            "c5_supported": False,
            "c6_supported": False,
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "long_tail_promotion_review_supported": False,
            "weak_accept_supported": False,
            "outcome_evidence_added": False,
            "requires_real_human_returns": True,
        },
        "artifacts": {
            "index": rel(index_path),
            "manifest": rel(out_dir / "static-collection-kit-r259.json"),
            "summary_md": rel(out_dir / "static-collection-kit-r259.md"),
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "generator": rel(Path(__file__)),
            "raw_trace_read": False,
            "llm_called": False,
            "participant_responses_added": 0,
            "human_labels_added": 0,
            "source_hashes": {
                rel(R249_MANIFEST): sha256_file(R249_MANIFEST),
                rel(R252_MANIFEST): sha256_file(R252_MANIFEST),
                rel(R258_JSON): sha256_file(R258_JSON),
            },
        },
    }
    return manifest


def render_index(forms: dict[str, list[dict[str, Any]]], r249: dict[str, Any], r252: dict[str, Any], r258: dict[str, Any]) -> str:
    participant_cards = "\n".join(
        f"<div class=\"card\"><a href=\"participants/{form['participant_id']}.html\">{form['participant_id']}</a><p>{form['row_count']} tasks</p></div>"
        for form in forms["participant_forms"]
    )
    labeler_cards = "\n".join(
        f"<div class=\"card\"><a href=\"labelers/{Path(form['html_path']).name}\">{html.escape(form['title'])}</a><p>{form['row_count']} rows</p></div>"
        for form in forms["labeler_forms"]
    )
    body = f"""<header>
<h1>R259 paper-scale static collection kit</h1>
<p class="muted">Static HTML forms for C5 participant responses and C6 label collection.</p>
</header>
<main>
<p class="warn">This kit is a collection interface only. It contains no answers and creates no evidence until real returns are scored.</p>
<div class="grid">
<div class="card"><strong>C5 participant packets</strong><p>{html.escape(str(r249.get('participant_packet_count')))} packets, {html.escape(str(r258.get('collection_inputs', {}).get('c5_response_rows')))} response rows.</p></div>
<div class="card"><strong>C6 labeler packets</strong><p>{html.escape(str(r252.get('labeler_packet_count')))} labelers, {html.escape(str(r252.get('total_independent_label_decisions_required')))} independent decisions.</p></div>
<div class="card"><strong>Coordinator</strong><p><a href="coordinator/c5-merge.html">Merge participant CSVs</a></p></div>
</div>
<h2>Participants</h2>
<div class="grid">{participant_cards}</div>
<h2>Labelers</h2>
<div class="grid">{labeler_cards}</div>
</main>
"""
    return page_shell("R259 paper-scale static collection kit", body)


def run_smoke(out_dir: Path, manifest: dict[str, Any], browser_path: str | None) -> dict[str, Any]:
    export_dir = out_dir / "synthetic-exports"
    template_rows, template_fields = read_csv(R249_TEMPLATE)
    expected_by_participant: dict[str, int] = {}
    for row in template_rows:
        expected_by_participant[row["participant_id"]] = expected_by_participant.get(row["participant_id"], 0) + 1

    participant_exports: list[dict[str, Any]] = []
    for form in manifest["forms"]["participant_forms"]:
        html_path = REPO_ROOT / form["html_path"]
        payload = form_payload(html_path)
        if payload["fields"] != template_fields:
            raise ValueError(f"participant field mismatch for {form['participant_id']}")
        exported = export_rows(payload["rows"] or [], payload["mutators"])
        out_csv = export_dir / "participants" / form["output_name"]
        write_csv(out_csv, exported, payload["fields"])
        reread_rows, reread_fields = read_csv(out_csv)
        participant_exports.append(
            {
                "participant_id": form["participant_id"],
                "html": payload["path"],
                "output": csv_info(out_csv),
                "expected_rows": expected_by_participant[form["participant_id"]],
                "fields_match_template": reread_fields == template_fields,
                "json_cells_valid": all(json.loads(row["response_json"]) for row in reread_rows),
            }
        )

    merged_rows: list[dict[str, str]] = []
    for export in participant_exports:
        rows, fields = read_csv(REPO_ROOT / export["output"]["path"])
        if fields != template_fields:
            raise ValueError(f"merged input field mismatch for {export['participant_id']}")
        merged_rows.extend(rows)
    merged_csv = export_dir / "user-task-response-template-r249-paper.csv"
    write_csv(merged_csv, merged_rows, template_fields)
    merged_info = csv_info(merged_csv)
    participant_counts: dict[str, int] = {}
    for row in merged_rows:
        participant_counts[row["participant_id"]] = participant_counts.get(row["participant_id"], 0) + 1

    labeler_exports: list[dict[str, Any]] = []
    for form in manifest["forms"]["labeler_forms"]:
        html_path = REPO_ROOT / form["html_path"]
        payload = form_payload(html_path)
        source_rows, source_fields = read_csv(REPO_ROOT / form["source"])
        if payload["fields"] != source_fields:
            raise ValueError(f"labeler field mismatch for {form['key']}")
        exported = export_rows(payload["rows"] or [], payload["mutators"])
        out_csv = export_dir / "labelers" / form["output_name"]
        write_csv(out_csv, exported, payload["fields"])
        reread_rows, reread_fields = read_csv(out_csv)
        labeler_exports.append(
            {
                "key": form["key"],
                "html": payload["path"],
                "output": csv_info(out_csv),
                "source_rows": len(source_rows),
                "fields_match_source": reread_fields == source_fields,
                "label_cells_filled": sum(1 for row in reread_rows if row.get(form["label_field"], "")),
            }
        )

    coordinator_path = out_dir / "coordinator" / "c5-merge.html"
    coordinator_payload = {
        "path": rel(coordinator_path),
        "fields": decode_const(coordinator_path.read_text(encoding="utf-8"), "FIELDS"),
        "output_name": decode_const(coordinator_path.read_text(encoding="utf-8"), "OUTPUT_NAME"),
    }

    browser = find_browser(browser_path)
    browser_pages = [
        (out_dir / "index.html", "R259 paper-scale static collection kit"),
        (out_dir / "coordinator" / "c5-merge.html", "R259 paper-scale participant response merge"),
        (out_dir / "participants" / "P01.html", "R259 paper-scale participant form P01"),
        (out_dir / "labelers" / "r124-labeler-1.html", "R124 tag adequacy labeler 1"),
        (out_dir / "labelers" / "r190-labeler-1.html", "R190 merge-risk labeler 1"),
        (out_dir / "labelers" / "r203-labeler-1.html", "R203 long-tail promotion labeler 1"),
    ]
    browser_checks = [browser_dump(browser, page, expected) for page, expected in browser_pages]

    generated_paths = sorted(path for path in export_dir.rglob("*") if path.is_file())
    generated_paths.extend(
        [
            out_dir / "index.html",
            out_dir / "coordinator" / "c5-merge.html",
            *[REPO_ROOT / form["html_path"] for form in manifest["forms"]["participant_forms"]],
            *[REPO_ROOT / form["html_path"] for form in manifest["forms"]["labeler_forms"]],
        ]
    )
    leak = leak_scan(generated_paths)

    checks = {
        "participant_form_count": len(manifest["forms"]["participant_forms"]) == 12,
        "participant_export_count": len(participant_exports) == 12,
        "participant_rows_ok": all(item["output"]["row_count"] == item["expected_rows"] for item in participant_exports),
        "participant_fields_ok": all(item["fields_match_template"] for item in participant_exports),
        "participant_json_ok": all(item["json_cells_valid"] for item in participant_exports),
        "merged_output_name_ok": coordinator_payload["output_name"] == "user-task-response-template-r249-paper.csv",
        "merged_fields_ok": coordinator_payload["fields"] == template_fields and merged_info["fields"] == template_fields,
        "merged_rows_ok": merged_info["row_count"] == len(template_rows) == 168,
        "merged_participants_ok": participant_counts == expected_by_participant,
        "labeler_form_count": len(manifest["forms"]["labeler_forms"]) == 6,
        "labeler_export_count": len(labeler_exports) == 6,
        "labeler_fields_ok": all(item["fields_match_source"] for item in labeler_exports),
        "labeler_rows_ok": all(item["output"]["row_count"] == item["source_rows"] for item in labeler_exports),
        "labeler_cells_blank": all(item["label_cells_filled"] == 0 for item in labeler_exports),
        "browser_checks_ok": all(item["status"] == "ok" for item in browser_checks),
        "leak_scan_ok": leak["status"] == "ok",
        "no_outcome_evidence_added": True,
    }
    return {
        "export_dir": rel(export_dir),
        "participant_exports": participant_exports,
        "coordinator": {
            "html": coordinator_payload["path"],
            "fields_match_template": coordinator_payload["fields"] == template_fields,
            "output_name": coordinator_payload["output_name"],
            "merged_export": merged_info,
            "participant_counts": participant_counts,
        },
        "labeler_exports": labeler_exports,
        "browser": {"path": browser, "checks": browser_checks},
        "leak_scan": leak,
        "checks": checks,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    checks = payload["checks"]
    lines = [
        "# R259 Paper-Scale Static Collection Kit",
        "",
        f"Status: `{payload['status']}`",
        "",
        "R259 generates static paper-scale collection forms and validates synthetic export shape only.",
        "",
        "## Outputs",
        "",
        f"- Index: `{payload['artifacts']['index']}`",
        f"- Synthetic export dir: `{payload['smoke']['export_dir']}`",
        f"- Merged C5 smoke CSV: `{payload['smoke']['coordinator']['merged_export']['path']}`",
        f"- Browser path: `{payload['smoke']['browser']['path']}`",
        "",
        "## Checks",
        "",
    ]
    for key, value in checks.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Claim Gate",
            "",
            f"- weak_accept_supported: `{payload['claim_gate']['weak_accept_supported']}`",
            f"- c5_supported: `{payload['claim_gate']['c5_supported']}`",
            f"- c6_supported: `{payload['claim_gate']['c6_supported']}`",
            f"- outcome_evidence_added: `{payload['claim_gate']['outcome_evidence_added']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--browser", default=None)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_kit(args.out_dir)
    smoke = run_smoke(args.out_dir, manifest, args.browser)
    all_checks = dict(smoke["checks"])
    all_checks.update(
        {
            "r249_ready_no_responses": read_json(R249_MANIFEST).get("status") == "paper_scale_launch_ready_no_responses",
            "r252_ready_no_labels": read_json(R252_MANIFEST).get("status") == "paper_scale_label_collection_ready_no_labels",
            "r258_bundle_ready_no_outcomes": read_json(R258_JSON).get("status")
            == "paper_scale_human_evidence_bundle_ready_no_outcomes",
        }
    )
    manifest["smoke"] = smoke
    manifest["checks"] = all_checks
    manifest["status"] = "paper_scale_static_collection_kit_passed" if all(all_checks.values()) else "paper_scale_static_collection_kit_failed"
    out_json = args.out_dir / "static-collection-kit-r259.json"
    out_md = args.out_dir / "static-collection-kit-r259.md"
    manifest["artifacts"]["manifest"] = rel(out_json)
    manifest["artifacts"]["summary_md"] = rel(out_md)
    write_json(out_json, manifest)
    write_text(out_md, render_markdown(manifest))
    if manifest["status"] != "paper_scale_static_collection_kit_passed":
        failed = [name for name, ok in all_checks.items() if not ok]
        print(f"R259 static kit failed: {failed}")
        return 1
    print(f"R259 static kit passed: {len(manifest['forms']['participant_forms'])} participant forms, {len(manifest['forms']['labeler_forms'])} labeler forms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
