#!/usr/bin/env python3
"""Create or verify the externally anchored current adjudication contract."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any


EXPERIMENT = Path(
    os.environ.get(
        "AGENTSIGHT_EXPERIMENT_ROOT", Path(__file__).resolve().parent
    )
)
ANALYST = EXPERIMENT / "analyst"
POST = EXPERIMENT / "postreview-adjudication"
CONTRACT = POST / "frozen-contract.json"
BOOTSTRAP = EXPERIMENT / "postreview_bootstrap.py"
VERIFICATION = POST / "contract-verification.json"
CREATE_COMMAND = POST / "create-contract-command.json"
VERIFY_LAUNCH = POST / "verify-launch-command.json"
ORIGINAL_CONTRACT = EXPERIMENT / "frozen-contract-analyst.json"
ORIGINAL_CONTRACT_SHA256 = (
    "bf29f168183ff5776ee24c57ea3f926f1d2ab391abaa0052d9c19751cddbeca0"
)
ANALYSIS_OUTPUT = ANALYST / "analysis.json"
POLICIES_OUTPUT = ANALYST / "policies"
ARCHIVES = {
    1: (
        EXPERIMENT / "postreview-adjudication-rejected-attempt-001",
        POST / "rejected-attempt-001-manifest.json",
    ),
    2: (
        EXPERIMENT / "postreview-adjudication-rejected-attempt-002",
        POST / "rejected-attempt-002-manifest.json",
    ),
    3: (
        EXPERIMENT / "postreview-adjudication-rejected-attempt-003",
        POST / "rejected-attempt-003-manifest.json",
    ),
    4: (
        EXPERIMENT / "postreview-adjudication-rejected-attempt-004",
        POST / "rejected-attempt-004-manifest.json",
    ),
    5: (
        EXPERIMENT / "postreview-adjudication-rejected-attempt-005",
        POST / "rejected-attempt-005-manifest.json",
    ),
    6: (
        EXPERIMENT / "postreview-adjudication-rejected-attempt-006",
        POST / "rejected-attempt-006-manifest.json",
    ),
    7: (
        EXPERIMENT / "postreview-adjudication-rejected-attempt-007",
        POST / "rejected-attempt-007-manifest.json",
    ),
}

STATIC_FILES = (
    "adjudicate_reviewer_audit.py",
    "test_adjudicate_reviewer_audit.py",
    "postreview_bootstrap.py",
    "test_postreview_bootstrap.py",
    "run_adjudicated_analysis.py",
    "test_run_adjudicated_analysis.py",
    "frozen_numpy_shim.py",
    "test_frozen_numpy_shim.py",
    "generate_bootstrap_indices.py",
    "bootstrap-indices-pcg64-seed2026072903-i8le.bin",
    "freeze_adjudicated_rank1_policies.py",
    "test_freeze_adjudicated_rank1_policies.py",
    "verify_postreview_adjudication_contract.py",
    "test_verify_postreview_adjudication_contract.py",
    "postreview-adjudication/pre-unblinding-attestation.json",
    "postreview-adjudication/pre-unblinding-attestation.md",
    "postreview-adjudication/reviewer-role-allowlist.json",
    "postreview-adjudication/adjudication-command.json",
    "postreview-adjudication/create-contract-command.json",
    "postreview-adjudication/rejected-attempt-001-manifest.json",
    "postreview-adjudication/rejected-attempt-002-manifest.json",
    "postreview-adjudication/rejected-attempt-003-manifest.json",
    "postreview-adjudication/rejected-attempt-004-manifest.json",
    "postreview-adjudication/rejected-attempt-005-manifest.json",
    "postreview-adjudication/rejected-attempt-006-manifest.json",
    "postreview-adjudication/rejected-attempt-007-manifest.json",
)
ADJUDICATION_FILES = (
    "postreview-adjudication/adjudication/report.json",
    "postreview-adjudication/adjudication/corrected-provenance.json",
    "postreview-adjudication/adjudication/cited-command-role-receipts.json",
)
CONTRACT_FIELDS = {
    "schema",
    "stage",
    "created_at",
    "experiment",
    "analysis_absent_at_creation",
    "policies_absent_at_creation",
    "original_contract",
    "original_runtime_files",
    "postreview_static_files",
    "adjudication_files",
    "rejected_attempt_archives",
    "trusted_runtime",
    "semantics",
}
SHA256_RE = re.compile(r"[0-9a-f]{64}")


class PostreviewContractError(RuntimeError):
    """Raised when an anchored postreview binding is missing or changed."""


def require_isolated_runtime() -> None:
    if (
        sys.flags.isolated != 1
        or sys.flags.no_site != 1
        or not sys.flags.safe_path
    ):
        raise PostreviewContractError(
            "contract execution requires Python -I -S safe-path mode"
        )


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


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


class PayloadCache:
    """Read every verifier input once and reuse those exact immutable bytes."""

    def __init__(self) -> None:
        self._payloads: dict[Path, bytes] = {}

    def bytes(self, path: Path) -> bytes:
        path = Path(path)
        if path in self._payloads:
            return self._payloads[path]
        flags = os.O_RDONLY | os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise PostreviewContractError(
                    f"verifier input is not a regular file: {path}"
                )
            chunks = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            payload = b"".join(chunks)
        finally:
            os.close(descriptor)
        self._payloads[path] = payload
        return payload

    def sha256(self, path: Path) -> str:
        return hashlib.sha256(self.bytes(path)).hexdigest()

    def json(self, path: Path) -> Any:
        try:
            return json.loads(self.bytes(path))
        except json.JSONDecodeError as exc:
            raise PostreviewContractError(
                f"verifier JSON is malformed: {path}"
            ) from exc


def trusted_runtime_binding(cache: PayloadCache) -> dict[str, Any]:
    interpreter = Path(sys.executable).resolve()
    return {
        "interpreter_path": str(interpreter),
        "interpreter_sha256": cache.sha256(interpreter),
        "python_implementation": sys.implementation.name,
        "python_version": sys.version,
        "python_cache_tag": sys.implementation.cache_tag,
        "isolated_flag": True,
        "no_site_flag": True,
        "safe_path_flag": True,
        "environment_policy": (
            "bootstrap passes only AGENTSIGHT_EXPERIMENT_ROOT, "
            "PYTHONDONTWRITEBYTECODE, and PYTHONHASHSEED"
        ),
        "tcb_scope": (
            "the absolute Python interpreter and its standard library are "
            "explicit trusted-computing-base components"
        ),
    }


def create_literal() -> list[str]:
    interpreter = str(Path(sys.executable).resolve())
    return [
        interpreter,
        "-I",
        "-S",
        str(Path(__file__).resolve()),
        "--create",
        "--output",
        str(CONTRACT.resolve()),
    ]


def verify_literal(
    expected_contract_sha256: str,
    expected_bootstrap_sha256: str,
    expected_script_sha256: str,
    expected_interpreter_sha256: str,
) -> list[str]:
    interpreter = str(Path(sys.executable).resolve())
    return [
        interpreter,
        "-I",
        "-S",
        str(BOOTSTRAP.resolve()),
        "--contract",
        str(CONTRACT.resolve()),
        "--expected-contract-sha256",
        expected_contract_sha256,
        "--script",
        "verify_postreview_adjudication_contract.py",
        "--expected-script-sha256",
        expected_script_sha256,
        "--expected-bootstrap-sha256",
        expected_bootstrap_sha256,
        "--expected-interpreter-sha256",
        expected_interpreter_sha256,
        "--",
        "--verify",
        "--contract",
        str(CONTRACT.resolve()),
        "--expected-contract-sha256",
        expected_contract_sha256,
        "--output",
        str(VERIFICATION.resolve()),
    ]


def prepare_create_command() -> dict[str, Any]:
    if CREATE_COMMAND.exists() or CONTRACT.exists() or VERIFICATION.exists():
        raise PostreviewContractError(
            "refusing to overwrite contract creation preparation"
        )
    dump_json(
        CREATE_COMMAND,
        {
            "schema": "agentsight.utility2.postreview-contract-create.v8",
            "command_identifier": (
                "experiment-002-postreview-contract-create-v8"
            ),
            "command": create_literal(),
        },
    )
    return {
        "status": "PASS",
        "command_sha256": sha256_file(CREATE_COMMAND),
        "model_calls_made": 0,
    }


def prepare_verify_launch(
    expected_contract_sha256: str,
    expected_bootstrap_sha256: str,
    expected_script_sha256: str,
    expected_interpreter_sha256: str,
) -> dict[str, Any]:
    if VERIFY_LAUNCH.exists() or VERIFICATION.exists():
        raise PostreviewContractError(
            "refusing to overwrite verification launcher/output"
        )
    if sha256_file(CONTRACT) != expected_contract_sha256:
        raise PostreviewContractError("verification launch SHA is not current")
    contract_bytes = CONTRACT.read_bytes()
    contract = json.loads(contract_bytes)
    if (
        CONTRACT.read_bytes() != contract_bytes
        or sha256_file(BOOTSTRAP) != expected_bootstrap_sha256
        or sha256_file(Path(__file__)) != expected_script_sha256
        or contract["postreview_static_files"].get(
            "postreview_bootstrap.py"
        )
        != expected_bootstrap_sha256
        or contract["postreview_static_files"].get(
            "verify_postreview_adjudication_contract.py"
        )
        != expected_script_sha256
        or contract.get("trusted_runtime", {}).get(
            "interpreter_path"
        )
        != str(Path(sys.executable).resolve())
        or contract.get("trusted_runtime", {}).get(
            "interpreter_sha256"
        )
        != expected_interpreter_sha256
        or sha256_file(Path(sys.executable).resolve())
        != expected_interpreter_sha256
    ):
        raise PostreviewContractError(
            "verification launcher code differs from anchored contract"
        )
    dump_json(
        VERIFY_LAUNCH,
        {
            "schema": "agentsight.utility2.postreview-contract-verify-launch.v8",
            "command_identifier": (
                "experiment-002-postreview-contract-verify-v8"
            ),
            "external_trust_anchor": True,
            "command": verify_literal(
                expected_contract_sha256,
                expected_bootstrap_sha256,
                expected_script_sha256,
                expected_interpreter_sha256,
            ),
        },
    )
    return {
        "status": "PASS",
        "command_sha256": sha256_file(VERIFY_LAUNCH),
        "contract_sha256": expected_contract_sha256,
        "bootstrap_sha256": expected_bootstrap_sha256,
        "script_sha256": expected_script_sha256,
        "interpreter_sha256": expected_interpreter_sha256,
        "model_calls_made": 0,
    }


def _hash_required_files(
    relative_paths: tuple[str, ...], cache: PayloadCache
) -> dict[str, str]:
    hashes = {}
    for relative in relative_paths:
        path = EXPERIMENT / relative
        try:
            hashes[relative] = cache.sha256(path)
        except OSError as exc:
            raise PostreviewContractError(
                f"required regular file missing: {relative}"
            ) from exc
    return hashes


def runtime_files() -> tuple[str, ...]:
    paths = [ANALYST / "batch-run.json"]
    for root in (
        ANALYST / "runs",
        ANALYST / "review-run",
        ANALYST / "review-bundle",
    ):
        if not root.is_dir() or root.is_symlink():
            raise PostreviewContractError(f"runtime directory missing: {root}")
        for path in root.rglob("*"):
            if path.is_symlink():
                raise PostreviewContractError(
                    f"runtime symlink is forbidden: {path}"
                )
            if path.is_file():
                paths.append(path)
    return tuple(
        sorted({str(path.relative_to(EXPERIMENT)) for path in paths})
    )


def _verify_hash_map(
    registered: dict[str, str],
    current_names: tuple[str, ...],
    cache: PayloadCache,
    *,
    label: str,
) -> None:
    if set(registered) != set(current_names):
        raise PostreviewContractError(f"{label} file set changed")
    for relative, expected in registered.items():
        path = EXPERIMENT / relative
        try:
            actual = cache.sha256(path)
        except OSError:
            actual = None
        if actual != expected:
            raise PostreviewContractError(f"{label} hash changed: {relative}")


def verify_original_frozen_contract(
    cache: PayloadCache,
) -> dict[str, Any]:
    payload = cache.bytes(ORIGINAL_CONTRACT)
    if hashlib.sha256(payload).hexdigest() != ORIGINAL_CONTRACT_SHA256:
        raise PostreviewContractError("original analyst contract hash changed")
    original = json.loads(payload)
    files = original.get("files")
    if (
        original.get("stage") != "analyst"
        or original.get("experiment") != str(EXPERIMENT.resolve())
        or not isinstance(files, dict)
        or len(files) != 80
    ):
        raise PostreviewContractError("original analyst contract shape changed")
    _verify_hash_map(
        files, tuple(files), cache, label="original frozen"
    )
    return {
        "path": str(ORIGINAL_CONTRACT.resolve()),
        "sha256": ORIGINAL_CONTRACT_SHA256,
        "file_count": 80,
        "files": files,
    }


def verify_rejected_archives(cache: PayloadCache) -> dict[str, Any]:
    verified = {}
    for attempt, (archive, manifest_path) in ARCHIVES.items():
        manifest = cache.json(manifest_path)
        expected = manifest.get("post_move_all_file_sha256")
        expected_status = (
            "REJECTED_BY_TWO_INDEPENDENT_READ_ONLY_REVIEWS"
            if attempt < 6
            else "REJECTED_BY_INDEPENDENT_READ_ONLY_REVIEW_GATE"
        )
        if (
            manifest.get("attempt") != attempt
            or manifest.get("status") != expected_status
            or not isinstance(expected, dict)
        ):
            raise PostreviewContractError(
                f"rejected-attempt-{attempt} archive manifest changed"
            )
        current = {
            str(path.relative_to(archive)): cache.sha256(path)
            for path in archive.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        if current != expected:
            raise PostreviewContractError(
                f"rejected-attempt-{attempt} archive hash set changed"
            )
        verified[str(attempt)] = {
            "path": str(archive.resolve()),
            "file_count": len(expected),
            "manifest_path": str(manifest_path.resolve()),
            "manifest_sha256": cache.sha256(manifest_path),
            "all_file_sha256": expected,
        }
    return verified


def verify_bundle_without_alias(cache: PayloadCache) -> dict[str, Any]:
    manifest_path = ANALYST / "review-bundle" / "manifest.json"
    manifest = cache.json(manifest_path)
    cases = manifest["cases"]
    case_ids = {row["case_id"] for row in cases}
    if len(cases) != 40 or len(case_ids) != 40:
        raise PostreviewContractError("public bundle is not 40 unique cases")
    expected_files: dict[str, str] = {
        relative: expected
        for relative, expected in manifest["files"].items()
    }
    for case in cases:
        for relative, expected in case["files"].items():
            expected_files[f"{case['path']}/{relative}"] = expected
    current_files = {
        str(path.relative_to(ANALYST / "review-bundle")): cache.sha256(path)
        for path in (ANALYST / "review-bundle").rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and path.name != "manifest.json"
    }
    if current_files != expected_files:
        raise PostreviewContractError("public bundle file/hash set changed")
    return {
        "case_count": 40,
        "alias_map_not_read": True,
        "manifest_sha256": cache.sha256(manifest_path),
    }


def _assert_downstream_absent_for_creation() -> None:
    if (
        ANALYSIS_OUTPUT.exists()
        or ANALYSIS_OUTPUT.is_symlink()
        or POLICIES_OUTPUT.exists()
        or POLICIES_OUTPUT.is_symlink()
    ):
        raise PostreviewContractError(
            "analysis and policies must be absent when creating contract"
        )


def verify_adjudication_without_import(
    cache: PayloadCache,
) -> dict[str, Any]:
    report_path = POST / "adjudication" / "report.json"
    corrected_path = POST / "adjudication" / "corrected-provenance.json"
    receipts_path = (
        POST / "adjudication" / "cited-command-role-receipts.json"
    )
    report = cache.json(report_path)
    original_path = ANALYST / "review-run" / "run.json"
    original = cache.json(original_path)
    corrected = cache.json(corrected_path)
    if set(corrected) != set(original):
        raise PostreviewContractError("corrected provenance field set changed")
    for field in original:
        expected = (
            "ok"
            if field == "status"
            else []
            if field == "validation_errors"
            else original[field]
        )
        if corrected[field] != expected:
            raise PostreviewContractError(
                f"corrected provenance changed forbidden field: {field}"
            )
    if (
        report.get("status") != "PASS"
        or report.get("reaudit_status") != "PASS"
        or report.get("decisions_reused") is not True
        or report.get("reviewer_model_rerun") is not False
        or report.get("corrected_provenance_sha256")
        != cache.sha256(corrected_path)
        or report.get("cited_command_reaudit", {}).get(
            "role_receipts_sha256"
        )
        != cache.sha256(receipts_path)
        or report.get("pre_result_unblinding_attestation_sha256")
        != cache.sha256(POST / "pre-unblinding-attestation.json")
        or report.get("exact_role_allowlist_sha256")
        != cache.sha256(POST / "reviewer-role-allowlist.json")
    ):
        raise PostreviewContractError("adjudication report binding changed")
    for path in (report_path, corrected_path, receipts_path):
        if path.stat().st_mode & 0o222:
            raise PostreviewContractError("adjudication output is writable")
    return report


def _current_bindings(
    cache: PayloadCache | None = None,
) -> dict[str, Any]:
    cache = cache or PayloadCache()
    original = verify_original_frozen_contract(cache)
    archives = verify_rejected_archives(cache)
    bundle = verify_bundle_without_alias(cache)
    report = verify_adjudication_without_import(cache)
    runtime_names = runtime_files()
    return {
        "original_contract": original,
        "original_runtime_files": _hash_required_files(
            runtime_names, cache
        ),
        "postreview_static_files": _hash_required_files(
            STATIC_FILES, cache
        ),
        "adjudication_files": _hash_required_files(
            ADJUDICATION_FILES, cache
        ),
        "rejected_attempt_archives": archives,
        "trusted_runtime": trusted_runtime_binding(cache),
        "semantics": {
            "bundle": bundle,
            "original_reviewer_status": "failed",
            "corrected_reviewer_status": "ok",
            "correction_type": report["correction_type"],
            "decisions_reused": report["decisions_reused"],
            "reviewer_model_rerun": report["reviewer_model_rerun"],
            "outer_command_reaudit_count": report[
                "outer_command_reaudit"
            ]["command_count"],
            "cited_command_reaudit_count": report[
                "cited_command_reaudit"
            ]["command_count"],
            "unique_cited_command_reaudit_count": report[
                "cited_command_reaudit"
            ]["unique_command_count"],
            "ordered_cited_hash_receipt_count": report[
                "cited_command_reaudit"
            ]["ordered_command_hash_receipt_count"],
            "no_network_sandbox_replay_count": report[
                "cited_command_reaudit"
            ]["no_network_sandbox_replay_count"],
            "risk_count": (
                report["outer_command_reaudit"]["risk_count"]
                + report["cited_command_reaudit"]["risk_count"]
            ),
            "bootstrap_indices": {
                "generator": "numpy.random.Generator(PCG64)",
                "seed": 2026072903,
                "shape": [100_000, 20],
                "dtype": "little-endian-int64",
                "sha256": cache.sha256(
                    EXPERIMENT
                    / "bootstrap-indices-pcg64-seed2026072903-i8le.bin"
                ),
                "generated_before_analysis": True,
                "analysis_inputs_read_during_generation": 0,
            },
            "numpy_execution": {
                "live_numpy_import_forbidden": True,
                "contract_bound_pure_stdlib_subset": True,
                "synthetic_equivalence_test_bound": True,
                "confirmatory_fields_exact_against_numpy": True,
                "descriptive_arithmetic_mean_may_differ_last_ulp": True,
                "arithmetic_mean_not_consumed_by_any_gate": True,
            },
            "policy_publication": {
                "private_random_store": True,
                "public_relative_symlink_no_replace": True,
                "final_live_binding_check_is_linearization_point": True,
                "consumer_revalidation_required_after_publication": True,
            },
        },
    }


def create_contract(output: Path) -> dict[str, Any]:
    require_isolated_runtime()
    if output.resolve() != CONTRACT.resolve():
        raise PostreviewContractError("contract output differs from frozen path")
    if output.exists() or output.is_symlink():
        raise PostreviewContractError("refusing to overwrite postreview contract")
    _assert_downstream_absent_for_creation()
    bindings = _current_bindings(PayloadCache())
    payload = {
        "schema": "agentsight.utility2.postreview-adjudication-contract.v8",
        "stage": "postreview-adjudication-attempt-8-pre-analysis",
        "created_at": utc_now(),
        "experiment": str(EXPERIMENT.resolve()),
        "analysis_absent_at_creation": True,
        "policies_absent_at_creation": True,
        **bindings,
    }
    if set(payload) != CONTRACT_FIELDS:
        raise PostreviewContractError("contract creator field set changed")
    dump_json(output, payload)
    os_mode = output.stat().st_mode
    output.chmod(os_mode & ~0o222)
    return {
        "status": "PASS",
        "contract_sha256": sha256_file(output),
        "total_file_count": (
            1
            + 1
            + payload["original_contract"]["file_count"]
            + len(payload["original_runtime_files"])
            + len(payload["postreview_static_files"])
            + len(payload["adjudication_files"])
            + sum(
                row["file_count"]
                for row in payload["rejected_attempt_archives"].values()
            )
        ),
        "analysis_calls_made": 0,
        "policy_files_written": 0,
    }


def verify_contract(
    contract_path: Path,
    output: Path | None,
    expected_contract_sha256: str,
) -> dict[str, Any]:
    if contract_path.resolve() != CONTRACT.resolve():
        raise PostreviewContractError("contract path differs from frozen path")
    if SHA256_RE.fullmatch(expected_contract_sha256) is None:
        raise PostreviewContractError("expected contract SHA is malformed")
    contract_bytes = contract_path.read_bytes()
    actual_contract_sha256 = hashlib.sha256(contract_bytes).hexdigest()
    if actual_contract_sha256 != expected_contract_sha256:
        raise PostreviewContractError("external contract SHA anchor mismatch")
    if output is not None and output.resolve() != VERIFICATION.resolve():
        raise PostreviewContractError(
            "verification output differs from frozen path"
        )
    contract = json.loads(contract_bytes)
    if set(contract) != CONTRACT_FIELDS:
        raise PostreviewContractError("contract exact field set changed")
    if (
        contract["schema"]
        != "agentsight.utility2.postreview-adjudication-contract.v8"
        or contract["stage"]
        != "postreview-adjudication-attempt-8-pre-analysis"
        or contract["experiment"] != str(EXPERIMENT.resolve())
        or contract["analysis_absent_at_creation"] is not True
        or contract["policies_absent_at_creation"] is not True
    ):
        raise PostreviewContractError("contract identity changed")
    current = _current_bindings(PayloadCache())
    for field in (
        "original_contract",
        "original_runtime_files",
        "postreview_static_files",
        "adjudication_files",
        "rejected_attempt_archives",
        "trusted_runtime",
        "semantics",
    ):
        if contract[field] != current[field]:
            raise PostreviewContractError(f"contract binding changed: {field}")
    if contract_path.read_bytes() != contract_bytes:
        raise PostreviewContractError(
            "contract changed after anchored byte parsing"
        )
    record = {
        "schema": (
            "agentsight.utility2.postreview-adjudication-verification.v8"
        ),
        "status": "PASS",
        "stage": contract["stage"],
        "checked_at": utc_now(),
        "contract": str(contract_path.resolve()),
        "contract_sha256": actual_contract_sha256,
        "external_contract_sha_anchor_checked": True,
        "total_file_count": (
            1
            + 1
            + contract["original_contract"]["file_count"]
            + len(contract["original_runtime_files"])
            + len(contract["postreview_static_files"])
            + len(contract["adjudication_files"])
            + sum(
                row["file_count"]
                for row in contract["rejected_attempt_archives"].values()
            )
        ),
        "original_frozen_file_count": 80,
        "analysis_may_be_absent_or_present_after_creation": True,
        "policies_may_be_absent_or_present_after_creation": True,
    }
    if output is not None:
        if output.exists() or output.is_symlink():
            raise PostreviewContractError(
                "refusing to overwrite postreview verification"
            )
        dump_json(output, record)
        output.chmod(output.stat().st_mode & ~0o222)
    return {**record, "contract_document": contract}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare-create-command", action="store_true")
    actions.add_argument("--prepare-verify-launch", action="store_true")
    actions.add_argument("--create", action="store_true")
    actions.add_argument("--verify", action="store_true")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--expected-contract-sha256")
    parser.add_argument("--expected-bootstrap-sha256")
    parser.add_argument("--expected-script-sha256")
    parser.add_argument("--expected-interpreter-sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.prepare_create_command:
        result = prepare_create_command()
    elif args.prepare_verify_launch:
        if (
            args.expected_contract_sha256 is None
            or args.expected_bootstrap_sha256 is None
            or args.expected_script_sha256 is None
            or args.expected_interpreter_sha256 is None
        ):
            raise SystemExit(
                "verify launcher requires contract, bootstrap, script, "
                "and interpreter SHAs"
            )
        result = prepare_verify_launch(
            args.expected_contract_sha256,
            args.expected_bootstrap_sha256,
            args.expected_script_sha256,
            args.expected_interpreter_sha256,
        )
    elif args.create:
        if args.output is None:
            raise SystemExit("--create requires --output")
        result = create_contract(args.output)
    else:
        if (
            args.contract is None
            or args.expected_contract_sha256 is None
            or args.output is None
        ):
            raise SystemExit(
                "--verify requires contract, expected SHA, and output"
            )
        require_isolated_runtime()
        result = verify_contract(
            args.contract, args.output, args.expected_contract_sha256
        )
        result = {
            key: value
            for key, value in result.items()
            if key != "contract_document"
        }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
