#!/usr/bin/env python3
"""Focused regression tests for the RQ7 v4 oracle grammar."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
ORACLE_PATH = REPO / "agentvis/research/rq7_source_oracle_check.py"
SPEC = importlib.util.spec_from_file_location("rq7_oracle_v4", ORACLE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load oracle")
ORACLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORACLE)


class OracleV4Tests(unittest.TestCase):
    def test_static_exec_patch_is_decoded(self) -> None:
        command = (
            'const patch = "*** Begin Patch\\n'
            "*** Update File: src/lib.rs\\n"
            "@@\\n"
            "-old\\n"
            "+new\\n"
            "*** End Patch"
            '"; text(await tools.apply_patch(patch));'
        )
        args = ORACLE.unwrap_exec("exec", {"command": command})
        self.assertIn("\n*** Update File:", args["_wrapped_patch"])
        self.assertEqual(ORACLE.atom_for("exec", args), "edit")
        self.assertEqual(
            ORACLE.event_effects(
                {
                    "kind": "tool",
                    "name": "exec",
                    "args": args,
                    "cwd": "/repo",
                }
            ),
            [("src/lib.rs", "write", None)],
        )

    def test_patch_body_is_not_parsed_as_shell(self) -> None:
        command = (
            'const patch = "*** Begin Patch\\n'
            "*** Update File: script.sh\\n"
            "@@\\n"
            "+touch docs/not-an-edge.md\\n"
            "*** End Patch"
            '"; text(await tools.apply_patch(patch));'
        )
        args = ORACLE.unwrap_exec("exec", {"command": command})
        self.assertEqual(
            ORACLE.event_effects(
                {
                    "kind": "tool",
                    "name": "exec",
                    "args": args,
                    "cwd": "/repo",
                }
            ),
            [("script.sh", "write", None)],
        )

    def test_patch_and_nested_shell_both_survive(self) -> None:
        command = (
            'const p = "*** Begin Patch\\n'
            "*** Update File: src/lib.rs\\n"
            "@@\\n"
            "-old\\n"
            "+new\\n"
            "*** End Patch"
            '"; text(await tools.apply_patch(p)); '
            'const r = await tools.exec_command({cmd:"cat README.md",'
            'workdir:"/repo"}); text(r.output);'
        )
        args = ORACLE.unwrap_exec("exec", {"command": command})
        self.assertEqual(args["cmd"], "cat README.md")
        self.assertEqual(
            ORACLE.event_effects(
                {
                    "kind": "tool",
                    "name": "exec",
                    "args": args,
                    "cwd": "/repo",
                }
            ),
            [
                ("/repo/README.md", "read", None),
                ("src/lib.rs", "write", None),
            ],
        )

    def test_inline_cd_scopes_later_relative_operand(self) -> None:
        effects = ORACLE.shell_effects(
            "cd third_party/openreviewer && cat README.md",
            "/repo",
        )
        self.assertEqual(
            effects,
            [
                (
                    "/repo/third_party/openreviewer/README.md",
                    "read",
                    None,
                )
            ],
        )

    def test_outside_and_dynamic_cd_do_not_fabricate_repo_paths(self) -> None:
        root = Path("/repo")
        outside = ORACLE.shell_effects(
            "cd /tmp/work && touch fake/docs/a.md",
            "/repo",
        )
        self.assertEqual(
            [
                ORACLE.repo_path(path, "/repo", root)
                for path, _, _ in outside
            ],
            [None],
        )
        self.assertEqual(
            ORACLE.shell_effects(
                'cd "$TMPDIR/work" && touch fake/docs/a.md',
                "/repo",
            ),
            [],
        )

    def test_option_arity_and_sed_program(self) -> None:
        self.assertEqual(
            ORACLE.shell_effects(
                "cat -n collector/src/view/mod.rs",
                "/repo",
            ),
            [
                (
                    "/repo/collector/src/view/mod.rs",
                    "read",
                    None,
                )
            ],
        )
        self.assertEqual(
            ORACLE.shell_effects(
                "sed -n '1,5p' README.md",
                "/repo",
            ),
            [("/repo/README.md", "read", None)],
        )
        self.assertEqual(
            ORACLE.shell_effects(
                "sed -f rules.sed README.md",
                "/repo",
            ),
            [("/repo/README.md", "read", None)],
        )
        self.assertEqual(
            ORACLE.shell_effects(
                "sed -e 's/x/y/' README.md",
                "/repo",
            ),
            [("/repo/README.md", "read", None)],
        )
        self.assertEqual(
            ORACLE.shell_effects(
                "find . | sed 's#^/repo/##'",
                "/repo",
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
