#!/usr/bin/env python3
"""Prepare and execute the additive pre-unblinding reviewer-audit adjudication."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from typing import Any


EXPERIMENT = Path(__file__).resolve().parent
ANALYST = EXPERIMENT / "analyst"
POST = EXPERIMENT / "postreview-adjudication"
ATTESTATION_JSON = POST / "pre-unblinding-attestation.json"
ATTESTATION_MD = POST / "pre-unblinding-attestation.md"
ALLOWLIST = POST / "reviewer-role-allowlist.json"
COMMAND = POST / "adjudication-command.json"
OUTPUT = POST / "adjudication"
REPORT = OUTPUT / "report.json"
CORRECTED = OUTPUT / "corrected-provenance.json"
ROLE_RECEIPTS = OUTPUT / "cited-command-role-receipts.json"

ORIGINAL_CONTRACT = EXPERIMENT / "frozen-contract-analyst.json"
ORIGINAL_CONTRACT_SHA256 = (
    "bf29f168183ff5776ee24c57ea3f926f1d2ab391abaa0052d9c19751cddbeca0"
)
ORIGINAL_RUN = ANALYST / "review-run" / "run.json"
EVENTS = ANALYST / "review-run" / "events.jsonl"
RECEIPTS = ANALYST / "review-run" / "event-receipts.jsonl"
DECISIONS = ANALYST / "review-run" / "decisions.json"
STDERR = ANALYST / "review-run" / "stderr.log"
BUNDLE = ANALYST / "review-bundle"
BUNDLE_MANIFEST = BUNDLE / "manifest.json"
PROMPT = ANALYST / "review-prompt.txt"
MODEL_CONTRACT = ANALYST / "review-model-contract.json"
REVIEW_COMMAND = ANALYST / "review-command.json"
BATCH_RECEIPT = ANALYST / "batch-run.json"

EXPECTED_OUTER_COUNT = 8
EXPECTED_CITED_COUNT = 103
EXPECTED_UNIQUE_CITED_COUNT = 79
EXPECTED_EVENT_TOPOLOGY = {
    "thread.started:-": 1,
    "turn.started:-": 1,
    "item.started:command_execution": 8,
    "item.completed:command_execution": 8,
    "item.completed:agent_message": 3,
    "turn.completed:-": 1,
}
EXPECTED_ERRORS = [
    f"tool call {index} used an absolute path" for index in range(8)
]
REVIEW_FIELDS = (
    "recurring_bad_vs_good_diagnosis_valid",
    "quantitative_support_valid",
    "executable_benchmark_agnostic_policy_at_most_60_words",
    "no_benchmark_specific_or_hidden_data_reference",
    "no_evidence_read_outside_assigned_package",
)
UNAVAILABLE_OUTPUT = {
    "schema": "agentsight.utility2.blind-output-unavailable.v1",
    "output_available": False,
    "terminal_without_final": True,
}
LOCKED_RG_PATTERN = (
    r"redact|outside|endpoint|http|mcp|web|browser|/home|\.\./|private|hidden"
)
CORRECTION_TYPE = (
    "post-execution audit-classification correction; no reviewer/model rerun"
)


class AdjudicationError(RuntimeError):
    """Raised when the narrow correction cannot be applied exactly."""


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


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise AdjudicationError(f"invalid required JSON: {path}") from exc


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AdjudicationError(f"invalid JSONL line {path}:{index}") from exc
        if not isinstance(row, dict):
            raise AdjudicationError(f"non-object JSONL line {path}:{index}")
        rows.append(row)
    return rows


def validate_output_document(document: Any) -> str:
    """Validate only the exact public shapes needed for command collection."""
    if document == UNAVAILABLE_OUTPUT:
        return "unavailable"
    if not isinstance(document, dict) or set(document) != {
        "diagnosis",
        "quantitative_evidence",
        "policy_text",
        "expected_mechanism",
    }:
        raise AdjudicationError("public analyst output shape changed")
    for field in ("diagnosis", "policy_text", "expected_mechanism"):
        if not isinstance(document[field], str) or not document[field]:
            raise AdjudicationError(
                f"public analyst output {field} is invalid"
            )
    evidence = document["quantitative_evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise AdjudicationError("public quantitative evidence is invalid")
    for item in evidence:
        if (
            not isinstance(item, dict)
            or set(item) != {"command", "finding"}
            or any(
                not isinstance(item[field], str) or not item[field]
                for field in ("command", "finding")
            )
        ):
            raise AdjudicationError("public evidence row shape changed")
    return "analyst-output"


def verify_public_bundle(
    bundle: Path, expected_case_ids: set[str]
) -> None:
    """Verify the exact manifest-declared public bundle without private data."""
    manifest_path = bundle / "manifest.json"
    manifest = load_json(manifest_path)
    cases = manifest.get("cases")
    root_files = manifest.get("files")
    if (
        bundle.stat().st_mode & 0o222
        or manifest_path.stat().st_mode & 0o222
        or not isinstance(cases, list)
        or len(cases) != 40
        or not isinstance(root_files, dict)
        or set(root_files) != {"review-output.schema.json"}
        or set(path.name for path in bundle.iterdir())
        != {"cases", "manifest.json", "review-output.schema.json"}
    ):
        raise AdjudicationError("public review bundle root changed")
    case_ids = [row.get("case_id") for row in cases]
    if len(set(case_ids)) != 40 or set(case_ids) != expected_case_ids:
        raise AdjudicationError("public review bundle case set changed")
    for relative, expected in root_files.items():
        path = bundle / relative
        if (
            not path.is_file()
            or path.is_symlink()
            or sha256_file(path) != expected
            or path.stat().st_mode & 0o222
        ):
            raise AdjudicationError("public review root file changed")
    for row in cases:
        if set(row) != {"case_id", "path", "files"}:
            raise AdjudicationError("public case manifest row changed")
        case_id = row["case_id"]
        relative_root = f"cases/{case_id}"
        case_dir = bundle / relative_root
        if (
            row["path"] != relative_root
            or not case_dir.is_dir()
            or case_dir.is_symlink()
            or case_dir.stat().st_mode & 0o222
        ):
            raise AdjudicationError("public case directory changed")
        actual = {
            str(path.relative_to(case_dir)): sha256_file(path)
            for path in case_dir.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        if actual != row["files"]:
            raise AdjudicationError("public case file/hash set changed")
        for path in case_dir.rglob("*"):
            if path.is_symlink() or path.stat().st_mode & 0o222:
                raise AdjudicationError("public case path is unsafe")
        validate_output_document(load_json(case_dir / "output.json"))


def event_topology(events: list[dict[str, Any]]) -> dict[str, int]:
    topology: Counter[str] = Counter()
    for event in events:
        item = event.get("item")
        item_type = item.get("type") if isinstance(item, dict) else "-"
        topology[f"{event.get('type')}:{item_type}"] += 1
    return dict(sorted(topology.items()))


def completed_tool_commands(events: list[dict[str, Any]]) -> list[str]:
    commands = []
    for event in events:
        item = event.get("item")
        if event.get("type") != "item.completed" or not isinstance(item, dict):
            continue
        if item.get("type") in {"mcp_tool_call", "web_search"}:
            raise AdjudicationError("reviewer event stream contains MCP/web use")
        if item.get("type") == "command_execution":
            command = item.get("command")
            if not isinstance(command, str) or not command:
                raise AdjudicationError("reviewer command event lacks literal command")
            commands.append(command)
    return commands


def ordered_command_hashes(commands: list[str]) -> list[str]:
    return [
        hashlib.sha256(command.encode("utf-8")).hexdigest()
        for command in commands
    ]


def prepare() -> dict[str, Any]:
    if ALLOWLIST.exists() or COMMAND.exists() or OUTPUT.exists():
        raise AdjudicationError("refusing to overwrite adjudication preparation")
    commands = completed_tool_commands(load_jsonl(EVENTS))
    if len(commands) != EXPECTED_OUTER_COUNT:
        raise AdjudicationError("reviewer command count is not exactly eight")
    manifest = load_json(BUNDLE_MANIFEST)
    cited = collect_cited_commands(manifest)
    if (
        len(cited) != EXPECTED_CITED_COUNT
        or len(set(cited)) != EXPECTED_UNIQUE_CITED_COUNT
    ):
        raise AdjudicationError("cited command count changed before adjudication")
    allowlist = {
        "schema": "agentsight.utility2.reviewer-role-allowlist.v6",
        "outer_command_count": 8,
        "outer_argv_exact_prefix": ["/bin/bash", "-lc"],
        "outer_command_sha256_ordered": ordered_command_hashes(commands),
        "allowed_absolute_roles": {
            "/bin/bash": [
                "outer argv[0] with argv exactly [/bin/bash, -lc, inner]",
                "nested executor only as exact /bin/bash -lc \"$cmd\"",
            ],
            "/dev/null": "write redirection sink only",
            "/home": f"literal only inside locked rg pattern: {LOCKED_RG_PATTERN}",
            "/output.json": "suffix only inside exact ${f%/output.json}",
        },
        "expected_event_topology": EXPECTED_EVENT_TOPOLOGY,
        "expected_failed_validation_errors": EXPECTED_ERRORS,
        "expected_cited_command_count": EXPECTED_CITED_COUNT,
        "expected_unique_cited_command_count": EXPECTED_UNIQUE_CITED_COUNT,
        "cited_command_sha256_ordered": ordered_command_hashes(cited),
        "cited_shell_grammar": {
            "scope": (
                "fixed role certificates for the exact ordered 103 cited "
                "command hashes only; not a general shell/AWK safety claim"
            ),
            "allowed_command_positions": [
                "go tool pprof",
                "jq",
                "sed",
                "awk",
                "sort",
                "cut",
                "uniq",
                "head",
            ],
            "allowed_operator": "pipe only",
            "input_artifact": (
                "exactly one local .pb.gz or .jsonl leaf (optional ./) "
                "resolved to one frozen analyst package"
            ),
            "redirection": "forbidden",
            "sandbox_replay": (
                "bubblewrap unshared network, read-only selected package, "
                "no home mount, empty environment, writable tmpfs only"
            ),
            "tool_sublanguages": (
                "report-only pprof flags; jq without module/env/file options; "
                "awk without system/getline/redirection/env/argv; print-only "
                "sed; comparison-only sort; fixed cut/uniq/head modes"
            ),
            "encoded_shell_forms": (
                "ANSI-C quoting, hexadecimal/octal/unicode escapes, command "
                "and process substitution, and all shell parameter expansion "
                "outside single-quoted tool programs are forbidden before "
                "shlex parsing"
            ),
        },
        "reject": [
            "any other absolute path role",
            "parent or home traversal",
            "network, endpoint, MCP, or web use",
            "redaction-marker execution",
            "base64, encoded execution, eval, or exec bypass",
            "any cited executable or shell operator outside the exact grammar",
        ],
    }
    dump_json(ALLOWLIST, allowlist)
    command = {
        "schema": "agentsight.utility2.adjudication-command.v1",
        "command_identifier": "experiment-002-review-audit-adjudication-v1",
        "command": [
            str(Path(sys.executable).resolve()),
            "-I",
            "-S",
            str(Path(__file__).resolve()),
            "--execute",
            "--allowlist",
            str(ALLOWLIST.resolve()),
            "--output",
            str(OUTPUT.resolve()),
        ],
    }
    dump_json(COMMAND, command)
    return {
        "status": "PASS",
        "allowlist_sha256": sha256_file(ALLOWLIST),
        "command_sha256": sha256_file(COMMAND),
        "outer_command_count": len(commands),
        "model_calls_made": 0,
    }


NETWORK_RE = re.compile(
    r"(?i)https?://|ftp://|\b(?:localhost|127\.0\.0\.1)(?::\d+)?\b|/dev/tcp"
)
NETWORK_PROGRAM_RE = re.compile(
    r"(?i)(?:^|[;&|(\n])\s*(?:(?:command|sudo)\s+)?"
    r"(?:curl|wget|nc|ncat|ssh|scp|sftp|telnet)(?=\s|$)"
)
NETWORK_LIBRARY_RE = re.compile(
    r"(?i)\b(?:socket|requests|urllib|httpx|aiohttp|openai|websocket|"
    r"ftplib|smtplib|paramiko)\b|"
    r"\bgit\s+(?:ls-remote|clone|fetch|pull|push)\b|"
    r"\bgh\s+api\b"
)
BYPASS_RE = re.compile(
    r"(?i)\b(?:base64|uuencode|xxd\s+-r|openssl\s+enc|eval|exec|compile|"
    r"__import__|fromhex|binascii|codecs|marshal|pickle|atob|b64decode|"
    r"subprocess|os\s*\.\s*system|popen|runpy)\b"
)
MARKER_RE = re.compile(
    r"\$(?:\{)?(?:OUTSIDE|ENDPOINT|RUN_ID|BLOCK_ID|OTHER_CASE_ID|CASE_ID)"
    r"(?:\})?(?![A-Za-z0-9_])"
)
ABSOLUTE_TOKEN_RE = re.compile(
    r"(^|[\s'\"=])/(?!/)(?:[A-Za-z0-9._${}-]+/)*[A-Za-z0-9._${}-]+"
)
TRAVERSAL_RE = re.compile(r"(^|[\s'\"=])(?:\.\.|~)(?:/|\\|\b)")
DYNAMIC_TRAVERSAL_RE = re.compile(
    r"(?i)\bPath\s*\.\s*cwd\s*\(\s*\)\s*\.\s*parent\b|"
    r"\bPath\s*\(\s*\)\s*\.\s*resolve\s*\(\s*\)\s*\.\s*parent\b|"
    r"\bos\s*\.\s*getcwd\s*\(|\bgetcwd\s*\(|"
    r"\breadlink\s+-f\b|\brealpath\b"
)
DYNAMIC_EXECUTION_RE = re.compile(
    r"\$(?:\{)?(?:cmd|command|tool|program|exe|shell)(?:\})?"
)


def audit_outer_command(command: str) -> list[str]:
    risks: list[str] = []
    try:
        argv = shlex.split(command)
    except ValueError:
        return ["outer command is not valid shlex"]
    if len(argv) != 3 or argv[:2] != ["/bin/bash", "-lc"]:
        return ["outer argv is not exactly [/bin/bash, -lc, inner]"]
    inner = argv[2]

    # Remove only the four registered path roles before rejecting every other
    # absolute/traversal/network literal.
    protected = inner
    if LOCKED_RG_PATTERN in protected:
        protected = protected.replace(LOCKED_RG_PATTERN, "$LOCKED_RG_PATTERN")
    protected = protected.replace("${f%/output.json}", "$LOCKED_SUFFIX")
    protected = re.sub(
        r"""/bin/bash\s+-lc\s+["']?\$cmd["']?""",
        "$LOCKED_NESTED_EXECUTOR",
        protected,
    )
    protected = re.sub(
        r"""(?<![<])>{1,2}\s*/dev/null\b""",
        "$LOCKED_NULL_WRITE_SINK",
        protected,
    )
    if any(literal in protected for literal in ("/bin/bash", "/dev/null", "/home")):
        risks.append("registered absolute literal appeared in an unallowed role")
    if ABSOLUTE_TOKEN_RE.search(protected):
        risks.append("unregistered absolute path")
    if TRAVERSAL_RE.search(protected):
        risks.append("parent/home traversal")
    if (
        NETWORK_RE.search(protected)
        or NETWORK_PROGRAM_RE.search(protected)
        or NETWORK_LIBRARY_RE.search(protected)
    ):
        risks.append("network or endpoint")
    if MARKER_RE.search(protected):
        risks.append("redaction marker execution")
    if BYPASS_RE.search(protected) or DYNAMIC_EXECUTION_RE.search(protected):
        risks.append("encoding/eval bypass")
    if DYNAMIC_TRAVERSAL_RE.search(protected):
        risks.append("dynamic parent traversal")
    return risks


