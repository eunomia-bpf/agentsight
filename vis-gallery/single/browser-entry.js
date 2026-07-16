import { init, use } from "echarts/core";
import {
  BarChart, EffectScatterChart, GraphChart, HeatmapChart, LineChart, PieChart,
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
  BarChart, EffectScatterChart, GraphChart, HeatmapChart, LineChart, PieChart, SankeyChart,
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
  const requested = Number(cursorMs);
  if (!Number.isFinite(requested)) return state.cursorMs;
  state.cursorMs = Math.max(state.startMs, Math.min(state.endMs, requested));
  const option = state.view.build(state.data, state.cursorMs, helpers);
  if (state.reducedMotion) {
    option.animation = false;
    for (const series of option.series ?? []) {
      Object.assign(series, {
        animation: false, animationDuration: 0, animationDurationUpdate: 0,
      });
    }
  }
  chart.setOption(option, { notMerge: true, lazyUpdate: false });
  if (state.reducedMotion) chart.getZr().flush();
  element("timeline").value = String(state.cursorMs);
  element("cursor-label").textContent = timeLabel(state.cursorMs);
  element("artifact").classList.toggle("commit-flash", state.commitTimes.has(state.cursorMs));
  window.__AGENTSIGHT_CURSOR__ = state.cursorMs;
  return state.cursorMs;
}

function stop() {
  if (frame) cancelAnimationFrame(frame);
  frame = 0;
  element("play").textContent = "▶";
}

function sampledMoments(values, startMs, endMs, limit = 120) {
  const ordered = [...new Set([startMs, ...values, endMs]
    .map(Number)
    .filter((value) => Number.isFinite(value) && value >= startMs && value <= endMs))]
    .sort((left, right) => left - right);
  if (ordered.length <= limit) return ordered;
  return Array.from({ length: limit }, (_, index) => (
    ordered[Math.round((ordered.length - 1) * index / (limit - 1))]
  ));
}

function togglePlayback() {
  if (frame) return stop();
  if (state.cursorMs >= state.endMs) renderAt(state.startMs);
  const started = performance.now();
  const cursorStart = state.cursorMs;
  const moments = state.playbackMoments?.filter((value) => value >= cursorStart) ?? [];
  let renderedMoment = Number.NaN;
  element("play").textContent = "Ⅱ";
  const tick = (now) => {
    const fraction = Math.min(1, (now - started) / 10_000);
    const cursor = moments.length > 1
      ? moments[Math.min(moments.length - 1, Math.floor(fraction * moments.length))]
      : cursorStart + (state.endMs - cursorStart) * fraction;
    if (cursor !== renderedMoment) {
      renderAt(cursor);
      renderedMoment = cursor;
    }
    if (fraction >= 1) return stop();
    frame = requestAnimationFrame(tick);
  };
  frame = requestAnimationFrame(tick);
}

function initialize(data, viewId, config = {}) {
  const view = requireView(viewId);
  const moments = view.playbackMoments?.(data)
    ?.map(Number).filter(Number.isFinite).sort((left, right) => left - right) ?? [];
  const startMs = moments[0] ?? data.meta.window_start_ms;
  const endMs = moments.at(-1) ?? data.meta.window_end_ms;
  const playbackMoments = moments.length ? sampledMoments(moments, startMs, endMs) : null;
  state = {
    data, view, startMs, endMs, cursorMs: config.cursorMs ?? endMs,
    playbackMoments, reducedMotion: Boolean(config.reducedMotion),
    commitTimes: new Set((data.commits ?? []).map((row) => Number(row.committed_at_ms))),
  };
  document.title = `${view.title} · AgentSight`;
  element("view-title").textContent = view.title;
  element("view-note").textContent = view.note;
  element("time-mode").textContent = view.timeMode === "static"
    ? "static reference" : "Agent event time";
  element("provenance").textContent = [
    `repository: ${data.meta.repository}`,
    `revision: ${data.meta.endpoint_revision.slice(0, 12)}`,
    `window: ${dayLabel(startMs)} → ${dayLabel(endMs)}`,
    "generator: agentsight-vis 0.1",
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
