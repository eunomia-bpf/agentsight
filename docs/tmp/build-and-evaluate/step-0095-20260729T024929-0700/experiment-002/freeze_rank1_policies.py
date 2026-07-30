#!/usr/bin/env python3
"""Prepare post-review commands or freeze the two preregistered rank-1 policies."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

import analyze_analyst_efficiency
import run_analysts


EXPERIMENT = Path(__file__).resolve().parent
ANALYST_DIR = EXPERIMENT / "analyst"
DEFAULT_VERIFICATION = EXPERIMENT / "contract-verification-analyst.json"
SCHEDULE = ANALYST_DIR / "order.json"
RUNS_ROOT = ANALYST_DIR / "runs"
DECISIONS = ANALYST_DIR / "review-run" / "decisions.json"
ALIAS_MAP = ANALYST_DIR / "review-alias-map.private.json"
REVIEW_PROVENANCE = ANALYST_DIR / "review-run" / "run.json"
ANALYSIS_OUTPUT = ANALYST_DIR / "analysis.json"
POLICIES_OUTPUT = ANALYST_DIR / "policies"
ANALYSIS_COMMAND_PATH = ANALYST_DIR / "analysis-command.json"
FREEZE_COMMAND_PATH = ANALYST_DIR / "policy-freeze-command.json"
ANALYSIS_COMMAND_IDENTIFIER = "experiment-002-analyst-analysis-v1"
FREEZE_COMMAND_IDENTIFIER = "experiment-002-rank1-policy-freeze-v1"
POLICY_FILES = {
    "PROFILE": "profile-policy.txt",
    "RAW-OPERATIONS": "raw-policy.txt",
}
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")


class PolicyFreezeError(RuntimeError):
    """Raised when policy freezing would violate a preregistered binding."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def analysis_command() -> list[str]:
    return [
        "python3",
        str((EXPERIMENT / "analyze_analyst_efficiency.py").resolve()),
        "--schedule",
        str(SCHEDULE.resolve()),
        "--runs-root",
        str(RUNS_ROOT.resolve()),
        "--validity-review",
        str(DECISIONS.resolve()),
        "--alias-map",
        str(ALIAS_MAP.resolve()),
        "--review-provenance",
        str(REVIEW_PROVENANCE.resolve()),
        "--output",
        str(ANALYSIS_OUTPUT.resolve()),
    ]


def freeze_command() -> list[str]:
    return [
        "python3",
        str(Path(__file__).resolve()),
        "--execute-freeze",
        "--contract-verification",
        str(DEFAULT_VERIFICATION.resolve()),
        "--analysis",
        str(ANALYSIS_OUTPUT.resolve()),
        "--review-decisions",
        str(DECISIONS.resolve()),
        "--review-provenance",
        str(REVIEW_PROVENANCE.resolve()),
    ]


def prepare() -> dict[str, Any]:
    if ANALYSIS_OUTPUT.exists() or POLICIES_OUTPUT.exists():
        raise PolicyFreezeError("refusing to prepare after analysis/policy freeze")
    dump_json(
        ANALYSIS_COMMAND_PATH,
        {
            "schema": "agentsight.utility2.analyst-analysis-command.v1",
            "command_identifier": ANALYSIS_COMMAND_IDENTIFIER,
            "command": analysis_command(),
        },
    )
    dump_json(
        FREEZE_COMMAND_PATH,
        {
            "schema": "agentsight.utility2.rank1-policy-freeze-command.v1",
            "command_identifier": FREEZE_COMMAND_IDENTIFIER,
            "command": freeze_command(),
        },
    )
    return {
        "status": "PASS",
        "analysis_command_identifier": ANALYSIS_COMMAND_IDENTIFIER,
        "analysis_command_sha256": sha256_file(ANALYSIS_COMMAND_PATH),
        "freeze_command_identifier": FREEZE_COMMAND_IDENTIFIER,
        "freeze_command_sha256": sha256_file(FREEZE_COMMAND_PATH),
        "analysis_calls_made": 0,
        "policy_files_written": 0,
    }


