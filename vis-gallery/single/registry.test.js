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
    const projected = projectForView(data, constellation);
    const path = data.events[0].path;
    const filePoint = (option) => option.series.find((series) => series.name === "files")
      .data.find((row) => row.path === path);
    const focused = filePoint(constellation.build(
      projected, data.events[0].ts_ms, helpers,
    ));
    const faded = filePoint(constellation.build(
      projected, data.events[0].ts_ms + 31 * 60_000, helpers,
    ));
    expect(focused.focus.effect).toBe("read");
    expect(faded.focus).toBeUndefined();
    expect(focused.itemStyle.shadowBlur).toBeGreaterThan(faded.itemStyle.shadowBlur);
    expect(constellation.build(projected, data.events[0].ts_ms, helpers)
      .series.find((series) => series.name === "active file cores").data).toHaveLength(1);
    expect(constellation.build(projected, data.events[0].ts_ms + 31 * 60_000, helpers)
      .series.find((series) => series.name === "active file cores").data).toHaveLength(0);

    const cursors = animationCursors(data, constellation, 6);
    expect(cursors[0]).toBe(data.events[0].ts_ms - 1);
    expect(cursors.at(-1)).toBe(data.verification_events.at(-1).ts_ms);
    expect(cursors.every((cursor) => cursor >= cursors[0] && cursor <= cursors.at(-1))).toBe(true);
    expect(cursors.some((cursor) => data.commits.some((commit) => commit.committed_at_ms === cursor))).toBe(true);
    const visual = new Set(constellation.visualMoments(data));
    const commitOnly = data.commits.find((commit) => !visual.has(commit.committed_at_ms));
    expect(commitOnly).toBeDefined();
    expect(constellation.playbackMoments(data)).toContain(commitOnly.committed_at_ms);
  });

  test("starts the nebula empty and never draws file-to-file edges", () => {
    const view = registry.get("workspace-constellation");
    const projected = projectForView(data, view);
    const before = view.build(projected, data.events[0].ts_ms - 1, helpers);
    const first = view.build(projected, data.events[0].ts_ms, helpers);
    const series = (option, name) => option.series.find((row) => row.name === name).data;
    const endpointCount = data.files.filter((file) => file.survives_to_head && file.current_path === file.path).length;

    expect(series(before, "files")).toHaveLength(0);
    expect(series(before, "repository context")).toHaveLength(0);
    expect(series(before, "directory color field")).toHaveLength(0);
    expect(series(first, "files")).toHaveLength(1);
    expect(series(first, "repository context")).toHaveLength(endpointCount - 1);
    expect(series(first, "directory color field").length).toBeGreaterThanOrEqual(3);
    expect(first.series.every((row) => row.type !== "line" && row.type !== "graph")).toBe(true);
    expect(first.series.some((row) => row.name === "directory labels")).toBe(false);
  });

  test("births a path-near file beside the closest previously observed star", () => {
    const view = registry.get("workspace-constellation");
    const projected = projectForView(data, view);
    const second = data.events.find((event) => event.path === "src/lib.rs");
    const option = view.build(projected, second.ts_ms, helpers);
    const point = option.series.find((series) => series.name === "files")
      .data.find((row) => row.path === second.path);
    const parent = option.series.find((series) => series.name === "files")
      .data.find((row) => row.path === "src/main.rs");

    expect(point.parent).toBe("src/main.rs");
    expect(Math.hypot(point.value[0] - parent.value[0], point.value[1] - parent.value[1])).toBeLessThan(0.03);
  });

  test("renders write ripples explicitly in still GIF frames", () => {
    const view = registry.get("workspace-constellation");
    const projected = projectForView(data, view);
    const write = data.events.find((event) => event.effect === "write");
    const atWrite = view.build(projected, write.ts_ms, helpers);
    const afterRipple = view.build(projected, write.ts_ms + 4 * 60_000, helpers);
    const ripples = (option) => option.series.find((row) => row.name === "recent writes").data;

    expect(ripples(atWrite)).toHaveLength(3);
    expect(ripples(afterRipple)).toHaveLength(0);
  });

  test("keeps recorded shell path effects visually distinct without calling them creation", () => {
    const shellWrite = data.events.find((event) => event.effect === "write");
    const shellData = {
      ...data,
      events: data.events.map((event) => event.id === shellWrite.id
        ? { ...event, category: "shell", action: "exec_command" }
        : event),
    };
    const view = registry.get("workspace-constellation");
    const option = view.build(projectForView(shellData, view), shellWrite.ts_ms, helpers);
    const command = option.series.find((series) => series.name === "command-associated effects").data;
    const directWrites = option.series.find((series) => series.name === "recent writes").data;

    expect(command.length).toBeGreaterThan(0);
    expect(command.every((row) => row.symbol === "diamond")).toBe(true);
    expect(directWrites.every((row) => row.path !== shellWrite.path)).toBe(true);
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

  test("keeps the treemap observed-only but embeds full tracked context for the nebula", () => {
    const treemap = projectForView(data, registry.get("repository-treemap"));
    expect(new Set(treemap.files.map((file) => file.path))).toEqual(
      new Set(data.events.map((event) => event.path)),
    );

    const unseen = {
      ...data.files[0],
      path: "src/unseen.rs",
      current_path: "src/unseen.rs",
      lifetime_id: "life-unseen",
      lifetime_ids: ["life-unseen"],
    };
    const untrackedNoise = {
      ...data.files[0],
      path: "target/generated.tmp",
      current_path: null,
      survives_to_head: false,
      lifetime_id: null,
      lifetime_ids: [],
    };
    const expanded = { ...data, files: [...data.files, unseen, untrackedNoise] };
    const view = registry.get("workspace-constellation");
    const projected = projectForView(expanded, view);
    expect(projected.files.some((file) => file.path === unseen.path)).toBe(true);
    const option = view.build(projected, data.events[0].ts_ms + 16 * 60_000, helpers);
    const contextPaths = new Set(option.series.find((series) => series.name === "repository context").data.map((row) => row.path));
    expect(contextPaths.has(unseen.path)).toBe(true);
    expect(contextPaths.has(untrackedNoise.path)).toBe(false);
  });
});
