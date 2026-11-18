// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

/** A conversation this recently active still counts as running. */
export const RUNNING_WINDOW_MS = 3 * 60_000;

/**
 * A live row is a process tree with a pid. A long-lived agent host keeps
 * helper processes (renderer, GPU, network) in that tree, so a live pid on its
 * own says nothing about a session being active.
 *
 * @param {{ pid?: number | null } | null} row
 */
export function isLiveProcess(row) {
  return typeof row?.pid === 'number' && row.pid > 0;
}

/**
 * A row a session owns. Process rows carry no `session_id`; the session rows
 * built from agent-native transcripts always do.
 *
 * @param {{ pid?: number | null, session_id?: string | null } | null} row
 */
export function isSessionRow(row) {
  return isLiveProcess(row) && typeof row?.session_id === 'string' && row.session_id !== '';
}

function observedAt(row) {
  const raw = row?.last_message_at;
  if (typeof raw !== 'string' || raw === '') return null;
  const parsed = Date.parse(raw);
  return Number.isFinite(parsed) ? parsed : null;
}

/**
 * Match the per-session running-state contract everywhere in the UI. A live
 * pid bound to a session is not proof of work: an agent host keeps its log
 * open after a conversation finishes, so an old conversation would otherwise
 * report as running for as long as the host lives. Require the conversation to
 * have been written to inside the running window as well. A row with no
 * recorded activity time keeps the older behaviour rather than dropping out of
 * the count.
 *
 * @param {{ pid?: number | null, session_id?: string | null, last_message_at?: string | null } | null} row
 * @param {number} [now]
 */
export function isRunningSession(row, now = Date.now()) {
  if (!isSessionRow(row)) return false;
  const last = observedAt(row);
  return last === null || now - last < RUNNING_WINDOW_MS;
}