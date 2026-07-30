#!/usr/bin/env python3
"""Run the frozen analyzer from a contract-verified immutable snapshot."""

from __future__ import annotations

import argparse
import ctypes
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
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
LAUNCH_COMMAND = POST / "analysis-launch-command.json"
OUTPUT = ANALYST / "analysis.json"
ORIGINAL_RUN = ANALYST / "review-run" / "run.json"
CORRECTED = POST / "adjudication" / "corrected-provenance.json"
REPORT = POST / "adjudication" / "report.json"
SCRIPT_RELATIVE = "run_adjudicated_analysis.py"
NUMPY_SHIM_RELATIVE = "frozen_numpy_shim.py"
BOOTSTRAP_INDICES_RELATIVE = (
    "bootstrap-indices-pcg64-seed2026072903-i8le.bin"
)
COMMAND_IDENTIFIER = "experiment-002-adjudicated-analysis-v8"
CORRECTION_TYPE = (
    "post-execution audit-classification correction; no reviewer/model rerun"
)


class AdjudicatedAnalysisError(RuntimeError):
    """Raised when the anchored snapshot analysis path is not exact."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
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
        "--output",
        str(OUTPUT.resolve()),
    ]


def prepare_launch(
    expected_contract_sha256: str,
    expected_bootstrap_sha256: str,
    expected_script_sha256: str,
    expected_interpreter_sha256: str,
) -> dict[str, Any]:
    if LAUNCH_COMMAND.exists() or OUTPUT.exists():
        raise AdjudicatedAnalysisError(
            "refusing to overwrite launch command or existing analysis"
        )
    if sha256_file(CONTRACT) != expected_contract_sha256:
        raise AdjudicatedAnalysisError("launch contract SHA is not current")
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
        raise AdjudicatedAnalysisError(
            "launcher code hashes differ from contract/external anchors"
        )
    dump_json(
        LAUNCH_COMMAND,
        {
            "schema": "agentsight.utility2.adjudicated-analysis-launch.v8",
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
        raise AdjudicatedAnalysisError(
            f"snapshot input is not uniquely contract-bound: {relative}"
        )
    return matches[0]


REQUIRED_SEALS = (
    fcntl.F_SEAL_WRITE
    | fcntl.F_SEAL_GROW
    | fcntl.F_SEAL_SHRINK
    | fcntl.F_SEAL_SEAL
)


def read_regular_file_once(path: Path) -> bytes:
    flags = os.O_RDONLY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise AdjudicatedAnalysisError(
                f"contract input is not a regular file: {path}"
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


class SealedPayload:
    """One immutable payload whose descriptor is the consumption boundary."""

    def __init__(self, payload: bytes, expected_sha256: str, label: str):
        actual = hashlib.sha256(payload).hexdigest()
        if actual != expected_sha256:
            raise AdjudicatedAnalysisError(
                f"contract payload hash mismatch: {label}"
            )
        self.expected_sha256 = expected_sha256
        self.label = label
        self.size = len(payload)
        self.descriptor = os.memfd_create(
            f"agentsight-{Path(label).name}",
            flags=os.MFD_ALLOW_SEALING,
        )
        try:
            written = 0
            while written < len(payload):
                count = os.write(self.descriptor, payload[written:])
                if count <= 0:
                    raise AdjudicatedAnalysisError(
                        f"cannot populate sealed payload: {label}"
                    )
                written += count
            fcntl.fcntl(
                self.descriptor, fcntl.F_ADD_SEALS, REQUIRED_SEALS
            )
            self.verify_sealed()
        except BaseException:
            os.close(self.descriptor)
            raise

    @classmethod
    def from_live(
        cls, path: Path, expected_sha256: str, label: str
    ) -> "SealedPayload":
        return cls(read_regular_file_once(path), expected_sha256, label)

    @property
    def fd_path(self) -> Path:
        return Path(f"/proc/self/fd/{self.descriptor}")

    def verify_sealed(self) -> None:
        seals = fcntl.fcntl(self.descriptor, fcntl.F_GET_SEALS)
        if seals & REQUIRED_SEALS != REQUIRED_SEALS:
            raise AdjudicatedAnalysisError(
                f"payload memfd is not fully sealed: {self.label}"
            )
        payload = os.pread(self.descriptor, self.size + 1, 0)
        if (
            len(payload) != self.size
            or hashlib.sha256(payload).hexdigest()
            != self.expected_sha256
        ):
            raise AdjudicatedAnalysisError(
                f"sealed payload bytes changed: {self.label}"
            )
        try:
            os.pwrite(self.descriptor, b"x", 0)
        except OSError as exc:
            if exc.errno not in {errno.EPERM, errno.EBADF}:
                raise
        else:
            raise AdjudicatedAnalysisError(
                f"sealed payload remains writable: {self.label}"
            )

    def read(self) -> bytes:
        self.verify_sealed()
        return os.pread(self.descriptor, self.size + 1, 0)

    def close(self) -> None:
        os.close(self.descriptor)


class SealedRegistry:
    """Map analyzer namespace paths to immutable contract-bound payloads."""

    def __init__(self, contract: dict[str, Any]):
        self.contract = contract
        self.by_path: dict[Path, SealedPayload] = {}
        self.payloads: list[SealedPayload] = []

    @staticmethod
    def _placeholder(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(
            path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o000
        )
        os.close(descriptor)

    def add_contract(self, relative: str, virtual: Path) -> SealedPayload:
        expected = contract_file_hash(self.contract, relative)
        payload = SealedPayload.from_live(
            EXPERIMENT / relative, expected, relative
        )
        self._placeholder(virtual)
        self.by_path[virtual] = payload
        self.payloads.append(payload)
        return payload

    def add_generated(
        self, virtual: Path, payload_bytes: bytes, label: str
    ) -> SealedPayload:
        expected = hashlib.sha256(payload_bytes).hexdigest()
        payload = SealedPayload(payload_bytes, expected, label)
        self._placeholder(virtual)
        self.by_path[virtual] = payload
        self.payloads.append(payload)
        return payload

    def payload(self, path: Path) -> SealedPayload:
        normalized = Path(path)
        payload = self.by_path.get(normalized)
        if payload is None:
            raise AdjudicatedAnalysisError(
                f"analyzer requested an unregistered path: {path}"
            )
        return payload

    def json(self, path: Path) -> Any:
        try:
            return json.loads(self.payload(path).read())
        except json.JSONDecodeError as exc:
            raise AdjudicatedAnalysisError(
                f"sealed JSON is malformed: {path}"
            ) from exc

    def sha256(self, path: Path) -> str:
        payload = self.payload(path)
        payload.verify_sealed()
        return payload.expected_sha256

    def verify_all(self) -> None:
        for payload in self.payloads:
            payload.verify_sealed()

    def close(self) -> None:
        for payload in reversed(self.payloads):
            payload.close()
        self.payloads.clear()
        self.by_path.clear()


def validate_corrected_provenance(
    original: dict[str, Any], corrected: dict[str, Any]
) -> None:
    if set(corrected) != set(original):
        raise AdjudicatedAnalysisError(
            "corrected provenance field set changed"
        )
    for field in original:
        expected = (
            "ok"
            if field == "status"
            else []
            if field == "validation_errors"
            else original[field]
        )
        if corrected[field] != expected:
            raise AdjudicatedAnalysisError(
                f"corrected provenance changed forbidden field: {field}"
            )


def load_verified_module(
    payload: SealedPayload, module_name: str, source_name: str
) -> Any:
    source = payload.read()
    module = types.ModuleType(module_name)
    module.__file__ = source_name
    exec(compile(source, source_name, "exec"), module.__dict__)
    payload.verify_sealed()
    return module


def read_anchored_contract(path: Path, expected_sha256: str) -> dict[str, Any]:
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise AdjudicatedAnalysisError("external contract SHA anchor mismatch")
    document = json.loads(payload)
    if path.read_bytes() != payload:
        raise AdjudicatedAnalysisError(
            "contract changed after anchored byte parsing"
        )
    return document


def load_verified_verifier(contract: dict[str, Any]) -> Any:
    relative = "verify_postreview_adjudication_contract.py"
    payload = SealedPayload.from_live(
        EXPERIMENT / relative,
        contract_file_hash(contract, relative),
        relative,
    )
    try:
        return load_verified_module(
            payload,
            "_snapshot_verify_postreview_contract",
            relative,
        )
    finally:
        payload.close()


def build_analysis_snapshot(
    contract: dict[str, Any], root: Path
) -> tuple[
    Path,
    SealedRegistry,
    Path,
    SealedPayload,
    SealedPayload,
    SealedPayload,
]:
    snapshot_analyst = root / "analyst"
    registry = SealedRegistry(contract)
    direct = (
        "analyst/order.json",
        "analyst/review-alias-map.private.json",
        "analyst/review-run/decisions.json",
        "analyst/review-prompt.txt",
        "analyst/review-model-contract.json",
        "analyst/review-command.json",
        "analyst/review-bundle/manifest.json",
    )
    for relative in direct:
        registry.add_contract(relative, root / relative)
    run_relatives = sorted(
        relative
        for relative in contract["original_runtime_files"]
        if relative.startswith("analyst/runs/")
        and relative.endswith("/run.json")
    )
    if len(run_relatives) != 40:
        raise AdjudicatedAnalysisError(
            "contract does not bind exactly 40 analyst run records"
        )
    for relative in run_relatives:
        registry.add_contract(relative, root / relative)
    analyzer_copy = root / "code" / "analyze_analyst_efficiency.py"
    analyzer_payload = registry.add_contract(
        "analyze_analyst_efficiency.py",
        analyzer_copy,
    )
    numpy_shim_payload = registry.add_contract(
        NUMPY_SHIM_RELATIVE,
        root / "code" / NUMPY_SHIM_RELATIVE,
    )
    bootstrap_indices_payload = registry.add_contract(
        BOOTSTRAP_INDICES_RELATIVE,
        root / "code" / BOOTSTRAP_INDICES_RELATIVE,
    )

    corrected_relative = (
        "postreview-adjudication/adjudication/corrected-provenance.json"
    )
    corrected_copy = (
        root / "adjudication" / "corrected-provenance.json"
    )
    registry.add_contract(corrected_relative, corrected_copy)
    original_copy = root / "source-review-run" / "run.json"
    registry.add_contract(
        "analyst/review-run/run.json",
        original_copy,
    )
    registry.add_contract(
        "postreview-adjudication/adjudication/report.json",
        root / "adjudication" / "report.json",
    )
    corrected = registry.json(corrected_copy)
    original = registry.json(original_copy)
    validate_corrected_provenance(original, corrected)
    projected = dict(corrected)
    projected["decisions_path"] = str(
        (
            snapshot_analyst / "review-run" / "decisions.json"
        ).resolve(strict=True)
    )
    projected_path = snapshot_analyst / "review-run" / "run.json"
    projected_bytes = (
        json.dumps(
            projected,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    registry.add_generated(
        projected_path, projected_bytes, "projected-review-provenance"
    )
    registry.verify_all()
    return (
        snapshot_analyst,
        registry,
        projected_path,
        analyzer_payload,
        numpy_shim_payload,
        bootstrap_indices_payload,
    )


def _normalize_projection_paths(
    result: dict[str, Any],
    projection_analyst: Path,
    projected_provenance: Path,
    contract: dict[str, Any],
) -> dict[str, Any]:
    provenance = result["input_provenance"]["review_provenance"]
    if Path(provenance["path"]) != projected_provenance:
        raise AdjudicatedAnalysisError(
            "analyzer returned an unexpected projected provenance path"
        )
    provenance["path"] = str(CORRECTED.resolve())
    provenance["sha256"] = contract_file_hash(
        contract,
        "postreview-adjudication/adjudication/corrected-provenance.json",
    )
    projected_decisions = (
        projection_analyst / "review-run" / "decisions.json"
    )
    if Path(provenance["decisions_path"]) != projected_decisions:
        raise AdjudicatedAnalysisError(
            "analyzer returned an unexpected projected decisions path"
        )
    provenance["decisions_path"] = str(
        (ANALYST / "review-run" / "decisions.json").resolve()
    )
    frozen = provenance["frozen_artifacts"]
    replacements = {
        "review_prompt": (
            ANALYST / "review-prompt.txt",
            "analyst/review-prompt.txt",
        ),
        "review_model_contract": (
            ANALYST / "review-model-contract.json",
            "analyst/review-model-contract.json",
        ),
        "review_command": (
            ANALYST / "review-command.json",
            "analyst/review-command.json",
        ),
        "review_bundle_manifest": (
            ANALYST / "review-bundle" / "manifest.json",
            "analyst/review-bundle/manifest.json",
        ),
    }
    for name, (source, relative) in replacements.items():
        projected = projection_analyst / (
            "review-bundle/manifest.json"
            if name == "review_bundle_manifest"
            else source.name
        )
        if Path(frozen[name]["path"]) != projected:
            raise AdjudicatedAnalysisError(
                f"unexpected projected analyzer path for {name}"
            )
        frozen[name]["path"] = str(source.resolve())
        registered = contract_file_hash(contract, relative)
        if name == "review_bundle_manifest":
            frozen[name]["sha256_before"] = registered
            frozen[name]["sha256_after"] = registered
            frozen[name]["sha256_current"] = registered
        else:
            frozen[name]["sha256"] = registered
    provenance["decisions_sha256"] = contract_file_hash(
        contract, "analyst/review-run/decisions.json"
    )
    top = result["input_provenance"]
    expected_paths = {
        "schedule": (
            ANALYST / "order.json",
            "analyst/order.json",
        ),
        "validity_review": (
            ANALYST / "review-run" / "decisions.json",
            "analyst/review-run/decisions.json",
        ),
        "alias_map": (
            ANALYST / "review-alias-map.private.json",
            "analyst/review-alias-map.private.json",
        ),
    }
    for name, (source, relative) in expected_paths.items():
        if not Path(top[name]["path"]).is_relative_to(projection_analyst):
            raise AdjudicatedAnalysisError(
                f"analyzer {name} did not come from the snapshot"
            )
        top[name]["path"] = str(source.resolve())
        top[name]["sha256"] = contract_file_hash(contract, relative)
    run_hashes = {
        run_id: contract_file_hash(
            contract, f"analyst/runs/{run_id}/run.json"
        )
        for run_id in top["run_record_sha256_by_run_id"]
    }
    top["run_record_sha256_by_run_id"] = run_hashes

    def normalize_nested_run_hashes(value: Any) -> None:
        if isinstance(value, dict):
            run_id = value.get("run_id")
            if (
                "run_record_sha256" in value
                and isinstance(run_id, str)
                and run_id in run_hashes
            ):
                value["run_record_sha256"] = run_hashes[run_id]
            for nested in value.values():
                normalize_nested_run_hashes(nested)
        elif isinstance(value, list):
            for nested in value:
                normalize_nested_run_hashes(nested)

    normalize_nested_run_hashes(result)
    result["postreview_adjudication"] = {
        "schema": "agentsight.utility2.analysis-adjudication-binding.v8",
        "correction_type": CORRECTION_TYPE,
        "reviewer_model_rerun": False,
        "decisions_reused": True,
        "projection_changed_only_decisions_path": True,
        "report": {
            "path": str(REPORT.resolve()),
            "sha256": contract_file_hash(
                contract,
                "postreview-adjudication/adjudication/report.json",
            ),
        },
        "corrected_provenance": {
            "path": str(CORRECTED.resolve()),
            "sha256": contract_file_hash(
                contract,
                (
                    "postreview-adjudication/adjudication/"
                    "corrected-provenance.json"
                ),
            ),
        },
        "original_failed_provenance": {
            "path": str(ORIGINAL_RUN.resolve()),
            "sha256": contract_file_hash(
                contract, "analyst/review-run/run.json"
            ),
        },
        "all_analysis_inputs_consumed_from_verified_snapshot": True,
        "all_input_hashes_normalized_from_contract": True,
        "sealed_memfd_consumption": True,
        "no_live_input_path_reopens": True,
        "all_seals_reverified_after_analysis": True,
        "numpy_runtime": {
            "implementation": "contract-bound pure-stdlib frozen subset",
            "shim_sha256": contract_file_hash(
                contract, NUMPY_SHIM_RELATIVE
            ),
            "bootstrap_indices_sha256": contract_file_hash(
                contract, BOOTSTRAP_INDICES_RELATIVE
            ),
            "bootstrap_seed": 2026072903,
            "bootstrap_shape": [100_000, 20],
            "live_numpy_imported": False,
        },
    }
    return result


def compute_adjudicated_analysis(
    contract: dict[str, Any]
) -> dict[str, Any]:
    """Consume every analyzer input exclusively through sealed memfds."""
    with tempfile.TemporaryDirectory(
        prefix=".adjudicated-analysis-snapshot-", dir=POST
    ) as directory:
        root = Path(directory)
        (
            snapshot,
            registry,
            projected,
            analyzer_payload,
            numpy_shim_payload,
            bootstrap_indices_payload,
        ) = build_analysis_snapshot(contract, root)
        previous_numpy = sys.modules.get("numpy")
        try:
            numpy_shim = load_verified_module(
                numpy_shim_payload,
                "_snapshot_frozen_numpy_shim",
                NUMPY_SHIM_RELATIVE,
            )
            numpy_shim.configure_indices(bootstrap_indices_payload.read())
            sys.modules["numpy"] = numpy_shim
            try:
                analyzer = load_verified_module(
                    analyzer_payload,
                    "_snapshot_analyze_analyst_efficiency",
                    "analyze_analyst_efficiency.py",
                )
            except BaseException:
                if previous_numpy is None:
                    sys.modules.pop("numpy", None)
                else:
                    sys.modules["numpy"] = previous_numpy
                raise

            def sealed_load_json(path: Path) -> Any:
                try:
                    return registry.json(Path(path))
                except AdjudicatedAnalysisError as exc:
                    raise analyzer.AnalysisInputError(str(exc)) from exc

            def sealed_sha256(path: Path) -> str:
                try:
                    return registry.sha256(Path(path))
                except AdjudicatedAnalysisError as exc:
                    raise analyzer.AnalysisInputError(str(exc)) from exc

            analyzer._load_json = sealed_load_json
            analyzer._sha256 = sealed_sha256
            analyzer._required_sha256 = (
                lambda path, _field: sealed_sha256(Path(path))
            )
            result = analyzer.analyze(
                schedule_path=snapshot / "order.json",
                runs_root=snapshot / "runs",
                validity_review_path=(
                    snapshot / "review-run" / "decisions.json"
                ),
                alias_map_path=(
                    snapshot / "review-alias-map.private.json"
                ),
                review_provenance_path=projected,
            )
            registry.verify_all()
            return _normalize_projection_paths(
                result, snapshot, projected, contract
            )
        finally:
            if previous_numpy is None:
                sys.modules.pop("numpy", None)
            else:
                sys.modules["numpy"] = previous_numpy
            registry.close()


def _write_all(descriptor: int, payload: bytes) -> None:
    written = 0
    while written < len(payload):
        count = os.write(descriptor, payload[written:])
        if count <= 0:
            raise AdjudicatedAnalysisError("short write while publishing output")
        written += count


def _read_all_at(descriptor: int) -> bytes:
    size = os.fstat(descriptor).st_size
    payload = os.pread(descriptor, size + 1, 0)
    if len(payload) != size:
        raise AdjudicatedAnalysisError("published descriptor size changed")
    return payload


def _assert_directory_name_matches_fd(path: Path, descriptor: int) -> None:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    current = os.open(path, flags)
    try:
        held_stat = os.fstat(descriptor)
        current_stat = os.fstat(current)
        if (held_stat.st_dev, held_stat.st_ino) != (
            current_stat.st_dev,
            current_stat.st_ino,
        ):
            raise AdjudicatedAnalysisError(
                f"publication directory pathname changed: {path}"
            )
    finally:
        os.close(current)


def atomic_write_json_noreplace(path: Path, value: Any) -> str:
    """Commit JSON from an unnamed inode through one held directory fd."""
    if not hasattr(os, "O_TMPFILE"):
        raise AdjudicatedAnalysisError("Linux O_TMPFILE is required")
    payload = (
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    directory_fd = os.open(path.parent, directory_flags)
    unnamed_fd: int | None = None
    published_fd: int | None = None
    try:
        _assert_directory_name_matches_fd(path.parent, directory_fd)
        unnamed_fd = os.open(
            ".",
            os.O_RDWR | os.O_TMPFILE | os.O_CLOEXEC,
            0o600,
            dir_fd=directory_fd,
        )
        _write_all(unnamed_fd, payload)
        os.fsync(unnamed_fd)
        os.fchmod(unnamed_fd, 0o444)
        before = os.fstat(unnamed_fd)
        if not stat.S_ISREG(before.st_mode):
            raise AdjudicatedAnalysisError(
                "unnamed publication inode is not a regular file"
            )
        verified_payload = _read_all_at(unnamed_fd)
        if verified_payload != payload:
            raise AdjudicatedAnalysisError(
                "unnamed publication bytes changed before commit"
            )
        try:
            json.loads(verified_payload)
        except json.JSONDecodeError as exc:
            raise AdjudicatedAnalysisError(
                "unnamed publication JSON is malformed"
            ) from exc
        publication_sha256 = hashlib.sha256(verified_payload).hexdigest()

        libc = ctypes.CDLL(None, use_errno=True)
        linkat = libc.linkat
        linkat.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        linkat.restype = ctypes.c_int
        if linkat(
            unnamed_fd,
            b"",
            directory_fd,
            os.fsencode(path.name),
            0x1000,  # AT_EMPTY_PATH
        ) != 0:
            error = ctypes.get_errno()
            if error == errno.EEXIST:
                raise AdjudicatedAnalysisError(
                    f"refusing to overwrite output: {path}"
                )
            raise AdjudicatedAnalysisError(
                f"linkat(AT_EMPTY_PATH) failed with errno {error}"
            )
        os.fsync(directory_fd)

        published_flags = os.O_RDONLY | os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            published_flags |= os.O_NOFOLLOW
        published_fd = os.open(
            path.name, published_flags, dir_fd=directory_fd
        )
        after = os.fstat(published_fd)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise AdjudicatedAnalysisError(
                "published inode differs from verified unnamed inode"
            )
        if _read_all_at(published_fd) != verified_payload:
            raise AdjudicatedAnalysisError(
                "published bytes differ from verified unnamed bytes"
            )
        _assert_directory_name_matches_fd(path.parent, directory_fd)
        return publication_sha256
    finally:
        if published_fd is not None:
            os.close(published_fd)
        if unnamed_fd is not None:
            os.close(unnamed_fd)
        os.close(directory_fd)


def execute(
    contract_path: Path,
    expected_contract_sha256: str,
    output: Path,
) -> dict[str, Any]:
    if (
        sys.flags.isolated != 1
        or sys.flags.no_site != 1
        or not sys.flags.safe_path
    ):
        raise AdjudicatedAnalysisError(
            "analysis execution requires Python -I -S safe-path mode"
        )
    if contract_path.resolve() != CONTRACT.resolve() or output.resolve() != OUTPUT.resolve():
        raise AdjudicatedAnalysisError("analysis inputs differ from frozen paths")
    contract = read_anchored_contract(
        contract_path, expected_contract_sha256
    )
    with tempfile.TemporaryDirectory(
        prefix=".verified-verifier-", dir=POST
    ):
        verifier = load_verified_verifier(contract)
        verified = verifier.verify_contract(
            contract_path, None, expected_contract_sha256
        )
        if verified["contract_document"] != contract:
            raise AdjudicatedAnalysisError(
                "verified contract document changed"
            )
        result = compute_adjudicated_analysis(contract)
        verifier.verify_contract(
            contract_path, None, expected_contract_sha256
        )
        analysis_sha256 = atomic_write_json_noreplace(output, result)
    return {
        "status": "PASS",
        "analysis_sha256": analysis_sha256,
        "adjudication_bound": True,
        "snapshot_consumed": True,
        "published_from_unnamed_inode": True,
    }


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
    parser.add_argument("--output", type=Path)
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
        or args.output is None
    ):
        raise SystemExit(
            "--execute requires contract, expected contract SHA, and output"
        )
    print(
        json.dumps(
            execute(
                args.contract, args.expected_contract_sha256, args.output
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
