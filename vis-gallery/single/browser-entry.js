import { helpers } from "./helpers.js";
import { requireView, views } from "./registry.js";

let chart;
let state;
let frame;

function timeLabel(value) {
  return new Date(value).toISOString().replace("T", " ").replace(".000Z", " UTC");
}

function renderAt(cursorMs) {
  state.cursorMs = Math.max(state.startMs, Math.min(state.endMs, Number(cursorMs)));
  const option = state.view.build(state.data, state.cursorMs, helpers);
  chart.setOption(option, { notMerge: true, lazyUpdate: false });
  document.querySelector("#timeline").value = String(state.cursorMs);
  document.querySelector("#cursor-label").textContent = timeLabel(state.cursorMs);
  window.__AGENTSIGHT_CURSOR__ = state.cursorMs;
  return state.cursorMs;
}

function stop() {
  if (frame) cancelAnimationFrame(frame);
  frame = 0;
  document.querySelector("#play").textContent = "▶";
}

function togglePlayback() {
  if (frame) return stop();
  if (state.cursorMs >= state.endMs) renderAt(state.startMs);
  const started = performance.now();
  const cursorStart = state.cursorMs;
  document.querySelector("#play").textContent = "Ⅱ";
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
  document.querySelector("#view-title").textContent = view.title;
  document.querySelector("#view-note").textContent = view.note;
  document.querySelector("#time-mode").textContent = view.timeMode.replaceAll("-", " ");
  document.querySelector("#provenance").textContent = `${data.meta.repository} · ${data.meta.endpoint_revision.slice(0, 12)} · ${data.meta.association_mode}`;
  const timeline = document.querySelector("#timeline");
  timeline.min = String(startMs);
  timeline.max = String(endMs);
  timeline.step = "1";
  timeline.addEventListener("input", () => {
    stop();
    renderAt(Number(timeline.value));
  });
  const play = document.querySelector("#play");
  play.addEventListener("click", togglePlayback);
  if (view.timeMode === "static") {
    timeline.disabled = true;
    play.disabled = true;
    play.title = "This view represents the frozen endpoint or complete interval";
  }
  chart = globalThis.echarts.init(document.querySelector("#chart"), null, {
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
