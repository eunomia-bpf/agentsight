import { describe, expect, it } from "vitest";
import { completedSessionsInVisibleInterval, eventVisible, formatCompact, linePixelVisible, projectOrderedEdges, projectTimeBuckets, topBy } from "./selectors";
import type { GalleryEvent, GallerySession, ViewState } from "./types";

const event: GalleryEvent = {
  id: "1", event_id: "1", session_id: "s", vendor: "codex", model: "m",
  ts_ms: 20, day: "2026-06-02", action: "read", category: "filesystem",
  effect: "read", status: "ok", prompt_index: 0, path: "src/a.rs", group: "src",
  association_state: "not_eligible", candidate_count: 0, evidence_bin: null, exact_hunk: false,
};
const state: ViewState = { family: "overview", cursorMs: 30, rangeStartMs: 10, rangeEndMs: 40, playing: false, speedHoursPerSecond: 1, vendors: new Set(), associationStates: new Set(), selectedPath: null, selectedSession: null };

describe("gallery selectors", () => {
  it("honors cursor, vendor, path, and session filters", () => {
    expect(eventVisible(event, state)).toBe(true);
    expect(eventVisible(event, { ...state, cursorMs: 19 })).toBe(false);
    expect(eventVisible(event, { ...state, vendors: new Set(["claude"]) })).toBe(false);
    expect(eventVisible(event, { ...state, selectedPath: "src/b.rs" })).toBe(false);
    expect(eventVisible(event, { ...state, selectedSession: "other" })).toBe(false);
  });
  it("sorts without mutating input", () => {
    const rows = [{ n: 1 }, { n: 3 }, { n: 2 }];
    expect(topBy(rows, (row) => row.n, 2).map((row) => row.n)).toEqual([3, 2]);
    expect(rows.map((row) => row.n)).toEqual([1, 3, 2]);
  });
  it("formats compact values", () => expect(formatCompact(6535)).toMatch(/6[.,]?5K/i));
  it("counts reported units only after the whole session is visible", () => {
    const sessions: GallerySession[] = [
      { id: "s", vendor: "codex", model: "m", started_at_ms: 15, ended_at_ms: 25, tool_events: 1, reported_tokens: 100, days: ["2026-06-02"] },
      { id: "later", vendor: "codex", model: "m", started_at_ms: 15, ended_at_ms: 35, tool_events: 1, reported_tokens: 200, days: ["2026-06-02"] },
    ];
    const rows = [event, { ...event, id: "2", session_id: "later" }];
    expect(completedSessionsInVisibleInterval(sessions, rows, state).map((row) => row.id)).toEqual(["s"]);
    expect(completedSessionsInVisibleInterval(sessions, rows, { ...state, cursorMs: 20 })).toEqual([]);
  });
  it("does not project endpoint lines before their Git origin", () => {
    const pixel = { path: "src/a.rs", line: 1, origin_commit: "abc", origin_ms: 50, author_label: "author-1" };
    expect(linePixelVisible(pixel, 49)).toBe(false);
    expect(linePixelVisible(pixel, 50)).toBe(true);
  });
  it("reprojects ordered edges from the filtered event set", () => {
    const rows = [
      event,
      { ...event, id: "2", event_id: "2", ts_ms: 21, action: "write", effect: "write", path: "src/b.rs" },
      { ...event, id: "3", event_id: "3", ts_ms: 22, vendor: "claude", action: "write", effect: "write", path: "src/c.rs" },
    ];
    const all = projectOrderedEdges(rows);
    const codex = projectOrderedEdges(rows.filter((row) => row.vendor === "codex"));
    expect(all.map((edge) => edge.target)).toEqual(["src/b.rs"]);
    expect(codex).toEqual(all);
    expect(projectOrderedEdges(rows.filter((row) => row.vendor === "claude"))).toEqual([]);
  });
  it("reprojects hourly vital signs from visible events", () => {
    const rows = [event, { ...event, id: "2", ts_ms: 3_600_020, effect: "write" }];
    expect(projectTimeBuckets(rows)).toEqual([
      { ts_ms: 0, events: 1, read: 1 },
      { ts_ms: 3_600_000, events: 1, write: 1 },
    ]);
  });
});
