// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import assert from 'node:assert/strict';
import test from 'node:test';
import { RUNNING_WINDOW_MS, isLiveProcess, isRunningSession } from './sessionState.mjs';

const now = Date.parse('2026-11-18T12:00:00Z');
const ago = (ms) => new Date(now - ms).toISOString();

test('a finished conversation on a live host is not running', () => {
  const row = { pid: 4242, session_id: 'old', last_message_at: ago(5 * 24 * 60 * 60_000) };

  assert.equal(isLiveProcess(row), true, 'the host process is alive');
  assert.equal(isRunningSession(row, now), false, 'the conversation is not');
});

test('a conversation written inside the window is running', () => {
  assert.equal(
    isRunningSession({ pid: 4242, session_id: 'current', last_message_at: ago(30_000) }, now),
    true,
  );
  assert.equal(
    isRunningSession({ pid: 4242, session_id: 'current', last_message_at: ago(RUNNING_WINDOW_MS + 1) }, now),
    false,
  );
});

test('a helper process row is not a session', () => {
  assert.equal(isRunningSession({ pid: 4243, session_id: null, last_message_at: ago(1_000) }, now), false);
  assert.equal(isRunningSession({ pid: 4243, last_message_at: ago(1_000) }, now), false);
  assert.equal(isLiveProcess({ pid: 4243 }), true);
});
