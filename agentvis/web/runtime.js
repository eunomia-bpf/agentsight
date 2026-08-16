import { init, use } from "echarts/core";
import { ScatterChart } from "echarts/charts";
import { GraphicComponent, GridComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer, SVGRenderer } from "echarts/renderers";
import {
  BufferTarget, CanvasSource, Mp4OutputFormat, Output, QUALITY_HIGH, canEncodeVideo,
} from "mediabunny";
import {
  nebulaVisualMoments, repositoryNebula,
} from "./repository-nebula.js";

use([ScatterChart, GraphicComponent, GridComponent, TooltipComponent, CanvasRenderer, SVGRenderer]);

const $ = (id) => document.getElementById(id);
const PLAYBACK_FRAME_MS = 125;
const palette = { text: "#dce8f7", muted: "#71839a", line: "rgba(135,160,190,.18)" };
const helper = { base: () => ({
  backgroundColor: "transparent", animation: false,
  textStyle: { color: palette.text, fontFamily: "Inter,system-ui,sans-serif" },
  tooltip: { trigger: "item", renderMode: "richText", backgroundColor: "#0b121c",
    borderColor: "rgba(135,160,190,.28)", textStyle: { color: palette.text, fontSize: 12 } },
}) };

let chart;
let data;
let cursor;
let frameIndex = 0;
let moments = [];
let frameTimes = [];
let playing = 0;
const exportMode = new URLSearchParams(location.search).has("still");

const timeLabel = (value) => new Date(value).toISOString().replace("T", " ").replace(".000Z", " UTC");
const dayLabel = (value) => new Date(value).toISOString().slice(0, 10);

function optionAt(value, step) {
  if (Number.isInteger(step)) data.meta.render_layout_step = step;
  else delete data.meta.render_layout_step;
  const option = repositoryNebula(data, value, helper);
  option.animation = false;
  if (exportMode) option.tooltip = { show: false };
  for (const series of option.series ?? []) Object.assign(series, {
    animation: false, animationDuration: 0, animationDurationUpdate: 0,
  });
  return option;
}

function isCommitFrame(value, step) {
  const found = frameTimes.findIndex((time) => time >= value);
  const index = Number.isInteger(step) ? step : (found < 0 ? frameTimes.length - 1 : found);
  const start = index > 0 ? frameTimes[index - 1] : data.meta.window_start_ms - 1;
  const end = frameTimes[index] ?? value;
  return data.commits.some((row) => row.committed_at_ms > start && row.committed_at_ms <= end);
}

function render(value, step) {
  const requested = Number.isInteger(step)
    ? step
    : frameTimes.findLastIndex((time) => time <= Number(value));
  frameIndex = Math.max(0, Math.min(frameTimes.length - 1, requested));
  cursor = frameTimes[frameIndex];
  chart.setOption(optionAt(cursor, frameIndex), { notMerge: true, lazyUpdate: false, silent: true });
  chart.getZr().flush();
  $("timeline").value = String(frameIndex);
  $("cursor-label").textContent = timeLabel(cursor);
  $("artifact").classList.toggle("commit-flash", isCommitFrame(cursor, frameIndex));
  return cursor;
}

function stop() {
  cancelAnimationFrame(playing);
  playing = 0;
  $("play").textContent = "▶";
}

function toggle() {
  if (playing) return stop();
  if (frameTimes.length < 2) return;
  if (frameIndex >= frameTimes.length - 1) render(frameTimes[0], 0);
  let nextIndex = frameIndex + 1;
  let nextAt = performance.now() + PLAYBACK_FRAME_MS;
  $("play").textContent = "Ⅱ";
  const tick = (now) => {
    if (now < nextAt) {
      playing = requestAnimationFrame(tick);
      return;
    }
    render(frameTimes[nextIndex], nextIndex);
    nextIndex += 1;
    nextAt += PLAYBACK_FRAME_MS;
    if (nextIndex >= frameTimes.length) return stop();
    playing = requestAnimationFrame(tick);
  };
  playing = requestAnimationFrame(tick);
}

