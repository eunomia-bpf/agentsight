import { useEffect, useMemo, useRef, useState } from "react";
import FilterBar from "./components/FilterBar";
import Playback from "./components/Playback";
import { visibleEvents } from "./selectors";
import type { FamilyId, GalleryData, ViewState } from "./types";
import AnimationView from "./views/AnimationView";
import ForensicView from "./views/ForensicView";
import LongitudinalView from "./views/LongitudinalView";
import MapView from "./views/MapView";
import MatrixView from "./views/MatrixView";
import OverviewView from "./views/OverviewView";
import PixelView from "./views/PixelView";
import RiverView from "./views/RiverView";
import StorylineView from "./views/StorylineView";

const families: Array<{ id: FamilyId; index: string; name: string; era: string; views: string }> = [
  { id: "overview", index: "00", name: "Field atlas", era: "2026", views: "evidence layers" },
  { id: "pixel", index: "01", name: "Pixels & lines", era: "1992", views: "SeeSoft · lanes" },
  { id: "matrix", index: "02", name: "Matrices", era: "2001", views: "evolution · joins" },
  { id: "map", index: "03", name: "Maps & cities", era: "2007", views: "treemap · constellation" },
  { id: "animation", index: "04", name: "Particles", era: "2008", views: "code_swarm · Gource" },
  { id: "river", index: "05", name: "Rivers & strata", era: "2004", views: "history · survival" },
  { id: "forensic", index: "06", name: "Crime scene", era: "2015", views: "hotspots · coupling" },
  { id: "storylines", index: "07", name: "Human storylines", era: "2010", views: "sessions · ownership" },
  { id: "longitudinal", index: "08", name: "Agent rhythms", era: "new", views: "vitals · receipt · QA" },
];

export default function App() {
  const [data, setData] = useState<GalleryData | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    fetch("./gallery-data.json").then((response) => {
      if (!response.ok) throw new Error(`gallery-data.json: ${response.status}`);
      return response.json() as Promise<GalleryData>;
    }).then(setData).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : String(cause)));
  }, []);
  if (error) return <main className="loading"><strong>Could not load the evidence atlas.</strong><span>{error}</span></main>;
  if (!data) return <main className="loading"><span className="loading-mark" />Loading 30 years of visual grammar…</main>;
  return <Atlas data={data} />;
}

function Atlas({ data }: { data: GalleryData }) {
  const [state, setState] = useState<ViewState>(() => ({
    family: "overview",
    cursorMs: data.meta.window_end_ms,
    rangeStartMs: data.meta.window_start_ms,
    rangeEndMs: data.meta.window_end_ms,
    playing: false,
    speedHoursPerSecond: 24,
    vendors: new Set(),
    associationStates: new Set(),
    selectedPath: null,
    selectedSession: null,
  }));
  const stateRef = useRef(state); stateRef.current = state;
  const change = (patch: Partial<ViewState>) => setState((current) => ({ ...current, ...patch }));
  useEffect(() => {
    if (!state.playing) return;
    let frame = 0; let previous = performance.now();
    const tick = (now: number) => {
      const current = stateRef.current;
      const advance = (now - previous) / 1000 * current.speedHoursPerSecond * 3_600_000;
      previous = now;
      setState((value) => {
        const next = value.cursorMs + advance;
        return next >= value.rangeEndMs ? { ...value, cursorMs: value.rangeEndMs, playing: false } : { ...value, cursorMs: next };
      });
      if (stateRef.current.playing) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick); return () => cancelAnimationFrame(frame);
  }, [state.playing]);
  const events = useMemo(() => visibleEvents(data, state), [data, state]);
  const props = { data, state, events, onChange: change };
  const family = families.find((row) => row.id === state.family)!;
  const view = state.family === "overview" ? <OverviewView {...props} />
    : state.family === "pixel" ? <PixelView {...props} />
    : state.family === "matrix" ? <MatrixView {...props} />
    : state.family === "map" ? <MapView {...props} />
    : state.family === "animation" ? <AnimationView {...props} />
    : state.family === "river" ? <RiverView {...props} />
    : state.family === "forensic" ? <ForensicView {...props} />
    : state.family === "storylines" ? <StorylineView {...props} />
    : <LongitudinalView {...props} />;
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">A∴</span><div><strong>AgentSight</strong><small>Evolution Atlas</small></div></div>
      <p className="sidebar-intro">A visual field instrument for software developed by agents over time.</p>
      <nav aria-label="visualization families">{families.map((item) => <button key={item.id} data-testid={`nav-${item.id}`} className={state.family === item.id ? "is-active" : ""} onClick={() => change({ family: item.id })}><span>{item.index}</span><div><strong>{item.name}</strong><small>{item.views}</small></div><em>{item.era}</em></button>)}</nav>
      <div className="evidence-key"><span>Evidence contract</span><div><i className="process" />recorded process</div><div><i className="durable" />durable Git outcome</div><div><i className="endpoint" />current endpoint</div><p>No layer is silently promoted to another.</p></div>
      <footer><span>{data.meta.endpoint_revision.slice(0, 10)}</span><small>frozen endpoint</small></footer>
    </aside>
    <main className="workspace">
      <header className="topbar"><div><span className="eyebrow">Family {family.index} · {family.era}</span><h1>{family.name}</h1><p>{data.meta.repository} · real native histories + first-parent Git</p></div><div className="status-cluster"><span className="status-live"><i />REAL DATA</span><span>{data.summary.sessions} sessions</span><span>{data.summary.path_records} path records</span><span>{data.summary.git_lifetimes} Git lifetimes</span></div></header>
      <FilterBar state={state} onChange={change} />
      <div className="view-stage" data-testid={`family-${state.family}`}>{view}</div>
      <div className="playback-dock"><Playback state={state} min={data.meta.window_start_ms} max={data.meta.window_end_ms} onChange={change} /></div>
    </main>
    {(state.selectedPath || state.selectedSession) && <aside className="inspector"><button onClick={() => change({ selectedPath: null, selectedSession: null })}>×</button><span className="eyebrow">Focused evidence</span>{state.selectedPath && <><h2>{state.selectedPath.split("/").at(-1)}</h2><p>{state.selectedPath}</p><dl>{(() => { const file = data.files.find((row) => row.path === state.selectedPath); return file ? <><dt>pattern</dt><dd>{file.pattern}</dd><dt>recorded touches</dt><dd>{file.touches}</dd><dt>Git churn</dt><dd>{file.churn}</dd><dt>Git lifetime</dt><dd>{file.lifetime_id === null ? "no matching Git lifetime" : file.survives_to_head ? "survives at endpoint" : "ended"}</dd><dt>join states</dt><dd>{Object.entries(file.association_states).map(([key, value]) => `${key}: ${value}`).join(" · ")}</dd></> : null; })()}</dl></>}{state.selectedSession && <><h2>{state.selectedSession}</h2><p>Pseudonymous native-history trajectory</p></>}</aside>}
  </div>;
}
