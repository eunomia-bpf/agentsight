import type { EChartsOption } from "echarts";
import { axisStyle, baseChart, colors, vendorColor } from "../chartTheme";
import EChart from "../components/EChart";
import Panel from "../components/Panel";
import { topBy } from "../selectors";
import type { ViewProps } from "./viewTypes";

export default function StorylineView({ data, state, events, onChange }: ViewProps) {
  const sessions = topBy(data.sessions.filter((session) => events.some((event) => event.session_id === session.id)), (session) => session.tool_events, 28);
  const groups = [...new Set(events.map((event) => event.group))].slice(0, 22);
  const series = sessions.map((session) => ({
    name: session.id,
    type: "line" as const,
    showSymbol: true,
    symbolSize: 4,
    lineStyle: { width: 1.4, color: vendorColor(session.vendor), opacity: .52 },
    itemStyle: { color: vendorColor(session.vendor) },
    data: events.filter((event) => event.session_id === session.id && groups.includes(event.group)).map((event) => ({ value: [event.ts_ms, groups.indexOf(event.group)], session: session.id, path: event.path })),
  }));
  const storyOption: EChartsOption = {
    ...baseChart,
    grid: { left: 155, right: 22, top: 24, bottom: 44 },
    xAxis: { type: "time", min: state.rangeStartMs, max: state.rangeEndMs, ...axisStyle() },
    yAxis: { type: "category", data: groups, axisLabel: { color: colors.muted, width: 142, overflow: "truncate", fontSize: 9 }, axisLine: { show: false }, axisTick: { show: false } },
    dataZoom: [{ type: "inside" }],
    series,
    tooltip: { trigger: "item", renderMode: "richText", formatter: (params: unknown) => { const row = (params as { data: { session: string; path: string } }).data; return `${row.session}\n${row.path}`; } },
  };

  const authors = topBy(data.ownership, (row) => row.churn, 30);
  const ownershipOption: EChartsOption = {
    ...baseChart,
    tooltip: { trigger: "item", renderMode: "richText" },
    series: [{ type: "sankey", nodeAlign: "justify", data: [...new Set(authors.flatMap((row) => [`a:${row.author}`, `g:${row.group}`]))].map((name) => ({ name, itemStyle: { color: name.startsWith("a:") ? "#7b93ad" : "#2c6e73" } })), links: authors.map((row) => ({ source: `a:${row.author}`, target: `g:${row.group}`, value: row.churn })), lineStyle: { color: "gradient", opacity: .24 }, label: { color: colors.text, fontSize: 9, formatter: (params: unknown) => String((params as { name: string }).name).slice(2) } }],
  };
  return <section className="panel-grid">
    <Panel eyebrow="Evolution Storylines · 2010" title="Session journeys through repository territory" note="Each pseudonymous session is a line crossing top-level path groups. The story is observed navigation, not intent reconstruction." wide>
      <EChart option={storyOption} className="chart chart--xxl" onClick={(params) => { const row = (params as { data?: { session?: string; path?: string } }).data; onChange({ selectedSession: row?.session ?? null, selectedPath: row?.path ?? null }); }} />
    </Panel>
    <Panel eyebrow="Git ownership map" title="Durable authorship × directory" note="This view uses Git author labels only. Native agent vendors remain a separate process layer, so no author label is reclassified as an agent." wide>
      <EChart option={ownershipOption} className="chart chart--large" />
    </Panel>
    <Panel eyebrow="Cast list" title="Visible trajectories" note="Click a trajectory to focus every family on that session.">
      <div className="cast-list">{sessions.map((session) => <button key={session.id} onClick={() => onChange({ selectedSession: session.id })}><i style={{ background: vendorColor(session.vendor) }} /><strong>{session.id}</strong><span>{session.vendor}</span><small>{session.tool_events} tools</small></button>)}</div>
    </Panel>
  </section>;
}
