# Independent REAL PREFLIGHT Review

- Reviewer: fresh independent subagent using `research-experiment-design`
- Verdict: **PASS**
- Blocking findings: none

## Independent checks

- The nine Mind2Web rows match the official `train_10.json` source. The
  GUI-Odyssey input matches the first row of the official same-repository
  Hugging Face converted Parquet, whose schema metadata identifies 7,735 rows.
  Reusing that Parquet after Dataset Viewer HTTP 503 is a source-access fallback,
  not a dataset or split change.
- Reinvoking the unchanged TF-IDF/K-Means backend reproduced all 49 Mind2Web
  predictions. Reinvoking unchanged `action_verb()` reproduced all 11
  GUI-Odyssey predictions.
- GUI predictor input contains only coordinates, `Todoist`, `KEY_HOME`, or an
  empty value. Native `step.action` appears only in the scorer sidecar; the
  source audit found zero structured gold copies.
- GUI has 9 literal `unmatched` predictions among 11 operations, while scorer
  support remains 11. Independent V-measure recomputation reproduced 0.5245;
  Mind2Web independently reproduced 0.5565 with support 49.
- Input operations and folded-stack multisets match exactly for Mind2Web
  (49 rows/weight), GUI-Odyssey (11), and their union (60).
- Preflight values remain confined to connectivity-labeled experiment records
  and raw artifacts. They do not appear in the paper or as admitted evidence in
  `docs/evaluation.md`.

## Full-run authorization

The preflight covers both real backend types, scorer-only references, literal
unmatched handling, the constant control, source-field audit, current AgentProf
per-cell folding, and union folding. The fixed full run is authorized. Its GUI
recovery should reuse the already downloaded official Parquet rather than wait
for Dataset Viewer or introduce a downloader.

The GUI preflight's 18.18% coverage is neither a blocker nor a positive result.
The full run must retain whatever complete result the unchanged backend
produces.
