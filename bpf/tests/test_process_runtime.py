#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
#
# Runtime tests for the process eBPF tracer. These tests require root because
# they load BPF programs, but they are intentionally small enough for make test.

import json
import os
import re
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


class SkipRuntimeTest(Exception):
    pass


def seed_pid_arg(pid):
    return ["--seed-pid", f"{pid}:0"]


def has_hidden_host_pids():
    """Detect a container PID namespace using the kernel's trace PID."""
    marker = f"agentsight-pid-namespace-{uuid.uuid4().hex}"
    try:
        with open("/sys/kernel/tracing/trace_marker", "w") as trace:
            trace.write(marker)
        with open("/sys/kernel/tracing/trace", encoding="utf-8") as trace:
            for line in trace:
                if marker in line:
                    match = re.search(r"-(\d+)\s+\[", line)
                    return bool(match and int(match.group(1)) != os.getpid())
    except OSError:
        pass
    return False


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
        with open(self.stdout.name, "r", encoding="utf-8") as f:
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
    if has_hidden_host_pids():
        raise SkipRuntimeTest("PID filter requires the host PID namespace")
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
    if has_hidden_host_pids():
        raise SkipRuntimeTest("session filter requires the host PID namespace")
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

        for _ in range(2):
            client = socket.socket()
            client.connect(("127.0.0.1", port))
            conn, _ = server.accept()
            client.close()
            conn.close()
        server.close()

        auto = socket.socket()
        auto.listen(1)
        auto_port = auto.getsockname()[1]
        auto.close()

        ipv6 = socket.socket(socket.AF_INET6)
        ipv6.bind(("::", 0))
        ipv6_port = ipv6.getsockname()[1]
        ipv6.listen(1)
        ipv6.close()

        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.bind(("127.0.0.1", 0))
        udp_port = udp.getsockname()[1]
        udp.close()

        icmp_port = None
        try:
            icmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_ICMP)
            icmp.bind(("127.0.0.1", 0))
            icmp_port = icmp.getsockname()[1]
            icmp.close()
        except OSError:
            pass  # Ping sockets depend on the host's ping_group_range policy.

        time.sleep(0.5)
        sess.stop()
        events = sess.events()
        types = summary_types(events)
        required = {"NET_BIND", "NET_LISTEN", "NET_CONNECT", "NET_ACCEPT"}
        assert_true(required.issubset(types), f"missing net SUMMARY types: {sorted(required - types)}")
        # Ephemeral ports identify these sockets even when BPF reports host PIDs
        # and this test sees container namespace PIDs.
        binds = [e for e in events if e.get("type") == "NET_BIND"
                 and e.get("port") in {udp_port, icmp_port}]
        assert_true(any(e.get("protocol") == "udp" and e.get("port") == udp_port
                        and e.get("detail") == f"127.0.0.1:{udp_port}" for e in binds),
                    f"missing assigned UDP port: {binds}")
        if icmp_port is not None:
            assert_true(any(e.get("protocol") == "icmp" and e.get("port") == icmp_port
                            for e in binds), f"missing ICMP echo bind: {binds}")
        listeners = [e for e in events if e.get("type") == "NET_LISTEN" and e.get("port") == port]
        assert_true(any(e.get("local_endpoint") == f"127.0.0.1:{port}" for e in listeners),
                    f"missing assigned TCP listener endpoint: {listeners}")
        assert_true(any(e.get("protocol") == "tcp" and e.get("address") == "127.0.0.1"
                        for e in listeners), f"missing structured TCP address: {listeners}")
        assert_true(any(e.get("type") == "NET_LISTEN" and e.get("port") == auto_port
                        and e.get("address") == "0.0.0.0" for e in events),
                    f"missing autobind listener port {auto_port}")
        assert_true(any(e.get("type") == "NET_LISTEN" and e.get("port") == ipv6_port
                        and e.get("address") == "0000:0000:0000:0000:0000:0000:0000:0000"
                        for e in events), f"missing IPv6 port-0 listener {ipv6_port}")
        assert_true(any(e.get("type") == "NET_BIND" and e.get("port") == 0
                        and e.get("address") == "0000:0000:0000:0000:0000:0000:0000:0000"
                        for e in events), f"missing IPv6 bind {ipv6_port}")
        peers = [e for e in events if e.get("type") == "NET_ACCEPT" and
                 e.get("port") == port]
        assert_true(len(peers) == 1 and peers[0].get("count") == 1,
                    f"accepted peer was not deduplicated: {peers}")
        assert_true(peers[0].get("address") == "127.0.0.1" and
                    peers[0].get("peer") == "127.0.0.1", f"missing accept addresses: {peers}")
    finally:
        sess.cleanup()


