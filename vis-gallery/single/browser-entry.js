import { init, use } from "echarts/core";
import {
  BarChart, GraphChart, HeatmapChart, LineChart, PieChart,
  SankeyChart, ScatterChart, ThemeRiverChart, TreemapChart,
} from "echarts/charts";
import {
  AxisPointerComponent, DataZoomComponent, GraphicComponent, GridComponent,
  LegendComponent, MarkLineComponent, SingleAxisComponent, TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import { helpers } from "./helpers.js";
import { requireView, views } from "./registry.js";

use([
  BarChart, GraphChart, HeatmapChart, LineChart, PieChart, SankeyChart,
  ScatterChart, ThemeRiverChart, TreemapChart, AxisPointerComponent,
  DataZoomComponent, GraphicComponent, GridComponent, LegendComponent,
  MarkLineComponent, SingleAxisComponent, TooltipComponent,
  VisualMapComponent, SVGRenderer,
]);

let chart;
let state;
let frame;
const element = (id) => document.querySelector(`#${id}`);

function timeLabel(value) {
  return new Date(value).toISOString().replace("T", " ").replace(".000Z", " UTC");
}

function dayLabel(value) {
  return new Date(value).toISOString().slice(0, 10);
}

function renderAt(cursorMs) {
  state.cursorMs = Math.max(state.startMs, Math.min(state.endMs, Number(cursorMs)));
  const option = state.view.build(state.data, state.cursorMs, helpers);
  chart.setOption(option, { notMerge: true, lazyUpdate: false });
  element("timeline").value = String(state.cursorMs);
  element("cursor-label").textContent = timeLabel(state.cursorMs);
  window.__AGENTSIGHT_CURSOR__ = state.cursorMs;
  return state.cursorMs;
}

function stop() {
  if (frame) cancelAnimationFrame(frame);
  frame = 0;
  element("play").textContent = "▶";
}

function togglePlayback() {
  if (frame) return stop();
  if (state.cursorMs >= state.endMs) renderAt(state.startMs);
  const started = performance.now();
  const cursorStart = state.cursorMs;
  element("play").textContent = "Ⅱ";
  const tick = (now) => {
    const fraction = Math.min(1, (now - started) / 10_000);
    renderAt(cursorStart + (state.endMs - cursorStart) * fraction);
    if (fraction >= 1) return stop();
    frame = requestAnimationFrame(tick);
  };
  frame = requestAnimationFrame(tick);
}

function initialize(data, viewId, config = {}) {
  const view = requireView(viewId);
  const startMs = data.meta.window_start_ms;
  const endMs = data.meta.window_end_ms;
  state = { data, view, startMs, endMs, cursorMs: config.cursorMs ?? endMs };
  document.title = `${view.title} · AgentSight`;
  element("view-title").textContent = view.title;
  element("view-note").textContent = view.note;
  element("time-mode").textContent = view.timeMode.replaceAll("-", " ");
  element("provenance").textContent = [
    `repository: ${data.meta.repository}`,
    `revision: ${data.meta.endpoint_revision.slice(0, 12)}`,
    `window: ${dayLabel(startMs)} → ${dayLabel(endMs)}`,
    "generator: agentsight-vis 0.1",
    `association mode: ${data.meta.association_mode.replaceAll("_", " ")}`,
  ].join(" · ");
  const timeline = element("timeline");
  Object.assign(timeline, { min: String(startMs), max: String(endMs), step: "1" });
  timeline.addEventListener("input", () => {
    stop();
    renderAt(Number(timeline.value));
  });
  const play = element("play");
  play.addEventListener("click", togglePlayback);
  if (view.timeMode === "static") {
    timeline.disabled = true;
    play.disabled = true;
    play.title = "This view represents the frozen endpoint or complete interval";
  }
  chart = init(element("chart"), null, {
    renderer: config.renderer ?? "svg",
    width: config.width ?? 1400,
    height: config.height ?? 760,
  });
  renderAt(state.cursorMs);
  window.__AGENTSIGHT_READY__ = true;
}

globalThis.AgentSightSingle = {
  initialize,
  renderAt,
  stop,
  viewIds: views.map((view) => view.id),
};
