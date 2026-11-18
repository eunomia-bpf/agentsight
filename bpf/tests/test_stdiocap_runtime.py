#!/usr/bin/env python3
import os
import select
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from test_process_runtime import has_hidden_host_pids


BPF_DIR = Path(__file__).resolve().parents[1]
STDIOCAP = BPF_DIR / "stdiocap"
READY_MARKER = "AGENTSIGHT_STDIOCAP_READY"


def wait_for_ready(proc, timeout=15.0):
    """Wait for stdiocap's attach-complete marker on stderr.

    stdiocap emits the marker only after its probes are attached and its ring
    buffer exists, so a target may write as soon as the marker is seen. This
    replaces the fixed sleep the test used to rely on, which raced the attach
    latency: when attach took longer than the sleep, the child wrote before
    any probe was live and the capture looked empty.
    """
    deadline = time.monotonic() + timeout
    lines = []
    while time.monotonic() < deadline:
        readable, _, _ = select.select([proc.stderr], [], [], deadline - time.monotonic())
        if not readable:
            break
        line = proc.stderr.readline()
        if not line:
            break
        lines.append(line.rstrip("\n"))
        if line.strip() == READY_MARKER:
            return lines
    raise AssertionError(
        "stdiocap did not report attach readiness within "
        f"{timeout}s; stderr tail={lines[-8:]!r}, rc={proc.poll()!r}"
    )


def test_session_captures_child_stdout():
    workdir = tempfile.TemporaryDirectory(prefix="agentsight-stdiocap-")
    go_marker = os.path.join(workdir.name, "go")
    # The target waits for the marker, so its fork-and-write happens after the
    # capture is attached instead of during the attach window.
    target = subprocess.Popen(
        [
            "python3",
            "-c",
            (
                "import os, sys, time\n"
                f"marker = {go_marker!r}\n"
                "deadline = time.monotonic() + 10\n"
                "while not os.path.exists(marker):\n"
                "    if time.monotonic() > deadline:\n"
                "        sys.exit(3)\n"
                "    time.sleep(0.01)\n"
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
    target_sid = os.getsid(target.pid)
    try:
        wait_for_ready(cap)
        with open(go_marker, "w", encoding="utf-8"):
            pass
        target_out, target_err = target.communicate(timeout=15)
        # Give one ring-buffer poll interval for the child's write to arrive.
        time.sleep(0.4)
        cap.send_signal(signal.SIGTERM)
        cap_out, cap_err = cap.communicate(timeout=10)
    finally:
        for proc in (target, cap):
            if proc.poll() is None:
                proc.kill()
        workdir.cleanup()

    assert target.returncode == 0, target_err
    assert "agentsight-stdio-session" in target_out
    # A capture that missed the write and one that saw no event at all are
    # different bugs, so report what stdiocap emitted: the event count
    # separates "the probe is not firing for this session" from "the write
    # was traced but carried no payload", and the session id proves the
    # target's session is the one stdiocap was asked to follow.
    events = [line for line in cap_out.splitlines() if line.startswith("{")]
    assert "agentsight-stdio-session" in cap_out, (
        f"stdiocap emitted {len(events)} event(s) for session {target_sid} "
        f"(target pid {target.pid}, session asked for {target.pid})\n"
        f"stdout={cap_out!r}\nstderr={cap_err!r}"
    )


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