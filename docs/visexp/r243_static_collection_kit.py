#!/usr/bin/env python3
"""R243: generate a static human-evidence collection kit.

The kit is a logistics artifact. It wraps existing blinded R142/R124/R190/R203
materials in static HTML forms that export CSV files matching the R195 inbox
contract. It does not create participant responses or human labels.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_DIR = SCRIPT_DIR / "out"
DEFAULT_OUT_DIR = OUT_DIR / "human-evidence-collection-kit-r243"

R142_LAUNCH = OUT_DIR / "user-task-pilot-r142" / "launch"
R142_RESPONSE_TEMPLATE = R142_LAUNCH / "responses" / "user-task-response-template-r142-pilot.csv"
R142_PARTICIPANTS = R142_LAUNCH / "participants"
R142_MANIFEST = R142_LAUNCH / "manifest.json"
R193_MANIFEST = OUT_DIR / "human-evidence-r193" / "manifest.json"
R207_MANIFEST = OUT_DIR / "human-evidence-launch-r207" / "human-evidence-launch-r207.json"
R195_DEFAULT = OUT_DIR / "human-evidence-pipeline-r195.json"

LABEL_SHEETS = [
    {
        "key": "r124_labeler_1",
        "group": "r124",
        "title": "R124 tag adequacy labeler 1",
        "source": OUT_DIR / "human-evidence-r193" / "r124" / "r124-tag-adequacy-labeler-1.csv",
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
        "source": OUT_DIR / "human-evidence-r193" / "r124" / "r124-tag-adequacy-labeler-2.csv",
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
        "source": OUT_DIR / "human-evidence-r193" / "r190" / "r190-merge-risk-labeler-1.csv",
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
        "source": OUT_DIR / "human-evidence-r193" / "r190" / "r190-merge-risk-labeler-2.csv",
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
        "source": OUT_DIR / "human-evidence-r193" / "r203" / "r203-long-tail-promotion-labeler-1.csv",
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
        "source": OUT_DIR / "human-evidence-r193" / "r203" / "r203-long-tail-promotion-labeler-2.csv",
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


def sha256_file(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def csv_row_count(path: Path) -> int:
    rows, _ = read_csv(path)
    return len(rows)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def path_info(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
    }
    if path.suffix.lower() == ".csv" and path.exists():
        info["row_count"] = csv_row_count(path)
    return info


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
h3 {{ margin: 18px 0 6px; font-size: 15px; }}
p {{ margin: 6px 0; }}
a {{ color: var(--accent); }}
.muted {{ color: var(--muted); }}
.warn {{ color: var(--warn); font-weight: 650; }}
.toolbar {{
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 10px;
}}
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
td.readonly {{ max-width: 310px; overflow-wrap: anywhere; }}
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
  if (status) {{
    status.textContent = `missing required cells: ${{missing}}; invalid JSON cells: ${{badJson}}`;
  }}
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
  for (const row of rows) {{
    lines.push(FIELDS.map((field) => csvEscape(row[field] ?? "")).join(","));
  }}
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
<h1>R142 participant form {html.escape(participant_id)}</h1>
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
<tbody>
{''.join(row_html)}
</tbody>
</table>
</main>
{export_script(rows, fields, f"r142-pilot-responses-{participant_id}.csv", mutators)}
"""
    return page_shell(f"R142 {participant_id}", body)


def labeler_page(config: dict[str, Any], rows: list[dict[str, str]], fields: list[str]) -> str:
    label_field = config["label_field"]
    notes_field = config["notes_field"]
    mutators = [
        {"field": label_field, "required": "true", "kind": "text"},
        {"field": notes_field, "required": "", "kind": "text"},
    ]
    visible_fields = [field for field in config["visible_fields"] if field in fields]
    row_html = []
    label_options = "".join(
        f"<option value=\"{html.escape(label)}\">{html.escape(label)}</option>"
        for label in config["labels"]
    )
    for index, row in enumerate(rows):
        cells = []
        for field in visible_fields:
            cells.append(f"<td class=\"readonly\">{html.escape(row.get(field, ''))}</td>")
        cells.append(
            f"<td><select id=\"{html.escape(label_field)}-{index}\"><option value=\"\"></option>{label_options}</select></td>"
        )
        cells.append(f"<td><textarea id=\"{html.escape(notes_field)}-{index}\"></textarea></td>")
        row_html.append("<tr>" + "".join(cells) + "</tr>")
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
<tbody>
{''.join(row_html)}
</tbody>
</table>
</main>
{export_script(rows, fields, config["output_name"], mutators)}
"""
    return page_shell(config["title"], body)


def r142_merge_page(fields: list[str]) -> str:
    body = f"""<header>
