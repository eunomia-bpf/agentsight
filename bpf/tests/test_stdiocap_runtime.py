#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from test_process_runtime import has_hidden_host_pids


BPF_DIR = Path(__file__).resolve().parents[1]
STDIOCAP = BPF_DIR / "stdiocap"


def test_session_captures_child_stdout():
    target = subprocess.Popen(
        [
            "python3",
            "-c",
            (
                "import os, time\n"
                "time.sleep(0.3)\n"
                "pid = os.fork()\n"
                "if pid == 0:\n"
                "    os.write(1, b'agentsight-stdio-session')\n"
                "    os._exit(0)\n"
                "os.waitpid(pid, 0)\n"
            ),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid,
    )
    cap = subprocess.Popen(
        [str(STDIOCAP), "--session", str(target.pid), "--max-bytes", "8192"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        target_out, target_err = target.communicate(timeout=10)
        time.sleep(0.3)
        cap.send_signal(signal.SIGTERM)
        cap_out, cap_err = cap.communicate(timeout=5)
    finally:
        for proc in (target, cap):
            if proc.poll() is None:
                proc.kill()

    assert target.returncode == 0, target_err
    assert "agentsight-stdio-session" in target_out
    assert "agentsight-stdio-session" in cap_out, cap_err


def main():
    if not STDIOCAP.exists():
        print(f"missing stdiocap binary at {STDIOCAP}", file=sys.stderr)
        return 1
    if has_hidden_host_pids():
        print("SKIP: stdiocap session filtering requires the host PID namespace")
        return 0
    test_session_captures_child_stdout()
    print("stdiocap runtime tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
