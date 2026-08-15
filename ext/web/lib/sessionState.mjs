// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

/**
 * Match the per-session running-state contract everywhere in the UI.
 * A process count alone cannot prove that the session root is still alive.
 *
 * @param {{ pid?: number | null } | null} row
 */
export function isRunningSession(row) {
  return typeof row?.pid === 'number' && row.pid > 0;
}
