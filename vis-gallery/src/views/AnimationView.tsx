import { useEffect, useMemo, useRef } from "react";
import type { EChartsOption } from "echarts";
import { axisStyle, baseChart, colors, vendorColor } from "../chartTheme";
import EChart from "../components/EChart";
import Panel from "../components/Panel";
import { topBy } from "../selectors";
import type { GalleryEvent } from "../types";
import type { ViewProps } from "./viewTypes";

export default function AnimationView({ data, state, events, onChange }: ViewProps) {
  const recent = events.filter((event) => state.cursorMs - event.ts_ms < 6 * 3_600_000);
  const commits = data.commits.filter((commit) => commit.committed_at_ms <= state.cursorMs);
  const commitOption = useMemo<EChartsOption>(() => ({
    ...baseChart,
    grid: { left: 44, right: 22, top: 22, bottom: 38 },
    xAxis: { type: "time", min: state.rangeStartMs, max: state.rangeEndMs, ...axisStyle() },
    yAxis: { type: "value", ...axisStyle(), name: "Git change" },
    series: [
      {
        type: "effectScatter",
        rippleEffect: { scale: 4, brushType: "stroke" },
        symbolSize: (value: unknown) => Math.min(32, 7 + Math.sqrt((value as number[])[1])),
        data: commits.map((commit) => {
          const churn = data.changes
            .filter((change) => change.commit_id === commit.id)
            .reduce((sum, change) => sum + change.additions + change.deletions, 0);
          return {
            value: [commit.committed_at_ms, churn],
            commit: commit.id,
            itemStyle: { color: commit.is_merge ? "#bb8fef" : colors.commit, opacity: 0.78 },
          };
        }),
        tooltip: { show: true },
        markLine: { silent: true, symbol: "none", data: [{ xAxis: state.cursorMs }] },
      },
    ],
    tooltip: {
      renderMode: "richText",
      formatter: (params: unknown) => {
        const row = (params as { data: { commit: string; value: number[] } }).data;
        return `${row.commit.slice(0, 10)}\n${row.value[1]} changed lines`;
      },
    },
  }), [commits, data.changes, state.cursorMs, state.rangeEndMs, state.rangeStartMs]);

  const recentFiles = topBy(data.files.filter((file) => recent.some((event) => event.path === file.path)), (file) => file.touches, 12);
  return (
    <section className="panel-grid">
      <Panel eyebrow="code_swarm · 2008" title="Agent–path particle field" note="Particles replay recorded reads and writes around stable path anchors. Trails show recency, not ownership or causality." wide badge="shared cursor">
        <ParticleField events={recent} files={data.files} cursorMs={state.cursorMs} onSelect={(path) => onChange({ selectedPath: path })} />
      </Panel>
      <Panel eyebrow="Gource · 2009" title="Durable-change pulse" note="Git commits pulse on their own lane. A nearby process event is not silently converted into a commit attribution." wide>
        <EChart option={commitOption} className="chart chart--large" />
      </Panel>
      <Panel eyebrow="Recent wake" title="Paths still glowing" note="A six-hour tail makes bursts readable without implying that quiet paths disappeared.">
        <div className="wake-list">
          {recentFiles.map((file) => {
            const count = recent.filter((event) => event.path === file.path).length;
            return <button key={file.path} onClick={() => onChange({ selectedPath: file.path })}><i style={{ width: `${Math.min(100, count * 5)}%` }} /><strong>{file.path}</strong><span>{count}</span></button>;
          })}
        </div>
      </Panel>
    </section>
  );
}

function ParticleField({ events, files, cursorMs, onSelect }: { events: GalleryEvent[]; files: ViewProps["data"]["files"]; cursorMs: number; onSelect: (path: string) => void }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const anchors = useMemo(() => new Map(files.map((file) => [file.path, file])), [files]);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const draw = () => {
      const box = canvas.getBoundingClientRect();
      const ratio = Math.min(2, devicePixelRatio || 1);
      canvas.width = box.width * ratio; canvas.height = box.height * ratio;
      const ctx = canvas.getContext("2d"); if (!ctx) return;
      ctx.scale(ratio, ratio); ctx.fillStyle = "#070b13"; ctx.fillRect(0, 0, box.width, box.height);
      ctx.globalCompositeOperation = "lighter";
      for (const event of events.slice(-1800)) {
        const file = anchors.get(event.path); if (!file) continue;
        const age = Math.max(0, cursorMs - event.ts_ms) / (6 * 3_600_000);
        const alpha = Math.max(0.025, (1 - age) * 0.62);
        const x = 18 + file.stable_x * (box.width - 36); const y = 18 + file.stable_y * (box.height - 36);
        const radius = event.effect === "write" ? 4.4 : 2.2;
        ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fillStyle = hexAlpha(vendorColor(event.vendor), alpha); ctx.shadowBlur = 14; ctx.shadowColor = vendorColor(event.vendor); ctx.fill();
      }
      ctx.globalCompositeOperation = "source-over"; ctx.shadowBlur = 0;
    };
    draw(); const ro = new ResizeObserver(draw); ro.observe(canvas); return () => ro.disconnect();
  }, [anchors, cursorMs, events]);
  return <canvas ref={ref} className="particle-canvas" onClick={(event) => {
    const box = event.currentTarget.getBoundingClientRect();
    const x = (event.clientX - box.left - 18) / (box.width - 36); const y = (event.clientY - box.top - 18) / (box.height - 36);
    const nearest = [...anchors.values()].sort((a, b) => Math.hypot(a.stable_x - x, a.stable_y - y) - Math.hypot(b.stable_x - x, b.stable_y - y))[0];
    if (nearest) onSelect(nearest.path);
  }} />;
}

function hexAlpha(hex: string, alpha: number): string {
  const value = hex.replace("#", ""); const number = Number.parseInt(value, 16);
  return `rgba(${number >> 16},${(number >> 8) & 255},${number & 255},${alpha})`;
}
