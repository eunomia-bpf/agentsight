#!/usr/bin/env python3
"""Freeze rank-1 policies from a contract-verified immutable snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import types
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
LAUNCH_COMMAND = POST / "policy-launch-command.json"
ANALYSIS = ANALYST / "analysis.json"
POLICIES = ANALYST / "policies"
SCRIPT_RELATIVE = "freeze_adjudicated_rank1_policies.py"
COMMAND_IDENTIFIER = "experiment-002-adjudicated-rank1-policy-freeze-v8"
POLICY_FILES = {
    "PROFILE": "profile-policy.txt",
    "RAW-OPERATIONS": "raw-policy.txt",
}
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")


class AdjudicatedPolicyFreezeError(RuntimeError):
    """Raised when anchored snapshot policy freezing is not exact."""


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


def launch_literal(
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
        SCRIPT_RELATIVE,
        "--expected-script-sha256",
        expected_script_sha256,
        "--expected-bootstrap-sha256",
        expected_bootstrap_sha256,
        "--expected-interpreter-sha256",
        expected_interpreter_sha256,
        "--",
        "--execute",
        "--contract",
        str(CONTRACT.resolve()),
        "--expected-contract-sha256",
        expected_contract_sha256,
        "--analysis",
        str(ANALYSIS.resolve()),
    ]


def prepare_launch(
    expected_contract_sha256: str,
    expected_bootstrap_sha256: str,
    expected_script_sha256: str,
    expected_interpreter_sha256: str,
) -> dict[str, Any]:
    if (
        LAUNCH_COMMAND.exists()
        or ANALYSIS.exists()
        or POLICIES.exists()
        or POLICIES.is_symlink()
    ):
        raise AdjudicatedPolicyFreezeError(
            "refusing to overwrite launcher or prepare after downstream output"
        )
    if sha256_file(CONTRACT) != expected_contract_sha256:
        raise AdjudicatedPolicyFreezeError("launch contract SHA is not current")
    contract = read_anchored_contract(
        CONTRACT, expected_contract_sha256
    )
    if (
        sha256_file(BOOTSTRAP) != expected_bootstrap_sha256
        or sha256_file(Path(__file__)) != expected_script_sha256
        or contract["postreview_static_files"].get(
            "postreview_bootstrap.py"
        )
        != expected_bootstrap_sha256
        or contract["postreview_static_files"].get(SCRIPT_RELATIVE)
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
        raise AdjudicatedPolicyFreezeError(
            "launcher code hashes differ from contract/external anchors"
        )
    dump_json(
        LAUNCH_COMMAND,
        {
            "schema": (
                "agentsight.utility2.adjudicated-rank1-policy-launch.v8"
            ),
            "command_identifier": COMMAND_IDENTIFIER,
            "external_trust_anchor": True,
            "command": launch_literal(
                expected_contract_sha256,
                expected_bootstrap_sha256,
                expected_script_sha256,
                expected_interpreter_sha256,
            ),
        },
    )
    return {
        "status": "PASS",
        "command_identifier": COMMAND_IDENTIFIER,
        "command_sha256": sha256_file(LAUNCH_COMMAND),
        "contract_sha256": expected_contract_sha256,
        "bootstrap_sha256": expected_bootstrap_sha256,
        "script_sha256": expected_script_sha256,
        "interpreter_sha256": expected_interpreter_sha256,
        "analysis_calls_made": 0,
        "policy_files_written": 0,
    }


def contract_file_hash(contract: dict[str, Any], relative: str) -> str:
    maps = (
        contract["original_contract"]["files"],
        contract["original_runtime_files"],
        contract["postreview_static_files"],
        contract["adjudication_files"],
    )
    matches = [mapping[relative] for mapping in maps if relative in mapping]
    if len(matches) != 1:
        raise AdjudicatedPolicyFreezeError(
            f"snapshot input is not uniquely contract-bound: {relative}"
        )
    return matches[0]


def read_regular_file_once(path: Path) -> bytes:
    flags = os.O_RDONLY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise AdjudicatedPolicyFreezeError(
                f"input is not a regular file: {path}"
            )
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def load_contract_module(
    contract: dict[str, Any], relative: str, module_name: str
) -> Any:
    payload = read_regular_file_once(EXPERIMENT / relative)
    expected = contract_file_hash(contract, relative)
    if hashlib.sha256(payload).hexdigest() != expected:
        raise AdjudicatedPolicyFreezeError(
            f"contract module payload hash changed: {relative}"
        )
    module = types.ModuleType(module_name)
    module.__file__ = relative
    exec(compile(payload, relative, "exec"), module.__dict__)
    return module


def read_anchored_contract(path: Path, expected_sha256: str) -> dict[str, Any]:
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise AdjudicatedPolicyFreezeError(
            "external contract SHA anchor mismatch"
        )
    document = json.loads(payload)
    if path.read_bytes() != payload:
        raise AdjudicatedPolicyFreezeError(
            "contract changed after anchored byte parsing"
        )
    return document


def count_english_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def assert_analysis_admission(
    registered: dict[str, Any], recomputed: dict[str, Any]
) -> None:
    if registered != recomputed:
        raise AdjudicatedPolicyFreezeError(
            "registered analysis differs from fresh snapshot recomputation"
        )
    if registered.get("confirmatory_gate", {}).get("pass") is not True:
        raise AdjudicatedPolicyFreezeError(
            "confirmatory analyst-efficiency gate did not pass"
        )
    if registered.get("rank_1_policy_gate", {}).get("pass") is not True:
        raise AdjudicatedPolicyFreezeError(
            "rank-1 policy validity gate did not pass"
        )


def rank1_policy_sources(
    contract: dict[str, Any],
    analysis_module: Any,
    sealed_payloads: list[Any],
) -> dict[str, dict[str, Any]]:
    def sealed_json(relative: str) -> tuple[dict[str, Any], str]:
        expected = contract_file_hash(contract, relative)
        payload = analysis_module.SealedPayload.from_live(
            EXPERIMENT / relative, expected, relative
        )
        sealed_payloads.append(payload)
        try:
            document = json.loads(payload.read())
        except json.JSONDecodeError as exc:
            raise AdjudicatedPolicyFreezeError(
                f"sealed rank-1 JSON is malformed: {relative}"
            ) from exc
        return document, expected

    schedule, _schedule_hash = sealed_json("analyst/order.json")
    rows = schedule.get("runs")
    rank_1 = schedule.get("rank_1")
    if (
        not isinstance(rows, list)
        or len(rows) != 40
        or not isinstance(rank_1, dict)
        or set(rank_1) != set(POLICY_FILES)
    ):
        raise AdjudicatedPolicyFreezeError(
            "frozen schedule/rank-1 mapping is malformed"
        )
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
            raise AdjudicatedPolicyFreezeError(
                f"rank-1 selection changed for {arm}"
            )
        run_id = rank_1[arm]
        run_relative = f"analyst/runs/{run_id}/run.json"
        final_relative = f"analyst/runs/{run_id}/final.json"
        run, run_hash = sealed_json(run_relative)
        final, final_hash = sealed_json(final_relative)
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
            raise AdjudicatedPolicyFreezeError(
                f"rank-1 source is not the exact valid run: {arm}"
            )
        policy = final["policy_text"]
        words = count_english_words(policy) if isinstance(policy, str) else 0
        if (
            not isinstance(policy, str)
            or not policy.strip()
            or not 1 <= words <= 60
        ):
            raise AdjudicatedPolicyFreezeError(
                f"rank-1 policy must contain 1..60 English words: {arm}"
            )
        selected[arm] = {
            "run_id": run_id,
            "policy_text": policy,
            "word_count": words,
            "run_record_sha256": run_hash,
            "final_sha256": final_hash,
        }
    return selected


def _write_all(descriptor: int, payload: bytes) -> None:
    written = 0
    while written < len(payload):
        count = os.write(descriptor, payload[written:])
        if count <= 0:
            raise AdjudicatedPolicyFreezeError(
                "short write while committing policy artifact"
            )
        written += count


def _read_policy_fd(descriptor: int) -> bytes:
    size = os.fstat(descriptor).st_size
    payload = os.pread(descriptor, size + 1, 0)
    if len(payload) != size:
        raise AdjudicatedPolicyFreezeError(
            "policy artifact descriptor size changed"
        )
    return payload


def _assert_directory_path_binding(path: Path, held_fd: int) -> None:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    current_fd = os.open(path, flags)
    try:
        held = os.fstat(held_fd)
        current = os.fstat(current_fd)
        if (held.st_dev, held.st_ino) != (current.st_dev, current.st_ino):
            raise AdjudicatedPolicyFreezeError(
                f"policy parent directory pathname changed: {path}"
            )
    finally:
        os.close(current_fd)


def _assert_directory_entry_matches_fd(
    parent_fd: int, name: str, held_fd: int
) -> None:
    entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    held = os.fstat(held_fd)
    if (
        not stat.S_ISDIR(entry.st_mode)
        or (entry.st_dev, entry.st_ino) != (held.st_dev, held.st_ino)
    ):
        raise AdjudicatedPolicyFreezeError(
            "reserved policy directory pathname changed"
        )


def _entry_exists_at(parent_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def _assert_public_policy_binding(
    parent_fd: int,
    public_name: str,
    private_name: str,
    held_directory_fd: int,
) -> None:
    entry = os.stat(
        public_name, dir_fd=parent_fd, follow_symlinks=False
    )
    if (
        not stat.S_ISLNK(entry.st_mode)
        or os.readlink(public_name, dir_fd=parent_fd) != private_name
    ):
        raise AdjudicatedPolicyFreezeError(
            "published policy symlink changed"
        )
    published_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    published_fd = os.open(
        public_name, published_flags, dir_fd=parent_fd
    )
    try:
        published = os.fstat(published_fd)
        held = os.fstat(held_directory_fd)
        if (published.st_dev, published.st_ino) != (
            held.st_dev,
            held.st_ino,
        ):
            raise AdjudicatedPolicyFreezeError(
                "published policy directory differs from held directory"
            )
    finally:
        os.close(published_fd)


def _reserve_private_policy_directory(parent_fd: int) -> str:
    for _attempt in range(64):
        name = f".policies.store-{secrets.token_hex(16)}"
        try:
            os.mkdir(name, 0o700, dir_fd=parent_fd)
        except FileExistsError:
            continue
        return name
    raise AdjudicatedPolicyFreezeError(
        "cannot reserve a private random policy directory"
    )


def _write_policy_file_at(
    directory_fd: int,
    filename: str,
    payload: bytes,
    flags: int,
) -> tuple[int, dict[str, int], str]:
    descriptor = os.open(
        filename, flags, 0o600, dir_fd=directory_fd
    )
    try:
        _write_all(descriptor, payload)
        os.fsync(descriptor)
        os.fchmod(descriptor, 0o444)
        os.fsync(descriptor)
        verified = _read_policy_fd(descriptor)
        if verified != payload:
            raise AdjudicatedPolicyFreezeError(
                f"policy artifact bytes changed before commit: {filename}"
            )
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o222:
            raise AdjudicatedPolicyFreezeError(
                f"policy artifact is not immutable regular data: {filename}"
            )
        return (
            descriptor,
            {"device": metadata.st_dev, "inode": metadata.st_ino},
            hashlib.sha256(verified).hexdigest(),
        )
    except BaseException:
        os.close(descriptor)
        raise


def validate_published_policy_bundle(
    policies: Path,
    expected_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Open one public bundle and validate manifest, inodes, and hashes."""
    parent_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        parent_flags |= os.O_NOFOLLOW
    parent_fd = os.open(policies.parent, parent_flags)
    directory_fd: int | None = None
    try:
        entry = os.stat(
            policies.name, dir_fd=parent_fd, follow_symlinks=False
        )
        if not stat.S_ISLNK(entry.st_mode):
            raise AdjudicatedPolicyFreezeError(
                "published policies entry is not a symlink"
            )
        private_name = os.readlink(policies.name, dir_fd=parent_fd)
        if re.fullmatch(r"\.policies\.store-[0-9a-f]{32}", private_name) is None:
            raise AdjudicatedPolicyFreezeError(
                "published policies target is not a private relative store"
            )
        directory_fd = os.open(
            policies.name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC,
            dir_fd=parent_fd,
        )
        directory_stat = os.fstat(directory_fd)
        if (
            expected_manifest.get("directory_identity")
            != {
                "device": directory_stat.st_dev,
                "inode": directory_stat.st_ino,
            }
        ):
            raise AdjudicatedPolicyFreezeError(
                "published policies directory identity changed"
            )
        file_flags = os.O_RDONLY | os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            file_flags |= os.O_NOFOLLOW

        def read_named(filename: str) -> tuple[bytes, os.stat_result]:
            try:
                descriptor = os.open(
                    filename, file_flags, dir_fd=directory_fd
                )
            except OSError as exc:
                raise AdjudicatedPolicyFreezeError(
                    f"published policy artifact is unavailable: {filename}"
                ) from exc
            try:
                return _read_policy_fd(descriptor), os.fstat(descriptor)
            finally:
                os.close(descriptor)

        manifest_payload, manifest_stat = read_named("manifest.json")
        if not stat.S_ISREG(manifest_stat.st_mode) or manifest_stat.st_mode & 0o222:
            raise AdjudicatedPolicyFreezeError(
                "published policy manifest is not read-only regular data"
            )
        try:
            manifest = json.loads(manifest_payload)
        except json.JSONDecodeError as exc:
            raise AdjudicatedPolicyFreezeError(
                "published policy manifest is malformed"
            ) from exc
        if manifest != expected_manifest:
            raise AdjudicatedPolicyFreezeError(
                "published policy manifest differs from expected contract binding"
            )
        rows = manifest.get("policies")
        if not isinstance(rows, dict) or set(rows) != set(POLICY_FILES):
            raise AdjudicatedPolicyFreezeError(
                "published policy manifest arm set changed"
            )
        for arm, filename in POLICY_FILES.items():
            row = rows[arm]
            payload, metadata = read_named(filename)
            if (
                row.get("file") != filename
                or row.get("file_identity")
                != {"device": metadata.st_dev, "inode": metadata.st_ino}
                or row.get("policy_sha256")
                != hashlib.sha256(payload).hexdigest()
                or not stat.S_ISREG(metadata.st_mode)
                or metadata.st_mode & 0o222
            ):
                raise AdjudicatedPolicyFreezeError(
                    f"published policy binding changed: {arm}"
                )
        return manifest
    finally:
        if directory_fd is not None:
            os.close(directory_fd)
        os.close(parent_fd)


