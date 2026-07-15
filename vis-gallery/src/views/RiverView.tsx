import type { EChartsOption } from "echarts";
import { axisStyle, baseChart, colors } from "../chartTheme";
import EChart from "../components/EChart";
import Panel from "../components/Panel";
import type { ViewProps } from "./viewTypes";

export default function RiverView({ data, state, events }: ViewProps) {
  const cohorts = data.survival_cohorts;
  const cohortOption: EChartsOption = {
    ...baseChart,
    grid: { left: 46, right: 20, top: 24, bottom: 54 },
    legend: { top: 0, textStyle: { color: colors.muted } },
    xAxis: { type: "category", data: cohorts.map((row) => row.cohort), ...axisStyle(), axisLabel: { rotate: 35, color: colors.muted, fontSize: 9 } },
    yAxis: { type: "value", ...axisStyle(), name: "file lifetimes" },
    series: [
      { name: "survives at endpoint", type: "bar", stack: "life", itemStyle: { color: "#4ab99a" }, data: cohorts.map((row) => row.surviving_files ?? 0) },
      { name: "ended before endpoint", type: "bar", stack: "life", itemStyle: { color: "#66445a" }, data: cohorts.map((row) => row.dead_files ?? 0) },
    ],
  };

  const days = data.source_days.map((day) => day.day);
  const riverOption: EChartsOption = {
    ...baseChart,
    tooltip: { trigger: "axis" },
    legend: { top: 0, textStyle: { color: colors.muted } },
    singleAxis: { type: "time", min: state.rangeStartMs, max: state.rangeEndMs, top: 44, bottom: 26, axisLabel: { color: colors.muted } },
    series: [{
      type: "themeRiver",
      emphasis: { itemStyle: { shadowBlur: 16, shadowColor: "rgba(0,0,0,.5)" } },
      data: events
        .reduce<Array<[number, number, string]>>((rows, event) => {
          const hour = Math.floor(event.ts_ms / 3_600_000) * 3_600_000;
          const found = rows.find((row) => row[0] === hour && row[2] === event.vendor);
          if (found) found[1] += 1; else rows.push([hour, 1, event.vendor]);
          return rows;
        }, []),
      color: ["#f0a06b", "#6ad4ff", "#a78bfa"],
    }],
  };

  const daily = days.map((day) => ({
    day,
    added: data.changes.filter((change) => new Date(change.committed_at_ms).toISOString().startsWith(day)).reduce((sum, row) => sum + row.additions, 0),
    deleted: data.changes.filter((change) => new Date(change.committed_at_ms).toISOString().startsWith(day)).reduce((sum, row) => sum + row.deletions, 0),
  }));
  return <section className="panel-grid">
    <Panel eyebrow="History Flow · 2004" title="Agent activity river" note="Width is recorded path activity, stratified by native-history vendor. The river describes observation volume, not durable authorship." wide>
      <EChart option={riverOption} className="chart chart--xl" />
    </Panel>
    <Panel eyebrow="git-of-theseus · 2016" title="File-lifetime cohorts" note="Birth is the first add in first-parent Git history; delete/recreate starts a new lifetime. Survival is measured only at the frozen endpoint." wide>
      <EChart option={cohortOption} className="chart chart--large" />
    </Panel>
    <Panel eyebrow="Survival ledger" title="The repository keeps and forgets" note="A compact endpoint view separates cohort survival from process attention.">
      <div className="cohort-ledger">{cohorts.slice(-10).reverse().map((row) => <div key={row.cohort}><strong>{row.cohort}</strong><span>{row.surviving_files ?? 0} alive</span><span>{row.dead_files ?? 0} ended</span><i style={{ width: `${100 * (row.surviving_files ?? 0) / Math.max(1, row.born_files)}%` }} /></div>)}</div>
    </Panel>
    <Panel eyebrow="Change balance" title="Observed-day Git sediment" note="Adds and deletes are actual Git changes on the three observation days, independent of event-to-Git candidates.">
      <div className="sediment">{daily.map((row) => <div key={row.day}><span>{row.day}</span><i className="add" style={{ width: `${Math.min(100, Math.log1p(row.added) * 9)}%` }} /><strong>+{row.added}</strong><i className="del" style={{ width: `${Math.min(100, Math.log1p(row.deleted) * 9)}%` }} /><strong>−{row.deleted}</strong></div>)}</div>
    </Panel>
  </section>;
}