<h1>R142 participant response merge</h1>
<p class="muted">Select returned participant CSV files, then export one R195-ready file.</p>
<div class="toolbar">
<input id="files" type="file" multiple accept=".csv,text/csv">
<button onclick="mergeFiles()">Read selected CSVs</button>
<button class="secondary" onclick="exportMerged()">Export r142-pilot-responses.csv</button>
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
const OUTPUT_NAME = "r142-pilot-responses.csv";
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
        if (text[i + 1] === '"') {{
          cell += '"';
          i += 1;
        }} else {{
          quoted = false;
        }}
      }} else {{
        cell += ch;
      }}
    }} else if (ch === '"') {{
      quoted = true;
    }} else if (ch === ",") {{
      row.push(cell);
      cell = "";
    }} else if (ch === "\\n") {{
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
    }} else if (ch !== "\\r") {{
      cell += ch;
    }}
  }}
  if (cell !== "" || row.length) {{
    row.push(cell);
    rows.push(row);
  }}
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
  for (const row of MERGED_ROWS) {{
    lines.push(FIELDS.map((field) => csvEscape(row[field] ?? "")).join(","));
  }}
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
    return page_shell("R142 participant merge", body)


def index_page(
    participant_forms: list[dict[str, Any]],
    label_forms: list[dict[str, Any]],
    coordinator_forms: list[dict[str, Any]],
) -> str:
    participant_cards = []
    for form in participant_forms:
        participant_cards.append(
            f"""<div class="card">
<h3>{html.escape(form['participant_id'])}</h3>
<p>{form['row_count']} task rows.</p>
<p><a href="{html.escape(form['relative_link'])}">Open participant form</a></p>
</div>"""
        )
    label_cards = []
    for form in label_forms:
        label_cards.append(
            f"""<div class="card">
<h3>{html.escape(form['title'])}</h3>
<p>{form['row_count']} label rows. Output: <code>{html.escape(form['output_name'])}</code></p>
<p><a href="{html.escape(form['relative_link'])}">Open label form</a></p>
</div>"""
        )
    coordinator_cards = []
    for form in coordinator_forms:
        coordinator_cards.append(
            f"""<div class="card">
<h3>{html.escape(form['title'])}</h3>
<p>{html.escape(form['purpose'])}</p>
<p><a href="{html.escape(form['relative_link'])}">Open coordinator form</a></p>
</div>"""
        )
    body = f"""<header>
<h1>R243 static collection kit</h1>
<p class="muted">Open these files directly in a browser. No server or model is required.</p>
</header>
<main>
<p class="warn">R243 is collection tooling only. It does not contain completed human responses or labels.</p>
<h2>Participant forms</h2>
<div class="grid">
{''.join(participant_cards)}
</div>
<h2>Labeler forms</h2>
<div class="grid">
{''.join(label_cards)}
</div>
<h2>Coordinator forms</h2>
<div class="grid">
{''.join(coordinator_cards)}
</div>
<h2>R195 return names</h2>
<p>Place completed exports in <code>docs/visexp/out/human-evidence-r195/inbox/</code>. Labeler exports already use the R195 filenames. Use the coordinator merge page to combine participant exports into <code>r142-pilot-responses.csv</code>.</p>
</main>
"""
    return page_shell("R243 static collection kit", body)


