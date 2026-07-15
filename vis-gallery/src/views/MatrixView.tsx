import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { axisStyle, baseChart, colors } from "../chartTheme";
import EChart from "../components/EChart";
import Panel from "../components/Panel";
import { topBy } from "../selectors";
import type { ViewProps } from "./viewTypes";

export default function MatrixView({ data, state, events, onChange }: ViewProps) {
  const eventCounts = new Map<string, number>();
  const eventCountsByPathDay = new Map<string, number>();
  events.forEach((event) => eventCounts.set(event.path, (eventCounts.get(event.path) ?? 0) + 1));
  events.forEach((event) => {
    const key = `${event.path}\u0000${event.day}`;
    eventCountsByPathDay.set(key, (eventCountsByPathDay.get(key) ?? 0) + 1);
  });
  const files = topBy(
    data.files,
    (file) => (eventCounts.get(file.path) ?? 0) * 5 + file.churn,
    55,
  );
  const days = data.source_days.map((day) => day.day);
  const matrixData = files.flatMap((file, y) =>
    days.map((day, x) => {
      const cell = file.daily[day] ?? {};
      const activity =
        (eventCountsByPathDay.get(`${file.path}\u0000${day}`) ?? 0) * 4 +
        (cell.additions ?? 0) +
        (cell.deletions ?? 0);
      return {
        value: [x, y, Math.log1p(activity)],
        raw: activity,
        path: file.path,
        day,
        pattern: file.pattern,
      };
    }),
  );
  const matrixOption = useMemo<EChartsOption>(() => ({
    ...baseChart,
    grid: { left: 215, right: 54, top: 18, bottom: 48 },
    xAxis: {
      type: "category",
      data: days,
      position: "top",
      ...axisStyle(),
      axisLabel: { color: colors.muted, fontSize: 10 },
    },
    yAxis: {
      type: "category",
      data: files.map((file) => file.path),
      inverse: true,
      axisLabel: {
        color: colors.muted,
        width: 205,
        overflow: "truncate",
        fontFamily: "ui-monospace, monospace",
        fontSize: 9,
      },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    visualMap: {
      min: 0,
      max: Math.max(1, ...matrixData.map((row) => Number(row.value[2]))),
      calculable: false,
      orient: "vertical",
      right: 2,
      top: "center",
      textStyle: { color: colors.muted, fontSize: 9 },
      inRange: { color: ["#101827", "#174d67", "#2ea6a0", "#f0c66e", "#ff7b72"] },
    },
    tooltip: {
      renderMode: "richText",
      formatter: (params: unknown) => {
        const row = (params as { data: typeof matrixData[number] }).data;
        return `${row.path}\n${row.day}\nactivity ${row.raw}\n${row.pattern}`;
      },
    },
    series: [
      {
        type: "heatmap",
        progressive: 1_000,
        data: matrixData,
        emphasis: { itemStyle: { borderColor: "#fff", borderWidth: 1 } },
      },
    ],
  }), [days, files, matrixData]);

  const groups = [...new Set(data.files.map((file) => file.group))]
    .map((group) => ({
      group,
      count: data.files.filter((file) => file.group === group).length,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 24)
    .map((row) => row.group);
  const states = ["not_eligible", "no_candidate", "unique_candidate", "ambiguous_candidates"];
  const associationData = groups.flatMap((group, y) =>
    states.map((joinState, x) => ({
      value: [
        x,
        y,
        events.filter(
          (event) => event.group === group && event.association_state === joinState,
        ).length,
      ],
      group,
      state: joinState,
    })),
  );
  const associationOption: EChartsOption = {
    ...baseChart,
    grid: { left: 155, right: 35, top: 25, bottom: 72 },
    xAxis: {
      type: "category",
      data: states.map((value) => value.replaceAll("_", " ")),
      axisLabel: { color: colors.muted, rotate: 25, fontSize: 9 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: "category",
      data: groups,
      inverse: true,
      axisLabel: { color: colors.muted, width: 140, overflow: "truncate", fontSize: 9 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    visualMap: {
      min: 0,
      max: Math.max(1, ...associationData.map((row) => Number(row.value[2]))),
      show: false,
      inRange: { color: ["#111827", "#254a68", "#e0a458", "#ff6b7a"] },
    },
    tooltip: {
      renderMode: "richText",
      formatter: (params: unknown) => {
        const row = (params as { data: typeof associationData[number] }).data;
        return `${row.group}\n${row.state.replaceAll("_", " ")}: ${row.value[2]}`;
      },
    },
    series: [{ type: "heatmap", data: associationData, label: { show: true, color: "#dbe6f7", fontSize: 9 } }],
  };

  const patterns = topBy(data.files, (file) => file.risk_score, 18);
  return (
    <section className="panel-grid" data-testid="matrix-projection" data-event-count={events.length}>
      <Panel
        eyebrow="Evolution Matrix · 2001"
        title="File × observation-day matrix"
        note="Brightness combines filtered recorded touches with filter-invariant Git churn. Rows stay stable across days, making bursts and pulses comparable."
        wide
        badge="log-scaled activity"
      >
        <EChart
          option={matrixOption}
          className="chart chart--xxl"
          onClick={(params) => {
            const path = (params as { data?: { path?: string } }).data?.path;
            if (path) onChange({ selectedPath: path });
          }}
        />
      </Panel>

      <Panel
        eyebrow="Join audit"
        title="Association-state matrix"
        note="This matrix makes missing and ambiguous links first-class. Large amber/red cells are evidence gaps, not agent failures."
      >
        <EChart option={associationOption} className="chart chart--large" />
      </Panel>

      <Panel
        eyebrow="Pattern lexicon"
        title="Named signals worth inspecting"
        note="Supernova, Pulsar, White Dwarf, and Dayfly are heuristic invitations to inspect—not statistical diagnoses."
      >
        <div className="signal-grid">
          {patterns.map((file) => (
            <button key={file.path} onClick={() => onChange({ selectedPath: file.path })}>
              <span>{file.pattern}</span>
              <strong>{file.path.split("/").at(-1)}</strong>
              <small>{file.touches} touches · {file.churn} churn</small>
            </button>
          ))}
        </div>
      </Panel>
    </section>
  );
}
