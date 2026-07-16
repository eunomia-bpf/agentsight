import { init } from "echarts";
import { describe, expect, test } from "vitest";
import { fixtureData as data } from "../tests/fixture-data.mjs";
import { helpers } from "./helpers.js";
import { registry, views } from "./registry.js";
import { animationBounds, animationCursors, parseTime, projectForView } from "./render.mjs";

const knownModes = new Set(["static", "cursor-marker", "cumulative", "trailing-6h", "endpoint-overlay", "mixed-day"]);

describe("single-view registry", () => {
  test("anchors relative ranges to the selected interval end", () => {
    const end = Date.UTC(2026, 6, 15);
    expect(parseTime("7d", 0, end)).toBe(end - 7 * 86_400_000);
    expect(parseTime("HEAD", end, end)).toBe(end);
  });

  test("samples shareable animations over each view's observed evidence", () => {
    const view = registry.get("session-storylines");
    expect(animationBounds(data, view)).toEqual([
      data.events[0].ts_ms,
      data.verification_events.at(-1).ts_ms,
    ]);
    expect(animationBounds({ ...data, events: [], verification_events: [], sessions: [] }, view)).toEqual([
      data.meta.window_start_ms,
      data.meta.window_end_ms,
    ]);
  });

  test("replays observed repository growth while recent attention fades", () => {
    const treemap = registry.get("repository-treemap");
    const first = treemap.build(projectForView(data, treemap), data.events[0].ts_ms, helpers);
    const last = treemap.build(projectForView(data, treemap), data.events.at(-1).ts_ms, helpers);
    const leafCount = (rows) => rows.reduce((count, row) => (
      count + (row.children?.length ? leafCount(row.children) : 1)
    ), 0);
    expect(leafCount(first.series[0].data)).toBeLessThan(leafCount(last.series[0].data));

    const constellation = registry.get("workspace-constellation");
    const path = data.events[0].path;
    const filePoint = (option) => option.series.find((series) => series.name === "files")
      .data.find((row) => row.path === path);
    const focused = filePoint(constellation.build(
      projectForView(data, constellation), data.events[0].ts_ms, helpers,
    ));
    const faded = filePoint(constellation.build(
      projectForView(data, constellation), data.events[0].ts_ms + 31 * 60_000, helpers,
    ));
    expect(focused.focus.effect).toBe("read");
    expect(faded.focus).toBeUndefined();
    expect(focused.itemStyle.shadowBlur).toBeGreaterThan(faded.itemStyle.shadowBlur);

    const cursors = animationCursors(data, constellation, 6);
    expect(cursors[0]).toBe(data.events[0].ts_ms);
    expect(cursors.at(-1)).toBe(data.verification_events.at(-1).ts_ms);
    expect(cursors.every((cursor) => cursor >= cursors[0] && cursor <= cursors.at(-1))).toBe(true);
  });

  test("contains exactly the 31 preserved visualizations", () => {
    expect(views).toHaveLength(31);
    expect(registry.size).toBe(31);
    expect(new Set(views.map((view) => view.id)).size).toBe(31);
    expect(views.filter((view) => view.timeMode === "static")).toHaveLength(9);
    expect(views.filter((view) => view.timeMode !== "static")).toHaveLength(22);
  });

  test("declares valid, satisfiable data contracts", () => {
    for (const view of views) {
      expect(view.id).toMatch(/^[a-z0-9-]+$/);
      expect(view.title.length).toBeGreaterThan(2);
      expect(view.note.length).toBeGreaterThan(10);
      expect(knownModes.has(view.timeMode), view.id).toBe(true);
      for (const key of view.requirements) expect(data, `${view.id}: ${key}`).toHaveProperty(key);
      expect(Object.keys(projectForView(data, view)).sort()).toEqual(
        [...new Set(["schema", "meta", "summary", ...view.requirements])].sort(),
      );
    }
  });

  test("renders every view at both ends of the interval as SVG", () => {
    for (const view of views) {
      const projected = Object.fromEntries(
        Object.entries(data).filter(([key]) => new Set(["schema", "meta", "summary", ...view.requirements]).has(key)),
      );
      for (const cursor of [data.meta.window_start_ms, data.meta.window_end_ms]) {
        const chart = init(null, null, { renderer: "svg", ssr: true, width: 1000, height: 600 });
        chart.setOption(view.build(projected, cursor, helpers));
        const svg = chart.renderToSVGString();
        expect(svg, `${view.id}@${cursor}`).toContain("<svg");
        expect(svg.length, view.id).toBeGreaterThan(300);
        chart.dispose();
      }
    }
  });

  test("explains missing native-session evidence instead of drawing blank axes", () => {
    const empty = {
      ...data,
      events: [],
      verification_events: [],
      sessions: [],
      source_days: [],
      time_buckets: [],
    };
    const ids = [
      "activity-pulse", "observed-days", "hot-paths", "touch-association-lanes",
      "path-day-matrix", "association-state-matrix", "read-before-write-network",
      "session-storylines", "trajectory-cast", "activity-punch-card", "agent-vitals",
      "vendor-semantic-flow", "verification-lag", "session-receipt", "mature-day-comparison",
    ];
    for (const id of ids) {
      const view = registry.get(id);
      const option = view.build(projectForView(empty, view), data.meta.window_end_ms, helpers);
      expect(option.graphic?.[0]?.style?.text, id).toMatch(/^No /);
    }
  });

  test("bounds dense repository views for readable single-file output", () => {
    const lineAge = registry.get("line-age-pixels").build(data, data.meta.window_end_ms, helpers);
    expect(lineAge.yAxis.data.length).toBeLessThanOrEqual(26);
    expect(lineAge.xAxis.data.length).toBeLessThanOrEqual(160);

    const dense = {
      ...data,
      files: Array.from({ length: 1_200 }, (_, index) => ({
        ...data.files[index % data.files.length],
        path: `dense/path-${index}.rs`,
        stable_x: (index % 40) / 40,
        stable_y: Math.floor(index / 40) / 30,
      })),
      events: Array.from({ length: 1_200 }, (_, index) => ({
        ...data.events[index % data.events.length],
        id: `dense-event-${index}`,
        path: `dense/path-${index}.rs`,
        group: "dense",
        ts_ms: data.meta.window_start_ms + index,
      })),
    };
    const constellation = registry.get("workspace-constellation").build(dense, data.meta.window_end_ms, helpers);
    expect(constellation.series.find((series) => series.name === "files").data).toHaveLength(1_200);
  });
});
