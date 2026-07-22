# Archived Python clustering prototype

This directory preserves an earlier TF-IDF/K-Means prompt-clustering prototype
for research history. It is not an installed AgentPProf backend or product
output path.

AgentPProf now writes exactly one standard `.pb` or `.pb.gz` pprof per run and
does not export prompt JSON, a tag-cache artifact, a custom flamegraph, or a
frontend for this prototype. Do not extend this directory into a parallel
product pipeline. If its clustering idea is revisited experimentally, keep the
experiment outside the CLI and feed any adopted deterministic field mapping
back through the normal operation-to-pprof path.