def write_policy_artifacts_exclusive(
    selected: dict[str, dict[str, Any]],
    bindings: dict[str, Any],
) -> dict[str, Any]:
    """Build by held dirfd, then atomically publish one relative symlink."""
    parent_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    file_flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        parent_flags |= os.O_NOFOLLOW
        directory_flags |= os.O_NOFOLLOW
        file_flags |= os.O_NOFOLLOW
    parent_fd = os.open(POLICIES.parent, parent_flags)
    directory_fd: int | None = None
    file_descriptors: dict[str, int] = {}
    try:
        _assert_directory_path_binding(POLICIES.parent, parent_fd)
        if _entry_exists_at(parent_fd, POLICIES.name):
            raise AdjudicatedPolicyFreezeError(
                "refusing to overwrite analyst/policies"
            )
        private_name = _reserve_private_policy_directory(parent_fd)
        directory_fd = os.open(
            private_name, directory_flags, dir_fd=parent_fd
        )
        reserved = os.fstat(directory_fd)
        if not stat.S_ISDIR(reserved.st_mode):
            raise AdjudicatedPolicyFreezeError(
                "reserved policy output is not a directory"
            )
        rows = {}
        for arm, filename in POLICY_FILES.items():
            policy = selected[arm]["policy_text"]
            payload = policy.encode("utf-8")
            descriptor, identity, policy_sha256 = _write_policy_file_at(
                directory_fd,
                filename,
                payload,
                file_flags,
            )
            file_descriptors[filename] = descriptor
            rows[arm] = {
                **{
                    key: value
                    for key, value in selected[arm].items()
                    if key != "policy_text"
                },
                "file": filename,
                "policy_sha256": policy_sha256,
                "file_identity": identity,
            }
        manifest = {
            "schema": "agentsight.utility2.rank1-policy-freeze.v8",
            "status": "PASS",
            "no_substitution": True,
            "atomic_final_symlink_publication": True,
            "manifest_committed_last": True,
            "publication_protocol": (
                "held-parent-dirfd/private-random-directory/"
                "held-staging-dirfd/openat-O_EXCL/manifest-last/"
                "relative-symlinkat-no-replace"
            ),
            "concurrent_public_path_replacement_fails_closed": True,
            "publication_linearization_point": (
                "final public symlink target and live-open directory inode "
                "check after all manifest and file-FD validation"
            ),
            "consumer_revalidation_required": True,
            "threat_boundary": (
                "protects against accidental or concurrent pathname "
                "replacement through the publication linearization point; "
                "later mutation is post-publication and must be caught by "
                "consumer manifest/inode/hash revalidation; does not claim "
                "resistance to persistent same-UID malicious alteration"
            ),
            "directory_identity": {
                "device": reserved.st_dev,
                "inode": reserved.st_ino,
            },
            "policies": rows,
            "bindings": bindings,
        }
        manifest_payload = (
            json.dumps(
                manifest,
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        manifest_fd, _manifest_identity, manifest_sha256 = (
            _write_policy_file_at(
                directory_fd,
                "manifest.json",
                manifest_payload,
                file_flags,
            )
        )
        file_descriptors["manifest.json"] = manifest_fd

        os.fchmod(directory_fd, 0o555)
        os.fsync(directory_fd)
        os.fsync(parent_fd)
        _assert_directory_entry_matches_fd(
            parent_fd, private_name, directory_fd
        )
        try:
            os.symlink(
                private_name,
                POLICIES.name,
                dir_fd=parent_fd,
            )
        except FileExistsError as exc:
            raise AdjudicatedPolicyFreezeError(
                "refusing to overwrite analyst/policies"
            ) from exc
        os.fsync(parent_fd)
        _assert_public_policy_binding(
            parent_fd, POLICIES.name, private_name, directory_fd
        )
        _assert_directory_entry_matches_fd(
            parent_fd, private_name, directory_fd
        )
        _assert_directory_path_binding(POLICIES.parent, parent_fd)
        expected_payloads = {
            filename: selected[arm]["policy_text"].encode("utf-8")
            for arm, filename in POLICY_FILES.items()
        }
        expected_payloads["manifest.json"] = manifest_payload
        for filename, expected_payload in expected_payloads.items():
            descriptor = file_descriptors[filename]
            current = _read_policy_fd(descriptor)
            if (
                current != expected_payload
                or hashlib.sha256(current).hexdigest()
                != (
                    manifest_sha256
                    if filename == "manifest.json"
                    else next(
                        row["policy_sha256"]
                        for row in rows.values()
                        if row["file"] == filename
                    )
                )
                or os.fstat(descriptor).st_mode & 0o222
            ):
                raise AdjudicatedPolicyFreezeError(
                    f"committed policy artifact changed: {filename}"
                )
        if json.loads(_read_policy_fd(manifest_fd)) != manifest:
            raise AdjudicatedPolicyFreezeError(
                "manifest bytes do not parse to committed manifest"
            )
        validate_published_policy_bundle(POLICIES, manifest)
        _assert_directory_entry_matches_fd(
            parent_fd, private_name, directory_fd
        )
        _assert_directory_path_binding(POLICIES.parent, parent_fd)
        # Publication linearizes here. Any later path mutation is
        # post-publication and must be caught by consumer revalidation.
        _assert_public_policy_binding(
            parent_fd, POLICIES.name, private_name, directory_fd
        )
        return manifest
    finally:
        for descriptor in reversed(list(file_descriptors.values())):
            os.close(descriptor)
        if directory_fd is not None:
            os.close(directory_fd)
        os.close(parent_fd)


def execute(
    contract_path: Path,
    expected_contract_sha256: str,
    analysis_path: Path,
) -> dict[str, Any]:
    if (
        sys.flags.isolated != 1
        or sys.flags.no_site != 1
        or not sys.flags.safe_path
    ):
        raise AdjudicatedPolicyFreezeError(
            "policy execution requires Python -I -S safe-path mode"
        )
    if contract_path.resolve() != CONTRACT.resolve() or analysis_path.resolve() != ANALYSIS.resolve():
        raise AdjudicatedPolicyFreezeError(
            "policy-freeze inputs differ from frozen paths"
        )
    contract = read_anchored_contract(
        contract_path, expected_contract_sha256
    )
    analysis_module = load_contract_module(
        contract,
        "run_adjudicated_analysis.py",
        "_snapshot_run_adjudicated_analysis",
    )
    verifier = analysis_module.load_verified_verifier(contract)
    sealed_payloads: list[Any] = []
    try:
        verification = verifier.verify_contract(
            contract_path, None, expected_contract_sha256
        )
        if verification["contract_document"] != contract:
            raise AdjudicatedPolicyFreezeError(
                "verified contract document changed"
            )
        registered_payload = read_regular_file_once(analysis_path)
        registered_hash = hashlib.sha256(registered_payload).hexdigest()
        registered_blob = analysis_module.SealedPayload(
            registered_payload,
            registered_hash,
            "registered-analysis.json",
        )
        sealed_payloads.append(registered_blob)
        try:
            registered = json.loads(registered_blob.read())
        except json.JSONDecodeError as exc:
            raise AdjudicatedPolicyFreezeError(
                "registered analysis is missing or malformed"
            ) from exc
        recomputed = analysis_module.compute_adjudicated_analysis(
            contract
        )
        assert_analysis_admission(registered, recomputed)
        selected = rank1_policy_sources(
            contract, analysis_module, sealed_payloads
        )
        for payload in sealed_payloads:
            payload.verify_sealed()
        selected_gate = registered["rank_1_policy_gate"]["selected_runs"]
        if any(
            selected_gate.get(arm, {}).get("run_id")
            != selected[arm]["run_id"]
            or selected_gate.get(arm, {}).get("valid") is not True
            for arm in POLICY_FILES
        ):
            raise AdjudicatedPolicyFreezeError(
                "rank-1 selection differs from frozen schedule or gate"
            )
        bindings = {
            "postreview_contract": {
                "path": str(contract_path.resolve()),
                "sha256": expected_contract_sha256,
                "external_trust_anchor_checked": True,
                "verified_file_count": verification["total_file_count"],
            },
            "adjudication": {
                "report_sha256": contract_file_hash(
                    contract,
                    "postreview-adjudication/adjudication/report.json",
                ),
                "corrected_provenance_sha256": (
                    contract_file_hash(
                        contract,
                        (
                            "postreview-adjudication/adjudication/"
                            "corrected-provenance.json"
                        ),
                    )
                ),
                "decisions_reused": True,
                "reviewer_model_rerun": False,
            },
            "analysis": {
                "path": str(analysis_path.resolve()),
                "sha256": registered_hash,
                "snapshot_sha256": registered_hash,
                "consumed_from_fully_sealed_memfd": True,
                "live_source_not_reopened_after_registration": True,
                "fresh_snapshot_recomputation_equal": True,
                "confirmatory_gate_pass": True,
                "rank_1_policy_gate_pass": True,
            },
            "rank1_sources": {
                "consumed_from_contract_verified_sealed_memfds": True,
                "all_seals_reverified_after_selection": True,
                "no_substitution": True,
            },
        }
        verifier.verify_contract(
            contract_path, None, expected_contract_sha256
        )
        for payload in sealed_payloads:
            payload.verify_sealed()
        return write_policy_artifacts_exclusive(selected, bindings)
    finally:
        for payload in reversed(sealed_payloads):
            payload.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare-launch", action="store_true")
    actions.add_argument("--execute", action="store_true")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--expected-contract-sha256")
    parser.add_argument("--expected-bootstrap-sha256")
    parser.add_argument("--expected-script-sha256")
    parser.add_argument("--expected-interpreter-sha256")
    parser.add_argument("--analysis", type=Path)
    args = parser.parse_args()
    if args.prepare_launch:
        if (
            args.expected_contract_sha256 is None
            or args.expected_bootstrap_sha256 is None
            or args.expected_script_sha256 is None
            or args.expected_interpreter_sha256 is None
        ):
            raise SystemExit(
                "--prepare-launch requires contract, bootstrap, and script SHAs"
            )
        print(
            json.dumps(
                prepare_launch(
                    args.expected_contract_sha256,
                    args.expected_bootstrap_sha256,
                    args.expected_script_sha256,
                    args.expected_interpreter_sha256,
                ),
                sort_keys=True,
            )
        )
        return 0
    if (
        args.contract is None
        or args.expected_contract_sha256 is None
        or args.analysis is None
    ):
        raise SystemExit(
            "--execute requires contract, expected contract SHA, and analysis"
        )
    manifest = execute(
        args.contract, args.expected_contract_sha256, args.analysis
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "no_substitution": manifest["no_substitution"],
                "policy_count": len(manifest["policies"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
