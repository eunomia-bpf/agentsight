#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

import json
import os
import re
import selectors
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


BPF_DIR = Path(__file__).resolve().parents[1]
SSLSNIFF = BPF_DIR / "sslsniff"
FIXTURE = BPF_DIR / "test_sslsniff_transport_identity"
MAIN_MARKERS = [
    "identity-main-a-1",
    "identity-main-b-1",
    "identity-main-a-2",
    "identity-main-b-2",
]
CAPTURE_LIMIT = 256 * 1024
TRUNCATED_PAYLOAD_SIZE = CAPTURE_LIMIT + 17
TRUNCATED_PREFIX = "identity-truncated-a"


class RuntimeTestError(AssertionError):
    pass


def assert_true(condition, message):
    if not condition:
        raise RuntimeTestError(message)


def read_line_with_timeout(stream, timeout):
    selector = selectors.DefaultSelector()
    selector.register(stream, selectors.EVENT_READ)
    try:
        if not selector.select(timeout):
            raise RuntimeTestError("timed out waiting for fixture readiness")
        line = stream.readline()
    finally:
        selector.close()
    if not line:
        raise RuntimeTestError("fixture exited before reporting readiness")
    return line.strip()


def parse_fields(line, prefix):
    assert_true(line.startswith(prefix), f"unexpected fixture output: {line!r}")
    return dict(re.findall(r"([a-z_]+)=([^ ]+)", line))