def collect_participant_forms(out_dir: Path) -> list[dict[str, Any]]:
    rows, fields = read_csv(R142_RESPONSE_TEMPLATE)
    by_participant: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_participant.setdefault(row["participant_id"], []).append(row)

    forms: list[dict[str, Any]] = []
    for participant_id in sorted(by_participant):
        packet_md_path = R142_PARTICIPANTS / f"{participant_id}.md"
        packet_md = packet_md_path.read_text(encoding="utf-8")
        html_path = out_dir / "participants" / f"{participant_id}.html"
        write_text(html_path, participant_page(participant_id, packet_md, by_participant[participant_id], fields))
        forms.append(
            {
                "participant_id": participant_id,
                "html_path": rel(html_path),
                "relative_link": f"participants/{participant_id}.html",
                "source_packet": rel(packet_md_path),
                "source_packet_sha256": sha256_file(packet_md_path),
                "row_count": len(by_participant[participant_id]),
                "output_name": f"r142-pilot-responses-{participant_id}.csv",
            }
        )
    return forms


def collect_coordinator_forms(out_dir: Path) -> list[dict[str, Any]]:
    _, fields = read_csv(R142_RESPONSE_TEMPLATE)
    html_path = out_dir / "coordinator" / "r142-merge.html"
    write_text(html_path, r142_merge_page(fields))
    return [
        {
            "key": "r142_response_merge",
            "title": "R142 response merge",
            "purpose": "Combine P01-P05 exports into r142-pilot-responses.csv for the R195 inbox.",
            "html_path": rel(html_path),
            "relative_link": "coordinator/r142-merge.html",
            "output_name": "r142-pilot-responses.csv",
        }
    ]


def collect_label_forms(out_dir: Path) -> list[dict[str, Any]]:
    forms: list[dict[str, Any]] = []
    for config in LABEL_SHEETS:
        rows, fields = read_csv(config["source"])
        html_path = out_dir / "labelers" / f"{config['key'].replace('_', '-')}.html"
        write_text(html_path, labeler_page(config, rows, fields))
        forms.append(
            {
                "key": config["key"],
                "group": config["group"],
                "title": config["title"],
                "html_path": rel(html_path),
                "relative_link": f"labelers/{config['key'].replace('_', '-')}.html",
                "source": rel(config["source"]),
                "source_sha256": sha256_file(config["source"]),
                "row_count": len(rows),
                "output_name": config["output_name"],
                "label_field": config["label_field"],
                "notes_field": config["notes_field"],
                "label_values": config["labels"],
            }
        )
    return forms


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


