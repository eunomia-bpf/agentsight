import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { axisStyle, baseChart, colors } from "../chartTheme";
import EChart from "../components/EChart";
import Panel from "../components/Panel";
import { formatCompact, topBy } from "../selectors";
import type { ViewProps } from "./viewTypes";

export default function OverviewView({ data, state, events, onChange }: ViewProps) {
  const activePaths = new Set(events.map((event) => event.path));
  const visibleCommits = data.commits.filter(
    (commit) => commit.committed_at_ms <= state.cursorMs,
  );
  const activeSessions = new Set(events.map((event) => event.session_id));
  const writes = events.filter((event) => event.effect === "write");
  const uncertain = writes.filter(
    (event) => event.association_state !== "unique_candidate",
  );
  const topPatterns = Object.entries(
    data.files.reduce<Record<string, number>>((counts, file) => {
      counts[file.pattern] = (counts[file.pattern] ?? 0) + 1;
      return counts;
    }, {}),
  ).sort((a, b) => b[1] - a[1]);

  const activityOption = useMemo<EChartsOption>(() => {
    const values = data.time_buckets.filter(
      (bucket) =>
        bucket.ts_ms >= state.rangeStartMs &&
        bucket.ts_ms <= state.rangeEndMs,
    );
    return {
      ...baseChart,
      grid: { left: 46, right: 18, top: 22, bottom: 42 },
      legend: {
        bottom: 2,
        textStyle: { color: colors.muted },
        itemWidth: 12,
      },
      xAxis: { type: "time", ...axisStyle() },
      yAxis: { type: "value", ...axisStyle(), name: "observations / hour" },
      series: [
        {
          name: "recorded reads",
          type: "line",
          smooth: 0.28,
          showSymbol: false,
          areaStyle: { opacity: 0.1 },
          lineStyle: { width: 1.5, color: colors.read },
          itemStyle: { color: colors.read },
          data: values.map((row) => [row.ts_ms, row.read ?? 0]),
        },
        {
          name: "recorded writes",
          type: "line",
          smooth: 0.28,
          showSymbol: false,
          areaStyle: { opacity: 0.1 },
          lineStyle: { width: 1.5, color: colors.write },
          itemStyle: { color: colors.write },
          data: values.map((row) => [row.ts_ms, row.write ?? 0]),
        },
        {
          name: "Git commits",
          type: "bar",
          barMaxWidth: 8,
          itemStyle: { color: colors.commit, opacity: 0.72 },
          data: values.map((row) => [row.ts_ms, row.commits ?? 0]),
        },
        {
          name: "cursor",
          type: "line",
          markLine: {
            silent: true,
            symbol: "none",
            lineStyle: { color: "#f6f8ff", width: 1, opacity: 0.6 },
            data: [{ xAxis: state.cursorMs }],
          },
          data: [],
        },
      ],
    };
  }, [data.time_buckets, state.cursorMs, state.rangeEndMs, state.rangeStartMs]);

  const topFiles = topBy(
    data.files.filter((file) => activePaths.has(file.path)),
    (file) => file.risk_score,
    7,
  );

  return (
    <>
      <section className="metric-strip">
        <Metric label="visible evidence" value={formatCompact(events.length)} detail="path-resolvable rows" />
        <Metric label="active files" value={formatCompact(activePaths.size)} detail={`of ${formatCompact(data.files.length)}`} />
        <Metric label="sessions" value={formatCompact(activeSessions.size)} detail="pseudonymous trajectories" />
        <Metric label="Git commits" value={formatCompact(visibleCommits.length)} detail="separate durable layer" />
        <Metric label="uncertain writes" value={formatCompact(uncertain.length)} detail="zero or many candidates" warning />
      </section>

      <section className="panel-grid">
        <Panel
          eyebrow="Shared clock"
          title="Longitudinal activity pulse"
          note="Recorded process activity and Git commits share time, but remain separate evidence layers. Drag the global cursor to replay."
          wide
          badge="real multi-day history"
        >
          <EChart option={activityOption} className="chart chart--large" />
        </Panel>

        <Panel
          eyebrow="Field notes"
          title="Three observed days"
          note="These are real source windows, not a continuous synthetic workload. Empty space is part of the history."
        >
          <div className="day-cards">
            {data.source_days.map((day) => (
              <button
                key={day.day}
                className="day-card"
                onClick={() => {
                  const start = Date.parse(`${day.day}T00:00:00Z`);
                  onChange({ cursorMs: start + 24 * 60 * 60 * 1000 - 1, playing: false });
                }}
              >
                <span>{day.day}</span>
                <strong>{formatCompact(day.events)}</strong>
                <small>{day.sessions} sessions · {day.write_event_paths} write-path pairs</small>
              </button>
            ))}
          </div>
          <div className="censor-note">
            <span>right-censored</span>
            July 14 stays process-only until its seven-day Git horizon matures.
          </div>
        </Panel>

        <Panel
          eyebrow="Lanza vocabulary"
          title="Named evolution signals"
          note="Heuristic names make patterns discussable; they are discovery labels, not defect predictions."
        >
          <div className="pattern-list">
            {topPatterns.map(([name, count]) => (
              <div key={name}>
                <span className={`pattern-dot pattern-${name.toLowerCase().replace(" ", "-")}`} />
                <strong>{name}</strong>
                <span>{count} files</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          eyebrow="Forensic queue"
          title="Hot files in the visible interval"
          note="Risk combines observed attention and Git churn; click a file to focus every compatible view."
          wide
        >
          <div className="rank-table">
            {topFiles.map((file, index) => (
              <button key={file.path} onClick={() => onChange({ selectedPath: file.path })}>
                <span className="rank">{String(index + 1).padStart(2, "0")}</span>
                <span className="rank-path">{file.path}</span>
                <span>{file.pattern}</span>
                <strong>{file.touches} touches</strong>
                <span>{formatCompact(file.churn)} churn</span>
              </button>
            ))}
          </div>
        </Panel>
      </section>
    </>
  );
}

function Metric({
  label,
  value,
  detail,
  warning,
}: {
  label: string;
  value: string;
  detail: string;
  warning?: boolean;
}) {
  return (
    <div className={`metric ${warning ? "metric--warning" : ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}
