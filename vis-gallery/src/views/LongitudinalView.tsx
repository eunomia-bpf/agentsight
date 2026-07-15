import { useEffect, useRef } from "react";
import type { EChartsOption } from "echarts";
import uPlot from "uplot";
import { axisStyle, baseChart, colors } from "../chartTheme";
import EChart from "../components/EChart";
import Panel from "../components/Panel";
import { completedSessionsInVisibleInterval, formatCompact, insertObservationGaps, projectTimeBuckets } from "../selectors";
import type { TimeBucket } from "../types";
import type { ViewProps } from "./viewTypes";

export default function LongitudinalView({ data, state, events }: ViewProps) {
  const visibleEnd = Math.min(state.cursorMs, state.rangeEndMs);
  const verifications = data.verification_events.filter((event) =>
    event.ts_ms >= state.rangeStartMs
    && event.ts_ms <= visibleEnd
    && (state.vendors.size === 0 || state.vendors.has(event.vendor))
    && (!state.selectedSession || event.session_id === state.selectedSession)
  );
  const timeBuckets = projectTimeBuckets(events, verifications);
  const hours = Array.from({ length: 24 }, (_, index) => index);
  const days = data.source_days.map((day) => day.day);
  const punch = days.flatMap((day, y) => hours.map((hour, x) => ({ value: [x, y,
    events.filter((event) => event.day === day && new Date(event.ts_ms).getUTCHours() === hour).length
    + verifications.filter((event) => event.day === day && new Date(event.ts_ms).getUTCHours() === hour).length,
  ] })));
  const punchOption: EChartsOption = {
    ...baseChart, grid: { left: 82, right: 24, top: 20, bottom: 44 },
    xAxis: { type: "category", data: hours, ...axisStyle(), name: "UTC hour" },
    yAxis: { type: "category", data: days, ...axisStyle() },
    visualMap: { min: 0, max: Math.max(1, ...punch.map((row) => row.value[2])), show: false, inRange: { color: ["#101827", "#235d78", "#5bd2b7", "#f4c95d"] } },
    series: [{ type: "heatmap", data: punch, label: { show: true, color: "#dce8f7", fontSize: 9 } }],
  };
  const vendorTotals = ["claude", "codex", "gemini"].map((vendor) => ({ vendor, value: events.filter((event) => event.vendor === vendor).length }));
  const effects = ["read", "write", "test", "process", "repo", "network"].map((effect) => ({ effect, value: events.filter((event) => event.effect === effect).length }));
  const sankeyOption: EChartsOption = {
    ...baseChart,
    series: [{ type: "sankey", data: [...vendorTotals.map((row) => ({ name: row.vendor })), ...effects.map((row) => ({ name: row.effect }))], links: vendorTotals.flatMap((vendor) => effects.map((effect) => ({ source: vendor.vendor, target: effect.effect, value: events.filter((event) => event.vendor === vendor.vendor && event.effect === effect.effect).length })).filter((row) => row.value > 0)), lineStyle: { color: "gradient", opacity: .35 }, label: { color: colors.text, fontSize: 10 } }],
  };
  const completedSessions = completedSessionsInVisibleInterval(data.sessions, events, state);
  const reportedTokens = completedSessions.reduce((sum, session) => sum + session.reported_tokens, 0);
  const writes = events.filter((event) => event.effect === "write");
  const lagRows = writes.slice(-250).map((write) => ({ write, next: verifications.find((event) => event.session_id === write.session_id && event.ts_ms >= write.ts_ms) })).filter((row) => row.next);
  const lagOption: EChartsOption = { ...baseChart, grid: { left: 48, right: 18, top: 18, bottom: 42 }, xAxis: { type: "time", ...axisStyle() }, yAxis: { type: "value", ...axisStyle(), name: "minutes" }, series: [{ type: "scatter", symbolSize: 6, itemStyle: { color: "#66d9a3", opacity: .55 }, data: lagRows.map((row) => [row.write.ts_ms, (row.next!.ts_ms - row.write.ts_ms) / 60_000]) }] };
  return <section className="panel-grid">
    <Panel eyebrow="Long-running rhythm" title="Activity punch card" note="Clock-hour rhythm across the three real observation days. Sparse days and right-censored days remain visible rather than interpolated." wide><EChart option={punchOption} className="chart chart--large" /></Panel>
    <Panel eyebrow="Physiological trace" title="Agent vital signs" note="uPlot reprojects the filtered hourly read/write/verify stream and breaks lines across unobserved gaps. It is a longitudinal shape detector, not a success score." wide><div data-testid="vital-projection" data-bucket-count={timeBuckets.length}><VitalPlot buckets={timeBuckets} cursorMs={state.cursorMs} /></div></Panel>
    <Panel eyebrow="Resource attribution" title="Vendor → semantic unit flow" note="Flow width counts recorded path events. Vendor is native-history source; semantic unit is observed effect." wide><EChart option={sankeyOption} className="chart chart--large" /></Panel>
    <Panel eyebrow="Process QA" title="Write-to-next-verify lag" note="Each dot is an observed write followed by a verification event in the same session. Missing dots remain missing; order is not proof of coverage." wide><EChart option={lagOption} className="chart chart--large" /></Panel>
    <Panel eyebrow="Session receipt" title="Completed sessions in the visible interval" note="Reported token units are summed only for sessions whose full start-to-end span is visible. Counters may still be cumulative or implausible; no currency conversion is attempted.">
      <div className="receipt"><div><span>path observations</span><strong>{formatCompact(events.length)}</strong></div><div><span>writes</span><strong>{formatCompact(writes.length)}</strong></div><div><span>verification events</span><strong>{formatCompact(verifications.length)}</strong></div><div><span>reported token units</span><strong>{formatCompact(reportedTokens)}</strong></div><div><span>completed sessions</span><strong>{completedSessions.length}</strong></div></div>
    </Panel>
    <Panel eyebrow="Ghost comparison" title="Mature days, side by side" note="A paired silhouette compares event mix only. June 2 and June 23 have mature Git horizons; July 14 is excluded from this comparison.">
      <div className="ghost-days">{days.slice(0, 2).map((day) => { const rows = events.filter((event) => event.day === day); const verifyCount = verifications.filter((event) => event.day === day).length; const total = rows.length + verifyCount; return <div key={day}><strong>{day}</strong>{["read", "write", "test"].map((effect) => { const count = effect === "test" ? verifyCount : rows.filter((event) => event.effect === effect).length; return <span key={effect}><i style={{ width: `${100 * count / Math.max(1, total)}%` }} />{effect}</span>; })}</div>; })}</div>
    </Panel>
  </section>;
}