ALLOWED_CITED_COMMANDS = {
    "go",
    "jq",
    "sed",
    "awk",
    "sort",
    "cut",
    "uniq",
    "head",
}
SHELL_OPERATORS = {";", "&&", "||", "|", "&", "<", ">", ">>", "<<"}


def cited_shell_tokens(command: str) -> list[str]:
    lexer = shlex.shlex(
        command, posix=True, punctuation_chars="<>&|();"
    )
    lexer.whitespace_split = True
    return list(lexer)


def cited_command_positions(tokens: list[str]) -> list[tuple[int, str]]:
    positions: list[tuple[int, str]] = []
    expect_command = True
    for index, token in enumerate(tokens):
        if expect_command and token not in {"(", ")"}:
            positions.append((index, token))
            expect_command = False
        if token in SHELL_OPERATORS:
            expect_command = True
    return positions


def cited_pipeline_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token == "|":
            segments.append([])
        else:
            segments[-1].append(token)
    if any(not segment for segment in segments):
        raise AdjudicationError("cited pipeline contains an empty segment")
    return segments


def audit_cited_segment(segment: list[str]) -> list[str]:
    """Validate one command against its exact non-executable sublanguage."""
    command = segment[0] if segment else ""
    risks: list[str] = []
    if command == "go":
        if len(segment) < 5 or segment[:3] != ["go", "tool", "pprof"]:
            return ["go invocation is not exactly go tool pprof"]
        if not (
            segment[-1].endswith(".pb.gz")
            and Path(segment[-1]).parent in {Path("."), Path("")}
        ):
            risks.append("pprof input is not one local profile")
        safe_flag = re.compile(
            r"(?:-top|-tags|-traces|-nodecount=\d+|-nodefraction=0|"
            r"-(?:focus|ignore|tagfocus)=[A-Za-z0-9_:()|=-]+)"
        )
        if any(
            safe_flag.fullmatch(token) is None for token in segment[3:-1]
        ):
            risks.append("pprof flag is outside registered report-only flags")
    elif command == "jq":
        if (
            len(segment) != 4
            or segment[1] not in {"-r", "-s"}
            or not segment[-1].endswith(".jsonl")
        ):
            risks.append("jq argv is outside one-filter one-input grammar")
        else:
            jq_filter = segment[2]
            if re.search(
                r"(?i)\b(?:module|include|import|env|input_filename|"
                r"debug|stderr|halt|halt_error)\b|\$ENV\b",
                jq_filter,
            ):
                risks.append("jq filter uses external/module/environment input")
    elif command == "awk":
        if len(segment) == 2:
            program = segment[1]
        elif (
            len(segment) == 4
            and segment[1:3] == ["-F", "\\t"]
        ):
            program = segment[3]
        else:
            return ["awk argv is outside frozen field-processing grammar"]
        masked = []
        in_string = False
        escaped = False
        for character in program:
            if escaped:
                masked.append(" " if in_string else character)
                escaped = False
            elif character == "\\":
                masked.append(" " if in_string else character)
                escaped = True
            elif character == '"':
                masked.append(" ")
                in_string = not in_string
            else:
                masked.append(" " if in_string else character)
        structural_program = "".join(masked)
        if re.search(
            r"(?i)\b(?:system|getline|close|ENVIRON|ARGV|ARGC)\b|@load|"
            r"@[A-Za-z_][A-Za-z0-9_]*\s*\(|@include|"
            r"\bprint(?:f)?\b[^;]*(?:>\s*[^=]|\|\s*[^|])",
            structural_program,
        ):
            risks.append("awk program has external read/write/execute capability")
    elif command == "sed":
        if (
            len(segment) != 3
            or segment[1] != "-n"
            or re.fullmatch(r"\d+(?:,\d+)?p", segment[2]) is None
        ):
            risks.append("sed program is outside print-only sandbox grammar")
    elif command == "sort":
        safe_sort = re.compile(r"(?:-u|-nr|-t=|-k\d+,\d+nr)")
        if any(safe_sort.fullmatch(token) is None for token in segment[1:]):
            risks.append("sort argv contains a non-comparison option or operand")
    elif command == "cut":
        if segment != ["cut", "-f1"]:
            risks.append("cut argv is outside fixed field selection")
    elif command == "uniq":
        if segment != ["uniq", "-c"]:
            risks.append("uniq argv is outside fixed count mode")
    elif command == "head":
        if not (
            len(segment) == 2
            and re.fullmatch(r"-\d+", segment[1])
            or len(segment) == 3
            and segment[1] == "-n"
            and re.fullmatch(r"\d+", segment[2])
        ):
            risks.append("head argv is outside fixed numeric prefix mode")
    else:
        risks.append("executable outside cited-command grammar")
    return risks


