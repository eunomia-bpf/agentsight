#!/usr/bin/env python3
"""Summarize frozen analyst runs and prepare a randomized read-only review bundle."""

from __future__ import annotations

import hashlib
import json
import random
import re
import shutil
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parent
ANALYST = ROOT / "analyst"
PACKAGES = ROOT / "analyst-packages"
RUN_IDS = (
    "profile-1",
    "profile-2",
    "profile-3",
    "raw-operations-1",
    "raw-operations-2",
    "raw-operations-3",
)
REVIEW_SEED = 2026072902


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def dump_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def policy_word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", text))


def actual_commands(events_path: Path) -> list[str]:
    commands: list[str] = []
    with events_path.open(encoding="utf-8") as stream:
        for line in stream:
            event = json.loads(line)
            item = event.get("item", {})
            if (
                event.get("type") == "item.completed"
                and item.get("type") == "command_execution"
            ):
                commands.append(item["command"])
    return commands


def make_summary() -> dict:
    records = []
    for run_id in RUN_IDS:
        run_dir = ANALYST / "runs" / run_id
        run = load_json(run_dir / "run.json")
        final = load_json(run_dir / "final.json")
        usage = run["provider_usage_totals"]
        records.append(
            {
                "run_id": run_id,
                "arm": run["run"]["arm"],
                "replicate": run["run"]["replicate"],
                "order_position": run["run"]["position"],
                "status": run["status"],
                "exit_code": run["exit_code"],
                "final_response_elapsed_seconds": run[
                    "final_response_elapsed_seconds"
                ],
                "wall_seconds": run["wall_seconds"],
                "provider_usage": usage,
                # input_tokens is the provider's total input field; cached tokens
                # are reported separately and are not added again. The provider's
                # output_tokens field is used without adding its reasoning detail.
                "provider_total_tokens": usage.get("input_tokens", 0)
                + usage.get("output_tokens", 0),
                "model_turns": run["model_turns"],
                "tool_call_total": run["tool_call_total"],
                "policy_word_count": policy_word_count(final["policy_text"]),
                "diagnosis": final["diagnosis"],
                "policy_text": final["policy_text"],
                "actual_commands": actual_commands(run_dir / "events.jsonl"),
                "artifact_sha256": {
                    "run.json": sha256(run_dir / "run.json"),
                    "final.json": sha256(run_dir / "final.json"),
                    "events.jsonl": sha256(run_dir / "events.jsonl"),
                    "event-receipts.jsonl": sha256(
                        run_dir / "event-receipts.jsonl"
                    ),
                },
            }
        )

    arm_summaries = {}
    for arm in ("PROFILE", "RAW-OPERATIONS"):
        selected = [record for record in records if record["arm"] == arm]
        arm_summaries[arm] = {
            "run_count": len(selected),
            "successful_run_count": sum(
                record["status"] == "ok" and record["exit_code"] == 0
                for record in selected
            ),
            "median_final_response_seconds": median(
                record["final_response_elapsed_seconds"] for record in selected
            ),
            "median_provider_total_tokens": median(
                record["provider_total_tokens"] for record in selected
            ),
            "median_tool_calls": median(
                record["tool_call_total"] for record in selected
            ),
        }

    return {
        "schema": "agentsight.utility.analyst-summary.v1",
        "status": "awaiting-independent-validity-review",
        "token_definition": (
            "provider_total_tokens = input_tokens + output_tokens; "
            "cached_input_tokens and reasoning_output_tokens are reported "
            "details and are not double-counted"
        ),
        "records": records,
        "arm_summaries_before_validity_review": arm_summaries,
        "faster_finding": "not-evaluated-before-independent-validity-review",
    }


def prepare_review_bundle(summary: dict) -> dict:
    bundle = ANALYST / "review-bundle"
    if bundle.exists():
        raise SystemExit(
            f"refusing to replace existing review bundle: {bundle}"
        )
    bundle.mkdir(parents=True)

    shuffled = list(RUN_IDS)
    random.Random(REVIEW_SEED).shuffle(shuffled)
    private_mapping = {
        f"case-{index:02d}": run_id
        for index, run_id in enumerate(shuffled, start=1)
    }
    record_by_id = {
        record["run_id"]: record for record in summary["records"]
    }
    public_cases = []

    for alias, run_id in private_mapping.items():
        source_run = ANALYST / "runs" / run_id
        record = record_by_id[run_id]
        package_name = (
            "PROFILE" if record["arm"] == "PROFILE" else "RAW-OPERATIONS"
        )
        case_dir = bundle / alias
        evidence_dir = case_dir / "evidence"
        evidence_dir.mkdir(parents=True)
        shutil.copy2(source_run / "final.json", case_dir / "output.json")
        for source in sorted((PACKAGES / package_name).iterdir()):
            if source.is_file():
                shutil.copy2(source, evidence_dir / source.name)
        dump_json(
            case_dir / "execution.json",
            {
                "schema": "agentsight.utility.analyst-review-execution.v1",
                "status": record["status"],
                "exit_code": record["exit_code"],
                "actual_commands": record["actual_commands"],
                "instruction": (
                    "Every command was launched with the evidence directory "
                    "as its working directory. Audit whether it attempted to "
                    "read outside that directory."
                ),
            },
        )
        public_cases.append(
            {
                "alias": alias,
                "output": f"{alias}/output.json",
                "execution": f"{alias}/execution.json",
                "evidence_directory": f"{alias}/evidence",
                "file_sha256": {
                    str(path.relative_to(bundle)): sha256(path)
                    for path in sorted(case_dir.rglob("*"))
                    if path.is_file()
                },
            }
        )

    public_manifest = {
        "schema": "agentsight.utility.analyst-review-bundle.v1",
        "review_seed_sha256": hashlib.sha256(
            str(REVIEW_SEED).encode("ascii")
        ).hexdigest(),
        "case_count": len(public_cases),
        "cases": public_cases,
        "review_instructions": {
            "score_each_case": [
                "recurring bad-vs-good diagnosis is valid",
                "every quantitative finding is supported by rerunning the cited command",
                "policy is executable, benchmark-agnostic, and at most 60 English words",
                "no benchmark-specific answer or hidden-data reference appears",
                "execution commands did not attempt to read outside the supplied evidence directory",
            ],
            "do_not_open": (
                "Do not inspect any file outside this review-bundle directory; "
                "downstream outcomes do not exist and are out of scope."
            ),
        },
    }
    dump_json(bundle / "manifest.json", public_manifest)
    dump_json(
        ANALYST / "review-alias-map.private.json",
        {
            "schema": "agentsight.utility.analyst-review-alias-map.v1",
            "seed": REVIEW_SEED,
            "mapping": private_mapping,
        },
    )

    for path in bundle.rglob("*"):
        path.chmod(0o555 if path.is_dir() else 0o444)
    bundle.chmod(0o555)
    return public_manifest


def main() -> None:
    summary = make_summary()
    dump_json(ANALYST / "analyst-summary.json", summary)
    manifest = prepare_review_bundle(summary)
    print(
        json.dumps(
            {
                "summary": str(ANALYST / "analyst-summary.json"),
                "review_bundle": str(ANALYST / "review-bundle"),
                "case_count": manifest["case_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