def load_events(path):
    events = []
    bad_lines = []
    with open(path, "r", encoding="utf-8", errors="replace") as stream:
        for lineno, line in enumerate(stream, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                bad_lines.append((lineno, str(exc), line[:200]))
    assert_true(not bad_lines, f"invalid JSON output: {bad_lines[:3]}")
    return events


def find_data_event(events, marker):
    matches = [event for event in events if event.get("data") == marker]
    assert_true(len(matches) == 1, f"expected one event for {marker!r}, got {len(matches)}")
    return matches[0]


def parse_handle(value):
    assert_true(isinstance(value, str) and value.startswith("0x"),
                f"invalid transport_handle: {value!r}")
    return int(value, 16)


def assert_common_metadata(events, pid):
    assert_true(events, "sslsniff emitted no events")
    assert_true(all(event.get("pid") == pid for event in events),
                "PID filter allowed an event from another process")
    assert_true(all(event.get("tls_library") == "openssl" for event in events),
                "TLS library identity was not propagated as openssl")

    process_starts = {event.get("process_start_ns") for event in events}
    assert_true(len(process_starts) == 1 and next(iter(process_starts)) > 0,
                f"invalid process-instance identities: {process_starts}")

    capture_sequences = [event.get("capture_seq") for event in events]
    assert_true(capture_sequences == list(range(1, len(events) + 1)),
                f"capture_seq is not contiguous output order: {capture_sequences}")

    for event in events:
        failures = event.get("ringbuf_reserve_failures")
        assert_true(isinstance(failures, int) and failures >= 0,
                    f"invalid capture-loss metadata: {event}")
        assert_true(parse_handle(event.get("transport_handle")) > 0,
                    f"missing TLS transport identity: {event}")
        assert_true("connection_closed" in event, f"missing lifecycle metadata: {event}")


def assert_payload_metadata(event, marker, function):
    marker_len = len(marker.encode())
    assert_true(event.get("function") == function, f"unexpected direction for {marker}: {event}")
    assert_true(event.get("len") == marker_len, f"wrong original length for {marker}: {event}")
    assert_true(event.get("buf_size") == marker_len, f"wrong captured length for {marker}: {event}")
    assert_true(event.get("truncated") is False, f"unexpected truncation for {marker}: {event}")
    assert_true("bytes_lost" not in event, f"unexpected loss count for {marker}: {event}")


def run_test():
    fixture = subprocess.Popen(
        [str(FIXTURE)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    tracer = None
    stdout_file = tempfile.NamedTemporaryFile(
        prefix="sslsniff-transport-", suffix=".jsonl", delete=False
    )
    stderr_file = tempfile.NamedTemporaryFile(
        prefix="sslsniff-transport-", suffix=".stderr", delete=False
    )
    stdout_path = stdout_file.name
    stderr_path = stderr_file.name
    stdout_file.close()
    stderr_file.close()

    try:
        ready = parse_fields(read_line_with_timeout(fixture.stdout, 5), "READY")
        pid = int(ready["pid"])
        main_tid = int(ready["main_tid"])
        handle_a = int(ready["handle_a"], 16)
        handle_b = int(ready["handle_b"], 16)
        assert_true(handle_a != handle_b, "fixture TLS handles are not distinct")

        with open(stdout_path, "wb") as tracer_stdout, open(stderr_path, "wb") as tracer_stderr:
            tracer = subprocess.Popen(
                [
                    str(SSLSNIFF),
                    "--no-openssl",
                    "--handshake",
                    "--pid",
                    str(pid),
                    "--binary-path",
                    str(FIXTURE),
                ],
                stdout=tracer_stdout,
                stderr=tracer_stderr,
            )

        time.sleep(1.5)
        if tracer.poll() is not None:
            with open(stderr_path, "r", encoding="utf-8", errors="replace") as stream:
                raise RuntimeTestError(
                    f"sslsniff exited during attach with {tracer.returncode}: {stream.read()}"
                )

        fixture.stdin.write("x")
        fixture.stdin.flush()
        remaining_stdout, fixture_stderr = fixture.communicate(timeout=10)
        assert_true(fixture.returncode == 0,
                    f"fixture failed with {fixture.returncode}: {fixture_stderr}")
        lines = [line.strip() for line in remaining_stdout.splitlines() if line.strip()]
        assert_true(len(lines) >= 2, f"fixture did not report worker TIDs: {lines}")
        worker_fields = parse_fields(lines[0], "THREADS")
        write_tid = int(worker_fields["write_tid"])
        read_tid = int(worker_fields["read_tid"])
        assert_true(write_tid != read_tid, "fixture workers unexpectedly shared a TID")

        time.sleep(0.5)
        tracer.send_signal(signal.SIGINT)
        tracer.wait(timeout=10)
        assert_true(tracer.returncode == 0, f"sslsniff exited with {tracer.returncode}")

        events = load_events(stdout_path)
        assert_common_metadata(events, pid)

        main_events = [event for event in events if event.get("data") in MAIN_MARKERS]
        assert_true(len(main_events) == len(MAIN_MARKERS),
                    f"missing main-thread events: {main_events}")
        assert_true([event["data"] for event in main_events] == MAIN_MARKERS,
                    "main-thread A/B/A/B event ordering changed")
        assert_true(all(event.get("tid") == main_tid for event in main_events),
                    "alternating TLS handles did not retain the same TID")
        assert_true(
            [parse_handle(event["transport_handle"]) for event in main_events]
            == [handle_a, handle_b, handle_a, handle_b],
            "one-TID A/B/A/B transport identities were not preserved",
        )
        for event, marker in zip(main_events, MAIN_MARKERS):
            assert_payload_metadata(event, marker, "WRITE/SEND")

        truncated_events = [
            event for event in events
            if isinstance(event.get("data"), str)
            and event["data"].startswith(TRUNCATED_PREFIX)
        ]
        assert_true(len(truncated_events) == 1,
                    f"expected one deliberately truncated event, got {len(truncated_events)}")
        truncated = truncated_events[0]
        assert_true(truncated.get("tid") == main_tid,
                    f"truncated event has wrong TID: {truncated}")
        assert_true(parse_handle(truncated["transport_handle"]) == handle_a,
                    f"truncated event lost transport identity: {truncated}")
        assert_true(truncated.get("len") == TRUNCATED_PAYLOAD_SIZE,
                    f"wrong original length on truncated event: {truncated.get('len')}")
        assert_true(truncated.get("buf_size") == CAPTURE_LIMIT,
                    f"wrong captured length on truncated event: {truncated.get('buf_size')}")
        assert_true(truncated.get("truncated") is True,
                    "oversized payload was not marked truncated")
        assert_true(truncated.get("bytes_lost") == 17,
                    f"wrong truncation loss count: {truncated.get('bytes_lost')}")

        thread_write = find_data_event(events, "identity-thread-write-a")
        thread_read = find_data_event(events, "identity-thread-read-a")
        assert_true(thread_write.get("tid") == write_tid,
                    f"write event has wrong TID: {thread_write}")
        assert_true(thread_read.get("tid") == read_tid,
                    f"read event has wrong TID: {thread_read}")
        assert_true(parse_handle(thread_write["transport_handle"]) == handle_a,
                    f"write event lost shared handle: {thread_write}")
        assert_true(parse_handle(thread_read["transport_handle"]) == handle_a,
                    f"read event lost shared handle: {thread_read}")
        assert_payload_metadata(thread_write, "identity-thread-write-a", "WRITE/SEND")
        assert_payload_metadata(thread_read, "identity-thread-read-a", "READ/RECV")

        handshakes = [event for event in events if event.get("is_handshake") is True]
        assert_true(len(handshakes) == 1, f"expected one handshake event, got {handshakes}")
        handshake = handshakes[0]
        assert_true(parse_handle(handshake["transport_handle"]) == handle_a,
                    f"handshake lost transport identity: {handshake}")
        assert_true(handshake.get("len") == 1 and handshake.get("buf_size") == 0,
                    f"unexpected handshake length metadata: {handshake}")
        assert_true(handshake.get("truncated") is False,
                    f"handshake result was misreported as payload truncation: {handshake}")
        assert_true("bytes_lost" not in handshake,
                    f"handshake result was misreported as payload loss: {handshake}")

        closes = [event for event in events if event.get("connection_closed") is True]
        assert_true(len(closes) == 2, f"expected two close events, got {closes}")
        assert_true(
            [parse_handle(event["transport_handle"]) for event in closes]
            == [handle_a, handle_b],
            f"close lifecycle identities were not preserved: {closes}",
        )
    finally:
        if tracer and tracer.poll() is None:
            tracer.send_signal(signal.SIGINT)
            try:
                tracer.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tracer.kill()
                tracer.wait(timeout=5)
        if fixture.poll() is None:
            fixture.kill()
            fixture.wait(timeout=5)
        for path in (stdout_path, stderr_path):
            try:
                os.unlink(path)
            except OSError:
                pass


def main():
    if os.geteuid() != 0:
        print("sslsniff transport identity runtime test requires root", file=sys.stderr)
        return 1
    for path in (SSLSNIFF, FIXTURE):
        if not path.exists():
            print(f"missing test binary: {path}", file=sys.stderr)
            return 1
    run_test()
    print("sslsniff transport identity runtime tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