def test_resolved_file_access():
    tempdir = tempfile.TemporaryDirectory(prefix="agentsight-file-access-")
    path = os.path.join(tempdir.name, "sample.txt")
    missing = os.path.join(tempdir.name, "missing.txt")
    sess = TracerSession("-m", "0")
    try:
        if "resolved file opens unavailable" in sess.stderr_text():
            print("[SKIP] resolved file hook unavailable; syscall fallback active")
            return
        with open(path, "w") as file:
            file.write("data")
        raw_path = os.fsencode(tempdir.name) + b"/bad\xff\xfename"
        with open(raw_path, "wb") as file:
            file.write(b"bytes")
        long_dir = tempdir.name
        for _ in range(6):
            long_dir = os.path.join(long_dir, "d" * 100)
        os.makedirs(long_dir)
        long_path = os.path.join(long_dir, "long.txt")
        with open(long_path, "w") as file:
            file.write("long")
        for _ in range(2):
            with open(path, "r") as file:
                assert file.read() == "data"
        try:
            open(missing, "r").close()
        except FileNotFoundError:
            pass
        subprocess.run(["/bin/true"], check=True)
        time.sleep(0.5)
        sess.stop()
        events = sess.events()
        # The unique temporary path identifies this process even when BPF
        # reports a host PID and Python sees a container namespace PID.
        files = [e for e in events if e.get("event") == "FILE_OPEN"
                 and e.get("filepath") == path]
        assert_true(len([e for e in files if e.get("read")]) == 1,
                    f"expected one deduplicated read: {files}")
        assert_true(len([e for e in files if e.get("write")]) == 1,
                    f"expected one write: {files}")
        assert_true(all(isinstance(e.get("dev"), int) and e.get("ino") for e in files),
                    f"missing real file identity: {files}")
        assert_true(all(e.get("dev_maj_min") ==
                        f"{os.major(e['dev'])}:{os.minor(e['dev'])}" for e in files),
                    f"missing device major:minor: {files}")
        assert_true(any(e.get("filepath_hex") == raw_path.hex() and "\ufffd" in e.get("filepath", "")
                        for e in events if e.get("event") == "FILE_OPEN"),
                    "non-UTF-8 path is not lossless")
        assert_true(any(e.get("filepath") == long_path and not e.get("path_error")
                        for e in events if e.get("event") == "FILE_OPEN"),
                    f"long path missing: {long_path}")
        assert_true(not any(e.get("filepath") == missing for e in events),
                    "failed open was reported")
        assert_true(any(e.get("event") == "FILE_OPEN" and e.get("exec")
                        and e.get("filepath", "").endswith("/true") for e in events),
                    "executable file open was not reported")
    finally:
        sess.cleanup()
        tempdir.cleanup()


def test_probe_heartbeat():
    sess = TracerSession("-m", "0", "--heartbeat", "1")
    try:
        time.sleep(1.2)
        sess.stop()
        records = [e for e in sess.events() if e.get("event") == "PROBE_LIVENESS"]
        assert_true(len(records) >= 2 and records[0].get("kind") == "start" and
                    records[0].get("every") == 1 and records[0].get("trace_net") is False and
                    any(e.get("kind") == "alive" for e in records[1:]),
                    f"missing liveness records: {records}")
    finally:
        sess.cleanup()


TESTS = [
    test_json_escaping_exec,
    test_pid_filter_tracks_target_tree_only,
    test_session_filter_tracks_session_tree_only,
    test_filter_mode_without_selector_does_not_fallback,
    test_trace_fs_summary_events,
    test_trace_net_summary_events,
    test_resolved_file_access,
    test_probe_heartbeat,
]


def main():
    if os.geteuid() != 0:
        print("SKIP: process runtime tests require root")
        return 77
    if not os.path.exists(PROCESS):
        print(f"FAIL: missing process binary at {PROCESS}")
        return 1

    failures = 0
    skipped = 0
    print("Running process runtime tests")
    for test in TESTS:
        name = test.__name__
        try:
            test()
            print(f"[PASS] {name}")
        except SkipRuntimeTest as exc:
            skipped += 1
            print(f"[SKIP] {name}: {exc}")
        except Exception as exc:
            failures += 1
            print(f"[FAIL] {name}: {exc}")

    if failures:
        print(f"process runtime tests failed: {failures}/{len(TESTS)}")
        return 1
    print(f"process runtime tests passed: {len(TESTS) - skipped}; skipped: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