function initialize(payload) {
  data = payload;
  moments = nebulaVisualMoments(data);
  frameTimes = moments.length > 2 ? moments.slice(1, -1) : [data.meta.window_end_ms];
  chart = init($("chart"), null, { renderer: "canvas", width: 1200, height: 675 });
  $("view-title").textContent = "Agent Session Evolution Graph";
  $("view-note").textContent = "Files are stars. Root entries define color; paths define attraction.";
  $("provenance").textContent = [
    `repository: ${data.meta.repository}`,
    `scope: ${data.meta.session_scope === "global_tool_operations" ? "all local sessions targeting repository" : "repository sessions"}`,
    `revision: ${data.meta.endpoint_revision.slice(0, 12)}`,
    `window: ${dayLabel(data.meta.window_start_ms)} → ${dayLabel(data.meta.window_end_ms)}`,
    "generator: evolution renderer",
  ].join(" · ");
  Object.assign($("timeline"), {
    min: "0", max: String(frameTimes.length - 1), step: "1",
  });
  $("timeline").addEventListener("input", () => {
    stop();
    const index = Number($("timeline").value);
    render(frameTimes[index], index);
  });
  $("play").addEventListener("click", toggle);
  render(frameTimes[0], 0);
  window.__AGENTVIS_READY__ = true;
  window.__AGENTVIS_FRAME_COUNT__ = frameTimes.length;
}

function composeFrame(canvas = document.createElement("canvas")) {
  if (canvas.width !== 1264 || canvas.height !== 936) {
    Object.assign(canvas, { width: 1264, height: 936 });
  }
  const context = canvas.getContext("2d");
  const artifact = $("artifact").getBoundingClientRect();
  context.fillStyle = "#070b12";
  context.fillRect(0, 0, canvas.width, canvas.height);
  if ($("artifact").classList.contains("commit-flash")) {
    context.save();
    context.strokeStyle = "#efd265";
    context.lineWidth = 2;
    context.shadowBlur = 24;
    context.shadowColor = "rgba(239,210,101,.72)";
    context.strokeRect(2, 2, canvas.width - 4, canvas.height - 4);
    context.restore();
  }
  const scaleX = canvas.width / artifact.width;
  const scaleY = canvas.height / artifact.height;
  for (const layer of $("chart").querySelectorAll("canvas")) {
    const style = getComputedStyle(layer);
    if (style.display === "none" || style.visibility === "hidden") continue;
    const box = layer.getBoundingClientRect();
    context.save();
    context.globalAlpha = Number.parseFloat(style.opacity) || 1;
    context.drawImage(layer,
      (box.x - artifact.x) * scaleX, (box.y - artifact.y) * scaleY,
      box.width * scaleX, box.height * scaleY);
    context.restore();
  }
  context.strokeStyle = palette.line;
  context.beginPath(); context.moveTo(32, 113); context.lineTo(1232, 113); context.stroke();
  context.fillStyle = "#61d7bf"; context.font = "11px monospace";
  context.fillText("REPOSITORY EVOLUTION", 32, 39);
  context.fillStyle = palette.text; context.font = "28px system-ui";
  context.fillText("Agent Session Evolution Graph", 32, 72);
  context.fillStyle = palette.muted; context.font = "12px system-ui";
  context.fillText("Files are stars. Root entries define color; paths define attraction.", 32, 96);
  context.strokeStyle = "rgba(135,160,190,.22)";
  context.beginPath(); context.roundRect(1096, 24, 136, 28, 14); context.stroke();
  context.fillStyle = "#8c9bb0"; context.font = "11px monospace";
  context.fillText("AGENT EVENT TIME", 1108, 42);
  context.strokeStyle = palette.line;
  context.beginPath(); context.moveTo(32, 803); context.lineTo(1232, 803); context.stroke();
  const progress = frameIndex / Math.max(1, frameTimes.length - 1);
  context.fillStyle = "#10231f"; context.strokeStyle = "rgba(97,215,191,.4)";
  context.beginPath(); context.arc(50, 836, 18, 0, 2 * Math.PI); context.fill(); context.stroke();
  context.fillStyle = "#61d7bf"; context.beginPath();
  context.moveTo(45, 830); context.lineTo(45, 842); context.lineTo(56, 836); context.closePath(); context.fill();
  context.fillStyle = "#16242b"; context.fillRect(89, 834, 935, 4);
  context.fillStyle = "#61d7bf"; context.fillRect(89, 834, 935 * progress, 4);
  context.fillStyle = "#9bacc0"; context.font = "10px monospace";
  context.fillText(timeLabel(cursor), 1103, 839);
  const legends = [["#f7ffff", "read attention"], ["#ff9678", "write ripple"],
    ["#75f0a9", "create"], ["#63dfff", "rename"], ["#ff647c", "delete"], ["#efd265", "commit frame"]];
  let legendX = 32;
  context.font = "10px monospace";
  for (const [color, label] of legends) {
    context.fillStyle = color; context.fillRect(legendX, 867, 13, 3);
    context.fillStyle = palette.muted; context.fillText(label, legendX + 18, 872);
    legendX += 36 + context.measureText(label).width;
  }
  context.fillStyle = palette.muted;
  context.fillText($("provenance").textContent, 32, 891);
  return canvas;
}

