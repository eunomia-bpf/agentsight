import { init } from "echarts";
import { describe, expect, test } from "vitest";
import { fixtureData as data } from "../tests/fixture-data.mjs";
import { helpers } from "./helpers.js";
import { registry, views } from "./registry.js";
import { animationBounds, animationCursors, parseArgs, parseTime, projectForView } from "./render.mjs";

const knownModes = new Set(["static", "cursor-marker", "cumulative", "trailing-6h", "endpoint-overlay", "mixed-day"]);

describe("single-view registry", () => {
  test("keeps global cross-session matching explicit", () => {
    expect(parseArgs(["--repo", "/repo", "--since", "repo"]).global).toBeUndefined();
    expect(parseArgs(["--repo", "/repo", "--since", "repo", "--global"]).global).toBe(true);
  });

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

  test("replays observed repository growth while attention fades by file-event step", () => {
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
      projected, data.events[1].ts_ms, helpers,
    ));
    expect(focused.focusType).toBe("read");
    expect(focused.age).toBe(0);
    expect(faded.age).toBeGreaterThan(0);
    expect(focused.itemStyle.shadowBlur).toBeGreaterThan(faded.itemStyle.shadowBlur);
    expect(constellation.build(projected, data.events[0].ts_ms, helpers)
      .series.find((series) => series.name === "reads").data).toHaveLength(1);

    const cursors = animationCursors(data, constellation, 6);
    expect(cursors[0]).toBe(data.meta.window_start_ms);
    expect(cursors.at(-1)).toBe(data.meta.window_end_ms);
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
    expect(series(first, "files")).toHaveLength(1);
    expect(endpointCount).toBeGreaterThan(1);
    expect(first.series).toHaveLength(4);
    expect(first.series.every((row) => row.type !== "line" && row.type !== "graph")).toBe(true);
    expect(first.series.some((row) => row.name === "directory labels")).toBe(false);
    expect(series(first, "files")[0].value.slice(0, 2)).toEqual([0.5, 0.5]);
  });

  test("drops pathless commands, processes, model responses, and network while retaining file lifecycle", () => {
    const view = registry.get("workspace-constellation");
    const projected = projectForView(data, view);
    const at = (name, cursor) => view.build(projected, cursor, helpers)
      .series.find((series) => series.name === name).data;
    const event = (id) => data.agent_events.find((row) => row.id === id);

    const names = view.build(projected, event("network-ambient").ts_ms, helpers)
      .series.map((series) => series.name);
    expect(names).toEqual(["files", "reads", "writes", "create / rename / delete"]);
    const durable = data.agent_events.find((row) => row.durable_changes.length);
    expect(at("create / rename / delete", durable.ts_ms).length).toBeGreaterThan(0);
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

    expect(point.bornNear).toBe("src/main.rs");
    expect(Math.hypot(point.value[0] - parent.value[0], point.value[1] - parent.value[1])).toBeLessThan(0.12);
  });

  test("keeps every path from one Tool event in the same visual step", () => {
    const view = registry.get("workspace-constellation");
    const ts = data.meta.window_start_ms + 1;
    const oneTool = {
      meta: data.meta,
      commits: [],
      agent_events: [{
        ...data.agent_events[0], id: "one-tool-two-files", ts_ms: ts,
        paths: ["src/a.rs", "src/b.rs"],
        read_paths: ["src/a.rs", "src/b.rs"], write_paths: [], durable_changes: [],
      }],
    };
    const option = view.build(oneTool, ts, helpers);
    const files = option.series.find((series) => series.name === "files").data;

    expect(files.map((file) => file.path).sort()).toEqual(["src/a.rs", "src/b.rs"]);
    expect(files.every((file) => file.age === 0)).toBe(true);
  });

  test("renders write ripples explicitly in still GIF frames", () => {
    const view = registry.get("workspace-constellation");
    const projected = projectForView(data, view);
    const write = data.events.find((event) => event.effect === "write" && event.path === "src/main.rs");
    const atWrite = view.build(projected, write.ts_ms, helpers);
    const ripples = (option) => option.series.find((row) => row.name === "writes").data;

    expect(ripples(atWrite)).toHaveLength(2);
    expect(ripples(atWrite).every((row) => row.path === write.path)).toBe(true);
  });

  test("projects inferred shell writes onto files without creating command nodes", () => {
    const shellWrite = data.events.find((event) => event.effect === "write" && event.path === "src/main.rs");
    const shellData = {
      ...data,
      agent_events: data.agent_events.map((event) => (
        event.ts_ms === shellWrite.ts_ms && event.paths?.includes(shellWrite.path)
      )
        ? { ...event, category: "shell", action: "exec_command" }
        : event),
    };
    const view = registry.get("workspace-constellation");
    const option = view.build(projectForView(shellData, view), shellWrite.ts_ms, helpers);
    const writes = option.series.find((series) => series.name === "writes").data;
    const file = option.series.find((series) => series.name === "files").data
      .find((row) => row.path === shellWrite.path);

    expect(writes.some((row) => row.path === shellWrite.path)).toBe(true);
    expect(file.source).toBe("bash");
    expect(option.series.some((series) => /command|bash/i.test(series.name))).toBe(false);
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
        [...new Set(["meta", ...view.requirements])].sort(),
      );
    }
  });

  test("renders every view at both ends of the interval as SVG", () => {
    for (const view of views) {
      const projected = Object.fromEntries(
        Object.entries(data).filter(([key]) => new Set(["meta", ...view.requirements]).has(key)),
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
      agent_events: Array.from({ length: 1_200 }, (_, index) => ({
        ...data.agent_events[index % data.agent_events.length],
        id: `dense-source-event-${index}`,
        kind: "tool",
        category: "filesystem",
        effect: index % 3 === 0 ? "write" : "read",
        paths: [`dense/path-${index}.rs`],
        read_paths: index % 3 === 0 ? [] : [`dense/path-${index}.rs`],
        write_paths: index % 3 === 0 ? [`dense/path-${index}.rs`] : [],
        durable_changes: [],
        ts_ms: data.meta.window_start_ms + index,
      })),
    };
    const constellation = registry.get("workspace-constellation").build(dense, data.meta.window_end_ms, helpers);
    const densePoints = constellation.series.find((series) => series.name === "files").data;
    expect(densePoints).toHaveLength(1_200);
    const resting = densePoints.find((point) => point.path === "dense/path-0.rs");
    const focused = densePoints.find((point) => point.path === "dense/path-1199.rs");
    expect(resting.age).toBeGreaterThan(24);
    expect(resting.symbolSize).toBeLessThan(5);
    expect(focused.symbolSize).toBeGreaterThan(resting.symbolSize);
    const edgePoints = densePoints.filter((point) => (
      point.value[0] <= 0.021 || point.value[0] >= 0.979
      || point.value[1] <= 0.021 || point.value[1] >= 0.979
    ));
    expect(edgePoints.length / densePoints.length).toBeLessThan(0.1);
  });

  test("keeps both treemap and nebula observed-only", () => {
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
    const untrackedEvent = {
      ...data.agent_events[0], id: "untracked-event", ts_ms: data.events[0].ts_ms + 1,
      paths: [untrackedNoise.path], write_paths: [untrackedNoise.path], durable_changes: [],
    };
    const expanded = {
      ...data,
      files: [...data.files, unseen, untrackedNoise],
      agent_events: [...data.agent_events, untrackedEvent].sort((a, b) => a.ts_ms - b.ts_ms),
    };
    const view = registry.get("workspace-constellation");
    const projected = projectForView(expanded, view);
    expect(projected.files).toBeUndefined();
    expect(projected.file_lifetimes).toBeUndefined();
    const option = view.build(projected, data.events[0].ts_ms + 16 * 60_000, helpers);
    const paths = new Set(option.series.find((series) => series.name === "files").data.map((row) => row.path));
    expect(paths.has(unseen.path)).toBe(false);
    expect(paths.has(untrackedNoise.path)).toBe(true);
  });
});
