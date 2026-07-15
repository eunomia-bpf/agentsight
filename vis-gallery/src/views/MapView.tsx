import { useMemo } from "react";
import type { EChartsOption } from "echarts";
import { baseChart, colors } from "../chartTheme";
import EChart from "../components/EChart";
import Panel from "../components/Panel";
import type { TreeNode } from "../types";
import type { ViewProps } from "./viewTypes";

const patternColors: Record<string, string> = {
  Supernova: "#ff6b7a",
  Pulsar: "#f4c95d",
  "White Dwarf": "#90a4be",
  Dayfly: "#bb8fef",
  Nova: "#5dd9c1",
  Fossil: "#3f4b5e",
  Steady: "#4d91c6",
};

export default function MapView({ data, state, events, onChange }: ViewProps) {
  const activePaths = new Set(events.map((event) => event.path));
  const tree = useMemo(() => decorateTree(data.tree, activePaths), [activePaths, data.tree]);
  const treemapOption: EChartsOption = {
    ...baseChart,
    tooltip: {
      formatter: (params: unknown) => {
        const value = params as { data?: TreeNode & { touches?: number; pattern?: string } };
        const row = value.data;
        return row?.path
          ? `<strong>${row.path}</strong><br/>${row.pattern ?? "directory"}<br/>${row.touches ?? 0} recorded touches<br/>${row.value ?? 0} current bytes`
          : row?.name ?? "repository";
      },
    },
    series: [
      {
        type: "treemap",
        data: tree.children ?? [],
        roam: true,
        nodeClick: "zoomToNode",
        breadcrumb: {
          show: true,
          bottom: 3,
          itemStyle: { color: "#151d2b", borderColor: "#26344b" },
        },
        label: { show: true, color: "#e9f1ff", fontSize: 10, overflow: "truncate" },
        upperLabel: { show: true, height: 22, color: "#9fb1c9" },
        itemStyle: { borderColor: "#080c14", borderWidth: 1, gapWidth: 1 },
        levels: [
          { itemStyle: { borderWidth: 0, gapWidth: 2 } },
          { colorSaturation: [0.25, 0.65], itemStyle: { gapWidth: 2 } },
          { colorSaturation: [0.3, 0.75], itemStyle: { gapWidth: 1 } },
        ],
      },
    ],
  };

  const constellationOption: EChartsOption = {
    ...baseChart,
    grid: { left: 18, right: 18, top: 18, bottom: 28 },
    xAxis: { min: 0, max: 1, show: false },
    yAxis: { min: 0, max: 1, show: false },
    tooltip: {
      formatter: (params: unknown) => {
        const row = (params as { data: { path: string; pattern: string; touches: number; risk: number } }).data;
        return `<strong>${row.path}</strong><br/>${row.pattern}<br/>${row.touches} touches · risk ${row.risk.toFixed(2)}`;
      },
    },
    series: [
      {
        type: "scatter",
        data: data.files.map((file) => ({
          value: [file.stable_x, file.stable_y, file.risk_score],
          path: file.path,
          pattern: file.pattern,
          touches: file.touches,
          risk: file.risk_score,
          symbolSize: Math.max(3, Math.min(28, 3 + Math.sqrt(file.current_bytes || file.churn) / 8)),
          itemStyle: {
            color: patternColors[file.pattern] ?? "#5f7d9e",
            opacity: activePaths.has(file.path) ? 0.95 : 0.14,
            borderColor: state.selectedPath === file.path ? "#fff" : "transparent",
            borderWidth: state.selectedPath === file.path ? 2 : 0,
            shadowBlur: activePaths.has(file.path) ? 12 : 0,
            shadowColor: patternColors[file.pattern] ?? "#5f7d9e",
          },
        })),
        emphasis: { scale: 1.8 },
      },
    ],
  };

  const groupRows = [...new Set(data.files.map((file) => file.group))]
    .map((group) => {
      const files = data.files.filter((file) => file.group === group);
      return {
        group,
        files: files.length,
        bytes: files.reduce((sum, file) => sum + file.current_bytes, 0),
        active: files.filter((file) => activePaths.has(file.path)).length,
      };
    })
    .sort((a, b) => b.bytes - a.bytes)
    .slice(0, 16);

  return (
    <section className="panel-grid">
      <Panel
        eyebrow="CodeCity descendants"
        title="Stable repository treemap"
        note="Area is current Git blob size. Color/brightness reflects recorded attention at the shared cursor. Zoom preserves deterministic path order."
        wide
      >
        <EChart
          option={treemapOption}
          className="chart chart--xxl"
          onClick={(params) => {
            const path = (params as { data?: { path?: string } }).data?.path;
            if (path) onChange({ selectedPath: path });
          }}
        />
      </Panel>

      <Panel
        eyebrow="Software cartography"
        title="Stable workspace constellation"
        note="Every path receives deterministic coordinates. Playback changes salience rather than geography, so the map stays mentally comparable."
        wide
      >
        <EChart
          option={constellationOption}
          className="chart chart--large"
          onClick={(params) => {
            const path = (params as { data?: { path?: string } }).data?.path;
            if (path) onChange({ selectedPath: path });
          }}
        />
      </Panel>

      <Panel
        eyebrow="Directory cartogram"
        title="Territories under attention"
        note="Repository size and visible attention are deliberately separate columns. Large but quiet territory is not hidden."
      >
        <div className="territory-list">
          {groupRows.map((row) => (
            <div key={row.group}>
              <strong>{row.group}</strong>
              <span>{row.files} files</span>
              <span>{(row.bytes / 1024).toFixed(0)} KiB</span>
              <i style={{ width: `${Math.max(2, (row.active / Math.max(1, row.files)) * 100)}%` }} />
            </div>
          ))}
        </div>
      </Panel>
    </section>
  );
}

function decorateTree(node: TreeNode, activePaths: Set<string>): TreeNode {
  const children = node.children?.map((child) => decorateTree(child, activePaths));
  const active = node.path ? activePaths.has(node.path) : children?.some((child) => (child as TreeNode & { active?: boolean }).active);
  return {
    ...node,
    children,
    ...(active ? { itemStyle: { color: "#216d7a", borderColor: "#6ee7da" }, active: true } : {}),
  } as TreeNode;
}