def cited_artifact_leaf(command: str) -> str:
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise AdjudicationError("cited command is not valid shlex") from exc
    artifacts = [
        token
        for token in tokens
        if token.endswith(".pb.gz") or token.endswith(".jsonl")
    ]
    if (
        len(artifacts) != 1
        or Path(artifacts[0]).is_absolute()
        or Path(artifacts[0]).parent not in {Path("."), Path("")}
        or Path(artifacts[0]).name in {".pb.gz", ".jsonl"}
    ):
        raise AdjudicationError(
            "cited command must name one local frozen artifact leaf"
        )
    return artifacts[0]


def audit_cited_command(
    command: str,
    exact_allowed_sha256: set[str] | None = None,
) -> list[str]:
    risks = []
    if not isinstance(command, str) or not command.strip():
        return ["missing cited command"]
    command_sha256 = hashlib.sha256(command.encode("utf-8")).hexdigest()
    if (
        exact_allowed_sha256 is None
        or command_sha256 not in exact_allowed_sha256
    ):
        return ["command is not in the frozen exact cited-command allowlist"]
    try:
        tokens = cited_shell_tokens(command)
    except ValueError:
        return ["cited command is not valid shlex"]
    if any(token.startswith("/") for token in tokens):
        risks.append("absolute path")
    if ABSOLUTE_TOKEN_RE.search(command):
        risks.append("absolute path")
    if TRAVERSAL_RE.search(command) or any(
        "../" in token or token.startswith("~") for token in tokens
    ):
        risks.append("parent/home traversal")
    if (
        NETWORK_RE.search(command)
        or NETWORK_PROGRAM_RE.search(command)
        or NETWORK_LIBRARY_RE.search(command)
    ):
        risks.append("network or endpoint")
    if MARKER_RE.search(command):
        risks.append("redaction marker")
    if BYPASS_RE.search(command) or DYNAMIC_EXECUTION_RE.search(command):
        risks.append("encoding/eval bypass")
    if DYNAMIC_TRAVERSAL_RE.search(command):
        risks.append("dynamic parent traversal")
    if re.search(r"\$(?:\{)?(?:HOME|OLDPWD|CODEX_HOME)(?:\})?", command):
        risks.append("private environment path")
    if re.search(r"`|\$\(|<\(|>\(", command):
        risks.append("shell or process substitution")
    quote_state = "unquoted"
    escaped = False
    for character in command:
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote_state != "single":
            escaped = True
            continue
        if character == "'" and quote_state != "double":
            quote_state = (
                "single" if quote_state == "unquoted" else "unquoted"
            )
            continue
        if character == '"' and quote_state != "single":
            quote_state = (
                "double" if quote_state == "unquoted" else "unquoted"
            )
            continue
        if character == "$" and quote_state != "single":
            risks.append("shell parameter expansion")
            break
    if re.search(
        r"\$'|\\x[0-9A-Fa-f]{2}|\\u[0-9A-Fa-f]{4}|"
        r"\\U[0-9A-Fa-f]{8}|\\[0-7]{3}",
        command,
    ):
        risks.append("encoded shell token")
    operators = [token for token in tokens if token in SHELL_OPERATORS]
    if any(operator != "|" for operator in operators):
        risks.append("shell operator outside pipe-only grammar")
    positions = cited_command_positions(tokens)
    if not positions or any(
        command_name not in ALLOWED_CITED_COMMANDS
        for _, command_name in positions
    ):
        risks.append("executable outside cited-command grammar")
    for index, command_name in positions:
        if command_name == "go" and tokens[index : index + 3] != [
            "go",
            "tool",
            "pprof",
        ]:
            risks.append("go invocation is not exactly go tool pprof")
    try:
        for segment in cited_pipeline_segments(tokens):
            risks.extend(audit_cited_segment(segment))
    except AdjudicationError:
        risks.append("invalid cited pipeline")
    try:
        cited_artifact_leaf(command)
    except AdjudicationError:
        risks.append("cited artifact is not one contained local leaf")
    return sorted(set(risks))


