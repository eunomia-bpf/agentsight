#!/usr/bin/env python3
"""Execute one contract-bound wrapper from verified in-memory bytes."""

from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any


ALLOWED_SCRIPTS = {
    "verify_postreview_adjudication_contract.py",
    "run_adjudicated_analysis.py",
    "freeze_adjudicated_rank1_policies.py",
}
SHA256_LENGTH = 64
REQUIRED_SEALS = (
    fcntl.F_SEAL_WRITE
    | fcntl.F_SEAL_GROW
    | fcntl.F_SEAL_SHRINK
    | fcntl.F_SEAL_SEAL
)


class BootstrapError(RuntimeError):
    """Raised when an external anchor or contract binding differs."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_stable_bytes(path: Path, label: str) -> bytes:
    payload = path.read_bytes()
    if path.read_bytes() != payload:
        raise BootstrapError(f"{label} changed while being read")
    return payload


def read_regular_file_once(path: Path, label: str) -> bytes:
    flags = os.O_RDONLY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise BootstrapError(f"{label} is not a regular file")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def require_isolated_runtime() -> None:
    if (
        sys.flags.isolated != 1
        or sys.flags.no_site != 1
        or not sys.flags.safe_path
    ):
        raise BootstrapError(
            "bootstrap requires Python -I -S isolated safe-path mode"
        )


def require_sha256(value: str, label: str) -> None:
    if len(value) != SHA256_LENGTH or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise BootstrapError(f"{label} is not a lowercase SHA-256")


def load_contract(
    path: Path, expected_sha256: str
) -> tuple[bytes, dict[str, Any]]:
    payload = read_stable_bytes(path, "contract")
    if sha256_bytes(payload) != expected_sha256:
        raise BootstrapError("external contract SHA anchor mismatch")
    try:
        document = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise BootstrapError("contract is not valid JSON") from exc
    if (
        not isinstance(document, dict)
        or document.get("schema")
        != "agentsight.utility2.postreview-adjudication-contract.v8"
        or document.get("stage")
        != "postreview-adjudication-attempt-8-pre-analysis"
    ):
        raise BootstrapError("contract identity changed")
    return payload, document


def verified_script_bytes(
    experiment: Path,
    contract: dict[str, Any],
    script_relative: str,
    expected_script_sha256: str,
) -> bytes:
    if script_relative not in ALLOWED_SCRIPTS:
        raise BootstrapError("script is outside the bootstrap allowlist")
    registered = contract.get("postreview_static_files")
    if (
        not isinstance(registered, dict)
        or registered.get(script_relative) != expected_script_sha256
    ):
        raise BootstrapError("script hash is not contract-bound")
    path = experiment / script_relative
    payload = read_stable_bytes(path, "wrapper script")
    if sha256_bytes(payload) != expected_script_sha256:
        raise BootstrapError("wrapper script SHA mismatch")
    return payload


def sealed_memfd(payload: bytes) -> int:
    descriptor = os.memfd_create(
        "agentsight-postreview-wrapper",
        flags=os.MFD_ALLOW_SEALING,
    )
    try:
        written = 0
        while written < len(payload):
            count = os.write(descriptor, payload[written:])
            if count <= 0:
                raise BootstrapError("cannot populate wrapper memfd")
            written += count
        fcntl.fcntl(descriptor, fcntl.F_ADD_SEALS, REQUIRED_SEALS)
        seals = fcntl.fcntl(descriptor, fcntl.F_GET_SEALS)
        if seals & REQUIRED_SEALS != REQUIRED_SEALS:
            raise BootstrapError("wrapper memfd is not fully sealed")
        if os.pread(descriptor, len(payload) + 1, 0) != payload:
            raise BootstrapError("sealed wrapper bytes changed")
        try:
            os.pwrite(descriptor, b"x", 0)
        except OSError as exc:
            if exc.errno not in {errno.EPERM, errno.EBADF}:
                raise
        else:
            raise BootstrapError("sealed wrapper remains writable")
        os.set_inheritable(descriptor, True)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def execute_verified(
    *,
    contract_path: Path,
    expected_contract_sha256: str,
    script_relative: str,
    expected_script_sha256: str,
    expected_bootstrap_sha256: str,
    expected_interpreter_sha256: str,
    script_args: list[str],
) -> None:
    require_isolated_runtime()
    for value, label in (
        (expected_contract_sha256, "contract SHA"),
        (expected_script_sha256, "script SHA"),
        (expected_bootstrap_sha256, "bootstrap SHA"),
        (expected_interpreter_sha256, "interpreter SHA"),
    ):
        require_sha256(value, label)
    bootstrap_path = Path(__file__).resolve()
    bootstrap_payload = read_stable_bytes(bootstrap_path, "bootstrap")
    if sha256_bytes(bootstrap_payload) != expected_bootstrap_sha256:
        raise BootstrapError("external bootstrap SHA anchor mismatch")
    contract_payload, contract = load_contract(
        contract_path, expected_contract_sha256
    )
    experiment = contract_path.resolve().parent.parent
    if contract.get("experiment") != str(experiment):
        raise BootstrapError("contract experiment path changed")
    registered = contract.get("postreview_static_files", {})
    if registered.get("postreview_bootstrap.py") != expected_bootstrap_sha256:
        raise BootstrapError("bootstrap hash is not contract-bound")
    runtime = contract.get("trusted_runtime")
    interpreter = Path(sys.executable).resolve()
    if (
        not isinstance(runtime, dict)
        or runtime.get("interpreter_path") != str(interpreter)
        or runtime.get("interpreter_sha256")
        != expected_interpreter_sha256
        or runtime.get("isolated_flag") is not True
        or runtime.get("no_site_flag") is not True
        or runtime.get("safe_path_flag") is not True
        or sha256_bytes(
            read_regular_file_once(interpreter, "Python interpreter")
        )
        != expected_interpreter_sha256
    ):
        raise BootstrapError("trusted isolated Python runtime changed")
    script_payload = verified_script_bytes(
        experiment,
        contract,
        script_relative,
        expected_script_sha256,
    )
    descriptor = sealed_memfd(script_payload)
    try:
        if (
            read_stable_bytes(contract_path, "contract") != contract_payload
            or read_stable_bytes(bootstrap_path, "bootstrap")
            != bootstrap_payload
        ):
            raise BootstrapError("trust anchor changed before execution")
        environment = {
            "AGENTSIGHT_EXPERIMENT_ROOT": str(experiment),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
        }
        snapshot_path = f"/proc/self/fd/{descriptor}"
        os.execve(
            str(interpreter),
            [
                str(interpreter),
                "-I",
                "-S",
                snapshot_path,
                *script_args,
            ],
            environment,
        )
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--expected-contract-sha256", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--expected-script-sha256", required=True)
    parser.add_argument("--expected-bootstrap-sha256", required=True)
    parser.add_argument("--expected-interpreter-sha256", required=True)
    parser.add_argument("script_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    script_args = list(args.script_args)
    if script_args[:1] == ["--"]:
        script_args = script_args[1:]
    execute_verified(
        contract_path=args.contract,
        expected_contract_sha256=args.expected_contract_sha256,
        script_relative=args.script,
        expected_script_sha256=args.expected_script_sha256,
        expected_bootstrap_sha256=args.expected_bootstrap_sha256,
        expected_interpreter_sha256=args.expected_interpreter_sha256,
        script_args=script_args,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
