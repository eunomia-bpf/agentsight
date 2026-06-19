#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
#
# Runtime tests for the process eBPF tracer. These tests require root because
# they load BPF programs, but they are intentionally small enough for make test.

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid


BPF_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESS = os.path.join(BPF_DIR, "process")


class RuntimeErrorWithContext(AssertionError):
    pass


def seed_pid_arg(pid):
    return ["--seed-pid", f"{pid}:0"]


class TracerSession:
    def __init__(self, *args, wait_attach=1.5):
        self.stdout = tempfile.NamedTemporaryFile(prefix="process-runtime-", suffix=".jsonl", delete=False)
        self.stderr = tempfile.NamedTemporaryFile(prefix="process-runtime-", suffix=".stderr", delete=False)
        self.proc = subprocess.Popen(
            [PROCESS] + list(args),
            stdout=self.stdout,
            stderr=self.stderr,
        )
        self.stdout.close()
        self.stderr.close()
        time.sleep(wait_attach)
        if self.proc.poll() is not None:
            raise RuntimeErrorWithContext(
                f"process tracer exited early with {self.proc.returncode}: {self.stderr_text()}"
            )

    def stop(self):
        if self.proc.poll() is None:
            self.proc.send_signal(signal.SIGINT)
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)

    def stderr_text(self):
        try:
            with open(self.stderr.name, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return ""

    def events(self):
        parsed = []
        bad = []
        with open(self.stdout.name, "r", encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    bad.append((lineno, str(exc), line[:240]))
        if bad:
            raise RuntimeErrorWithContext(f"bad JSON lines: {bad[:3]}")
        return parsed

    def cleanup(self):
        self.stop()
        for path in (self.stdout.name, self.stderr.name):
            try:
                os.unlink(path)
            except OSError:
                pass


def assert_true(condition, message):
    if not condition:
        raise RuntimeErrorWithContext(message)


def event_text(event):
    return json.dumps(event, sort_keys=True, ensure_ascii=False)


def any_event_contains(events, text):
    return any(text in event_text(event) for event in events)


def summary_types(events):
    return {event.get("type") for event in events if event.get("event") == "SUMMARY"}


def wait_for_file(path, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(path):
            return
        time.sleep(0.05)
    raise RuntimeErrorWithContext(f"timeout waiting for {path}")


def run_controlled_parent(preexec_fn=None):
    tempdir = tempfile.TemporaryDirectory(prefix="agentsight-runtime-parent-")
    trigger = os.path.join(tempdir.name, "trigger")
    done = os.path.join(tempdir.name, "done")
    marker = f"agentsight-target-{uuid.uuid4().hex}"
    code = r"""
import os
import subprocess
import sys
import time

trigger, done, marker = sys.argv[1], sys.argv[2], sys.argv[3]
while not os.path.exists(trigger):
    time.sleep(0.05)
subprocess.run(["/bin/echo", marker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
with open(done, "w") as f:
    f.write("done")
time.sleep(0.4)
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", code, trigger, done, marker],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=preexec_fn,
    )
    return tempdir, proc, trigger, done, marker


def run_controlled_network_parent():
    tempdir = tempfile.TemporaryDirectory(prefix="agentsight-runtime-network-parent-")
    trigger = os.path.join(tempdir.name, "trigger")
    done = os.path.join(tempdir.name, "done")
    port_file = os.path.join(tempdir.name, "port")
    target_port = reserve_loopback_port()
    child_code = r"""
import socket
import sys

port_file, port_arg = sys.argv[1], sys.argv[2]
port = int(port_arg)
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", port))
server.listen(1)
with open(port_file, "w") as f:
    f.write(str(port))
client = socket.socket()
client.connect(("127.0.0.1", port))
conn, _ = server.accept()
client.close()
conn.close()
server.close()
"""
    parent_code = r"""
import os
import subprocess
import sys
import time

trigger, done, port_file, child_code = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
target_port = sys.argv[5]
while not os.path.exists(trigger):
    time.sleep(0.05)
subprocess.run([sys.executable, "-c", child_code, port_file, target_port], check=True)
with open(done, "w") as f:
    f.write("done")
time.sleep(0.4)
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", parent_code, trigger, done, port_file, child_code, str(target_port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return tempdir, proc, trigger, done, port_file


def reserve_loopback_port():
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def loopback_exchange(exclude_port=None):
    for _ in range(10):
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 0))
        port = server.getsockname()[1]
        if exclude_port is not None and port == exclude_port:
            server.close()
            continue
        server.listen(1)
        client = socket.socket()
        client.connect(("127.0.0.1", port))
        conn, _ = server.accept()
        client.close()
        conn.close()
        server.close()
        return port
    raise RuntimeErrorWithContext("could not allocate a distinct loopback port")


def test_json_escaping_exec():
    marker = f"agentsight-json-{uuid.uuid4().hex}"
    sess = TracerSession("-m", "0")
    try:
        subprocess.run(
            ["/bin/sh", "-c", f"echo \"{marker} quote\" && printf '\\\\backslash\\n'"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        time.sleep(0.5)
        sess.stop()
        events = sess.events()
        assert_true(any_event_contains(events, marker), "quoted exec command marker was not captured")
    finally:
        sess.cleanup()


def test_pid_filter_tracks_target_tree_only():
    tempdir, target, trigger, done, marker = run_controlled_parent()
    unrelated = f"agentsight-unrelated-{uuid.uuid4().hex}"
    sess = None
    try:
        sess = TracerSession("-m", "2", "-p", str(target.pid), *seed_pid_arg(target.pid))
        open(trigger, "w").close()
        wait_for_file(done)
        subprocess.run(["/bin/echo", unrelated], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
        sess.stop()
        events = sess.events()
        assert_true(any_event_contains(events, marker), "-p did not capture the target child exec")
        assert_true(not any_event_contains(events, unrelated), "-p captured an unrelated process")
    finally:
        if sess:
            sess.cleanup()
        target.terminate()
        target.wait(timeout=5)
        tempdir.cleanup()


def test_session_filter_tracks_session_tree_only():
    tempdir, target, trigger, done, marker = run_controlled_parent(preexec_fn=os.setsid)
    unrelated = f"agentsight-session-unrelated-{uuid.uuid4().hex}"
    sess = None
    try:
        sid = os.getsid(target.pid)
        sess = TracerSession("-m", "2", "--session", str(sid), *seed_pid_arg(target.pid))
        open(trigger, "w").close()
        wait_for_file(done)
        subprocess.run(["/bin/echo", unrelated], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
        sess.stop()
        events = sess.events()
        assert_true(any_event_contains(events, marker), "--session did not capture the target child exec")
        assert_true(not any_event_contains(events, unrelated), "--session captured an unrelated process")
    finally:
        if sess:
            sess.cleanup()
        target.terminate()
        target.wait(timeout=5)
        tempdir.cleanup()


def test_session_filter_does_not_track_out_of_session_command_matches():
    tempdir, target, trigger, done, marker = run_controlled_parent(preexec_fn=os.setsid)
    unrelated = f"agentsight-session-comm-unrelated-{uuid.uuid4().hex}"
    sess = None
    try:
        sid = os.getsid(target.pid)
        sess = TracerSession(
            "-m",
            "2",
            "--session",
            str(sid),
            "-c",
            "echo",
            *seed_pid_arg(target.pid),
        )
        open(trigger, "w").close()
        wait_for_file(done)
        subprocess.run(["/bin/echo", unrelated], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
        sess.stop()
        events = sess.events()
        assert_true(any_event_contains(events, marker), "--session plus -c missed the target child exec")
        assert_true(
            not any_event_contains(events, unrelated),
            "--session plus -c captured an out-of-session command match",
        )
    finally:
        if sess:
            sess.cleanup()
        target.terminate()
        target.wait(timeout=5)
        tempdir.cleanup()


def test_filter_mode_without_selector_does_not_fallback():
    marker = f"agentsight-no-selector-{uuid.uuid4().hex}"
    sess = TracerSession("-m", "2", "--trace-fs")
    try:
        tmp = tempfile.NamedTemporaryFile(prefix=marker, delete=False)
        tmp.write(b"data")
        tmp.close()
        os.unlink(tmp.name)
        subprocess.run(["/bin/echo", marker], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
        sess.stop()
        events = sess.events()
        assert_true(not summary_types(events), "-m 2 without selectors emitted SUMMARY events")
        assert_true(not any_event_contains(events, marker), "-m 2 without selectors captured marker activity")
    finally:
        sess.cleanup()


def test_trace_fs_summary_events():
    sess = TracerSession("-m", "0", "--trace-fs")
    tempdir = tempfile.TemporaryDirectory(prefix="agentsight-runtime-fs-")
    old_cwd = os.getcwd()
    try:
        subdir = os.path.join(tempdir.name, "dir")
        os.mkdir(subdir)
        path = os.path.join(subdir, 'file "quote" \\ slash.txt')
        renamed = os.path.join(subdir, "renamed.txt")
        with open(path, "w") as f:
            f.write("hello")
            f.truncate(2)
        os.rename(path, renamed)
        os.chdir(subdir)
        os.unlink(renamed)
        os.chdir(old_cwd)
        time.sleep(0.5)
        sess.stop()
        types = summary_types(sess.events())
        required = {"DIR_CREATE", "WRITE", "FILE_RENAME", "FILE_DELETE"}
        assert_true(required.issubset(types), f"missing fs SUMMARY types: {sorted(required - types)}")
    finally:
        os.chdir(old_cwd)
        sess.cleanup()
        tempdir.cleanup()


def test_trace_net_summary_events():
    sess = TracerSession("-m", "0", "--trace-net")
    try:
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 0))
        port = server.getsockname()[1]
        server.listen(1)

        client = socket.socket()
        client.connect(("127.0.0.1", port))
        conn, _ = server.accept()
        client.close()
        conn.close()
        server.close()

        time.sleep(0.5)
        sess.stop()
        types = summary_types(sess.events())
        required = {"NET_BIND", "NET_LISTEN", "NET_CONNECT"}
        assert_true(required.issubset(types), f"missing net SUMMARY types: {sorted(required - types)}")
    finally:
        sess.cleanup()


def test_pid_filter_tracks_target_child_network_summary():
    tempdir, target, trigger, done, port_file = run_controlled_network_parent()
    sess = None
    try:
        sess = TracerSession(
            "-m",
            "2",
            "-p",
            str(target.pid),
            *seed_pid_arg(target.pid),
            "--trace-net",
        )
        open(trigger, "w").close()
        wait_for_file(done)
        wait_for_file(port_file)
        with open(port_file, "r", encoding="utf-8") as f:
            target_port = int(f.read().strip())
        unrelated_port = loopback_exchange(exclude_port=target_port)
        time.sleep(0.5)
        sess.stop()
        events = sess.events()
        types = summary_types(events)
        assert_true(
            any(
                event.get("event") == "SUMMARY"
                and event.get("type") == "NET_BIND"
                and f":{target_port}" in event_text(event)
                for event in events
            ),
            f"-p --trace-net missed target child NET_BIND summary for port {target_port}",
        )
        assert_true("NET_LISTEN" in types, "-p --trace-net missed target child NET_LISTEN summary")
        assert_true(
            any(
                event.get("event") == "SUMMARY"
                and event.get("type") == "NET_CONNECT"
                and f":{target_port}" in event_text(event)
                for event in events
            ),
            f"-p --trace-net missed target child NET_CONNECT summary for port {target_port}",
        )
        assert_true(
            not any(f":{unrelated_port}" in event_text(event) for event in events),
            "-p --trace-net captured unrelated loopback network activity",
        )
    finally:
        if sess:
            sess.cleanup()
        target.terminate()
        target.wait(timeout=5)
        tempdir.cleanup()


TESTS = [
    test_json_escaping_exec,
    test_pid_filter_tracks_target_tree_only,
    test_session_filter_tracks_session_tree_only,
    test_session_filter_does_not_track_out_of_session_command_matches,
    test_filter_mode_without_selector_does_not_fallback,
    test_trace_fs_summary_events,
    test_trace_net_summary_events,
    test_pid_filter_tracks_target_child_network_summary,
]


def main():
    if os.geteuid() != 0:
        print("SKIP: process runtime tests require root")
        return 77
    if not os.path.exists(PROCESS):
        print(f"FAIL: missing process binary at {PROCESS}")
        return 1

    failures = 0
    print("Running process runtime tests")
    for test in TESTS:
        name = test.__name__
        try:
            test()
            print(f"[PASS] {name}")
        except Exception as exc:
            failures += 1
            print(f"[FAIL] {name}: {exc}")

    if failures:
        print(f"process runtime tests failed: {failures}/{len(TESTS)}")
        return 1
    print(f"process runtime tests passed: {len(TESTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
