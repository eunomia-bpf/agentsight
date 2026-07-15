import { useEffect, useMemo, useRef } from "react";
import cytoscape from "cytoscape";
import type { EChartsOption } from "echarts";
import { baseChart } from "../chartTheme";
import EChart from "../components/EChart";
import Panel from "../components/Panel";
import { projectOrderedEdges, topBy } from "../selectors";
import type { GraphEdge } from "../types";
import type { ViewProps } from "./viewTypes";

export default function ForensicView({ data, state, events, onChange }: ViewProps) {
  const visible = new Set(events.map((event) => event.path));
  const orderedEdges = useMemo(() => projectOrderedEdges(events), [events]);
  const hotspots = topBy(
    data.files.filter(
      (file) => file.survives_to_head && file.path === file.current_path,
    ),
    (file) => file.risk_score,
    90,
  );
  const minRisk = Math.min(...hotspots.map((file) => file.risk_score));
  const maxRisk = Math.max(...hotspots.map((file) => file.risk_score));
  const hotspotOption: EChartsOption = {
    ...baseChart,
    tooltip: { renderMode: "richText", formatter: (params: unknown) => { const row = (params as { data: { path: string; risk: number; churn: number; touches: number } }).data; return `${row.path}\nrisk ${row.risk.toFixed(2)}\n${row.touches} touches · ${row.churn} Git churn`; } },
    series: [{
      type: "treemap", roam: true, breadcrumb: { show: false },
      data: hotspots.map((file) => ({ name: file.path.split("/").at(-1), path: file.path, value: Math.max(1, file.current_bytes), risk: file.risk_score, churn: file.churn, touches: file.touches, itemStyle: { color: riskColor(file.risk_score, minRisk, maxRisk), opacity: visible.has(file.path) ? .95 : .35 } })),
      label: { color: "#f2f5fb", fontSize: 9 }, itemStyle: { borderColor: "#080c14", gapWidth: 1 },
    }],
  };
  return <section className="panel-grid">
    <Panel eyebrow="Crime Scene · 2015" title="Hotspot investment map" note="Area is current file size; color is a heuristic blend of Git churn and recorded attention. It ranks inspection candidates, not defects." wide>
      <EChart option={hotspotOption} className="chart chart--xl" onClick={(params) => { const path = (params as { data?: { path?: string } }).data?.path; if (path) onChange({ selectedPath: path }); }} />
    </Panel>
    <Panel eyebrow="Temporal coupling" title="Git co-change network" note="Edges mean files changed in the same commit. This is correlation in durable history, not runtime or semantic dependency." wide>
      <EvidenceGraph edges={data.cochange_edges} semantics="co-change" selected={state.selectedPath} onSelect={(path) => onChange({ selectedPath: path })} />
    </Panel>
    <Panel eyebrow="Ordered information flow" title="Read-before-write network" note="A directed edge records temporal order inside a session. It is explicitly not a causal edge and not proof that the read informed the write." wide>
      <div data-testid="ordered-edge-projection" data-edge-count={orderedEdges.length}>
        <EvidenceGraph edges={orderedEdges} semantics="ordered" selected={state.selectedPath} onSelect={(path) => onChange({ selectedPath: path })} />
      </div>
    </Panel>
  </section>;
}

function EvidenceGraph({ edges, semantics, selected, onSelect }: { edges: GraphEdge[]; semantics: string; selected: string | null; onSelect: (path: string) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const rows = useMemo(() => edges.slice(0, 180), [edges]);
  useEffect(() => {
    if (!ref.current) return;
    const paths = [...new Set(rows.flatMap((edge) => [edge.source, edge.target]))];
    const cy = cytoscape({
      container: ref.current,
      elements: [
        ...paths.map((path) => ({ data: { id: path, label: path.split("/").at(-1) } })),
        ...rows.map((edge, index) => ({ data: { id: `e${index}`, source: edge.source, target: edge.target, weight: edge.count } })),
      ],
      style: [
        { selector: "node", style: { "background-color": "#4c83a6", label: "data(label)", color: "#b8c8db", "font-size": 7, "text-valign": "bottom", "text-margin-y": 4, width: 9, height: 9 } },
        { selector: "edge", style: { width: "mapData(weight, 1, 20, .3, 3)", "line-color": semantics === "ordered" ? "#d69b62" : "#56718b", "target-arrow-color": "#d69b62", "target-arrow-shape": semantics === "ordered" ? "triangle" : "none", "curve-style": "bezier", opacity: .46 } },
      ],
      layout: { name: "cose", animate: false, randomize: false, fit: true, padding: 24, nodeRepulsion: () => 90_000 },
    });
    if (selected) {
      cy.getElementById(selected).style({ "background-color": "#fff1a8", width: 18, height: 18 });
    }
    cy.on("tap", "node", (event) => onSelect(String(event.target.id())));
    return () => cy.destroy();
  }, [onSelect, rows, selected, semantics]);
  return <div ref={ref} className="evidence-graph" />;
}

export function normalizedRisk(risk: number, minimum: number, maximum: number): number {
  if (!Number.isFinite(risk) || maximum <= minimum) return 0.5;
  const low = Math.log1p(Math.max(0, minimum));
  const high = Math.log1p(Math.max(0, maximum));
  return Math.max(0, Math.min(1, (Math.log1p(Math.max(0, risk)) - low) / (high - low)));
}

function riskColor(risk: number, minimum: number, maximum: number): string {
  const t = normalizedRisk(risk, minimum, maximum);
  return `hsl(${190 - t * 170} 60% ${31 + t * 20}%)`;
}
