import { describe, expect, it } from "vitest";
import { eventVisible, formatCompact, topBy } from "./selectors";
import type { GalleryEvent, ViewState } from "./types";

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
});