def _frozen_literal(path: Path, schema: str, identifier: str) -> list[str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if (
        document.get("schema") != schema
        or document.get("command_identifier") != identifier
        or not isinstance(document.get("command"), list)
    ):
        raise PolicyFreezeError(f"malformed frozen command: {path}")
    return document["command"]


def count_english_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def _rank1_policy_sources(
    schedule_path: Path = SCHEDULE,
    runs_root: Path = RUNS_ROOT,
) -> dict[str, dict[str, Any]]:
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    rows = schedule.get("runs")
    rank_1 = schedule.get("rank_1")
    if (
        not isinstance(rows, list)
        or len(rows) != 40
        or not isinstance(rank_1, dict)
        or set(rank_1) != set(POLICY_FILES)
    ):
        raise PolicyFreezeError("frozen schedule/rank-1 mapping is malformed")
    selected: dict[str, dict[str, Any]] = {}
    for arm in POLICY_FILES:
        matching = [
            row
            for row in rows
            if row.get("arm") == arm and row.get("arm_rank") == 1
        ]
        if (
            len(matching) != 1
            or matching[0].get("run_id") != rank_1[arm]
        ):
            raise PolicyFreezeError(f"rank-1 selection changed for {arm}")
        run_id = rank_1[arm]
        run_path = runs_root / run_id / "run.json"
        final_path = runs_root / run_id / "final.json"
        run = json.loads(run_path.read_text(encoding="utf-8"))
        final = json.loads(final_path.read_text(encoding="utf-8"))
        if (
            run.get("status") != "ok"
            or run.get("run", {}).get("run_id") != run_id
            or run.get("run", {}).get("arm") != arm
            or not isinstance(final, dict)
            or set(final)
            != {
                "diagnosis",
                "quantitative_evidence",
                "policy_text",
                "expected_mechanism",
            }
        ):
            raise PolicyFreezeError(f"rank-1 source is not the exact valid run: {arm}")
        policy = final["policy_text"]
        words = count_english_words(policy) if isinstance(policy, str) else 0
        if not isinstance(policy, str) or not policy.strip() or not 1 <= words <= 60:
            raise PolicyFreezeError(
                f"rank-1 policy must contain 1..60 English words: {arm}"
            )
        selected[arm] = {
            "run_id": run_id,
            "policy_text": policy,
            "word_count": words,
            "run_record_sha256": sha256_file(run_path),
            "final_sha256": sha256_file(final_path),
        }
    return selected


def _assert_analysis_admission(
    registered: dict[str, Any], recomputed: dict[str, Any]
) -> None:
    if registered != recomputed:
        raise PolicyFreezeError(
            "registered analysis differs from fresh literal recomputation"
        )
    if registered.get("confirmatory_gate", {}).get("pass") is not True:
        raise PolicyFreezeError("confirmatory analyst-efficiency gate did not pass")
    if registered.get("rank_1_policy_gate", {}).get("pass") is not True:
        raise PolicyFreezeError("rank-1 policy validity gate did not pass")


def _write_policy_artifacts(
    output: Path,
    selected: dict[str, dict[str, Any]],
    bindings: dict[str, Any],
) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise PolicyFreezeError(f"refusing to overwrite policy output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent)
    )
    try:
        policy_rows: dict[str, Any] = {}
        for arm, filename in POLICY_FILES.items():
            target = staging / filename
            policy = selected[arm]["policy_text"]
            target.write_text(policy, encoding="utf-8")
            if target.read_text(encoding="utf-8") != policy:
                raise PolicyFreezeError(f"policy text changed while writing: {arm}")
            policy_rows[arm] = {
                **{key: value for key, value in selected[arm].items() if key != "policy_text"},
                "file": filename,
                "policy_sha256": sha256_file(target),
            }
        manifest = {
            "schema": "agentsight.utility2.rank1-policy-freeze.v1",
            "status": "PASS",
            "no_substitution": True,
            "policies": policy_rows,
            "bindings": bindings,
        }
        dump_json(staging / "manifest.json", manifest)
        staging.rename(output)
        return manifest
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def execute(
    verification_path: Path,
    analysis_path: Path,
    review_decisions_path: Path,
    review_provenance_path: Path,
) -> dict[str, Any]:
    if (
        verification_path.resolve() != DEFAULT_VERIFICATION.resolve()
        or analysis_path.resolve() != ANALYSIS_OUTPUT.resolve()
        or review_decisions_path.resolve() != DECISIONS.resolve()
        or review_provenance_path.resolve() != REVIEW_PROVENANCE.resolve()
    ):
        raise PolicyFreezeError("policy freeze inputs differ from frozen paths")
    run_analysts.verify_execution_gate(verification_path)
    if analysis_command() != _frozen_literal(
        ANALYSIS_COMMAND_PATH,
        "agentsight.utility2.analyst-analysis-command.v1",
        ANALYSIS_COMMAND_IDENTIFIER,
    ):
        raise PolicyFreezeError("dynamic analysis command changed")
    if freeze_command() != _frozen_literal(
        FREEZE_COMMAND_PATH,
        "agentsight.utility2.rank1-policy-freeze-command.v1",
        FREEZE_COMMAND_IDENTIFIER,
    ):
        raise PolicyFreezeError("dynamic policy-freeze command changed")
    registered = json.loads(analysis_path.read_text(encoding="utf-8"))
    recomputed = analyze_analyst_efficiency.analyze(
        schedule_path=SCHEDULE,
        runs_root=RUNS_ROOT,
        validity_review_path=review_decisions_path,
        alias_map_path=ALIAS_MAP,
        review_provenance_path=review_provenance_path,
    )
    _assert_analysis_admission(registered, recomputed)
    selected = _rank1_policy_sources()
    selected_gate = registered["rank_1_policy_gate"]["selected_runs"]
    if any(
        selected_gate.get(arm, {}).get("run_id") != selected[arm]["run_id"]
        or selected_gate.get(arm, {}).get("valid") is not True
        for arm in POLICY_FILES
    ):
        raise PolicyFreezeError("rank-1 analysis selection differs from schedule")

    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    provenance = json.loads(review_provenance_path.read_text(encoding="utf-8"))
    current_bundle_manifest = (
        ANALYST_DIR / "review-bundle" / "manifest.json"
    )
    bundle_sha = sha256_file(current_bundle_manifest)
    if not (
        provenance.get("review_bundle_manifest_unchanged") is True
        and provenance.get("review_bundle_manifest_sha256_before")
        == provenance.get("review_bundle_manifest_sha256_after")
        == bundle_sha
    ):
        raise PolicyFreezeError("review-bundle provenance binding changed")
    bindings = {
        "contract": {
            "path": verification["contract"],
            "sha256": verification["contract_sha256"],
        },
        "review_decisions": {
            "path": str(review_decisions_path.resolve()),
            "sha256": sha256_file(review_decisions_path),
        },
        "review_provenance": {
            "path": str(review_provenance_path.resolve()),
            "sha256": sha256_file(review_provenance_path),
        },
        "review_bundle_manifest": {
            "path": str(current_bundle_manifest.resolve()),
            "sha256": bundle_sha,
        },
        "analysis": {
            "path": str(analysis_path.resolve()),
            "sha256": sha256_file(analysis_path),
            "fresh_recomputation_equal": True,
            "confirmatory_gate_pass": True,
            "rank_1_policy_gate_pass": True,
        },
        "commands": {
            "analysis_command_sha256": sha256_file(ANALYSIS_COMMAND_PATH),
            "policy_freeze_command_sha256": sha256_file(FREEZE_COMMAND_PATH),
        },
    }
    return _write_policy_artifacts(POLICIES_OUTPUT, selected, bindings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--execute-freeze", action="store_true")
    parser.add_argument("--contract-verification", type=Path)
    parser.add_argument("--analysis", type=Path)
    parser.add_argument("--review-decisions", type=Path)
    parser.add_argument("--review-provenance", type=Path)
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(prepare(), sort_keys=True))
        return 0
    required = (
        args.contract_verification,
        args.analysis,
        args.review_decisions,
        args.review_provenance,
    )
    if any(path is None for path in required):
        raise SystemExit(
            "--execute-freeze requires contract, analysis, decisions, and provenance"
        )
    result = execute(
        args.contract_verification,
        args.analysis,
        args.review_decisions,
        args.review_provenance,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
