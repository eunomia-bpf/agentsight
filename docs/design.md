# Design

## Evidence model

The design keeps three non-interchangeable sources joinable:

1. **Recorded process:** prompts, model responses, tool actions, repository-
   relative path evidence, status, vendor/model/session labels, tokens, and
   timestamps from native session files.
2. **Durable Git outcome:** commits, rename-aware path changes, additions and
   deletions, Git author metadata, parent relationships, file birth/death
   intervals, and optional hunk lineage.
3. **Current-tree endpoint:** current paths and, where lineage confidence is
   supported, current lines, blame, age, and size.

All normalized events remain in the export. Only events with usable repository-
relative paths are association-eligible. An eligible event has zero, one, or
several candidate Git changes; multiple candidates remain ambiguous. Git
changes without an event are a separate Git-side unmatched set. A recorded
test/build/lint action is a verification action with a status, not proof that
code is correct. Read-before-edit is ordered process evidence, not causality.

Path-level event-to-Git association, optional event-to-hunk association, Git
hunk-to-current-line lineage, and endpoint survival are separate links with
separate confidence. Unsupported records remain path-level. No temporal join
is presented as Git authorship or causal attribution.

A file lifetime starts when Git adds a path that is absent from its parent,
continues across detected renames, and ends at deletion. Recreating the same
path after deletion starts a new lifetime identifier. Endpoint path survival
means that the same continuous lifetime reaches the selected current-tree
revision; name equality alone is insufficient.

The primary RQ1 association unit is one normalized event--path reference. Its
candidate target is a rename-aware file-change entry in a non-merge commit. The
primary search window is from 15 minutes before the event through 24 hours
after it, restricted to the same file lifetime. Zero, one, and many candidates
remain distinct labels. Merge commits are excluded from primary targets and
reported separately; multiple events may map to a squash change, and a split
change may leave multiple candidates rather than forcing a one-to-one match.

## Frozen core tasks and views

| Review decision | Required layers | Core coordinated views |
|---|---|---|
| Locate an edit with no recorded subsequent verification action | Process | Temporal summary + event detail |
| Distinguish eligible-unmatched from candidate-associated events | Process + Git | Association-state matrix + linked detail |
| Reconstruct cross-file exploration order | Process + repository structure | Playback + ordered coupling |
| Find frequently changed code that survives in the current tree | Git + endpoint | Hotspot + endpoint-survival strata |

These combinations are frozen before final evaluation. Supporting views do not
inherit a task-utility claim merely by appearing in the gallery.

## Coordinated view families

| Family | Planned views | Primary decision |
|---|---|---|
| Pixel/line | SeeSoft line-age map; touch/association overlay | Which old or concentrated lines deserve inspection, and at what confidence can a process event be linked? |
| Matrix | Evolution Matrix; association-state matrix | Which files burst, pulse, decay, or briefly exist, and where is the join ambiguous? |
| Map/city | Stable treemap/circle pack; directory cartogram | Where did activity and durable growth concentrate? |
| Animation | Event particles; Gource export; stable growth replay | In what order did exploration, editing, checks, and commits unfold? |
| River/strata | Code-age burndown; endpoint-survival strata; History-Flow-style contribution bands | What remains from each period, and which evidence supports the association? |
| Forensic | Hotspot; Git co-change; ordered read-before-edit network | Where is risk or hidden correlation concentrated, and what process order was recorded? |
| Storylines | Git-author ownership map; vendor/model/session storylines | How did authors and recorded agent sessions move through directory space without conflating their identities? |
| Longitudinal | Calendar heatmap; punch card; vital signs; token Sankey; paired-run/ghost comparison | When did work happen, at what cost, with what rhythm and mismatch? |

The gallery therefore contains at least eighteen projections while preserving
the seven historical families requested by the user.

## Interaction contract

All time-dependent views share one playback cursor, play/pause, speed control,
draggable scrubbing, interval brushing, and deterministic path coordinates.
Selections over time, path, session, vendor/model label, association state, and
survival state propagate to every compatible view. Semantic zoom switches from
preaggregated overview buckets to linked event detail; it does not silently
discard unmatched evidence. Stable and recomputed layout modes remain an RQ4
ablation.

## Reuse policy

Use established libraries and interchange formats for layout and interaction:
ECharts and D3 for hierarchy/matrix/flow encodings, Cytoscape.js for coupling
networks, uPlot for dense time series, Perfetto Trace Event for a reusable trace
baseline, and Gource custom logs for animation export. Custom code is limited
to source parsing, evidence-preserving joins, projections, shared interaction
state, and rendering not supplied by those tools. Dependencies must be package-
locked and available without a runtime CDN.