let encoder;

async function beginMp4(plan = {}) {
  if (!await canEncodeVideo("avc", { width: 1264, height: 936, bitrate: QUALITY_HIGH })) {
    throw new Error("This Chromium build has no H.264 WebCodecs encoder; use a Chrome/Chromium build with AVC encoding support.");
  }
  render(frameTimes[0], 0);
  const canvas = composeFrame();
  const target = new BufferTarget();
  const output = new Output({ format: new Mp4OutputFormat({ fastStart: "in-memory" }), target });
  const source = new CanvasSource(canvas, { codec: "avc", bitrate: QUALITY_HIGH });
  const frameRate = Number(plan.frameRate) || 8;
  const indices = Array.isArray(plan.indices) && plan.indices.length
    ? plan.indices : frameTimes.map((_, index) => index);
  output.addVideoTrack(source, { frameRate });
  await output.start();
  encoder = { canvas, target, output, source, index: 0, indices, frameRate };
  return indices.length;
}

async function encodeMp4Chunk(count = 12) {
  const end = Math.min(encoder.indices.length, encoder.index + count);
  for (; encoder.index < end; encoder.index += 1) {
    const layoutIndex = encoder.indices[encoder.index];
    render(frameTimes[layoutIndex], layoutIndex);
    composeFrame(encoder.canvas);
    await encoder.source.add(
      encoder.index / encoder.frameRate,
      1 / encoder.frameRate,
      { keyFrame: encoder.index % 64 === 0 },
    );
  }
  return [encoder.index, encoder.indices.length];
}

function base64(buffer) {
  const bytes = new Uint8Array(buffer);
  let value = "";
  for (let offset = 0; offset < bytes.length; offset += 0x8000) {
    value += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
  }
  return btoa(value);
}

async function finishMp4() {
  await encoder.output.finalize();
  const value = base64(encoder.target.buffer);
  encoder = null;
  return value;
}

function pngBase64() {
  render(frameTimes.at(-1), frameTimes.length - 1);
  return composeFrame().toDataURL("image/png").split(",", 2)[1];
}

async function svg() {
  const host = document.createElement("div");
  Object.assign(host.style, { position: "fixed", left: "-10000px", width: "1200px", height: "675px" });
  document.body.append(host);
  const svgChart = init(host, null, { renderer: "svg", width: 1200, height: 675 });
  svgChart.setOption(optionAt(cursor, frameTimes.length - 1), { notMerge: true, lazyUpdate: false });
  svgChart.getZr().flush();
  const value = host.querySelector("svg").outerHTML;
  svgChart.dispose(); host.remove();
  return value;
}

globalThis.AgentVis = {
  initialize, render, beginMp4, encodeMp4Chunk, finishMp4, pngBase64, svg, composeFrame,
};
