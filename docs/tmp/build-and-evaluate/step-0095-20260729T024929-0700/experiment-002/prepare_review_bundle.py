#!/usr/bin/env python3
"""Build the blinded 40-case analyst-output validity-review bundle.

This command is intentionally unusable until every frozen analyst run has a
terminal ``run.json``. Successful runs must have ``final.json``; failed or
timed-out runs without one receive an opaque unavailable-output marker. The
bundle never exposes the private case-to-run map, arm, schedule, timing, usage,
rank, block, endpoint command, or source-package path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any


EXPERIMENT = Path(__file__).resolve().parent
ANALYST_DIR = EXPERIMENT / "analyst"
DEFAULT_OUTPUT = ANALYST_DIR / "review-bundle"
PACKAGES = {
    "PROFILE": EXPERIMENT / "analyst-packages" / "PROFILE",
    "RAW-OPERATIONS": EXPERIMENT / "analyst-packages" / "RAW-OPERATIONS",
}
TERMINAL_STATUSES = {"ok", "failed", "timeout"}
FORBIDDEN_PUBLIC_KEYS = {
    "run_id",
    "arm",
    "timing",
    "usage",
    "position",
    "schedule_position",
    "within_block_order",
    "arm_rank",
    "block_id",
    "block_index",
    "package",
    "prompt_file",
    "endpoint",
    "command",
}
FORBIDDEN_OUTPUT_KEYS = (
    FORBIDDEN_PUBLIC_KEYS
    | {
        "status",
        "exit_code",
        "wall_seconds",
        "provider_usage_totals",
        "provider_usage_events",
        "final_response_elapsed_seconds",
        "model_turns",
        "tool_call_counts",
        "actual_tool_commands",
    }
) - {"command"}
POLICY_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")
UNAVAILABLE_OUTPUT = {
    "schema": "agentsight.utility2.blind-output-unavailable.v1",
    "output_available": False,
    "terminal_without_final": True,
}

INSTRUCTIONS = [
    (
        "Review all 40 opaque cases before returning decisions; do not infer or "
        "seek the private case mapping."
    ),
    (
        "For each case, inspect output.json and rerun every cited evidence "
        "command with that case's evidence directory as the current directory."
    ),
    (
        "Use execution.json only to audit whether the analyst read outside its "
        "assigned evidence directory or used a disallowed nonlocal tool."
    ),
    (
        "Return one decision per case_id using review-output.schema.json; each "
        "of the five registered fields is a boolean."
    ),
]


class BundleError(RuntimeError):
    """Raised when the blind bundle cannot be built without leakage."""


def _assert_no_forbidden_output_keys(value: Any) -> None:
    if isinstance(value, dict):
        overlap = set(value) & FORBIDDEN_OUTPUT_KEYS
        if overlap:
            raise BundleError(
                f"review output exposes forbidden keys: {sorted(overlap)}"
            )
        for nested in value.values():
            _assert_no_forbidden_output_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_forbidden_output_keys(nested)


def validate_output_document(document: Any) -> str:
    """Validate one public output as strict analyst output or exact marker."""

    if document == UNAVAILABLE_OUTPUT:
        return "unavailable"
    if not isinstance(document, dict):
        raise BundleError("analyst output must be a JSON object")
    _assert_no_forbidden_output_keys(document)
    if set(document) != {
        "diagnosis",
        "quantitative_evidence",
        "policy_text",
        "expected_mechanism",
    }:
        raise BundleError("analyst output has nonregistered top-level fields")
    for field in ("diagnosis", "policy_text", "expected_mechanism"):
        if not isinstance(document[field], str) or not document[field]:
            raise BundleError(f"analyst output {field} must be a nonempty string")
    policy_words = POLICY_WORD_RE.findall(document["policy_text"])
    if not 1 <= len(policy_words) <= 60:
        raise BundleError("analyst output policy_text must contain 1..60 English words")
    evidence = document["quantitative_evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise BundleError(
            "analyst output quantitative_evidence must be a nonempty array"
        )
    for index, item in enumerate(evidence):
        if not isinstance(item, dict) or set(item) != {"command", "finding"}:
            raise BundleError(
                f"analyst output evidence {index} has nonregistered fields"
            )
        for field in ("command", "finding"):
            if not isinstance(item[field], str) or not item[field]:
                raise BundleError(
                    f"analyst output evidence {index}.{field} "
                    "must be a nonempty string"
                )
    return "analyst-output"


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_inputs(
    analyst_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    order_path = analyst_dir / "order.json"
    alias_path = analyst_dir / "review-alias-map.private.json"
    if not order_path.is_file() or not alias_path.is_file():
        raise BundleError("frozen order or private review alias map is missing")
    order = json.loads(order_path.read_text(encoding="utf-8"))
    aliases = json.loads(alias_path.read_text(encoding="utf-8"))
    rows = order.get("runs")
    cases = aliases.get("cases")
    if not isinstance(rows, list) or len(rows) != 40:
        raise BundleError("frozen schedule does not contain exactly 40 runs")
    if not isinstance(cases, list) or len(cases) != 40:
        raise BundleError("private alias map does not contain exactly 40 cases")
    run_ids = [row.get("run_id") for row in rows]
    case_ids = [case.get("case_id") for case in cases]
    mapped_ids = [case.get("run_id") for case in cases]
    if (
        any(not isinstance(value, str) for value in run_ids + case_ids + mapped_ids)
        or len(set(run_ids)) != 40
        or len(set(case_ids)) != 40
        or len(set(mapped_ids)) != 40
        or set(mapped_ids) != set(run_ids)
    ):
        raise BundleError("private aliases are not a complete run-id bijection")
    return rows, cases


def _validate_terminal_runs(
    analyst_dir: Path,
    rows: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, bool]]:
    records: dict[str, dict[str, Any]] = {}
    final_available: dict[str, bool] = {}
    for row in rows:
        run_id = row["run_id"]
        run_dir = analyst_dir / "runs" / run_id
        record_path = run_dir / "run.json"
        final_path = run_dir / "final.json"
        if not record_path.is_file():
            raise BundleError(f"scheduled run is not terminal: {run_id}")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        embedded = record.get("run")
        if (
            record.get("status") not in TERMINAL_STATUSES
            or not isinstance(embedded, dict)
            or embedded.get("run_id") != run_id
            or embedded.get("arm") != row.get("arm")
        ):
            raise BundleError(f"scheduled run record is nonterminal or mismatched: {run_id}")
        status = record["status"]
        has_final = False
        if status == "ok":
            if final_path.is_symlink() or not final_path.is_file():
                raise BundleError(
                    f"successful scheduled run lacks regular final.json: {run_id}"
                )
            try:
                final = json.loads(final_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise BundleError(
                    f"scheduled final.json is invalid JSON: {run_id}"
                ) from exc
            if not isinstance(final, dict):
                raise BundleError(
                    f"scheduled final.json is not a JSON object: {run_id}"
                )
            validate_output_document(final)
            has_final = True
        tools = record.get("actual_tool_commands")
        if not isinstance(tools, list):
            raise BundleError(f"scheduled run lacks actual tool-command audit: {run_id}")
        for tool in tools:
            if (
                not isinstance(tool, dict)
                or not isinstance(tool.get("type"), str)
                or tool.get("command") is not None
                and not isinstance(tool.get("command"), str)
            ):
                raise BundleError(f"malformed actual tool-command audit: {run_id}")
        records[run_id] = record
        final_available[run_id] = has_final
    return records, final_available


def _package_files(package: Path) -> list[Path]:
    if not package.is_dir() or package.is_symlink():
        raise BundleError(f"invalid evidence package: {package}")
    files = sorted(path for path in package.iterdir() if path.is_file())
    if len(files) != len(list(package.iterdir())) or not files:
        raise BundleError(f"evidence package contains links or directories: {package}")
    if any(path.is_symlink() for path in files):
        raise BundleError(f"evidence package contains a symlink: {package}")
    return files


def _copy_exact(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    source_hash = sha256_file(source)
    if sha256_file(destination) != source_hash:
        raise BundleError(f"copied file hash mismatch: {destination}")
    return source_hash


def _public_execution(
    record: dict[str, Any],
    assigned_package: Path,
    all_packages: list[Path],
    all_run_ids: set[str],
    all_block_ids: set[str],
    all_case_ids: set[str],
    current_case_id: str,
) -> dict[str, Any]:
    tools = []
    for tool in record["actual_tool_commands"]:
        public: dict[str, Any] = {"type": tool["type"]}
        if tool.get("command") is not None:
            literal = _redact_text(
                tool["command"],
                assigned_package=assigned_package,
                all_packages=all_packages,
                all_run_ids=all_run_ids,
                all_block_ids=all_block_ids,
                all_case_ids=all_case_ids,
                current_case_id=current_case_id,
            )
            public["literal"] = literal
        tools.append(public)
    return {
        "schema": "agentsight.utility2.blind-execution-audit.v1",
        "tool_calls": tools,
    }


def _redact_text(
    text: str,
    *,
    assigned_package: Path,
    all_packages: list[Path],
    all_run_ids: set[str],
    all_block_ids: set[str],
    all_case_ids: set[str],
    current_case_id: str,
) -> str:
    package_literals = {
        str(assigned_package),
        str(assigned_package.resolve()),
    }
    for package_literal in sorted(package_literals, key=len, reverse=True):
        text = text.replace(package_literal, "$EVIDENCE")
    for other_package in all_packages:
        if other_package.resolve() == assigned_package.resolve():
            continue
        for package_literal in sorted(
            {str(other_package), str(other_package.resolve())},
            key=len,
            reverse=True,
        ):
            text = text.replace(
                package_literal, "$OUTSIDE_EVIDENCE_PACKAGE"
            )
    for run_id in sorted(all_run_ids, key=len, reverse=True):
        text = text.replace(run_id, "$RUN_ID")
    for block_id in sorted(all_block_ids, key=len, reverse=True):
        text = text.replace(block_id, "$BLOCK_ID")
    for case_id in sorted(all_case_ids, key=len, reverse=True):
        marker = "$CASE_ID" if case_id == current_case_id else "$OTHER_CASE_ID"
        text = text.replace(case_id, marker)
    for private_root in sorted(
        {
            str(EXPERIMENT),
            str(EXPERIMENT.resolve()),
            str(ANALYST_DIR),
            str(ANALYST_DIR.resolve()),
        },
        key=len,
        reverse=True,
    ):
        text = re.sub(
            re.escape(private_root) + r"""[^\s"']*""",
            "$OUTSIDE_SCHEDULE_METADATA",
            text,
        )
    text = re.sub(
        r"""(?:\.\./|~/)[^\s"']*""",
        "$OUTSIDE_SCHEDULE_METADATA",
        text,
    )
    text = re.sub(
        r"""\$(?:\{)?(?:HOME|OLDPWD|CODEX_HOME)(?:\})?[^\s"']*|"""
        r"""\$(?:\{)?PWD(?:\})?/(?:\.\./)+[^\s"']*""",
        "$OUTSIDE_SCHEDULE_METADATA",
        text,
    )
    text = re.sub(
        r"""(?:(?:[A-Za-z0-9._-]+/)*)(?:"""
        r"""order\.json|review-alias-map\.private\.json|commands\.json|"""
        r"""model-contract\.json|batch-command\.json|analysis-command\.json|"""
        r"""policy-freeze-command\.json|frozen-contract-analyst\.json|"""
        r"""contract-verification-analyst\.json|review-command\.json|"""
        r"""review-prompt\.txt|review-model-contract\.json"""
        r""")""",
        "$OUTSIDE_SCHEDULE_METADATA",
        text,
    )
    text = re.sub(
        r"""(?<![\w$])/(?:home|root|tmp|etc|proc|sys|var|mnt|workspace)/"""
        r"""[^\s"']*""",
        "$OUTSIDE_PATH",
        text,
    )
    text = re.sub(r"""https?://[^\s"']+""", "$ENDPOINT", text)
    text = re.sub(
        r"\b(?:localhost|127\.0\.0\.1)(?::\d{1,5})?\b",
        "$ENDPOINT",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _redact_json_strings(value: Any, **redaction: Any) -> Any:
    if isinstance(value, str):
        return _redact_text(value, **redaction)
    if isinstance(value, list):
        return [
            _redact_json_strings(item, **redaction) for item in value
        ]
    if isinstance(value, dict):
        return {
            key: _redact_json_strings(item, **redaction)
            for key, item in value.items()
        }
    return value


def _make_read_only(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            os.chmod(path, 0o444)
    for path in sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        os.chmod(path, 0o555)
    os.chmod(root, 0o555)


def _assert_public_json_keys(value: Any) -> None:
    if isinstance(value, dict):
        overlap = set(value) & FORBIDDEN_PUBLIC_KEYS
        if overlap:
            raise BundleError(f"public metadata exposes forbidden keys: {sorted(overlap)}")
        for nested in value.values():
            _assert_public_json_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_public_json_keys(nested)


def verify_bundle(bundle: Path, expected_case_ids: set[str]) -> dict[str, Any]:
    manifest_path = bundle / "manifest.json"
    if not manifest_path.is_file():
        raise BundleError("public manifest is missing")
    if bundle.stat().st_mode & 0o222 or manifest_path.stat().st_mode & 0o222:
        raise BundleError("public bundle root or manifest is writable")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _assert_public_json_keys(manifest)
    if set(path.name for path in bundle.iterdir()) != {
        "cases",
        "manifest.json",
        "review-output.schema.json",
    }:
        raise BundleError("public bundle root file set is not exact")
    if (bundle / "cases").stat().st_mode & 0o222:
        raise BundleError("public cases directory is writable")
    root_files = manifest.get("files")
    if not isinstance(root_files, dict) or set(root_files) != {
        "review-output.schema.json"
    }:
        raise BundleError("public manifest does not register the internal schema")
    if manifest.get("decision_schema_path") != "review-output.schema.json":
        raise BundleError("public decision schema path is not bundle-internal")
    for relative, expected_hash in root_files.items():
        path = bundle / relative
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise BundleError(f"public root file hash mismatch: {relative}")
        if path.stat().st_mode & 0o222:
            raise BundleError(f"public root file is writable: {relative}")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) != 40:
        raise BundleError("public manifest does not contain exactly 40 cases")
    case_ids = [case.get("case_id") for case in cases]
    if len(set(case_ids)) != 40 or set(case_ids) != expected_case_ids:
        raise BundleError("public manifest case IDs differ from private aliases")
    copied_file_count = 0
    for case in cases:
        if set(case) != {"case_id", "path", "files"}:
            raise BundleError("public case row has nonregistered metadata")
        case_id = case["case_id"]
        expected_relative = f"cases/{case_id}"
        if case["path"] != expected_relative:
            raise BundleError(f"public case path is not opaque: {case_id}")
        case_dir = bundle / expected_relative
        if not case_dir.is_dir():
            raise BundleError(f"public case directory is missing: {case_id}")
        actual_files = sorted(
            str(path.relative_to(case_dir))
            for path in case_dir.rglob("*")
            if path.is_file()
        )
        registered = case["files"]
        if not isinstance(registered, dict) or set(registered) != set(actual_files):
            raise BundleError(f"manifest file set mismatch: {case_id}")
        for relative, expected_hash in registered.items():
            path = case_dir / relative
            if sha256_file(path) != expected_hash:
                raise BundleError(f"manifest hash mismatch: {case_id}/{relative}")
            if path.stat().st_mode & 0o222:
                raise BundleError(f"review file is writable: {case_id}/{relative}")
            copied_file_count += 1
        if case_dir.stat().st_mode & 0o222:
            raise BundleError(f"review case directory is writable: {case_id}")
        for directory in (
            path for path in case_dir.rglob("*") if path.is_dir()
        ):
            if directory.stat().st_mode & 0o222:
                raise BundleError(
                    f"review subdirectory is writable: "
                    f"{case_id}/{directory.relative_to(case_dir)}"
                )
        execution = json.loads(
            (case_dir / "execution.json").read_text(encoding="utf-8")
        )
        _assert_public_json_keys(execution)
        if set(execution) != {"schema", "tool_calls"}:
            raise BundleError(f"execution audit exposes extra metadata: {case_id}")
        for tool in execution["tool_calls"]:
            if set(tool) not in ({"type"}, {"type", "literal"}):
                raise BundleError(f"execution tool row exposes extra metadata: {case_id}")
        output_document = json.loads(
            (case_dir / "output.json").read_text(encoding="utf-8")
        )
        validate_output_document(output_document)
    return {
        "status": "PASS",
        "case_count": len(cases),
        "copied_file_count": copied_file_count,
        "root_file_count": len(root_files),
        "manifest_sha256": sha256_file(manifest_path),
    }


def build_bundle(
    output: Path = DEFAULT_OUTPUT,
    analyst_dir: Path = ANALYST_DIR,
    packages: dict[str, Path] = PACKAGES,
) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise BundleError(f"refusing to overwrite review bundle: {output}")
    rows, aliases = _load_inputs(analyst_dir)
    records, final_available = _validate_terminal_runs(analyst_dir, rows)
    rows_by_id = {row["run_id"]: row for row in rows}
    all_run_ids = set(rows_by_id)
    all_block_ids = {row["block_id"] for row in rows}
    all_case_ids = {alias["case_id"] for alias in aliases}
    package_files = {
        arm: _package_files(path) for arm, path in packages.items()
    }
    if set(package_files) != {row["arm"] for row in rows}:
        raise BundleError("evidence-package arms differ from frozen schedule")

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent)
    )
    try:
        public_cases = []
        schema_source = analyst_dir / "review-output.schema.json"
        if not schema_source.is_file() or schema_source.is_symlink():
            raise BundleError("frozen public review-output schema is missing")
        schema_hash = _copy_exact(
            schema_source, staging / "review-output.schema.json"
        )
        for alias in aliases:
            case_id = alias["case_id"]
            run_id = alias["run_id"]
            row = rows_by_id[run_id]
            source_run = analyst_dir / "runs" / run_id
            case_dir = staging / "cases" / case_id
            copied: dict[str, str] = {}
            if final_available[run_id]:
                final_document = json.loads(
                    (source_run / "final.json").read_text(encoding="utf-8")
                )
                redaction = {
                    "assigned_package": packages[row["arm"]],
                    "all_packages": list(packages.values()),
                    "all_run_ids": all_run_ids,
                    "all_block_ids": all_block_ids,
                    "all_case_ids": all_case_ids,
                    "current_case_id": case_id,
                }
                output_path = case_dir / "output.json"
                dump_json(
                    output_path,
                    _redact_json_strings(final_document, **redaction),
                )
                copied["output.json"] = sha256_file(output_path)
            else:
                marker_path = case_dir / "output.json"
                dump_json(
                    marker_path,
                    UNAVAILABLE_OUTPUT,
                )
                copied["output.json"] = sha256_file(marker_path)
            for source in package_files[row["arm"]]:
                relative = f"evidence/{source.name}"
                copied[relative] = _copy_exact(source, case_dir / relative)
            execution_path = case_dir / "execution.json"
            dump_json(
                execution_path,
                _public_execution(
                    records[run_id],
                    packages[row["arm"]],
                    list(packages.values()),
                    all_run_ids,
                    all_block_ids,
                    all_case_ids,
                    case_id,
                ),
            )
            copied["execution.json"] = sha256_file(execution_path)
            public_cases.append(
                {
                    "case_id": case_id,
                    "path": f"cases/{case_id}",
                    "files": dict(sorted(copied.items())),
                }
            )

        manifest = {
            "schema": "agentsight.utility2.blind-review-manifest.v1",
            "case_count": 40,
            "instructions": INSTRUCTIONS,
            "decision_schema_path": "review-output.schema.json",
            "files": {"review-output.schema.json": schema_hash},
            "cases": public_cases,
        }
        _assert_public_json_keys(manifest)
        dump_json(staging / "manifest.json", manifest)
        _make_read_only(staging)
        result = verify_bundle(
            staging, {alias["case_id"] for alias in aliases}
        )
        staging.rename(output)
        return {
            **result,
            "bundle": str(output.resolve()),
        }
    except BaseException:
        if staging.exists():
            for path in staging.rglob("*"):
                if path.is_dir():
                    os.chmod(path, 0o755)
                elif path.is_file():
                    os.chmod(path, 0o644)
            os.chmod(staging, 0o755)
            shutil.rmtree(staging)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build_bundle(args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
