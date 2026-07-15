# AgentSight Evolution Atlas

An experimental, local-first gallery for inspecting how coding-agent activity
and a repository's durable Git history unfold over long intervals. It adapts
seven established software-evolution visualization families without replacing
AgentSight's existing single-run timeline, process tree, log, or flame graph.

The atlas is an evidence instrument, not a provenance detector. Its three
layers remain separate:

1. recorded process: native Claude, Codex, and Gemini path/tool events;
2. durable outcome: first-parent Git commits, changes, renames, and lifetimes;
3. endpoint state: frozen-tree blobs and Git-blame line origins.

Candidate event-to-Git links expose zero/one/many alternatives. Temporal order
does not establish causality, authorship, or verification. The real-history
association experiment did not pass calibration/support gates, so the shipped
atlas is intentionally `descriptive_only`.

## Run

```bash
cd vis-gallery
npm install
npm run dev
```

Open <http://127.0.0.1:5173>. The checked public dataset is privacy-scanned and
contains 56 deduplicated sessions, 3,960 path-event rows, 858 path records,
652 Git lifetimes, 177 commits, 1,852 changes, and 12,000 current Git-blame
line pixels. Of the path records, 693 map to one or more Git lifetimes; aliases
and reused literal paths may map to the same lifetime, while event-only paths
remain explicit rather than being mislabeled as lifetimes. The three real
observation days span 2026-06-02 through 2026-07-14; they are not a continuous
synthetic workload. July 14 is right-censored and is used only for descriptive
process views.

## Visual families

| Family | Implemented views |
|---|---|
| SeeSoft / pixels | current-line age pixels; touch/association lanes |
| Evolution Matrix | path × day evolution; association-state matrix; named signals |
| CodeCity / cartography | stable treemap; stable constellation; directory cartogram |
| code_swarm / Gource | agent–path particle field; durable commit pulses; recent wake |
| History Flow / strata | activity river; lifetime cohorts; survival ledger; Git sediment |
| Crime Scene | hotspot map; Git co-change network; ordered read-before-write network |
| Storylines | session journeys; Git author ownership flow; visible cast |
| Longitudinal extras | punch card; uPlot vitals; semantic flow; verification lag; receipt; mature-day ghost |

All compatible process views share one draggable/playable time cursor, vendor
and association-state filters, and path/session focus. Durable Git-only and
frozen endpoint layers remain filter-invariant and are labeled as such rather
than silently reinterpreted as agent evidence. ECharts handles dense canvas charts,
Cytoscape.js the evidence networks, uPlot the high-frequency vital trace, and
custom canvases the SeeSoft and particle fields.

## Rebuild the public projection

`analysis/build_gallery_data.py` consumes canonical private exports produced by
`agent-session-export`, a frozen repository revision, RQ1 public metrics, and
the censored-cell record. Its output validator rejects prompt/command/edit body
fields and absolute home paths. Native inputs remain ignored.

```bash
cargo run --manifest-path ../agent-session/Cargo.toml \
  --bin agent-session-export -- \
  --repo .. --head REV --since 2026-06-02T07:00:00Z --until 2026-06-03T07:00:00Z \
  --output /private/day.json
```

The exporter also supports `--format events-jsonl`, `--format perfetto`, and
`--format gource`. Those compatibility projections are lossy and do not carry
the complete uncertainty/evidence model.

Event-level exact-hunk fingerprints are intentionally available only for a
single repository file with a single native edit hunk. Multi-file and
multi-hunk patches retain process/path evidence but are never presented as one
exact Git-hunk match.

## Verify

```bash
npm run build
npm test
npm run test:e2e
# with `npm run dev -- --port 4173` running in another terminal:
npm run measure -- http://127.0.0.1:4173 artifacts/browser-metrics.json
npm run capture -- http://127.0.0.1:4173 artifacts
```

Playwright visits every family, changes the shared cursor and filter state, and
captures ephemeral representative plates under ignored
`test-results/screenshots/`. Curated, privacy-scanned paper plates live under
`artifacts/` and are not rewritten by routine CI.