def generated_file_info(out_dir: Path) -> list[dict[str, Any]]:
    files = sorted(
        path
        for path in out_dir.rglob("*")
        if path.is_file() and path.name != "collection-kit-r243.json"
    )
    return [{"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size} for path in files]


def write_readme(
    out_dir: Path,
    participant_forms: list[dict[str, Any]],
    label_forms: list[dict[str, Any]],
    coordinator_forms: list[dict[str, Any]],
) -> Path:
    lines = [
        "# R243 Static Human-Evidence Collection Kit",
        "",
        "Status: `collection_kit_ready_no_outcomes`",
        "",
        "Open `index.html` directly in a browser. The pages are static HTML files and need no server.",
        "",
        "## Scope",
        "",
        "- Wraps existing blinded R142/R124/R190/R203 materials in local forms.",
        "- Exports CSV files that match the R195 inbox naming contract.",
        "- Does not create participant responses, human labels, or claim support.",
        "",
        "## Participant Collection",
        "",
        "Send each participant only their matching form:",
        "",
    ]
    for form in participant_forms:
        lines.append(f"- `{form['participant_id']}`: `{form['relative_link']}` exports `{form['output_name']}`")
    lines.extend(
        [
            "",
            "After all five participant exports return, open the coordinator merge page and export one `r142-pilot-responses.csv`:",
            "",
        ]
    )
    for form in coordinator_forms:
        lines.append(f"- `{form['relative_link']}` exports `{form['output_name']}`")
    lines.extend(
        [
            "",
            "Place the merged file in `docs/visexp/out/human-evidence-r195/inbox/`.",
            "",
            "## Label Collection",
            "",
            "Send paired labeler sheets independently:",
            "",
        ]
    )
    for form in label_forms:
        lines.append(f"- `{form['relative_link']}` exports `{form['output_name']}`")
    lines.extend(
        [
            "",
            "Place completed labeler exports in `docs/visexp/out/human-evidence-r195/inbox/` using the exported filenames.",
            "",
            "## Scoring",
            "",
            "After returns are frozen, run:",
            "",
            "```bash",
            "python3 docs/visexp/r195_human_evidence_pipeline.py",
            "```",
            "",
            "R243 itself is not outcome evidence. C5/C6 remain unsupported until real completed files score through R195.",
        ]
    )
    readme = out_dir / "README.md"
    write_text(readme, "\n".join(lines) + "\n")
    return readme


def build_manifest(
    out_dir: Path,
    participant_forms: list[dict[str, Any]],
    label_forms: list[dict[str, Any]],
    coordinator_forms: list[dict[str, Any]],
) -> dict[str, Any]:
    generated_paths = sorted(path for path in out_dir.rglob("*") if path.is_file())
    leak = leak_scan([path for path in generated_paths if path.name != "collection-kit-r243.json"])
    rows_by_group = {
        "r142_response_rows": csv_row_count(R142_RESPONSE_TEMPLATE),
        "r124_labeler_rows_each": csv_row_count(LABEL_SHEETS[0]["source"]),
        "r190_labeler_rows_each": csv_row_count(LABEL_SHEETS[2]["source"]),
        "r203_labeler_rows_each": csv_row_count(LABEL_SHEETS[4]["source"]),
    }
    return {
        "schema_version": 1,
        "run_id": "R243",
        "status": "collection_kit_ready_no_outcomes" if leak["status"] == "ok" else "failed_leak_scan",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "claim_boundary": (
            "R243 is a static collection UX and return-format artifact. It does not "
            "collect, infer, score, or synthesize human responses or labels, and it "
            "does not upgrade C5, C6, canonicalization, promotion, or weak-accept gates."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(SCRIPT_DIR / "r243_static_collection_kit.py"),
        },
        "source_artifacts": {
            "r142_manifest": path_info(R142_MANIFEST),
            "r142_response_template": path_info(R142_RESPONSE_TEMPLATE),
            "r193_manifest": path_info(R193_MANIFEST),
            "r207_launch_readiness": path_info(R207_MANIFEST),
            "r195_default_pipeline": path_info(R195_DEFAULT),
            "label_sheets": {config["key"]: path_info(config["source"]) for config in LABEL_SHEETS},
        },
        "row_counts": rows_by_group,
        "forms": {
            "participant_forms": participant_forms,
            "labeler_forms": label_forms,
            "coordinator_forms": coordinator_forms,
        },
        "r195_return_plan": {
            "inbox": "docs/visexp/out/human-evidence-r195/inbox",
            "participant_merge_required": True,
            "participant_merged_name": "r142-pilot-responses.csv",
            "labeler_output_names": [form["output_name"] for form in label_forms],
        },
        "leak_scan": leak,
        "claim_gate": {
            "c5_supported": False,
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "long_tail_promotion_review_supported": False,
            "canonical_map_updated": False,
            "weak_accept_supported": False,
            "requires_real_human_returns": True,
        },
        "generated_files": generated_file_info(out_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    participant_forms = collect_participant_forms(out_dir)
    coordinator_forms = collect_coordinator_forms(out_dir)
    label_forms = collect_label_forms(out_dir)
    write_text(out_dir / "index.html", index_page(participant_forms, label_forms, coordinator_forms))
    write_readme(out_dir, participant_forms, label_forms, coordinator_forms)

    manifest_path = out_dir / "collection-kit-r243.json"
    manifest = build_manifest(out_dir, participant_forms, label_forms, coordinator_forms)
    write_json(manifest_path, manifest)

    if manifest["status"] != "collection_kit_ready_no_outcomes":
        print(json.dumps(manifest["leak_scan"], indent=2, sort_keys=True))
        return 1
    print(f"wrote {rel(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
