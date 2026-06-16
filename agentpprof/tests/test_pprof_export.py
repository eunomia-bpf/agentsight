from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agentpprof.pprof import SemanticSample, write_pprof


class PprofExportTests(unittest.TestCase):
    def test_profile_is_accepted_by_go_pprof_when_available(self) -> None:
        if not shutil.which("go"):
            self.skipTest("go toolchain unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.pb.gz"
            write_pprof(
                path,
                "tokens",
                "count",
                [
                    SemanticSample(("project:demo", "agent:codex", "prompt:debug", "token:input"), 10),
                    SemanticSample(("project:demo", "agent:codex", "prompt:debug", "token:output"), 5),
                ],
                comments=["agentpprof test profile"],
            )
            proc = subprocess.run(
                ["go", "tool", "pprof", "-top", str(path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("token:input", proc.stdout)


if __name__ == "__main__":
    unittest.main()
