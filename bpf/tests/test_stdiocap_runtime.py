#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from test_process_runtime import has_hidden_host_pids


BPF_DIR = Path(__file__).resolve().parents[1]
STDIOCAP = BPF_DIR / "stdiocap"
READY_MARKER = "AGENTSIGHT_STDIOCAP_READY"


def _start_reader(stream, sink):
    """Drain `stream` into `sink` on a thread, so no line is lost.

    `select()` on a pipe that a text-mode `Popen` wraps only reports data
    still in the pipe itself: the wrapper reads ahead, so lines it already
    holds are invisible to `select()` and are dropped by a later
    `communicate()`. Reading every pipe on its own thread is the only way to
    see each line exactly once.
    """
    def run():
        for line in stream:
            sink.append(line)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread


def _wait_for_line(sink, needle, timeout):
    """Wait until a collected line contains `needle`."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if any(needle in line for line in sink):
            return True
        time.sleep(0.02)
    return False


def wait_for_ready(err_lines, timeout=15.0):
    """Wait for stdiocap's attach-complete marker in `err_lines`.

    stdiocap emits the marker only after its probes are attached and its ring
    buffer exists, so a target may write as soon as the marker is seen. This
    replaces the fixed sleep the test used to rely on, which raced the attach
    latency: when attach took longer than the sleep, the child wrote before
    any probe was live and the capture looked empty.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if any(line.strip() == READY_MARKER for line in err_lines):
            return
        time.sleep(0.02)
    raise AssertionError(
        "stdiocap did not report attach readiness within "
        f"{timeout}s; stderr tail={err_lines[-8:]!r}"
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
    cap_out_lines, cap_err_lines = [], []
    _start_reader(cap.stdout, cap_out_lines)
    _start_reader(cap.stderr, cap_err_lines)
    try:
        try:
            wait_for_ready(cap_err_lines)
        except AssertionError:
            # Report everything stdiocap printed, including the session
            # summary it writes before the marker.
            raise AssertionError(
                "stdiocap reported no readiness: "
                f"{''.join(cap_err_lines)!r}"
            ) from None
        # stdiocap reports the session filter before the readiness marker:
        # "tracked N pid(s)" answers "did the scan find the target?", which
        # separates an empty filter from a probe that never fired. It is
        # therefore already collected once the marker arrives.
        filter_line = next(
            (
                line.rstrip("\n")
                for line in cap_err_lines
                if line.startswith("session ") and "tracked" in line
            ),
            None,
        )
        with open(go_marker, "w", encoding="utf-8"):
            pass
        target_out, target_err = target.communicate(timeout=15)
        # Wait for the event rather than sleeping a fixed 0.4 s: the ring
        # buffer is polled every PERF_POLL_TIMEOUT_MS (100 ms) and the
        # target's own exit does not mean its last write was drained, so a
        # fixed sleep passes on an idle runner and loses the write on a
        # loaded one.
        _wait_for_line(cap_out_lines, "agentsight-stdio-session", 5.0)
        cap.send_signal(signal.SIGTERM)
        cap.wait(timeout=10)
        cap_out = "".join(cap_out_lines)
        cap_err = "".join(cap_err_lines)
        if filter_line:
            cap_err = filter_line + "\n" + cap_err
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