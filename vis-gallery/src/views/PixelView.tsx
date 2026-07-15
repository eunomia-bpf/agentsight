import { useEffect, useMemo, useRef } from "react";
import type { EChartsOption } from "echarts";
import { axisStyle, baseChart, stateColor } from "../chartTheme";
import EChart from "../components/EChart";
import Panel from "../components/Panel";
import { topBy } from "../selectors";
import type { LinePixel } from "../types";
import type { ViewProps } from "./viewTypes";

export default function PixelView({ data, state, events, onChange }: ViewProps) {
  const activePaths = new Set(events.map((event) => event.path));
  const pixels = state.selectedPath
    ? data.line_pixels.filter((pixel) => pixel.path === state.selectedPath)
    : data.line_pixels;
  const laneFiles = topBy(
    data.files.filter((file) => activePaths.has(file.path)),
    (file) => file.touches + file.git_changes * 2,
    42,
  );
  const lanePaths = new Set(laneFiles.map((file) => file.path));
  const laneEvents = events.filter((event) => lanePaths.has(event.path));
  const lanesOption = useMemo<EChartsOption>(() => ({
    ...baseChart,
    grid: { left: 190, right: 20, top: 18, bottom: 42 },
    xAxis: { type: "time", ...axisStyle() },
    yAxis: {
      type: "category",
      data: laneFiles.map((file) => file.path),
      inverse: true,
      axisLabel: {
        color: "#8c9bb1",
        width: 175,
        overflow: "truncate",
        fontFamily: "ui-monospace, monospace",
        fontSize: 9,
      },
      axisTick: { show: false },
      axisLine: { show: false },
    },
    dataZoom: [{ type: "inside", xAxisIndex: 0 }, { type: "slider", height: 12, bottom: 4 }],
    series: [
      {
        name: "process evidence",
        type: "scatter",
        symbolSize: (value: unknown) => {
          const row = value as [number, string, number];
          return row[2] === 1 ? 7 : 4;
        },
        data: laneEvents.map((event) => ({
          value: [event.ts_ms, event.path, event.effect === "write" ? 1 : 0],
          path: event.path,
          itemStyle: {
            color:
              event.effect === "write"
                ? stateColor(event.association_state)
                : "rgba(89, 174, 255, .44)",
          },
        })),
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { color: "rgba(255,255,255,.65)" },
          data: [{ xAxis: state.cursorMs }],
        },
      },
    ],
    tooltip: {
      trigger: "item",
      formatter: (params: unknown) => {
        const value = (params as { value: [number, string, number] }).value;
        return `${value[1]}<br/>${new Date(value[0]).toISOString()}<br/>${value[2] ? "write evidence" : "read evidence"}`;
      },
    },
  }), [laneEvents, laneFiles, state.cursorMs]);

  return (
    <section className="panel-grid">
      <Panel
        eyebrow="SeeSoft · 1992"
        title="Current-line age pixels"
        note="Each dash is one current line colored by Git blame age. Bright outlines mark files touched in the visible process interval; they do not claim the agent authored those lines."
        wide
        badge={`${pixels.length.toLocaleString()} real lines`}
      >
        <SeeSoftCanvas
          pixels={pixels}
          activePaths={activePaths}
          cursorMs={state.cursorMs}
          selectedPath={state.selectedPath}
          onSelect={(path) => onChange({ selectedPath: path })}
        />
      </Panel>

      <Panel
        eyebrow="Evidence overlay"
        title="Touch and association lanes"
        note="Blue ticks are recorded reads. Write ticks use green/amber/red for one/many/zero Git candidates. Candidate state is uncertainty, not provenance."
        wide
      >
        <EChart
          option={lanesOption}
          className="chart chart--xl"
          onClick={(params) => {
            const dataPoint = (params as { data?: { path?: string } }).data;
            if (dataPoint?.path) onChange({ selectedPath: dataPoint.path });
          }}
        />
      </Panel>
    </section>
  );
}

function SeeSoftCanvas({
  pixels,
  activePaths,
  cursorMs,
  selectedPath,
  onSelect,
}: {
  pixels: LinePixel[];
  activePaths: Set<string>;
  cursorMs: number;
  selectedPath: string | null;
  onSelect: (path: string) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const columnsRef = useRef<string[]>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const draw = () => {
      const bounds = canvas.getBoundingClientRect();
      const ratio = Math.min(2, window.devicePixelRatio || 1);
      canvas.width = Math.floor(bounds.width * ratio);
      canvas.height = Math.floor(bounds.height * ratio);
      const context = canvas.getContext("2d");
      if (!context) return;
      context.scale(ratio, ratio);
      context.clearRect(0, 0, bounds.width, bounds.height);
      context.fillStyle = "#080c14";
      context.fillRect(0, 0, bounds.width, bounds.height);
      const grouped = new Map<string, LinePixel[]>();
      for (const pixel of pixels) {
        const values = grouped.get(pixel.path) ?? [];
        values.push(pixel);
        grouped.set(pixel.path, values);
      }
      const columns = [...grouped.entries()]
        .sort((a, b) => b[1].length - a[1].length)
        .slice(0, Math.max(1, Math.floor(bounds.width / 10)));
      columnsRef.current = columns.map(([path]) => path);
      const gap = 2;
      const width = Math.max(4, (bounds.width - gap * columns.length) / columns.length);
      columns.forEach(([path, lines], column) => {
        const x = column * (width + gap);
        const step = Math.max(1, (bounds.height - 20) / Math.max(1, lines.length));
        if (activePaths.has(path)) {
          context.strokeStyle = selectedPath === path ? "#fff3bf" : "rgba(102,217,163,.72)";
          context.lineWidth = selectedPath === path ? 2 : 1;
          context.strokeRect(x - 1, 5, width + 2, bounds.height - 10);
        }
        lines.forEach((line, index) => {
          const ageDays = Math.max(0, (cursorMs - line.origin_ms) / 86_400_000);
          const freshness = Math.max(0, 1 - Math.log1p(ageDays) / Math.log(900));
          const hue = 205 - freshness * 165;
          context.fillStyle = `hsla(${hue}, 78%, ${34 + freshness * 34}%, .92)`;
          context.fillRect(x, 7 + index * step, width, Math.max(1, step - 0.3));
        });
      });
    };
    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [activePaths, cursorMs, pixels, selectedPath]);

  return (
    <canvas
      ref={canvasRef}
      className="seesoft-canvas"
      onClick={(event) => {
        const bounds = event.currentTarget.getBoundingClientRect();
        const index = Math.floor(
          (event.clientX - bounds.left) / (bounds.width / Math.max(1, columnsRef.current.length)),
        );
        const path = columnsRef.current[index];
        if (path) onSelect(path);
      }}
    />
  );
}