def frozen_artifact_for_leaf(leaf: str) -> Path:
    leaf_name = Path(leaf).name
    candidates = [
        path
        for package in (
            EXPERIMENT / "analyst-packages" / "PROFILE",
            EXPERIMENT / "analyst-packages" / "RAW-OPERATIONS",
        )
        for path in package.iterdir()
        if path.is_file() and not path.is_symlink() and path.name == leaf_name
    ]
    if len(candidates) != 1:
        raise AdjudicationError(
            "cited artifact leaf does not resolve uniquely in frozen packages"
        )
    candidate = candidates[0].resolve(strict=True)
    package = candidate.parent.resolve(strict=True)
    if candidate.parent != package:
        raise AdjudicationError("cited artifact escaped its frozen package")
    return candidate


def sandbox_replay_cited(
    command: str, exact_allowed_sha256: set[str]
) -> None:
    """Execute one exact cited command with no network and one read-only package."""
    if audit_cited_command(command, exact_allowed_sha256):
        raise AdjudicationError("unsafe cited command cannot enter sandbox")
    artifact = frozen_artifact_for_leaf(cited_artifact_leaf(command))
    package = artifact.parent
    sandbox = [
        "bwrap",
        "--die-with-parent",
        "--unshare-net",
        "--clearenv",
        "--ro-bind",
        "/usr",
        "/usr",
        "--ro-bind",
        "/bin",
        "/bin",
        "--ro-bind",
        "/lib",
        "/lib",
        "--ro-bind",
        "/lib64",
        "/lib64",
        "--ro-bind",
        "/etc/alternatives",
        "/etc/alternatives",
        "--ro-bind",
        str(package),
        "/work",
        "--tmpfs",
        "/tmp",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--chdir",
        "/work",
        "--setenv",
        "PATH",
        "/usr/bin:/bin",
        "--setenv",
        "HOME",
        "/tmp",
        "--setenv",
        "GOCACHE",
        "/tmp/go-cache",
        "/bin/bash",
        "--noprofile",
        "--norc",
        "-c",
        re.sub(
            r"(^|\|\s*)sed\s+",
            r"\1sed --sandbox ",
            command,
        ),
    ]
    completed = subprocess.run(
        sandbox,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0:
        raise AdjudicationError(
            "cited command failed exact no-network sandbox replay"
        )


def cited_role_receipt(command: str, index: int) -> dict[str, Any]:
    tokens = cited_shell_tokens(command)
    segments = cited_pipeline_segments(tokens)
    artifact = cited_artifact_leaf(command)
    return {
        "index": index,
        "command_sha256": hashlib.sha256(
            command.encode("utf-8")
        ).hexdigest(),
        "pipeline_executables": [segment[0] for segment in segments],
        "normalized_argv_sha256": [
            hashlib.sha256(
                json.dumps(
                    segment,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            for segment in segments
        ],
        "artifact_class": (
            "semantic-pprof" if artifact.endswith(".pb.gz") else "raw-jsonl"
        ),
        "static_sublanguage_risk_count": 0,
        "artifact_realpath_contained": True,
        "bwrap_unshare_net_replay": "PASS",
    }


def validate_decisions_shape(path: Path, expected_case_ids: set[str]) -> None:
    document = load_json(path)
    if not isinstance(document, dict) or set(document) != {"cases"}:
        raise AdjudicationError("decisions top-level shape changed")
    cases = document["cases"]
    if not isinstance(cases, list) or len(cases) != 40:
        raise AdjudicationError("decisions must contain exactly 40 cases")
    seen = set()
    for row in cases:
        if not isinstance(row, dict) or set(row) != {"case_id", *REVIEW_FIELDS}:
            raise AdjudicationError("decision row shape changed")
        case_id = row["case_id"]
        if not isinstance(case_id, str) or case_id in seen:
            raise AdjudicationError("decision case ID is invalid or duplicated")
        # Type-check only. Never aggregate, emit, branch on, or otherwise
        # inspect the boolean values.
        if any(type(row[field]) is not bool for field in REVIEW_FIELDS):
            raise AdjudicationError("decision fields are not all booleans")
        seen.add(case_id)
    if seen != expected_case_ids:
        raise AdjudicationError("decision case IDs differ from public bundle")


def collect_cited_commands(manifest: dict[str, Any]) -> list[str]:
    commands = []
    for case in manifest["cases"]:
        output = load_json(BUNDLE / case["path"] / "output.json")
        kind = validate_output_document(output)
        if kind == "unavailable":
            continue
        commands.extend(
            item["command"] for item in output["quantitative_evidence"]
        )
    return commands


def original_hashes() -> dict[str, str]:
    paths = {
        "original_failed_attempt": ORIGINAL_RUN,
        "original_events": EVENTS,
        "original_event_receipts": RECEIPTS,
        "original_decisions": DECISIONS,
        "original_bundle_manifest": BUNDLE_MANIFEST,
        "frozen_prompt": PROMPT,
        "frozen_model_contract": MODEL_CONTRACT,
        "frozen_review_command": REVIEW_COMMAND,
        "original_batch_receipt": BATCH_RECEIPT,
        "original_frozen_contract": ORIGINAL_CONTRACT,
    }
    return {name: sha256_file(path) for name, path in paths.items()}


def _verify_original_attempt(allowlist: dict[str, Any]) -> dict[str, Any]:
    if sha256_file(ORIGINAL_CONTRACT) != ORIGINAL_CONTRACT_SHA256:
        raise AdjudicationError("original frozen contract changed")
    run = load_json(ORIGINAL_RUN)
    if (
        run.get("status") != "failed"
        or run.get("exit_code") != 0
        or run.get("validation_errors") != EXPECTED_ERRORS
    ):
        raise AdjudicationError("original failed review signature changed")
    events = load_jsonl(EVENTS)
    if len(events) != 22 or event_topology(events) != EXPECTED_EVENT_TOPOLOGY:
        raise AdjudicationError("reviewer event topology changed")
    commands = completed_tool_commands(events)
    if (
        len(commands) != 8
        or ordered_command_hashes(commands)
        != allowlist.get("outer_command_sha256_ordered")
    ):
        raise AdjudicationError("reviewer command literals changed")
    recorded_tools = run.get("actual_tool_commands")
    if not isinstance(recorded_tools, list) or len(recorded_tools) != 8:
        raise AdjudicationError("reviewer provenance tool list changed")
    if [row.get("command") for row in recorded_tools] != commands or any(
        row.get("type") != "command_execution" for row in recorded_tools
    ):
        raise AdjudicationError("event and provenance tool commands differ")
    receipts = load_jsonl(RECEIPTS)
    if len(receipts) != len(events):
        raise AdjudicationError("event receipt count changed")
    for index, (receipt, event) in enumerate(zip(receipts, events), 1):
        if (
            receipt.get("line_index") != index
            or receipt.get("event_type") != event.get("type")
        ):
            raise AdjudicationError("event receipt topology changed")
    if STDERR.stat().st_size != 0:
        raise AdjudicationError("reviewer stderr is not empty")
    hashes = original_hashes()
    if (
        run.get("events_sha256") != hashes["original_events"]
        or run.get("event_receipts_sha256")
        != hashes["original_event_receipts"]
        or run.get("decisions_sha256") != hashes["original_decisions"]
        or run.get("stderr_sha256") != sha256_file(STDERR)
        or run.get("review_bundle_manifest_sha256_before")
        != hashes["original_bundle_manifest"]
        or run.get("review_bundle_manifest_sha256_after")
        != hashes["original_bundle_manifest"]
        or run.get("review_bundle_manifest_unchanged") is not True
    ):
        raise AdjudicationError("original provenance hash bindings changed")
    manifest = load_json(BUNDLE_MANIFEST)
    expected_case_ids = {case["case_id"] for case in manifest["cases"]}
    verify_public_bundle(BUNDLE, expected_case_ids)
    validate_decisions_shape(DECISIONS, expected_case_ids)
    batch = load_json(BATCH_RECEIPT)
    if (
        batch.get("status") != "completed"
        or batch.get("run_count") != 40
        or len(batch.get("ordered_run_ids", [])) != 40
    ):
        raise AdjudicationError("40-run batch aggregate changed")
    return {
        "run": run,
        "commands": commands,
        "manifest": manifest,
        "hashes": hashes,
    }


def execute(allowlist_path: Path, output: Path) -> dict[str, Any]:
    if allowlist_path.resolve() != ALLOWLIST.resolve():
        raise AdjudicationError("adjudication allowlist path changed")
    if output.resolve() != OUTPUT.resolve():
        raise AdjudicationError("adjudication output path changed")
    if output.exists() or output.is_symlink():
        raise AdjudicationError("refusing to overwrite adjudication outputs")
    allowlist = load_json(allowlist_path)
    original = _verify_original_attempt(allowlist)

    outer_risks = [
        risk
        for command in original["commands"]
        for risk in audit_outer_command(command)
    ]
    cited = collect_cited_commands(original["manifest"])
    if ordered_command_hashes(cited) != allowlist.get(
        "cited_command_sha256_ordered"
    ):
        raise AdjudicationError("ordered cited command literals changed")
    exact_allowed_sha256 = set(
        allowlist.get("cited_command_sha256_ordered", [])
    )
    cited_risks = [
        risk
        for command in cited
        for risk in audit_cited_command(command, exact_allowed_sha256)
    ]
    if (
        outer_risks
        or len(cited) != EXPECTED_CITED_COUNT
        or len(set(cited)) != EXPECTED_UNIQUE_CITED_COUNT
        or cited_risks
    ):
        raise AdjudicationError(
            "full outer/cited command re-audit did not pass exactly"
        )
    for command in cited:
        sandbox_replay_cited(command, exact_allowed_sha256)
    role_receipts = [
        cited_role_receipt(command, index)
        for index, command in enumerate(cited)
    ]

    corrected = dict(original["run"])
    corrected["status"] = "ok"
    corrected["validation_errors"] = []
    unchanged_fields = set(original["run"]) - {"status", "validation_errors"}
    if any(
        corrected[field] != original["run"][field]
        for field in unchanged_fields
    ):
        raise AdjudicationError("corrected provenance changed another field")

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=".adjudication-staging-", dir=output.parent)
    )
    try:
        corrected_path = staging / "corrected-provenance.json"
        dump_json(corrected_path, corrected)
        role_receipts_path = staging / "cited-command-role-receipts.json"
        dump_json(
            role_receipts_path,
            {
                "schema": (
                    "agentsight.utility2.cited-command-role-receipts.v1"
                ),
                "command_count": len(role_receipts),
                "commands_not_emitted": True,
                "receipts": role_receipts,
            },
        )
        report = {
            "schema": "agentsight.utility2.reviewer-audit-adjudication.v6",
            "status": "PASS",
            "reaudit_status": "PASS",
            "correction_type": CORRECTION_TYPE,
            "decisions_reused": True,
            "reviewer_model_rerun": False,
            "all_original_hashes_unchanged": True,
            "only_changed_provenance_fields": [
                "status",
                "validation_errors",
            ],
            "original_status": "failed",
            "corrected_status": "ok",
            "pre_result_unblinding_attestation_sha256": sha256_file(
                ATTESTATION_JSON
            ),
            "exact_role_allowlist_sha256": sha256_file(ALLOWLIST),
            "original_hashes": original["hashes"],
            "outer_command_reaudit": {
                "command_count": len(original["commands"]),
                "risk_count": 0,
                "all_exact_role_allowlist_pass": True,
            },
            "cited_command_reaudit": {
                "command_count": len(cited),
                "unique_command_count": len(set(cited)),
                "risk_count": 0,
                "commands_not_emitted": True,
                "ordered_command_hash_receipt_count": len(cited),
                "strict_shell_grammar_pass": True,
                "exact_frozen_command_allowlist_pass": True,
                "general_language_safety_claimed": False,
                "artifact_realpath_containment_pass": True,
                "no_network_sandbox_replay_count": len(cited),
                "tool_sublanguage_static_receipt_count": len(role_receipts),
                "role_receipts_sha256": sha256_file(role_receipts_path),
                "sandbox_scope": (
                    "current deterministic replay; not a claim of historical "
                    "execution equivalence"
                ),
            },
            "decisions_shape_validation": {
                "case_count": 40,
                "complete": True,
                "boolean_values_not_aggregated_or_emitted": True,
                "sha256": original["hashes"]["original_decisions"],
            },
            "bundle_manifest": {
                "before_after_current_equal": True,
                "sha256": original["hashes"]["original_bundle_manifest"],
            },
            "corrected_provenance_sha256": sha256_file(corrected_path),
        }
        report_path = staging / "report.json"
        dump_json(report_path, report)
        os.chmod(corrected_path, 0o444)
        os.chmod(role_receipts_path, 0o444)
        os.chmod(report_path, 0o444)
        os.chmod(staging, 0o555)
        staging.rename(output)
        return report
    except BaseException:
        if staging.exists():
            os.chmod(staging, 0o755)
            for path in staging.iterdir():
                os.chmod(path, 0o644)
            shutil.rmtree(staging)
        raise


def validate_corrected_provenance(
    original: dict[str, Any], corrected: dict[str, Any]
) -> None:
    """Require exactly the two adjudicated value changes and no schema drift."""
    if set(corrected) != set(original):
        raise AdjudicationError("corrected provenance field set changed")
    for field in original:
        expected = (
            "ok"
            if field == "status"
            else []
            if field == "validation_errors"
            else original[field]
        )
        if corrected[field] != expected:
            raise AdjudicationError(
                f"corrected provenance changed forbidden field: {field}"
            )


def verify_existing_adjudication() -> dict[str, Any]:
    if (
        not REPORT.is_file()
        or not CORRECTED.is_file()
        or not ROLE_RECEIPTS.is_file()
    ):
        raise AdjudicationError("adjudication outputs are missing")
    report = load_json(REPORT)
    if (
        report.get("status") != "PASS"
        or report.get("reaudit_status") != "PASS"
        or report.get("correction_type") != CORRECTION_TYPE
        or report.get("decisions_reused") is not True
        or report.get("reviewer_model_rerun") is not False
        or report.get("all_original_hashes_unchanged") is not True
        or report.get("corrected_provenance_sha256") != sha256_file(CORRECTED)
        or report.get("original_hashes") != original_hashes()
        or report.get("pre_result_unblinding_attestation_sha256")
        != sha256_file(ATTESTATION_JSON)
        or report.get("exact_role_allowlist_sha256") != sha256_file(ALLOWLIST)
        or report.get("cited_command_reaudit", {}).get(
            "role_receipts_sha256"
        )
        != sha256_file(ROLE_RECEIPTS)
    ):
        raise AdjudicationError("adjudication report bindings changed")
    original = load_json(ORIGINAL_RUN)
    corrected = load_json(CORRECTED)
    validate_corrected_provenance(original, corrected)
    if (
        REPORT.stat().st_mode & 0o222
        or CORRECTED.stat().st_mode & 0o222
        or ROLE_RECEIPTS.stat().st_mode & 0o222
    ):
        raise AdjudicationError("adjudication outputs are writable")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--execute", action="store_true")
    parser.add_argument("--allowlist", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(prepare(), sort_keys=True))
        return 0
    if args.allowlist is None or args.output is None:
        raise SystemExit("--execute requires --allowlist and --output")
    report = execute(args.allowlist, args.output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "outer_command_count": report["outer_command_reaudit"][
                    "command_count"
                ],
                "cited_command_count": report["cited_command_reaudit"][
                    "command_count"
                ],
                "unique_cited_command_count": report[
                    "cited_command_reaudit"
                ]["unique_command_count"],
                "decisions_boolean_values_emitted": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
