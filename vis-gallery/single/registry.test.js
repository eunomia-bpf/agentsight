import { readFileSync } from "node:fs";
import { init } from "echarts";
import { describe, expect, test } from "vitest";
import { helpers } from "./helpers.js";
import { registry, views } from "./registry.js";
import { parseTime } from "./render.mjs";

const data = JSON.parse(readFileSync(new URL("../tests/fixtures/gallery-data.json", import.meta.url), "utf8"));
const knownModes = new Set(["static", "cursor-marker", "cumulative", "trailing-6h", "endpoint-overlay", "mixed-day"]);

describe("single-view registry", () => {
  test("anchors relative ranges to the selected interval end", () => {
    const end = Date.UTC(2026, 6, 15);
    expect(parseTime("7d", 0, end)).toBe(end - 7 * 86_400_000);
    expect(parseTime("HEAD", end, end)).toBe(end);
  });

  test("contains exactly the 31 preserved visualizations", () => {
    expect(views).toHaveLength(31);
    expect(registry.size).toBe(31);
    expect(new Set(views.map((view) => view.id)).size).toBe(31);
    expect(views.filter((view) => view.timeMode === "static")).toHaveLength(8);
    expect(views.filter((view) => view.timeMode !== "static")).toHaveLength(23);
  });

  test("declares valid, satisfiable data contracts", () => {
    for (const view of views) {
      expect(view.id).toMatch(/^[a-z0-9-]+$/);
      expect(view.title.length).toBeGreaterThan(2);
      expect(view.note.length).toBeGreaterThan(10);
      expect(knownModes.has(view.timeMode), view.id).toBe(true);
      for (const key of view.requirements) expect(data, `${view.id}: ${key}`).toHaveProperty(key);
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
});
