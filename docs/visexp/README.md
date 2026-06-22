# Semantic Flamegraph Research Notes

This directory keeps the public, curated research notes for semantic agent
flamegraphs and `agentpprof`. It intentionally does not include the large
generated experiment-output tree from the research branch.

Start here:

- [paper/evaluation-claims-setup.zh-CN.md](paper/evaluation-claims-setup.zh-CN.md):
  paper-shaped Chinese write-up of the claims, terminology, experiment setup,
  oracles, results, and evidence boundaries.
- [CLAIMS.md](CLAIMS.md): claim ledger and allowed/disallowed paper wording.
- [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md): current result narrative and run
  table.
- [EXPERIMENT_TRACKER.md](EXPERIMENT_TRACKER.md): run IDs, commands, oracles,
  and result paths.
- [AGENTPPROF_DESIGN.md](AGENTPPROF_DESIGN.md): product-oriented design notes
  for `agentpprof`.
- [LONG_TAIL_COMPACTION.md](LONG_TAIL_COMPACTION.md): reversible display-map
  and long-tail tag governance design.
- [CLUSTERING_DEEP_RESEARCH.md](CLUSTERING_DEEP_RESEARCH.md): survey and design
  notes for semantic tag clustering.

Generated files under `docs/visexp/out/` are not committed to `main` here. They
remain on the research branch as experiment artifacts and can be regenerated
from the scripts referenced by the tracker when needed.