function VitalPlot({ buckets, cursorMs }: { buckets: TimeBucket[]; cursorMs: number }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current || buckets.length === 0) return;
    const plottedBuckets = insertObservationGaps(buckets);
    const values = plottedBuckets.map((row) => row.ts_ms / 1000);
    const aligned: uPlot.AlignedData = [
      values,
      plottedBuckets.map((row) => row.events !== undefined ? row.read ?? 0 : null),
      plottedBuckets.map((row) => row.events !== undefined ? row.write ?? 0 : null),
      plottedBuckets.map((row) => row.events !== undefined ? row.test ?? 0 : null),
      plottedBuckets.map((row) =>
        row.events !== undefined && Math.abs(row.ts_ms - cursorMs) < 1_800_000
          ? Math.max(row.read ?? 0, row.write ?? 0, row.test ?? 0)
          : null,
      ),
    ];
    const plot = new uPlot(
      {
        width: ref.current.clientWidth,
        height: 330,
        cursor: { drag: { x: true, y: false } },
        scales: { x: { time: true } },
        axes: [
          { stroke: "#728098", grid: { stroke: "rgba(148,163,184,.12)" } },
          { stroke: "#728098", grid: { stroke: "rgba(148,163,184,.12)" } },
        ],
        series: [
          { label: "time" },
          { label: "read", stroke: colors.read, width: 1 },
          { label: "write", stroke: colors.write, width: 1 },
          { label: "verify", stroke: colors.test, width: 1 },
          { label: "cursor", stroke: "rgba(255,255,255,.55)", width: 1 },
        ],
      },
      aligned,
      ref.current,
    );
    const ro = new ResizeObserver(() => plot.setSize({ width: ref.current!.clientWidth, height: 330 })); ro.observe(ref.current); return () => { ro.disconnect(); plot.destroy(); };
  }, [buckets, cursorMs]);
  return <div ref={ref} className="uplot-host" />;
}
