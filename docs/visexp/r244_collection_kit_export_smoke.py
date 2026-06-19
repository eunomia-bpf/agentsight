#!/usr/bin/env python3
"""R244: smoke-test the R243 static collection kit export contract.

This script does not create human evidence. It verifies that the generated
static forms are loadable as local HTML and that their embedded ROWS/FIELDS data
can produce CSV files matching the R195 return contract.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
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
KIT_DIR = OUT_DIR / "human-evidence-collection-kit-r243"
DEFAULT_OUT_DIR = OUT_DIR / "human-evidence-collection-kit-export-smoke-r244"

R142_TEMPLATE = OUT_DIR / "user-task-pilot-r142" / "launch" / "responses" / "user-task-response-template-r142-pilot.csv"
R243_MANIFEST = KIT_DIR / "collection-kit-r243.json"

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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    payload: dict[str, Any] = {
        "path": rel(path),
        "rows": decode_const(text, "ROWS") if "const ROWS =" in text else None,
        "fields": decode_const(text, "FIELDS"),
        "output_name": decode_const(text, "OUTPUT_NAME"),
        "mutators": decode_const(text, "MUTATORS") if "const MUTATORS =" in text else None,
        "sha256": sha256_file(path),
    }
    return payload


def export_rows(rows: list[dict[str, str]], mutators: list[dict[str, str]] | None) -> list[dict[str, str]]:
    exported: list[dict[str, str]] = []
    for index, row in enumerate(rows):
        next_row = dict(row)
        for mutator in mutators or []:
            field = mutator["field"]
            if field == "response_json":
                next_row[field] = json.dumps(
                    {
                        "r244_export_smoke": True,
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
                next_row[field] = "r244_synthetic_export_smoke_not_human_evidence"
            else:
                # Keep label fields empty so exported smoke files cannot be
                # mistaken for completed human labels.
                next_row[field] = ""
        exported.append(next_row)
    return exported


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


def run_smoke(out_dir: Path, browser_path: str | None) -> dict[str, Any]:
    manifest = read_json(R243_MANIFEST)
    export_dir = out_dir / "synthetic-exports"
    participant_exports: list[dict[str, Any]] = []
    labeler_exports: list[dict[str, Any]] = []

    template_rows, template_fields = read_csv(R142_TEMPLATE)
    expected_by_participant: dict[str, int] = {}
    for row in template_rows:
        expected_by_participant[row["participant_id"]] = expected_by_participant.get(row["participant_id"], 0) + 1

    for form in manifest["forms"]["participant_forms"]:
        html_path = REPO_ROOT / form["html_path"]
        payload = form_payload(html_path)
        if payload["fields"] != template_fields:
            raise ValueError(f"participant field mismatch for {form['participant_id']}")
        rows = payload["rows"] or []
        exported = export_rows(rows, payload["mutators"])
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
    merged_csv = export_dir / "r142-pilot-responses.csv"
    write_csv(merged_csv, merged_rows, template_fields)
    merged_info = csv_info(merged_csv)

    participant_counts: dict[str, int] = {}
    for row in merged_rows:
        participant_counts[row["participant_id"]] = participant_counts.get(row["participant_id"], 0) + 1

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

    coordinator_payload = {
        "path": rel(KIT_DIR / "coordinator" / "r142-merge.html"),
        "fields": decode_const((KIT_DIR / "coordinator" / "r142-merge.html").read_text(encoding="utf-8"), "FIELDS"),
        "output_name": decode_const((KIT_DIR / "coordinator" / "r142-merge.html").read_text(encoding="utf-8"), "OUTPUT_NAME"),
    }

    browser = find_browser(browser_path)
    browser_pages = [
        (KIT_DIR / "index.html", "R243 static collection kit"),
        (KIT_DIR / "coordinator" / "r142-merge.html", "R142 participant response merge"),
        (KIT_DIR / "participants" / "P01.html", "R142 participant form P01"),
        (KIT_DIR / "labelers" / "r124-labeler-1.html", "R124 tag adequacy labeler 1"),
        (KIT_DIR / "labelers" / "r190-labeler-1.html", "R190 merge-risk labeler 1"),
        (KIT_DIR / "labelers" / "r203-labeler-1.html", "R203 long-tail promotion labeler 1"),
    ]
    browser_checks = [browser_dump(browser, page, expected) for page, expected in browser_pages]

    generated_paths = sorted(path for path in export_dir.rglob("*") if path.is_file())
    generated_paths.extend(
        [
            KIT_DIR / "index.html",
            KIT_DIR / "coordinator" / "r142-merge.html",
            *[REPO_ROOT / form["html_path"] for form in manifest["forms"]["participant_forms"]],
            *[REPO_ROOT / form["html_path"] for form in manifest["forms"]["labeler_forms"]],
        ]
    )
    leak = leak_scan(generated_paths)

    checks = {
        "participant_export_count": len(participant_exports),
        "participant_rows_ok": all(item["output"]["row_count"] == item["expected_rows"] for item in participant_exports),
        "participant_fields_ok": all(item["fields_match_template"] for item in participant_exports),
        "participant_json_ok": all(item["json_cells_valid"] for item in participant_exports),
        "merged_output_name_ok": coordinator_payload["output_name"] == "r142-pilot-responses.csv",
        "merged_fields_ok": coordinator_payload["fields"] == template_fields and merged_info["fields"] == template_fields,
        "merged_rows_ok": merged_info["row_count"] == len(template_rows),
        "merged_participants_ok": participant_counts == expected_by_participant,
        "labeler_export_count": len(labeler_exports),
        "labeler_fields_ok": all(item["fields_match_source"] for item in labeler_exports),
        "labeler_rows_ok": all(item["output"]["row_count"] == item["source_rows"] for item in labeler_exports),
        "labeler_cells_blank": all(item["label_cells_filled"] == 0 for item in labeler_exports),
        "browser_checks_ok": all(item["status"] == "ok" for item in browser_checks),
        "leak_scan_ok": leak["status"] == "ok",
    }

    status = "collection_kit_export_smoke_passed" if all(checks.values()) else "collection_kit_export_smoke_failed"
    return {
        "schema_version": 1,
        "run_id": "R244",
        "status": status,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "claim_boundary": (
            "R244 tests only the R243 static form/export contract. It generates "
            "synthetic CSV exports under an R244 directory, does not place files "
            "in the R195 inbox, and cannot support C5/C6 outcome claims."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(SCRIPT_DIR / "r244_collection_kit_export_smoke.py"),
            "r243_manifest_sha256": sha256_file(R243_MANIFEST),
        },
        "source_artifacts": {
            "r243_manifest": rel(R243_MANIFEST),
            "r142_response_template": rel(R142_TEMPLATE),
        },
        "browser": {
            "path": browser,
            "checks": browser_checks,
        },
        "coordinator": {
            "html": coordinator_payload["path"],
            "fields_match_template": coordinator_payload["fields"] == template_fields,
            "output_name": coordinator_payload["output_name"],
            "merged_export": merged_info,
            "participant_counts": participant_counts,
        },
        "participant_exports": participant_exports,
        "labeler_exports": labeler_exports,
        "checks": checks,
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
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    checks = payload["checks"]
    lines = [
        "# R244 Collection Kit Export Smoke",
        "",
        f"Status: `{payload['status']}`",
        "",
        "R244 validates static form loading and CSV export shape only. It is not human evidence.",
        "",
        "## Checks",
        "",
    ]
    for key, value in checks.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Merged R142 smoke CSV: `{payload['coordinator']['merged_export']['path']}`",
            f"- Browser path: `{payload['browser']['path']}`",
            "",
            "All synthetic exports stay under the R244 output directory and are not placed in the R195 inbox.",
        ]
    )
    write_text(path, "\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--browser", default=None)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    payload = run_smoke(args.out_dir, args.browser)
    out_json = args.out_dir / "collection-kit-export-smoke-r244.json"
    out_md = args.out_dir / "collection-kit-export-smoke-r244.md"
    write_json(out_json, payload)
    write_markdown(out_md, payload)
    print(f"wrote {rel(out_json)}")
    return 0 if payload["status"] == "collection_kit_export_smoke_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
